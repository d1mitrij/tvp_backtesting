"""
_param_utils.py — Shared helpers for building MESSAGEix parameter DataFrames
=============================================================================
All scenario modules import from here to build consistently structured
DataFrames that can be passed directly to `scenario.add_par()`.
"""

from __future__ import annotations

import pandas as pd


def make_tax_df(
    carbon_prices: dict[str, dict[int, float]],
    years: list[int],
    emission_type: str = "TCE",
    tec_type: str = "all",
    unit: str = "USD/tCO2",
) -> pd.DataFrame:
    """
    Build the MESSAGEix `tax_emission` DataFrame.

    Parameters
    ----------
    carbon_prices : {node: {year: price_usd_per_tco2}}
    years         : time periods to include
    emission_type : MESSAGEix emission type string (default 'TCE')
    tec_type      : technology type filter (default 'all')
    unit          : unit string for the DataFrame

    Returns
    -------
    pd.DataFrame with columns:
        node, type_emission, type_tec, type_year, value, unit
    """
    rows = []
    for node, price_path in carbon_prices.items():
        for yr in years:
            price = price_path.get(yr)
            if price is None:
                continue
            rows.append({
                "node":           node,
                "type_emission":  emission_type,
                "type_tec":       tec_type,
                "type_year":      yr,
                "value":          float(price),
                "unit":           unit,
            })
    return pd.DataFrame(rows)


def make_bound_emission_df(
    emission_caps: dict[str, dict[int, float]],
    years: list[int],
    emission_type: str = "TCE",
    tec_type: str = "all",
    unit: str = "Mt CO2/yr",
) -> pd.DataFrame:
    """
    Build the MESSAGEix `bound_emission` DataFrame (annual emission cap).

    Parameters
    ----------
    emission_caps : {node: {year: cap_mt_co2_yr}}
    """
    rows = []
    for node, cap_path in emission_caps.items():
        for yr in years:
            cap = cap_path.get(yr)
            if cap is None:
                continue
            rows.append({
                "node":           node,
                "type_emission":  emission_type,
                "type_tec":       tec_type,
                "type_year":      yr,
                "bound":          "up",
                "value":          float(cap),
                "unit":           unit,
            })
    return pd.DataFrame(rows)


def make_growth_df(
    fossil_growth: dict[str, dict[str, float]],
    years: list[int],
    time: str = "year",
    unit: str = "-",
) -> pd.DataFrame:
    """
    Build the MESSAGEix `growth_activity_up` DataFrame.

    Sets the maximum permitted annual growth rate for fossil technology activity
    per node. A value of 0.0 prevents any new investment; negative values would
    force retirement (use with care).

    Parameters
    ----------
    fossil_growth : {technology: {node: max_growth_fraction}}
    """
    rows = []
    for technology, node_rates in fossil_growth.items():
        for node, rate in node_rates.items():
            for yr in years:
                rows.append({
                    "node_loc":    node,
                    "technology":  technology,
                    "year_act":    yr,
                    "time":        time,
                    "value":       float(rate),
                    "unit":        unit,
                })
    return pd.DataFrame(rows)


def apply_params(scen, params: dict[str, pd.DataFrame]) -> None:
    """
    Apply a dict of {parameter_name: DataFrame} to a checked-out MESSAGEix scenario.

    Skips any empty DataFrames silently.

    Parameters
    ----------
    scen   : message_ix.Scenario (must be in check_out() state)
    params : dict from ssp{N}.get_params()
    """
    for param_name, df in params.items():
        if df is None or df.empty:
            continue
        scen.add_par(param_name, df)
