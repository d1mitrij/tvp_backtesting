#!/usr/bin/env python3
"""
run_simulation.py  (MESSAGEix / message-ix version)
====================================================
REMIND-MAgPIE IPCC Scenario Simulation via MESSAGEix + ixmp

Workflow
--------
1. derive_parameters.py reads project CSVs → coal EFs, hydro capacity, rail demand.
2. ixmp.Platform connects to a local ixmp4 (SQLite) or hsqldb backend.
3. `mix-models fetch snapshot-1` (run once) populates the platform with the
   MESSAGEix-GLOBIOM R11 baseline scenario from Zenodo.
4. For each SSP, the baseline is cloned, then:
     a. base_params.apply_to_scenario()  — project-calibrated overrides
     b. ssp{N}.apply_to_scenario()       — carbon prices + emission caps + growth limits
5. GAMS solves the MESSAGE LP/MIP via scenario.solve().
6. iamc_bridge extracts ACT/CAP/EMISS solution variables and converts to IAMC format.
7. tvp_dbio intensity factors are computed and saved.

Prerequisites
-------------
  # GAMS (demo license — covers tutorial-scale models)
  export GAMS_PATH=/path/to/gams

  # Java 11+ (required by ixmp hsqldb backend)
  java -version

  # Python packages
  pip install -r requirements.txt

  # Fetch snapshot (internet, ~400 MB, cached locally)
  mix-models fetch snapshot-1

Usage
-----
    python run_simulation.py                          # all 5 SSPs
    python run_simulation.py --scenario ssp1 ssp5    # two scenarios
    python run_simulation.py --scenario ssp2 --backend ixmp4
    python run_simulation.py --dry-run               # skip GAMS solve

Outputs (written to results/)
------------------------------
    results/iamc_<scenario>.csv          IAMC long-form per scenario
    results/iamc_all_scenarios.csv       Combined across all scenarios
    results/tvpdbio_intensity_factors.csv tvp_dbio GHG/employment ratios
"""

from __future__ import annotations

import argparse
import logging
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
RESULTS_DIR = HERE / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Add scenarios/ to sys.path so that ssp*.py can do `from _param_utils import …`
if str(HERE / "scenarios") not in sys.path:
    sys.path.insert(0, str(HERE / "scenarios"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── All five SSP scenarios ────────────────────────────────────────────────────
from scenarios import ALL as SCENARIO_MODULES

# iamc_label, description — from scenarios_registry (single source of truth).
# No MESSAGEix-specific fields added to shared metadata.
SCENARIOS: dict[str, dict] = {
    key: {k: v for k, v in SSP_REGISTRY[key].items()
          if k in ("iamc_label", "description")}
    for key in ("ssp1", "ssp2", "ssp3", "ssp4", "ssp5")
}

# MESSAGEix baseline model / scenario name (from snapshot-1)
BASE_MODEL    = "MESSAGEix-GLOBIOM 1.1"
BASE_SCENARIO = "baseline"

REGIONS = ["Africa", "Asia", "Europe", "LATAM"]


# ── ixmp platform ─────────────────────────────────────────────────────────────

def get_platform(backend: str = "ixmp4") -> "ixmp.Platform":
    """
    Connect to a local ixmp platform.

    ixmp4 (SQLite):
        No Java required. Database stored at results/ixmp4.db.
        Recommended for initial runs and CI.

    hsqldb (Java):
        Requires Java 11+ and the ixmp Java backend.
        Database stored at results/ixmp_db.
        Use when Java is available and you need full ixmp feature set.
    """
    import ixmp

    db_path = RESULTS_DIR / ("ixmp4.db" if backend == "ixmp4" else "ixmp_db")

    if backend == "ixmp4":
        # ixmp 3.11+: ixmp4 backend uses ixmp4_name + dsn (not url)
        mp = ixmp.Platform(
            backend="ixmp4",
            ixmp4_name="s4_scenarios",
            dsn=f"sqlite:///{db_path}",
        )
    else:
        mp = ixmp.Platform(
            backend="jdbc",
            driver="hsqldb",
            url=f"jdbc:hsqldb:file:{db_path}",
        )
    log.info("  ixmp platform: %s backend at %s", backend, db_path)
    return mp


def ensure_snapshot(mp, dry_run: bool = False) -> bool:
    """
    Check whether the snapshot baseline exists in the platform; if not, fetch it.

    Returns True if baseline is available, False if fetch failed.
    """
    import ixmp

    try:
        scen = ixmp.TimeSeries(mp, BASE_MODEL, BASE_SCENARIO, version="last")
        log.info("  Snapshot baseline found: %s / %s", BASE_MODEL, BASE_SCENARIO)
        return True
    except Exception:
        pass

    if dry_run:
        log.warning("  [dry-run] Snapshot not found; would run: mix-models fetch snapshot-1")
        return False

    log.info("  Snapshot not found. Fetching from Zenodo (mix-models fetch snapshot-1)…")
    import subprocess
    result = subprocess.run(
        ["mix-models", "fetch", "snapshot-1"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error("  mix-models fetch failed:\n%s", result.stderr)
        return False
    log.info("  Snapshot fetched successfully.")
    return True


# ── Per-scenario runner ───────────────────────────────────────────────────────

def run_scenario(
    scenario_key: str,
    mp,
    dry_run: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clone baseline, apply SSP parameters, solve, and extract IAMC + factors."""
    import message_ix
    from scenarios import base_params
    from iamc_bridge import solution_to_iamc_via_reporter, compute_tvp_dbio_intensity_factors
    from derive_parameters import load_project_data

    cfg = SCENARIOS[scenario_key]
    ssp_mod = SCENARIO_MODULES[scenario_key]

    log.info("=" * 70)
    log.info("Scenario : %s  |  %s", scenario_key.upper(), cfg["iamc_label"])
    log.info("          %s", cfg["description"])
    log.info("=" * 70)

    # ── 1. Log derived parameters ─────────────────────────────────────────
    proj_params = load_project_data()
    log.info("  Project-derived parameters (from modeled_input_data/):")
    for r in REGIONS:
        p = proj_params[r]
        log.info(
            "    %s: coal_ef=%.4f Mt CO2/PJ  → %.4f Mt CO2/GWa, "
            "hydro_retro=%.3f GW%s",
            f"{r:8s}", p.coal_ef_mt_pj,
            p.coal_ef_mt_pj * 31.536,
            p.hydro_retro_gw,
            f", rail={p.rail_elec_demand_pj:.4f} PJ/yr"
            if p.rail_elec_demand_pj > 0 else "",
        )

    # ── 2. Clone baseline ─────────────────────────────────────────────────
    if dry_run:
        # In dry-run mode, validate parameters without needing the snapshot.
        log.info("  [dry-run] Validating parameter DataFrames (no ixmp clone needed).")
        p_ssp = ssp_mod.get_params()
        base_dfs = {
            "emission_factor":   base_params.get_emission_factor_df(),
            "bound_activity_up": base_params.get_hydro_retro_bounds_df(),
            "demand":            base_params.get_rail_demand_df(),
        }
        for param, df in {**base_dfs, **p_ssp}.items():
            log.info("    %s: %d rows", param, len(df) if df is not None else 0)
        log.info("  [dry-run] Skipping GAMS solve.")
        return pd.DataFrame(), pd.DataFrame()

    log.info("  Loading baseline scenario …")
    base = message_ix.Scenario(mp, BASE_MODEL, BASE_SCENARIO)

    clone_name = cfg["iamc_label"]
    log.info("  Cloning to '%s' …", clone_name)
    scen = base.clone(
        model=BASE_MODEL,
        scenario=clone_name,
        annotation=f"S4 {cfg['description']}",
        keep_solution=False,
    )
    scen.check_out()

    # ── 3. Apply project-calibrated base parameters ───────────────────────
    log.info("  Applying project_params (coal EF, hydro retro, rail demand) …")
    base_params.apply_to_scenario(scen)

    # ── 4. Apply SSP-specific parameters ─────────────────────────────────
    log.info("  Applying %s parameters (carbon price, emission caps, growth limits) …",
             scenario_key.upper())
    ssp_mod.apply_to_scenario(scen)

    scen.commit(f"S4 scenario: {cfg['description']}")

    # ── 5. Solve ──────────────────────────────────────────────────────────
    log.info("  Solving with GAMS (MESSAGE) …")

    log.info("  Solving with GAMS (MESSAGE) …")
    t0 = time.perf_counter()
    scen.solve(model="MESSAGE", case=scenario_key.upper())
    elapsed = time.perf_counter() - t0
    log.info("  Solve complete in %.1f s", elapsed)

    # ── 6. Extract IAMC output ────────────────────────────────────────────
    log.info("  Extracting solution variables …")
    iamc_df = solution_to_iamc_via_reporter(scen, cfg["iamc_label"])
    log.info("  IAMC records: %d", len(iamc_df))

    # ── 7. Compute tvp_dbio factors ───────────────────────────────────────
    factor_df = compute_tvp_dbio_intensity_factors(iamc_df)

    # ── 8. Save ───────────────────────────────────────────────────────────
    out = RESULTS_DIR / f"iamc_{scenario_key}.csv"
    iamc_df.to_csv(out, index=False)
    log.info("  Saved → %s", out.name)

    return iamc_df, factor_df


# ── Summary printer ───────────────────────────────────────────────────────────

def summarise(iamc_df: pd.DataFrame, label: str) -> None:
    if iamc_df.empty:
        return
    log.info("  ── %s key metrics ──", label)
    for region in REGIONS:
        rdf = iamc_df[iamc_df["region"] == region]

        def _val(var, yr):
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
    backend: str = "ixmp4",
    dry_run: bool = False,
) -> None:
    if scenarios is None:
        scenarios = list(SCENARIOS.keys())

    # ── Connect to local database ─────────────────────────────────────────
    mp = get_platform(backend)

    # ── Ensure snapshot is available ──────────────────────────────────────
    if not ensure_snapshot(mp, dry_run=dry_run) and not dry_run:
        log.error("Snapshot not available. Run: mix-models fetch snapshot-1")
        sys.exit(1)

    all_iamc:    list[pd.DataFrame] = []
    all_factors: list[pd.DataFrame] = []

    for sc in scenarios:
        if sc not in SCENARIOS:
            log.error("Unknown scenario '%s'. Valid: %s", sc, list(SCENARIOS))
            sys.exit(1)

        iamc_df, factor_df = run_scenario(sc, mp, dry_run=dry_run)

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
        description="REMIND-MAgPIE IPCC Simulation — MESSAGEix (all 5 SSPs)"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        nargs="+",
        default=list(SCENARIOS.keys()),
        help="Scenario(s) to run (default: all five SSPs)",
    )
    parser.add_argument(
        "--backend",
        choices=["ixmp4", "hsqldb"],
        default="ixmp4",
        help="ixmp database backend: ixmp4 (SQLite, no Java) or hsqldb (Java)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Clone and configure scenarios without running GAMS",
    )
    args = parser.parse_args()
    main(scenarios=args.scenario, backend=args.backend, dry_run=args.dry_run)
