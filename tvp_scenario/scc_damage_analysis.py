"""
Social Cost of Carbon — Damage Cost Breakdown
=============================================
Uses electricity-sector CO2 emissions from all available simulation frameworks
(OSeMOSYS; GCAM and MESSAGEix added when results are ready) to compute annual
damage costs by category for each SSP × region × year (2020–2045).

SCC trajectories
----------------
Central values from IPCC AR6 WG3 Chapter 2 synthesis, calibrated to SSP
warming trajectories. Real growth rate 2.5 %/yr (consistent with DICE-2023R).

  Scenario   2020 SCC  Rationale
  SSP1-1.9   $130/t    Low-end; steep early mitigation limits future exposure
  SSP2-4.5   $190/t    Central US EPA (2023) estimate
  SSP3-7.0   $310/t    High warming → convex damage acceleration
  SSP4-6.0   $260/t    Regional inequality amplifies vulnerability in poor regions
  SSP5-8.5   $420/t    Highest warming path; tail-risk damages dominant

Named damage models
-------------------
Four integrated assessment / damage function models are carried in parallel.
Sector weights are sourced from each model's published calibration:

  GIVE      — Rennert et al. (2022) Nature 610:687–692.  Sector-resolved Monte
               Carlo damage functions for mortality, agriculture, coastal, and
               energy.  Highest central SCC (~$185/t in 2020 at 2.5 % DR).

  FUND      — Anthoff & Tol, FUND 3.9 (2014).  Six-sector reduced-form model
               with explicit water resources and ecosystem modules.

  META-2021 — Dietz et al. (2021) Nature Climate Change 11:557–564.  Meta-
               analytic damage function combining Burke et al. agriculture,
               Carleton et al. mortality, and tipping-point amplification.

  DICE-2023R — Nordhaus (2023).  Single-sector quadratic damage function split
                into sector proxies consistent with WG2 Ch. 16 attribution.

Ensemble mean weights (used when no specific model is requested):

  Category              GIVE    FUND  META   DICE   Ensemble
  Agriculture           10 %    17 %  20 %   20 %    17 %
  Human Health          37 %    28 %  32 %   30 %    32 %
  Water Resources        0 %    16 %  12 %   15 %    11 %
  Coastal / SLR         10 %    11 %   8 %    5 %     9 %
  Ecosystems            37 %    13 %  15 %   15 %    20 %
  Energy Systems         6 %    10 %   8 %   10 %     9 %
  Other                  0 %     5 %   5 %    5 %     4 %

Scope
-----
Only electricity-sector CO2 is monetised here — the narrowest scope consistent
with the tvp_dbio framework. Full-economy SCC would add industry, transport,
agriculture, and LULUCF emissions (typically 4–6× larger for Africa/LATAM).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Shared scenario registry (single source of truth) ────────────────────────
from scenarios_registry import (
    DAMAGE_MODELS,
    SCC_BASE,
    SCC_GROWTH_RATE,
    SCC_BASE_YEAR,
    SCENARIO_ORDER,
    ANALYSIS_YEARS,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
OSEMOSYS_CSV   = ROOT / "osemosys/results/iamc_all_scenarios.csv"
GCAM_CSV       = ROOT / "gcam/results/iamc_all_scenarios.csv"
MESSAGEIX_CSV  = ROOT / "messageix/results/iamc_all_scenarios.csv"
OUT_CSV        = ROOT / "results_scc_damage.csv"
OUT_CSV.parent.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# IPCC nexus weights (Water / Land / Social) — dynamic, derived from AR6
# ---------------------------------------------------------------------------
# Attempt to load the pre-computed nexus weights produced by ipcc_nexus_weights.py.
# If the CSV is absent (weights not yet extracted) the static fallbacks below
# are used and a notice is printed.
_NEXUS_WEIGHTS_CSV = ROOT / "results" / "ipcc_nexus_weights.csv"
_NEXUS_WEIGHTS: pd.DataFrame | None = None

if _NEXUS_WEIGHTS_CSV.exists():
    _NEXUS_WEIGHTS = pd.read_csv(_NEXUS_WEIGHTS_CSV)
    print(f"[OK] IPCC nexus weights loaded from {_NEXUS_WEIGHTS_CSV.name}")
else:
    print(
        "[NOTE] IPCC nexus weights not found. Run:\n"
        "       python ipcc_nexus_weights.py\n"
        "       to extract dynamic Water/Land/Social weights from AR6.\n"
        "       Using static fallback weights for now."
    )

# ---------------------------------------------------------------------------
# Named damage models — imported from scenarios_registry (project root)
# ---------------------------------------------------------------------------
# DAMAGE_MODELS (GIVE / FUND / META-2021 / DICE-2023R) is defined and
# validated in scenarios_registry.py; imported above.

# Ensemble mean (equal-weight average across all named models)
_CATEGORIES = list(next(iter(DAMAGE_MODELS.values())).keys())
_STATIC_DAMAGE_WEIGHTS: dict[str, float] = {
    cat: round(sum(DAMAGE_MODELS[m][cat] for m in DAMAGE_MODELS) / len(DAMAGE_MODELS), 6)
    for cat in _CATEGORIES
}
# Renormalise to absorb floating-point residual
_total = sum(_STATIC_DAMAGE_WEIGHTS.values())
_STATIC_DAMAGE_WEIGHTS = {k: v / _total for k, v in _STATIC_DAMAGE_WEIGHTS.items()}
assert abs(sum(_STATIC_DAMAGE_WEIGHTS.values()) - 1.0) < 1e-9


def get_damage_weights(
    scenario: str,
    year: int,
    region: str = "World",
    damage_model: str | None = None,
) -> dict[str, float]:
    """
    Return damage-category weights for a given (scenario, region, year) triple.

    Parameters
    ----------
    scenario       : SSP label, e.g. "SSP2-4.5"
    year           : analysis year
    region         : AR6 region name (used for dynamic nexus adjustment)
    damage_model   : one of the keys in DAMAGE_MODELS ("GIVE", "FUND",
                     "META-2021", "DICE-2023R"), or None for the ensemble mean.

    When IPCC nexus weights are available (ipcc_nexus_weights.py has been
    run), the Agriculture, Human Health, and Water Resources shares are
    adjusted with AR6-derived shadow-price weights for the specific region.
    The named-model base shares serve as the starting point for that
    adjustment.  Falls back to the static named-model (or ensemble) weights
    when the nexus CSV is absent.
    """
    base = dict(DAMAGE_MODELS[damage_model]) if damage_model else dict(_STATIC_DAMAGE_WEIGHTS)

    if _NEXUS_WEIGHTS is None:
        return base

    from ipcc_nexus_weights import get_dynamic_damage_weights
    return get_dynamic_damage_weights(
        _NEXUS_WEIGHTS,
        scenario=scenario,
        year=year,
        region=region,
        base_water_share=base["Water Resources"],
        base_land_share=base["Agriculture"],
        base_social_share=base["Human Health"],
    )


# ---------------------------------------------------------------------------
# SCC parameters and analysis years — imported from scenarios_registry
# ---------------------------------------------------------------------------
# SCC_BASE, SCC_GROWTH_RATE, SCC_BASE_YEAR, SCENARIO_ORDER, ANALYSIS_YEARS
# are defined in scenarios_registry.py; imported above.

# Ensemble alias (backward-compatible name used elsewhere)
DAMAGE_WEIGHTS = _STATIC_DAMAGE_WEIGHTS

# YEARS: local alias so display code below needs no changes
YEARS = ANALYSIS_YEARS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scc(scenario: str, year: int) -> float:
    """Return SCC (USD / tCO2) for a given scenario and year."""
    base = SCC_BASE[scenario]
    return base * (1 + SCC_GROWTH_RATE) ** (year - SCC_BASE_YEAR)


def load_emissions(csv_path: Path, model_label: str) -> pd.DataFrame | None:
    """Load aggregate electricity CO2 from an IAMC CSV, return long-form df."""
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    # Keep only aggregate electricity CO2 (not sub-tech breakdowns)
    mask = df["variable"] == "Emissions|CO2|Energy|Supply|Electricity"
    df = df[mask & df["year"].isin(YEARS)].copy()
    if df.empty:
        return None
    df["model_label"] = model_label
    # Ensure value is Mt CO2/yr
    assert (df["unit"] == "Mt CO2/yr").all(), f"Unexpected unit in {csv_path}"
    return df[["model_label", "scenario", "region", "year", "value"]].rename(
        columns={"value": "co2_mt"}
    )


def build_damage_table(em: pd.DataFrame) -> pd.DataFrame:
    """Given emissions df, compute annual damage cost by category × damage model.

    Runs each row through every named damage model (GIVE, FUND, META-2021,
    DICE-2023R) plus the ensemble mean ("Ensemble"), producing a row per
    (sim_model, damage_model, scenario, region, year, category).

    Category weights for Agriculture, Human Health, and Water Resources are
    further adjusted by AR6 nexus weights (Water/Land/Social algorithms) when
    ipcc_nexus_weights.py has been run; static named-model weights are used as
    the base for that adjustment.
    """
    models_to_run: list[tuple[str, str | None]] = [
        ("Ensemble",   None),
    ] + [(m, m) for m in DAMAGE_MODELS]

    rows = []
    for _, r in em.iterrows():
        sc  = r["scenario"]
        yr  = int(r["year"])
        co2 = r["co2_mt"]          # Mt CO2/yr

        s = scc(sc, yr)            # USD / tCO2
        # Total damage: Mt CO2/yr × 1e6 t/Mt × USD/t = USD/yr; convert to B USD
        total_B = co2 * 1e6 * s / 1e9  # billion USD / yr

        for dm_label, dm_key in models_to_run:
            weights = get_damage_weights(sc, yr, region=r["region"],
                                         damage_model=dm_key)
            for cat, w in weights.items():
                rows.append({
                    "sim_model":          r["model_label"],
                    "damage_model":       dm_label,
                    "scenario":           sc,
                    "region":             r["region"],
                    "year":               yr,
                    "scc_usd_per_tco2":   round(s, 1),
                    "co2_mt_per_yr":      round(co2, 2),
                    "total_damage_B_usd": round(total_B, 3),
                    "damage_category":    cat,
                    "weight_pct":         round(w * 100, 1),
                    "category_damage_B":  round(total_B * w, 3),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
frames = []

osemosys_em = load_emissions(OSEMOSYS_CSV, "OSeMOSYS|tz-osemosys")
if osemosys_em is not None:
    frames.append(osemosys_em)
    print(f"[OK]      OSeMOSYS : {len(osemosys_em)} emission rows")
else:
    print("[MISSING] OSeMOSYS : run osemosys/run_simulation.py first")

gcam_em = load_emissions(GCAM_CSV, "GCAM|pygcam")
if gcam_em is not None:
    frames.append(gcam_em)
    print(f"[OK]      GCAM     : {len(gcam_em)} emission rows")
else:
    print("[PENDING] GCAM     : gcamdata XML generation still running")

messageix_em = load_emissions(MESSAGEIX_CSV, "MESSAGEix|message-ix")
if messageix_em is not None:
    frames.append(messageix_em)
    print(f"[OK]      MESSAGEix: {len(messageix_em)} emission rows")
else:
    print("[PENDING] MESSAGEix: requires GAMS license + Zenodo snapshot solve")

if not frames:
    print("\nNo results available. Run simulations first.")
    sys.exit(1)

all_em = pd.concat(frames, ignore_index=True)
damage = build_damage_table(all_em)

# ---------------------------------------------------------------------------
# Save full output
# ---------------------------------------------------------------------------
damage.to_csv(OUT_CSV, index=False)
print(f"\nFull table → {OUT_CSV}  ({len(damage)} rows)\n")

# ---------------------------------------------------------------------------
# Display: pivot by damage category for each scenario × model
# ---------------------------------------------------------------------------
# Derive region and scenario ordering from the actual data so no region names
# are hardcoded here.
CATEGORY_ORDER = list(_STATIC_DAMAGE_WEIGHTS.keys())

# Regions present in the loaded data (sorted for stable output)
AVAILABLE_REGIONS = sorted(all_em["region"].unique().tolist())


def show_pivot(sim_model: str, damage_model: str, region: str) -> None:
    sub = damage[
        (damage["sim_model"]    == sim_model) &
        (damage["damage_model"] == damage_model) &
        (damage["region"]       == region)
    ]
    if sub.empty:
        return

    pivot = sub.pivot_table(
        index="damage_category",
        columns=["scenario", "year"],
        values="category_damage_B",
        aggfunc="sum",
    )
    pivot = pivot.reindex(CATEGORY_ORDER)
    pivot = pivot.reindex(
        columns=pd.MultiIndex.from_product([SCENARIO_ORDER, YEARS]),
    )
    pivot = pivot.dropna(axis=1, how="all")

    print("=" * 120)
    print(f"  SIM: {sim_model}  |  DAMAGE MODEL: {damage_model}  |  REGION: {region}")
    print(f"  Annual damage cost by category (billion USD 2020)   [electricity CO2 only]")
    print("=" * 120)
    sc_years = list(pivot.columns)
    current_sc = None
    header1, header2 = "  Category         ", "  ─────────────────"
    for sc, yr in sc_years:
        label = sc if sc != current_sc else " " * len(sc)
        current_sc = sc
        header1 += f"  {yr:4d} "
        header2 += "──────"
    print(header1)
    print(header2)
    for cat in CATEGORY_ORDER:
        if cat not in pivot.index:
            continue
        line = f"  {cat:<17s}"
        for sc, yr in sc_years:
            val = pivot.loc[cat, (sc, yr)]
            line += f"  {val:5.2f}" if not np.isnan(val) else "      "
        print(line)
    print(header2)
    line = f"  {'TOTAL':<17s}"
    for sc, yr in sc_years:
        col_total = sub[
            (sub["scenario"] == sc) & (sub["year"] == yr)
        ]["category_damage_B"].sum()
        line += f"  {col_total:5.2f}"
    print(line)
    print()


# Per-model SCC schedule
print("─" * 80)
print("SCC SCHEDULE (USD 2020 / tCO2)  —  2.5 %/yr real growth from 2020 base")
print("─" * 80)
hdr = f"  {'Scenario':<12}"
for yr in YEARS:
    hdr += f"  {yr:4d}"
print(hdr)
print("  " + "─" * 12 + ("──────" * len(YEARS)))
for sc in SCENARIO_ORDER:
    row = f"  {sc:<12}"
    for yr in YEARS:
        row += f"  {scc(sc, yr):4.0f}"
    print(row)
print()

# CO2 emissions summary before damage split
print("─" * 80)
print("CO2 EMISSIONS  (Mt CO2/yr)  —  Electricity sector only")
print("─" * 80)
for mdl in all_em["model_label"].unique():
    sub = all_em[all_em["model_label"] == mdl]
    pivot_em = sub.pivot_table(
        index="region",
        columns=["scenario", "year"],
        values="co2_mt",
        aggfunc="sum",
    )
    pivot_em = pivot_em.reindex(
        columns=pd.MultiIndex.from_product([SCENARIO_ORDER, YEARS]),
    ).dropna(axis=1, how="all")

    print(f"\n  {mdl}")
    sc_years = list(pivot_em.columns)
    prev_sc = None
    hdr_line = "  Region    "
    for sc, yr in sc_years:
        tag = sc[:5] if sc != prev_sc else "     "
        prev_sc = sc
        hdr_line += f"  {yr:4d}"
    print(hdr_line)
    for reg in sorted(pivot_em.index.tolist()):
        line = f"  {reg:<10}"
        for sc, yr in sc_years:
            val = pivot_em.loc[reg, (sc, yr)]
            line += f"  {val:5.0f}" if not np.isnan(val) else "      "
        print(line)

print()

# Damage breakdown tables: OSeMOSYS Ensemble first, then per damage model
first_sim = all_em["model_label"].iloc[0]
for dm in ["Ensemble"] + list(DAMAGE_MODELS.keys()):
    for reg in AVAILABLE_REGIONS:
        show_pivot(first_sim, dm, reg)

# Cross-scenario total damage comparison (all sim models × all damage models �� all regions)
print("─" * 80)
print("TOTAL DAMAGE COST ACROSS ALL REGIONS  (billion USD 2020 / yr)")
print("─" * 80)
summary = (
    damage.groupby(["sim_model", "damage_model", "scenario", "year"])["category_damage_B"]
    .sum()
    .reset_index()
    .rename(columns={"category_damage_B": "total_damage_B"})
)
pivot_sum = summary.pivot_table(
    index=["sim_model", "damage_model", "scenario"],
    columns="year",
    values="total_damage_B",
)
pivot_sum = pivot_sum.reindex(columns=YEARS)
with pd.option_context("display.float_format", "{:8.1f}".format,
                        "display.width", 140,
                        "display.max_columns", 20):
    print(pivot_sum.to_string())
print()

# Model uncertainty note
n_sim_models = all_em["model_label"].nunique()
if n_sim_models == 1:
    print("NOTE: Only OSeMOSYS results available.")
    print("      GCAM    — gcamdata XML generation running in background; watcher")
    print("                will auto-launch run_simulation.py when complete.")
    print("      MESSAGEix — requires GAMS license + Zenodo snapshot solve.")
    print("      Re-run this script after each model completes to add its results.")
