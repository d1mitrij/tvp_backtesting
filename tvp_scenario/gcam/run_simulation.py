#!/usr/bin/env python3
"""
run_simulation.py  (GCAM / pygcam version)
==========================================
REMIND-MAgPIE IPCC Scenario Simulation via GCAM + pygcam

Workflow
--------
1. derive_parameters.py reads hydro/hospital/rail CSVs → project-calibrated
   parameters (coal efficiencies, hydro capacity, rail demand).
2. `gt run` (pygcam CLI) executes each scenario in an isolated sandbox:
     - copies GCAM XML inputs
     - applies xml/project_params.xml and xml/ssp{N}_policy.xml modifications
     - runs the GCAM C++ binary
3. `gt query` extracts electricity generation, CO2 emissions, installed
   capacity, and capital investment from the GCAM output database (BaseX).
4. iamc_bridge.py aggregates 32 GCAM regions → Africa/Asia/Europe/LATAM,
   maps subsectors to IAMC variables, and converts units.
5. tvp_dbio intensity adjustment factors (adj_ratio_ghg, adj_ratio_employment)
   are computed and saved.

Prerequisites
-------------
  export GCAM_HOME=/path/to/gcam-core        # GCAM release directory
  export GCAM_EXE=$GCAM_HOME/exe/gcam        # GCAM binary
  export GCAM_XML=$GCAM_HOME/input/gcamdata/xml

  pip install -r requirements.txt
  # (installs pygcam, gcam-reader, pandas, numpy, lxml)

Usage
-----
    python run_simulation.py                          # all 5 SSPs
    python run_simulation.py --scenario ssp1 ssp5    # two scenarios
    python run_simulation.py --scenario ssp2 --dry-run  # print commands only

Outputs (written to results/)
------------------------------
    results/iamc_<scenario>.csv          IAMC long-form per scenario
    results/iamc_all_scenarios.csv       Combined across all scenarios
    results/tvpdbio_intensity_factors.csv tvp_dbio GHG/employment ratios
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

# ── Shared scenario registry ──────────────────────────────────────────────────
_REG_ROOT = Path(__file__).resolve().parent.parent
if str(_REG_ROOT) not in sys.path:
    sys.path.insert(0, str(_REG_ROOT))
from scenarios_registry import SSP_REGISTRY

HERE        = Path(__file__).parent
PROJECT_XML = HERE / "config" / "project.xml"
RESULTS_DIR = HERE / "results"
RESULTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── All five SSP scenarios ────────────────────────────────────────────────────
# iamc_label, description, rcp — from scenarios_registry (single source of truth).
# co2_price_2050_usd_t (regional carbon prices) — GCAM-specific, kept here.
_CO2_PRICES: dict[str, dict[str, int]] = {
    "ssp1": {"Africa": 500, "Asia": 400, "Europe": 800, "LATAM": 400},
    "ssp2": {"Africa": 200, "Asia": 175, "Europe": 350, "LATAM": 200},
    "ssp3": {"Africa":  15, "Asia":  15, "Europe":  60, "LATAM":  20},
    "ssp4": {"Africa":  25, "Asia": 120, "Europe": 500, "LATAM":  80},
    "ssp5": {"Africa":   8, "Asia":   8, "Europe":  20, "LATAM":  10},
}
SCENARIOS: dict[str, dict] = {
    key: {
        **{k: v for k, v in SSP_REGISTRY[key].items()
           if k in ("iamc_label", "description", "rcp")},
        "co2_price_2050_usd_t": _CO2_PRICES[key],
    }
    for key in ("ssp1", "ssp2", "ssp3", "ssp4", "ssp5")
}

REGIONS = ["Africa", "Asia", "Europe", "LATAM"]

# Query names must match the <query name="..."> entries in config/project.xml
QUERY_NAMES = ["elec_gen", "co2", "capacity", "investment"]


# ── pygcam subprocess helpers ─────────────────────────────────────────────────

def _gt(args: list[str], dry_run: bool = False) -> subprocess.CompletedProcess:
    """Run a pygcam `gt` command.  Raises on non-zero exit unless dry_run."""
    cmd = ["gt", "-p", str(PROJECT_XML), "-g", "SSPs"] + args
    log.info("  $ %s", " ".join(cmd))
    if dry_run:
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            log.debug("    gt: %s", line)
    if result.returncode != 0:
        log.error("  gt failed (rc=%d):\n%s", result.returncode, result.stderr)
        raise RuntimeError(f"gt command failed: {' '.join(cmd)}")
    return result


def _sandbox_query_dir(scenario_key: str) -> Path:
    """Return the expected pygcam query results directory for a scenario."""
    # pygcam places query CSVs at: {sandboxDir}/queryResults/
    # The sandboxDir is defined in project.xml as {GCAM_HOME}/sandbox/{scenarioName}
    import os
    gcam_home = Path(os.environ.get("GCAM_HOME", "."))
    return gcam_home / "sandbox" / scenario_key / "queryResults"


def _read_query_results(scenario_key: str) -> dict[str, pd.DataFrame]:
    """
    Read all query CSV files for a completed scenario.

    Tries gcam_reader first (if available); falls back to iamc_bridge.read_query_csv.
    """
    from iamc_bridge import read_query_csv

    query_dir = _sandbox_query_dir(scenario_key)
    results: dict[str, pd.DataFrame] = {}

    for qname in QUERY_NAMES:
        csv_path = query_dir / f"{qname}.csv"
        if not csv_path.exists():
            # pygcam may use the query title as filename; try common alternatives
            for alt in [f"{scenario_key}_{qname}.csv", f"{qname}_query.csv"]:
                alt_path = query_dir / alt
                if alt_path.exists():
                    csv_path = alt_path
                    break
            else:
                log.warning("  Query result not found: %s", csv_path)
                results[qname] = pd.DataFrame()
                continue
        try:
            results[qname] = read_query_csv(csv_path)
            log.info("  Read %s: %d rows", csv_path.name, len(results[qname]))
        except Exception as exc:
            log.error("  Failed to read %s: %s", csv_path, exc)
            results[qname] = pd.DataFrame()

    return results


# ── Per-scenario runner ───────────────────────────────────────────────────────

def run_scenario(
    scenario_key: str,
    dry_run: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Set up, run, query, and convert one GCAM scenario to IAMC + tvp_dbio factors."""
    from iamc_bridge import solution_to_iamc, compute_tvp_dbio_intensity_factors
    from derive_parameters import load_project_data

    cfg = SCENARIOS[scenario_key]
    log.info("=" * 70)
    log.info("Scenario : %s  |  %s", scenario_key.upper(), cfg["iamc_label"])
    log.info("          %s", cfg["description"])
    log.info("=" * 70)

    # ── 1. Log derived parameters for traceability ────────────────────────
    proj_params = load_project_data()
    log.info("  Project-derived parameters (from modeled_input_data/):")
    for r in REGIONS:
        p = proj_params[r]
        log.info(
            "    %s: coal_ef=%.4f Mt CO2/PJ, hydro_retro_max=%.3f GW%s",
            f"{r:8s}", p.coal_ef_mt_pj, p.hydro_retro_gw,
            f", rail_elec={p.rail_elec_demand_pj:.4f} PJ/yr"
            if p.rail_elec_demand_pj > 0 else "",
        )

    # ── 2. Run GCAM via pygcam ─────────────────────────────────────────────
    log.info("  Running GCAM (pygcam gt run) …")
    t0 = time.perf_counter()
    _gt(["run", "-s", scenario_key, "--setup", "--gcam"], dry_run=dry_run)
    elapsed = time.perf_counter() - t0
    log.info("  GCAM run complete in %.1f s", elapsed)

    # ── 3. Extract results via pygcam query ───────────────────────────────
    log.info("  Querying GCAM output database …")
    _gt(["query", "-s", scenario_key,
         "-q", ",".join(QUERY_NAMES)], dry_run=dry_run)

    if dry_run:
        log.info("  [dry-run] Skipping result reading.")
        return pd.DataFrame(), pd.DataFrame()

    query_data = _read_query_results(scenario_key)
    if all(df.empty for df in query_data.values()):
        log.error("  All query results empty for %s. Skipping.", scenario_key)
        return pd.DataFrame(), pd.DataFrame()

    # ── 4. Convert to IAMC ───────────────────────────────────────────────
    iamc_df = solution_to_iamc(
        elec_gen_df   = query_data.get("elec_gen",    pd.DataFrame()),
        co2_df        = query_data.get("co2",         pd.DataFrame()),
        capacity_df   = query_data.get("capacity",    pd.DataFrame()),
        investment_df = query_data.get("investment",  None),
        scenario      = cfg["iamc_label"],
    )
    log.info("  IAMC records: %d", len(iamc_df))

    # ── 5. Compute tvp_dbio factors ───────────────────────────────────────
    factor_df = compute_tvp_dbio_intensity_factors(iamc_df)

    # ── 6. Save per-scenario IAMC CSV ─────────────────────────────────────
    out = RESULTS_DIR / f"iamc_{scenario_key}.csv"
    iamc_df.to_csv(out, index=False)
    log.info("  Saved → %s", out.name)

    return iamc_df, factor_df


# ── Summary printer ───────────────────────────────────────────────────────────

def summarise(iamc_df: pd.DataFrame, label: str) -> None:
    """Print compact energy + emissions summary (mirrors OSeMOSYS runner format)."""
    if iamc_df.empty:
        return
    log.info("  ── %s key metrics ──", label)
    for region in REGIONS:
        rdf = iamc_df[iamc_df["region"] == region]

        def _val(var: str, yr: int) -> float:
            v = rdf[(rdf["variable"] == var) & (rdf["year"] == yr)]["value"]
            return float(v.iloc[0]) if len(v) else 0.0

        e20 = _val("Secondary Energy|Electricity", 2020)
        e50 = _val("Secondary Energy|Electricity", 2050)
        c20 = _val("Emissions|CO2|Energy|Supply|Electricity", 2020)
        c50 = _val("Emissions|CO2|Energy|Supply|Electricity", 2050)
        s50 = _val("Capacity|Electricity|Solar", 2050)
        w50 = _val("Capacity|Electricity|Wind",  2050)
        log.info(
            "    %s: elec %.2f→%.2f EJ/yr  CO2 %.0f→%.0f Mt/yr  "
            "Solar/Wind 2050: %.0f/%.0f GW",
            f"{region:7s}", e20, e50, c20, c50, s50, w50,
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main(
    scenarios: list[str] | None = None,
    dry_run: bool = False,
) -> None:
    if scenarios is None:
        scenarios = list(SCENARIOS.keys())

    all_iamc:    list[pd.DataFrame] = []
    all_factors: list[pd.DataFrame] = []

    for sc in scenarios:
        if sc not in SCENARIOS:
            log.error("Unknown scenario '%s'. Valid: %s", sc, list(SCENARIOS))
            sys.exit(1)

        iamc_df, factor_df = run_scenario(sc, dry_run=dry_run)

        if not iamc_df.empty:
            summarise(iamc_df, SCENARIOS[sc]["iamc_label"])
            all_iamc.append(iamc_df)
        if not factor_df.empty:
            all_factors.append(factor_df)

    # ── Write combined outputs ────────────────────────────────────────────
    if all_iamc:
        combined = pd.concat(all_iamc, ignore_index=True)
        out = RESULTS_DIR / "iamc_all_scenarios.csv"
        combined.to_csv(out, index=False)
        log.info("\nCombined IAMC output (%d rows) → %s", len(combined), out.name)

    if all_factors:
        factors = pd.concat(all_factors, ignore_index=True)
        out = RESULTS_DIR / "tvpdbio_intensity_factors.csv"
        factors.to_csv(out, index=False)
        log.info("tvp_dbio factors (%d rows) → %s", len(factors), out.name)

        log.info("\n  ── adj_ratio_ghg (Energy_Utilities GHG intensity vs 2020) ──")
        pivot = factors.pivot_table(
            index=["scenario", "region"], columns="year",
            values="adj_ratio_ghg",
        ).round(3)
        log.info("\n%s", pivot.to_string())

    log.info("\nSimulation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="REMIND-MAgPIE IPCC Scenario Simulation — GCAM/pygcam (all 5 SSPs)"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        nargs="+",
        default=list(SCENARIOS.keys()),
        help="Scenario(s) to run (default: all five SSPs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print pygcam commands without executing GCAM binary",
    )
    args = parser.parse_args()
    main(scenarios=args.scenario, dry_run=args.dry_run)
