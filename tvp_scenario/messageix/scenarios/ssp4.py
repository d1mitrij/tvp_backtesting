"""
ssp4.py — SSP4-6.0 Inequality (polarised ~3 °C pathway)
========================================================
Narrative: stark inequality between/within countries.
Wealthy regions (WEU, urban CPA): high-tech, rapid decarbonisation.
Poor regions (AFR, rural SAS): fossil-dependent, near-zero policy capacity.

KEY SSP4 SIGNAL: within-scenario divergence, not uniform fragmentation.
  WEU carbon price: 100→500 USD/tCO2  (mirrors SSP1 level by 2050)
  AFR carbon price:   8→ 25 USD/tCO2  (limited enforcement capacity)

Project link: Africa Proj_002 hospital serves only 3 000 elite patients,
reflecting the extreme inequality that characterises SSP4 in low-income regions.
Rail_EU_DEV exemplifies the high institutional capacity in wealthy Europe.

Carbon prices [USD/tCO2]:
  AFR: 8→25   CPA/PAS/SAS: 28→120   WEU/EEU/FSU: 100→500   LAM: 20→80
"""

from __future__ import annotations

import pandas as pd

SCENARIO_META = {
    "iamc_label":  "SSP4-6.0",
    "description": "Inequality — polarised 3 °C pathway",
    "rcp":         "6.0",
}

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

CARBON_PRICES: dict[str, dict[int, float]] = {
    # Poor regions — very low price
    "AFR": {2020:   8, 2025:  11, 2030:  14, 2035:  17, 2040:  20, 2045:  23, 2050:  25},
    # Asia — intermediate (urban strict, rural weak; net middle)
    "CPA": {2020:  28, 2025:  45, 2030:  65, 2035:  85, 2040: 100, 2045: 112, 2050: 120},
    "PAS": {2020:  28, 2025:  45, 2030:  65, 2035:  85, 2040: 100, 2045: 112, 2050: 120},
    "SAS": {2020:  28, 2025:  45, 2030:  65, 2035:  85, 2040: 100, 2045: 112, 2050: 120},
    # Wealthy Europe — high price, mirrors SSP1 ambition
    "WEU": {2020: 100, 2025: 170, 2030: 265, 2035: 360, 2040: 430, 2045: 475, 2050: 500},
    "EEU": {2020: 100, 2025: 170, 2030: 265, 2035: 360, 2040: 430, 2045: 475, 2050: 500},
    "FSU": {2020: 100, 2025: 170, 2030: 265, 2035: 360, 2040: 430, 2045: 475, 2050: 500},
    # LATAM — intermediate-loose
    "LAM": {2020:  20, 2025:  32, 2030:  47, 2035:  60, 2040:  70, 2045:  76, 2050:  80},
}

EMISSION_CAPS: dict[str, dict[int, float]] = {
    # Africa: very loose — limited capital, no enforcement
    "AFR": {2020: 1600, 2025: 1800, 2030: 2100, 2035: 2500, 2040: 3000, 2045: 3700, 2050: 4600},
    # Asia: intermediate
    "CPA": {2020: 5200, 2025: 5700, 2030: 6100, 2035: 6500, 2040: 7000, 2045: 7500, 2050: 8100},
    "PAS": {2020: 1100, 2025: 1200, 2030: 1270, 2035: 1350, 2040: 1450, 2045: 1560, 2050: 1680},
    "SAS": {2020:  800, 2025:  880, 2030:  940, 2035: 1000, 2040: 1075, 2045: 1160, 2050: 1250},
    # Europe: strict (polarised — rich regions decarbonise)
    "WEU": {2020: 1950, 2025: 1500, 2030: 1100, 2035:  760, 2040:  490, 2045:  260, 2050:  105},
    "EEU": {2020:  450, 2025:  345, 2030:  250, 2035:  174, 2040:  112, 2045:   60, 2050:   24},
    "FSU": {2020:  650, 2025:  500, 2030:  364, 2035:  252, 2040:  162, 2045:   87, 2050:   35},
    # LATAM: intermediate-loose
    "LAM": {2020:  900, 2025:  950, 2030: 1020, 2035: 1100, 2040: 1200, 2045: 1340, 2050: 1500},
}

FOSSIL_GROWTH: dict[str, dict[str, float]] = {
    "coal_ppl": {
        "AFR": 0.08,  "CPA": 0.05, "PAS": 0.05, "SAS": 0.05,   # lax in poor regions
        "WEU": 0.00, "EEU": 0.00, "FSU": 0.00,                  # no new coal in Europe
        "LAM": 0.04,
    },
    "gas_cc": {
        "AFR": 0.12, "CPA": 0.08, "PAS": 0.08, "SAS": 0.08,
        "WEU": 0.03, "EEU": 0.03, "FSU": 0.05,
        "LAM": 0.10,
    },
}

RENEW_SHARE: dict[str, dict[int, float]] = {
    # Africa: floor only — no capital for ambition
    "AFR": {2020: 0.26, 2025: 0.26, 2030: 0.27, 2035: 0.27, 2040: 0.28, 2045: 0.29, 2050: 0.30},
    # Asia: rapid urban deployment
    "CPA": {2020: 0.26, 2025: 0.33, 2030: 0.42, 2035: 0.51, 2040: 0.60, 2045: 0.68, 2050: 0.75},
    "PAS": {2020: 0.26, 2025: 0.33, 2030: 0.42, 2035: 0.51, 2040: 0.60, 2045: 0.68, 2050: 0.75},
    "SAS": {2020: 0.26, 2025: 0.33, 2030: 0.42, 2035: 0.51, 2040: 0.60, 2045: 0.68, 2050: 0.75},
    # Europe: near-full decarbonisation by 2050
    "WEU": {2020: 0.44, 2025: 0.58, 2030: 0.72, 2035: 0.83, 2040: 0.91, 2045: 0.96, 2050: 0.98},
    "EEU": {2020: 0.42, 2025: 0.56, 2030: 0.69, 2035: 0.80, 2040: 0.89, 2045: 0.95, 2050: 0.97},
    "FSU": {2020: 0.40, 2025: 0.54, 2030: 0.66, 2035: 0.77, 2040: 0.87, 2045: 0.94, 2050: 0.97},
    "LAM": {2020: 0.50, 2025: 0.53, 2030: 0.57, 2035: 0.61, 2040: 0.66, 2045: 0.71, 2050: 0.76},
}


def get_params(years=None):
    from _param_utils import make_tax_df, make_bound_emission_df, make_growth_df
    yrs = years or YEARS
    return {
        "tax_emission":       make_tax_df(CARBON_PRICES, yrs),
        "bound_emission":     make_bound_emission_df(EMISSION_CAPS, yrs),
        "growth_activity_up": make_growth_df(FOSSIL_GROWTH, yrs),
    }


def apply_to_scenario(scen):
    from _param_utils import apply_params
    apply_params(scen, get_params())
