"""
iamc_bridge.py  (GCAM version)
================================
Converts pygcam CSV query outputs to IAMC-format DataFrames and computes
tvp_dbio intensity adjustment factors for the Energy_Utilities sector.

Input format (from pygcam gt query / gcam_reader)
-------------------------------------------------
Each query produces a CSV with at least these columns:
    scenario, region, subsector (or technology), year, value

GCAM regions → S4 macro-regions
---------------------------------
GCAM 32-region → Africa / Asia / Europe / LATAM aggregation:

  Africa : Africa_Eastern, Africa_Northern, Africa_Southern, Africa_Western
  Asia   : China, India, South Korea, Japan, Southeast Asia, South Asia,
           Pakistan, Taiwan, Australia_NZ (excluded — Oceania)
  Europe : EU-15, EU-12, Europe Eastern, Europe Non-EU, Russia, Ukraine,
           Switzerland
  LATAM  : Mexico, Central America and Caribbean, Brazil,
           South America (Northern Latitude), South America (Southern Latitude),
           Colombia, Argentina

  Unmatched GCAM regions (USA, Canada, Middle East, etc.) are excluded from
  the S4 regional aggregation but present in full GCAM output.

GCAM subsectors → IAMC technology labels
-----------------------------------------
  "coal"         → Coal
  "coal CCS"     → Coal          (included in Coal total)
  "gas"          → Gas
  "gas CCS"      → Gas           (included in Gas total)
  "hydro"        → Hydro
  "wind"         → Wind
  "solar"        → Solar
  "geothermal"   → Geothermal    (not mapped to OSeMOSYS equivalent, reported separately)
  "nuclear"      → Nuclear

Unit conversions
----------------
  GCAM energy  : EJ/yr  →  IAMC: EJ/yr  (no conversion needed)
  GCAM CO2     : Mt CO2/yr  →  IAMC: Mt CO2/yr  (no conversion)
  GCAM capacity: GW  →  IAMC: GW  (no conversion)
  GCAM invest  : billion US$2020/yr × 1000  →  IAMC: million US$2020/yr
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── GCAM region → S4 macro-region mapping ────────────────────────────────────
REGION_MAP: dict[str, str] = {
    # Africa
    "Africa_Eastern":   "Africa",
    "Africa_Northern":  "Africa",
    "Africa_Southern":  "Africa",
    "Africa_Western":   "Africa",
    # Asia
    "China":            "Asia",
    "India":            "Asia",
    "South Korea":      "Asia",
    "Japan":            "Asia",
    "Southeast Asia":   "Asia",
    "South Asia":       "Asia",
    "Pakistan":         "Asia",
    "Taiwan":           "Asia",
    # Europe
    "EU-15":            "Europe",
    "EU-12":            "Europe",
    "Europe Eastern":   "Europe",
    "Europe Non-EU":    "Europe",
    "Russia":           "Europe",
    "Ukraine":          "Europe",
    "Switzerland":      "Europe",
    # LATAM
    "Mexico":                               "LATAM",
    "Central America and Caribbean":        "LATAM",
    "Brazil":                               "LATAM",
    "South America (Northern Latitude)":    "LATAM",
    "South America (Southern Latitude)":    "LATAM",
    "Colombia":                             "LATAM",
    "Argentina":                            "LATAM",
}

# S4 macro-regions in display order
S4_REGIONS = ["Africa", "Asia", "Europe", "LATAM"]

# ── GCAM subsector → IAMC technology label ───────────────────────────────────
SUBSECTOR_IAMC: dict[str, str] = {
    "coal":          "Coal",
    "coal CCS":      "Coal",
    "gas":           "Gas",
    "gas CCS":       "Gas",
    "hydro":         "Hydro",
    "wind":          "Wind",
    "solar":         "Solar",
    "geothermal":    "Geothermal",
    "nuclear":       "Nuclear",
    "biomass":       "Biomass",
    "biomass CCS":   "Biomass",
}

FOSSIL_SUBSECTORS = {"coal", "coal CCS", "gas", "gas CCS"}

IAMC_MODEL    = "GCAM|pygcam"
IAMC_UNIT_EJ  = "EJ/yr"
IAMC_UNIT_MT  = "Mt CO2/yr"
IAMC_UNIT_GW  = "GW"
IAMC_UNIT_MUSD = "million US$2020/yr"

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_macro_region(df: pd.DataFrame, gcam_col: str = "region") -> pd.DataFrame:
    """Add 's4_region' column by mapping GCAM region names → Africa/Asia/Europe/LATAM."""
    df = df.copy()
    df["s4_region"] = df[gcam_col].map(REGION_MAP)
    n_unmapped = df["s4_region"].isna().sum()
    if n_unmapped:
        unmapped = df.loc[df["s4_region"].isna(), gcam_col].unique().tolist()
        log.debug("  %d rows from unmapped GCAM regions (excluded): %s", n_unmapped, unmapped)
    return df.dropna(subset=["s4_region"])


def _pivot_to_years(df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
    """Ensure 'year' column is integer and filter to YEARS."""
    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df[df["year"].isin(YEARS)]


# ── Main conversion function ──────────────────────────────────────────────────

def solution_to_iamc(
    elec_gen_df:  pd.DataFrame,
    co2_df:       pd.DataFrame,
    capacity_df:  pd.DataFrame,
    investment_df: pd.DataFrame | None,
    scenario: str,
) -> pd.DataFrame:
    """
    Convert GCAM query DataFrames to IAMC long-form DataFrame.

    Parameters
    ----------
    elec_gen_df   : electricity generation query output [EJ/yr]
                    columns: region, subsector, year, value
    co2_df        : CO2 emissions query output [Mt CO2/yr]
                    columns: region, subsector, year, value
    capacity_df   : installed capacity query output [GW]
                    columns: region, subsector, year, value
    investment_df : capital investment query output [bn US$2020/yr] or None
                    columns: region, subsector, year, value
    scenario      : IAMC scenario label (e.g. "SSP2-4.5")

    Returns
    -------
    pd.DataFrame  with columns: model, scenario, region, variable, unit, year, value
    """
    records: list[dict] = []

    # ── Electricity generation ─────────────────────────────────────────────
    gen = _add_macro_region(_pivot_to_years(elec_gen_df))

    # Per-technology production
    for (s4_region, subsector), grp in gen.groupby(["s4_region", "subsector"]):
        label = SUBSECTOR_IAMC.get(subsector)
        if label is None:
            continue
        for yr in YEARS:
            val = grp.loc[grp["year"] == yr, "value"].sum()
            records.append({
                "model": IAMC_MODEL, "scenario": scenario,
                "region": s4_region,
                "variable": f"Secondary Energy|Electricity|{label}",
                "unit": IAMC_UNIT_EJ, "year": int(yr), "value": float(val),
            })

    # Total electricity per region/year
    for (s4_region, yr), grp in gen.groupby(["s4_region", "year"]):
        records.append({
            "model": IAMC_MODEL, "scenario": scenario,
            "region": s4_region,
            "variable": "Secondary Energy|Electricity",
            "unit": IAMC_UNIT_EJ, "year": int(yr), "value": float(grp["value"].sum()),
        })

    # ── CO2 emissions ──────────────────────────────────────────────────────
    emis = _add_macro_region(_pivot_to_years(co2_df))

    # Per-technology CO2
    for (s4_region, subsector), grp in emis.groupby(["s4_region", "subsector"]):
        label = SUBSECTOR_IAMC.get(subsector)
        if label is None:
            continue
        for yr in YEARS:
            val = grp.loc[grp["year"] == yr, "value"].sum()
            records.append({
                "model": IAMC_MODEL, "scenario": scenario,
                "region": s4_region,
                "variable": f"Emissions|CO2|Energy|Supply|Electricity|{label}",
                "unit": IAMC_UNIT_MT, "year": int(yr), "value": float(val),
            })

    # Total fossil CO2 per region/year
    fossil_mask = emis["subsector"].isin(FOSSIL_SUBSECTORS)
    for (s4_region, yr), grp in emis[fossil_mask].groupby(["s4_region", "year"]):
        records.append({
            "model": IAMC_MODEL, "scenario": scenario,
            "region": s4_region,
            "variable": "Emissions|CO2|Energy|Supply|Electricity",
            "unit": IAMC_UNIT_MT, "year": int(yr), "value": float(grp["value"].sum()),
        })

    # ── Installed capacity ─────────────────────────────────────────────────
    cap = _add_macro_region(_pivot_to_years(capacity_df))

    for (s4_region, subsector), grp in cap.groupby(["s4_region", "subsector"]):
        label = SUBSECTOR_IAMC.get(subsector)
        if label is None:
            continue
        for yr in YEARS:
            val = grp.loc[grp["year"] == yr, "value"].sum()
            records.append({
                "model": IAMC_MODEL, "scenario": scenario,
                "region": s4_region,
                "variable": f"Capacity|Electricity|{label}",
                "unit": IAMC_UNIT_GW, "year": int(yr), "value": float(val),
            })

    # ── Capital investment ─────────────────────────────────────────────────
    if investment_df is not None:
        inv = _add_macro_region(_pivot_to_years(investment_df))
        for (s4_region, subsector), grp in inv.groupby(["s4_region", "subsector"]):
            label = SUBSECTOR_IAMC.get(subsector)
            if label is None:
                continue
            for yr in YEARS:
                val = grp.loc[grp["year"] == yr, "value"].sum()
                records.append({
                    "model": IAMC_MODEL, "scenario": scenario,
                    "region": s4_region,
                    "variable": f"Investment|Energy Supply|Electricity|{label}",
                    "unit": IAMC_UNIT_MUSD, "year": int(yr),
                    # GCAM investment in billion US$ → × 1000 → million US$
                    "value": float(val) * 1000.0,
                })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Aggregate technologies that share an IAMC label (coal + coal CCS → Coal, etc.)
    df = (
        df.groupby(
            ["model", "scenario", "region", "variable", "unit", "year"],
            as_index=False,
        )["value"].sum()
    )
    return df.sort_values(["region", "variable", "year"]).reset_index(drop=True)


# ── tvp_dbio intensity factors ────────────────────────────────────────────────

def compute_tvp_dbio_intensity_factors(
    iamc_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """
    Compute per-region, per-year tvp_dbio intensity adjustment factors.

    adj_ratio_ghg(r, t) = grid_intensity(r, t) / grid_intensity(r, base_year)
    where grid_intensity [Mt CO2/EJ] = CO2 emissions / electricity production.

    Identical calculation to osemosys/iamc_bridge.py — ensures that the two
    model frameworks produce directly comparable adj_ratio_ghg outputs.

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
        )
        emis_s = (
            grp[grp["variable"] == "Emissions|CO2|Energy|Supply|Electricity"]
            .set_index("year")["value"]
        )
        ren_mask = grp["variable"].str.startswith("Secondary Energy|Electricity|") & (
            grp["variable"].str.contains("Solar|Wind|Hydro|Geothermal")
        )
        ren_s = grp[ren_mask].groupby("year")["value"].sum()

        years = sorted(prod_s.index.tolist())
        base_prod  = prod_s.get(base_year, np.nan)
        base_emis  = emis_s.get(base_year, np.nan)
        base_intensity = (
            base_emis / base_prod
            if (not np.isnan(base_prod) and base_prod > 0)
            else np.nan
        )

        for yr in years:
            prod = prod_s.get(yr, 0.0)
            emis = emis_s.get(yr, 0.0)
            ren  = ren_s.get(yr, 0.0)

            grid_intensity = emis / prod if prod > 0 else 0.0
            adj_ratio_ghg  = (
                grid_intensity / base_intensity
                if (not np.isnan(base_intensity) and base_intensity > 0)
                else 1.0
            )
            renewable_share = ren / prod if prod > 0 else 0.0
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


# ── Query result readers ──────────────────────────────────────────────────────

def read_query_csv(path: Path, value_col: str = "value") -> pd.DataFrame:
    """
    Read a pygcam query result CSV.

    pygcam writes query results as CSV files with the following structure:
        - First row(s) may contain metadata (scenario, query name)
        - Column headers include 'region', the axis dimension, and year columns
        - Years are typically wide-format (one column per year)

    This function normalises the output to long-form with columns:
        region, subsector, year, value

    Parameters
    ----------
    path      : Path to the CSV query result file
    value_col : Name to use for the melted value column

    Returns
    -------
    pd.DataFrame in long format
    """
    if not path.exists():
        raise FileNotFoundError(f"GCAM query result not found: {path}")

    # Detect if wide-format (year columns as integers) vs already long
    raw = pd.read_csv(path, comment="#")

    # Identify year columns (integer column names like 2020, 2025, ...)
    year_cols = [c for c in raw.columns if str(c).strip().isdigit()
                 and 2000 <= int(c) <= 2100]

    if year_cols:
        # Wide → long pivot
        id_cols = [c for c in raw.columns if c not in year_cols]
        df = raw.melt(id_vars=id_cols, value_vars=year_cols,
                      var_name="year", value_name=value_col)
        df["year"] = df["year"].astype(int)
    else:
        # Already long — assume columns include 'year' and value_col
        df = raw
        if value_col not in df.columns and "value" in df.columns:
            df = df.rename(columns={"value": value_col})

    # Normalise axis column name (pygcam may use subsector, technology, fuel, etc.)
    for alias in ("subsector", "technology", "fuel", "sector", "input"):
        if alias in df.columns and "subsector" not in df.columns:
            df = df.rename(columns={alias: "subsector"})
            break

    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0)
    return df
