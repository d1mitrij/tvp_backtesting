"""
ssp1.py — SSP1-1.9 Sustainability (1.5 °C pathway)
===================================================
Narrative: rapid global cooperation, low resource intensity, strong climate
governance. Very high carbon prices force near-complete decarbonisation by
2035–2040. New coal investment is prohibited; gas declines sharply.

Project links:
  Rail_EU_DEV + hospital Proj_003 (WEU): institutional capacity for ambition.
  Hospital Proj_001 (LAM): social investment consistent with SSP1 equity focus.
  Hydro retrofits deployed early and fully in all regions.

Carbon prices [USD/tCO2]:  (applied via `tax_emission`)
  AFR: 80→500   CPA/PAS/SAS: 65→400   WEU/EEU/FSU: 120→800   LAM: 80→400

Emission caps [Mt CO2/yr]:  (applied via `bound_emission`)
  AFR: 950→20   CPA: 4100→60   WEU: 1950→12   LAM: 680→8

Fossil technology growth upper bound [fraction per 5-year period]:
  coal_ppl: 0.0 in all regions (no new coal)
  gas_cc:   0.05 max annual growth (capacity reduction allowed)
"""

from __future__ import annotations

import pandas as pd

SCENARIO_META = {
    "iamc_label":  "SSP1-1.9",
    "description": "Sustainability — 1.5 °C pathway",
    "rcp":         "1.9",
}

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

# ── Carbon prices [USD/tCO2] ──────────────────────────────────────────────────
CARBON_PRICES: dict[str, dict[int, float]] = {
    "AFR": {2020:  80, 2025: 130, 2030: 210, 2035: 320, 2040: 440, 2045: 500, 2050: 500},
    "CPA": {2020:  65, 2025: 110, 2030: 180, 2035: 270, 2040: 360, 2045: 400, 2050: 400},
    "PAS": {2020:  65, 2025: 110, 2030: 180, 2035: 270, 2040: 360, 2045: 400, 2050: 400},
    "SAS": {2020:  65, 2025: 110, 2030: 180, 2035: 270, 2040: 360, 2045: 400, 2050: 400},
    "WEU": {2020: 120, 2025: 200, 2030: 330, 2035: 500, 2040: 660, 2045: 800, 2050: 800},
    "EEU": {2020: 120, 2025: 200, 2030: 330, 2035: 500, 2040: 660, 2045: 800, 2050: 800},
    "FSU": {2020: 120, 2025: 200, 2030: 330, 2035: 500, 2040: 660, 2045: 800, 2050: 800},
    "LAM": {2020:  80, 2025: 130, 2030: 210, 2035: 300, 2040: 380, 2045: 400, 2050: 400},
}

# ── Emission caps [Mt CO2/yr] ─────────────────────────────────────────────────
EMISSION_CAPS: dict[str, dict[int, float]] = {
    "AFR": {2020:  950, 2025:  750, 2030:  520, 2035:  310, 2040:  155, 2045:   60, 2050:  20},
    "CPA": {2020: 4100, 2025: 3150, 2030: 2120, 2035: 1280, 2040:  620, 2045:  220, 2050:  60},
    "PAS": {2020:  800, 2025:  620, 2030:  420, 2035:  250, 2040:  120, 2045:   45, 2050:  12},
    "SAS": {2020:  600, 2025:  460, 2030:  310, 2035:  185, 2040:   90, 2045:   32, 2050:   8},
    "WEU": {2020: 1950, 2025: 1330, 2030:  800, 2035:  420, 2040:  175, 2045:   55, 2050:  12},
    "EEU": {2020:  500, 2025:  330, 2030:  195, 2035:  100, 2040:   42, 2045:   14, 2050:   4},
    "FSU": {2020:  700, 2025:  470, 2030:  275, 2035:  140, 2040:   58, 2045:   20, 2050:   5},
    "LAM": {2020:  680, 2025:  500, 2030:  340, 2035:  190, 2040:   88, 2045:   30, 2050:   8},
}

# ── Fossil technology maximum growth rate [fraction/period] ──────────────────
# 0.0 = no new builds; negative values = forced retirement
FOSSIL_GROWTH: dict[str, dict[str, float]] = {
    "coal_ppl": {n: 0.00 for n in CARBON_PRICES},   # no new coal in SSP1
    "gas_cc":   {n: 0.05 for n in CARBON_PRICES},   # limited gas growth
}

# ── Minimum renewable electricity share ──────────────────────────────────────
# Used to set `share_commodity_lo` in MESSAGEix (fraction of electricity)
RENEW_SHARE: dict[str, dict[int, float]] = {
    "AFR": {2020: 0.36, 2025: 0.51, 2030: 0.66, 2035: 0.79, 2040: 0.89, 2045: 0.95, 2050: 0.98},
    "CPA": {2020: 0.26, 2025: 0.41, 2030: 0.59, 2035: 0.73, 2040: 0.85, 2045: 0.93, 2050: 0.97},
    "PAS": {2020: 0.26, 2025: 0.41, 2030: 0.59, 2035: 0.73, 2040: 0.85, 2045: 0.93, 2050: 0.97},
    "SAS": {2020: 0.26, 2025: 0.41, 2030: 0.59, 2035: 0.73, 2040: 0.85, 2045: 0.93, 2050: 0.97},
    "WEU": {2020: 0.44, 2025: 0.60, 2030: 0.74, 2035: 0.86, 2040: 0.93, 2045: 0.97, 2050: 0.99},
    "EEU": {2020: 0.40, 2025: 0.56, 2030: 0.70, 2035: 0.82, 2040: 0.91, 2045: 0.96, 2050: 0.99},
    "FSU": {2020: 0.38, 2025: 0.52, 2030: 0.66, 2035: 0.78, 2040: 0.89, 2045: 0.95, 2050: 0.98},
    "LAM": {2020: 0.52, 2025: 0.65, 2030: 0.76, 2035: 0.85, 2040: 0.92, 2045: 0.96, 2050: 0.99},
}


def get_params(years: list[int] | None = None) -> dict[str, pd.DataFrame]:
    """
    Return MESSAGEix-ready parameter DataFrames for SSP1-1.9.

    Returns
    -------
    dict mapping MESSAGEix parameter name → pd.DataFrame
    """
    from _param_utils import make_tax_df, make_bound_emission_df, make_growth_df
    yrs = years or YEARS
    return {
        "tax_emission":    make_tax_df(CARBON_PRICES, yrs),
        "bound_emission":  make_bound_emission_df(EMISSION_CAPS, yrs),
        "growth_activity_up": make_growth_df(FOSSIL_GROWTH, yrs),
    }


def apply_to_scenario(scen) -> None:
    """Apply SSP1-1.9 parameters to a checked-out MESSAGEix scenario."""
    from _param_utils import apply_params
    apply_params(scen, get_params())
