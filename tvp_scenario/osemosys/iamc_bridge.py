"""
iamc_bridge.py
==============
Converts tz-osemosys solution (xr.Dataset) into IAMC-format DataFrames and
computes time-varying tvp_dbio intensity adjustment factors for the
Energy_Utilities sector.

Solution coordinate names (tz-osemosys convention)
---------------------------------------------------
ProductionByTechnology   dims: (REGION, TECHNOLOGY, YEAR, FUEL, TIMESLICE)  [PJ/yr]
GrossCapacity            dims: (REGION, TECHNOLOGY, YEAR)                    [GW]
NewCapacity              dims: (REGION, TECHNOLOGY, YEAR)                    [GW]
AnnualTechnologyEmission dims: (REGION, TECHNOLOGY, YEAR, EMISSION)          [Mt CO2/yr]
CapitalInvestment        dims: (REGION, TECHNOLOGY, YEAR)                    [M$/yr]

IAMC variable mapping
---------------------
ProductionByTechnology[COAL_PP]   → Secondary Energy|Electricity|Coal   [EJ/yr]
ProductionByTechnology[GAS_PP]    → Secondary Energy|Electricity|Gas    [EJ/yr]
ProductionByTechnology[HYDRO_*]   → Secondary Energy|Electricity|Hydro  [EJ/yr]
ProductionByTechnology[SOLAR_PV]  → Secondary Energy|Electricity|Solar  [EJ/yr]
ProductionByTechnology[WIND]      → Secondary Energy|Electricity|Wind   [EJ/yr]
sum all above                     → Secondary Energy|Electricity         [EJ/yr]
AnnualTechnologyEmission (fossil) → Emissions|CO2|Energy|Supply|Electricity [Mt CO2/yr]
GrossCapacity                     → Capacity|Electricity|<tech>          [GW]
NewCapacity                       → Capacity Additions|Electricity|<tech>[GW]
CapitalInvestment                 → Investment|Energy Supply|Electricity|<tech> [M$/yr]

tvp_dbio adjustment factor
---------------------------
adj_ratio_ghg(r, t) = grid_intensity(r, t) / grid_intensity(r, base_year)
where grid_intensity = Emissions|CO2|Energy / Secondary Energy|Electricity [Mt CO2/EJ]
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import xarray as xr

# ── Technology → IAMC label ───────────────────────────────────────────────────
TECH_IAMC = {
    "COAL_PP":     "Coal",
    "GAS_PP":      "Gas",
    "HYDRO_EXIST": "Hydro",
    "HYDRO_RETRO": "Hydro",
    "SOLAR_PV":    "Solar",
    "WIND":        "Wind",
}

FOSSIL_TECHS = {"COAL_PP", "GAS_PP"}

IAMC_MODEL   = "OSeMOSYS|tz-osemosys"
IAMC_UNIT_EJ = "EJ/yr"
IAMC_UNIT_MT = "Mt CO2/yr"
IAMC_UNIT_GW = "GW"
IAMC_UNIT_MUSD = "million US$2020/yr"

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]


def solution_to_iamc(
    solution: xr.Dataset,
    scenario: str,
    regions: list[str],
) -> pd.DataFrame:
    """
    Convert a tz-osemosys solution to IAMC long-form DataFrame.

    Parameters
    ----------
    solution : xr.Dataset
        model._solution after a successful solve.
    scenario : str
        Scenario label (e.g. "SSP2-4.5").
    regions : list[str]
        Region IDs to process.

    Returns
    -------
    pd.DataFrame with columns:
        model, scenario, region, variable, unit, year, value
    """
    records = []

    for region in regions:
        # ── Production by technology [PJ/yr → EJ/yr] ─────────────────────────
        if "ProductionByTechnology" in solution:
            prod = solution["ProductionByTechnology"]
            # Sum over FUEL (=ELC, only one) and TIMESLICE (only one)
            prod_rt = (
                prod.sel(REGION=region)
                .sum(dim=["FUEL", "TIMESLICE"])
            )  # (TECHNOLOGY, YEAR)

            for tech in TECH_IAMC:
                if tech in prod_rt.coords["TECHNOLOGY"].values:
                    label = TECH_IAMC[tech]
                    for yr in YEARS:
                        val_pj = float(prod_rt.sel(TECHNOLOGY=tech, YEAR=yr).values)
                        records.append({
                            "model": IAMC_MODEL, "scenario": scenario,
                            "region": region,
                            "variable": f"Secondary Energy|Electricity|{label}",
                            "unit": IAMC_UNIT_EJ, "year": yr,
                            "value": val_pj / 1000.0,
                        })

            # Total electricity production
            prod_total = prod_rt.sum(dim="TECHNOLOGY")
            for yr in YEARS:
                records.append({
                    "model": IAMC_MODEL, "scenario": scenario,
                    "region": region,
                    "variable": "Secondary Energy|Electricity",
                    "unit": IAMC_UNIT_EJ, "year": yr,
                    "value": float(prod_total.sel(YEAR=yr).values) / 1000.0,
                })

        # ── Emissions [Mt CO2/yr] ─────────────────────────────────────────────
        if "AnnualTechnologyEmission" in solution:
            emis = solution["AnnualTechnologyEmission"]
            emis_r = emis.sel(REGION=region, EMISSION="CO2")  # (TECHNOLOGY, YEAR)

            for tech in TECH_IAMC:
                if tech in emis_r.coords["TECHNOLOGY"].values:
                    label = TECH_IAMC[tech]
                    for yr in YEARS:
                        val = float(emis_r.sel(TECHNOLOGY=tech, YEAR=yr).values)
                        records.append({
                            "model": IAMC_MODEL, "scenario": scenario,
                            "region": region,
                            "variable": f"Emissions|CO2|Energy|Supply|Electricity|{label}",
                            "unit": IAMC_UNIT_MT, "year": yr,
                            "value": val,
                        })

            # Total fossil electricity emissions
            fossil_mask = [t for t in FOSSIL_TECHS
                           if t in emis_r.coords["TECHNOLOGY"].values]
            if fossil_mask:
                emis_fossil = emis_r.sel(TECHNOLOGY=fossil_mask).sum(dim="TECHNOLOGY")
                for yr in YEARS:
                    records.append({
                        "model": IAMC_MODEL, "scenario": scenario,
                        "region": region,
                        "variable": "Emissions|CO2|Energy|Supply|Electricity",
                        "unit": IAMC_UNIT_MT, "year": yr,
                        "value": float(emis_fossil.sel(YEAR=yr).values),
                    })

        # ── Gross capacity [GW] ───────────────────────────────────────────────
        if "GrossCapacity" in solution:
            cap = solution["GrossCapacity"].sel(REGION=region)

            for tech in TECH_IAMC:
                if tech in cap.coords["TECHNOLOGY"].values:
                    label = TECH_IAMC[tech]
                    for yr in YEARS:
                        val = float(cap.sel(TECHNOLOGY=tech, YEAR=yr).values)
                        records.append({
                            "model": IAMC_MODEL, "scenario": scenario,
                            "region": region,
                            "variable": f"Capacity|Electricity|{label}",
                            "unit": IAMC_UNIT_GW, "year": yr,
                            "value": val,
                        })

        # ── New capacity additions [GW] ───────────────────────────────────────
        if "NewCapacity" in solution:
            ncap = solution["NewCapacity"].sel(REGION=region)

            for tech in TECH_IAMC:
                if tech in ncap.coords["TECHNOLOGY"].values:
                    label = TECH_IAMC[tech]
                    for yr in YEARS:
                        val = float(ncap.sel(TECHNOLOGY=tech, YEAR=yr).values)
                        records.append({
                            "model": IAMC_MODEL, "scenario": scenario,
                            "region": region,
                            "variable": f"Capacity Additions|Electricity|{label}",
                            "unit": IAMC_UNIT_GW, "year": yr,
                            "value": val,
                        })

        # ── Capital investment [M$/yr] ────────────────────────────────────────
        if "CapitalInvestment" in solution:
            inv = solution["CapitalInvestment"].sel(REGION=region)

            for tech in TECH_IAMC:
                if tech in inv.coords["TECHNOLOGY"].values:
                    label = TECH_IAMC[tech]
                    for yr in YEARS:
                        val = float(inv.sel(TECHNOLOGY=tech, YEAR=yr).values)
                        records.append({
                            "model": IAMC_MODEL, "scenario": scenario,
                            "region": region,
                            "variable": f"Investment|Energy Supply|Electricity|{label}",
                            "unit": IAMC_UNIT_MUSD, "year": yr,
                            "value": val,
                        })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Aggregate Hydro (HYDRO_EXIST + HYDRO_RETRO both map to "Hydro")
    df = (
        df.groupby(
            ["model", "scenario", "region", "variable", "unit", "year"],
            as_index=False,
        )["value"].sum()
    )
    return df.sort_values(["region", "variable", "year"]).reset_index(drop=True)


def compute_tvp_dbio_intensity_factors(
    iamc_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """
    Compute per-region, per-year tvp_dbio intensity adjustment factors for
    the Energy_Utilities sector from the IAMC scenario output.

    adj_ratio_ghg(r, t) = grid_intensity(r, t) / grid_intensity(r, base_year)
    where grid_intensity [Mt CO2/EJ] = CO2 emissions / electricity production.

    A ratio < 1 means the grid has decarbonised relative to base_year,
    so supply-chain GHG intensity of electricity-heavy sectors should be
    scaled DOWN by this factor when projecting into the future.

    Parameters
    ----------
    iamc_df : pd.DataFrame
    base_year : int

    Returns
    -------
    pd.DataFrame with columns:
        model, scenario, region, year,
        grid_intensity_mt_ej, adj_ratio_ghg,
        renewable_share, adj_ratio_employment
    """
    records = []

    for (model, scenario, region), grp in iamc_df.groupby(
        ["model", "scenario", "region"]
    ):
        prod_s = (
            grp[grp["variable"] == "Secondary Energy|Electricity"]
            .set_index("year")["value"]
        )  # EJ/yr
        emis_s = (
            grp[grp["variable"] == "Emissions|CO2|Energy|Supply|Electricity"]
            .set_index("year")["value"]
        )  # Mt CO2/yr

        # Renewable production (solar + wind + hydro)
        ren_mask = grp["variable"].str.startswith("Secondary Energy|Electricity|") & (
            grp["variable"].str.contains("Solar|Wind|Hydro")
        )
        ren_s = grp[ren_mask].groupby("year")["value"].sum()  # EJ/yr

        years = sorted(prod_s.index.tolist())

        base_prod  = prod_s.get(base_year, np.nan)
        base_emis  = emis_s.get(base_year, np.nan)
        base_intensity = (
            base_emis / base_prod
            if (base_prod and base_prod > 0)
            else np.nan
        )

        for yr in years:
            prod = prod_s.get(yr, 0.0)
            emis = emis_s.get(yr, 0.0)
            ren  = ren_s.get(yr, 0.0)

            grid_intensity = emis / prod if prod > 0 else 0.0
            adj_ratio_ghg = (
                grid_intensity / base_intensity
                if (base_intensity and base_intensity > 0)
                else 1.0
            )
            renewable_share = ren / prod if prod > 0 else 0.0

            # Employment: renewables are ~40% more labour-intensive per TWh.
            # Ratio relative to a ~30% renewable share baseline.
            adj_ratio_employment = round(1.0 + 0.40 * (renewable_share - 0.30), 4)

            records.append({
                "model":                model,
                "scenario":             scenario,
                "region":               region,
                "year":                 yr,
                "grid_intensity_mt_ej": round(grid_intensity, 4),
                "adj_ratio_ghg":        round(adj_ratio_ghg, 4),
                "renewable_share":      round(renewable_share, 4),
                "adj_ratio_employment": adj_ratio_employment,
            })

    return (
        pd.DataFrame(records)
        .sort_values(["scenario", "region", "year"])
        .reset_index(drop=True)
    )
