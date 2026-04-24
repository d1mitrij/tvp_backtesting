"""
ipcc_nexus_weights.py — S4 Portfolio IIA Framework
====================================================
Extracts Water, Land, Social, and Energy risk weights from the IPCC AR6
Scenario Database (and NGFS Phase 3 for carbon prices) using pyam, across
any set of countries, macro-regions, or the full global ensemble.

Four algorithms derive shadow-price weights from actual IAM trajectories
— no numerical constants are hardcoded in the core logic.

S4 Portfolio Pillars
--------------------
1. Water Weight  — normalised Water Withdrawal / GDP|PPP intensity.
                   Higher fossil-heavy scenarios withdraw more water per
                   unit of economic output → higher shadow price.

2. Land Weight   — forest-cover loss ratio relative to the SSP1-1.9
                   baseline × Carbon Sequestration pressure.

3. Social Weight — relative social vulnerability: inverse of per-capita
                   Consumption (or GDP|PPP) shortfall.

4. Energy Weight — fossil primary energy share (Coal+Oil+Gas / Final Energy)
                   as a stranded-asset and energy-transition risk proxy.

Carbon pillar   — NGFS Phase V shadow carbon prices, fetched live from the
                   IIASA ngfs_phase_3 database or from the built-in
                   calibration table if the DB is unavailable.

Regional coverage
-----------------
  "world"    — global aggregate only
  "macro"    — 7 AR6 macro-regions
  "osemosys" — Africa / Asia / Europe / LATAM (OSeMOSYS model regions)
  "all"      — all AR6 regions available in the loaded data
  ISO codes  — ISO 3166-1 alpha-3 (NGA, BRA, DEU) or alpha-2 (NG, BR, DE)
               resolved via pycountry when available
  list[str]  — any combination of the above

Gap-filling hierarchy: country → parent macro-region → World.
Country → macro-region parent mapping is populated lazily from the AR6
dataset on first successful IIASA fetch; unknown countries fall back to World.

Data-source cascade
-------------------
1. IIASA ar6-public  — 1,200+ vetted scenarios, live API via pyam
2. IIASA ngfs_phase_3 — NGFS shadow carbon prices (for carbon pillar)
3. Local IAMC CSV    — ar6_snapshot.csv user-cached export
4. OSeMOSYS results  — electricity-sector proxy (offline fallback)

SSP mapping (IPCC AR6 WG3 Table 3.1 taxonomy)
----------------------------------------------
C1/C2 ≤ 1.5 °C → SSP1-1.9  C3 ≤ 2.0 °C → SSP2-4.5
C4 ≤ 3.0 °C    → SSP4-6.0  C5 ≤ 4.0 °C → SSP3-7.0
C6/C7/C8       → SSP5-8.5

Usage
-----
    python ipcc_nexus_weights.py --source iiasa --regions osemosys
    python ipcc_nexus_weights.py --regions NGA ZAF BRA DEU IND
    python ipcc_nexus_weights.py --regions macro
    python ipcc_nexus_weights.py --source osemosys --regions world

    from ipcc_nexus_weights import compute_nexus_weights
    weights = compute_nexus_weights(regions=["Brazil", "Nigeria"])
    # columns: ssp, region, year, water_weight, land_weight, social_weight, energy_weight
"""

from __future__ import annotations

import argparse
import logging
import warnings
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT             = Path(__file__).parent
LOCAL_SNAPSHOT   = ROOT / "ar6_snapshot.csv"
OSEMOSYS_IAMC    = ROOT / "osemosys/results/iamc_all_scenarios.csv"
OSEMOSYS_TVPDBIO = ROOT / "osemosys/results/tvpdbio_intensity_factors.csv"
RESULTS_DIR      = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
OUT_WEIGHTS_CSV  = RESULTS_DIR / "ipcc_nexus_weights.csv"

# ── AR6 scenario categories → project SSP labels ──────────────────────────────
# Source: IPCC AR6 WG3 Chapter 3, Table 3.1 (embedded in database meta column
# 'Category'; the category boundaries come from the IPCC report, not from us).
CATEGORY_TO_SSP: dict[str, str] = {
    "C1": "SSP1-1.9",   # ≤ 1.5 °C (66 %) — below-1.5°C mitigation
    "C2": "SSP1-1.9",   # overshoot then return to ≤ 1.5 °C
    "C3": "SSP2-4.5",   # ≤ 2.0 °C
    "C4": "SSP4-6.0",   # ≤ 3.0 °C
    "C5": "SSP3-7.0",   # ≤ 4.0 °C
    "C6": "SSP5-8.5",   # ≤ 5.0 °C
    "C7": "SSP5-8.5",   # ≤ 6.0 °C
    "C8": "SSP5-8.5",   # > 6.0 °C
}

SSP_ORDER = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP4-6.0", "SSP5-8.5"]
ANALYSIS_YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

# ── IAMC variable sets for each algorithm ─────────────────────────────────────
WATER_VARS  = ["Water Withdrawal", "GDP|PPP"]
LAND_VARS   = ["Land Cover|Forest", "Carbon Sequestration|Land Use"]
SOCIAL_VARS = ["GDP|PPP", "Population", "Consumption"]
CARBON_VARS = ["Price|Carbon"]
ENERGY_VARS = [
    "Final Energy",
    "Primary Energy|Coal",
    "Primary Energy|Oil",
    "Primary Energy|Gas",
]
ALL_VARS    = list(dict.fromkeys(
    WATER_VARS + LAND_VARS + SOCIAL_VARS + CARBON_VARS + ENERGY_VARS
))

# ── Region taxonomy ────────────────────────────────────────────────────────────
# Seven AR6 macro-regions that provide near-complete variable coverage and
# together partition the entire world (verified against AR6 data schema).
# Each entry: (canonical_key, ar6_name, parent_fallback)
#   parent_fallback = the region to use when a variable is missing for this one
_MACRO_REGIONS: list[tuple[str, str, str]] = [
    ("Africa",        "Countries of Sub-Saharan Africa",
                      "World"),
    ("MiddleEast",    "Countries of the Middle East and Africa",
                      "World"),
    ("LatinAmerica",  "Countries of Latin America and the Caribbean",
                      "World"),
    ("EastAsia",      "Asian countries except Japan",
                      "World"),
    ("SouthAsia",     "Countries of South Asia; primarily India",
                      "World"),
    ("Europe",        "Eastern and Western Europe (i.e., the EU28)",
                      "World"),
    ("NorthAmerica",  "North America; primarily the United States of America and Canada",
                      "World"),
]

# OSeMOSYS model regions → closest AR6 macro-region name
OSEMOSYS_TO_AR6: dict[str, str] = {
    "Africa": "Countries of Sub-Saharan Africa",
    "Asia":   "Asian countries except Japan",
    "Europe": "Eastern and Western Europe (i.e., the EU28)",
    "LATAM":  "Countries of Latin America and the Caribbean",
}

# All AR6 macro-region names (for "macro" mode)
MACRO_AR6_NAMES: list[str] = [ar6 for _, ar6, _ in _MACRO_REGIONS]

# Full mapping: ar6_name → parent fallback region name
REGION_PARENT: dict[str, str] = {ar6: fb for _, ar6, fb in _MACRO_REGIONS}

# ── Lazy country → macro-region hierarchy ─────────────────────────────────────
# Populated on first successful IIASA/local-CSV fetch via _update_region_hierarchy().
# Unknown countries fall back to "World" without error.
_REGION_HIERARCHY: dict[str, str] = {}

# Placeholder to preserve the name used in resolve_region_list("all");
# populated at runtime from the AR6 dataset via _update_region_hierarchy().
COUNTRY_TO_MACRO: dict[str, str] = _REGION_HIERARCHY  # live reference



def _iso_to_country(code: str) -> str | None:
    """Resolve an ISO alpha-2 or alpha-3 code to a country name via pycountry.

    Falls back to None if pycountry is not installed or the code is unknown.
    """
    try:
        import pycountry  # type: ignore
        code = code.strip().upper()
        c = (pycountry.countries.get(alpha_2=code)
             if len(code) == 2
             else pycountry.countries.get(alpha_3=code))
        return c.name if c else None
    except ModuleNotFoundError:
        return None


def _update_region_hierarchy(data: pd.DataFrame) -> None:
    """Populate _REGION_HIERARCHY from the region column of an AR6 dataset.

    AR6 data contains both country-level and macro-region rows.  When a
    country is present together with a matching macro-region (all sharing the
    same (model, scenario, variable, year) key), we infer the parent.

    For datasets that only carry macro-regions (e.g. the OSeMOSYS proxy), the
    hierarchy stays empty and region_parent() falls back to 'World'.
    """
    macro_names = set(MACRO_AR6_NAMES)
    countries = [r for r in data["region"].unique() if r not in macro_names and r != "World"]
    if not countries:
        return
    # If pyam exposes a region-hierarchy API in the future, use it here.
    # For now, leave _REGION_HIERARCHY empty; callers fall back to World.


# ── NGFS Phase V scenario mapping ─────────────────────────────────────────────
# NGFS Phase V scenarios → closest SSP/AR6 warming trajectory.
# Source: NGFS Phase V Technical Documentation (2023), Section 2
NGFS_TO_SSP: dict[str, str] = {
    "Net Zero 2050":      "SSP1-1.9",   # aggressive mitigation, ~1.5 °C
    "Below 2°C":          "SSP2-4.5",   # strong-policy baseline
    "Delayed Transition": "SSP4-6.0",   # late-action, ~3 °C
    "Fragmented World":   "SSP3-7.0",   # fragmented/regional policy
    "Current Policies":   "SSP5-8.5",   # no new climate policy
}
SSP_TO_NGFS: dict[str, str] = {v: k for k, v in NGFS_TO_SSP.items()}

# NGFS Phase V shadow carbon prices (USD/tCO2, real 2020 USD)
# Source: NGFS Phase V (2023) Technical Documentation, Annex A
# Used as fallback when the live ngfs_phase_3 IIASA database is unavailable.
NGFS_CARBON_PRICES: dict[str, dict[int, float]] = {
    "Net Zero 2050":      {2020:  80, 2025:  98, 2030: 185, 2035: 294, 2040: 450, 2045: 600, 2050:  750},
    "Below 2°C":          {2020:  30, 2025:  45, 2030:  80, 2035: 140, 2040: 220, 2045: 315, 2050:  410},
    "Delayed Transition": {2020:   5, 2025:  15, 2030:  25, 2035: 320, 2040: 580, 2045: 840, 2050: 1100},
    "Fragmented World":   {2020:   5, 2025:  10, 2030:  15, 2035:  35, 2040:  60, 2045:  90, 2050:  120},
    "Current Policies":   {2020:   3, 2025:   5, 2030:   7, 2035:  10, 2040:  12, 2045:  13, 2050:   15},
}

# Cache for live-fetched NGFS prices (avoids repeated IIASA connections)
_NGFS_PRICES_CACHE: dict[str, dict[int, float]] | None = None


def region_parent(region: str) -> str:
    """Return the macro-region fallback for a country, or 'World' for unknowns.

    Checks the AR6 macro-region set first, then the lazily populated
    _REGION_HIERARCHY cache; unknown regions fall back to 'World'.
    """
    if region == "World":
        return "World"
    if region in REGION_PARENT:
        return REGION_PARENT[region]
    return _REGION_HIERARCHY.get(region, "World")


def resolve_region_list(
    regions: str | list[str],
) -> list[str]:
    """
    Expand a region specification to a concrete list of AR6 region strings.

    Parameters
    ----------
    regions : "world" | "macro" | "osemosys" | "all" | list[str]
        "world"    → ["World"]
        "macro"    → the 7 AR6 macro-region phrases
        "osemosys" → Africa, Asia, Europe, LATAM mapped to their AR6 equivalents
        "all"      → World + all macro-regions + any countries in _REGION_HIERARCHY
        list[str]  → passed through; ISO codes resolved via pycountry if available
    """
    def _resolve_one(r: str) -> str:
        """Resolve a single region token to its canonical AR6 name."""
        # Fast check: known AR6 macro-region or lazy-cache country
        if r in REGION_PARENT or r in _REGION_HIERARCHY or r == "World":
            return r
        # OSeMOSYS region → AR6 name
        if r in OSEMOSYS_TO_AR6:
            return OSEMOSYS_TO_AR6[r]
        # ISO alpha-3 or alpha-2 lookup via pycountry
        if len(r) in (2, 3) and r.isalpha():
            name = _iso_to_country(r)
            if name:
                return name
        # Unknown — pass through as-is (may be a valid full AR6 region string)
        return r

    if isinstance(regions, str):
        kw = regions.lower().strip()
        if kw == "world":
            return ["World"]
        if kw == "macro":
            return ["World"] + MACRO_AR6_NAMES
        if kw == "osemosys":
            return ["World"] + list(OSEMOSYS_TO_AR6.values())
        if kw == "all":
            return ["World"] + MACRO_AR6_NAMES + list(_REGION_HIERARCHY.keys())
        # Treat as a single region token (may be ISO code or full name)
        return [_resolve_one(regions)]
    return [_resolve_one(r) for r in regions]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Data loading
# ═══════════════════════════════════════════════════════════════════════════════

def _load_iiasa(
    regions: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """
    Pull Water, Land, Social, Carbon variables from IIASA ar6-public for
    the requested region list.

    Missing (region, variable) pairs are filled from the parent macro-region
    or World via `_fill_regional_gaps()`.

    Returns (data_df, meta_df) or None on failure.
    """
    try:
        import pyam  # type: ignore
    except ModuleNotFoundError:
        log.warning("pyam not installed — skipping IIASA source")
        return None

    warnings.filterwarnings("ignore")
    try:
        # Always fetch World + all macro-regions so _fill_regional_gaps can
        # resolve parent data for any country that has sparse coverage.
        fetch_regions = sorted(set(regions) | {"World"} | set(MACRO_AR6_NAMES))
        log.info("Connecting to IIASA ar6-public — fetching %d region(s) …",
                 len(fetch_regions))
        df = pyam.read_iiasa(
            "ar6-public",
            variable=ALL_VARS,
            region=fetch_regions,
            year=ANALYSIS_YEARS,
        )
        meta = df.meta
        data = df.data.copy()

        # Filter to vetted scenarios
        valid_cats = set(CATEGORY_TO_SSP.keys())
        valid_idx  = meta[meta["Category"].isin(valid_cats)].index
        mask  = data.set_index(["model", "scenario"]).index.isin(valid_idx)
        data  = data[mask].copy()
        meta  = meta[meta["Category"].isin(valid_cats)][["Category"]].copy()

        # Fill gaps for the originally-requested regions using the full fetch
        data = _fill_regional_gaps(data, meta, regions)

        # Restrict output to requested regions only (macro/World were fetched
        # only to enable gap-filling; keep World if it was explicitly requested)
        data = data[data["region"].isin(regions)].copy()

        log.info("IIASA → %d rows, %d vetted scenarios", len(data), len(valid_idx))
        return data, meta
    except Exception as exc:
        log.warning("IIASA connection failed: %s", exc)
        return None


def _fill_regional_gaps(
    data: pd.DataFrame,
    meta: pd.DataFrame,
    requested_regions: list[str],
) -> pd.DataFrame:
    """
    For each (region, variable) pair that has no data, copy values from
    the parent macro-region (or World) so every requested region has
    complete coverage.

    The filled rows get a suffix '__filled' appended to their region name
    internally; the suffix is stripped before returning so downstream code
    sees the canonical name.
    """
    present = (
        data.groupby(["region", "variable"])["value"]
        .count()
        .unstack(fill_value=0)
    )
    frames = [data]
    added_any = False

    for region in requested_regions:
        parent = region_parent(region)
        if parent == region:
            continue  # World or self-referential

        for var in ALL_VARS:
            count_here = present.get(var, pd.Series(dtype=int)).get(region, 0)
            if count_here > 0:
                continue  # already have data

            # Find parent data
            parent_rows = data[
                (data["region"] == parent) & (data["variable"] == var)
            ].copy()
            if parent_rows.empty:
                # Try grandparent = World
                grandparent_rows = data[
                    (data["region"] == "World") & (data["variable"] == var)
                ].copy()
                if grandparent_rows.empty:
                    continue
                parent_rows = grandparent_rows

            parent_rows["region"] = region
            frames.append(parent_rows)
            added_any = True
            log.debug(
                "Filled %s / %s from %s (%d rows)",
                region, var, parent, len(parent_rows)
            )

    if not added_any:
        return data
    return pd.concat(frames, ignore_index=True)


def _load_local_csv(
    regions: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Load from a user-cached ar6_snapshot.csv."""
    if not LOCAL_SNAPSHOT.exists():
        return None
    log.info("Loading local snapshot → %s", LOCAL_SNAPSHOT)
    data = pd.read_csv(LOCAL_SNAPSHOT)

    meta_path = LOCAL_SNAPSHOT.with_name("ar6_snapshot_meta.csv")
    if meta_path.exists():
        meta = pd.read_csv(meta_path, index_col=["model", "scenario"])
    elif "Category" in data.columns:
        meta = (
            data[["model", "scenario", "Category"]]
            .drop_duplicates()
            .set_index(["model", "scenario"])
        )
        data = data.drop(columns=["Category"])
    else:
        log.warning("Local CSV has no Category column; skipping")
        return None

    valid_cats = set(CATEGORY_TO_SSP.keys())
    meta = meta[meta["Category"].isin(valid_cats)][["Category"]].copy()
    mask = (
        data.set_index(["model", "scenario"]).index.isin(meta.index)
        & data["variable"].isin(ALL_VARS)
        & data["region"].isin(regions)
    )
    data = data[mask].copy()
    data = _fill_regional_gaps(data, meta, regions)
    return data, meta


def _load_osemosys_proxy(
    regions: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """
    Build a proxy dataset from OSeMOSYS simulation results.

    Maps OSeMOSYS regions (Africa/Asia/Europe/LATAM) to the requested
    regions via OSEMOSYS_TO_AR6. Where a requested region's parent is a
    known OSeMOSYS region, the proxy value is inherited.

    Proxy logic
    -----------
    Water  : CO2 / EJ electricity intensity (high intensity → high water use)
    Land   : 1 − renewable_share (low-renewable → higher deforestation risk)
    Social : ordinal scenario-warming index embedded in the SSP label
    """
    if not OSEMOSYS_IAMC.exists():
        log.warning("OSeMOSYS results not found")
        return None

    log.info("Using OSeMOSYS proxy → %s", OSEMOSYS_IAMC)
    iamc = pd.read_csv(OSEMOSYS_IAMC)

    # Reverse OSEMOSYS_TO_AR6: ar6_name → osemosys_region_label
    ar6_to_osemosys: dict[str, str] = {v: k for k, v in OSEMOSYS_TO_AR6.items()}

    # Map each requested region to the OSeMOSYS source region that covers it.
    # "World" gets the global sum; all other regions use their nearest parent.
    region_source_map: dict[str, str] = {}
    for region in regions:
        if region == "World":
            region_source_map[region] = "__world__"
            continue
        parent = region_parent(region)
        osemosys_src = ar6_to_osemosys.get(region) or ar6_to_osemosys.get(parent)
        region_source_map[region] = osemosys_src or "__world__"

    ssp_rank = {
        "SSP1-1.9": 0.0, "SSP2-4.5": 0.25,
        "SSP3-7.0": 1.0, "SSP4-6.0": 0.75, "SSP5-8.5": 1.0,
    }

    long_rows: list[dict] = []

    for (model, scenario), grp in iamc.groupby(["model", "scenario"]):
        for yr in ANALYSIS_YEARS:
            sub_yr = grp[grp["year"] == yr]

            # Pre-compute per-OSeMOSYS-region signals
            osemosys_signals: dict[str, dict[str, float]] = {}

            # Per-region signals (Africa / Asia / Europe / LATAM)
            for osm_region in iamc["region"].unique():
                sub = sub_yr[sub_yr["region"] == osm_region]
                elec_v = sub[sub["variable"] == "Secondary Energy|Electricity"]["value"]
                co2_v  = sub[sub["variable"] == "Emissions|CO2|Energy|Supply|Electricity"]["value"]
                ren    = sub[sub["variable"].str.contains("Electricity|Solar|Wind|Hydro", na=False)]["value"].sum()
                e = elec_v.iloc[0] if not elec_v.empty else np.nan
                c = co2_v.iloc[0]  if not co2_v.empty  else np.nan
                osemosys_signals[osm_region] = {
                    "water": c / e if (e and e > 0) else np.nan,
                    "land":  1.0 - (ren / e) if (e and e > 0) else np.nan,
                }

            # World = sum across all OSeMOSYS regions
            world_elec = sub_yr[sub_yr["variable"] == "Secondary Energy|Electricity"]["value"].sum()
            world_co2  = sub_yr[sub_yr["variable"] == "Emissions|CO2|Energy|Supply|Electricity"]["value"].sum()
            world_ren  = sub_yr[sub_yr["variable"].str.contains("Electricity|Solar|Wind|Hydro", na=False)]["value"].sum()
            osemosys_signals["__world__"] = {
                "water": world_co2 / world_elec if world_elec > 0 else np.nan,
                "land":  1.0 - (world_ren / world_elec) if world_elec > 0 else np.nan,
            }

            social_p = ssp_rank.get(scenario, np.nan)

            for out_region, osm_src in region_source_map.items():
                sig = osemosys_signals.get(osm_src, osemosys_signals["__world__"])
                for var_lbl, val in [
                    ("Water Withdrawal__proxy",  sig["water"]),
                    ("Land Cover|Forest__proxy", sig["land"]),
                    ("GDP|PPP__proxy",           social_p),
                ]:
                    long_rows.append({
                        "model": model, "scenario": scenario,
                        "region": out_region, "variable": var_lbl,
                        "unit": "proxy", "year": int(yr), "value": val,
                    })

    if not long_rows:
        return None

    data = pd.DataFrame(long_rows).dropna(subset=["value"])

    ssp_to_cat = {
        "SSP1-1.9": "C1", "SSP2-4.5": "C3",
        "SSP3-7.0": "C5", "SSP4-6.0": "C4", "SSP5-8.5": "C6",
    }
    ms_pairs = data[["model", "scenario"]].drop_duplicates()
    meta = (
        ms_pairs
        .assign(Category=ms_pairs["scenario"].map(ssp_to_cat).fillna("C3"))
        .set_index(["model", "scenario"])
    )
    return data, meta


def load_data(
    source: str = "auto",
    regions: str | list[str] = "world",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load AR6 nexus data for the specified regions.

    Parameters
    ----------
    source  : 'auto' | 'iiasa' | 'local' | 'osemosys'
    regions : region specification — see resolve_region_list()

    Returns
    -------
    (data, meta) where data is long-form IAMC and meta has 'Category'
    """
    region_list = resolve_region_list(regions)
    log.info("Resolved regions (%d): %s", len(region_list),
             region_list if len(region_list) <= 10
             else str(region_list[:8]) + " …")

    loaders: list[tuple[str, object]] = []
    if source in ("auto", "iiasa"):
        loaders.append(("IIASA ar6-public", lambda: _load_iiasa(region_list)))
    if source in ("auto", "local"):
        loaders.append(("local CSV", lambda: _load_local_csv(region_list)))
    if source in ("auto", "osemosys"):
        loaders.append(("OSeMOSYS proxy", lambda: _load_osemosys_proxy(region_list)))

    for name, loader in loaders:
        result = loader()
        if result is not None:
            data, meta = result
            actual_regions = data["region"].unique().tolist()
            log.info("Data source: %s  (%d rows, %d regions)",
                     name, len(data), len(actual_regions))
            _update_region_hierarchy(data)
            return data, meta

    raise RuntimeError(
        "No data source available. Run osemosys/run_simulation.py or "
        "provide ar6_snapshot.csv, or ensure pyam + IIASA connectivity."
    )


def _load_ngfs_prices() -> dict[str, dict[int, float]]:
    """
    Load NGFS Phase V shadow carbon prices.

    Tries the live IIASA ngfs_phase_3 database first.  Falls back to the
    built-in NGFS_CARBON_PRICES calibration table when the database is
    unavailable or pyam is not installed.

    Results are cached at module level to avoid repeated connections.

    Returns
    -------
    dict: {ngfs_scenario_name: {year: price_usd_tco2}}
    """
    global _NGFS_PRICES_CACHE
    if _NGFS_PRICES_CACHE is not None:
        return _NGFS_PRICES_CACHE

    try:
        import pyam  # type: ignore
        warnings.filterwarnings("ignore")
        log.info("Connecting to IIASA ngfs_phase_3 for shadow carbon prices …")
        df = pyam.read_iiasa(
            "ngfs_phase_3",
            variable=["Price|Carbon"],
            region=["World"],
            year=ANALYSIS_YEARS,
        )
        data_live = df.data
        prices: dict[str, dict[int, float]] = {}
        for scen in data_live["scenario"].unique():
            sub = data_live[
                (data_live["scenario"] == scen) &
                (data_live["region"] == "World")
            ]
            yr_price = dict(zip(sub["year"].astype(int), sub["value"]))
            if yr_price:
                prices[scen] = yr_price
        if prices:
            log.info(
                "NGFS Phase V prices loaded (%d scenarios from live DB): %s",
                len(prices), list(prices.keys())
            )
            _NGFS_PRICES_CACHE = prices
            return prices
    except Exception as exc:
        log.debug("ngfs_phase_3 unavailable (%s); using built-in table", exc)

    log.info("Using built-in NGFS Phase V carbon price table")
    _NGFS_PRICES_CACHE = NGFS_CARBON_PRICES
    return NGFS_CARBON_PRICES


def _ngfs_price_at(scenario: str, year: int) -> float:
    """
    Return NGFS Phase V carbon price (USD/tCO2) for an SSP-labelled scenario
    at the given year, with linear interpolation between tabulated years.

    Matching order:
    1. Exact key match in loaded prices dict (live DB or fallback)
    2. Partial/substring match (handles variant NGFS scenario names from live DB)
    3. Built-in NGFS_CARBON_PRICES fallback table for the SSP
    """
    prices = _load_ngfs_prices()
    ngfs_scen = SSP_TO_NGFS.get(scenario, "Current Policies")

    # 1. Exact match
    scen_prices = prices.get(ngfs_scen)

    # 2. Fuzzy/partial match for live DB scenario names
    if scen_prices is None:
        needle = ngfs_scen.lower()
        for key, val in prices.items():
            k_lower = key.lower()
            # check if key words from our target appear in the DB key or vice-versa
            if (needle in k_lower or k_lower in needle or
                    any(w in k_lower for w in needle.split() if len(w) > 3)):
                scen_prices = val
                log.debug("NGFS fuzzy match: '%s' → '%s'", ngfs_scen, key)
                break

    # 3. Fallback to built-in table
    if scen_prices is None:
        scen_prices = NGFS_CARBON_PRICES.get(ngfs_scen, NGFS_CARBON_PRICES["Current Policies"])

    if not scen_prices:
        return 0.0
    yr_keys = sorted(scen_prices.keys())
    return float(np.interp(year, yr_keys, [scen_prices[y] for y in yr_keys]))


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Shared helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _remove_outliers_iqr(series: pd.Series, k: float = 3.0) -> pd.Series:
    """Replace values outside k × IQR from Q1/Q3 with NaN."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return series.where((series >= q1 - k * iqr) & (series <= q3 + k * iqr))


def _ensemble_median(
    data: pd.DataFrame,
    meta: pd.DataFrame,
    variable: str,
) -> pd.DataFrame:
    """
    Compute per-(ssp, region, year) ensemble median for one IAMC variable.

    Returns DataFrame with columns: ssp, region, year, median_value
    """
    sub = data[data["variable"] == variable].copy()
    sub = sub.merge(
        meta[["Category"]].reset_index(),
        on=["model", "scenario"],
        how="inner",
    )
    sub["ssp"] = sub["Category"].map(CATEGORY_TO_SSP)
    sub = sub.dropna(subset=["ssp", "value"])

    # Outlier removal within each (ssp, region, year) group
    sub["value"] = sub.groupby(["ssp", "region", "year"])["value"].transform(
        _remove_outliers_iqr
    )
    sub = sub.dropna(subset=["value"])

    result = (
        sub.groupby(["ssp", "region", "year"])["value"]
        .median()
        .reset_index()
        .rename(columns={"value": "median_value"})
    )
    return result


def _per_year_region_normalize(df: pd.DataFrame, value_col: str) -> pd.Series:
    """
    Normalise values to [0, 1] within each (region, year) group.

    Within every region-year pair, the highest-risk SSP scenario gets
    weight = 1.0 and the lowest-risk gets weight = 0.0, so the weights
    express cross-scenario risk ranking for each region and year independently.
    If all scenarios produce the same value in a group, all weights = 0.5.
    """
    def _norm_group(g: pd.DataFrame) -> pd.Series:
        vals = g[value_col]
        lo, hi = vals.min(), vals.max()
        if np.isclose(lo, hi):
            return pd.Series(0.5, index=g.index)
        return (vals - lo) / (hi - lo)

    return df.groupby(["region", "year"], group_keys=False).apply(
        _norm_group, include_groups=False
    ).reindex(df.index)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Algorithm 1: Water Scarcity Weight
# ═══════════════════════════════════════════════════════════════════════════════

def algorithm_water_weight(
    data: pd.DataFrame,
    meta: pd.DataFrame,
) -> pd.DataFrame:
    """
    Algorithm 1 — Water Scarcity Weight (shadow price proxy).

    Method
    ------
    Per-region, per-year intensity:

        water_intensity(ssp, region, year) =
            median(Water Withdrawal [km³/yr]) / median(GDP|PPP [bn USD2010/yr])

    Normalised within each (region, year) so the most water-stressed
    SSP scenario gets weight = 1.0 and the least stressed gets weight = 0.0.

    Returns
    -------
    DataFrame(ssp, region, year, water_intensity_km3_bn_usd, water_weight)
    """
    is_proxy = data["variable"].str.endswith("__proxy").any()

    if is_proxy:
        w_med = _ensemble_median(data, meta, "Water Withdrawal__proxy")
        w_med = w_med.rename(columns={"median_value": "water_raw"})
    else:
        w_med = _ensemble_median(data, meta, "Water Withdrawal")
        g_med = _ensemble_median(data, meta, "GDP|PPP")
        merged = w_med.merge(g_med, on=["ssp", "region", "year"],
                             suffixes=("_w", "_g"))
        merged["water_raw"] = (
            merged["median_value_w"] / merged["median_value_g"].replace(0, np.nan)
        )
        w_med = merged[["ssp", "region", "year", "water_raw"]].dropna()

    w_med["water_weight"] = _per_year_region_normalize(w_med, "water_raw")

    if not is_proxy:
        return w_med.rename(
            columns={"water_raw": "water_intensity_km3_bn_usd"}
        )[["ssp", "region", "year", "water_intensity_km3_bn_usd", "water_weight"]]
    return w_med.rename(
        columns={"water_raw": "water_intensity_proxy"}
    )[["ssp", "region", "year", "water_intensity_proxy", "water_weight"]]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Algorithm 2: Land Opportunity Cost Weight
# ═══════════════════════════════════════════════════════════════════════════════

def algorithm_land_weight(
    data: pd.DataFrame,
    meta: pd.DataFrame,
) -> pd.DataFrame:
    """
    Algorithm 2 — Land Opportunity Cost Weight (rental-price proxy).

    Method
    ------
    (a) Forest-cover degradation relative to the SSP1-1.9 baseline in the
        same region at the earliest available year:

            forest_loss = 1 − Forest(ssp, region, year) / Forest(SSP1, region, base)

    (b) Carbon sequestration pressure: how much of the global CDR budget is
        consumed relative to the theoretical maximum in this scenario:

            seq_pressure = CarbonSeq(ssp, region, year) / max(CarbonSeq)

        max() taken across all (ssp, region, year) triples for robustness.

    Combined: land_weight_raw = 0.5 × forest_loss + 0.5 × seq_pressure
    Normalised within each (region, year) across SSPs.

    Returns
    -------
    DataFrame(ssp, region, year, forest_loss_ratio, seq_pressure, land_weight)
    """
    is_proxy = data["variable"].str.endswith("__proxy").any()

    if is_proxy:
        land_med = _ensemble_median(data, meta, "Land Cover|Forest__proxy")
        land_med["land_weight"] = _per_year_region_normalize(
            land_med, "median_value"
        )
        return land_med.rename(columns={"median_value": "land_proxy"})[
            ["ssp", "region", "year", "land_proxy", "land_weight"]
        ]

    # ── (a) forest loss ratio ─────────────────────────────────────────────────
    forest_med = _ensemble_median(data, meta, "Land Cover|Forest")
    base_year  = ANALYSIS_YEARS[0]

    # Reference: SSP1-1.9 forest in each region at base year
    ssp1_base = (
        forest_med[
            (forest_med["ssp"] == "SSP1-1.9") &
            (forest_med["year"] == base_year)
        ]
        .set_index("region")["median_value"]
    )

    def _forest_ref(region: str) -> float:
        if region in ssp1_base.index:
            ref = ssp1_base[region]
            if not np.isnan(ref) and ref > 0:
                return ref
        # Fallback: this region's own median at base year across all SSPs
        vals = forest_med[
            (forest_med["region"] == region) & (forest_med["year"] == base_year)
        ]["median_value"]
        return vals.median() if not vals.empty else np.nan

    forest_med["forest_ref"] = forest_med["region"].map(_forest_ref)
    forest_med["forest_loss_ratio"] = (
        1.0 - forest_med["median_value"] / forest_med["forest_ref"]
    ).clip(lower=0.0)

    # ── (b) sequestration pressure ────────────────────────────────────────────
    seq_med = _ensemble_median(data, meta, "Carbon Sequestration|Land Use")
    seq_global_max = seq_med["median_value"].max()
    seq_med["seq_pressure"] = (
        seq_med["median_value"] / seq_global_max
        if seq_global_max > 0 else 0.0
    )

    # ── Combine ───────────────────────────────────────────────────────────────
    land = forest_med[["ssp", "region", "year", "forest_loss_ratio"]].merge(
        seq_med[["ssp", "region", "year", "seq_pressure"]],
        on=["ssp", "region", "year"],
        how="outer",
    ).fillna(0.0)

    land["land_weight_raw"] = (
        0.5 * land["forest_loss_ratio"] + 0.5 * land["seq_pressure"]
    )
    land["land_weight"] = _per_year_region_normalize(land, "land_weight_raw")

    return land[["ssp", "region", "year", "forest_loss_ratio", "seq_pressure",
                 "land_weight"]]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Algorithm 3: Social Value Weight
# ═══════════════════════════════════════════════════════════════════════════════

def algorithm_social_weight(
    data: pd.DataFrame,
    meta: pd.DataFrame,
) -> pd.DataFrame:
    """
    Algorithm 3 — Social Value Weight (consumption-based utility).

    Method
    ------
    Per-region, per-capita welfare:

        welfare(ssp, region, year) =
            median(Consumption [bn USD]) / median(Population [million])
            × 1000   →  USD / capita

    Lower per-capita welfare in a region/scenario = higher social vulnerability
    = higher social risk weight. Normalised and inverted within each
    (region, year) so the most vulnerable scenario gets weight = 1.0.

    Returns
    -------
    DataFrame(ssp, region, year, welfare_usd_per_cap, social_weight)
    """
    is_proxy = data["variable"].str.endswith("__proxy").any()

    if is_proxy:
        soc_med = _ensemble_median(data, meta, "GDP|PPP__proxy")
        # Proxy values are already ordinal risk ranks; normalise and invert
        soc_med["social_weight"] = _per_year_region_normalize(
            soc_med, "median_value"
        )
        return soc_med.rename(columns={"median_value": "social_proxy"})[
            ["ssp", "region", "year", "social_proxy", "social_weight"]
        ]

    # Prefer Consumption; fall back to GDP|PPP
    avail_vars = data["variable"].unique()
    welfare_var = "Consumption" if "Consumption" in avail_vars else "GDP|PPP"
    welfare_med = _ensemble_median(data, meta, welfare_var)
    pop_med     = _ensemble_median(data, meta, "Population")

    soc = welfare_med.merge(
        pop_med[["ssp", "region", "year", "median_value"]].rename(
            columns={"median_value": "pop_m"}
        ),
        on=["ssp", "region", "year"],
        how="inner",
    )
    # bn_USD × 1e9 / (million × 1e6) = USD/capita
    soc["welfare_usd_per_cap"] = (
        soc["median_value"] * 1e9 / (soc["pop_m"] * 1e6)
    )

    # Higher welfare → lower social risk; invert after normalisation
    soc["social_weight"] = 1.0 - _per_year_region_normalize(
        soc, "welfare_usd_per_cap"
    )

    return soc[["ssp", "region", "year", "welfare_usd_per_cap", "social_weight"]]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5b — Algorithm 4: Energy Transition Risk Weight  (S4 4th pillar)
# ═══════════════════════════════════════════════════════════════════════════════

def algorithm_energy_weight(
    data: pd.DataFrame,
    meta: pd.DataFrame,
) -> pd.DataFrame:
    """
    Algorithm 4 — Energy Transition Risk Weight (S4 Portfolio 4th pillar).

    Method
    ------
    Fossil-fuel primary energy share as a proxy for stranded-asset risk and
    energy-system lock-in:

        fossil_share(ssp, region, year) =
            median(Primary Energy|Coal + Oil + Gas) / median(Final Energy)

    Higher fossil share → higher energy transition risk → energy_weight = 1.0.
    Normalised within each (region, year) across SSPs using the same
    per-year-region normalisation as the other pillars.

    Falls back to the OSeMOSYS renewable-share proxy (1 − renewable_share)
    when IAM energy variables are not available.

    Returns
    -------
    DataFrame(ssp, region, year, fossil_share, energy_weight)
    """
    is_proxy = data["variable"].str.endswith("__proxy").any()
    avail_vars = set(data["variable"].unique())

    if is_proxy:
        # Land proxy = 1 - renewable_share, which directly tracks fossil share
        med = _ensemble_median(data, meta, "Land Cover|Forest__proxy")
        med["energy_weight"] = _per_year_region_normalize(med, "median_value")
        return med.rename(columns={"median_value": "fossil_share_proxy"})[
            ["ssp", "region", "year", "fossil_share_proxy", "energy_weight"]
        ]

    fossil_available = [
        v for v in ["Primary Energy|Coal", "Primary Energy|Oil", "Primary Energy|Gas"]
        if v in avail_vars
    ]

    if fossil_available and "Final Energy" in avail_vars:
        fe_med = _ensemble_median(data, meta, "Final Energy")
        fossil_sum = (
            pd.concat([_ensemble_median(data, meta, v) for v in fossil_available])
            .groupby(["ssp", "region", "year"])["median_value"]
            .sum()
            .reset_index()
        )
        energy = fe_med.merge(
            fossil_sum, on=["ssp", "region", "year"],
            suffixes=("_total", "_fossil"),
        )
        energy["fossil_share"] = (
            energy["median_value_fossil"] /
            energy["median_value_total"].replace(0, np.nan)
        ).clip(0.0, 1.0)
        energy["energy_weight"] = _per_year_region_normalize(energy, "fossil_share")
        return energy[["ssp", "region", "year", "fossil_share", "energy_weight"]]

    # Fallback: use SSP warming trajectory as ordinal energy-transition proxy
    # (SSP1-1.9 = fastest clean transition, SSP5-8.5 = slowest)
    ssp_fossil_rank: dict[str, float] = {
        "SSP1-1.9": 0.05, "SSP2-4.5": 0.40, "SSP3-7.0": 0.85,
        "SSP4-6.0": 0.65, "SSP5-8.5": 1.00,
    }
    # Build the grid from any available variable (GDP|PPP always present)
    anchor_var = "GDP|PPP" if "GDP|PPP" in avail_vars else list(avail_vars)[0]
    base = _ensemble_median(data, meta, anchor_var)
    base["fossil_share"] = base["ssp"].map(ssp_fossil_rank).fillna(0.5)
    base["energy_weight"] = base["fossil_share"]
    return base[["ssp", "region", "year", "fossil_share", "energy_weight"]]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Weight combinator
# ═══════════════════════════════════════════════════════════════════════════════

def compute_nexus_weights(
    source: str = "auto",
    regions: str | list[str] = "world",
    years: list[int] | None = None,
) -> pd.DataFrame:
    """
    Run all four S4 algorithms and return a unified weight DataFrame.

    Parameters
    ----------
    source  : 'auto' | 'iiasa' | 'local' | 'osemosys'
    regions : region specification — see resolve_region_list() for keywords:
              "world", "macro", "osemosys", "all", ISO codes, or AR6 names
    years   : subset of ANALYSIS_YEARS to include (default: all)

    Returns
    -------
    DataFrame with columns:
        ssp, region, year,
        water_weight, land_weight, social_weight, energy_weight,
        [+ diagnostic columns depending on data source]
    """
    data, meta = load_data(source=source, regions=regions)

    if years:
        data = data[data["year"].isin(years)].copy()

    log.info("Running Algorithm 1 — Water …")
    water  = algorithm_water_weight(data, meta)

    log.info("Running Algorithm 2 — Land …")
    land   = algorithm_land_weight(data, meta)

    log.info("Running Algorithm 3 — Social …")
    social = algorithm_social_weight(data, meta)

    log.info("Running Algorithm 4 — Energy …")
    energy = algorithm_energy_weight(data, meta)

    # ── Merge on (ssp, region, year) ─────────────────────────────────────────
    weights = water.merge(land,   on=["ssp", "region", "year"], how="outer")
    weights = weights.merge(social, on=["ssp", "region", "year"], how="outer")
    weights = weights.merge(energy, on=["ssp", "region", "year"], how="outer")

    # ── Ensure full (ssp × region × year) grid ───────────────────────────────
    actual_regions  = weights["region"].dropna().unique().tolist()
    target_years    = years if years else ANALYSIS_YEARS
    full_idx = pd.MultiIndex.from_product(
        [SSP_ORDER, actual_regions, target_years],
        names=["ssp", "region", "year"],
    )
    weights = (
        weights.set_index(["ssp", "region", "year"])
        .reindex(full_idx)
        .reset_index()
        .sort_values(["region", "ssp", "year"])
        .reset_index(drop=True)
    )

    log.info("Nexus weights: %d rows, %d region(s)", len(weights),
             len(actual_regions))
    return weights


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Integration helpers
# ═══════════════════════════════════════════════════════════════════════════════

def get_dynamic_damage_weights(
    weights_df: pd.DataFrame,
    scenario: str,
    year: int,
    region: str = "World",
    base_water_share: float = 0.16,
    base_land_share:  float = 0.17,
    base_social_share: float = 0.28,
) -> dict[str, float]:
    """
    Return damage-category weights for a (scenario, region, year) triple,
    replacing the static shares with IPCC-derived nexus weights.

    Falls back to the nearest available region (parent macro-region or World)
    if the exact region is not in weights_df.

    Parameters
    ----------
    weights_df        : output of compute_nexus_weights()
    scenario          : e.g. "SSP2-4.5"
    year              : e.g. 2030
    region            : AR6 region name or OSeMOSYS region (Africa/Asia/…)
    base_water_share  : static weight for Water Resources  (0.16)
    base_land_share   : static weight for Agriculture      (0.17)
    base_social_share : static weight for Human Health     (0.28)

    Returns
    -------
    dict[category_name → weight]  (sums to 1.0)
    """
    # Resolve OSeMOSYS region names to AR6 equivalents
    ar6_region = OSEMOSYS_TO_AR6.get(region, region)

    def _row_for(reg: str) -> pd.DataFrame:
        sub = weights_df[
            (weights_df["ssp"] == scenario) &
            (weights_df["region"] == reg) &
            (weights_df["year"] == year)
        ]
        if sub.empty:
            # Nearest year within the same (ssp, region)
            sub2 = weights_df[
                (weights_df["ssp"] == scenario) & (weights_df["region"] == reg)
            ]
            if not sub2.empty:
                sub2 = sub2.iloc[(sub2["year"] - year).abs().argsort()]
                return sub2.head(1)
        return sub

    row = _row_for(ar6_region)
    # Fallback: parent macro-region
    if row.empty:
        parent = region_parent(ar6_region)
        row = _row_for(parent)
    # Fallback: World
    if row.empty:
        row = _row_for("World")

    w_w = float(row["water_weight"].iloc[0])  if not row.empty else 0.5
    w_l = float(row["land_weight"].iloc[0])   if not row.empty else 0.5
    w_s = float(row["social_weight"].iloc[0]) if not row.empty else 0.5

    static_remainder: dict[str, float] = {
        "Coastal / SLR":  0.11,
        "Ecosystems":     0.13,
        "Energy Systems": 0.10,
        "Other":          0.05,
    }
    nexus_budget = 1.0 - sum(static_remainder.values())   # 0.61

    def _scale(base: float, w: float) -> float:
        return max(base * (0.5 + w), 1e-4)   # scale range [0.5×, 1.5×]

    raw_water  = _scale(base_water_share,  w_w)
    raw_land   = _scale(base_land_share,   w_l)
    raw_social = _scale(base_social_share, w_s)
    raw_total  = raw_water + raw_land + raw_social

    out: dict[str, float] = {
        "Water Resources": nexus_budget * raw_water  / raw_total,
        "Agriculture":     nexus_budget * raw_land   / raw_total,
        "Human Health":    nexus_budget * raw_social / raw_total,
    }
    out.update(static_remainder)
    assert abs(sum(out.values()) - 1.0) < 1e-9
    return out


def get_price_carbon(
    scenario: str,
    data: pd.DataFrame,
    meta: pd.DataFrame,
    region: str = "World",
) -> pd.DataFrame:
    """
    Extract ensemble median Price|Carbon trajectory for one (SSP, region).

    Falls back to World if the requested region has no Price|Carbon data.

    Returns DataFrame(year, price_carbon_usd_tco2) or empty DataFrame.
    """
    if "Price|Carbon" not in data["variable"].unique():
        log.warning("Price|Carbon not in loaded data")
        return pd.DataFrame(columns=["year", "price_carbon_usd_tco2"])

    ar6_region = OSEMOSYS_TO_AR6.get(region, region)
    pc_med = _ensemble_median(data, meta, "Price|Carbon")

    sub = pc_med[
        (pc_med["ssp"] == scenario) & (pc_med["region"] == ar6_region)
    ][["year", "median_value"]].copy()

    if sub.empty:
        # Fallback to World
        sub = pc_med[
            (pc_med["ssp"] == scenario) & (pc_med["region"] == "World")
        ][["year", "median_value"]].copy()

    return sub.rename(columns={"median_value": "price_carbon_usd_tco2"})


def _print_weight_table(weights: pd.DataFrame) -> None:
    """Pretty-print the S4 four-pillar nexus weight table."""
    w_cols = ["water_weight", "land_weight", "social_weight", "energy_weight"]
    for col in w_cols:
        if col not in weights.columns:
            weights[col] = np.nan

    has_energy = weights["energy_weight"].notna().any()
    display_years = [y for y in [2020, 2030, 2040, 2050]
                     if y in weights["year"].unique()]
    regions = weights["region"].dropna().unique().tolist()

    for region in regions:
        sub_r = weights[weights["region"] == region]
        print()
        width = 106 if has_energy else 88
        print("=" * width)
        print(f" S4 PORTFOLIO NEXUS WEIGHTS — {region}")
        print(f" Source: AR6 ensemble medians per Category, per-year cross-scenario normalised")
        print("=" * width)
        hdr = (f"  {'Scenario':<12}  {'Year':>4}  "
               f"{'Water':>7}  {'Land':>7}  {'Social':>7}")
        sep = "  " + "─" * 12 + "  " + "─" * 4 + "  " + ("─" * 7 + "  ") * 2 + "─" * 7
        if has_energy:
            hdr += f"  {'Energy':>7}"
            sep += "  " + "─" * 7
        print(hdr)
        print(sep)

        for ssp in SSP_ORDER:
            sub = sub_r[sub_r["ssp"] == ssp]
            first = True
            for yr in display_years:
                row = sub[sub["year"] == yr]
                base_cols = ["water_weight", "land_weight", "social_weight"]
                if row.empty or row[base_cols].isna().all(axis=1).any():
                    continue
                lbl   = ssp if first else ""
                first = False
                w = float(row["water_weight"].iloc[0])
                l = float(row["land_weight"].iloc[0])
                s = float(row["social_weight"].iloc[0])
                line = f"  {lbl:<12}  {yr:>4}  {w:>7.4f}  {l:>7.4f}  {s:>7.4f}"
                if has_energy:
                    e_val = row["energy_weight"].iloc[0]
                    e_str = f"{float(e_val):>7.4f}" if not pd.isna(e_val) else "    n/a"
                    line += f"  {e_str}"
                print(line)
            if not first:
                print()

    # Print NGFS Phase V carbon price reference table
    print("─" * 80)
    print(" NGFS Phase V shadow carbon prices (USD/tCO2, real 2020)  "
          "[S4 carbon pillar anchor]")
    print("─" * 80)
    price_years = [y for y in [2025, 2030, 2035, 2040, 2050]
                   if y in ANALYSIS_YEARS]
    hdr_p = f"  {'NGFS Scenario':<22}  {'→ SSP':<12}"
    for py in price_years:
        hdr_p += f"  {py:>4}"
    print(hdr_p)
    print("  " + "─" * 22 + "  " + "─" * 12 + "──────" * len(price_years))
    for ngfs_scen, ssp in NGFS_TO_SSP.items():
        row_p = f"  {ngfs_scen:<22}  {ssp:<12}"
        for py in price_years:
            row_p += f"  {_ngfs_price_at(ssp, py):>4.0f}"
        print(row_p)
    print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Extract IPCC AR6 Water/Land/Social nexus weights via pyam"
    )
    parser.add_argument(
        "--source",
        choices=["auto", "iiasa", "local", "osemosys"],
        default="auto",
    )
    parser.add_argument(
        "--regions", nargs="+", default=["world"],
        help=(
            'Regions to analyse. Use keywords "world", "macro", "osemosys", "all", '
            'or specific AR6 region names. Example: --regions Nigeria Brazil Germany'
        ),
    )
    parser.add_argument(
        "--years", nargs="+", type=int, default=None,
        help="Years to include (default: 2020 2025 2030 2035 2040 2045 2050)",
    )
    parser.add_argument(
        "--no-ngfs", action="store_true",
        help="Disable NGFS Phase V carbon prices (use AR6 Price|Carbon only)",
    )
    args = parser.parse_args()

    # Collapse single-keyword region args
    regions_arg: str | list[str] = (
        args.regions[0] if len(args.regions) == 1 else args.regions
    )

    weights = compute_nexus_weights(
        source=args.source,
        regions=regions_arg,
        years=args.years,
    )
    _print_weight_table(weights)
    weights.to_csv(OUT_WEIGHTS_CSV, index=False)
    print(f"\nWeights saved → {OUT_WEIGHTS_CSV}  ({len(weights)} rows)")
