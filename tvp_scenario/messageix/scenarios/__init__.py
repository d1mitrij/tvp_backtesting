"""
scenarios/ — MESSAGEix parameter packages for each SSP.

Each module exports:
    SCENARIO_META : dict   IAMC label, description, rcp
    CARBON_PRICES : dict   {node: {year: USD/tCO2}}
    EMISSION_CAPS : dict   {node: {year: Mt CO2/yr}}
    FOSSIL_GROWTH : dict   {technology: {node: max_growth_fraction}}
    RENEW_SHARE   : dict   {node: {year: min_renewable_fraction}}

And a function:
    get_params(years) → dict[str, pd.DataFrame]
        Returns MESSAGEix-ready DataFrames keyed by parameter name.
"""

from . import ssp1, ssp2, ssp3, ssp4, ssp5

ALL = {
    "ssp1": ssp1,
    "ssp2": ssp2,
    "ssp3": ssp3,
    "ssp4": ssp4,
    "ssp5": ssp5,
}

__all__ = ["ALL", "ssp1", "ssp2", "ssp3", "ssp4", "ssp5"]
