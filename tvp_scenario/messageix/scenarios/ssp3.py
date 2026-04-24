"""
ssp3.py — SSP3-7.0 Regional Rivalry (3–4 °C pathway)
======================================================
Narrative: fragmented world, weak international governance, high barriers
to technology transfer. All regions show weak climate policy; fossil fuels
dominate throughout. Very loose emission caps; low carbon prices.

Carbon prices [USD/tCO2]:
  AFR: 5→15   CPA/PAS/SAS: 5→15   WEU/EEU/FSU: 18→60   LAM: 6→20

Emission caps [Mt CO2/yr]: very loose (above BAU to avoid infeasibility)
  AFR: 2100→9400   CPA: 8500→38500   WEU: 4000→8000   LAM: 1600→6900

Fossil growth: unconstrained new investment everywhere
"""

from __future__ import annotations

import pandas as pd

SCENARIO_META = {
    "iamc_label":  "SSP3-7.0",
    "description": "Regional Rivalry — 3–4 °C pathway",
    "rcp":         "7.0",
}

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

CARBON_PRICES: dict[str, dict[int, float]] = {
    "AFR": {2020:  5, 2025:  7, 2030:  9, 2035: 11, 2040: 13, 2045: 14, 2050: 15},
    "CPA": {2020:  5, 2025:  7, 2030:  9, 2035: 11, 2040: 13, 2045: 14, 2050: 15},
    "PAS": {2020:  5, 2025:  7, 2030:  9, 2035: 11, 2040: 13, 2045: 14, 2050: 15},
    "SAS": {2020:  5, 2025:  7, 2030:  9, 2035: 11, 2040: 13, 2045: 14, 2050: 15},
    "WEU": {2020: 18, 2025: 25, 2030: 33, 2035: 42, 2040: 50, 2045: 56, 2050: 60},
    "EEU": {2020: 18, 2025: 25, 2030: 33, 2035: 42, 2040: 50, 2045: 56, 2050: 60},
    "FSU": {2020: 18, 2025: 25, 2030: 33, 2035: 42, 2040: 50, 2045: 56, 2050: 60},
    "LAM": {2020:  6, 2025:  9, 2030: 12, 2035: 15, 2040: 17, 2045: 19, 2050: 20},
}

EMISSION_CAPS: dict[str, dict[int, float]] = {
    "AFR": {2020:  2100, 2025:  2700, 2030:  3500, 2035:  4500, 2040:  5800, 2045:  7400, 2050:  9400},
    "CPA": {2020:  8500, 2025: 11300, 2030: 14700, 2035: 18900, 2040: 24100, 2045: 30500, 2050: 38500},
    "PAS": {2020:  1800, 2025:  2400, 2030:  3100, 2035:  4000, 2040:  5100, 2045:  6400, 2050:  8100},
    "SAS": {2020:  1300, 2025:  1700, 2030:  2200, 2035:  2800, 2040:  3600, 2045:  4600, 2050:  5800},
    "WEU": {2020:  4000, 2025:  4300, 2030:  4800, 2035:  5400, 2040:  6100, 2045:  7000, 2050:  8000},
    "EEU": {2020:   900, 2025:   980, 2030:  1100, 2035:  1230, 2040:  1390, 2045:  1600, 2050:  1820},
    "FSU": {2020:  1300, 2025:  1410, 2030:  1580, 2035:  1770, 2040:  2000, 2045:  2300, 2050:  2620},
    "LAM": {2020:  1600, 2025:  2000, 2030:  2600, 2035:  3300, 2040:  4200, 2045:  5400, 2050:  6900},
}

FOSSIL_GROWTH: dict[str, dict[str, float]] = {
    "coal_ppl": {n: 0.10 for n in ("AFR", "CPA", "PAS", "SAS", "WEU",
                                    "EEU", "FSU", "LAM")},
    "gas_cc":   {n: 0.15 for n in ("AFR", "CPA", "PAS", "SAS", "WEU",
                                    "EEU", "FSU", "LAM")},
}

RENEW_SHARE: dict[str, dict[int, float]] = {
    "AFR": {2020: 0.26, 2025: 0.26, 2030: 0.27, 2035: 0.28, 2040: 0.29, 2045: 0.30, 2050: 0.31},
    "CPA": {2020: 0.18, 2025: 0.19, 2030: 0.20, 2035: 0.21, 2040: 0.23, 2045: 0.25, 2050: 0.27},
    "PAS": {2020: 0.18, 2025: 0.19, 2030: 0.20, 2035: 0.21, 2040: 0.23, 2045: 0.25, 2050: 0.27},
    "SAS": {2020: 0.18, 2025: 0.19, 2030: 0.20, 2035: 0.21, 2040: 0.23, 2045: 0.25, 2050: 0.27},
    "WEU": {2020: 0.36, 2025: 0.38, 2030: 0.40, 2035: 0.42, 2040: 0.45, 2045: 0.47, 2050: 0.50},
    "EEU": {2020: 0.34, 2025: 0.36, 2030: 0.38, 2035: 0.40, 2040: 0.43, 2045: 0.45, 2050: 0.48},
    "FSU": {2020: 0.32, 2025: 0.34, 2030: 0.36, 2035: 0.38, 2040: 0.41, 2045: 0.43, 2050: 0.46},
    "LAM": {2020: 0.42, 2025: 0.42, 2030: 0.43, 2035: 0.44, 2040: 0.45, 2045: 0.46, 2050: 0.47},
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
