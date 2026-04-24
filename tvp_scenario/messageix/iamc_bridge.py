"""
iamc_bridge.py  (MESSAGEix version)
=====================================
Converts MESSAGEix scenario results to IAMC-format DataFrames and computes
tvp_dbio intensity adjustment factors for the Energy_Utilities sector.

MESSAGEix output extraction
---------------------------
After a successful `scenario.solve()`, results are extracted via:

    Option A — message_ix Reporter (recommended, uses genno framework):
        from message_ix.report import Reporter
        rep = Reporter.from_scenario(scen)
        # built-in IAMC keys:
        iamc_df = rep.get("message::default")      # returns pyam.IamDataFrame

    Option B — scenario.timeseries() (simple, pyam-compatible):
        import pyam
        df = pyam.IamDataFrame(scen.timeseries())

    Option C — direct parameter extraction (used here for flexibility):
        act  = scen.var("ACT")           # technology activity [GWa/yr]
        cap  = scen.var("CAP")           # installed capacity [GW]
        emis = scen.var("EMISS")         # emissions [Mt CO2/yr]
        inv  = scen.var("CAP_NEW")       # new capacity [GW/yr]

This module implements Option C, which works regardless of whether the
default reporting configuration is present in the snapshot.

MESSAGEix node → S4 macro-region mapping
------------------------------------------
R11 MESSAGEix nodes:
  Africa  : AFR
  Asia    : CPA, PAS, SAS
  Europe  : WEU, EEU, FSU
  LATAM   : LAM
  Excluded: NAM, MEA, PAO (not in S4 portfolio)

MESSAGEix technologies → IAMC labels
--------------------------------------
  coal_ppl, coal_ppl_u  → Coal
  igcc, igcc_ccs        → Coal (CCS variant)
  gas_cc, gas_ct        → Gas
  gas_cc_ccs            → Gas  (CCS variant)
  hydro_lc, hydro_hc    → Hydro
  solar_pv_ppl, solar_res → Solar
  wind_ppl, wind_ref    → Wind
  nuc_lc, nuc_hc        → Nuclear
  bio_ppl, bio_istig    → Biomass
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── Node → S4 macro-region ────────────────────────────────────────────────────
NODE_MAP: dict[str, str] = {
    "AFR": "Africa",
    "CPA": "Asia",
    "PAS": "Asia",
    "SAS": "Asia",
    "WEU": "Europe",
    "EEU": "Europe",
    "FSU": "Europe",
    "LAM": "LATAM",
}

S4_REGIONS = ["Africa", "Asia", "Europe", "LATAM"]

# ── Technology → IAMC label ───────────────────────────────────────────────────
TECH_IAMC: dict[str, str] = {
    "coal_ppl":    "Coal",
    "coal_ppl_u":  "Coal",
    "igcc":        "Coal",
    "igcc_ccs":    "Coal",
    "gas_cc":      "Gas",
    "gas_ct":      "Gas",
    "gas_cc_ccs":  "Gas",
    "gas_htfc":    "Gas",
    "hydro_lc":    "Hydro",
    "hydro_hc":    "Hydro",
    "solar_pv_ppl":"Solar",
    "solar_res1":  "Solar",
    "solar_res2":  "Solar",
    "solar_res3":  "Solar",
    "wind_ppl":    "Wind",
    "wind_ref":    "Wind",
    "nuc_lc":      "Nuclear",
    "nuc_hc":      "Nuclear",
    "bio_ppl":     "Biomass",
    "bio_istig":   "Biomass",
    "bio_istig_ccs":"Biomass",
    "geo_ppl":     "Geothermal",
}

FOSSIL_TECHS  = {t for t, lbl in TECH_IAMC.items() if lbl in ("Coal", "Gas")}
RENEW_LABELS  = {"Hydro", "Wind", "Solar", "Geothermal", "Biomass"}

IAMC_MODEL     = "MESSAGEix|message-ix"
IAMC_UNIT_EJ   = "EJ/yr"
IAMC_UNIT_MT   = "Mt CO2/yr"
IAMC_UNIT_GW   = "GW"
IAMC_UNIT_MUSD = "million US$2020/yr"

YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]
PJ_PER_GWA = 31.536   # PJ per GWa (matches OSeMOSYS capacity_activity_unit_ratio)


# ── Extraction helpers ────────────────────────────────────────────────────────

def _extract_activity(scen) -> pd.DataFrame:
    """Extract ACT variable (technology activity [GWa/yr]) from solved scenario."""
    act = scen.var("ACT")
    # ACT columns: node_loc, technology, year_vtg, year_act, mode, time, lvl, mrg
    act = act.rename(columns={"node_loc": "node", "year_act": "year"})
    act = act[act["time"] == "year"].groupby(
        ["node", "technology", "year"], as_index=False
    )["lvl"].sum()
    return act


def _extract_capacity(scen) -> pd.DataFrame:
    """Extract CAP variable (total installed capacity [GW])."""
    cap = scen.var("CAP")
    # CAP columns: node_loc, technology, year_vtg, year_act, lvl, mrg
    cap = cap.rename(columns={"node_loc": "node", "year_act": "year"})
    cap = cap.groupby(["node", "technology", "year"], as_index=False)["lvl"].sum()
    return cap


def _extract_emissions(scen, emission: str = "CO2_Emission") -> pd.DataFrame:
    """Extract EMISS variable [Mt CO2/yr] for a given emission type."""
    emis = scen.var("EMISS")
    emis = emis.rename(columns={"node_loc": "node", "year": "year"})
    if "emission" in emis.columns:
        emis = emis[emis["emission"] == emission]
    emis = emis.groupby(["node", "technology", "year"], as_index=False)["lvl"].sum()
    return emis


def _extract_investment(scen) -> pd.DataFrame:
    """Extract CAP_NEW variable (new capacity additions [GW]) and compute capex."""
    cap_new = scen.var("CAP_NEW")
    # Approximate investment = CAP_NEW × inv_cost (not stored in CAP_NEW directly)
    # Return new capacity only; investment $ computation requires inv_cost parameter
    cap_new = cap_new.rename(columns={"node_loc": "node", "year_vtg": "year"})
    cap_new = cap_new.groupby(["node", "technology", "year"], as_index=False)["lvl"].sum()
    return cap_new


# ── Main conversion ───────────────────────────────────────────────────────────

def solution_to_iamc(scen, scenario_label: str) -> pd.DataFrame:
    """
    Convert a solved MESSAGEix Scenario to IAMC long-form DataFrame.

    Parameters
    ----------
    scen           : message_ix.Scenario (must have been solved)
    scenario_label : IAMC scenario string (e.g. "SSP2-4.5")

    Returns
    -------
    pd.DataFrame with columns: model, scenario, region, variable, unit, year, value
    """
    records: list[dict] = []

    # ── Activity → energy output [GWa/yr → EJ/yr] ────────────────────────
    try:
        act = _extract_activity(scen)
    except Exception as exc:
        log.error("  Failed to extract ACT: %s", exc)
        act = pd.DataFrame(columns=["node", "technology", "year", "lvl"])

    for (node, tech), grp in act.groupby(["node", "technology"]):
        s4 = NODE_MAP.get(node)
        label = TECH_IAMC.get(tech)
        if s4 is None or label is None:
            continue
        for yr in YEARS:
            val_gwa = float(grp.loc[grp["year"] == yr, "lvl"].sum())
            val_ej  = val_gwa * PJ_PER_GWA * 1e-3   # GWa × PJ/GWa × EJ/PJ
            records.append({
                "model": IAMC_MODEL, "scenario": scenario_label,
                "region": s4,
                "variable": f"Secondary Energy|Electricity|{label}",
                "unit": IAMC_UNIT_EJ, "year": yr, "value": val_ej,
            })

    # ── Total electricity per region/year ─────────────────────────────────
    if not act.empty:
        act["s4_region"] = act["node"].map(NODE_MAP)
        act["label"]     = act["technology"].map(TECH_IAMC)
        act_mapped = act.dropna(subset=["s4_region", "label"])
        for (s4, yr), grp in act_mapped.groupby(["s4_region", "year"]):
            records.append({
                "model": IAMC_MODEL, "scenario": scenario_label,
                "region": s4,
                "variable": "Secondary Energy|Electricity",
                "unit": IAMC_UNIT_EJ, "year": yr,
                "value": float(grp["lvl"].sum()) * PJ_PER_GWA * 1e-3,
            })

    # ── Capacity [GW] ─────────────────────────────────────────────────────
    try:
        cap = _extract_capacity(scen)
        for (node, tech), grp in cap.groupby(["node", "technology"]):
            s4    = NODE_MAP.get(node)
            label = TECH_IAMC.get(tech)
            if s4 is None or label is None:
                continue
            for yr in YEARS:
                val = float(grp.loc[grp["year"] == yr, "lvl"].sum())
                records.append({
                    "model": IAMC_MODEL, "scenario": scenario_label,
                    "region": s4,
                    "variable": f"Capacity|Electricity|{label}",
                    "unit": IAMC_UNIT_GW, "year": yr, "value": val,
                })
    except Exception as exc:
        log.warning("  Capacity extraction failed: %s", exc)

    # ── CO2 emissions [Mt CO2/yr] ─────────────────────────────────────────
    try:
        emis = _extract_emissions(scen)
        # Per-technology
        for (node, tech), grp in emis.groupby(["node", "technology"]):
            s4    = NODE_MAP.get(node)
            label = TECH_IAMC.get(tech)
            if s4 is None or label is None:
                continue
            for yr in YEARS:
                val = float(grp.loc[grp["year"] == yr, "lvl"].sum())
                records.append({
                    "model": IAMC_MODEL, "scenario": scenario_label,
                    "region": s4,
                    "variable": f"Emissions|CO2|Energy|Supply|Electricity|{label}",
                    "unit": IAMC_UNIT_MT, "year": yr, "value": val,
                })
        # Total fossil CO2
        emis["s4_region"] = emis["node"].map(NODE_MAP)
        fossil_mask = emis["technology"].isin(FOSSIL_TECHS)
        for (s4, yr), grp in emis[fossil_mask].groupby(["s4_region", "year"]):
            if pd.isna(s4):
                continue
            records.append({
                "model": IAMC_MODEL, "scenario": scenario_label,
                "region": s4,
                "variable": "Emissions|CO2|Energy|Supply|Electricity",
                "unit": IAMC_UNIT_MT, "year": yr,
                "value": float(grp["lvl"].sum()),
            })
    except Exception as exc:
        log.warning("  Emission extraction failed: %s", exc)

    # ── New capacity additions [GW] ───────────────────────────────────────
    try:
        ncap = _extract_investment(scen)
        for (node, tech), grp in ncap.groupby(["node", "technology"]):
            s4    = NODE_MAP.get(node)
            label = TECH_IAMC.get(tech)
            if s4 is None or label is None:
                continue
            for yr in YEARS:
                val = float(grp.loc[grp["year"] == yr, "lvl"].sum())
                records.append({
                    "model": IAMC_MODEL, "scenario": scenario_label,
                    "region": s4,
                    "variable": f"Capacity Additions|Electricity|{label}",
                    "unit": IAMC_UNIT_GW, "year": yr, "value": val,
                })
    except Exception as exc:
        log.warning("  New capacity extraction failed: %s", exc)

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Aggregate technologies that share an IAMC label (e.g., coal_ppl + coal_ppl_u → Coal)
    df = (
        df.groupby(
            ["model", "scenario", "region", "variable", "unit", "year"],
            as_index=False,
        )["value"].sum()
    )
    return df.sort_values(["region", "variable", "year"]).reset_index(drop=True)


def solution_to_iamc_via_reporter(scen, scenario_label: str) -> pd.DataFrame:
    """
    Alternative extraction using message_ix's built-in Reporter.

    More accurate than direct variable extraction for models where the
    default reporting configuration is present (e.g., snapshot-based models).
    Falls back to solution_to_iamc() if reporter fails.
    """
    try:
        from message_ix.report import Reporter
        import pyam

        rep = Reporter.from_scenario(scen)
        # The default key 'message::default' returns a pyam.IamDataFrame
        iamc = rep.get("message::default")
        if isinstance(iamc, pyam.IamDataFrame):
            df = iamc.data.copy()
            df["scenario"] = scenario_label
            df["model"]    = IAMC_MODEL
            return df
    except Exception as exc:
        log.warning("  Reporter extraction failed (%s); falling back to variable extract.", exc)

    return solution_to_iamc(scen, scenario_label)


# ── tvp_dbio factors ──────────────────────────────────────────────────────────

def compute_tvp_dbio_intensity_factors(
    iamc_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """
    Compute adj_ratio_ghg and adj_ratio_employment.

    Identical to OSeMOSYS and GCAM versions — ensures direct cross-model
    comparability of the tvp_dbio intensity adjustment outputs.
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
            grp["variable"].str.contains("|".join(RENEW_LABELS))
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
            renewable_share      = ren / prod if prod > 0 else 0.0
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
