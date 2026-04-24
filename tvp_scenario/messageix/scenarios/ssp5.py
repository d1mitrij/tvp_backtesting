"""
ssp5.py — SSP5-8.5 Fossil-Fueled Development (4–5 °C pathway)
=============================================================
Narrative: rapid global growth driven by fossil fuels and human capital
investment. Strong institutions but no meaningful climate policy. Very high
energy demand; near-total absence of binding CO2 constraints. Renewables
become cost-competitive after 2040 through technology learning, not policy.

Carbon prices [USD/tCO2]: negligible
  AFR: 3→8   CPA/PAS/SAS: 3→8   WEU/EEU/FSU: 8→20   LAM: 4→10

Emission caps [Mt CO2/yr]: essentially non-binding (well above BAU)
  AFR: 3000→32000   CPA: 13000→80000   WEU: 6000→37000   LAM: 2500→27000

Fossil growth: unconstrained; new coal and gas built at scale
"""

from __future__ import annotations

import pandas as pd

SCENARIO_META = {
    "iamc_label":  "SSP5-8.5",
    "description": "Fossil-Fueled Development — 4–5 °C pathway",
    "rcp":         "8.5",
}

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

CARBON_PRICES: dict[str, dict[int, float]] = {
    "AFR": {2020:  3, 2025:  4, 2030:  5, 2035:  6, 2040:  7, 2045:  7, 2050:  8},
    "CPA": {2020:  3, 2025:  4, 2030:  5, 2035:  6, 2040:  7, 2045:  7, 2050:  8},
    "PAS": {2020:  3, 2025:  4, 2030:  5, 2035:  6, 2040:  7, 2045:  7, 2050:  8},
    "SAS": {2020:  3, 2025:  4, 2030:  5, 2035:  6, 2040:  7, 2045:  7, 2050:  8},
    "WEU": {2020:  8, 2025: 11, 2030: 13, 2035: 15, 2040: 17, 2045: 19, 2050: 20},
    "EEU": {2020:  8, 2025: 11, 2030: 13, 2035: 15, 2040: 17, 2045: 19, 2050: 20},
    "FSU": {2020:  8, 2025: 11, 2030: 13, 2035: 15, 2040: 17, 2045: 19, 2050: 20},
    "LAM": {2020:  4, 2025:  5, 2030:  7, 2035:  8, 2040:  9, 2045: 10, 2050: 10},
}

EMISSION_CAPS: dict[str, dict[int, float]] = {
    "AFR": {2020:  3000, 2025:  5000, 2030:  8000, 2035: 12000, 2040: 17000, 2045: 23500, 2050: 32000},
    "CPA": {2020: 13000, 2025: 18500, 2030: 26000, 2035: 36000, 2040: 48000, 2045: 63000, 2050: 80000},
    "PAS": {2020:  2800, 2025:  3900, 2030:  5500, 2035:  7700, 2040: 10200, 2045: 13400, 2050: 17000},
    "SAS": {2020:  2000, 2025:  2800, 2030:  3900, 2035:  5500, 2040:  7300, 2045:  9600, 2050: 12200},
    "WEU": {2020:  6000, 2025:  8500, 2030: 12000, 2035: 16500, 2040: 22000, 2045: 29000, 2050: 37000},
    "EEU": {2020:  1400, 2025:  1950, 2030:  2750, 2035:  3800, 2040:  5000, 2045:  6600, 2050:  8400},
    "FSU": {2020:  2000, 2025:  2800, 2030:  3950, 2035:  5450, 2040:  7200, 2045:  9500, 2050: 12000},
    "LAM": {2020:  2500, 2025:  3800, 2030:  6000, 2035:  9200, 2040: 13500, 2045: 19500, 2050: 27000},
}

FOSSIL_GROWTH: dict[str, dict[str, float]] = {
    "coal_ppl": {n: 0.15 for n in ("AFR", "CPA", "PAS", "SAS", "WEU",
                                    "EEU", "FSU", "LAM")},
    "gas_cc":   {n: 0.20 for n in ("AFR", "CPA", "PAS", "SAS", "WEU",
                                    "EEU", "FSU", "LAM")},
}

RENEW_SHARE: dict[str, dict[int, float]] = {
    "AFR": {2020: 0.18, 2025: 0.18, 2030: 0.19, 2035: 0.19, 2040: 0.20, 2045: 0.21, 2050: 0.22},
    "CPA": {2020: 0.15, 2025: 0.15, 2030: 0.16, 2035: 0.17, 2040: 0.18, 2045: 0.19, 2050: 0.20},
    "PAS": {2020: 0.15, 2025: 0.15, 2030: 0.16, 2035: 0.17, 2040: 0.18, 2045: 0.19, 2050: 0.20},
    "SAS": {2020: 0.15, 2025: 0.15, 2030: 0.16, 2035: 0.17, 2040: 0.18, 2045: 0.19, 2050: 0.20},
    "WEU": {2020: 0.30, 2025: 0.31, 2030: 0.33, 2035: 0.35, 2040: 0.37, 2045: 0.39, 2050: 0.42},
    "EEU": {2020: 0.28, 2025: 0.29, 2030: 0.31, 2035: 0.33, 2040: 0.35, 2045: 0.37, 2050: 0.40},
    "FSU": {2020: 0.26, 2025: 0.27, 2030: 0.29, 2035: 0.31, 2040: 0.33, 2045: 0.35, 2050: 0.38},
    "LAM": {2020: 0.42, 2025: 0.42, 2030: 0.43, 2035: 0.43, 2040: 0.44, 2045: 0.45, 2050: 0.46},
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
