"""
ssp2.py — SSP2-4.5 Middle of the Road (~2 °C pathway)
======================================================
Narrative: current socioeconomic trends continue, uneven progress.
Carbon prices rise moderately; renewable transition is market-led.
New coal is still possible in early years in developing regions.

Carbon prices [USD/tCO2]:
  AFR: 35→200   CPA/PAS/SAS: 30→175   WEU/EEU/FSU: 75→350   LAM: 40→200

Emission caps [Mt CO2/yr]:
  AFR: 1000→410   CPA: 4200→1900   WEU: 1950→210   LAM: 680→340

Fossil growth [fraction/period]:
  coal_ppl: 0.03 (modest new coal allowed in early periods, developing regions)
  gas_cc:   0.10
"""

from __future__ import annotations

import pandas as pd

SCENARIO_META = {
    "iamc_label":  "SSP2-4.5",
    "description": "Middle of the Road — ~2 °C pathway",
    "rcp":         "4.5",
}

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

CARBON_PRICES: dict[str, dict[int, float]] = {
    "AFR": {2020:  35, 2025:  55, 2030:  85, 2035: 120, 2040: 155, 2045: 180, 2050: 200},
    "CPA": {2020:  30, 2025:  48, 2030:  75, 2035: 108, 2040: 138, 2045: 160, 2050: 175},
    "PAS": {2020:  30, 2025:  48, 2030:  75, 2035: 108, 2040: 138, 2045: 160, 2050: 175},
    "SAS": {2020:  30, 2025:  48, 2030:  75, 2035: 108, 2040: 138, 2045: 160, 2050: 175},
    "WEU": {2020:  75, 2025: 120, 2030: 185, 2035: 260, 2040: 305, 2045: 330, 2050: 350},
    "EEU": {2020:  75, 2025: 120, 2030: 185, 2035: 260, 2040: 305, 2045: 330, 2050: 350},
    "FSU": {2020:  75, 2025: 120, 2030: 185, 2035: 260, 2040: 305, 2045: 330, 2050: 350},
    "LAM": {2020:  40, 2025:  63, 2030:  98, 2035: 138, 2040: 170, 2045: 188, 2050: 200},
}

EMISSION_CAPS: dict[str, dict[int, float]] = {
    "AFR": {2020: 1000, 2025:  950, 2030:  880, 2035:  790, 2040:  670, 2045:  540, 2050: 410},
    "CPA": {2020: 4200, 2025: 4250, 2030: 4050, 2035: 3650, 2040: 3100, 2045: 2500, 2050: 1900},
    "PAS": {2020:  900, 2025:  880, 2030:  840, 2035:  760, 2040:  640, 2045:  510, 2050: 390},
    "SAS": {2020:  700, 2025:  680, 2030:  640, 2035:  580, 2040:  490, 2045:  390, 2050: 300},
    "WEU": {2020: 1950, 2025: 1600, 2030: 1260, 2035:  950, 2040:  680, 2045:  430, 2050: 210},
    "EEU": {2020:  450, 2025:  370, 2030:  290, 2035:  220, 2040:  158, 2045:  100, 2050:  48},
    "FSU": {2020:  650, 2025:  535, 2030:  415, 2035:  315, 2040:  225, 2045:  143, 2050:  70},
    "LAM": {2020:  680, 2025:  660, 2030:  630, 2035:  580, 2040:  510, 2045:  430, 2050: 340},
}

FOSSIL_GROWTH: dict[str, dict[str, float]] = {
    "coal_ppl": {"AFR": 0.03, "CPA": 0.03, "PAS": 0.03, "SAS": 0.03,
                 "WEU": 0.00, "EEU": 0.00, "FSU": 0.01, "LAM": 0.02},
    "gas_cc":   {n: 0.10 for n in ("AFR", "CPA", "PAS", "SAS", "WEU",
                                    "EEU", "FSU", "LAM")},
}

RENEW_SHARE: dict[str, dict[int, float]] = {
    "AFR": {2020: 0.30, 2025: 0.36, 2030: 0.43, 2035: 0.51, 2040: 0.59, 2045: 0.67, 2050: 0.75},
    "CPA": {2020: 0.22, 2025: 0.28, 2030: 0.37, 2035: 0.45, 2040: 0.54, 2045: 0.63, 2050: 0.72},
    "PAS": {2020: 0.22, 2025: 0.28, 2030: 0.37, 2035: 0.45, 2040: 0.54, 2045: 0.63, 2050: 0.72},
    "SAS": {2020: 0.22, 2025: 0.28, 2030: 0.37, 2035: 0.45, 2040: 0.54, 2045: 0.63, 2050: 0.72},
    "WEU": {2020: 0.40, 2025: 0.48, 2030: 0.57, 2035: 0.65, 2040: 0.73, 2045: 0.82, 2050: 0.89},
    "EEU": {2020: 0.38, 2025: 0.45, 2030: 0.53, 2035: 0.62, 2040: 0.70, 2045: 0.78, 2050: 0.86},
    "FSU": {2020: 0.36, 2025: 0.43, 2030: 0.51, 2035: 0.59, 2040: 0.67, 2045: 0.75, 2050: 0.83},
    "LAM": {2020: 0.47, 2025: 0.52, 2030: 0.58, 2035: 0.64, 2040: 0.70, 2045: 0.76, 2050: 0.83},
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
