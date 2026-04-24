#!/usr/bin/env python3
"""
run_simulation.py
=================
REMIND-MAgPIE IPCC Scenario Simulation via tz-osemosys (OSeMOSYS / linopy / HiGHS)

Model parameters are derived from the project finance CSVs via derive_parameters.py
(see: modeled_input_data/). Region names match the CSV values exactly:
Africa, Asia, Europe, LATAM.

Workflow
--------
1. derive_parameters.py reads hydro/hospital/rail CSVs → region-specific
   coal emission factors and hydro-retrofit capacities.
2. Model.from_yaml() merges base.yaml + ssp*.yaml into a validated RunSpec.
3. HiGHS LP solver optimises total discounted system cost.
4. iamc_bridge.py converts the xr.Dataset solution to IAMC-format CSV.
5. tvp_dbio intensity adjustment factors are saved for downstream use.

Usage
-----
    python run_simulation.py                          # all 5 SSPs
    python run_simulation.py --scenario ssp1 ssp5    # two scenarios
    python run_simulation.py --scenario ssp2 --solver highs

Outputs (written to results/)
------------------------------
    results/iamc_<scenario>.csv          IAMC long-form per scenario
    results/iamc_all_scenarios.csv       Combined across all scenarios
    results/tvpdbio_intensity_factors.csv tvp_dbio GHG/employment adjustment ratios
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
MODEL_DIR   = HERE / "model"
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
# yaml (OSeMOSYS-specific model path) — added here.
SCENARIOS = {
    key: {
        **{k: v for k, v in SSP_REGISTRY[key].items()
           if k in ("iamc_label", "description", "rcp")},
        "yaml": MODEL_DIR / f"{key}.yaml",
    }
    for key in ("ssp1", "ssp2", "ssp3", "ssp4", "ssp5")
}

# Region names must match CSV data exactly
REGIONS = ["Africa", "Asia", "Europe", "LATAM"]


def run_scenario(
    scenario_key: str,
    solver: str = "highs",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, solve, and convert one OSeMOSYS scenario to IAMC + intensity factors."""
    from tz.osemosys import Model
    from iamc_bridge import solution_to_iamc, compute_tvp_dbio_intensity_factors
    from derive_parameters import load_project_data

    cfg = SCENARIOS[scenario_key]
    log.info("=" * 70)
    log.info(f"Scenario : {scenario_key.upper()}  |  {cfg['iamc_label']}")
    log.info(f"          {cfg['description']}")
    log.info("=" * 70)

    # ── 1. Show derived parameters for traceability ───────────────────────────
    proj_params = load_project_data()
    log.info("  Project-derived parameters (from modeled_input_data/):")
    for r in REGIONS:
        p = proj_params[r]
        log.info(
            f"    {r:8s}: coal_ef={p.coal_ef_mt_pj:.4f} Mt CO2/PJ, "
            f"hydro_retro_max={p.hydro_retro_gw:.3f} GW"
            + (f", rail_elec={p.rail_elec_demand_pj:.4f} PJ/yr"
               if p.rail_elec_demand_pj > 0 else "")
        )

    # ── 2. Load model ─────────────────────────────────────────────────────────
    log.info("  Loading YAML model files …")
    t0 = time.perf_counter()
    model = Model.from_yaml(
        str(MODEL_DIR / "base.yaml"),
        str(cfg["yaml"]),
    )
    log.info(
        f"  Model loaded in {time.perf_counter()-t0:.1f}s  "
        f"({len(model.regions)} regions, {len(model.technologies)} technologies, "
        f"{len(model.time_definition.years)} years)"
    )

    # ── 3. Solve ──────────────────────────────────────────────────────────────
    log.info(f"  Solving with {solver.upper()} …")
    t1 = time.perf_counter()
    status, termination = model.solve(solver_name=solver)
    elapsed = time.perf_counter() - t1
    log.info(
        f"  Solver: status={status}  termination={termination}  "
        f"elapsed={elapsed:.1f}s"
    )

    if status != "ok":
        log.error(f"  No optimal solution for {scenario_key}. Skipping.")
        return pd.DataFrame(), pd.DataFrame()

    # ── 4. Convert to IAMC ───────────────────────────────────────────────────
    iamc_df = solution_to_iamc(
        solution=model.solution,
        scenario=cfg["iamc_label"],
        regions=REGIONS,
    )
    log.info(f"  IAMC records: {len(iamc_df):,}")

    # ── 5. Compute tvp_dbio factors ───────────────────────────────────────────
    factor_df = compute_tvp_dbio_intensity_factors(iamc_df)

    # ── 6. Save ───────────────────────────────────────────────────────────────
    out = RESULTS_DIR / f"iamc_{scenario_key}.csv"
    iamc_df.to_csv(out, index=False)
    log.info(f"  Saved → {out.name}")

    return iamc_df, factor_df


def summarise(iamc_df: pd.DataFrame, label: str) -> None:
    """Print a compact energy + emissions summary."""
    if iamc_df.empty:
        return
    log.info(f"  ── {label} key metrics ──")
    for region in REGIONS:
        rdf = iamc_df[iamc_df["region"] == region]

        def _val(var, yr):
            v = rdf[(rdf["variable"] == var) & (rdf["year"] == yr)]["value"]
            return v.iloc[0] if len(v) else 0.0

        e20 = _val("Secondary Energy|Electricity", 2020)
        e50 = _val("Secondary Energy|Electricity", 2050)
        c20 = _val("Emissions|CO2|Energy|Supply|Electricity", 2020)
        c50 = _val("Emissions|CO2|Energy|Supply|Electricity", 2050)
        s50 = _val("Capacity|Electricity|Solar", 2050)
        w50 = _val("Capacity|Electricity|Wind", 2050)
        log.info(
            f"    {region:7s}: elec {e20:.0f}→{e50:.0f} EJ/yr  "
            f"CO2 {c20:.0f}→{c50:.0f} Mt/yr  "
            f"Solar/Wind 2050: {s50:.0f}/{w50:.0f} GW"
        )


def main(scenarios: list[str] | None = None, solver: str = "highs") -> None:
    if scenarios is None:
        scenarios = list(SCENARIOS.keys())

    all_iamc: list[pd.DataFrame]    = []
    all_factors: list[pd.DataFrame] = []

    for sc in scenarios:
        if sc not in SCENARIOS:
            log.error(f"Unknown scenario '{sc}'. Valid: {list(SCENARIOS)}")
            sys.exit(1)

        iamc_df, factor_df = run_scenario(sc, solver=solver)

        if not iamc_df.empty:
            summarise(iamc_df, SCENARIOS[sc]["iamc_label"])
            all_iamc.append(iamc_df)
        if not factor_df.empty:
            all_factors.append(factor_df)

    # ── Write combined outputs ────────────────────────────────────────────────
    if all_iamc:
        combined = pd.concat(all_iamc, ignore_index=True)
        out = RESULTS_DIR / "iamc_all_scenarios.csv"
        combined.to_csv(out, index=False)
        log.info(f"\nCombined IAMC output ({len(combined):,} rows) → {out.name}")

    if all_factors:
        factors = pd.concat(all_factors, ignore_index=True)
        out = RESULTS_DIR / "tvpdbio_intensity_factors.csv"
        factors.to_csv(out, index=False)
        log.info(f"tvp_dbio factors ({len(factors):,} rows) → {out.name}")

        log.info("\n  ── adj_ratio_ghg (Energy_Utilities GHG intensity vs 2020) ──")
        pivot = factors.pivot_table(
            index=["scenario", "region"], columns="year",
            values="adj_ratio_ghg",
        ).round(3)
        log.info(f"\n{pivot.to_string()}")

    log.info("\nSimulation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="REMIND-MAgPIE IPCC Scenario Simulation — OSeMOSYS (all 5 SSPs)"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        nargs="+",
        default=list(SCENARIOS.keys()),
        help="Scenario(s) to run (default: all five SSPs)",
    )
    parser.add_argument(
        "--solver",
        default="highs",
        help="LP solver name passed to linopy (default: highs)",
    )
    args = parser.parse_args()
    main(scenarios=args.scenario, solver=args.solver)
