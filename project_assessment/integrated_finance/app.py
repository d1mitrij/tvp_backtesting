"""
integrated_finance/app.py
=========================
Streamlit application for Integrated Finance Analysis.
Consolidates all 9 per-project notebooks into a single interactive app.

Usage (from project_assessment/ directory):
    streamlit run integrated_finance/app.py

Or from the integrated_finance/ directory:
    streamlit run app.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import streamlit as st
from scipy.optimize import brentq

# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP
# ─────────────────────────────────────────────────────────────────────────────
APP_DIR   = Path(__file__).parent           # integrated_finance/
PA_DIR    = APP_DIR.parent                  # project_assessment/
REPO_ROOT = PA_DIR.parent                   # tvp5/

for _p in [str(REPO_ROOT / "tvp_dbio"),
           str(REPO_ROOT / "tvp_dependency"),
           str(PA_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

INTENSITY_CSV = (
    REPO_ROOT / "tvp_scenario" / "osemosys" / "results"
    / "tvpdbio_intensity_factors.csv"
)

# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS  (graceful fallbacks so UI still loads)
# ─────────────────────────────────────────────────────────────────────────────
IO_AVAILABLE    = False
DEP_AVAILABLE   = False
ASSESS_AVAILABLE = False

try:
    from tvp_io_lib import (
        tier0_impact, tier1_impact, tier_impact,
        ISO2_TO_REGION, SECTOR_ALLOC,
    )
    IO_AVAILABLE = True
except ImportError:
    tier0_impact = tier1_impact = tier_impact = None  # type: ignore[assignment]

try:
    from dependency_profiler.encore_materiality import get_materiality_profile
    from dependency_profiler.wwf_risk_filter import (
        score_project, REGIONAL_BASELINES, HIGH_RISK_THRESHOLD,
    )
    DEP_AVAILABLE = True
except ImportError:
    get_materiality_profile = score_project = None  # type: ignore[assignment]
    REGIONAL_BASELINES: list[str] = []
    HIGH_RISK_THRESHOLD = 3.5

try:
    from assess import (
        PROJECT_SECTOR_TO_ENCORE, STRESSOR_ECOSYSTEM_MAP,
        STRESSOR_WWF_COL, STRESSOR_SC_DEP_KEY, SC_SECTOR_DEP_PROFILE,
        DEP_NEUTRAL, REGION_TO_ISO3, PROJECT_SECTOR_TO_NACE,
        VF_FILE_SPECS, FTE_HOURS_PER_YEAR,
        _resolve_wifor_dir, _load_vf_coeff, _load_gva_per_hour,
    )
    ASSESS_AVAILABLE = True
except ImportError:
    DEP_NEUTRAL         = 3.0
    FTE_HOURS_PER_YEAR  = 1_880
    REGION_TO_ISO3      = {"LATAM": "BRA", "Africa": "NGA", "Asia": "IND", "Europe": "DEU"}
    PROJECT_SECTOR_TO_NACE = {
        "Health_Social": "Q", "Health_Specialized": "Q", "Health_General": "Q",
        "Energy": "D35", "Rail_Dev": "F", "Rail_Op": "H49",
    }
    PROJECT_SECTOR_TO_ENCORE = {}
    STRESSOR_ECOSYSTEM_MAP = {}
    STRESSOR_WWF_COL = {}
    STRESSOR_SC_DEP_KEY = {}
    SC_SECTOR_DEP_PROFILE = {}
    VF_FILE_SPECS = {}

    def _resolve_wifor_dir():   # type: ignore[misc]
        return None
    def _load_vf_coeff(*a, **kw):  # type: ignore[misc]
        return None
    def _load_gva_per_hour(*a, **kw):  # type: ignore[misc]
        return 0.0

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & COLOURS
# ─────────────────────────────────────────────────────────────────────────────
ALL_SSPS   = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP4-6.0", "SSP5-8.5"]
SSP_COLORS = {
    "SSP1-1.9": "#1a9641", "SSP2-4.5": "#a6d96a",
    "SSP3-7.0": "#fdae61", "SSP4-6.0": "#ffffbf", "SSP5-8.5": "#d73027",
}
COLS_SC = ["GHG_tCO2e", "Employment_FTE", "Water_1000m3", "ValueAdded_M$"]
C_NEG = "#d62728"; C_POS = "#2ca02c"; C_FIN = "#4e79a7"
C_GHG = "#e07070"; C_EMP = "#2ca02c"; C_WAT = "#1f77b4"; C_TOT = "#6b4c9a"

# ─────────────────────────────────────────────────────────────────────────────
# ROLE-BASED UX CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
ROLES: list[str] = [
    "Investment Officer",
    "Strategy Economist",
    "Portfolio Manager",
    "Compliance Specialist",
]

# Tab index map for existing 10 tabs (0-based):
# 0:Overview  1:IO Supply Chain  2:NPV/iNPV  3:S-IRR  4:WACC
# 5:Cash Flow  6:SSP Comparison  7:Project Profile  8:Methodology  9:Portfolio
ALL_TAB_LABELS: list[str] = [
    "Overview", "IO Supply Chain", "NPV / iNPV", "S-IRR", "WACC Adjustment",
    "Cash Flow Dashboard", "SSP Comparison", "Project Profile", "Methodology", "Portfolio",
]
ROLE_TABS: dict[str, list[int]] = {
    "Investment Officer":    [0, 2, 3, 4, 5, 6, 7, 8],
    "Strategy Economist":    [0, 6, 7, 8, 9],
    "Portfolio Manager":     [0, 5, 6, 9],
    "Compliance Specialist": [0, 7, 8],
}
ROLE_EXTRA_TAB: dict[str, str] = {
    "Investment Officer":    "Country Comparison",
    "Strategy Economist":    "Country Canvas",
    "Portfolio Manager":     "Risk Dashboard",
    "Compliance Specialist": "Regulatory Mapping",
}

# ─────────────────────────────────────────────────────────────────────────────
# EBRD ATQ CONSTANTS  (real 2024-25 data — ebrd_atq_scores_2024_25.csv)
# ─────────────────────────────────────────────────────────────────────────────
ATQ_DIMENSIONS: list[str] = [
    "Competitive", "Well_Governed", "Green", "Inclusive", "Resilient", "Integrated",
]
ATQ_DIM_LABELS: list[str] = [
    "Competitive", "Well Governed", "Green", "Inclusive", "Resilient", "Integrated",
]
# ISO-2 → ATQ CSV country name (full-name keys in ebrd_atq_scores_2024_25.csv)
ATQ_ISO2_TO_NAME: dict[str, str] = {
    "AL": "Albania", "AM": "Armenia", "AZ": "Azerbaijan",
    "BA": "Bosnia and Herzegovina", "BG": "Bulgaria",
    "BJ": "Benin", "CI": "Côte d'Ivoire", "CZ": "Czechia",
    "DE": "Germany",  # not in ATQ but useful for lookup below
    "EE": "Estonia", "EG": "Egypt", "GE": "Georgia",
    "GH": "Ghana", "GR": "Greece", "HR": "Croatia",
    "HU": "Hungary", "JO": "Jordan", "KE": "Kenya",
    "KG": "Kyrgyz Republic", "KZ": "Kazakhstan",
    "LB": "Lebanon", "LT": "Lithuania", "LV": "Latvia",
    "MA": "Morocco", "MD": "Moldova", "ME": "Montenegro",
    "MK": "North Macedonia", "MN": "Mongolia",
    "NG": "Nigeria", "PL": "Poland", "RO": "Romania",
    "RS": "Serbia", "SI": "Slovenia", "SK": "Slovak Republic",
    "SN": "Senegal", "TJ": "Tajikistan", "TM": "Turkmenistan",
    "TN": "Tunisia", "TR": "Türkiye", "UA": "Ukraine",
    "UZ": "Uzbekistan", "XK": "Kosovo",
}

# Broader ISO-2 → Global Footprint Network country name (for EarthOvershoot lookup)
_ISO2_TO_OVERSHOOT_NAME: dict[str, str] = {
    "AT": "Austria", "BE": "Belgium", "CH": "Switzerland",
    "CZ": "Czech Republic", "DE": "Germany", "DK": "Denmark",
    "ES": "Spain", "FI": "Finland", "FR": "France",
    "GB": "United Kingdom", "GR": "Greece", "HR": "Croatia",
    "HU": "Hungary", "IE": "Ireland", "IT": "Italy",
    "NL": "Netherlands", "NO": "Norway", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "SE": "Sweden",
    "SK": "Slovakia", "UA": "Ukraine",
    "AR": "Argentina", "BO": "Bolivia", "BR": "Brazil",
    "CL": "Chile", "CO": "Colombia", "EC": "Ecuador",
    "MX": "Mexico", "PE": "Peru", "PY": "Paraguay",
    "UY": "Uruguay", "VE": "Venezuela",
    "AO": "Angola", "DZ": "Algeria", "EG": "Egypt",
    "ET": "Ethiopia", "GH": "Ghana", "KE": "Kenya",
    "MA": "Morocco", "MZ": "Mozambique", "NG": "Nigeria",
    "SN": "Senegal", "TZ": "Tanzania", "UG": "Uganda",
    "ZA": "South Africa", "ZM": "Zambia", "ZW": "Zimbabwe",
    "BD": "Bangladesh", "CN": "China", "ID": "Indonesia",
    "IN": "India", "JP": "Japan", "KR": "South Korea",
    "MM": "Myanmar", "MY": "Malaysia", "PH": "Philippines",
    "PK": "Pakistan", "TH": "Thailand", "VN": "Vietnam",
}

# ─────────────────────────────────────────────────────────────────────────────
# ETI / AIMM SCORING CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SFB_SECTORS: dict[str, list[str]] = {
    "Rail_Dev":         ["Modal shift (%)", "Passenger-km added", "GHG avoided (tCO₂e/yr)"],
    "Rail_Op":          ["On-time performance (%)", "Energy efficiency gain (%)"],
    "Energy":           ["MWh generated", "New connections (#)", "Carbon intensity reduction (%)"],
    "Health_Social":    ["Patients served (#)", "Cost-per-DALY saved", "Beds added (#)"],
    "Health_Specialized": ["Surgeries/yr", "Beds (ICU) added (#)"],
    "Health_General":   ["Patients served (#)", "Beds added (#)"],
}
UPLIFT_ETI_DELTA: dict[str, float] = {
    "Local currency": 0.05, "Equity": 0.08,
    "SME focus": 0.04, "Climate-aligned": 0.06, "Inclusion focus": 0.05,
}

# ─────────────────────────────────────────────────────────────────────────────
# REGULATORY MATRIX (SFDR / TCFD / TNFD / SEC / EBRD ATQ / AIIB EP)
# ─────────────────────────────────────────────────────────────────────────────
JURISDICTIONS: list[str] = [
    "EU (SFDR/Taxonomy/CSRD)", "UK (TCFD)", "US (SEC Climate)",
    "TNFD", "EBRD ATQ", "AIIB EP",
]
REGULATORY_MATRIX: dict[str, dict] = {
    "EU (SFDR/Taxonomy/CSRD)": {
        "PAI — GHG intensity (SFDR Annex I #1)": {
            "model_field": "tier0_ghg",
            "description": "GHG emissions attributable to project per M USD invested",
            "threshold": None,
        },
        "PAI — Biodiversity (SFDR Annex I #7)": {
            "model_field": "dep_factor",
            "description": "ENCORE biodiversity materiality score",
            "threshold": 1.2,
        },
        "PAI — Water intensity (SFDR Annex I #6)": {
            "model_field": "wwf_score",
            "description": "WWF Water Risk Filter score (1–5)",
            "threshold": 3.0,
        },
        "EU Taxonomy — Climate Mitigation (Art. 10)": {
            "model_field": "tier0_ghg",
            "description": "Substantial contribution: positive GHG impact required",
            "threshold": 0,
        },
        "EU Taxonomy — DNSH Water (Art. 17)": {
            "model_field": "wwf_score",
            "description": "Do No Significant Harm: wwf_score must not exceed 3.5",
            "threshold": 3.5,
        },
        "CSRD — Double Materiality": {
            "model_field": "inpv_usd",
            "description": "Financial materiality of nature risk: dep_factor deviation from 1.0",
            "threshold": None,
        },
    },
    "UK (TCFD)": {
        "TCFD — Physical Risk (scenario analysis)": {
            "model_field": "inpv_usd",
            "description": "iNPV range across SSP1-1.9 to SSP5-8.5 constitutes scenario analysis",
            "threshold": None,
        },
        "TCFD — Transition Risk": {
            "model_field": "adj_ratio_ghg",
            "description": "SSP-driven GHG intensity adjustment = transition risk factor",
            "threshold": None,
        },
    },
    "US (SEC Climate)": {
        "SEC — Material GHG emissions": {
            "model_field": "tier0_ghg",
            "description": "Scope 1/2 GHG emissions of project operations",
            "threshold": None,
        },
        "SEC — Climate scenario analysis": {
            "model_field": "inpv_usd",
            "description": "Financial impact under at least one climate scenario",
            "threshold": None,
        },
    },
    "TNFD": {
        "TNFD LEAP — Locate (L)": {
            "model_field": "country",
            "description": "Country and region of operations identified",
            "threshold": None,
        },
        "TNFD LEAP — Evaluate (E)": {
            "model_field": "dep_factor",
            "description": "ENCORE dependency assessment completed (dep_factor computed)",
            "threshold": None,
        },
        "TNFD LEAP — Assess (A)": {
            "model_field": "wwf_score",
            "description": "WWF Water Risk Filter quantified",
            "threshold": None,
        },
        "TNFD LEAP — Prepare (P)": {
            "model_field": "nature_dividend_usd",
            "description": "Monetised nature dividend computed via WifOR VFs",
            "threshold": None,
        },
        "TNFD — Overshoot Contribution Index": {
            "model_field": "oci_pct",
            "description": "Project EF as % of host biocapacity; flag if OCI > 0.1 %",
            "threshold": 0.1,
        },
    },
    "EBRD ATQ": {
        "ATQ Green — GHG transition quality": {
            "model_field": "tier0_ghg",
            "description": "GHG avoided as evidence for Green transition quality (ATQ 'Green' dimension)",
            "threshold": 0,
        },
        "ATQ Green — OCI biophysical benchmark": {
            "model_field": "oci_pct",
            "description": "OCI as quantitative sub-indicator for Green transition quality gap",
            "threshold": 0.1,
        },
        "ATQ Resilient — nature dependency": {
            "model_field": "dep_factor_adj",
            "description": "BC-adjusted nature dependency loading; contributes to financial-sector resilience scoring",
            "threshold": 1.2,
        },
    },
    "AIIB EP": {
        "AIIB EP Category A — biodiversity": {
            "model_field": "dep_factor",
            "description": "High-dependency projects (dep_factor > 1.4) require full ESIA",
            "threshold": 1.4,
        },
        "AIIB EP — Water risk": {
            "model_field": "wwf_score",
            "description": "wwf_score > 3.0 triggers Water Management Plan requirement",
            "threshold": 3.0,
        },
    },
}

# Average IO intensities per $1M CAPEX (portfolio estimate, fallback for multi-project runner)
_INTENSITY_FALLBACK: dict[str, float] = {
    "GHG_tCO2e":     280.0,
    "Employment_FTE": 18.0,
    "Water_1000m3":   1.5,
    "ValueAdded_M$":  1.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT REGISTRY  (mirrors _build_integrated_notebooks.py PROJECTS list)
# ─────────────────────────────────────────────────────────────────────────────
EUR_TO_USD = 1.08
PROJECTS: list[dict] = [
    dict(project_id="Rail_EU_DEV", country="DE", region="Europe", sector="Rail_Dev",
         capex_usd=round(1_850_000_000 * EUR_TO_USD), avoided_co2=50_000,
         revenue_yield=0.12, opex_ratio=0.04, bond_years=10, project_years=30,
         wacc_base=0.065, scenario="SSP2-4.5",
         label="Rail EU DEV – Large-scale European rail development"),
    dict(project_id="Rail_EU_OP1", country="DE", region="Europe", sector="Rail_Op",
         capex_usd=round(130_000 * EUR_TO_USD), avoided_co2=0,
         revenue_yield=0.10, opex_ratio=0.06, bond_years=5, project_years=15,
         wacc_base=0.055, scenario="SSP2-4.5",
         label="Rail EU OP1 – Operational maintenance (EUR 130k)"),
    dict(project_id="Rail_EU_OP2", country="DE", region="Europe", sector="Rail_Op",
         capex_usd=round(90_000 * EUR_TO_USD), avoided_co2=0,
         revenue_yield=0.10, opex_ratio=0.06, bond_years=5, project_years=15,
         wacc_base=0.055, scenario="SSP2-4.5",
         label="Rail EU OP2 – Operational maintenance (EUR 90k)"),
    dict(project_id="Proj_001", country="BR", region="LATAM", sector="Health_Social",
         capex_usd=250_000_000, avoided_co2=0,
         revenue_yield=0.08, opex_ratio=0.06, bond_years=10, project_years=25,
         wacc_base=0.080, scenario="SSP2-4.5",
         label="Proj 001 – LATAM primary/preventative care hub (5M beneficiaries)"),
    dict(project_id="Proj_002", country="NG", region="Africa", sector="Health_Specialized",
         capex_usd=25_000_000, avoided_co2=0,
         revenue_yield=0.09, opex_ratio=0.07, bond_years=7, project_years=20,
         wacc_base=0.090, scenario="SSP2-4.5",
         label="Proj 002 – Africa tertiary surgical hospital (3k beneficiaries)"),
    dict(project_id="Proj_003", country="DE", region="Europe", sector="Health_General",
         capex_usd=75_000_000, avoided_co2=0,
         revenue_yield=0.09, opex_ratio=0.05, bond_years=10, project_years=25,
         wacc_base=0.060, scenario="SSP2-4.5",
         label="Proj 003 – European general hospital (500k beneficiaries)"),
    dict(project_id="Hydro_AF", country="NG", region="Africa", sector="Energy",
         capex_usd=30_000_000, avoided_co2=150_000,
         revenue_yield=0.11, opex_ratio=0.03, bond_years=10, project_years=30,
         wacc_base=0.085, scenario="SSP2-4.5",
         label="Hydro AF – Africa hydro refurbishment (150k tCO₂e/yr)"),
    dict(project_id="Hydro_AS", country="IN", region="Asia", sector="Energy",
         capex_usd=150_000_000, avoided_co2=834_218,
         revenue_yield=0.11, opex_ratio=0.03, bond_years=15, project_years=35,
         wacc_base=0.075, scenario="SSP2-4.5",
         label="Hydro AS – Asia large-scale hydro retrofit (834k tCO₂e/yr)"),
    dict(project_id="Hydro_EU", country="DE", region="Europe", sector="Energy",
         capex_usd=2_000_000, avoided_co2=6_126,
         revenue_yield=0.10, opex_ratio=0.04, bond_years=5, project_years=20,
         wacc_base=0.060, scenario="SSP2-4.5",
         label="Hydro EU – European efficiency tweak (6k tCO₂e/yr)"),
]
PROJECT_BY_ID = {p["project_id"]: p for p in PROJECTS}

# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY / SECTOR OPTION LISTS
# ─────────────────────────────────────────────────────────────────────────────
# ISO-2 → IO modelling region (4-region model)
COUNTRY_REGION_MAP: dict[str, str] = {
    # Europe
    "AT": "Europe", "BE": "Europe", "CH": "Europe", "CZ": "Europe",
    "DE": "Europe", "DK": "Europe", "ES": "Europe", "FI": "Europe",
    "FR": "Europe", "GB": "Europe", "GR": "Europe", "HR": "Europe",
    "HU": "Europe", "IE": "Europe", "IT": "Europe", "NL": "Europe",
    "NO": "Europe", "PL": "Europe", "PT": "Europe", "RO": "Europe",
    "SE": "Europe", "SK": "Europe", "UA": "Europe",
    # LATAM
    "AR": "LATAM",  "BO": "LATAM",  "BR": "LATAM",  "CL": "LATAM",
    "CO": "LATAM",  "EC": "LATAM",  "MX": "LATAM",  "PE": "LATAM",
    "PY": "LATAM",  "UY": "LATAM",  "VE": "LATAM",
    # Africa
    "AO": "Africa", "DZ": "Africa", "EG": "Africa", "ET": "Africa",
    "GH": "Africa", "KE": "Africa", "MA": "Africa", "MZ": "Africa",
    "NG": "Africa", "SN": "Africa", "TZ": "Africa", "UG": "Africa",
    "ZA": "Africa", "ZM": "Africa", "ZW": "Africa",
    # Asia
    "BD": "Asia",   "CN": "Asia",   "ID": "Asia",   "IN": "Asia",
    "JP": "Asia",   "KR": "Asia",   "MM": "Asia",   "MY": "Asia",
    "PH": "Asia",   "PK": "Asia",   "TH": "Asia",   "VN": "Asia",
}

# ISO-2 → ISO-3 (for WifOR value-factor H5 lookup)
COUNTRY_ISO2_TO_ISO3: dict[str, str] = {
    "AT": "AUT", "BE": "BEL", "CH": "CHE", "CZ": "CZE",
    "DE": "DEU", "DK": "DNK", "ES": "ESP", "FI": "FIN",
    "FR": "FRA", "GB": "GBR", "GR": "GRC", "HR": "HRV",
    "HU": "HUN", "IE": "IRL", "IT": "ITA", "NL": "NLD",
    "NO": "NOR", "PL": "POL", "PT": "PRT", "RO": "ROU",
    "SE": "SWE", "SK": "SVK", "UA": "UKR",
    "AR": "ARG", "BO": "BOL", "BR": "BRA", "CL": "CHL",
    "CO": "COL", "EC": "ECU", "MX": "MEX", "PE": "PER",
    "PY": "PRY", "UY": "URY", "VE": "VEN",
    "AO": "AGO", "DZ": "DZA", "EG": "EGY", "ET": "ETH",
    "GH": "GHA", "KE": "KEN", "MA": "MAR", "MZ": "MOZ",
    "NG": "NGA", "SN": "SEN", "TZ": "TZA", "UG": "UGA",
    "ZA": "ZAF", "ZM": "ZMB", "ZW": "ZWE",
    "BD": "BGD", "CN": "CHN", "ID": "IDN", "IN": "IND",
    "JP": "JPN", "KR": "KOR", "MM": "MMR", "MY": "MYS",
    "PH": "PHL", "PK": "PAK", "TH": "THA", "VN": "VNM",
}

_ALL_COUNTRY_LIST: list[str] = sorted(COUNTRY_REGION_MAP.keys())
ALL_SECTORS: list[str] = list(PROJECT_SECTOR_TO_NACE.keys())

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fmt_capex(v: float) -> str:
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"

def _musd(qty: float, conv: float, coeff: Optional[float]) -> float:
    """qty × unit_conversion × coeff / 1e6  →  M USD."""
    return qty * conv * (coeff or 0.0) / 1e6

def _find_irr(fn, lo: float = 0.001, hi: float = 0.99) -> Optional[float]:
    try:
        if fn(lo) * fn(hi) > 0:
            return None
        return brentq(fn, lo, hi, xtol=1e-8)
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# CACHED: IO TIER ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Running supply-chain IO analysis (tiers 0–10)…")
def _run_io(capex_usd: int, sector: str, region: str) -> Optional[dict]:
    if not IO_AVAILABLE:
        return None
    database = "exiobase"
    pid = f"{sector}_{region}"
    t0_res = tier0_impact(capex_usd, sector, region, database)
    t1_res = tier1_impact(capex_usd, sector, region, database)
    t2_raw = tier_impact(capex_usd, sector, region, database, tier_from=2, tier_to=2)
    t3_raw = tier_impact(capex_usd, sector, region, database, tier_from=3, tier_to=10)

    def _t0_df() -> pd.DataFrame:
        rows = [
            {"project_id": pid, "supplying_sector": sec,
             **{k: v for k, v in vals.items() if k != "spend_M$"}}
            for sec, vals in t0_res["impact_by_sector"].items()
        ]
        return pd.DataFrame(rows)

    def _t1_df() -> pd.DataFrame:
        rows = [
            {"project_id": pid, "supplying_sector": sec, "sourcing_region": reg,
             **{k: v for k, v in rv.items() if k not in ("share", "spend_M$")}}
            for sec, regions in t1_res["tier1_by_sector"].items()
            for reg, rv in regions.items()
        ]
        return pd.DataFrame(rows)

    t0 = _t0_df()
    t1 = _t1_df()
    t2 = t2_raw.copy(); t2["project_id"] = pid
    t3 = t3_raw.copy(); t3["project_id"] = pid
    return {"t0": t0, "t1": t1, "t2": t2, "t3": t3}


# ─────────────────────────────────────────────────────────────────────────────
# CACHED: SSP INTENSITY FACTORS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_all_ssp_factors(region: str, focus_year: int) -> dict:
    """Returns {ssp: factor_dict | None} for all five SSPs."""
    if not INTENSITY_CSV.exists():
        return {s: None for s in ALL_SSPS}
    df = pd.read_csv(INTENSITY_CSV)

    def _one(scenario: str) -> Optional[dict]:
        row = df[(df["region"] == region) & (df["scenario"] == scenario)
                 & (df["year"] == float(focus_year))]
        if row.empty:
            return None
        r = row.iloc[0]
        rs = float(r.get("renewable_share", 0.5))
        return {
            "GHG_tCO2e":      float(r["adj_ratio_ghg"]),
            "Employment_FTE": float(r["adj_ratio_employment"]),
            "Water_1000m3":   float(rs * 0.15 + (1 - rs) * 1.0),
            "ValueAdded_M$":  float(r["adj_ratio_employment"]),
        }

    return {s: _one(s) for s in ALL_SSPS}


# ─────────────────────────────────────────────────────────────────────────────
# CACHED: WIFOR VALUE FACTORS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_value_factors(iso3: str, nace: str, focus_year: int) -> dict:
    """Returns dict with c_ghg, c_ghg_paris, c_water, c_gva coefficients."""
    if not ASSESS_AVAILABLE:
        return {"c_ghg": -0.0669, "c_ghg_paris": -0.0723,
                "c_water": -0.2291, "c_gva": 99.82, "fallback": True}
    vf_dir = _resolve_wifor_dir()
    if vf_dir is None:
        return {"c_ghg": -0.0669, "c_ghg_paris": -0.0723,
                "c_water": -0.2291, "c_gva": 99.82, "fallback": True}

    def _vf(key: str) -> Optional[float]:
        spec = {**VF_FILE_SPECS[key], "year": str(focus_year)}
        return _load_vf_coeff(spec, vf_dir, iso3, nace)

    return {
        "c_ghg":       _vf("ghg"),
        "c_ghg_paris": _vf("ghg_paris"),
        "c_water":     _vf("water"),
        "c_gva":       _load_gva_per_hour(vf_dir, iso3, nace, focus_year),
        "fallback":    False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DEPENDENCY: ENCORE + WWF SCORES
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _compute_dep_context(encore_sector: str) -> dict:
    """ENCORE dependency scores + WWF risk scores for all regions."""
    if not (DEP_AVAILABLE and ASSESS_AVAILABLE):
        return {"encore_dep": {}, "wwf_by_region": {}}

    enc_profile = get_materiality_profile(encore_sector)
    encore_dep: dict = {}
    for stressor, svcs in STRESSOR_ECOSYSTEM_MAP.items():
        scores = [enc_profile.ratings.get(svc, {}).get("dependency_score", 0)
                  for svc in svcs]
        encore_dep[stressor] = sum(scores) / max(len(scores), 1)

    wwf_by_region: dict = {}
    for dep_reg in REGIONAL_BASELINES:
        res = score_project(f"_dyn_{dep_reg}", dep_reg, encore_sector)
        wwf_by_region[dep_reg] = {
            "wrf_physical":        res.wrf.physical,
            "wrf_regulatory":      res.wrf.regulatory,
            "wrf_reputational":    res.wrf.reputational,
            "wrf_composite":       res.wrf.composite,
            "brf_species_threat":  res.brf.species_threat,
            "brf_ecosystem":       res.brf.ecosystem_intactness,
            "brf_protected_areas": res.brf.protected_areas,
            "brf_composite":       res.brf.composite,
        }
    return {"encore_dep": encore_dep, "wwf_by_region": wwf_by_region}


# ─────────────────────────────────────────────────────────────────────────────
# CACHED: ATQ + EARTHOVERSHOOT DATA LOADERS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def _load_atq_data() -> pd.DataFrame:
    path = PA_DIR / "indicators" / "ebrd_atq_scores_2024_25.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).set_index("Country")


@st.cache_data
def _load_overshoot_data() -> pd.DataFrame:
    path = PA_DIR / "indicators" / "earthovershoot" / "overshoot_results.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Use 2023 baseline; fall back to latest available year per country
    df_23 = df[df["year"] == 2023]
    if df_23.empty:
        df_23 = df.sort_values("year").groupby("area").last().reset_index()
    return df_23.set_index("area")


def _compute_overshoot_single(country_iso2: str, capex_usd: float,
                               ghg_tco2e: float, land_ha: float) -> dict:
    """EarthOvershoot metrics for one project host country."""
    country_name = ATQ_ISO2_TO_NAME.get(country_iso2) or _ISO2_TO_OVERSHOOT_NAME.get(country_iso2)

    ef_carbon_gha = ghg_tco2e * (1 - 0.35) / 2.677 * 1.3
    ef_land_gha   = land_ha * 2.1  # simplified (treated as cropland EQF 2.1)

    ef_per_capita = bc_per_capita = bc_total = deficit = 0.0
    df_eo = _load_overshoot_data()
    if country_name and not df_eo.empty and country_name in df_eo.index:
        row = df_eo.loc[country_name]
        ef_per_capita = float(row.get("ef_per_capita_gha", 0.0))
        bc_per_capita = float(row.get("bc_per_capita_gha", 0.0))
        bc_total      = float(row.get("bc_total_gha", 1.0))
        deficit       = float(row.get("ecological_deficit_gha", 0.0))

    bc_total_safe  = max(bc_total, 1.0)
    oci_pct        = (ef_carbon_gha + ef_land_gha) / bc_total_safe * 100
    bc_deficit_mult = 1.0 if deficit >= 0 else min(1.5, 1.0 + abs(deficit) / bc_total_safe)

    return {
        "ef_carbon_gha":    ef_carbon_gha,
        "ef_land_gha":      ef_land_gha,
        "oci_pct":          oci_pct,
        "bc_deficit_mult":  bc_deficit_mult,
        "ef_per_capita_host": ef_per_capita,
        "bc_per_capita_host": bc_per_capita,
        "deficit_host_gha": deficit,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PURE COMPUTATION  (non-cached, fast given cached IO inputs)
# ─────────────────────────────────────────────────────────────────────────────

def _raw(df: pd.DataFrame, c: str) -> float:
    return float(df[c].sum()) if c in df.columns else 0.0

def _apply(val: float, col: str, factors: Optional[dict]) -> float:
    return val * factors[col] if (factors and col in factors) else val

def _dep_factor(stressor: str, sourcing_region: str, supplying_sector: str,
                encore_dep: dict, wwf_by_region: dict) -> float:
    enc = encore_dep.get(stressor, DEP_NEUTRAL)
    # wwf_by_region keys are lowercase (from REGIONAL_BASELINES); normalise before lookup
    _reg_key = (sourcing_region or "").lower()
    wwf_entry = wwf_by_region.get(_reg_key, wwf_by_region.get("europe", {}))
    wwf = wwf_entry.get(STRESSOR_WWF_COL.get(stressor, "wrf_physical"), DEP_NEUTRAL)
    sc = SC_SECTOR_DEP_PROFILE.get(supplying_sector, {}).get(
        STRESSOR_SC_DEP_KEY.get(stressor, "water"), DEP_NEUTRAL)
    base = (enc / DEP_NEUTRAL + wwf / DEP_NEUTRAL) / 2.0
    return (base + sc / DEP_NEUTRAL) / 2.0


def _build_tier_dep(io: dict, region: str, encore_dep: dict, wwf_by_region: dict) -> dict:
    """Weighted average dep_factor per tier per stressor."""
    t0, t1, t2, t3 = io["t0"], io["t1"], io["t2"], io["t3"]
    tier_defs = [("t0", t0, None), ("t1", t1, "sourcing_region"),
                 ("t2", t2, None), ("t3", t3, None)]
    tier_dep: dict = {}
    for tk, df, region_col in tier_defs:
        tier_dep[tk] = {}
        for st in COLS_SC:
            if st not in df.columns or df.empty or not (DEP_AVAILABLE and ASSESS_AVAILABLE):
                tier_dep[tk][st] = 1.0
                continue
            weights = np.abs(df[st].values) + 1e-9
            factors_list = [
                _dep_factor(st,
                            row.get(region_col, region) if region_col else region,
                            row["supplying_sector"],
                            encore_dep, wwf_by_region)
                for _, row in df.iterrows()
            ]
            tier_dep[tk][st] = float(np.average(factors_list, weights=weights))
    return tier_dep


def _build_summary(io: dict, factors: Optional[dict], tier_dep: dict) -> tuple[dict, dict]:
    """Build SUMMARY and GRAND dicts from IO DataFrames + scenario factors."""
    t0, t1, t2, t3 = io["t0"], io["t1"], io["t2"], io["t3"]
    tier_defs = [("t0", t0), ("t1", t1), ("t2", t2), ("t3", t3)]
    summary: dict = {}
    for tk, df in tier_defs:
        summary[tk] = {
            "raw": {c: _raw(df, c) for c in COLS_SC},
            "adj": {c: _apply(_raw(df, c), c, factors) for c in COLS_SC},
            "dep": {c: _apply(_raw(df, c), c, factors) * tier_dep[tk][c] for c in COLS_SC},
        }
    grand = {
        layer: {c: sum(summary[tk][layer][c] for tk, _ in tier_defs)
                for c in COLS_SC}
        for layer in ["raw", "adj", "dep"]
    }
    return summary, grand


def _monetise(grand: dict, project: dict, vf: dict) -> dict:
    """Part A: construction-phase and annual operational monetary values."""
    c_ghg   = vf["c_ghg"]
    c_water = vf["c_water"]
    c_gva   = vf["c_gva"]

    ghg_adj  = grand["adj"]["GHG_tCO2e"]
    wat_adj  = grand["adj"]["Water_1000m3"]
    emp_adj  = grand["adj"]["Employment_FTE"]

    ghg_cost_m       = _musd(ghg_adj,  1_000,              c_ghg)
    ghg_paris_cost_m = _musd(ghg_adj,  1_000,              vf.get("c_ghg_paris", c_ghg))
    water_cost_m     = _musd(wat_adj,  1_000,              c_water)
    emp_ben_m        = _musd(emp_adj,  FTE_HOURS_PER_YEAR, c_gva)
    s_constr_net     = ghg_cost_m + water_cost_m - emp_ben_m  # positive = net cost

    opex_r = project["opex_ratio"]
    annual_op_fte        = emp_adj * opex_r
    annual_emp_m         = _musd(annual_op_fte, FTE_HOURS_PER_YEAR, c_gva)
    annual_ghg_save_m    = _musd(project["avoided_co2"], 1_000, c_ghg)
    annual_op_water_m    = _musd(wat_adj * opex_r, 1_000, c_water)
    s_annual             = annual_emp_m + annual_ghg_save_m - annual_op_water_m

    capex_m = project["capex_usd"] / 1e6
    annual_rev_m   = project["revenue_yield"] * capex_m
    annual_opex_m  = opex_r * capex_m
    annual_fin_cf  = annual_rev_m - annual_opex_m

    return dict(
        ghg_cost_m=ghg_cost_m, ghg_paris_cost_m=ghg_paris_cost_m,
        water_cost_m=water_cost_m, emp_ben_m=emp_ben_m,
        s_constr_net=s_constr_net,
        annual_emp_m=annual_emp_m, annual_ghg_save_m=annual_ghg_save_m,
        annual_op_water_m=annual_op_water_m, s_annual=s_annual,
        annual_fin_cf=annual_fin_cf, annual_rev_m=annual_rev_m,
        annual_opex_m=annual_opex_m,
        ghg_adj=ghg_adj, wat_adj=wat_adj, emp_adj=emp_adj,
    )


def _build_cashflow_df(project: dict, mon: dict) -> pd.DataFrame:
    """Part B: year-by-year cash flow table."""
    T = project["project_years"]
    years, fin_cf, mon_ghg, mon_soc, total = [], [], [], [], []
    for yr in range(T + 1):
        if yr == 0:
            fc =  -(project["capex_usd"] / 1e6)
            mg =  -(mon["ghg_cost_m"] + mon["water_cost_m"])
            ms =  + mon["emp_ben_m"]
        else:
            fc =  mon["annual_fin_cf"]
            mg =  mon["annual_ghg_save_m"] - mon["annual_op_water_m"]
            ms =  mon["annual_emp_m"]
        years.append(yr); fin_cf.append(fc); mon_ghg.append(mg)
        mon_soc.append(ms); total.append(fc + mg + ms)

    return pd.DataFrame({
        "Year":                     years,
        "Financial CF (M$)":        fin_cf,
        "Monetised GHG/Water (M$)": mon_ghg,
        "Monetised Social (M$)":    mon_soc,
        "Total Integrated CF (M$)": total,
    })


def _compute_npv_fn(rate: float, fin_only: bool,
                    annual_fin_cf: float, s_annual: float,
                    capex_m: float, s_constr_net: float,
                    project_years: int) -> float:
    pv = sum(
        (annual_fin_cf if fin_only else annual_fin_cf + s_annual) / (1 + rate) ** yr
        for yr in range(1, project_years + 1)
    )
    return pv - capex_m - (0.0 if fin_only else s_constr_net)


def _compute_metrics(project: dict, mon: dict,
                     tier_dep: dict, wwf_by_region: dict) -> dict:
    """Parts C–E: NPV, iNPV, IRR, S-IRR, WACC adjustment."""
    capex_m  = project["capex_usd"] / 1e6
    wacc     = project["wacc_base"]
    T        = project["project_years"]
    B        = project["bond_years"]
    afc      = mon["annual_fin_cf"]
    sa       = mon["s_annual"]
    scn      = mon["s_constr_net"]

    fn_npv  = lambda r: _compute_npv_fn(r, True,  afc, sa, capex_m, scn, T)
    fn_inpv = lambda r: _compute_npv_fn(r, False, afc, sa, capex_m, scn, T)

    npv_base  = fn_npv(wacc)
    inpv_base = fn_inpv(wacc)
    delta_npv = inpv_base - npv_base

    rates     = np.linspace(0.01, 0.25, 240)
    npv_curve  = [fn_npv(r)  for r in rates]
    inpv_curve = [fn_inpv(r) for r in rates]

    cum_npv  = [0.0]; cum_inpv = [0.0]
    for yr in range(1, T + 1):
        cum_npv.append( cum_npv[-1]  + afc          / (1 + wacc) ** yr)
        cum_inpv.append(cum_inpv[-1] + (afc + sa)   / (1 + wacc) ** yr)
    cum_npv  = [v - capex_m       for v in cum_npv]
    cum_inpv = [v - capex_m - scn for v in cum_inpv]

    fin_irr = _find_irr(fn_npv)
    s_irr   = _find_irr(fn_inpv)
    pv_nat_div = sum(sa / (1 + wacc) ** yr for yr in range(1, T + 1))

    # WWF + dep → WACC adjustment
    dep_region = project["region"].lower()
    wwf_scores = wwf_by_region.get(dep_region, wwf_by_region.get("europe", {}))
    wwf_water  = wwf_scores.get("wrf_physical", 3.0)
    wwf_bio    = wwf_scores.get("brf_composite", 3.0)
    wwf_water_norm = (wwf_water - 1.0) / 4.0

    dep_vals = [tier_dep[tk][st]
                for tk in ["t0", "t1", "t2", "t3"]
                for st in ["GHG_tCO2e", "Water_1000m3"]]
    mean_dep = float(np.mean(dep_vals)) if dep_vals else 1.0
    dep_resilience = max(0.0, min(1.0, (1.5 - mean_dep) / 0.5))

    ESG_MAX = 0.0010
    water_discount = ESG_MAX * 0.5 * (1.0 - wwf_water_norm)
    dep_discount   = ESG_MAX * 0.5 * dep_resilience
    sust_discount  = water_discount + dep_discount
    wacc_adj       = wacc - sust_discount

    npv_adj  = fn_npv(wacc_adj)
    inpv_adj = fn_inpv(wacc_adj)

    # Bond period is capped at project lifetime to keep the model consistent
    B_eff = min(B, T)
    cum_npv_base, cum_npv_adj, cum_inpv_adj = [], [], []
    _nb = _na = _ia = 0.0
    for yr in range(1, B_eff + 1):
        _nb  += afc       / (1 + wacc)     ** yr
        _na  += afc       / (1 + wacc_adj) ** yr
        _ia  += (afc + sa)/ (1 + wacc_adj) ** yr
        cum_npv_base.append( _nb  - capex_m)
        cum_npv_adj.append(  _na  - capex_m)
        cum_inpv_adj.append( _ia  - capex_m - scn)

    rates2 = np.linspace(0.02, 0.15, 200)
    inpv_wacc_base = [fn_inpv(r) for r in rates2]
    inpv_wacc_adj  = [fn_inpv(r - sust_discount) for r in rates2]

    return dict(
        npv_base=npv_base, inpv_base=inpv_base, delta_npv=delta_npv,
        rates=rates, npv_curve=npv_curve, inpv_curve=inpv_curve,
        cum_npv=cum_npv, cum_inpv=cum_inpv,
        fin_irr=fin_irr, s_irr=s_irr, pv_nat_div=pv_nat_div,
        wwf_water=wwf_water, wwf_bio=wwf_bio, mean_dep=mean_dep,
        dep_resilience=dep_resilience, water_discount=water_discount,
        dep_discount=dep_discount, sust_discount=sust_discount,
        wacc_adj=wacc_adj, npv_adj=npv_adj, inpv_adj=inpv_adj,
        bond_eff=B_eff,  # effective bond years (capped at project lifetime)
        cum_npv_base=cum_npv_base, cum_npv_adj=cum_npv_adj,
        cum_inpv_adj=cum_inpv_adj, rates2=rates2,
        inpv_wacc_base=inpv_wacc_base, inpv_wacc_adj=inpv_wacc_adj,
        wwf_scores=wwf_scores,
    )


def _compute_one_ssp(ssp: str, factors: Optional[dict], raw_sums: dict,
                     project: dict, vf: dict) -> Optional[dict]:
    """Part G: full integrated finance metrics for one SSP."""
    if factors is None:
        return None
    c_ghg   = vf["c_ghg"]
    c_water = vf["c_water"]
    c_gva   = vf["c_gva"]

    ghg_adj = raw_sums["GHG_tCO2e"]      * factors["GHG_tCO2e"]
    emp_adj = raw_sums["Employment_FTE"]  * factors["Employment_FTE"]
    wat_adj = raw_sums["Water_1000m3"]    * factors["Water_1000m3"]

    ghg_m  = _musd(ghg_adj, 1_000,              c_ghg)
    wat_m  = _musd(wat_adj, 1_000,              c_water)
    emp_m  = _musd(emp_adj, FTE_HOURS_PER_YEAR, c_gva)
    s_cnet = ghg_m + wat_m - emp_m

    op_emp_m = _musd(emp_adj * project["opex_ratio"], FTE_HOURS_PER_YEAR, c_gva)
    op_ghg_m = _musd(project["avoided_co2"], 1_000, c_ghg)
    op_wat_m = _musd(wat_adj * project["opex_ratio"], 1_000, c_water)
    s_ann    = op_emp_m + op_ghg_m - op_wat_m

    capex_m = project["capex_usd"] / 1e6
    afc = (project["revenue_yield"] - project["opex_ratio"]) * capex_m

    fn = lambda r, fo=True, _sa=s_ann, _sc=s_cnet: _compute_npv_fn(
        r, fo, afc, _sa, capex_m, _sc, project["project_years"])

    return dict(
        ssp=ssp,
        factor_ghg=factors["GHG_tCO2e"],
        factor_emp=factors["Employment_FTE"],
        factor_wat=factors["Water_1000m3"],
        ghg_cost_m=ghg_m, water_cost_m=wat_m, emp_ben_m=emp_m,
        nature_debt=s_cnet, annual_dividend=s_ann,
        npv=fn(project["wacc_base"], True),
        inpv=fn(project["wacc_base"], False),
        fin_irr=_find_irr(lambda r: fn(r, True)),
        s_irr=_find_irr(lambda r: fn(r, False)),
    )


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-PROJECT RUNNER  (cross-country / cross-sector comparison core)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Running multi-project analysis…")
def _run_multi_project(
    project_specs: tuple,   # hashable: ((pid, country, sector, capex_usd, avoided_co2), ...)
    focus_year: int,
    ssps: tuple,
) -> pd.DataFrame:
    rows: list[dict] = []
    for spec in project_specs:
        pid, country, sector, capex_usd, avoided_co2 = spec
        region   = COUNTRY_REGION_MAP.get(country, "Europe")
        iso3     = COUNTRY_ISO2_TO_ISO3.get(country, REGION_TO_ISO3.get(region, "DEU"))
        nace     = PROJECT_SECTOR_TO_NACE.get(sector, "Q")
        enc_sec  = PROJECT_SECTOR_TO_ENCORE.get(sector, sector.lower())

        vf          = _load_value_factors(iso3, nace, focus_year)
        dep_ctx     = _compute_dep_context(enc_sec)
        all_ssp_f   = _load_all_ssp_factors(region, focus_year)

        # Raw IO sums — try cached IO first, else fallback estimate
        capex_m  = capex_usd / 1e6
        raw_sums = {k: v * capex_m for k, v in _INTENSITY_FALLBACK.items()}
        if IO_AVAILABLE:
            io_res = _run_io(capex_usd, sector, region)
            if io_res is not None:
                raw_sums = {
                    c: sum(float(io_res[tk][c].sum()) if c in io_res[tk].columns else 0.0
                           for tk in ["t0", "t1", "t2", "t3"])
                    for c in COLS_SC
                }

        dep_region = region.lower()
        wwf_scores = dep_ctx["wwf_by_region"].get(dep_region,
                         dep_ctx["wwf_by_region"].get("europe", {}))
        wwf_water  = wwf_scores.get("wrf_physical", 3.0)
        dep_factor = 1.0  # simplified (full tier_dep not available without raw tier dfs)
        eo         = _compute_overshoot_single(country, capex_usd,
                                               raw_sums.get("GHG_tCO2e", 0.0), 0.0)
        bc_mult    = eo.get("bc_deficit_mult", 1.0)
        dep_f_adj  = dep_factor * bc_mult

        # ATQ lookup — resolved once per spec (outside ssp loop)
        _atq_src = _load_atq_data()
        _atq_cn  = ATQ_ISO2_TO_NAME.get(country, "")
        _atq_row = (_atq_src.loc[_atq_cn]
                    if (_atq_cn and not _atq_src.empty and _atq_cn in _atq_src.index)
                    else None)

        proj_spec: dict = {
            "capex_usd": capex_usd, "avoided_co2": avoided_co2,
            "revenue_yield": 0.10, "opex_ratio": 0.05,
            "project_years": 25, "wacc_base": 0.070,
            "country": country, "region": region, "sector": sector,
        }
        if pid in PROJECT_BY_ID:
            proj_spec.update(PROJECT_BY_ID[pid])

        proj_name = PROJECT_BY_ID.get(pid, {}).get("label", pid)

        for ssp in ssps:
            ssp_f = all_ssp_f.get(ssp)
            r = _compute_one_ssp(ssp, ssp_f, raw_sums, proj_spec, vf)
            if r is None:
                continue
            rows.append({
                "pid":              pid,
                "project_name":     proj_name,
                "country":          country,
                "sector":           sector,
                "region":           region,
                "capex_usd":        capex_usd,
                "ssp":              ssp,
                "inpv_usd":         r["inpv"] * 1e6,
                "s_irr":            r.get("s_irr"),
                "dep_factor":       dep_factor,
                "dep_factor_adj":   dep_f_adj,
                "wwf_score":        wwf_water,
                "wacc_adj":         proj_spec["wacc_base"],
                "tier0_ghg":        raw_sums.get("GHG_tCO2e", 0.0),
                "tier1_ghg":        0.0,
                "tier0_emp":        raw_sums.get("Employment_FTE", 0.0),
                "tier1_emp":        0.0,
                "c_ghg":            vf.get("c_ghg") or 0.0,
                "c_gva":            vf.get("c_gva") or 0.0,
                "c_water":          vf.get("c_water") or 0.0,
                "adj_ratio_ghg":    ssp_f.get("GHG_tCO2e", 1.0) if ssp_f else 1.0,
                "adj_ratio_emp":    ssp_f.get("Employment_FTE", 1.0) if ssp_f else 1.0,
                "nature_debt_usd":  r.get("nature_debt", 0.0) * 1e6,
                "nature_dividend_usd": r.get("annual_dividend", 0.0) * 1e6,
                "ef_carbon_gha":    eo.get("ef_carbon_gha", 0.0),
                "ef_land_gha":      eo.get("ef_land_gha", 0.0),
                "oci_pct":          eo.get("oci_pct", 0.0),
                "bc_deficit_mult":  bc_mult,
                "ef_per_capita_host":  eo.get("ef_per_capita_host", 0.0),
                "bc_per_capita_host":  eo.get("bc_per_capita_host", 0.0),
                "deficit_host_gha":    eo.get("deficit_host_gha", 0.0),
                # ATQ 2024-25 (one value per country, repeated across SSPs)
                "atq_competitive":  float(_atq_row["Competitive"])   if _atq_row is not None else None,
                "atq_well_governed":float(_atq_row["Well_Governed"]) if _atq_row is not None else None,
                "atq_green":        float(_atq_row["Green"])         if _atq_row is not None else None,
                "atq_inclusive":    float(_atq_row["Inclusive"])     if _atq_row is not None else None,
                "atq_resilient":    float(_atq_row["Resilient"])     if _atq_row is not None else None,
                "atq_integrated":   float(_atq_row["Integrated"])    if _atq_row is not None else None,
                "atq_avg":          float(_atq_row["ATQ_Average"])   if _atq_row is not None else None,
            })
    return pd.DataFrame(rows)


def _compute_eti_score(country_gap: float, intensity_scores: list[float],
                       uplifts: list[str]) -> float:
    base = country_gap * sum(intensity_scores)
    return round(base * (1 + sum(UPLIFT_ETI_DELTA.get(u, 0) for u in uplifts)), 3)


def _compute_aimm_score(project_outcome: float, market_outcome: float,
                        risk_factor: float) -> float:
    return round((project_outcome + market_outcome) * risk_factor, 2)


# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _fig_npv(project: dict, metrics: dict, sc_label: str) -> go.Figure:
    p   = project
    m   = metrics
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=["NPV vs iNPV across discount rates",
                        f"Cumulative NPV/iNPV over {p['project_years']}-yr life"],
        column_widths=[0.5, 0.5])
    fig.add_trace(go.Scatter(x=m["rates"]*100, y=m["npv_curve"],
        name="Standard NPV", line=dict(color=C_FIN, width=2.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=m["rates"]*100, y=m["inpv_curve"],
        name="Integrated iNPV", line=dict(color=C_TOT, width=2.5, dash="dash")), row=1, col=1)
    fig.add_vline(x=p["wacc_base"]*100, line_color="#555", line_dash="dot",
                  annotation_text=f"WACC {p['wacc_base']*100:.1f}%",
                  annotation_position="top right", row=1, col=1)
    fig.add_hline(y=0, line_color="#aaa", line_width=1, row=1, col=1)

    yrs = list(range(p["project_years"] + 1))
    fig.add_trace(go.Scatter(x=yrs, y=m["cum_npv"],  name="Cum NPV",
        line=dict(color=C_FIN, width=2.5)), row=1, col=2)
    fig.add_trace(go.Scatter(x=yrs, y=m["cum_inpv"], name="Cum iNPV",
        line=dict(color=C_TOT, width=2.5, dash="dash")), row=1, col=2)
    fig.add_vline(x=p["bond_years"], line_color="#f28e2b", line_dash="dot",
                  annotation_text=f"Bond end (Yr {p['bond_years']})",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=0, line_color="#aaa", line_width=1, row=1, col=2)

    fig.update_layout(
        title=dict(text=(f"<b>Integrated NPV — {fmt_capex(p['capex_usd'])} · "
                         f"{p['country']} ({p['region']}) · {p['sector']} · {sc_label}</b>"),
                   x=0.01, xanchor="left", font=dict(size=13)),
        height=440, margin=dict(l=20, r=20, t=100, b=20),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", size=10),
        yaxis_title="M USD", yaxis2_title="M USD",
        xaxis_title="Discount rate (%)", xaxis2_title="Year",
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )
    return fig


def _fig_sirr(project: dict, metrics: dict, mon: dict) -> go.Figure:
    p, m = project, metrics
    wacc = p["wacc_base"]
    pv_nd = m["pv_nat_div"]
    wf_labels = ["Financial NPV", "− Nature Debt\n(GHG+Water)",
                 "+ Constr.\nEmployment",
                 f"+ Annual\nNature Div. PV\n(×{p['project_years']}yr)",
                 "Integrated iNPV"]
    wf_values = [m["npv_base"],
                 -(mon["ghg_cost_m"] + mon["water_cost_m"]),
                 +mon["emp_ben_m"],
                 +pv_nd,
                 m["inpv_base"]]
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=["NPV → iNPV Waterfall (M USD)",
                        "IRR comparison: Financial vs Societal"],
        column_widths=[0.58, 0.42])
    fig.add_trace(go.Waterfall(
        orientation="v", measure=["absolute","relative","relative","relative","total"],
        x=wf_labels, y=wf_values, opacity=0.88,
        connector=dict(line=dict(color="#aaa", width=1.5)),
        increasing=dict(marker=dict(color=C_POS)),
        decreasing=dict(marker=dict(color=C_NEG)),
        totals=dict(marker=dict(color=C_POS if m["inpv_base"] >= 0 else C_NEG)),
        text=[f"{v:+.2f} M" for v in wf_values], textposition="outside",
    ), row=1, col=1)
    fig.add_hline(y=0, line_color="#555", line_width=1.2, row=1, col=1)

    irr_labels, irr_vals, irr_cols = [], [], []
    if m["fin_irr"]: irr_labels.append("Financial IRR"); irr_vals.append(m["fin_irr"]*100); irr_cols.append(C_FIN)
    irr_labels.append(f"WACC ({wacc*100:.1f}%)"); irr_vals.append(wacc*100); irr_cols.append("#aaa")
    if m["s_irr"]: irr_labels.append("Societal S-IRR"); irr_vals.append(m["s_irr"]*100); irr_cols.append(C_TOT)
    fig.add_trace(go.Bar(x=irr_labels, y=irr_vals, marker_color=irr_cols, marker_opacity=0.85,
        text=[f"{v:.2f}%" for v in irr_vals], textposition="outside", showlegend=False), row=1, col=2)
    fig.update_layout(
        title=dict(text=(f"<b>S-IRR Analysis — {fmt_capex(p['capex_usd'])} · "
                         f"{p['country']} ({p['region']}) · {p['sector']}</b>"),
                   x=0.01, xanchor="left", font=dict(size=13)),
        height=460, margin=dict(l=20, r=20, t=100, b=20),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", size=10),
        yaxis_title="M USD", yaxis2_title="Rate (%)", showlegend=False,
    )
    return fig


def _fig_wacc(project: dict, metrics: dict) -> go.Figure:
    p, m = project, metrics
    b_eff  = m["bond_eff"]          # capped at project_years if bond > project
    bond_x = list(range(1, b_eff + 1))
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=[f"Cumulative NPV over bond lifetime ({b_eff} yrs)",
                        "iNPV sensitivity: base vs ESG-adjusted WACC"])
    fig.add_trace(go.Scatter(x=bond_x, y=m["cum_npv_base"],
        name=f"NPV @ {p['wacc_base']*100:.2f}%",
        line=dict(color=C_FIN, width=2.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=bond_x, y=m["cum_npv_adj"],
        name=f"NPV @ {m['wacc_adj']*100:.3f}% (adj)",
        line=dict(color="#59a14f", width=2.5, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=bond_x, y=m["cum_inpv_adj"],
        name=f"iNPV @ {m['wacc_adj']*100:.3f}%",
        line=dict(color=C_TOT, width=2.5, dash="dot")), row=1, col=1)
    fig.add_hline(y=0, line_color="#aaa", line_width=1, row=1, col=1)

    fig.add_trace(go.Scatter(x=m["rates2"]*100, y=m["inpv_wacc_base"],
        name="iNPV (base WACC)", line=dict(color=C_FIN, width=2.5)), row=1, col=2)
    fig.add_trace(go.Scatter(x=m["rates2"]*100, y=m["inpv_wacc_adj"],
        name=f"iNPV (ESG−{m['sust_discount']*10000:.1f}bp)",
        line=dict(color=C_TOT, width=2.5, dash="dash")), row=1, col=2)
    fig.add_vline(x=p["wacc_base"]*100, line_color="#555", line_dash="dot",
                  annotation_text=f"WACC_base {p['wacc_base']*100:.1f}%",
                  annotation_position="top right", row=1, col=2)
    fig.add_vline(x=m["wacc_adj"]*100, line_color="#59a14f", line_dash="dot",
                  annotation_text=f"WACC_adj {m['wacc_adj']*100:.2f}%",
                  annotation_position="top left", row=1, col=2)
    fig.add_hline(y=0, line_color="#aaa", line_width=1, row=1, col=2)
    fig.update_layout(
        title=dict(text=(f"<b>WACC Adjustment — {fmt_capex(p['capex_usd'])} · "
                         f"{p['country']} ({p['region']}) · {p['sector']}</b>"),
                   x=0.01, xanchor="left", font=dict(size=13)),
        height=460, margin=dict(l=20, r=20, t=100, b=20),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", size=10),
        yaxis_title="M USD", yaxis2_title="M USD",
        xaxis2_title="WACC (%)",
        legend=dict(orientation="h", y=-0.20, x=0.5, xanchor="center"),
    )
    return fig


def _fig_cashflow(project: dict, cf_df: pd.DataFrame,
                  metrics: dict, sc_label: str) -> go.Figure:
    p, m = project, metrics
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Financial CF",
        x=cf_df["Year"], y=cf_df["Financial CF (M$)"],
        marker_color=C_FIN, marker_opacity=0.85))
    fig.add_trace(go.Bar(name="Monetised GHG/Water",
        x=cf_df["Year"], y=cf_df["Monetised GHG/Water (M$)"],
        marker_color=C_GHG, marker_opacity=0.85))
    fig.add_trace(go.Bar(name="Monetised Social",
        x=cf_df["Year"], y=cf_df["Monetised Social (M$)"],
        marker_color=C_EMP, marker_opacity=0.85))
    fig.add_trace(go.Scatter(name="Total Integrated CF",
        x=cf_df["Year"], y=cf_df["Total Integrated CF (M$)"],
        mode="lines+markers", line=dict(color=C_TOT, width=2.5),
        marker=dict(size=5)))
    fig.add_vline(x=p["bond_years"] + 0.5, line_color="#f28e2b", line_dash="dot",
                  annotation_text=f"Bond end (Yr {p['bond_years']})",
                  annotation_position="top right")
    fig.add_hline(y=0, line_color="#555", line_width=1.2)
    fig.update_layout(
        barmode="relative",
        title=dict(text=(f"<b>Combined Cash Flows — {fmt_capex(p['capex_usd'])} · "
                         f"{p['country']} ({p['region']}) · {p['sector']} · {sc_label}</b>"
                         f"<br><span style='font-size:10px;color:#555'>"
                         f"Bond: {p['bond_years']} yrs · Project: {p['project_years']} yrs · "
                         f"WACC_base: {p['wacc_base']*100:.2f}% · "
                         f"WACC_adj: {m['wacc_adj']*100:.3f}%</span>"),
                   x=0.01, xanchor="left", font=dict(size=13)),
        xaxis_title="Year", yaxis_title="M USD",
        height=480, margin=dict(l=20, r=20, t=110, b=20),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", size=10),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )
    return fig


def _fig_ssp_comparison(project: dict, ssp_results: dict) -> go.Figure:
    p = project
    ssps   = list(ssp_results.keys())
    colors = [SSP_COLORS.get(s, "#888") for s in ssps]

    fig = make_subplots(rows=2, cols=2,
        subplot_titles=[
            "SSP Intensity Adjustment Factors (1.0 = baseline)",
            "Nature Debt decomposition (M USD, Year 0)",
            "Financial NPV vs Integrated iNPV (M USD)",
            "IRR comparison across SSPs (%)",
        ],
        vertical_spacing=0.16, horizontal_spacing=0.10)

    # Panel 1: adjustment factors
    for label, key, col in [("GHG intensity","factor_ghg",C_NEG),
                              ("Employment","factor_emp",C_POS),
                              ("Water intensity","factor_wat",C_WAT)]:
        fig.add_trace(go.Bar(name=label, x=ssps,
            y=[ssp_results[s][key] for s in ssps],
            marker_color=col, marker_opacity=0.82,
            text=[f"{ssp_results[s][key]:.3f}" for s in ssps],
            textposition="outside"), row=1, col=1)
    fig.add_hline(y=1.0, line_color="#555", line_dash="dot",
                  annotation_text="Baseline = 1.0",
                  annotation_position="right", row=1, col=1)

    # Panel 2: nature debt decomposition
    for label, key, sign in [("GHG cost","ghg_cost_m",1),
                               ("Water cost","water_cost_m",1),
                               ("Employment ben.","emp_ben_m",-1)]:
        vals = [ssp_results[s][key] for s in ssps]
        y = [v * sign for v in vals]
        fig.add_trace(go.Bar(name=label, x=ssps, y=y,
            marker_color=C_NEG if key!="emp_ben_m" else C_POS,
            marker_opacity=0.82,
            text=[f"{v:.2f}" for v in vals],
            textposition="outside"), row=1, col=2)
    fig.add_trace(go.Scatter(name="Net Nature Debt", x=ssps,
        y=[ssp_results[s]["nature_debt"] for s in ssps],
        mode="lines+markers", line=dict(color="#333", width=2, dash="dot"),
        marker=dict(size=7, symbol="diamond")), row=1, col=2)
    fig.add_hline(y=0, line_color="#aaa", line_width=1, row=1, col=2)

    # Panel 3: NPV vs iNPV
    npv_vals  = [ssp_results[s]["npv"]  for s in ssps]
    inpv_vals = [ssp_results[s]["inpv"] for s in ssps]
    fig.add_trace(go.Bar(name="Standard NPV (constant)", x=ssps, y=npv_vals,
        marker_color=C_FIN, marker_opacity=0.5,
        text=[f"{v:+.1f}" for v in npv_vals], textposition="inside"), row=2, col=1)
    fig.add_trace(go.Bar(name="Integrated iNPV", x=ssps, y=inpv_vals,
        marker_color=colors, marker_opacity=0.88,
        text=[f"{v:+.1f}" for v in inpv_vals], textposition="outside"), row=2, col=1)
    fig.add_hline(y=0, line_color="#555", line_width=1.2, row=2, col=1)
    _spread = max(inpv_vals) - min(inpv_vals)
    # Use row/col only — Plotly resolves axis refs automatically from subplot position
    fig.add_annotation(
        x=ssps[-1], y=max(inpv_vals),
        text=f"Scenario risk:<br><b>{_spread:.1f} M USD</b>",
        showarrow=False, font=dict(size=9, color="#333"),
        bgcolor="#fff8e7", bordercolor="#f28e2b", borderwidth=1,
        xanchor="right", row=2, col=1)

    # Panel 4: S-IRR vs Financial IRR
    fin_irrs = [ssp_results[s]["fin_irr"] for s in ssps]
    s_irrs   = [ssp_results[s]["s_irr"]   for s in ssps]
    fig.add_trace(go.Bar(name="Financial IRR", x=ssps,
        y=[v*100 if v else 0 for v in fin_irrs],
        marker_color=C_FIN, marker_opacity=0.6,
        text=[f"{v*100:.2f}%" if v else "N/A" for v in fin_irrs],
        textposition="outside"), row=2, col=2)
    fig.add_trace(go.Bar(name="Societal S-IRR", x=ssps,
        y=[v*100 if v else 0 for v in s_irrs],
        marker_color=colors, marker_opacity=0.88,
        text=[f"{v*100:.2f}%" if v else "N/A" for v in s_irrs],
        textposition="outside"), row=2, col=2)
    fig.add_hline(y=p["wacc_base"]*100, line_color="#555", line_dash="dot",
                  annotation_text=f"WACC {p['wacc_base']*100:.1f}%",
                  annotation_position="right", row=2, col=2)
    fig.update_layout(
        barmode="group",
        title=dict(text=(f"<b>All-SSP Scenario Comparison — {fmt_capex(p['capex_usd'])} · "
                         f"{p['country']} ({p['region']}) · {p['sector']}</b>"
                         f"<br><span style='font-size:10px;color:#555'>"
                         f"Bond: {p['bond_years']} yr · Project: {p['project_years']} yr · "
                         f"WACC_base: {p['wacc_base']*100:.2f}% · "
                         f"Financial NPV is scenario-neutral (contractual CF)</span>"),
                   x=0.01, xanchor="left", font=dict(size=12)),
        height=680, margin=dict(l=20, r=20, t=120, b=20),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", size=10),
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
    )
    return fig


def _fig_pathway_schematic(project: dict, ssp_results: dict,
                           dark_mode: bool = False) -> plt.Figure:
    """IPCC pathway flow diagram (Matplotlib)."""
    p = project
    ssp_list = list(ssp_results.keys()) if ssp_results else ALL_SSPS
    ssp_cols  = [SSP_COLORS.get(s, "#888") for s in ssp_list]
    _bg  = "#1a1a2e" if dark_mode else "#f8f9fb"
    _txt_col = "white" if dark_mode else "#1a1a2e"

    fig, ax = plt.subplots(figsize=(14, 8), facecolor=_bg)
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis("off")
    ax.set_facecolor(_bg)

    def _box(x, y, w, h, fc="#e8f0ff", ec="#5577aa", lw=1.6, r=0.22):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
            boxstyle=f"round,pad={r}", facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3))

    def _txt(x, y, s, fs=8.5, fw="normal", col="#1a1a2e", ha="center", va="center"):
        ax.text(x, y, s, fontsize=fs, fontweight=fw, color=col, ha=ha, va=va, zorder=4)

    def _arrow(x1, y1, x2, y2, col="#555", lw=1.8):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color=col, lw=lw, shrinkA=4, shrinkB=4), zorder=5)

    # Title
    ax.text(7, 7.65, "IPCC SSP Scenario → Integrated Project Value: Transmission Pathway",
            fontsize=11, fontweight="bold", ha="center", color=_txt_col, zorder=4)

    # SSP spectrum bar
    _box(0.4, 6.75, 13.2, 0.65, fc="#eef2ff", ec="#7788cc", lw=1.4)
    _txt(7, 7.2, "IPCC SSP Scenario", fs=10, fw="bold", col="#22266a")
    _ssp_full_cols = ["#1a9641","#a6d96a","#fdae61","#f46d43","#d73027"]
    _ssp_labels_full = ["SSP1-1.9\n1.5°C","SSP2-4.5\n2°C","SSP3-7.0\n3°C",
                         "SSP4-6.0\n2.5°C","SSP5-8.5\n>4°C"]
    for i, (sc, sl) in enumerate(zip(_ssp_full_cols, _ssp_labels_full)):
        bx = 0.8 + i * 2.5
        _box(bx, 6.78, 2.15, 0.52, fc=sc, ec="none", r=0.12)
        _txt(bx + 1.07, 7.04, sl, fs=7, fw="bold", col="white")

    # Three channels
    channel_xs = [1.2, 5.6, 10.0]
    ch_fc  = ["#ffe8e8", "#e8ffe8", "#e8f0ff"]
    ch_ec  = ["#cc4444", "#44aa44", "#4477cc"]
    ch_ttl = ["Channel 1\nGHG Intensity\nadj_ratio_ghg",
               "Channel 2\nEmployment\nadj_ratio_employment",
               "Channel 3\nWater Intensity\nf(renewable_share)"]
    fk_lst = ["factor_ghg", "factor_emp", "factor_wat"]

    for ci, (cx, fc, ec, ct, fk) in enumerate(zip(channel_xs, ch_fc, ch_ec, ch_ttl, fk_lst)):
        _box(cx, 5.0, 2.8, 1.45, fc=fc, ec=ec, lw=1.8)
        _txt(cx + 1.4, 6.1, ct, fs=7.5, fw="bold", col=ec)
        if ssp_results:
            vals = [ssp_results[s][fk] for s in ssp_list]
            bw = 2.4 / max(len(vals), 1)
            mxv = max(abs(v) for v in vals) + 0.01
            for bi, (s, v) in enumerate(zip(ssp_list, vals)):
                bh = 0.85 * abs(v - 1.0) / mxv + 0.04
                bx2 = cx + 0.2 + bi * bw
                by2 = 5.05 + (0.65 - bh) / 2
                ax.add_patch(plt.Rectangle((bx2, by2), bw*0.7, bh,
                    facecolor=SSP_COLORS.get(s,"#888"), edgecolor="none", alpha=0.85, zorder=5))
                ax.text(bx2+bw*0.35, by2+bh+0.04, f"{v:.2f}",
                    fontsize=5, ha="center", va="bottom", color="#333", zorder=6)
        _arrow(0.8+ci*2.5+1.07, 6.78, cx+1.4, 6.46, col=ec, lw=1.5)

    # Monetary impact boxes
    money_xs  = [0.7, 5.2, 9.7]
    money_fc  = ["#ffeaea", "#eafff0", "#eaf2ff"]
    money_ec  = ["#cc3333", "#33aa33", "#3366cc"]
    money_lbl = ["GHG Cost (M USD)\n[negative externality]",
                 "Employment Benefit (M USD)\n[positive externality]",
                 "Water Cost (M USD)\n[negative externality]"]
    money_keys = [("ghg_cost_m",-1), ("emp_ben_m",+1), ("water_cost_m",-1)]

    for mi, (mx, mfc, mec, ml, (mk, sign)) in enumerate(
            zip(money_xs, money_fc, money_ec, money_lbl, money_keys)):
        _box(mx, 3.3, 3.3, 1.2, fc=mfc, ec=mec, lw=1.6)
        _txt(mx+1.65, 4.0, ml, fs=7, fw="bold", col="#1a1a2e")
        if ssp_results:
            vals_m = [ssp_results[s][mk]*sign for s in ssp_list]
            bw2 = 2.8 / max(len(vals_m), 1)
            mxm = max(abs(v) for v in vals_m) + 0.01
            for bi2, (s, v) in enumerate(zip(ssp_list, vals_m)):
                bh2 = 0.45 * abs(v)/mxm + 0.04
                bx3 = mx + 0.25 + bi2 * bw2
                ax.add_patch(plt.Rectangle((bx3, 3.35), bw2*0.7, bh2,
                    facecolor=SSP_COLORS.get(s,"#888"), edgecolor="none", alpha=0.8, zorder=5))
                ax.text(bx3+bw2*0.35, 3.35+bh2+0.03, f"{v:.2f}",
                    fontsize=5, ha="center", va="bottom", color="#333", zorder=6)
        _arrow(channel_xs[mi]+1.4, 5.0, mx+1.65, 4.5, col=ch_ec[mi], lw=1.4)

    # Nature Debt / Dividend boxes
    _box(0.3, 1.6, 5.8, 1.35, fc="#fff3e8", ec="#cc6600", lw=1.8)
    _txt(3.2, 2.5,  "NATURE DEBT  (Year 0)", fs=8.5, fw="bold", col="#7a3300")
    _txt(3.2, 2.17, "GHG cost + Water cost − Construction employment", fs=7, col="#5a2200")
    _txt(3.2, 1.88, "Greener SSP → smaller debt → lower iNPV penalty", fs=6.5, col="#884400")

    _box(7.9, 1.6, 5.8, 1.35, fc="#e8fff0", ec="#006633", lw=1.8)
    _txt(10.8, 2.5,  "NATURE DIVIDEND  (Years 1 – T)", fs=8.5, fw="bold", col="#003d1a")
    _txt(10.8, 2.17, "Employment benefit + Avoided GHG savings − Op. water", fs=7, col="#002210")
    _txt(10.8, 1.88, "Greener SSP → larger dividend → higher S-IRR", fs=6.5, col="#005522")

    _arrow(2.0, 3.3, 2.5, 2.95, col="#cc6600", lw=1.5)
    _arrow(10.0, 3.3, 8.5, 2.95, col="#cc6600", lw=1.5)
    _arrow(7.0, 3.3, 9.5, 2.95, col="#006633", lw=1.5)
    _arrow(12.0, 3.3, 12.0, 2.95, col="#006633", lw=1.5)

    # iNPV and S-IRR output boxes
    _box(0.8, 0.5, 4.8, 1.3, fc="#eae8ff", ec="#6b4c9a", lw=2.0)
    _txt(3.2, 1.3,  "Integrated iNPV", fs=9, fw="bold", col="#3d1a7a")
    _txt(3.2, 0.95, "NPV − Nature Debt + PV(Nature Dividend)", fs=7, col="#2a0060")
    if ssp_results:
        best = max(ssp_results.values(), key=lambda r: r["inpv"])
        worst = min(ssp_results.values(), key=lambda r: r["inpv"])
        _txt(3.2, 0.65, f"{best['ssp']}: {best['inpv']:+.1f}M ↔ {worst['ssp']}: {worst['inpv']:+.1f}M",
             fs=6.5, col="#5500aa")

    _box(8.4, 0.5, 4.8, 1.3, fc="#eafff0", ec="#006633", lw=2.0)
    _txt(10.8, 1.3,  "Societal S-IRR", fs=9, fw="bold", col="#003d1a")
    _txt(10.8, 0.95, "Discount rate r* where iNPV(r*) = 0", fs=7, col="#002210")
    if ssp_results:
        sirr_pairs = [(s, r["s_irr"]) for s, r in ssp_results.items() if r["s_irr"]]
        if sirr_pairs:
            bs = max(sirr_pairs, key=lambda x: x[1])
            ws = min(sirr_pairs, key=lambda x: x[1])
            _txt(10.8, 0.65, f"{bs[0]}: {bs[1]*100:.2f}% ↔ {ws[0]}: {ws[1]*100:.2f}%",
                 fs=6.5, col="#005522")

    _arrow(3.2, 1.6, 3.2, 1.8, col="#cc6600", lw=1.5)
    _arrow(10.8, 1.6, 10.8, 1.8, col="#006633", lw=1.5)

    # Legend
    for i, (s, c) in enumerate(zip(ssp_list, ssp_cols)):
        ax.add_patch(plt.Rectangle((0.3+i*2.7, 0.05), 0.3, 0.2,
            facecolor=c, edgecolor="none", zorder=4))
        ax.text(0.65+i*2.7, 0.15, s, fontsize=7, va="center", color="#222", zorder=4)

    plt.tight_layout()
    return fig


def _fig_dashboard(project: dict, mon: dict, metrics: dict, sc_label: str,
                   dark_mode: bool = False) -> plt.Figure:
    """4-panel static Matplotlib integrated finance dashboard."""
    p, m = project, metrics
    T = p["project_years"]
    B = p["bond_years"]
    _bg = "#1a1a2e" if dark_mode else "#fafafa"
    _fg = "white"   if dark_mode else "#2c3e50"

    fig_d, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor=_bg)
    for ax in axes.flat:
        ax.set_facecolor(_bg)
    fig_d.suptitle(
        f"Integrated Finance Dashboard  |  {fmt_capex(p['capex_usd'])}  |  "
        f"{p['country']} ({p['region']})  |  {p['sector']}  |  {sc_label}",
        fontsize=11, fontweight="bold", y=1.01, color=_fg)

    yrs = list(range(T + 1))
    ax1 = axes[0, 0]
    ax1.plot(yrs, m["cum_npv"],  label=f"NPV  (WACC {p['wacc_base']*100:.1f}%)",
             color=C_FIN, lw=2.5)
    ax1.plot(yrs, m["cum_inpv"], label=f"iNPV (WACC {p['wacc_base']*100:.1f}%)",
             color=C_TOT, lw=2.5, ls="--")
    ax1.axhline(0, color="#555", lw=1.2)
    ax1.axvline(B, color="#f28e2b", lw=1.5, ls=":", label=f"Bond end (Yr {B})")
    ax1.set_xlabel("Year", fontsize=9); ax1.set_ylabel("M USD", fontsize=9)
    ax1.set_title("Cumulative NPV / iNPV", fontsize=10, fontweight="bold")
    ax1.legend(fontsize=8); ax1.spines[["top","right"]].set_visible(False)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax2 = axes[0, 1]
    yr_range = list(range(1, T + 1))
    _fc = np.full(T, mon["annual_fin_cf"])
    _mg = np.full(T, mon["annual_ghg_save_m"] - mon["annual_op_water_m"])
    _ms = np.full(T, mon["annual_emp_m"])
    ax2.bar(yr_range, _fc, label="Financial CF", color=C_FIN, alpha=0.85, edgecolor="none")
    ax2.bar(yr_range, _mg, label="GHG/Water",    color=C_GHG, alpha=0.85,
            edgecolor="none", bottom=_fc)
    ax2.bar(yr_range, _ms, label="Employment",   color=C_EMP, alpha=0.85,
            edgecolor="none", bottom=_fc+_mg)
    ax2.axvline(B+0.5, color="#f28e2b", lw=1.5, ls=":")
    ax2.axhline(0, color="#555", lw=1)
    ax2.set_xlabel("Year", fontsize=9); ax2.set_ylabel("M USD", fontsize=9)
    ax2.set_title(f"Annual Integrated Cash Flows (Yrs 1–{T})", fontsize=10, fontweight="bold")
    ax2.legend(fontsize=8, loc="upper right"); ax2.spines[["top","right"]].set_visible(False)

    ax3 = axes[1, 0]
    lbl = []; vals = []; cols = []
    if m["fin_irr"]:  lbl.append("Financial\nIRR"); vals.append(m["fin_irr"]*100); cols.append(C_FIN)
    lbl.append("WACC\nbase");  vals.append(p["wacc_base"]*100); cols.append("#aaa")
    lbl.append(f"WACC\nadj"); vals.append(m["wacc_adj"]*100);   cols.append("#59a14f")
    if m["s_irr"]:    lbl.append("Societal\nS-IRR"); vals.append(m["s_irr"]*100); cols.append(C_TOT)
    bars = ax3.bar(lbl, vals, color=cols, alpha=0.85, edgecolor="white", width=0.5)
    for b, v in zip(bars, vals):
        ax3.text(b.get_x()+b.get_width()/2, v+0.1, f"{v:.2f}%",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax3.set_ylabel("Rate (%)", fontsize=9)
    ax3.set_title("IRR Comparison", fontsize=10, fontweight="bold")
    ax3.spines[["top","right"]].set_visible(False)
    if vals: ax3.set_ylim(0, max(vals)*1.3)

    ax4 = axes[1, 1]; ax4.axis("off")
    irr_s  = f"{m['fin_irr']*100:.2f}%" if m["fin_irr"] else "N/A"
    sirr_s = f"{m['s_irr']*100:.2f}%"   if m["s_irr"]   else "N/A"
    kpi = [
        ["Parameter",              "Value"],
        ["CAPEX",                  fmt_capex(p["capex_usd"])],
        ["Bond / Project life",    f"{B} yr / {T} yr"],
        ["Sector / Region",        f"{p['sector']} / {p['region']}"],
        ["Scenario",               sc_label],
        ["────────────────────",   "──────────"],
        ["Annual Financial CF",    f"{mon['annual_fin_cf']:+.2f} M USD/yr"],
        ["Annual Nature Dividend", f"{mon['s_annual']:+.3f} M USD/yr"],
        ["Nature Debt (Yr 0)",     f"{-mon['s_constr_net']:+.3f} M USD"],
        ["────────────────────",   "──────────"],
        ["NPV (WACC base)",        f"{m['npv_base']:+.2f} M USD"],
        ["iNPV (WACC base)",       f"{m['inpv_base']:+.2f} M USD"],
        ["NPV (WACC adj)",         f"{m['npv_adj']:+.2f} M USD"],
        ["iNPV (WACC adj)",        f"{m['inpv_adj']:+.2f} M USD"],
        ["────────────────────",   "──────────"],
        ["Financial IRR",          irr_s],
        ["Societal S-IRR",         sirr_s],
        ["────────────────────",   "──────────"],
        ["WACC base",              f"{p['wacc_base']*100:.3f}%"],
        ["Sustainability disc.",   f"{m['sust_discount']*10000:.2f} bp"],
        ["WACC adjusted",          f"{m['wacc_adj']*100:.3f}%"],
        ["WWF water risk",         f"{m['wwf_water']:.3f} / 5.0"],
        ["Mean dep factor",        f"{m['mean_dep']:.3f}"],
    ]
    tbl = ax4.table(
        cellText=[[r[1]] for r in kpi[1:]],
        rowLabels=[r[0] for r in kpi[1:]],
        colLabels=[kpi[0][1]],
        cellLoc="right", rowLoc="left", loc="center",
        bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(8)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#ddd")
        if r == 0:
            cell.set_facecolor("#4e79a7"); cell.set_text_props(color="white", fontweight="bold")
        elif kpi[r][0].startswith("────"):
            cell.set_facecolor("#e8e8e8")
        else:
            cell.set_facecolor("#f7f7f7" if r % 2 == 1 else "white")
    ax4.set_title("Integrated Finance KPIs", fontsize=10, fontweight="bold", pad=8)

    plt.tight_layout()
    return fig_d


def _fig_atq_radar(
    country_iso2: str,
    template: str = "plotly_white",
    compare_iso2: str | None = None,
    title: str | None = None,
) -> go.Figure:
    """ATQ Transition Quality radar — country (+ optional comparison) vs frontier."""
    df_atq = _load_atq_data()

    def _get_vals(iso2: str) -> tuple[list[float], str]:
        name = ATQ_ISO2_TO_NAME.get(iso2, "")
        if name and not df_atq.empty and name in df_atq.index:
            return [float(df_atq.loc[name, d]) for d in ATQ_DIMENSIONS], name
        return [5.0] * len(ATQ_DIMENSIONS), f"{iso2} (no ATQ data)"

    c_vals, label   = _get_vals(country_iso2)
    theta_closed    = ATQ_DIM_LABELS + [ATQ_DIM_LABELS[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[10.0] * (len(ATQ_DIMENSIONS) + 1), theta=theta_closed,
        name="Frontier (10)", line=dict(color="gold", width=2, dash="dot"),
    ))
    fig.add_trace(go.Scatterpolar(
        r=c_vals + [c_vals[0]], theta=theta_closed,
        name=label, fill="toself", opacity=0.7,
    ))
    if compare_iso2 and compare_iso2 != country_iso2:
        cmp_vals, cmp_label = _get_vals(compare_iso2)
        fig.add_trace(go.Scatterpolar(
            r=cmp_vals + [cmp_vals[0]], theta=theta_closed,
            name=cmp_label, fill="toself", opacity=0.45, line=dict(dash="dash"),
        ))

    _title = title or f"EBRD ATQ 2024-25 — {label} vs Frontier"
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 10], tickvals=[2, 4, 6, 8, 10])),
        title=_title,
        template=template,
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.12),
        height=420,
    )
    return fig


def _fig_dependency_radar(df: pd.DataFrame, template: str = "plotly_white") -> go.Figure:
    """Polar chart: dep_factor and wwf_score per sector."""
    fig = go.Figure()
    for _, row in df.iterrows():
        sector_lbl = row.get("sector", "?")
        r_vals = [
            float(row.get("dep_factor", 1.0)),
            float(row.get("wwf_score", 3.0)),
            float(row.get("dep_factor", 1.0)),
        ]
        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=["ENCORE dep", "WWF water", "ENCORE dep"],
            name=sector_lbl, fill="toself", opacity=0.75,
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 5])),
        title="Nature dependency profile by sector",
        template=template,
        paper_bgcolor="rgba(0,0,0,0)",
        height=380,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENTATION & NARRATIVE TEXT
# Drawn from: integrated_finance_assessment.md, final_analysis.md,
#             onpv_formula_corrected.md, modeled_input_data/assumptions.txt
# ─────────────────────────────────────────────────────────────────────────────

# Per-project narrative profiles (§7 of integrated_finance_assessment.md)
PROJECT_PROFILES: dict[str, dict] = {
    "Rail_EU_DEV": {
        "overview": (
            "Large-scale European rail development project. Primarily greenfield infrastructure; "
            "full electrification eliminates diesel rolling stock. Serves **5.5 million passengers/year** "
            "at a 65% standard load factor. Annual Nature Dividend of **+$254.8 M/yr** is the portfolio's "
            "largest absolute societal cash flow, driven by 30,977 FTE construction employment at the "
            "European GVA/h rate of $111.61/h (DEU/F, NACE construction sector)."
        ),
        "sector_link": (
            "**Rail sector — Modal Shift Link:** Passenger density of 5.5M ppl/yr assumes a 65% standard "
            "load factor, setting line length and service frequency and therefore infrastructure cost. "
            "Air quality improvement (<1%) achieved via full electrification and removal of diesel rolling "
            "stock; investment includes the Power-to-Rail supply chain (substations and catenary). "
            "Climate resilience contribution (<5%) allocated to elevated tracks, drainage, and ERTMS "
            "signalling — 7% of total CAPEX is hardened."
        ),
        "key_finding": (
            "iNPV (+$9,972 M) is **112× the standard NPV** (+$89 M). The project creates "
            "societal value primarily through the employment channel: 30,977 FTE × 1,880 h/yr × "
            "$111.61/h = ~$6.5 B Nature Debt at t=0, and $254.8 M/yr in annual dividend. "
            "ESG greenium: WRF_physical = 2.906 (low), giving WACC_adj = 6.49% (−1 bp)."
        ),
        "ssp_note": (
            "SSP1-1.9 ≈ SSP4-6.0 > SSP2-4.5 > SSP3-7.0 ≈ SSP5-8.5. "
            "SSP4-6.0 ranks near SSP1 because its policy structure (inequality with technology access) "
            "keeps GHG intensity low and employment uplift high. Scenario spread: **$1,414 M** "
            "(SSP1 $10,505 M vs SSP5 $9,091 M iNPV), normalised 0.71/CAPEX."
        ),
    },
    "Rail_EU_OP1": {
        "overview": (
            "Operational maintenance tranche for European rail; no new construction. OPEX-heavy (6% of CAPEX/yr). "
            "Small absolute scale (EUR 130k / $140k) but demonstrates model granularity at micro-tranche level. "
            "Positive iNPV (+$0.59 M) across all SSPs — the employment channel (2 FTE × $121.47/h DEU/H49) "
            "dominates even at this scale."
        ),
        "sector_link": (
            "**Rail sector — Operations:** Rail_Op uses NACE H49 (Land Transport / Railways). "
            "GVA/labour-hour for DEU/H49 at 2030 = **$121.47/h** — highest among all project NACEs "
            "in this portfolio, reflecting the capital intensity and productivity of European rail operations. "
            "Avoided CO₂ = 0 tCO₂e/yr (maintenance-only, no modal shift credit)."
        ),
        "key_finding": (
            "iNPV of +$0.59 M vs NPV of −$0.08 M: the project is financially marginal but "
            "socially value-creating across all five SSPs. SVA/CAPEX = +4.86 — one of the "
            "highest in the portfolio on a per-dollar-invested basis."
        ),
        "ssp_note": (
            "Scenario spread = $0.10 M (SSP1 +0.63 M vs SSP5 +0.53 M). "
            "Employment channel dominates; water and GHG terms are negligible at this CAPEX scale."
        ),
    },
    "Rail_EU_OP2": {
        "overview": (
            "Identical structure to OP1; EUR 90k ($97k) CAPEX. Acts as minimum-scale validation of model — "
            "demonstrates that even sub-$100k transactions produce computable, non-trivial iNPV values "
            "when European GVA/h coefficients are applied."
        ),
        "sector_link": (
            "**Rail sector — Operations:** Same NACE H49 structure as OP1. "
            "Proportionally scaled to EUR 90k; all intensity ratios (FTE/M, GHG/M, iNPV/CAPEX) "
            "are nearly identical to OP1."
        ),
        "key_finding": (
            "iNPV +$0.41 M vs NPV −$0.06 M. SVA/CAPEX = +4.70. "
            "Portfolio minimum-scale anchor: proves the model is scale-invariant "
            "and does not require a size threshold to produce meaningful results."
        ),
        "ssp_note": (
            "Scenario spread = $0.07 M (SSP1 +0.43 M vs SSP5 +0.37 M). "
            "Same channel ordering as OP1."
        ),
    },
    "Proj_001": {
        "overview": (
            "Primary/preventive care hub reaching **5 million beneficiaries** at $50/person. "
            "Large construction footprint (6,394 FTE) generates a massive employment benefit. "
            "LATAM PPP import leakage increases supply-chain GHG — more investment flows to international "
            "medical equipment suppliers (higher Import Leakage in the IO table). "
            "Financial NPV = **−$196.6 M** — project requires societal accounting to demonstrate value."
        ),
        "sector_link": (
            "**Health sector — Capacity-to-Cost Link:** Fixed cost per beneficiary at the systemic/primary "
            "scale: $50/person for 5M reach. Regional adjustment: LATAM modelled with higher PPP import "
            "leakage — more supply-chain spending flows to international medical equipment suppliers, "
            "increasing the GHG and FTE footprint per dollar relative to a European hospital. "
            "The H&S stressor in this model is the primary clinical capacity outcome, not just "
            "construction site safety."
        ),
        "key_finding": (
            "iNPV +$2,028 M vs NPV −$197 M. SVA/CAPEX = **+8.90** — highest in the portfolio. "
            "Driven by BRA/Q GVA/h = $112.24/h: 6,394 FTE × 1,880 h × $112.24/h = $1.35 B "
            "construction-phase employment benefit alone. Annual Nature Dividend = +$81.0 M/yr. "
            "High water risk (WRF 3.788, high-risk flag) → revenue at risk = $42.0 M."
        ),
        "ssp_note": (
            "Scenario ordering: SSP1 ≈ SSP4 > SSP2 ≈ SSP3 ≈ SSP5. "
            "LATAM decarbonisation trajectory (SSP4 inequality dynamics) keeps supply-chain GHG "
            "moderate even under inequality scenario. Scenario spread = $109 M. "
            "Employment channel dominates (adj_emp range 1.126–1.184)."
        ),
    },
    "Proj_002": {
        "overview": (
            "3,000-beneficiary specialised surgical facility at $8,000/person (tertiary/high-intensity "
            "specialisation model). High WACC (9%) reflects Africa risk premium. Nigeria's low "
            "GVA/labour-hour coefficient (NGA/Q = **$5.04/h**) severely limits the employment benefit — "
            "the key structural constraint driving persistently negative iNPV."
        ),
        "sector_link": (
            "**Health sector — High-Intensity Specialisation:** $8,000/person for 3,000 beneficiaries "
            "(tertiary/surgical). Import leakage is highest in Africa: medical equipment procurement "
            "is almost entirely imported, so the IO supply chain shows high GHG intensity with limited "
            "domestic employment multiplier. NGA/Q GVA/h ($5.04) is ~22× below the European health "
            "sector ($84.94/h DEU/Q) — reflecting Nigeria's current sectoral GVA productivity, not "
            "a model artefact."
        ),
        "key_finding": (
            "iNPV **−$7.9 M** across all SSPs (negative). S-IRR = 1.26–2.25% (below any reasonable WACC). "
            "Societal VA = +$12–13 M (SVA/CAPEX = +0.50 — positive but modest). "
            "Two structurally valid alternatives to the baseline: (a) PPP shadow-price: uplift c_gva "
            "to global median ~$30–50/h → iNPV turns positive; (b) Anker living-wage floor: "
            "apply minimum $3/h (Anker Nigeria 2023) → conservative but guaranteed floor."
        ),
        "ssp_note": (
            "SSP1-1.9 gives the best outcome (adj_ghg = 0.041 — near-zero supply-chain GHG under "
            "aggressive decarbonisation) but iNPV remains negative even then. "
            "The GHG channel dominates (Africa SSP1 = 4% of baseline) because the employment channel "
            "is suppressed by the low c_gva. Scenario spread = $1.07 M (narrow)."
        ),
    },
    "Proj_003": {
        "overview": (
            "500,000-beneficiary general hospital under a European regulated tariff structure. "
            "Low WACC (6%) and European GVA/h ($84.94/h for DEU/Q — NACE Q Health sector) "
            "produce positive iNPV across all five IPCC scenarios. "
            "Annual Nature Dividend = +$9.5 M/yr."
        ),
        "sector_link": (
            "**Health sector — Capacity-to-Cost Link (European):** General hospital model. "
            "Lower import leakage than LATAM/Africa — European medical equipment is partly "
            "sourced domestically. NACE Q (Health and Social Work) maps to DEU/Q in WifOR: "
            "c_gva = $84.94/h, well above living wage, with GVA/LAB ratio of 1.42×."
        ),
        "key_finding": (
            "iNPV +$276.8 M vs NPV −$36.7 M. SVA/CAPEX = +4.18. "
            "Low WRF physical score (2.774) → not high-risk, $0 revenue at risk. "
            "Strongest SLB candidate among health projects."
        ),
        "ssp_note": (
            "Scenario risk = $44.4 M (SSP1 +$293.5 M vs SSP5 +$249.1 M). "
            "Positive across all five scenarios. SSP4-6.0 ranks near SSP1-1.9 "
            "(European grid decarbonises fast under SSP4 inequality-technology structure)."
        ),
    },
    "Hydro_AF": {
        "overview": (
            "Turbine refurbishment displacing **150,000 tCO₂e/yr** of coal-fired generation in Africa. "
            "Africa's high water scarcity coefficient (NGA/D35: c_water = −$1.95/m³) creates large "
            "**negative** annual Nature Dividend in operations. "
            "The negative dividend structure means iNPV is negative across all SSPs."
        ),
        "sector_link": (
            "**Hydro sector — Carbon-Displacement Link:** Turbine exchange provides 10–15% nameplate "
            "capacity/efficiency gain. Avoided CO₂ calculated against a coal-heavy marginal generation "
            "baseline (Africa grid is among the most carbon-intensive). Refurbishment CAPEX benchmark: "
            "$1,000/kW upgraded capacity (turbine runner + governor + generator rewinding). "
            "Water stressor is operational: hydro plants consume large volumes of evaporative "
            "reservoir water, priced at Africa's scarcity premium."
        ),
        "key_finding": (
            "iNPV **−$159.3 M**. Annual Nature Dividend = **−$15.4 M/yr** — water cost dominates. "
            "Despite 150,000 tCO₂e/yr avoided (valued at ~$1.1 M/yr at WifOR GHG_BASE), the "
            "operational water consumption at c_water = −$1.95/m³ creates a negative annual term "
            "that overwhelms GHG savings and employment. "
            "WRF_physical = 4.670 (high-risk), revenue at risk = $15.8 M."
        ),
        "ssp_note": (
            "Water-energy nexus (Channel 3) dominates. SSP1-1.9 gives the best outcome "
            "(adj_wat = 0.221 — lower renewable-related water demand) but iNPV remains "
            "deeply negative. Scenario spread = $1.0 M (very narrow — structural deficit). "
            "Under SSP3/SSP5, physical water stress worsens, increasing the negative dividend."
        ),
    },
    "Hydro_AS": {
        "overview": (
            "Portfolio's largest hydro project — **834,218 tCO₂e/yr** avoided. "
            "India's extreme water scarcity coefficient (IND/D35: c_water = **−$23.04/m³**) "
            "generates an annual Nature Debt in operations that overwhelms the financial returns "
            "and GHG-savings benefits. Annual Nature Dividend = **−$74.9 M/yr**."
        ),
        "sector_link": (
            "**Hydro sector — Carbon-Displacement Link (Asia):** Asia grid is the most "
            "carbon-intensive in the model — displacing 834,218 tCO₂e/yr represents the largest "
            "single GHG-avoidance credit in the portfolio. However, India's water scarcity index "
            "(WRI Aqueduct: near maximum stress in the Ganges/Indus catchments) translates "
            "directly into the highest c_water coefficient in the portfolio (−$23.04/m³). "
            "At 3,949 FTE × $54.98/h (IND/D35) = +$408 M construction employment, but this is "
            "overwhelmed by the operational water term."
        ),
        "key_finding": (
            "iNPV **−$499.7 M** (SSP2). S-IRR = 23.1% — but note: this is the rate at which "
            "the large negative PV of annual dividends is discounted to zero. It signals the "
            "project requires an *extraordinarily* high social return rate to break even — "
            "**not** a positive societal signal. "
            "WRF_physical = **4.970** (highest in portfolio), revenue at risk = $83.1 M."
        ),
        "ssp_note": (
            "Water-energy nexus dominates (Channel 3). SSP5-8.5 (adj_wat = 0.864) is the worst "
            "scenario; SSP1-1.9 (adj_wat = 0.499) is best. Scenario spread = $78.7 M. "
            "Structural recommendation: Commission InVEST Hydropower Water Yield model. "
            "Water-efficiency measures or water-right offset mechanisms are required before FID."
        ),
    },
    "Hydro_EU": {
        "overview": (
            "Small-scale European hydro efficiency improvement — **6,126 tCO₂e/yr** avoided. "
            "Despite its tiny absolute scale ($2M CAPEX), the European GVA/labour-hour coefficient "
            "for DEU/D35 (**$447.79/h** — highest in the portfolio) creates an outsized "
            "employment-driven iNPV of **+$30.5 M**. iNPV/CAPEX = 15.25."
        ),
        "sector_link": (
            "**Hydro sector — Carbon-Displacement Link (Europe):** Efficiency tweak; no new "
            "capacity. 6,126 tCO₂e/yr avoided at the European grid margin. "
            "DEU/D35 GVA/h = $447.79/h reflects the capital intensity and productivity of the "
            "European energy sector — 3.41× the actual labour compensation (LAB/h = $131.18/h). "
            "Even 31 FTE × 1,880 h × $447.79/h = $26.3 M Nature Debt at t=0."
        ),
        "key_finding": (
            "iNPV +$30.5 M vs NPV −$0.6 M. SVA/CAPEX = **+15.55** — highest in the portfolio. "
            "Demonstrates that very small projects can have outsized iNPV/CAPEX ratios when "
            "the supply chain operates in a high-coefficient region. "
            "WRF_physical = 3.170 (borderline high-risk), revenue at risk = $0.9 M."
        ),
        "ssp_note": (
            "Highest normalised scenario risk in the portfolio (2.81 Δ iNPV / CAPEX). "
            "At $2M CAPEX, even modest absolute SSP swings ($5.7 M) represent large relative "
            "differences. SSP1-1.9 = +$32.7 M, SSP5-8.5 = +$27.0 M. "
            "Employment channel dominates (adj_emp 0.944–1.116)."
        ),
    },
}

# ── Sector-specific methodology assumptions (from modeled_input_data/assumptions.txt)
SECTOR_ASSUMPTIONS_MD = """
### Health Sector — Capacity-to-Cost Link

The figures for the three hospital projects are based on **Service Density** and **Regional Tiering**:

- **Scale assumption** — Fixed cost per beneficiary: primary/preventative care (5M reach) = $50/person;
  tertiary/surgical care (3,000 reach) = $8,000/person.
- **Regional adjustment** — PPP variance: LATAM and Africa are modelled with higher **import leakage**,
  meaning more of the investment flows to international medical tech suppliers in the IO table
  (higher GHG/FTE footprint per dollar vs. European equivalents at the same NACE code).
- **H&S stressor** — "Improved H&S" is the *primary project outcome* (clinical capacity),
  not only construction site safety for workers.

### Hydro Sector — Carbon-Displacement Link

The Hydro estimates rely on **Grid Emission Factors** and **Technical Retrofit Benchmarks**:

- **Efficiency gain** — The "Turbine Exchange" provides a 10–15% increase in nameplate capacity or efficiency.
- **Avoided emissions** — Regional grid baseline used (Asia grid is coal-heavy → highest avoided-emissions
  credit for Hydro_AS). Avoided tCO₂e/yr = MW-equivalent avoided × regional carbon intensity.
- **Refurbishment CAPEX benchmark** — $1,000/kW of upgraded capacity (turbine runner + governor +
  generator rewinding).

### Rail Sector — Modal Shift Link

The Rail figures are driven by **European Infrastructure Standards** (2026):

- **Passenger density** — 5.5M ppl/yr assumes a 65% standard load factor, which sets line length and
  service frequency and in turn determines the infrastructure cost.
- **Air quality contribution** — <1% improvement via full electrification; investment includes the
  Power-to-Rail supply chain (substations and catenary).
- **Critical infrastructure** — <5% contribution from climate resilience (elevated tracks, drainage,
  ERTMS signalling); 7% of total CAPEX is hardened.
"""

# ── iNPV / S-IRR / WACC methodology (from §2 of integrated_finance_assessment.md)
METHODOLOGY_INTEGRATED_FINANCE_MD = """
## Integrated Finance Model

### iNPV — Integrated Net Present Value

Standard NPV captures only contractual financial cash flows. The **Integrated NPV (iNPV)** adds
monetised societal impacts at every time step:

$$iNPV = \\underbrace{\\sum_{t=1}^{T} \\frac{CF_t}{(1+r)^t} - CAPEX}_{NPV}
         \\underbrace{- S_{\\text{construction}}}_{-\\text{Nature Debt (t=0)}}
         + \\underbrace{\\sum_{t=1}^{T} \\frac{S_t}{(1+r)^t}}_{+PV(\\text{Nature Dividend})}$$

**Nature Debt** (construction phase, t = 0):
$S_{\\text{construction}} = \\text{GHG cost} + \\text{Water cost} - \\text{Employment benefit}$

All three terms derive from Leontief supply-chain analysis (EXIOBASE 3.8 IO table, tiers 0–10),
multiplied by WifOR H5 value-factor coefficients at FOCUS_YEAR.

**Annual Nature Dividend** (operational, years 1–T):
$S_t = \\text{Employment benefit}_t + \\text{Avoided GHG savings}_t - \\text{Operational water cost}_t$

The NPV bar is **identical across all SSP scenarios** (contractual cash flows are scenario-neutral).
The entire `iNPV – NPV` spread is the **Societal Value Added (SVA)**.

### Societal IRR (S-IRR)

$\\text{S-IRR} = r^* \\text{ such that } iNPV(r^*) = 0$

Solved via Brent's method. S-IRR > WACC → project creates integrated value above cost of capital.
**Caution for negative-iNPV projects:** a high S-IRR indicates the rate needed to discount the
negative annual dividend to zero — it is not a positive societal signal.

### ESG-Adjusted WACC

$$WACC_{adj} = WACC_{base} - \\Delta_{ESG}$$

$$\\Delta_{ESG} = \\min\\left(\\delta_{max},\\ \\frac{1 - \\overline{wrf}_{norm}}{2} \\times \\delta_{max} + \\frac{1 - \\overline{dep}_{norm}}{2} \\times \\delta_{max}\\right)$$

Maximum SLB greenium = **10 basis points** (δ_max = 0.0010), consistent with green-bond literature
(CBI 2023). Projects with low WRF physical scores and positive iNPV across all SSPs are the
strongest SLB candidates.

### SSP Transmission Channels

Three channels translate an IPCC scenario label into model inputs:

| Channel | Parameter | Mechanism |
|---------|-----------|-----------|
| **1 — GHG intensity** | `adj_ratio_ghg` | Energy-transition trajectory scales supply-chain GHG per dollar spent |
| **2 — Labour market** | `adj_ratio_employment` | Structural economic conditions scale FTE output per unit investment |
| **3 — Water-energy nexus** | `adj_ratio_water` | Renewable penetration determines supply-chain water intensity |

Calibrated from `tvpdbio_intensity_factors.csv` (OSeMOSYS/REMIND-MAgPIE coupled models).
"""

# ── WifOR value factors and GVA/h table (from §3.2 and §3.5)
WIFOR_VF_MD = """
## WifOR Value Factors — H5 Coefficient Files

Coefficients are loaded live from WifOR Institute H5 files at FOCUS_YEAR.
Employment is monetised via **GVA per labour-hour** (productivity-based living-wage proxy).

| Factor | File | Unit | Approx. @ DEU/F 2030 |
|--------|------|------|----------------------|
| **GHG_BASE** (Nordhaus DICE) | `MonGHG_my.h5` | USD/kg CO₂e | −0.1047 (≈ $105/tCO₂e) |
| **GHG_PARIS-aligned** | `MonGHG_my.h5` | USD/kg CO₂e | −0.1140 (≈ $114/tCO₂e) |
| **Water** (Blue Consumption) | `MonWaterCon_my.h5` | USD/m³ | −0.256 (DEU); −23.04 (IND) |
| **GVA / labour-hour** | `training_value_per_hour_bysector.h5` | USD/h | $111.61 (DEU/F) |

**Why GVA per labour-hour?** The `value_per_hour_GVA_2020USD_PPP` field represents the sector's
gross value added per hour of work — the full economic output attributable to one labour-hour.
In most markets GVA/h exceeds the Anker living wage, making it the appropriate floor coefficient.
Projected to FOCUS_YEAR via the MonTrain growth index (≈1.12%/yr real).

**Conversion formula:**
- GHG: `M USD = tCO₂e × 1,000 kg/t × c_ghg / 1,000,000`
- Water: `M USD = 1,000 m³ × 1,000 m³/unit × c_water / 1,000,000`
- Employment: `M USD = FTE × 1,880 h/yr × c_gva / 1,000,000`

**GVA/h cross-project table (2030 projection):**

| Country | NACE | Sector | c_gva (USD/h) | GVA/LAB ratio | Anker LW | LW Met? |
|---------|------|--------|--------------|---------------|----------|---------|
| DEU | F | Rail_Dev / Construction | $111.61 | 1.44× | ~$16–20/h | ✓ |
| DEU | H49 | Rail_Op | $121.47 | 1.97× | ~$16–20/h | ✓ |
| DEU | Q | Health | $84.94 | 1.42× | ~$16–20/h | ✓ |
| DEU | D35 | Energy | $447.79 | 3.41× | ~$16–20/h | ✓ |
| BRA | Q | Health_Social | $112.24 | 1.43× | ~$40/h PPP | ✓ |
| NGA | Q | Health_Specialized | $5.04 | 9.2× | ~$2–3/h PPP | ✓* |
| IND | D35 | Energy/Hydro | $54.98 | 2.30× | ~$3–6/h PPP | ✓ |
| NGA | D35 | Energy/Hydro | $5.78 | 20.0× | ~$2–3/h PPP | ✓* |

\\* NGA GVA/h is above ILO poverty threshold ($0.24/h) but below Anker Nigeria living wage (~$2–3/h PPP).
GVA/LAB = 9–20× in Nigeria reflects an extractive sectoral structure.

**IPCC SCC comparison:** WifOR GHG_BASE 2030 ≈ $105/tCO₂e = 61% of IPCC AR6 WG3 central ($171/tCO₂e).
All iNPV figures are therefore conservative lower bounds. Multiply GHG cost/savings by ×1.63
to obtain IPCC-aligned estimates.
"""

# ── Nature dependency scoring (from §3.3 and §6)
NATURE_DEP_MD = """
## Nature Dependency Scoring (ENCORE / WWF / EXIOBASE)

The combined `dep_factor` captures nature-related risk amplification per tier, sector, and region:

| Component | Framework | Score range | Weight |
|-----------|-----------|-------------|--------|
| ENCORE ecosystem materiality | ENCORE / TNFD | 1–5 per stressor | 1/3 |
| WWF Water Risk Filter (WRF) physical | WWF WRF 2.0 | 1–5 | 1/3 |
| Supply-chain sector sensitivity | EXIOBASE/IPBES sector typology | 0.33–1.67 | 1/3 |
| **Combined dep_factor** | | **0.33–1.67** (neutral = 1.0) | |

The dep_factor multiplies the scenario-adjusted supply-chain stressors to produce
**dependency-weighted** quantities that feed into the WACC ESG greenium calculation.

**WWF WRF Portfolio Summary:**

| Project | WRF Physical | High Risk | Revenue at Risk |
|---------|-------------|-----------|----------------|
| Rail_EU_DEV/OP1/OP2 | 2.906 | No | $0 M |
| Proj_003 | 2.774 | No | $0 M |
| Hydro_EU | 3.170 | Yes | $0.9 M |
| Proj_002 | 4.087 | Yes | $3.6 M |
| Hydro_AF | 4.670 | Yes | $15.8 M |
| Proj_001 | 3.788 | Yes | $42.0 M |
| **Hydro_AS** | **4.970** | **Yes** | **$83.1 M** |

**Portfolio: 5/9 high-risk · total revenue at risk = $145.2 M**

In line with IPBES Global Assessment (2022): projects with WRF_physical > 4.0 operate in
watersheds experiencing high-to-very-high physical water stress. Under SSP3-7.0/SSP5-8.5,
water scarcity costs grow non-linearly — the current linear model (P2, see ONPV Limitations)
understates downside risk for Hydro_AS and Hydro_AF.
"""

# ── ONPV formula problems (from onpv_formula_corrected.md)
ONPV_GAPS_MD = """
## ONPV Formula Gaps — Known Limitations

*Source: onpv_formula_corrected.md · Wetzer et al. (2024) Science 383:152*

The iNPV implementation is a first-order approximation. Eight structural problems (P1–P8) are
identified in the underlying ONPV specification:

| ID | Problem | Direction of bias |
|----|---------|-------------------|
| **P1** | Overshoot toggle O is binary (0/1) — real resource damage is a gradient | Cliff-edge: 99% of safe yield = 0% overshoot; 101% = full premium |
| **P2** | Scarcity premium linear `(1+O×S)` — true damage function is **convex** | Understates cost near critical thresholds (Hydro_AS/AF most affected) |
| **P3** | Single EF_exposure — physical, transition, and legal channels have different profiles | Conflates three structurally distinct risk types |
| **P4** | `(1−VR)` reduces impact linearly — legal exposure is **threshold-gated** | Partial management acknowledgement may worsen legal exposure |
| **P5** | `L_legal` (attribution-based litigation liability) **entirely absent** | Understates downside; Hydro projects and Health in Africa most exposed |
| **P6** | Σ assumes additivity — combined stressor shocks are **multiplicative** | Understates combined risk under simultaneous GHG + water stress |
| **P7** | Static WACC — does not reprice as climate risk evolves over project lifetime | May under/overstate cost of capital in later project years |
| **P8** | L_legal uncapped — can theoretically exceed insolvency value | Systemic risk signal for highly-exposed projects not currently captured |

**Corrected formula (conceptual):**
```
iNPV = Σ [ Physical_Unit × VF × f_scarcity(O, S)
           × (w_p·EF_physical + w_t·EF_transition + w_l·EF_legal)
           × g_readiness(VR, BF) × AF_direct ]
       + Σ [ L_legal_effective × AF_engagement ]
       + Interaction_penalty
```
where `f_scarcity(O,S) = (1+S)^(1+O)` (convex) and `g_readiness` is threshold-gated.

**To obtain IPCC-aligned estimates** from this model: multiply all GHG cost/savings by ×1.63
(= $171/tCO₂e ÷ $105/tCO₂e). Under IPCC SCC, Hydro_AF/AS GHG-savings credits grow ×1.63
but are still likely insufficient to offset water scarcity costs at India/Africa levels.
"""

# ── CFA / IPBES / IPCC alignment (from §1 of integrated_finance_assessment.md)
CONCEPTUAL_FRAMEWORK_MD = """
## Conceptual Framework

### CFA Alignment — Financial Valuation Layer

| CFA concept | Application in this model |
|-------------|--------------------------|
| **NPV** | Discounted sum of contractual cash flows (revenue – OPEX) over project lifetime, minus CAPEX at t=0 |
| **IRR** | Rate r* at which financial NPV = 0; comparable to bond YTM |
| **WACC** | Blended debt/equity hurdle rate, adjusted for ESG sustainability discount |
| **Duration** | Cash-flow-weighted maturity; bond coupon covers 5–15 yr, project tail 15–35 yr |
| **Yield spread** | ESG SLB discount of 0–10 bps vs conventional debt |
| **Enterprise value** | Extended to include discounted societal cash flows (iNPV) |
| **Risk-adjusted return** | WACC_adj = WACC_base − sustainability_discount |

### IPBES Alignment — Biodiversity and Ecosystem Services Layer

The nature-risk layer is grounded in the **IPBES Global Assessment (2022)**:

| IPBES service category | Model proxy | Stressor |
|------------------------|-------------|---------|
| Regulation of freshwater | Blue water consumption (1,000 m³) | `MonWaterCon_my.h5` |
| Regulation of air quality | GHG emissions (tCO₂e) | `MonGHG_my.h5` |
| Labour income / human capital | Employment × GVA per labour-hour | `training_value_per_hour_bysector.h5` |

ENCORE materiality rates each sector's dependence on 21 ecosystem services (1–5 scale).
Combined with WWF WRF physical and BRF scores, this produces `dep_factor ∈ [0.33, 1.67]`.

In line with IPBES findings that 1 million species face extinction risk and freshwater ecosystem
health has declined 84% since 1970, projects in water-intensive sectors in Asia and Africa
carry the highest nature-related financial risk (WRF up to 4.97).

### IPCC Alignment — Climate Scenario Layer

| SSP | Warming 2100 | Narrative | Key supply-chain effect |
|-----|-------------|-----------|------------------------|
| **SSP1-1.9** | ~1.5 °C | Sustainability — rapid decarbonisation | Lowest GHG intensity; highest employment uplift |
| **SSP2-4.5** | ~2.7 °C | Middle of the road | Moderate on all channels; model baseline |
| **SSP3-7.0** | ~3.6 °C | Regional rivalry | High GHG intensity; near-neutral employment |
| **SSP4-6.0** | ~3.0 °C | Inequality with technology access | Low GHG (policy decoupling); strong employment |
| **SSP5-8.5** | ~4.4 °C | Fossil-fuelled development | Highest GHG; weakest employment dividend |

*Source: IPCC AR6 WGI SPM (2021); IPCC AR6 WGIII Chapter 3 (2022)*

**SSP4-6.0 ordering:** SSP4 consistently ranks near SSP1-1.9 for European projects, despite
higher absolute warming, because its policy structure keeps GHG intensity low *and* employment
uplift high through technological access under inequality — similar outcomes to SSP1 on all
three transmission channels.
"""

# ── Portfolio synthesis and recommendations (from §9 of integrated_finance_assessment.md)
PORTFOLIO_SYNTHESIS_MD = """
## Portfolio Synthesis and Investment Implications

### iNPV Classification

| Classification | Projects | Rationale |
|----------------|---------|-----------|
| **Integrated value positive — all SSPs** | Rail_EU_DEV, Rail_EU_OP1/OP2, Proj_001, Proj_003, Hydro_EU | iNPV > 0 across all five scenarios |
| **Borderline — structurally constrained** | Proj_002 (Africa) | Employment channel too weak at NGA/Q GVA/h; S-IRR 1.26–2.25% |
| **Structurally negative — water cost dominant** | Hydro_AF, Hydro_AS | Operational water scarcity overrides financial CF and GHG savings |

### SSP Channel Dominance by Sector

| Sector | Dominant channel | Rationale |
|--------|-----------------|-----------|
| **Rail (EU)** | Employment (Ch. 2) | DEU GVA/h $111–121/h amplifies 30k+ FTE; employment channel >> others |
| **Health (LATAM/EU)** | Employment (Ch. 2) | BRA/Q $112/h × 6,394 FTE = $1.35 B construction benefit |
| **Health (Africa)** | GHG intensity (Ch. 1) | NGA/Q $5.04/h eliminates employment; SSP1 adj_ghg = 0.041 |
| **Hydro (Asia/Africa)** | Water-energy nexus (Ch. 3) | c_water = −$23/m³ (IND) / −$1.95/m³ (NGA) is the swing factor |

### Structural Recommendations

1. **Hydro_AS / Hydro_AF** — Water costs dominate. Operational water-efficiency measures or
   water-right offset mechanisms are required before FID. Current model parameters show
   both projects destroy integrated value despite large GHG-avoidance credits.

2. **Proj_002 (Africa)** — NGA/Q GVA/h ($5.04/h) reflects Nigeria's current sectoral
   productivity. Two analytically sound alternatives: (a) PPP shadow-price to global
   median ~$30–50/h → iNPV turns positive; (b) Anker living-wage floor ~$3/h Nigeria.

3. **Hydro_EU** — Demonstrates outsized iNPV/CAPEX (+15.25) from a $2M base. Scale-up or
   portfolio-aggregation strategies for European small hydro are attractive under SLB structures.

4. **Portfolio diversification** — SSP4-6.0 consistently scores near SSP1-1.9 for European
   projects. Portfolio managers should not assume monotonic iNPV improvement under lower-emission
   scenarios — the inequality channel (SSP4) can produce similar co-benefits to the green-
   transition channel (SSP1).

5. **SLB structuring** — Best candidates: Rail_EU_DEV (WRF 2.906, iNPV positive all SSPs,
   10 bps → saves ~$2M over bond lifetime) and Proj_003 (WRF 2.774, 10 bps). Proj_001
   (WRF 3.788 high-risk flag) requires nature-risk mitigation covenants first.

### All-SSP iNPV Summary

| Project | SSP1-1.9 | SSP2-4.5 | SSP3-7.0 | SSP4-6.0 | SSP5-8.5 | Scenario Risk (M) |
|---------|---------|---------|---------|---------|---------|-----------------|
| Rail_EU_DEV | +10,504.7 | +9,972.4 | +9,338.4 | +10,435.5 | +9,090.7 | **1,414** |
| Rail_EU_OP1 | +0.63 | +0.59 | +0.55 | +0.63 | +0.53 | 0.10 |
| Rail_EU_OP2 | +0.43 | +0.41 | +0.38 | +0.43 | +0.37 | 0.07 |
| Proj_001 | +2,116.5 | +2,027.7 | +2,005.5 | +2,027.6 | +2,007.4 | 111.1 |
| Proj_002 | −7.24 | −7.90 | −8.14 | −8.23 | −8.31 | 1.07 |
| Proj_003 | +293.5 | +276.8 | +256.9 | +291.3 | +249.1 | 44.4 |
| Hydro_AF | −158.7 | −159.3 | −159.5 | −159.6 | −159.7 | 1.0 |
| Hydro_AS | −482.9 | −499.7 | −557.1 | −490.2 | −561.6 | 78.7 |
| Hydro_EU | +32.7 | +30.5 | +28.0 | +32.4 | +27.0 | 5.7 |
"""

ABBREVIATIONS_MD = """
## Index of Abbreviations

| Abbreviation | Full term | Context |
|---|---|---|
| **adj_ratio_emp** | SSP employment adjustment ratio | Multiplier applied to FTE output per unit investment under each climate scenario |
| **adj_ratio_ghg** | SSP GHG intensity adjustment ratio | Multiplier applied to supply-chain GHG per dollar spent, driven by grid decarbonisation trajectory |
| **adj_ratio_water** | SSP water adjustment ratio | `1 − renewable_share × 0.85`; captures water-energy nexus under each SSP |
| **AIMM** | Anticipated Impact Measurement and Monitoring | IFC/MDB framework for assessing project development impact |
| **ATQ** | Assessment of Transition Qualities | EBRD annual reform benchmarking tool; 6 dimensions scored 1–10 vs advanced-economy frontier |
| **bc_deficit_mult** | Biocapacity deficit multiplier | `1.0` if ecological surplus; `min(1.5, 1 + |deficit|/BC_total)` if in overshoot. Scales `dep_factor` upward for countries in ecological deficit. Source: GFN NFA 2023 |
| **BC** | Biocapacity | Total biological regenerative capacity of a country's ecosystems, in global hectares (gha). Source: GFN NFA 2023 |
| **BP** | Basis point | 1 bp = 0.01 percentage points (used for WACC adjustments) |
| **BRF** | Biodiversity Risk Framework | WWF framework assessing sectoral dependence on biodiversity; combined with WRF to form `dep_factor` |
| **CAPEX** | Capital Expenditure | Total upfront investment cost in USD |
| **CFA** | Chartered Financial Analyst | Refers to CFA Institute's investment analysis framework (NPV, IRR, WACC, efficient frontier) |
| **c_ghg** | GHG value factor | Social cost per kg CO₂e, from WifOR H5 (Nordhaus DICE baseline ≈ −$0.105/kg) |
| **c_gva** | GVA per labour-hour value factor | Gross Value Added per labour-hour in USD/h, used as employment monetisation proxy |
| **c_water** | Water value factor | Shadow price per m³ of blue water consumption in USD/m³ |
| **CSRD** | Corporate Sustainability Reporting Directive | EU mandatory sustainability disclosure regulation (effective 2024) |
| **DEU / BRA / NGA / IND** | ISO-3 country codes | Germany / Brazil / Nigeria / India — regional proxies for IO analysis |
| **dep_factor** | Nature-dependency factor | Composite score `∈ [0.33, 1.67]` = geometric mean of ENCORE materiality, WWF WRF physical, and supply-chain sector sensitivity |
| **DFI** | Development Finance Institution | Multilateral or bilateral institution providing concessional finance (EBRD, IFC, ADB, etc.) |
| **EBRD** | European Bank for Reconstruction and Development | Multilateral DFI; source of ATQ country scores |
| **EF** | Ecological Footprint | Total biologically productive area required to provide resources used and absorb waste, in gha |
| **EF_carbon** | Carbon ecological footprint | `GHG_tCO₂e × (1−0.35) / 2.677 × 1.3` gha; carbon sequestration demand of project GHG |
| **EF_land** | Land ecological footprint | Simplified proxy: `land_ha × 2.1` (cropland EQF 2.1 gha) |
| **ENCORE** | Exploring Natural Capital Opportunities, Risks and Exposure | UNEP-WCMC / WWF tool mapping 21 ecosystem services to business dependencies (1–5 materiality scale) |
| **EP** | Environmental Policy / Equator Principles | Refers to AIIB Environmental Policy or Equator Principles risk management framework |
| **ESG** | Environmental, Social and Governance | Non-financial risk/return dimensions integrated into investment analysis |
| **ETI** | Efficiency of Transition Investment | EBRD internal additionality score; product of country gap and sectoral intensity |
| **EXIOBASE** | Extended Input-Output Table for Europe and Beyond | Multi-regional IO database (43 countries, 163 sectors); source of supply-chain stressor intensities |
| **FTE** | Full-Time Equivalent | Standard labour unit = one person working 1,880 hours/year |
| **GFN** | Global Footprint Network | NGO producing National Footprint and Biocapacity Accounts (NFA) |
| **gha** | Global hectare | Standardised unit of biologically productive land/sea area, weighted by productivity |
| **GHG** | Greenhouse Gas | CO₂-equivalent emissions aggregated across GWP100 (CO₂, CH₄, N₂O, F-gases) |
| **GVA** | Gross Value Added | GDP measure = output − intermediate consumption; used as employment benefit proxy |
| **iNPV** | Integrated Net Present Value | NPV extended with monetised societal impacts: `iNPV = NPV − Nature Debt + PV(Nature Dividend)` |
| **IO** | Input-Output (analysis) | Leontief supply-chain model tracing upstream stressors through the economy |
| **IPBES** | Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services | UN body; Global Assessment (2022) underpins biodiversity risk layer |
| **IPCC** | Intergovernmental Panel on Climate Change | UN body; AR6 (2021-22) underpins SSP scenarios and carbon cost benchmarks |
| **IRR** | Internal Rate of Return | Discount rate at which NPV = 0; financial performance benchmark |
| **ISO-2** | Two-letter ISO 3166-1 country code | e.g. DE = Germany, PL = Poland |
| **ISO-3** | Three-letter ISO 3166-1 country code | e.g. DEU = Germany, BRA = Brazil; used for WifOR H5 file lookups |
| **LATAM** | Latin America | Regional grouping; IO proxy = BRA (Brazil) |
| **MDB** | Multilateral Development Bank | See DFI |
| **NACE** | Nomenclature of Economic Activities | EU statistical classification of economic activities; used for WifOR H5 sector lookups |
| **NFA** | National Footprint and Biocapacity Accounts | GFN annual dataset of EF and BC per country (2023 edition used) |
| **NPV** | Net Present Value | Sum of discounted financial cash flows minus CAPEX; standard investment valuation metric |
| **NVD** | Nature Value Dividend | Annual net monetised societal benefit from operational phase (employment benefit − GHG cost − water cost) |
| **OCI** | Overshoot Contribution Index | `(EF_carbon + EF_land) / BC_total × 100`; project's EF as % of host country's biocapacity |
| **ONPV** | Original / "old" NPV | Term used in methodology notes for the pre-integration NPV formulation; replaced by iNPV |
| **OPEX** | Operating Expenditure | Annual operating costs as a fraction of CAPEX |
| **OSeMOSYS** | Open Source Energy Modelling System | Energy system model used to calibrate SSP GHG intensity adjustment factors |
| **PAI** | Principal Adverse Impact | SFDR Annex I mandatory disclosure indicators (e.g. GHG intensity, biodiversity) |
| **PPP** | Purchasing Power Parity | Adjustment factor for comparing monetary values across countries |
| **PV** | Present Value | Discounted value of future cash flows at a specified discount rate |
| **REMIND-MAgPIE** | Regional Model of Investments and Development — Model of Agricultural Production and its Impact on the Environment | Coupled energy-land-use model; source of SSP employment and water adjustment factors |
| **SCC** | Social Cost of Carbon | Monetary value of damage from emitting one tonne of CO₂e; IPCC AR6 central = $171/tCO₂e |
| **SFDR** | Sustainable Finance Disclosure Regulation | EU regulation requiring DFI/fund-level ESG disclosures (Article 8/9; PAI Annex I) |
| **SLB** | Sustainability-Linked Bond | Bond whose coupon adjusts based on achievement of sustainability KPIs (ESG WACC discount source) |
| **S-IRR** | Societal Internal Rate of Return | IRR applied to the integrated cash flow stream `[−CAPEX, S_1, …, S_T]`; rate at which iNPV = 0 |
| **SSP** | Shared Socioeconomic Pathway | IPCC climate-economy scenario framework (SSP1-1.9 → SSP5-8.5); drives three transmission channels |
| **SVA** | Societal Value Added | `iNPV − NPV`; the portion of integrated return attributable to societal externalities |
| **TCFD** | Task Force on Climate-related Financial Disclosures | Voluntary climate disclosure framework; scenario analysis required |
| **Tier 0** | Direct supply-chain tier | CAPEX spent directly with construction contractors (NACE F, H49, D35, Q) |
| **Tier 1** | First upstream tier | What Tier 0 suppliers procure; includes bilateral sourcing-country effects |
| **TNFD** | Taskforce on Nature-related Financial Disclosures | Nature-equivalent of TCFD; OCI > 0.1% triggers disclosure flag |
| **TVP** | Transition Value Programme (internal project name) | Framework combining iNPV, ATQ, and EarthOvershoot for integrated infrastructure assessment |
| **WACC** | Weighted Average Cost of Capital | Blended hurdle rate `= E/(E+D)×r_e + D/(E+D)×r_d×(1−τ)` |
| **WACC_adj** | ESG-adjusted WACC | `WACC_base − Δ_ESG`; reduced hurdle rate earned through low water risk and nature dependency |
| **WifOR** | Wirtschaftsforschung (Economic Research) Institute | German research institute providing H5 value factor files (GHG, water, GVA/h) by ISO-3/NACE/year |
| **WRF** | Water Risk Framework | WWF tool scoring physical and reputational water risk 0–5; source: WWF WRF 2.0 |
| **WWF** | World Wide Fund for Nature | Provides WRF and BRF biodiversity risk scores used in `dep_factor` |
"""

FINANCIAL_FIGURES_MD = """
## Financial and Impact Figures — Plain-Language Guide

### Capital Expenditure (CAPEX)
The total upfront investment cost in USD at time zero. All supply-chain stressors (GHG, water,
employment) are proportional to CAPEX via EXIOBASE intensity coefficients (tCO₂e/M USD invested,
FTE/M USD, 1,000 m³/M USD). Increasing CAPEX scales all impact channels linearly.

### Standard Net Present Value (NPV)
$$NPV = -CAPEX + \\sum_{t=1}^{T} \\frac{CF_t}{(1+WACC)^t}$$
where $CF_t = Revenue_t - OPEX_t - DebtService_t$.
- **Revenue**: `CAPEX × revenue_yield` per year (set in sidebar slider, default 10%)
- **OPEX**: `CAPEX × opex_ratio` per year (default 5%)
- **Debt service**: bond coupon over the bond lifetime only

A negative NPV means the project does not cover its cost of capital on financial terms alone —
this is common for infrastructure and DFI projects, which is the rationale for blended finance.

### Integrated Net Present Value (iNPV)
$$iNPV = NPV - \\underbrace{Nature\\,Debt}_{{\\text{construction externalities}}} + \\underbrace{PV(Nature\\,Dividend)}_{{\\text{operational externalities}}}$$
- **Nature Debt** (t=0): GHG cost + water cost − employment benefit from the construction supply chain. Always negative when GHG and water costs exceed employment benefits.
- **Nature Dividend** (years 1–T): Annual avoided GHG savings (if `avoided_co2 > 0`) + employment benefit − operational water cost. Discounted at `WACC_adj`.
- **Societal Value Added (SVA)** = iNPV − NPV. A positive SVA is the quantitative additionality case for public/concessional co-financing.

A project with NPV < 0 but iNPV > 0 should receive blended finance up to SVA to make it
bankable — society's share of the return (SVA) justifies a public subsidy of that amount.

### Financial IRR vs Societal IRR (S-IRR)
- **Financial IRR**: rate at which NPV = 0. Comparable to a bond yield-to-maturity.
- **S-IRR**: rate at which iNPV = 0, applied to the stream `[−CAPEX, S_1, …, S_T]` where $S_t$ is the annual nature dividend.
- **S-IRR > Financial IRR** → the project's societal return exceeds its financial hurdle rate: the strongest possible signal for blended or public finance engagement.
- **Caution — negative annual dividend**: If the annual nature dividend is consistently negative (e.g., hydro projects where water costs dominate), the S-IRR solver may return a high value that does *not* signal a positive outcome — it is the rate needed to discount the negative stream to zero.

### ESG-Adjusted WACC (WACC_adj)
$$WACC_{adj} = WACC_{base} - \\Delta_{ESG}$$
$$\\Delta_{ESG} = \\underbrace{(1 - \\overline{WRF}_{norm}) \\times \\delta_{water}}_{\\text{water discount}} + \\underbrace{(1 - \\overline{dep}_{norm}) \\times \\delta_{dep}}_{\\text{dependency discount}}$$
- **Sustainability discount** (Δ_ESG): capped at 10 bp (δ_max = 0.001), consistent with green-bond literature (CBI 2023). Applied as an SLB greenium.
- **Water discount component**: projects with low WWF WRF physical scores earn a larger discount.
- **Dep resilience discount**: projects in low-dependency sectors earn a larger discount.
- The adjusted WACC is used to discount all future cash flows in both NPV and iNPV.

### Nature Debt
The present-value cost of construction-phase externalities at t=0:
$$Nature\\,Debt = GHG\\,cost_{construction} + Water\\,cost_{construction} - Employment\\,benefit_{construction}$$
All three terms come from Leontief supply-chain analysis (EXIOBASE 3.8, tiers 0–10), multiplied
by WifOR H5 value-factor coefficients at FOCUS_YEAR. A large negative Nature Debt indicates
the project's construction supply chain produces more GHG + water cost than employment benefit.

### Annual Nature Dividend
$$Nature\\,Dividend_t = Employment\\,benefit_t + Avoided\\,GHG\\,savings_t - Water\\,cost_t$$
The employment benefit uses the FTE count from the IO model multiplied by `c_gva` (GVA per
labour-hour × 1,880 h/yr). The avoided GHG term scales `avoided_co2` by the SSP-adjusted GHG
value factor. The water cost uses operational water consumption × `c_water`.

### dep_factor (Nature-Dependency Factor)
$$dep\\_factor = \\left(\\frac{enc_{norm}}{1} + \\frac{wwf_{phys}}{1} + \\frac{sc_{dep}}{1}\\right) / 3$$
Three evidence streams, each normalised to neutral = 1.0:
1. **ENCORE materiality**: sector's dependence on 21 ecosystem services (scored 1–5)
2. **WWF WRF physical score**: regional water-risk intensity (scored 0–5)
3. **Supply-chain sensitivity index**: sector-level empirical water/biodiversity exposure

`dep_factor > 1.0` → above-neutral dependency, smaller ESG WACC discount, higher iNPV risk.
`bc_deficit_mult` (from EarthOvershoot) scales `dep_factor` upward for countries in ecological deficit.

### Impact Sharpe Ratio
$$Impact\\,Sharpe = \\frac{\\overline{iNPV}}{\\sigma(iNPV)}$$
Computed across 5 SSP scenarios. Higher = better risk-adjusted societal return.
Analogous to a CFA portfolio Sharpe ratio but applied to the societal return distribution
instead of financial returns. Used in the Portfolio Manager risk dashboard.

### OCI — Overshoot Contribution Index
$$OCI\\,(\\%) = \\frac{EF_{carbon} + EF_{land}}{BC_{total}} \\times 100$$
Measures what share of the host country's total biocapacity the project claims via its
carbon and land ecological footprint. TNFD disclosure threshold: OCI > 0.1%.
- **EF_carbon** = supply-chain GHG × (1−0.35)/2.677 × 1.3 gha (GFN sequestration factors)
- **EF_land** = land_ha × 2.1 gha (cropland equivalence factor; currently 0 as land input not yet wired)
- **BC_total** from GFN NFA 2023 national accounts

### Scenario VaR (iNPV at SSP5-8.5)
The worst-case iNPV under the fossil-fuelled high-emission scenario (SSP5-8.5, ~4.4°C warming).
This is the project's **climate Value-at-Risk**: the integrated return under the most adverse
supply-chain decarbonisation trajectory. Used in the Portfolio Manager CFA risk summary.
"""

REFERENCES_MD = """
## References and Data Sources

### IPCC Climate Scenarios

| Reference | Role in model | DOI / URL |
|-----------|--------------|-----------|
| **IPCC AR6 WGI SPM (2021)** | SSP scenario definitions; warming levels at 2100 | https://doi.org/10.1017/9781009157896 |
| **IPCC AR6 WGII (2022)** | Physical climate risk to infrastructure; freshwater impacts | https://doi.org/10.1017/9781009325844 |
| **IPCC AR6 WGIII Ch.3 (2022)** | Mitigation pathways; central SCC ≈ $171/tCO₂e | https://doi.org/10.1017/9781009157926 |
| **Riahi et al. (2017)** | SSP1–SSP5 narrative and quantification | https://doi.org/10.1016/j.gloenvcha.2016.05.009 |

### Biodiversity and Ecosystem Services

| Reference | Role in model | DOI / URL |
|-----------|--------------|-----------|
| **IPBES Global Assessment (2022)** | Ecosystem service valuation; nature-related financial risk | https://doi.org/10.5281/zenodo.6417333 |
| **ENCORE v2024** | Sectoral ecosystem service dependency materiality (1–5 scale) | https://encore.naturalcapital.finance/ |
| **WWF Water Risk Framework 2.0** | WRF physical and BRF biodiversity risk scores | https://www.worldwildlife.org/pages/water-risk-filter |
| **GFN NFA 2023** | National Footprint and Biocapacity Accounts — `overshoot_results.csv` | https://data.footprintnetwork.org |

### Input-Output and Supply-Chain

| Reference | Role in model | DOI / URL |
|-----------|--------------|-----------|
| **EXIOBASE 3.8** | Multi-regional IO table; stressor intensities (GHG, water, employment) | https://doi.org/10.5281/zenodo.3583071 |
| **Stadler et al. (2018)** | EXIOBASE 3 methodology | https://doi.org/10.1111/jiec.12715 |
| **OSeMOSYS** | Open Source Energy Modelling System; SSP GHG adjustment factors | https://osemosys.org |
| **Dietrich et al. (2014)** | REMIND-MAgPIE coupled energy-land model; employment + water adjustment factors | https://doi.org/10.5194/gmd-7-1343-2014 |

### Financial Valuation and Disclosure

| Reference | Role in model | DOI / URL |
|-----------|--------------|-----------|
| **Nordhaus (2017) DICE** | GHG social cost (BASE): embedded in WifOR H5 `MonGHG_my.h5` | https://doi.org/10.1257/aer.20150649 |
| **Wetzer et al. (2024)** *Science* 383:152 | Three-channel ONPV risk model (physical, transition, legal) | https://doi.org/10.1126/science.adj6654 |
| **CBI Green Bond Principles (2023)** | SLB greenium 0–10 bp benchmark (δ_max = 0.001) | https://www.climatebonds.net/standard/sustainability-linked |
| **Shishlov, Morel & Cochran (2016)** I4CE, *Beyond Transparency* | No clear evidence that green bonds reduce the cost of capital | https://www.i4ce.org |
| **Löffler, Petreski & Stephan (2021)** | Average green-bond yield discount of 15–20 bps (global sample) | https://doi.org/10.1007/s40822-020-00165-y |
| **SFDR Annex I (2022)** | PAI mandatory indicator definitions (#1 GHG, #6 water, #7 biodiversity) | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R1288 |
| **TCFD Final Report (2017)** | Scenario analysis disclosure framework | https://assets.fsb.org/2017-06-29_tcfd_report.pdf |
| **TNFD v1.0 (2023)** | Nature-related financial disclosure; OCI > 0.1% flag | https://tnfd.global/publication/nature-related-risks-and-opportunities/ |

### EBRD Transition Quality

| Reference | Role in model | DOI / URL |
|-----------|--------------|-----------|
| **EBRD Transition Report 2024-25** | ATQ scores; 42 economies; 6 dimensions (1–10) | https://2024.tr-ebrd.com/structural-reform/ |
| **EBRD Methodological Notes 2024-25** | ATQ construction: min-max normalisation, frontier = advanced-economy best | https://www.ebrd.com/content/dam/ebrd_dxp/assets/pdfs/office-of-the-chief-economist/transition-report-archive/transition-report-2024/chapters/Transition-Report-2024-25-Methodological-Notes.pdf |
| **EBRD ATQ Overview** | Scoring scale (1=very weak, 10=frontier) | https://www.ebrd.com/economic-research-and-data/transition-qualities-asses.html |

### WifOR Value Factors

| Reference | Role in model | Contact |
|-----------|--------------|---------|
| **WifOR Institute H5 files (2024)** | `MonGHG_my.h5`, `MonWaterCon_my.h5`, `training_value_per_hour_bysector.h5` | https://wifor.com |
| **GVA/labour-hour methodology** | Gross Value Added per labour-hour as living-wage proxy; projected at FOCUS_YEAR via MonTrain growth index | Internal WifOR documentation |

### Data File Locations (this deployment)

| Dataset | Local path | Version / notes |
|---------|-----------|-----------------|
| IO table | `tvp_io_lib` (Python package) | EXIOBASE 3.8 — tiers 0–10 |
| WifOR value factors | `value-factors/*.h5` | 2024 release; ISO-3/NACE/year lookup |
| SSP adjustment factors | `tvp_scenario/osemosys/results/tvpdbio_intensity_factors.csv` | OSeMOSYS + REMIND-MAgPIE calibration |
| Nature dependency | `results/dependency_summary.csv` | ENCORE v2024 + WWF WRF 2.0 / BRF 1.0 |
| EarthOvershoot NFA | `indicators/earthovershoot/overshoot_results.csv` | GFN NFA 2023 edition |
| EBRD ATQ scores | `indicators/ebrd_atq_scores_2024_25.csv` | EBRD Transition Report 2024-25; 42 economies |
| Project inputs | `modeled_input_data/*.csv` | TVP portfolio — 9 modelled projects |
| Scenario adjustments | `results/scenario_adjustment.csv` | Calibrated per-project SSP ratios |

### Supply-Chain Analysis — Technical Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| IO database | EXIOBASE 3.8 | Stadler et al. (2018) |
| Supply-chain tiers | 0–10 (Leontief power series) | A-matrix spectral radius ≈ 0.52 |
| Tiers >8 share | < 0.1% of total stressor signal | Geometric convergence verified |
| Sector mapping | NACE F = Construction · H49 = Rail · Q = Health · D35 = Energy | NACE Rev.2 |
| Regional IO proxy | Europe = DEU · LATAM = BRA · Africa = NGA · Asia = IND | EXIOBASE country coverage |
| EUR/USD rate | 1.08 | Applied to Rail CAPEX inputs |
| FTE hours/year | 1,880 | ILO standard full-time equivalent |
| GHG aggregation | GWP100 AR6 | CO₂, CH₄, N₂O, F-gases |
"""

# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT APP
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TVP Integrated Assessment",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
_ss_defaults: dict = {
    "dark_mode": False,
    "active_role": ROLES[0],
    "canvas_country": "DE",
    "compare_countries": ["DE", "PL", "RO"],
    "portfolio_pids": [p["project_id"] for p in PROJECTS],
    "reg_juris": JURISDICTIONS[0],
}
for _k, _v in _ss_defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## TVP Integrated Assessment")
    st.caption(
        "WifOR · EXIOBASE · EBRD ATQ · GFN NFA  \n"
        "iNPV · S-IRR · ESG WACC · OCI · dep_factor"
    )
    st.divider()
    # ── View controls ─────────────────────────────────────────────────────────
    st.header("View")
    active_role = st.selectbox(
        "Role",
        options=ROLES,
        index=ROLES.index(st.session_state["active_role"]),
        key="active_role",
    )
    dark_mode = st.toggle("Dark mode", value=st.session_state["dark_mode"], key="dark_mode")
    plotly_template = "plotly_dark" if dark_mode else "plotly_white"

    # ── Role-specific sidebar panels ──────────────────────────────────────────
    st.divider()
    if active_role == "Strategy Economist":
        st.subheader("Country Canvas")
        canvas_country = st.selectbox(
            "Host country (ISO-2)",
            options=sorted(ATQ_ISO2_TO_NAME.keys()),
            index=sorted(ATQ_ISO2_TO_NAME.keys()).index(st.session_state["canvas_country"])
            if st.session_state["canvas_country"] in ATQ_ISO2_TO_NAME else 0,
            key="canvas_country",
        )
        st.caption("Add hypothetical projects in different sectors under this country:")
        _canvas_default = pd.DataFrame([
            {"sector": "Rail",   "capex_m": 140.0, "avoided_co2": 0},
            {"sector": "Energy", "capex_m": 500.0, "avoided_co2": 50000},
            {"sector": "Health", "capex_m": 100.0, "avoided_co2": 0},
        ])
        canvas_entries = st.data_editor(
            _canvas_default,
            column_config={
                "sector":      st.column_config.SelectboxColumn("Sector", options=ALL_SECTORS),
                "capex_m":     st.column_config.NumberColumn("CAPEX (USD M)", min_value=0.1),
                "avoided_co2": st.column_config.NumberColumn("Avoided CO₂/yr (tCO₂e)"),
            },
            num_rows="dynamic",
            key="canvas_entries",
            use_container_width=True,
        )
        st.session_state["canvas_entries_df"] = canvas_entries
    elif active_role == "Investment Officer":
        st.subheader("Country Comparison")
        st.caption("Fix sector + CAPEX; all ATQ countries are ranked automatically.")
        _io_sector_default = sector_sel if sector_sel in ALL_SECTORS else ALL_SECTORS[0]
        compare_sector = st.selectbox(
            "Sector (fixed)",
            options=ALL_SECTORS,
            index=ALL_SECTORS.index(_io_sector_default),
            key="compare_sector",
        )
        compare_capex_m = st.number_input(
            "CAPEX (USD M, fixed)",
            min_value=1.0, max_value=5000.0, value=100.0, step=10.0,
            key="compare_capex",
        )
        compare_countries = st.multiselect(
            "Highlight countries (ISO-2)",
            options=sorted(ATQ_ISO2_TO_NAME.keys()),
            default=[c for c in st.session_state["compare_countries"]
                     if c in ATQ_ISO2_TO_NAME],
            key="compare_countries",
        )
    elif active_role == "Portfolio Manager":
        st.subheader("Portfolio selection")
        portfolio_pids = st.multiselect(
            "Include projects",
            options=[p["project_id"] for p in PROJECTS],
            default=st.session_state["portfolio_pids"],
            key="portfolio_pids",
        )
    elif active_role == "Compliance Specialist":
        st.subheader("Jurisdiction")
        reg_juris = st.selectbox(
            "Regulatory framework",
            options=JURISDICTIONS,
            index=JURISDICTIONS.index(st.session_state["reg_juris"])
            if st.session_state["reg_juris"] in JURISDICTIONS else 0,
            key="reg_juris",
        )

    # ── Project selection ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Project")
    project_label = st.selectbox(
        "Project",
        options=[p["label"] for p in PROJECTS],
        index=0,
        key="project_label_select",
    )
    _base_proj = next(p for p in PROJECTS if p["label"] == project_label)
    _pid = _base_proj["project_id"]

    # ── Financial / scenario parameters ──────────────────────────────────────
    st.divider()
    st.subheader("Financial parameters")
    wacc_pct = st.slider(
        "WACC base (%)",
        min_value=1.0, max_value=20.0,
        value=round(_base_proj["wacc_base"] * 100, 1), step=0.1,
        key=f"wacc_{_pid}",
    )
    rev_yield_pct = st.slider(
        "Revenue yield (% of CAPEX/yr)",
        min_value=0.0, max_value=30.0,
        value=round(_base_proj["revenue_yield"] * 100, 1), step=0.5,
        key=f"rev_{_pid}",
    )
    opex_pct = st.slider(
        "OPEX ratio (% of CAPEX/yr)",
        min_value=0.0, max_value=20.0,
        value=round(_base_proj["opex_ratio"] * 100, 1), step=0.5,
        key=f"opex_{_pid}",
    )
    bond_yr = st.number_input(
        "Bond lifetime (years)",
        min_value=1, max_value=30,
        value=_base_proj["bond_years"],
        key=f"bond_{_pid}",
    )
    proj_yr = st.number_input(
        "Project lifetime (years)",
        min_value=5, max_value=50,
        value=_base_proj["project_years"],
        key=f"projyr_{_pid}",
    )
    focus_yr = st.number_input(
        "Focus year",
        min_value=2020, max_value=2050,
        value=2030,
        key="focus_year_global",
    )
    ssp_sel = st.selectbox(
        "Default SSP",
        options=ALL_SSPS,
        index=ALL_SSPS.index(_base_proj["scenario"]),
        key=f"ssp_{_pid}",
    )

    # ── Project composition ───────────────────────────────────────────────────
    st.divider()
    st.subheader("Project composition")

    _default_country = _base_proj["country"]
    _country_idx = (
        _ALL_COUNTRY_LIST.index(_default_country)
        if _default_country in _ALL_COUNTRY_LIST else 0
    )
    country_sel = st.selectbox(
        "Country (ISO-2)",
        options=_ALL_COUNTRY_LIST,
        index=_country_idx,
        key=f"country_{_pid}",
    )

    _default_sector = _base_proj["sector"]
    _sector_idx = (
        ALL_SECTORS.index(_default_sector)
        if _default_sector in ALL_SECTORS else 0
    )
    sector_sel = st.selectbox(
        "Sector",
        options=ALL_SECTORS,
        index=_sector_idx,
        key=f"sector_{_pid}",
    )

    capex_m = st.number_input(
        "CAPEX (USD millions)",
        min_value=0.001, max_value=10_000.0,
        value=round(_base_proj["capex_usd"] / 1e6, 3),
        step=0.1, format="%.3f",
        key=f"capex_{_pid}",
    )
    avoided_co2_input = st.number_input(
        "Avoided CO₂ (tCO₂e/yr)",
        min_value=0, max_value=50_000_000,
        value=int(_base_proj["avoided_co2"]),
        step=1_000,
        key=f"co2_{_pid}",
    )

    # ── Warnings ─────────────────────────────────────────────────────────────
    st.divider()
    if not IO_AVAILABLE:
        st.warning("tvp_io_lib not found — IO analysis unavailable.")
    if not ASSESS_AVAILABLE:
        st.warning("assess.py not found — WifOR value factors using fallback coefficients.")
    if not DEP_AVAILABLE:
        st.warning("dependency_profiler not found — dep factors set to neutral.")
    if int(bond_yr) > int(proj_yr):
        st.warning(
            f"Bond lifetime ({int(bond_yr)} yr) exceeds project lifetime ({int(proj_yr)} yr). "
            "The bond-period cumulative chart will be clipped to the project lifetime."
        )

# ── Page title ────────────────────────────────────────────────────────────────
st.title("TVP Integrated Assessment")
st.caption(
    f"Role: **{active_role}** · "
    "Integrated Net Present Value (iNPV) · Societal IRR (S-IRR) · ESG-adjusted WACC · "
    "EarthOvershoot OCI · EBRD ATQ — 9 modelled projects · "
    "Focus year: **" + str(int(focus_yr)) + "**"
)

# ── Derive region / ISO-3 from selected country ───────────────────────────────
_region_override = COUNTRY_REGION_MAP.get(country_sel, _base_proj["region"])
_iso3_override   = COUNTRY_ISO2_TO_ISO3.get(country_sel, REGION_TO_ISO3.get(_region_override, "DEU"))

proj = dict(
    _base_proj,
    country=country_sel,
    region=_region_override,
    sector=sector_sel,
    capex_usd=int(round(capex_m * 1e6)),
    avoided_co2=int(avoided_co2_input),
    wacc_base=wacc_pct / 100,
    revenue_yield=rev_yield_pct / 100,
    opex_ratio=opex_pct / 100,
    bond_years=int(bond_yr),
    project_years=int(proj_yr),
    scenario=ssp_sel,
)

region     = proj["region"]
sector     = proj["sector"]
iso3       = _iso3_override
nace       = PROJECT_SECTOR_TO_NACE.get(sector, "Q")
encore_sec = PROJECT_SECTOR_TO_ENCORE.get(sector, sector.lower())
dep_region = region.lower()

# ── Run computations ─────────────────────────────────────────────────────────
with st.spinner("Loading scenario factors and value factors…"):
    all_ssp_factors = _load_all_ssp_factors(region, focus_yr)
    vf              = _load_value_factors(iso3, nace, focus_yr)
    dep_ctx         = _compute_dep_context(encore_sec)

factors   = all_ssp_factors.get(ssp_sel)
sc_label  = f"{ssp_sel} {focus_yr}" if (ssp_sel and factors) else "Baseline"

if IO_AVAILABLE:
    io = _run_io(proj["capex_usd"], sector, region)
else:
    io = None

if io is None:
    st.error(
        "IO analysis is not available. "
        "Ensure tvp_io_lib is importable and run from the project_assessment/ directory."
    )
    st.info("Tip: `streamlit run integrated_finance/app.py` from `project_assessment/`")
    st.stop()

# ── Derived quantities ────────────────────────────────────────────────────────
tier_dep = _build_tier_dep(
    io, region,
    dep_ctx["encore_dep"], dep_ctx["wwf_by_region"],
)
summary, grand = _build_summary(io, factors, tier_dep)
mon            = _monetise(grand, proj, vf)
cf_df          = _build_cashflow_df(proj, mon)
metrics        = _compute_metrics(proj, mon, tier_dep, dep_ctx["wwf_by_region"])

raw_sums = {c: sum(summary[tk]["raw"][c] for tk in ["t0","t1","t2","t3"]) for c in COLS_SC}
ssp_results = {
    s: r for s in ALL_SSPS
    if (r := _compute_one_ssp(s, all_ssp_factors.get(s), raw_sums, proj, vf)) is not None
}

eo_single = _compute_overshoot_single(
    proj["country"], proj["capex_usd"],
    raw_sums.get("GHG_tCO2e", 0.0), 0.0,
)

# ── Header KPIs (role-adapted) ────────────────────────────────────────────────
if active_role == "Investment Officer":
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("CAPEX", fmt_capex(proj["capex_usd"]))
    c2.metric("NPV (base)", f"{metrics['npv_base']:+.1f} M")
    c3.metric("iNPV (base)", f"{metrics['inpv_base']:+.1f} M",
              delta=f"Δ {metrics['delta_npv']:+.1f} M")
    c4.metric("Financial IRR",
              f"{metrics['fin_irr']*100:.2f}%" if metrics["fin_irr"] else "N/A")
    c5.metric("S-IRR",
              f"{metrics['s_irr']*100:.2f}%" if metrics["s_irr"] else "N/A")

elif active_role == "Strategy Economist":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CAPEX", fmt_capex(proj["capex_usd"]))
    c2.metric("iNPV (base)", f"{metrics['inpv_base']:+.1f} M",
              delta=f"Δ {metrics['delta_npv']:+.1f} M")
    _atq_df = _load_atq_data()
    _atq_name = ATQ_ISO2_TO_NAME.get(proj["country"], "")
    _atq_avg = float(_atq_df.loc[_atq_name, "ATQ_Average"]) if (_atq_name and _atq_name in _atq_df.index) else None
    c3.metric("ATQ Score", f"{_atq_avg:.2f} / 10" if _atq_avg else "N/A")
    c4.metric("OCI (%)", f"{eo_single.get('oci_pct', 0.0):.1f}%")

elif active_role == "Portfolio Manager":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CAPEX", fmt_capex(proj["capex_usd"]))
    c2.metric("iNPV (base)", f"{metrics['inpv_base']:+.1f} M")
    c3.metric("WACC adj", f"{metrics['wacc_adj']*100:.3f}%",
              delta=f"−{metrics['sust_discount']*10000:.1f} bp")
    c4.metric("bc_deficit_mult", f"{eo_single.get('bc_deficit_mult', 1.0):.3f}×")

elif active_role == "Compliance Specialist":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CAPEX", fmt_capex(proj["capex_usd"]))
    c2.metric("iNPV (base)", f"{metrics['inpv_base']:+.1f} M")
    c3.metric("GHG supply-chain", f"{raw_sums.get('GHG_tCO2e', 0.0):,.0f} tCO₂e")
    c4.metric("OCI (%)", f"{eo_single.get('oci_pct', 0.0):.1f}%")

st.divider()

# ── Dynamic role-based tabs ───────────────────────────────────────────────────
_visible_labels = [ALL_TAB_LABELS[i] for i in ROLE_TABS[active_role]]
_visible_labels.append(ROLE_EXTRA_TAB[active_role])
_tabs = st.tabs(_visible_labels)
_role_tab = _tabs[-1]   # the role-specific extra tab

# ── Shared tab bodies ─────────────────────────────────────────────────────────
for _tpos, _tidx in enumerate(ROLE_TABS[active_role]):
    with _tabs[_tpos]:

        # ── Tab 0: Overview ───────────────────────────────────────────────────
        if _tidx == 0:
            _role_hints_0 = {
                "Investment Officer": (
                    "**Investment Officer view** — Verify that project parameters (CAPEX, sector, country) "
                    "match the term sheet before reviewing iNPV and S-IRR. WifOR value factors determine "
                    "how GHG, water, and employment externalities are priced into the integrated NPV."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — Country and sector selections drive the WifOR H5 "
                    "labour-productivity coefficients and the SSP adjustment factors applied in all "
                    "scenario analyses. The EarthOvershoot block below contextualises the host country's "
                    "biocapacity relative to the project's footprint."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — The `bc_deficit_mult` (EarthOvershoot) scales the "
                    "nature-dependency factor upward for countries in ecological overshoot, increasing "
                    "the ESG WACC greenium. OCI > 100% flags a project that exceeds the host country's "
                    "full biocapacity in carbon + land EF terms."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — These parameters feed directly into your disclosure "
                    "templates. CAPEX and NACE code determine sectoral intensity benchmarks; GHG (tCO₂e) "
                    "and water coefficients are used in SFDR PAI and TCFD reporting calculations."
                ),
            }
            st.info(_role_hints_0[active_role])
            st.subheader(f"Project: {proj['project_id']}")
            oc1, oc2 = st.columns(2)
            with oc1:
                st.markdown(f"""
| Parameter | Value |
|-----------|-------|
| **Sector** | {proj['sector']} |
| **Region** | {proj['region']} |
| **Country (ISO-2)** | {proj['country']} |
| **CAPEX** | {fmt_capex(proj['capex_usd'])} |
| **Avoided CO₂** | {proj['avoided_co2']:,} tCO₂e/yr |
| **Bond lifetime** | {proj['bond_years']} years |
| **Project lifetime** | {proj['project_years']} years |
| **WACC base** | {proj['wacc_base']*100:.2f}% |
| **Revenue yield** | {proj['revenue_yield']*100:.1f}% of CAPEX/yr |
| **OPEX ratio** | {proj['opex_ratio']*100:.1f}% of CAPEX/yr |
| **Default scenario** | {proj['scenario']} |
| **Focus year** | {focus_yr} |
| **WifOR ISO3/NACE** | {iso3} / {nace} |
""")
            with oc2:
                if vf.get("fallback"):
                    st.warning("WifOR H5 directory not found — using fallback coefficients.")
                c_ghg   = vf["c_ghg"] or 0.0
                c_ghg_p = vf.get("c_ghg_paris") or 0.0
                c_water = vf["c_water"] or 0.0
                c_gva   = vf["c_gva"]
                st.markdown("**WifOR Value Factors**")
                st.caption(
                    "Source: WifOR Institute H5 database, look-up by ISO-3 country code "
                    f"({iso3}) and NACE sector ({nace}). GHG coefficients: Nordhaus DICE "
                    "social cost of carbon (base) and IPCC SR1.5 Paris-aligned pathway. "
                    "Water: blue water consumption shadow price. GVA/h: gross value added "
                    "per labour-hour, used as employment monetisation proxy. "
                    "Fallback coefficients apply if H5 file is unavailable."
                )
                st.dataframe(pd.DataFrame({
                    "Factor":      ["GHG BASE (Nordhaus DICE)", "GHG PARIS-aligned",
                                    "Water (Blue Consumption)", "GVA / labour-hour"],
                    "Coefficient": [f"{c_ghg:.6f} USD/kg",  f"{c_ghg_p:.6f} USD/kg",
                                    f"{c_water:.6f} USD/m³", f"{c_gva:.4f} USD/h"],
                    "Per-unit":    [f"${abs(c_ghg)*1000:.2f}/tCO₂e",
                                    f"${abs(c_ghg_p)*1000:.2f}/tCO₂e",
                                    f"${abs(c_water):.4f}/m³",
                                    f"${c_gva:.2f}/FTE-hr"],
                }), hide_index=True, use_container_width=True)

            st.markdown("**SSP Adjustment Factors** (calibrated from `results/scenario_adjustment.csv`)")
            try:
                sa_path = PA_DIR / "results" / "scenario_adjustment.csv"
                sa = pd.read_csv(sa_path)
                sa_proj = sa[
                    (sa["project_id"] == proj["project_id"]) & (sa["year"] == focus_yr)
                ][["scenario","adj_ratio_ghg","adj_ratio_employment","adj_ratio_water"]].copy()
                sa_proj.columns = ["SSP","adj_ghg","adj_employment","adj_water"]
                if not sa_proj.empty:
                    st.dataframe(sa_proj.reset_index(drop=True), hide_index=True,
                                 use_container_width=True)
                else:
                    st.info(f"No scenario adjustment rows found for {proj['project_id']} @ {focus_yr}.")
            except FileNotFoundError:
                st.info("results/scenario_adjustment.csv not found.")

            st.markdown("**Nature-Dependency Scores** (from `results/dependency_summary.csv`)")
            try:
                ds_path = PA_DIR / "results" / "dependency_summary.csv"
                ds = pd.read_csv(ds_path)
                ds_proj = ds[ds["project_id"] == proj["project_id"]]
                if ds_proj.empty:
                    st.info(f"No dependency rows for {proj['project_id']}.")
                else:
                    cols_show = ["project_id","wrf_physical","wrf_composite","brf_composite",
                                 "overall_high_risk","revenue_at_risk_usd_m","top_dependency"]
                    cols_show = [c for c in cols_show if c in ds_proj.columns]
                    st.dataframe(ds_proj[cols_show], hide_index=True, use_container_width=True)
            except FileNotFoundError:
                st.info("results/dependency_summary.csv not found.")

            st.markdown("**EarthOvershoot Context**")
            st.caption(
                "Source: Global Footprint Network — National Footprint and Biocapacity Accounts "
                "(NFA 2023 edition), `indicators/earthovershoot/overshoot_results.csv`. "
                "EF carbon = supply-chain GHG × (1−0.35)/2.677 × 1.3 (sequestration factor, "
                "net-of-ocean-uptake, EQF 1.3). OCI = (EF_carbon + EF_land) / BC_total × 100. "
                "bc_deficit_mult = 1.0 if surplus, else min(1.5, 1 + |deficit|/BC_total). "
                "Country not in NFA coverage → bc_deficit_mult defaults to 1.0."
            )
            eo_rows = [
                ("EF carbon (gha)",        f"{eo_single.get('ef_carbon_gha', 0.0):.4f}"),
                ("EF land (gha)",          f"{eo_single.get('ef_land_gha', 0.0):.4f}"),
                ("OCI (%)",                f"{eo_single.get('oci_pct', 0.0):.2f}%"),
                ("bc_deficit_mult",        f"{eo_single.get('bc_deficit_mult', 1.0):.4f}×"),
                ("EF/capita host (gha)",   f"{eo_single.get('ef_per_capita_host', 0.0):.3f}"),
                ("BC/capita host (gha)",   f"{eo_single.get('bc_per_capita_host', 0.0):.3f}"),
            ]
            st.dataframe(pd.DataFrame(eo_rows, columns=["Metric","Value"]),
                         hide_index=True, use_container_width=True)

            st.divider()
            st.markdown(f"**EBRD ATQ Transition Quality — {ATQ_ISO2_TO_NAME.get(proj['country'], proj['country'])} ({proj['country']})**")
            st.caption(
                "Source: EBRD Transition Report 2024-25 · `indicators/ebrd_atq_scores_2024_25.csv`. "
                "Six dimensions scored 1–10 vs frontier (best-practice advanced economies = 10). "
                "ATQ Average is the weighted composite. Green dimension ↔ OCI/EarthOvershoot; "
                "Resilient dimension ↔ bc_deficit_mult (overshoot penalty on dep_factor)."
            )
            _atq_df_ov = _load_atq_data()
            _atq_cn_ov = ATQ_ISO2_TO_NAME.get(proj["country"], "")
            _atq0_col, _atq0_radar = st.columns([1, 1])
            with _atq0_col:
                if _atq_cn_ov and _atq_cn_ov in _atq_df_ov.index:
                    _atq_row_ov = _atq_df_ov.loc[_atq_cn_ov]
                    _atq_interp = {
                        "Competitive":   "Market openness, SME, innovation",
                        "Well_Governed": "Rule of law, anti-corruption",
                        "Green":         "GHG mitigation, renewables — links to OCI",
                        "Inclusive":     "Labour participation, gender equity",
                        "Resilient":     "Financial stability — links to bc_deficit_mult",
                        "Integrated":    "Trade, FDI, transport & digital",
                    }
                    _atq_rows_ov = [
                        (lbl, f"{float(_atq_row_ov[d]):.2f} / 10",
                         "★★★" if float(_atq_row_ov[d]) >= 7 else
                         "★★☆" if float(_atq_row_ov[d]) >= 5 else "★☆☆",
                         _atq_interp.get(d, ""))
                        for d, lbl in zip(ATQ_DIMENSIONS, ATQ_DIM_LABELS[:-1])
                    ]
                    _atq_rows_ov.append(
                        ("Average", f"{float(_atq_row_ov['ATQ_Average']):.2f} / 10",
                         "★★★" if float(_atq_row_ov['ATQ_Average']) >= 7 else
                         "★★☆" if float(_atq_row_ov['ATQ_Average']) >= 5 else "★☆☆",
                         "Weighted composite")
                    )
                    st.dataframe(
                        pd.DataFrame(_atq_rows_ov, columns=["Dimension","Score","Tier","What it measures"]),
                        hide_index=True, use_container_width=True,
                    )
                else:
                    st.info(f"No ATQ data for {proj['country']} — country outside EBRD coverage.")
            with _atq0_radar:
                st.plotly_chart(
                    _fig_atq_radar(
                        proj["country"], plotly_template,
                        title=f"ATQ — {_atq_cn_ov or proj['country']} vs Frontier · {int(focus_yr)}",
                    ),
                    use_container_width=True,
                )

        # ── Tab 1: IO Supply Chain ─────────────────────────────────────────────
        elif _tidx == 1:
            st.info(
                "**Investment Officer view — Supply-Chain Scope** — "
                "Tiers 0–10 capture the full Leontief upstream chain triggered by CAPEX spending. "
                "Tier 0 is the direct construction spend; Tier 1 includes bilateral sourcing-country "
                "procurement (e.g., steel from Germany for a Romanian rail project). "
                "The 'adj' columns apply SSP-scenario intensity factors to the raw EXIOBASE stressor "
                "intensities, showing how decarbonisation trajectories change the GHG and water "
                "footprint of the same physical spend. "
                "High Tier-1 GHG relative to Tier-0 signals significant import-leakage risk."
            )
            st.caption(
                "Source: EXIOBASE 3.8 multi-regional input–output database (Eurostat/OECD). "
                "IO model run via `tvp_io_lib` using CAPEX split across 8 construction sub-sectors "
                "(NACE F, H49, D35, Q). Spectral radius of A-matrix ≈ 0.52 — tiers >8 contribute "
                "<0.1% of signal. SSP adjustment factors from `tvpdbio_intensity_factors.csv` "
                "(OSeMOSYS + REMIND-MAgPIE grid-intensity trajectories)."
            )
            st.subheader("Supply-Chain IO Analysis (Leontief Tiers 0–10)")
            tier_defs = [("t0","Tier 0  Direct"), ("t1","Tier 1  Bilateral"),
                         ("t2","Tier 2  Upstream"), ("t3","Tier 3-10  Deep Chain")]

            rows_summary = []
            for tk, lbl in tier_defs:
                row = {"Tier": lbl}
                for c in COLS_SC:
                    row[f"{c} (raw)"] = f"{summary[tk]['raw'][c]:,.0f}"
                    row[f"{c} (adj)"] = f"{summary[tk]['adj'][c]:,.0f}"
                rows_summary.append(row)
            grand_row = {"Tier": "GRAND TOTAL"}
            for c in COLS_SC:
                grand_row[f"{c} (raw)"] = f"{grand['raw'][c]:,.0f}"
                grand_row[f"{c} (adj)"] = f"{grand['adj'][c]:,.0f}"
            rows_summary.append(grand_row)

            st.dataframe(pd.DataFrame(rows_summary), hide_index=True, use_container_width=True)
            st.caption(f"Scenario: {sc_label} · Focus year: {focus_yr}")

            with st.expander("Tier 0 detail"):
                st.dataframe(io["t0"].head(30), use_container_width=True)
            with st.expander("Tier 1 detail"):
                st.dataframe(io["t1"].head(30), use_container_width=True)

        # ── Tab 2: NPV / iNPV ─────────────────────────────────────────────────
        elif _tidx == 2:
            _role_hints_2 = {
                "Investment Officer": (
                    "**Investment Officer view** — iNPV > NPV indicates that the project creates "
                    "**additional societal value** beyond what the bank's financial model captures. "
                    "This gap (SVA = iNPV − NPV) is the quantitative case for concessional co-financing "
                    "or blended finance: society's share of the return justifies a public subsidy up to "
                    "the SVA amount. A negative iNPV even when NPV > 0 signals that externalities "
                    "destroy more value than the project earns financially."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — The iNPV spread across SSPs (see SSP Comparison tab) "
                    "reveals which transmission channel dominates country-sector pairs. "
                    "Employment monetisation via GVA/labour-hour (WifOR H5) typically dominates in "
                    "high-income OECD countries; GHG cost dominates where the grid is carbon-intensive "
                    "and employment coefficients are low."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — NPV measures bank return; iNPV measures total "
                    "stakeholder return. The delta is your additionality argument to DFI co-investors. "
                    "Compare iNPV/CAPEX ratios across projects in the Portfolio tab to allocate "
                    "concessional capital where the societal multiplier is highest."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — iNPV is the primary output metric for EBRD ATQ "
                    "and AIIB EP additionality assessments. A negative delta (NPV > iNPV) must be "
                    "disclosed as a material negative externality under SFDR Article 8/9 and TNFD."
                ),
            }
            st.info(_role_hints_2[active_role])
            st.caption(
                "Method: iNPV = NPV + PV(nature dividend stream over project lifetime). "
                "Nature dividend = annual employment benefit − annual GHG cost − annual water cost "
                "(all monetised via WifOR value factors). Discounted at WACC_adj. "
                "WifOR value factors: H5 database look-up by ISO-3 / NACE (see Overview tab). "
                "Fallback: fixed coefficients if H5 unavailable."
            )
            st.subheader("Integrated NPV (iNPV) vs Standard NPV")
            st.plotly_chart(_fig_npv(proj, metrics, sc_label), use_container_width=True)

            col_l, col_r = st.columns(2)
            col_l.metric("Standard NPV (WACC base)", f"{metrics['npv_base']:+.2f} M USD")
            col_r.metric("Integrated iNPV (WACC base)", f"{metrics['inpv_base']:+.2f} M USD",
                         delta=f"Δ = {metrics['delta_npv']:+.2f} M USD")

            if metrics["inpv_base"] >= metrics["npv_base"]:
                st.success("iNPV > NPV — project creates **more value for society** than for the bank.")
            else:
                st.warning("iNPV < NPV — societal externalities reduce net project value.")
            if metrics["inpv_base"] < 0:
                st.error("⚠ iNPV < 0 — project is value-destructive to society even if financially profitable.")

        # ── Tab 3: S-IRR ──────────────────────────────────────────────────────
        elif _tidx == 3:
            _role_hints_3 = {
                "Investment Officer": (
                    "**Investment Officer view** — S-IRR is the discount rate that sets iNPV = 0. "
                    "S-IRR > Financial IRR means the project's societal return exceeds its financial "
                    "hurdle rate — the strongest possible signal for blended/public finance engagement. "
                    "Note: for projects with deeply negative annual dividends (e.g., Hydro_AS), "
                    "S-IRR has an inverted interpretation — it is the rate at which the negative "
                    "externality stream is discounted to zero, not a positive signal."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — S-IRR is driven by the sign and magnitude of the "
                    "annual nature dividend. Large positive employment benefits relative to GHG costs "
                    "produce high S-IRR (Rail EU, Health LATAM). Large negative water costs in "
                    "water-scarce countries suppress or reverse S-IRR (Hydro Asia/Africa)."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — S-IRR > Financial IRR across the portfolio indicates "
                    "that societal returns systematically exceed bank returns — the portfolio's "
                    "concessional finance case in DFI co-investment discussions."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — S-IRR anchors the EBRD ATQ additionality "
                    "assessment and the AIIB Environmental and Social Framework (ESF) benefit-cost "
                    "analysis. Where S-IRR is unavailable (IRR solver non-convergence), disclose "
                    "iNPV/CAPEX ratio as the fallback additionality metric."
                ),
            }
            st.info(_role_hints_3[active_role])
            st.caption(
                "Method: S-IRR is the internal rate of return on the stream "
                "[−CAPEX, annual_dividend, …, annual_dividend] over project lifetime. "
                "Annual dividend = employment benefit − GHG cost − water cost (WifOR-monetised, "
                "SSP-adjusted). Solver: `numpy.irr` / `scipy.optimize.brentq`. "
                "Non-convergence → N/A (occurs when dividend stream has no sign change)."
            )
            st.subheader("Societal IRR (S-IRR)")
            st.plotly_chart(_fig_sirr(proj, metrics, mon), use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Financial IRR",
                        f"{metrics['fin_irr']*100:.2f}%" if metrics["fin_irr"] else "N/A")
            col2.metric("WACC base", f"{proj['wacc_base']*100:.2f}%")
            col3.metric("Societal S-IRR",
                        f"{metrics['s_irr']*100:.2f}%" if metrics["s_irr"] else "N/A")

            if metrics["s_irr"] and metrics["fin_irr"]:
                if metrics["s_irr"] > metrics["fin_irr"]:
                    st.success("S-IRR > Financial IRR — strong societal case; supports blended/public finance.")
                else:
                    st.info("S-IRR ≤ Financial IRR — societal externalities partly offset financial returns.")

        # ── Tab 4: WACC Adjustment ────────────────────────────────────────────
        elif _tidx == 4:
            _role_hints_4 = {
                "Investment Officer": (
                    "**Investment Officer view** — The ESG greenium (sustainability discount) reduces "
                    "WACC, improving NPV and iNPV. It is earned through two channels: "
                    "(1) low WWF water-risk score → water discount; "
                    "(2) low ENCORE nature-dependency factor → dep resilience discount. "
                    "Projects in high-dependency sectors (e.g., hydro in water-scarce regions) earn "
                    "a **smaller** greenium because risk is higher, not lower. "
                    "The adjusted WACC is then used to discount all future cash flows."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — The dep_factor integrates three evidence streams: "
                    "ENCORE ecosystem service materiality, WWF Water Risk Framework physical scores, "
                    "and supply-chain sector sensitivity. A bc_deficit_mult > 1 (ecological overshoot) "
                    "from EarthOvershoot scales dep_factor upward, reducing the greenium for countries "
                    "already in biocapacity deficit."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — WACC_adj feeds directly into NPV and iNPV. "
                    "A 50 bp ESG discount on a 1,998 M CAPEX project changes NPV by ~30 M over a "
                    "20-year bond. Aggregate the WACC_adj distribution across the portfolio "
                    "in the Risk Dashboard to quantify the portfolio-level greenium."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — The sustainability discount components (water, dep) "
                    "must be disclosed under SFDR Article 8/9 as quantified ESG integration evidence. "
                    "The dep_factor methodology uses ENCORE v2024 and WWF WRF 2.0 — cite these in "
                    "TNFD LEAP-aligned reporting."
                ),
            }
            st.info(_role_hints_4[active_role])
            st.caption(
                "Source: WACC_adj = WACC_base − sust_discount. "
                "sust_discount = water_discount + dep_discount. "
                "water_discount = WWF WRF physical score × 0.002 (scale factor). "
                "dep_discount = mean(dep_factor) × 0.005. "
                "dep_factor = geometric mean of ENCORE materiality score (source: ENCORE v2024, "
                "`results/dependency_summary.csv`), WWF WRF composite score (WWF Water Risk "
                "Framework 2.0 / BRF 1.0), and supply-chain sector sensitivity index. "
                "Fallback dep_factor = 1.0 (neutral) when `dependency_profiler` is unavailable."
            )
            st.subheader("WACC Adjustment via Nature Dependency (ESG Alpha)")
            st.plotly_chart(_fig_wacc(proj, metrics), use_container_width=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("WWF Water Risk", f"{metrics['wwf_water']:.3f} / 5.0")
            c2.metric("Mean Dep Factor", f"{metrics['mean_dep']:.3f}")
            c3.metric("Sustainability Discount", f"{metrics['sust_discount']*10000:.2f} bp")
            c4.metric("WACC adj", f"{metrics['wacc_adj']*100:.3f}%",
                      delta=f"−{metrics['sust_discount']*10000:.1f} bp")

            st.markdown(f"""
| Metric | Value |
|--------|-------|
| WACC base | {proj['wacc_base']*100:.3f}% |
| Water discount component | {metrics['water_discount']*10000:.2f} bp |
| Dep resilience discount | {metrics['dep_discount']*10000:.2f} bp |
| Total sustainability discount | {metrics['sust_discount']*10000:.2f} bp |
| WACC adjusted | {metrics['wacc_adj']*100:.3f}% |
| NPV @ WACC_adj | {metrics['npv_adj']:+.2f} M USD |
| iNPV @ WACC_adj | {metrics['inpv_adj']:+.2f} M USD |
""")

        # ── Tab 5: Cash Flow Dashboard ────────────────────────────────────────
        elif _tidx == 5:
            _role_hints_5 = {
                "Investment Officer": (
                    "**Investment Officer view** — The combined cash flow table shows financial (NPV) "
                    "and societal (iNPV) streams on the same timeline. Bond-period rows are the "
                    "investor's direct horizon; project-lifetime rows capture the full societal tail. "
                    "Negative financial CF in early years is normal for revenue-yield projects; "
                    "the positive societal dividend offsets this in iNPV."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — Cash flow timing reveals when societal returns "
                    "materialise relative to financial breakeven. For employment-heavy sectors, "
                    "the annual dividend is front-loaded (construction phase); for avoided-GHG "
                    "projects it is operational-phase-weighted."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — Compare the cumulative iNPV curve vs the bond "
                    "redemption profile. Projects where cumulative iNPV turns positive before bond "
                    "maturity have the strongest refinancing case for green bonds."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — The annual dividend breakdown (GHG cost, water "
                    "cost, employment benefit) provides the line-item data required for SFDR PAI "
                    "tables 1 and 2, and for TCFD physical risk quantification."
                ),
            }
            st.info(_role_hints_5[active_role])
            st.caption(
                "Cash flow model: Year 0 = −CAPEX (construction). Years 1–bond: "
                "revenue (CAPEX × revenue_yield) − OPEX (CAPEX × opex_ratio) − debt service. "
                "Years bond+1–project: revenue − OPEX. iNPV CF adds annual nature dividend "
                "(employment benefit − GHG cost − water cost, WifOR-monetised, SSP-adjusted). "
                "All discounted at WACC_adj. Bond redemption at par assumed."
            )
            st.subheader("Combined Cash Flow Dashboard")
            st.plotly_chart(_fig_cashflow(proj, cf_df, metrics, sc_label), use_container_width=True)

            sample = [0] + list(range(1, min(6, proj["project_years"]+1))) + \
                     [proj["bond_years"], proj["project_years"]]
            sample = sorted(set(sample))
            st.markdown("**Representative rows from the combined cash flow table**")
            st.dataframe(cf_df[cf_df["Year"].isin(sample)].set_index("Year").style
                .format("{:+.3f}").map(
                    lambda v: ("color:green" if isinstance(v, float) and v > 0 else
                               "color:red"   if isinstance(v, float) and v < 0 else "")
                ), use_container_width=True)

            st.markdown("**Static 4-panel dashboard**")
            fig_d = _fig_dashboard(proj, mon, metrics, sc_label, dark_mode=dark_mode)
            st.pyplot(fig_d, use_container_width=True)
            plt.close(fig_d)

        # ── Tab 6: SSP Comparison ─────────────────────────────────────────────
        elif _tidx == 6:
            _role_hints_6 = {
                "Investment Officer": (
                    "**Investment Officer view** — Financial NPV is identical across all SSPs "
                    "(the market does not price climate scenarios). The iNPV spread is your "
                    "climate-risk-adjusted return range. The scenario with the worst iNPV defines "
                    "the downside; a lender should stress-test against it before committing."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — SSP channel dominance varies by sector and region. "
                    "European rail and health projects are employment-dominated (SSP1 best, SSP5 worst). "
                    "Asian hydro is water-energy-nexus dominated (SSP5 worst due to high adj_water). "
                    "Use this tab to identify which SSP is the binding constraint for each project."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — Scenario spread (best − worst iNPV) is the portfolio's "
                    "climate value-at-risk. Aggregate across the portfolio in the Risk Dashboard. "
                    "SSP4-6.0 ranks near SSP1-1.9 for most projects — its policy structure keeps "
                    "grid intensity low despite higher warming."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — Multi-scenario analysis is required under TCFD "
                    "scenario analysis disclosure. SSP1-1.9 / SSP2-4.5 / SSP5-8.5 span the IPCC "
                    "representative pathways. Document the scenario spread as climate financial risk "
                    "in your SFDR Article 8/9 pre-contractual disclosures."
                ),
            }
            st.info(_role_hints_6[active_role])
            st.caption(
                "SSP adjustment factors source: `tvpdbio_intensity_factors.csv` "
                "(OSeMOSYS energy model + REMIND-MAgPIE land-use model). "
                "Three transmission channels per SSP: "
                "(1) adj_ratio_ghg — grid decarbonisation trajectory (GHG intensity of electricity); "
                "(2) adj_ratio_employment — labour-market structural change; "
                "(3) adj_ratio_water — water-energy nexus (renewable share × 0.85 reduction factor). "
                "Hardcoded fallback: factors = 1.0 if CSV not found for the project's region."
            )
            st.subheader("Multi-Scenario IPCC Comparison")

            if not ssp_results:
                st.warning("No SSP scenario data available for this region — check intensity CSV.")
            else:
                st.plotly_chart(_fig_ssp_comparison(proj, ssp_results), use_container_width=True)

                rows_ssp = []
                ref_npv = list(ssp_results.values())[0]["npv"]
                for s, r in ssp_results.items():
                    rows_ssp.append({
                        "SSP":           s,
                        "adj_ghg":       f"{r['factor_ghg']:.3f}",
                        "adj_emp":       f"{r['factor_emp']:.3f}",
                        "adj_wat":       f"{r['factor_wat']:.3f}",
                        "Nature Debt M": f"{r['nature_debt']:+.2f}",
                        "Ann. Div. M":   f"{r['annual_dividend']:+.3f}",
                        "NPV M":         f"{r['npv']:+.2f}",
                        "iNPV M":        f"{r['inpv']:+.2f}",
                        "Δ(iNPV−NPV)":   f"{r['inpv']-r['npv']:+.2f}",
                        "Fin IRR":       f"{r['fin_irr']*100:.2f}%" if r["fin_irr"] else "N/A",
                        "S-IRR":         f"{r['s_irr']*100:.2f}%"  if r["s_irr"]   else "N/A",
                    })
                st.dataframe(pd.DataFrame(rows_ssp), hide_index=True, use_container_width=True)

                best  = max(ssp_results.values(), key=lambda r: r["inpv"])
                worst = min(ssp_results.values(), key=lambda r: r["inpv"])
                spread = best["inpv"] - worst["inpv"]
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Best iNPV",  f"{best['inpv']:+.2f} M USD",  delta=best["ssp"])
                sc2.metric("Worst iNPV", f"{worst['inpv']:+.2f} M USD", delta=worst["ssp"])
                sc3.metric("Scenario risk (spread)", f"{spread:.2f} M USD")

                st.info(
                    f"Financial NPV is identical across all scenarios ({ref_npv:+.2f} M USD). "
                    "The entire iNPV spread is driven by the three SSP transmission channels."
                )

                st.markdown("**IPCC SSP Pathway Schematic**")
                fig_sch = _fig_pathway_schematic(proj, ssp_results, dark_mode=dark_mode)
                st.pyplot(fig_sch, use_container_width=True)
                plt.close(fig_sch)

        # ── Tab 7: Project Profile ────────────────────────────────────────────
        elif _tidx == 7:
            _role_hints_7 = {
                "Investment Officer": (
                    "**Investment Officer view** — The project narrative explains the sector-specific "
                    "methodology (why this NACE code, what the IO supply-chain proxy covers, how "
                    "avoided CO₂ is estimated). The live metrics recap at the bottom shows the exact "
                    "values computed from your current sidebar parameters — use this as a sanity check "
                    "before presenting to investment committee."
                ),
                "Strategy Economist": (
                    "**Strategy Economist view** — SSP scenario ordering notes explain which "
                    "transmission channel dominates for this country-sector pair, and why some SSPs "
                    "produce counter-intuitive rankings. The sector methodology section covers the "
                    "EXIOBASE sector mapping and any proxy assumptions applied."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — OCI and bc_deficit_mult in the live recap table "
                    "show the project's biocapacity pressure on the host country. These feed into "
                    "the nature-adjusted dep_factor used in WACC greenium calculations across the "
                    "portfolio risk dashboard."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — The live metrics table provides the disclosure "
                    "inputs: iNPV, S-IRR, WACC_adj, GHG totals, water coefficients, and OCI. "
                    "Cross-reference the 'Active SSP' with the scenario used in your TCFD disclosures. "
                    "WifOR value factors and their source H5 file are documented in the Overview tab."
                ),
            }
            st.info(_role_hints_7[active_role])
            _pid_sel = proj["project_id"]
            _profile = PROJECT_PROFILES.get(_pid_sel)

            st.subheader(f"Project Profile — {_pid_sel}")

            if _profile:
                st.info(_profile["overview"])

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    with st.expander("Sector-specific methodology link", expanded=True):
                        st.markdown(_profile["sector_link"])
                with col_p2:
                    with st.expander("Key findings & investment interpretation", expanded=True):
                        st.markdown(_profile["key_finding"])

                with st.expander("SSP scenario ordering & channel interpretation", expanded=True):
                    st.markdown(_profile["ssp_note"])
            else:
                st.info(f"Narrative profile not yet available for {_pid_sel}.")

            st.divider()
            st.markdown("#### Sector Methodology Assumptions")
            st.markdown(SECTOR_ASSUMPTIONS_MD)

            st.divider()
            st.markdown("#### Live Computation Results for Selected Parameters")
            m = metrics
            recap_rows = [
                ("CAPEX",                  fmt_capex(proj["capex_usd"])),
                ("Standard NPV",           f"{m['npv_base']:+.2f} M USD"),
                ("Integrated iNPV",        f"{m['inpv_base']:+.2f} M USD"),
                ("Societal Value Added",   f"{m['inpv_base'] - m['npv_base']:+.2f} M USD"),
                ("SVA / CAPEX",            f"{(m['inpv_base'] - m['npv_base']) / proj['capex_usd'] * 1e6:.2f}×"),
                ("Financial IRR",          f"{m['fin_irr']*100:.2f}%" if m['fin_irr'] else "N/A"),
                ("Societal S-IRR",         f"{m['s_irr']*100:.2f}%"  if m['s_irr']   else "N/A"),
                ("WACC base",              f"{proj['wacc_base']*100:.3f}%"),
                ("WACC adj (ESG)",         f"{m['wacc_adj']*100:.3f}%"),
                ("ESG discount",           f"−{m['sust_discount']*10000:.2f} bp"),
                ("WRF physical",           f"{m['wwf_water']:.3f} / 5.0"),
                ("Mean dep_factor",        f"{m['mean_dep']:.3f}"),
                ("Nature Debt (t=0)",      f"{mon.get('nature_debt', 0.0):+.3f} M USD"),
                ("Annual Nature Dividend", f"{mon.get('annual_dividend', 0.0):+.3f} M USD/yr"),
                ("Bond lifetime (eff.)",   f"{m.get('bond_eff', proj['bond_years'])} yr"),
                ("WifOR ISO3/NACE",        f"{iso3} / {nace}"),
                ("Focus year",             str(int(focus_yr))),
                ("Active SSP",             ssp_sel),
                ("OCI (%)",                f"{eo_single.get('oci_pct', 0.0):.2f}%"),
                ("bc_deficit_mult",        f"{eo_single.get('bc_deficit_mult', 1.0):.4f}×"),
            ]
            # Append ATQ scores for the project's host country
            _atq_df_7 = _load_atq_data()
            _atq_cn_7 = ATQ_ISO2_TO_NAME.get(proj["country"], "")
            if _atq_cn_7 and _atq_cn_7 in _atq_df_7.index:
                _atq_r7 = _atq_df_7.loc[_atq_cn_7]
                recap_rows += [
                    ("─── ATQ (" + _atq_cn_7 + ") ───", "EBRD 2024-25"),
                    ("ATQ Average",          f"{float(_atq_r7['ATQ_Average']):.2f} / 10"),
                    ("ATQ Competitive",      f"{float(_atq_r7['Competitive']):.2f} / 10"),
                    ("ATQ Well Governed",    f"{float(_atq_r7['Well_Governed']):.2f} / 10"),
                    ("ATQ Green",            f"{float(_atq_r7['Green']):.2f} / 10  ← OCI link"),
                    ("ATQ Inclusive",        f"{float(_atq_r7['Inclusive']):.2f} / 10"),
                    ("ATQ Resilient",        f"{float(_atq_r7['Resilient']):.2f} / 10  ← bc_deficit link"),
                    ("ATQ Integrated",       f"{float(_atq_r7['Integrated']):.2f} / 10"),
                ]
            st.dataframe(
                pd.DataFrame(recap_rows, columns=["Metric", "Value"]),
                hide_index=True, use_container_width=True,
            )

        # ── Tab 8: Methodology ────────────────────────────────────────────────
        elif _tidx == 8:
            st.subheader("TVP Integrated Assessment — Methodology & Documentation")
            st.caption(
                "TVP Integrated Assessment · WifOR Institute · EXIOBASE 3.8 · EBRD ATQ 2024-25 · GFN NFA 2023  \n"
                "Drawn from: integrated_finance_assessment.md · onpv_formula_corrected.md · "
                "final_analysis.md · modeled_input_data/assumptions.txt"
            )

            with st.expander("Index of Abbreviations — all terms used in this tool", expanded=False):
                st.markdown(ABBREVIATIONS_MD)

            with st.expander("Financial & Impact Figures — Plain-Language Guide", expanded=True):
                st.markdown(FINANCIAL_FIGURES_MD)

            with st.expander("Conceptual Framework — CFA / IPBES / IPCC alignment"):
                st.markdown(CONCEPTUAL_FRAMEWORK_MD)

            with st.expander("Integrated Finance Model — iNPV formula · S-IRR · ESG WACC · SSP channels"):
                st.markdown(METHODOLOGY_INTEGRATED_FINANCE_MD)

            with st.expander("WifOR Value Factors — H5 Coefficients & GVA/Labour-Hour Table"):
                st.markdown(WIFOR_VF_MD)

            with st.expander("Nature Dependency Scoring — ENCORE · WWF WRF/BRF · dep_factor"):
                st.markdown(NATURE_DEP_MD)

            with st.expander("ONPV Formula Gaps — Known Limitations (P1–P8)"):
                st.markdown(ONPV_GAPS_MD)

            with st.expander("Sector Methodology Assumptions — Health · Hydro · Rail"):
                st.markdown(SECTOR_ASSUMPTIONS_MD)

            with st.expander("Supply-Chain Analysis — EXIOBASE 3.8 Leontief Tiers 0–10"):
                st.markdown("""
## Supply-Chain IO Analysis (EXIOBASE 3.8 · Tiers 0–10)

The Leontief power-series decomposition is computed over tiers 0–10.
Source: Stadler et al. (2018) — https://doi.org/10.1111/jiec.12715

| Tier | Table | Description |
|------|-------|-------------|
| **0** | `t0` | Direct investment — one-time CAPEX split across 8 supplying sectors |
| **1** | `t1` | First upstream round — what Tier 0 suppliers procure; includes bilateral sourcing-country |
| **2** | `t2` | Second upstream round — sub-suppliers of Tier 1 |
| **3–10** | `t3` | Deep upstream — aggregated; A-matrix spectral radius ≈ 0.52; tiers >8 < 0.1% of signal |

**Four stressors** are computed per tier and adjusted for SSP scenario:

| Stressor | Raw unit | SSP adjustment | Source |
|----------|---------|----------------|--------|
| GHG (tCO₂e) | `adj_ratio_ghg` | OSeMOSYS grid-intensity trajectory | EXIOBASE 3.8 satellite account |
| Employment (FTE) | `adj_ratio_employment` | Labour-market structural change | EXIOBASE 3.8 + ILO standard (1,880 h/yr) |
| Water (1,000 m³) | `1 − renewable_share × 0.85` | Water-energy nexus | IEA Water for Energy + REMIND-MAgPIE |
| Value Added (M USD) | `adj_ratio_employment` | Productivity proxy | EXIOBASE 3.8 |

**Dependency weighting:** Each scenario-adjusted stressor is multiplied by the three-component
`dep_factor` (ENCORE × WWF × SC sector sensitivity) to produce the **dep-weighted** quantities
used in the WACC ESG greenium calculation.

**Portfolio supply-chain totals (SSP2-4.5, 2030):**

| Project | GHG adj (tCO₂e) | FTE adj | Water adj (000 m³) |
|---------|-----------------|---------|--------------------|
| Rail_EU_DEV | 527,429 | 30,977 | 2,697 |
| Proj_001 | 97,844 | 6,394 | 462 |
| Hydro_AS | 51,579 | 3,949 | 362 |
| Proj_003 | 17,849 | 1,190 | 106 |
| Proj_002 | 7,955 | 742 | 61 |
| Hydro_AF | 10,185 | 871 | 69 |
| Hydro_EU | 548 | 31 | 3 |
| Rail_EU_OP1 | 29 | 2 | 0 |
| Rail_EU_OP2 | 20 | 1 | 0 |

**Portfolio net GHG position:**
1,077,302 tCO₂e supply-chain emissions − 990,344 tCO₂e avoided = **86,958 tCO₂e net**
(portfolio is a net GHG emitter despite the hydro GHG-avoidance credits).
""")

            with st.expander("References & Data Sources — full bibliography with DOIs"):
                st.markdown(REFERENCES_MD)

        # ── Tab 9: Portfolio ──────────────────────────────────────────────────
        elif _tidx == 9:
            _role_hints_9 = {
                "Strategy Economist": (
                    "**Strategy Economist view** — The portfolio tables show how sector and region "
                    "interact to determine iNPV/CAPEX ratios. European health and rail dominate on "
                    "employment benefit (high GVA/h); African hydro underperforms due to low "
                    "labour coefficients and high water scarcity. Use SSP Scenario Analysis to "
                    "understand the portfolio's climate-pathway sensitivity."
                ),
                "Portfolio Manager": (
                    "**Portfolio Manager view** — Revenue at risk ($145.2 M portfolio total) and "
                    "high-risk project count (5/9) drive the ESG WACC adjustment. The iNPV/CAPEX "
                    "column is the concessional capital allocation signal: deploy blended finance "
                    "where SVA/CAPEX > 1× and financial NPV is negative."
                ),
                "Investment Officer": (
                    "**Investment Officer view** — Compare iNPV and SVA across projects to identify "
                    "where co-financing adds most societal value. Proj_001 (Health/LATAM) has the "
                    "highest SVA/CAPEX (+8.90×); Hydro Africa/Asia projects are value-destructive "
                    "at current WifOR water coefficients."
                ),
                "Compliance Specialist": (
                    "**Compliance Specialist view** — The construction-phase stressor table provides "
                    "portfolio-level GHG and water footprint for SFDR PAI table 1 aggregation. "
                    "Net GHG = supply-chain emissions − avoided CO₂ (86,958 tCO₂e net for this "
                    "portfolio) must be disclosed per SFDR Annex I, indicator 1."
                ),
            }
            st.info(_role_hints_9[active_role])
            st.warning(
                "**Data note — hardcoded pre-computed values.** "
                "The tables below are fixed outputs from the integrated finance assessment run "
                "(SSP2-4.5, focus year 2030, default project parameters). "
                "They do **not** update when you change sidebar parameters. "
                "For live values, use the Project Profile tab's 'Live Computation Results' section "
                "or the Portfolio Manager's Risk Dashboard which uses the live multi-project runner. "
                "Source: `integrated_finance_assessment.pdf` / executed notebook "
                "`project_finance_analysis.ipynb` (commit 222c4ae)."
            )
            st.subheader("Portfolio Overview — All 9 Projects")

            with st.expander("Financial & Societal Metrics Summary (SSP2-4.5 baseline)", expanded=True):
                st.caption(
                    "Source: pre-computed assessment run · SSP2-4.5 · focus year 2030 · "
                    "default project parameters. iNPV monetised via WifOR H5 (ISO3/NACE look-up). "
                    "WACC adj from ENCORE v2024 + WWF WRF 2.0. Hardcoded — see note above."
                )
                st.markdown("""
*Results from the pre-computed assessment run (values may differ from live sidebar overrides).*

| Project | Sector | Region | CAPEX (M) | NPV (M) | iNPV (M) | SVA (M) | Fin IRR | S-IRR | WACC adj |
|---------|--------|--------|-----------|---------|---------|---------|---------|-------|---------|
| Rail_EU_DEV | Rail Dev | Europe | 1,998 | +89.3 | +9,972.4 | +9,883.1 | 6.93% | — | 6.49% |
| Rail_EU_OP1 | Rail Op | Europe | 0.14 | −0.08 | +0.59 | +0.68 | — | — | 6.49% |
| Rail_EU_OP2 | Rail Op | Europe | 0.10 | −0.06 | +0.41 | +0.47 | — | — | 6.49% |
| Proj_001 | Health | LATAM | 250.0 | −196.6 | +2,027.7 | +2,224.3 | — | — | 7.99% |
| Proj_002 | Health | Africa | 25.0 | −20.4 | −7.9 | +12.5 | — | 1.58% | 8.99% |
| Proj_003 | Health | Europe | 75.0 | −36.7 | +276.8 | +313.4 | — | — | 5.99% |
| Hydro_AF | Energy | Africa | 30.0 | −4.2 | −159.3 | −155.1 | 6.93% | — | 8.49% |
| Hydro_AS | Energy | Asia | 150.0 | −2.7 | −499.7 | −497.0 | 7.33% | 23.1%* | 7.49% |
| Hydro_EU | Energy | Europe | 2.0 | −0.6 | +30.5 | +31.1 | 1.80% | — | 5.99% |

SVA = Societal Value Added = iNPV − NPV.
\\* Hydro_AS S-IRR of 23.1% is the rate that discounts the deeply negative annual dividend to zero —
not a positive signal; see Project Profile for full interpretation.
""")

            with st.expander("Construction-Phase Stressors (IO Supply-Chain, SSP2-4.5)"):
                st.caption(
                    "Source: EXIOBASE 3.8 IO model via tvp_io_lib · SSP2-4.5 · 2030. "
                    "GHG cost = supply-chain GHG × WifOR c_ghg (Nordhaus DICE). "
                    "Water cost = supply-chain water × WifOR c_water (shadow price, ISO3/NACE). "
                    "Employment benefit = supply-chain FTE × 1,880 h/yr × WifOR c_gva (GVA/h). "
                    "Nature Debt = Employment benefit − GHG cost − Water cost (at t=0). "
                    "Hardcoded — does not reflect sidebar parameter changes."
                )
                st.markdown("""
| Project | GHG (tCO₂e) | FTE | Water (000 m³) | GHG cost (M) | Water cost (M) | Emp benefit (M) | Nature Debt (M) |
|---------|------------|-----|---------------|-------------|---------------|----------------|----------------|
| Rail_EU_DEV | 527,429 | 30,977 | 2,697 | −55.24 | −0.69 | +6,499.96 | +6,555.88 |
| Rail_EU_OP1 | 29 | 2 | 0 | −0.003 | 0.000 | +0.42 | +0.43 |
| Rail_EU_OP2 | 20 | 1 | 0 | −0.002 | 0.000 | +0.29 | +0.29 |
| Proj_001 | 97,844 | 6,394 | 462 | −10.25 | −0.51 | +1,349.12 | +1,359.88 |
| Proj_002 | 7,955 | 742 | 61 | −0.83 | −0.12 | +7.02 | +7.97 |
| Proj_003 | 17,849 | 1,190 | 106 | −1.87 | −0.03 | +190.05 | +191.95 |
| Hydro_AF | 10,185 | 871 | 69 | −1.07 | −0.14 | +9.47 | +10.67 |
| Hydro_AS | 51,579 | 3,949 | 362 | −5.40 | −8.35 | +408.17 | +421.92 |
| Hydro_EU | 548 | 31 | 3 | −0.06 | −0.001 | +26.34 | +26.40 |

Nature Debt is **positive** when Employment benefit > GHG + Water cost (net societal asset at construction).
All nine projects show positive Nature Debt — employment creation dominates.
For Hydro_AS: the high water cost (−$8.35 M) reflects India's extreme water scarcity
coefficient (c_water = −$23.04/m³ from WifOR H5 file).
""")

            with st.expander("Supply-Chain Intensity per $1 M CAPEX"):
                st.caption(
                    "Source: same IO run as stressor table, normalised by CAPEX (USD M). "
                    "Enables scale-independent cross-project comparison. "
                    "iNPV/CAPEX and SVA/CAPEX are the concessional finance allocation metrics: "
                    "higher = more societal return per dollar deployed. "
                    "Hardcoded — does not reflect sidebar parameter changes."
                )
                st.markdown("""
Normalising to per-$1M CAPEX enables cross-project comparison regardless of scale.

| Project | GHG intensity (tCO₂e/M) | FTE intensity (FTE/M) | Water intensity (000m³/M) | iNPV/CAPEX | SVA/CAPEX |
|---------|-----------------------|----------------------|--------------------------|-----------|---------|
| Rail_EU_DEV | 264 | 15.5 | 1.35 | +4.99 | +4.95 |
| Rail_EU_OP1 | 207 | 14.3 | 0.0 | +4.21 | +4.86 |
| Rail_EU_OP2 | 200 | 10.0 | 0.0 | +4.10 | +4.70 |
| Proj_001 | 391 | 25.6 | 1.85 | +8.11 | **+8.90** |
| Proj_002 | 318 | 29.7 | 2.44 | −0.32 | +0.50 |
| Proj_003 | 238 | 15.9 | 1.41 | +3.69 | +4.18 |
| Hydro_AF | 340 | 29.0 | 2.30 | −5.31 | −5.17 |
| Hydro_AS | 344 | 26.3 | 2.41 | −3.33 | −3.31 |
| **Hydro_EU** | 274 | 15.5 | 1.50 | **+15.25** | **+15.55** |

Health projects carry the highest GHG intensity (318–391 tCO₂e/M) due to import leakage on
medical equipment. Hydro_EU has the highest iNPV/CAPEX (+15.25) — DEU/D35 GVA/h = $447/h
creates outsized employment benefit at $2M scale.
""")

            with st.expander("Nature Dependency & WWF Risk Scores"):
                st.caption(
                    "Source: ENCORE v2024 ecosystem service materiality screening + "
                    "WWF Water Risk Framework 2.0 (WRF) / Biodiversity Risk Filter 1.0 (BRF) "
                    "via `dependency_profiler`. Revenue at risk = WRF physical × annual revenue "
                    "(CAPEX × revenue_yield). High risk = WRF physical ≥ 3.5 (threshold). "
                    "Top dependency = highest-scoring ENCORE materiality dimension for the sector. "
                    "Hardcoded — does not reflect sidebar parameter changes."
                )
                st.markdown("""
| Project | WRF Physical | WRF Composite | BRF Composite | High Risk | Revenue at Risk (M) | Top Dependency |
|---------|-------------|--------------|--------------|-----------|-------------------|----------------|
| Rail_EU_DEV/OP1/OP2 | 2.906 | 3.378 | 3.133 | No | $0.0 | Flood & storm protection |
| Proj_003 | 2.774 | 3.312 | 2.974 | No | $0.0 | Water supply |
| Hydro_EU | 3.170 | 3.622 | 3.231 | Yes | $0.9 | Water supply |
| Proj_002 | 4.087 | 3.513 | 3.598 | Yes | $3.6 | Water supply |
| Hydro_AF | 4.670 | 3.889 | 3.994 | Yes | $15.8 | Water supply |
| Proj_001 | 3.788 | 3.477 | 4.087 | Yes | $42.0 | Water supply |
| **Hydro_AS** | **4.970** | **4.266** | **4.259** | **Yes** | **$83.1** | Water supply |

**Portfolio: 5/9 high-risk · total revenue at risk = $145.2 M**

Top ecosystem dependencies portfolio-wide (from ENCORE materiality screening):
`water_supply` (6/9 projects, score 5/5) · `climate_regulation` (6/9) ·
`erosion_control` (6/9) · `flood_and_storm_protection` (6/9)
""")

            with st.expander("SSP Scenario Analysis & Channel Dominance"):
                st.markdown("""
### SSP Ordering Pattern (European projects)

**SSP1-1.9 ≈ SSP4-6.0 > SSP2-4.5 > SSP3-7.0 ≈ SSP5-8.5**

SSP4-6.0 ranks near SSP1-1.9 despite higher warming because its policy structure
(technological access under inequality) keeps GHG intensity low **and** employment uplift high —
similar to SSP1 on all three transmission channels.

For **Hydro_AS** the ordering inverts: SSP5-8.5 (highest water adj = 0.864) is worst;
SSP1-1.9 (lowest water adj = 0.499) is best. Water-energy nexus (Channel 3) dominates.

### Channel Dominance by Sector

| Sector | Dominant channel | Rationale |
|--------|-----------------|-----------|
| **Rail (EU)** | Employment (Ch. 2) | DEU GVA/h $111–121/h × 30k+ FTE >> GHG and water |
| **Health (LATAM/EU)** | Employment (Ch. 2) | BRA/Q $112/h × 6,394 FTE = $1.35 B construction benefit |
| **Health (Africa)** | GHG intensity (Ch. 1) | NGA/Q $5.04/h suppresses employment; SSP1 adj_ghg = 0.041 |
| **Hydro (Asia/Africa)** | Water-energy nexus (Ch. 3) | c_water = −$23/m³ (IND) / −$1.95/m³ (NGA) is the swing factor |

### Scenario GHG Totals — SSP1 vs SSP5 (2030)

- **SSP1-1.9:** portfolio supply-chain GHG ≈ 388,000 tCO₂e (−63% from 2020 baseline of 1,046,000)
- **SSP5-8.5:** portfolio supply-chain GHG ≈ 860,000 tCO₂e (−18% from baseline)
- **Scenario spread:** 472,000 tCO₂e — driven by bilateral sourcing-country divergence at tier 1
""")

            with st.expander("Portfolio Synthesis & Investment Implications"):
                st.markdown(PORTFOLIO_SYNTHESIS_MD)

            with st.expander("References & Data Sources"):
                st.markdown(REFERENCES_MD)

# ── Role-specific extra tabs ──────────────────────────────────────────────────
with _role_tab:

    # ── Investment Officer: Country Comparison ────────────────────────────────
    if active_role == "Investment Officer":
        _io_sector  = st.session_state.get("compare_sector", sector_sel)
        _io_capex_m = st.session_state.get("compare_capex", 100.0)
        _io_capex   = int(_io_capex_m * 1e6)
        _highlight  = st.session_state.get("compare_countries", [])

        st.subheader(f"Country Comparison — {_io_sector} · {_io_capex_m:.0f} M USD")
        st.info(
            "**Investment Officer view** — Sector and CAPEX are fixed (set in sidebar). "
            "All 42 EBRD ATQ countries are ranked by iNPV (SSP2-4.5 baseline). "
            "The ranking shows where the same project produces the highest societal return, "
            "driven by host-country labour coefficients (WifOR GVA/h), dep_factor, and OCI. "
            "Highlighted countries (sidebar multiselect) appear in the ATQ radar below."
        )
        st.caption(
            "iNPV ranked via `_run_multi_project` (live, IO fallback). "
            "ATQ: EBRD 2024-25 · `ebrd_atq_scores_2024_25.csv`. "
            "Overshoot: GFN NFA 2023 · `overshoot_results.csv`. "
            "All 42 ATQ-covered countries computed at SSP2-4.5 · focus year " + str(int(focus_yr)) + "."
        )

        _atq_df = _load_atq_data()
        _all_iso2 = list(ATQ_ISO2_TO_NAME.keys())

        # Build specs for all ATQ countries at fixed sector/CAPEX
        _cc_specs = tuple(
            (f"cc_{c}", c, _io_sector, _io_capex, 0)
            for c in _all_iso2
        )
        with st.spinner(f"Running {len(_all_iso2)} countries × {len(ALL_SSPS)} SSPs…"):
            _df_cc_all = _run_multi_project(_cc_specs, int(focus_yr), tuple(ALL_SSPS))

        if _df_cc_all.empty:
            st.warning("Multi-project runner returned no results.")
        else:
            _df_cc_mid = (
                _df_cc_all[_df_cc_all["ssp"] == "SSP2-4.5"].copy()
                if "ssp" in _df_cc_all.columns else _df_cc_all.copy()
            )
            # ATQ is now native in runner output — no post-hoc map needed
            _df_cc_mid["highlighted"] = _df_cc_mid["country"].isin(_highlight)

            # ── Ranked iNPV bar — colored by ATQ average ──────────────────────
            st.markdown(f"#### iNPV Ranking — {_io_sector} · {_io_capex_m:.0f} M USD · all countries (SSP2-4.5 · {int(focus_yr)})")
            _sorted_cc = _df_cc_mid.sort_values("inpv_usd", ascending=False) if "inpv_usd" in _df_cc_mid.columns else _df_cc_mid
            _inpv_col  = "inpv_usd" if "inpv_usd" in _sorted_cc.columns else ([c for c in _sorted_cc.columns if "inpv" in c.lower()] or [None])[0]
            if _inpv_col:
                # Color bars by ATQ average (RdYlGn: low=red, mid=yellow, high=green)
                _atq_vals = _sorted_cc["atq_avg"].fillna(5.0).tolist()
                _atq_norm = [(v - 1.0) / 9.0 for v in _atq_vals]
                def _rdylgn_hex(t: float) -> str:
                    if t < 0.5:
                        r = 215 + int((255 - 215) * (1 - t * 2))
                        g = int(48 + (255 - 48) * (t * 2))
                        b = 39
                    else:
                        r = int(255 * (1 - (t - 0.5) * 2))
                        g = int(150 + (100 - 150) * (t - 0.5) * 2)
                        b = int((t - 0.5) * 2 * 70)
                    r, g, b = max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b))
                    return f"#{r:02x}{g:02x}{b:02x}"
                _bar_colors_atq = [_rdylgn_hex(t) for t in _atq_norm]
                _border_colors = ["gold" if c in _highlight else "rgba(0,0,0,0)"
                                   for c in _sorted_cc["country"]]
                _hovertext = [
                    f"{ATQ_ISO2_TO_NAME.get(c,c)}<br>iNPV: {y:.1f} M USD<br>ATQ avg: {a:.2f}/10"
                    f"<br>OCI: {o:.2f}%<br>bc_deficit_mult: {b:.3f}×"
                    for c, y, a, o, b in zip(
                        _sorted_cc["country"],
                        _sorted_cc[_inpv_col],
                        _sorted_cc["atq_avg"].fillna(0),
                        _sorted_cc["oci_pct"].fillna(0) if "oci_pct" in _sorted_cc.columns else [0]*len(_sorted_cc),
                        _sorted_cc["bc_deficit_mult"].fillna(1) if "bc_deficit_mult" in _sorted_cc.columns else [1]*len(_sorted_cc),
                    )
                ]
                _fig_ranked = go.Figure(go.Bar(
                    x=_sorted_cc["country"],
                    y=_sorted_cc[_inpv_col],
                    marker=dict(color=_bar_colors_atq, line=dict(color=_border_colors, width=2)),
                    hovertext=_hovertext, hoverinfo="text",
                ))
                _fig_ranked.update_layout(
                    title=f"{_io_sector} iNPV ({_io_capex_m:.0f} M USD) — all ATQ economies · SSP2-4.5 · {int(focus_yr)}<br><sup>Bar colour = ATQ average (green=high, red=low) · Gold border = highlighted country</sup>",
                    xaxis_title="Country (ISO-2)", yaxis_title="iNPV (USD)",
                    template=plotly_template, paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(_fig_ranked, use_container_width=True)
                st.caption("Bar colour encodes EBRD ATQ Average (1–10): green = strong transition quality, red = weak. Gold border = countries selected in sidebar. Source: EBRD 2024-25 · GFN NFA 2023.")

            # ── ATQ heatmap — all countries × 6 dimensions ───────────────────
            st.markdown(f"#### EBRD ATQ Transition Quality — all {len(_all_iso2)} economies · 6 dimensions")
            _all_names = [ATQ_ISO2_TO_NAME[c] for c in _all_iso2
                          if ATQ_ISO2_TO_NAME[c] in _atq_df.index]
            if _all_names:
                _atq_heat_sorted = _atq_df.loc[_all_names, ATQ_DIMENSIONS + ["ATQ_Average"]].sort_values("ATQ_Average", ascending=False)
                _atq_heat_sorted.columns = ATQ_DIM_LABELS[:-1] + ["Average"]
                _fig_heat = px.imshow(
                    _atq_heat_sorted,
                    color_continuous_scale="RdYlGn",
                    zmin=1, zmax=10,
                    aspect="auto",
                    title=f"EBRD ATQ 2024-25 — 6 dimensions + average · sorted by ATQ Average · {_io_sector} deployment context",
                    labels={"color": "ATQ Score (1–10)"},
                )
                _fig_heat.update_layout(
                    template=plotly_template, paper_bgcolor="rgba(0,0,0,0)",
                    height=720,
                )
                st.plotly_chart(_fig_heat, use_container_width=True)
                st.caption(
                    "Source: EBRD Transition Report 2024-25 · `indicators/ebrd_atq_scores_2024_25.csv` · 42 economies. "
                    "Green dimension → links to OCI / GHG mitigation. Resilient → links to bc_deficit_mult."
                )

            # ── Ranked table: iNPV + all 6 ATQ dimensions + OCI ─────────────
            st.markdown(f"#### Full cross-country ranking — {_io_sector} · {_io_capex_m:.0f} M USD · SSP2-4.5 · {int(focus_yr)}")
            _atq_cols_native = [c for c in ["atq_avg","atq_competitive","atq_well_governed",
                                             "atq_green","atq_inclusive","atq_resilient","atq_integrated"]
                                if c in _df_cc_mid.columns]
            _rank_show = [c for c in (["country", _inpv_col, "oci_pct", "bc_deficit_mult",
                                        "wwf_score", "ef_carbon_gha"] + _atq_cols_native)
                          if c and c in _df_cc_mid.columns]
            if _rank_show and _inpv_col:
                _rank_df = _df_cc_mid[_rank_show].copy().sort_values(_inpv_col, ascending=False)
                _rank_df.insert(1, "Country name",
                                _rank_df["country"].map(lambda c: ATQ_ISO2_TO_NAME.get(c, c)))
                _rank_df = _rank_df.drop(columns=["country"]).set_index("Country name")
                _green_cols  = [c for c in [_inpv_col] + _atq_cols_native if c in _rank_df.columns]
                _red_cols    = [c for c in ["oci_pct","bc_deficit_mult","wwf_score","ef_carbon_gha"] if c in _rank_df.columns]
                st.dataframe(
                    _rank_df.style
                        .background_gradient(subset=_green_cols, cmap="RdYlGn")
                        .background_gradient(subset=_red_cols,   cmap="RdYlGn_r")
                        .format({c: "{:.2f}" for c in _rank_df.select_dtypes("number").columns}),
                    use_container_width=True,
                )
                st.caption("Columns: iNPV (USD) at SSP2-4.5, OCI = overshoot contribution (%), bc_deficit_mult, WWF water risk, EF carbon (gha), then all 6 ATQ dimensions + average.")

            # ── iNPV vs ATQ scatter ──────────────────────────────────────────
            st.markdown("#### iNPV vs ATQ Average — investment quality map")
            if _inpv_col and "atq_avg" in _df_cc_mid.columns:
                _scat_df = _df_cc_mid[["country", _inpv_col, "atq_avg",
                                        "oci_pct", "bc_deficit_mult"]].dropna(subset=["atq_avg"])
                _scat_df["label"] = _scat_df["country"].map(ATQ_ISO2_TO_NAME)
                _fig_scat2 = px.scatter(
                    _scat_df, x="atq_avg", y=_inpv_col,
                    text="country",
                    color="oci_pct" if "oci_pct" in _scat_df.columns else None,
                    size="bc_deficit_mult" if "bc_deficit_mult" in _scat_df.columns else None,
                    color_continuous_scale="RdYlGn_r",
                    labels={"atq_avg": "ATQ Average (1–10)", _inpv_col: "iNPV (M USD)",
                            "oci_pct": "OCI (%)"},
                    title=f"{_io_sector}: iNPV vs ATQ Average (colour=OCI, size=bc_deficit_mult)",
                    template=plotly_template,
                )
                _fig_scat2.update_traces(textposition="top center")
                _fig_scat2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(_fig_scat2, use_container_width=True)
                st.caption(
                    "Top-right quadrant (high ATQ + high iNPV) = optimal deployment. "
                    "Bubble size = bc_deficit_mult (larger = more biocapacity pressure). "
                    "Colour = OCI (darker red = higher overshoot contribution)."
                )

            # ── ATQ radar for highlighted countries only ──────────────────────
            if _highlight:
                st.markdown(f"#### ATQ Radar — highlighted countries ({', '.join(_highlight)})")
                _fig_hl = go.Figure()
                _fig_hl.add_trace(go.Scatterpolar(
                    r=[10.0] * len(ATQ_DIMENSIONS) + [10.0],
                    theta=ATQ_DIM_LABELS + [ATQ_DIM_LABELS[0]],
                    name="Frontier (10)", line_color="gold", line_dash="dot",
                ))
                for _hc in _highlight:
                    _hcn = ATQ_ISO2_TO_NAME.get(_hc, "")
                    if _hcn and _hcn in _atq_df.index:
                        _hv = [float(_atq_df.loc[_hcn, d]) for d in ATQ_DIMENSIONS]
                        _hv.append(_hv[0])
                        _fig_hl.add_trace(go.Scatterpolar(
                            r=_hv, theta=ATQ_DIM_LABELS + [ATQ_DIM_LABELS[0]],
                            fill="toself", name=_hcn,
                        ))
                _fig_hl.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                    template=plotly_template, paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h"),
                )
                st.plotly_chart(_fig_hl, use_container_width=True)

    # ── Strategy Economist: Country Canvas ────────────────────────────────────
    elif active_role == "Strategy Economist":
        _cc        = st.session_state.get("canvas_country", "DE")
        _cc_name   = ATQ_ISO2_TO_NAME.get(_cc, _cc)
        _ce        = st.session_state.get("canvas_entries_df")
        _atq_df    = _load_atq_data()
        _ov_df     = _load_overshoot_data()

        st.subheader(f"Country Canvas — {_cc_name} ({_cc})")
        st.info(
            "**Strategy Economist view** — Add hypothetical projects in the sidebar (sector + CAPEX). "
            "The canvas compares how different sectors perform under the same host country, "
            "across all SSP scenarios. This reveals sector-level channel dominance: "
            "which sector benefits most from this country's labour productivity, "
            "which is most exposed to water scarcity or GHG intensity trajectories."
        )
        st.caption(
            "ATQ: EBRD 2024-25 · `ebrd_atq_scores_2024_25.csv`. "
            "Overshoot: GFN NFA 2023 · `overshoot_results.csv`. "
            "iNPV via `_run_multi_project` (IO fallback when tvp_io_lib unavailable). "
            "EF carbon = supply-chain GHG × (1−0.35)/2.677 × 1.3 [gha]."
        )

        # ── ATQ + Overshoot country header ───────────────────────────────────
        col_atq, col_ov = st.columns(2)
        with col_atq:
            st.markdown(f"**ATQ Profile — {_cc_name}**")
            st.plotly_chart(_fig_atq_radar(_cc, plotly_template), use_container_width=True)
            _cn_atq = ATQ_ISO2_TO_NAME.get(_cc, "")
            if _cn_atq and _cn_atq in _atq_df.index:
                _atq_row = _atq_df.loc[_cn_atq]
                st.dataframe(pd.DataFrame({
                    "Dimension": ATQ_DIM_LABELS + ["Average"],
                    "Score": [float(_atq_row[d]) for d in ATQ_DIMENSIONS] + [float(_atq_row["ATQ_Average"])],
                    "Interpretation": [
                        "Market openness, SME, innovation",
                        "Rule of law, anti-corruption, governance",
                        "GHG mitigation, renewables, adaptation",
                        "Labour participation, gender equity, finance access",
                        "Financial stability, energy liberalisation",
                        "Trade, FDI, transport & digital infra",
                        "Weighted composite",
                    ],
                }), hide_index=True, use_container_width=True)
            else:
                st.info(f"No ATQ data for {_cc}.")

        with col_ov:
            st.markdown(f"**Ecological Overshoot — {_cc_name}**")
            _ov_name = _ISO2_TO_OVERSHOOT_NAME.get(_cc, "")
            if _ov_name and _ov_name in _ov_df.index:
                _ov = _ov_df.loc[_ov_name]
                _ef_tot  = float(_ov.get("ef_total_gha", 0))
                _bc_tot  = float(_ov.get("bc_total_gha", 0))
                _deficit = float(_ov.get("ecological_deficit_gha", 0))
                _oci_c   = (_ef_tot / _bc_tot * 100) if _bc_tot > 0 else 0.0
                _mult_c  = 1.0 if _deficit >= 0 else min(1.5, 1 + abs(_deficit) / max(_bc_tot, 1))
                ov_kpi1, ov_kpi2, ov_kpi3 = st.columns(3)
                ov_kpi1.metric("EF total (gha)", f"{_ef_tot:.2f}")
                ov_kpi2.metric("BC total (gha)", f"{_bc_tot:.2f}",
                               delta="surplus" if _deficit >= 0 else f"deficit {_deficit:+.2f}")
                ov_kpi3.metric("bc_deficit_mult", f"{_mult_c:.3f}×")
                _cats_ov = ["Carbon","Cropland","Grazing","Forest","Fishing","Built-up"]
                _cols_ov = ["ef_carbon_gha","ef_cropland_gha","ef_grazing_gha",
                            "ef_forest_gha","ef_fishing_gha","ef_built_up_gha"]
                _ef_vs_bc = {
                    "Component": _cats_ov + _cats_ov,
                    "Value (gha)": [float(_ov.get(c, 0)) for c in _cols_ov] +
                                   [float(_ov.get(c.replace("ef_","bc_"), 0)) for c in _cols_ov],
                    "Type": ["EF"] * 6 + ["BC"] * 6,
                }
                _fig_efbc = px.bar(
                    _ef_vs_bc, x="Component", y="Value (gha)", color="Type",
                    barmode="group",
                    color_discrete_map={"EF": "#e6550d", "BC": "#31a354"},
                    title=f"EF vs BC by component — {_ov_name}",
                    template=plotly_template,
                )
                _fig_efbc.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(_fig_efbc, use_container_width=True)
            else:
                st.info(f"No overshoot data for {_cc} ({_ov_name or 'name mapping missing'}).")

        st.divider()

        # ── Multi-sector canvas run ───────────────────────────────────────────
        _ce_df = _ce if isinstance(_ce, pd.DataFrame) else pd.DataFrame([
            {"sector": "Rail",   "capex_m": 140.0, "avoided_co2": 0},
            {"sector": "Energy", "capex_m": 500.0, "avoided_co2": 50000},
            {"sector": "Health", "capex_m": 100.0, "avoided_co2": 0},
        ])
        _canvas_valid = _ce_df[_ce_df["capex_m"] > 0] if not _ce_df.empty else pd.DataFrame()

        if _canvas_valid.empty:
            st.info("Add at least one project in the sidebar to run the canvas analysis.")
        else:
            _canvas_specs = tuple(
                (f"canvas_{row['sector']}_{i}", _cc, row["sector"],
                 int(row["capex_m"] * 1e6), int(row.get("avoided_co2", 0)))
                for i, (_, row) in enumerate(_canvas_valid.iterrows())
            )
            with st.spinner(f"Running {len(_canvas_valid)} sectors × {len(ALL_SSPS)} SSPs…"):
                _df_canvas = _run_multi_project(_canvas_specs, int(focus_yr), tuple(ALL_SSPS))

            if _df_canvas.empty:
                st.warning("Canvas runner returned no data.")
            else:
                _df_mid_c = (_df_canvas[_df_canvas["ssp"] == "SSP2-4.5"].copy()
                             if "ssp" in _df_canvas.columns else _df_canvas.copy())

                # ── GHG tier 0 vs tier 1 by sector ───────────────────────────
                st.markdown(f"#### Supply-chain GHG by sector — {_cc_name} (SSP2-4.5)")
                _tier_cols = [c for c in ["tier0_ghg","tier1_ghg"] if c in _df_mid_c.columns]
                _id_col    = "sector" if "sector" in _df_mid_c.columns else "project_id"
                if _tier_cols and _id_col in _df_mid_c.columns:
                    _fig_tier = px.bar(
                        _df_mid_c, x=_id_col, y=_tier_cols,
                        barmode="group",
                        labels={"value": "GHG (tCO₂e)", "variable": "Tier",
                                _id_col: "Sector"},
                        title="GHG — Tier 0 (direct) vs Tier 1 (upstream) per sector",
                        template=plotly_template,
                        color_discrete_map={"tier0_ghg": "#2166ac", "tier1_ghg": "#d73027"},
                    )
                    _fig_tier.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_tier, use_container_width=True)
                    st.caption("Tier 0 = direct construction spend. Tier 1 = bilateral upstream procurement. Source: EXIOBASE 3.8 · IO fallback when tvp_io_lib unavailable.")

                # ── iNPV by sector × SSP ─────────────────────────────────────
                st.markdown(f"#### iNPV across SSP scenarios — {_cc_name}")
                _inpv_c = next((c for c in ["inpv","inpv_usd"] if c in _df_canvas.columns), None)
                if _inpv_c and _id_col in _df_canvas.columns:
                    _fig_inpv_c = px.bar(
                        _df_canvas, x=_id_col, y=_inpv_c, color="ssp",
                        barmode="group",
                        labels={_id_col: "Sector", _inpv_c: "iNPV (M USD)", "ssp": "SSP"},
                        title=f"Monetised iNPV by sector × SSP — {_cc_name}",
                        template=plotly_template,
                    )
                    _fig_inpv_c.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_inpv_c, use_container_width=True)

                # ── Aggregate country iNPV by SSP ─────────────────────────────
                st.markdown("#### Aggregate country iNPV by SSP scenario")
                if _inpv_c:
                    _agg_ssp = _df_canvas.groupby("ssp")[_inpv_c].sum().reset_index()
                    _fig_agg = px.bar(
                        _agg_ssp, x="ssp", y=_inpv_c,
                        labels={"ssp": "SSP", _inpv_c: "Aggregate iNPV (M USD)"},
                        title=f"Total portfolio iNPV across scenarios — {_cc_name}",
                        color="ssp",
                        template=plotly_template,
                    )
                    _fig_agg.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_agg, use_container_width=True)
                    st.caption("Aggregate = sum of iNPV across all canvas sectors. Scenario spread = climate VaR for this country's investment pipeline.")

                # ── WifOR value factors by sector ─────────────────────────────
                st.markdown("#### WifOR value factors applied per sector")
                _vf_cols = [c for c in ["sector","c_ghg","c_gva","c_water"] if c in _df_mid_c.columns]
                if _vf_cols:
                    _vf_tbl = _df_mid_c[_vf_cols].drop_duplicates().set_index("sector") if "sector" in _vf_cols else _df_mid_c[_vf_cols]
                    st.dataframe(_vf_tbl, use_container_width=True)
                    st.caption("c_ghg: GHG social cost (USD/kg). c_gva: GVA per labour-hour (USD/h). c_water: water shadow price (USD/m³). Source: WifOR H5 database by ISO-3/NACE.")

                # ── OCI by sector ─────────────────────────────────────────────
                st.markdown("#### Overshoot Contribution Index by sector")
                if "oci_pct" in _df_mid_c.columns and _id_col in _df_mid_c.columns:
                    _fig_oci = px.bar(
                        _df_mid_c, x=_id_col, y="oci_pct",
                        color="bc_deficit_mult" if "bc_deficit_mult" in _df_mid_c.columns else None,
                        color_continuous_scale="RdYlGn_r",
                        labels={_id_col: "Sector", "oci_pct": "OCI (%)",
                                "bc_deficit_mult": "BC deficit mult"},
                        title=f"OCI per sector as % of {_cc_name} biocapacity",
                        template=plotly_template,
                    )
                    _fig_oci.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_oci, use_container_width=True)
                    st.caption("OCI = (EF_carbon + EF_land) / BC_total × 100. bc_deficit_mult applied to dep_factor when country is in overshoot. Source: GFN NFA 2023.")

    # ── Portfolio Manager: Risk Dashboard ─────────────────────────────────────
    elif active_role == "Portfolio Manager":
        st.subheader("Portfolio Risk Dashboard — CFA-aligned impact framework")
        st.info(
            "**Portfolio Manager view** — Full CFA-style risk analysis across selected projects. "
            "Each project's financial parameters are shown first, followed by iNPV statistics "
            "across 5 SSP scenarios (mean, std, Sharpe). "
            "The efficient frontier maps mean iNPV vs SSP volatility. "
            "The 4-factor model decomposes risk into GHG transition, water scarcity, "
            "employment formality, and biocapacity deficit loadings per project."
        )
        st.caption(
            "Live runner: `_run_multi_project` (project × SSP). "
            "IO fallback: _INTENSITY_FALLBACK when tvp_io_lib unavailable. "
            "Impact Sharpe = mean(iNPV) / std(iNPV) across 5 SSPs. "
            "Scenario VaR = iNPV at SSP5-8.5. Source: GFN NFA 2023 · EXIOBASE 3.8."
        )

        _pids = st.session_state.get("portfolio_pids", [p["project_id"] for p in PROJECTS])
        _port_projs = [p for p in PROJECTS if p["project_id"] in _pids]

        if not _port_projs:
            st.info("Select at least one project in the sidebar.")
        else:
            # ── Per-project financial parameters ─────────────────────────────
            st.markdown("#### Per-project financial parameters")
            _param_rows = []
            for _pp in _port_projs:
                _param_rows.append({
                    "Project":        _pp["project_id"],
                    "Sector":         _pp["sector"],
                    "Region":         _pp["region"],
                    "Country":        _pp.get("country", "—"),
                    "CAPEX (M USD)":  f"{_pp['capex_usd']/1e6:.2f}",
                    "WACC base (%)":  f"{_pp['wacc_base']*100:.2f}%",
                    "Rev yield (%)":  f"{_pp['revenue_yield']*100:.1f}%",
                    "OPEX ratio (%)": f"{_pp['opex_ratio']*100:.1f}%",
                    "Bond (yr)":      _pp["bond_years"],
                    "Project (yr)":   _pp["project_years"],
                    "Scenario":       _pp["scenario"],
                    "Avoided CO₂/yr": f"{_pp['avoided_co2']:,} tCO₂e",
                })
            st.dataframe(pd.DataFrame(_param_rows), hide_index=True, use_container_width=True)
            st.caption("Financial parameters as per PROJECTS registry. Override via Project sidebar controls for single-project analysis.")

            # ── Run multi-project across all SSPs ─────────────────────────────
            _pm_specs = tuple(
                (p["project_id"], p.get("country", "DE"), p["sector"],
                 p["capex_usd"], p.get("avoided_co2", 0))
                for p in _port_projs
            )
            with st.spinner(f"Running {len(_port_projs)} projects × {len(ALL_SSPS)} SSPs…"):
                _port_df = _run_multi_project(_pm_specs, int(focus_yr), tuple(ALL_SSPS))

            if _port_df.empty:
                st.warning("Multi-project runner returned no data.")
            else:
                _pid_col   = "project_id" if "project_id" in _port_df.columns else "pid"
                _name_col  = "sector" if "sector" in _port_df.columns else _pid_col
                _inpv_col2 = next((c for c in ["inpv","inpv_usd"] if c in _port_df.columns), None)

                # ── CFA risk summary table ─────────────────────────────────────
                st.markdown(f"#### CFA Risk Summary — {', '.join(p['project_id'] for p in _port_projs)} · {int(focus_yr)}")
                if _inpv_col2 and _pid_col in _port_df.columns:
                    _agg_dict: dict = {
                        "sector":    (_name_col,           "first") if _name_col != _pid_col else (_pid_col, "first"),
                        "country":   ("country",           "first") if "country"   in _port_df.columns else (_pid_col, "first"),
                        "capex_usd": ("capex_usd",         "first") if "capex_usd" in _port_df.columns else (_pid_col, "first"),
                        "inpv_mean": (_inpv_col2,          "mean"),
                        "inpv_std":  (_inpv_col2,          "std"),
                        "inpv_worst":(_inpv_col2,          "min"),
                        "wacc_adj":  ("wacc_adj",          "first") if "wacc_adj"  in _port_df.columns else (_pid_col, "first"),
                        "mean_dep":  ("dep_factor",        "first") if "dep_factor" in _port_df.columns else (_pid_col, "first"),
                        "wwf_water": ("wwf_score",         "first") if "wwf_score"  in _port_df.columns else (_pid_col, "first"),
                        "oci_pct":   ("oci_pct",           "first") if "oci_pct"    in _port_df.columns else (_pid_col, "first"),
                        "bc_mult":   ("bc_deficit_mult",   "first") if "bc_deficit_mult" in _port_df.columns else (_pid_col, "first"),
                    }
                    # Add native ATQ columns
                    for _atqc in ["atq_avg","atq_competitive","atq_well_governed",
                                  "atq_green","atq_inclusive","atq_resilient","atq_integrated"]:
                        if _atqc in _port_df.columns:
                            _agg_dict[_atqc] = (_atqc, "first")
                    _risk_summary = (
                        _port_df.groupby(_pid_col)
                        .agg(**_agg_dict)
                        .assign(impact_sharpe=lambda d: (
                            d["inpv_mean"] / d["inpv_std"].replace(0, float("nan"))
                        ))
                        .reset_index()
                    )
                    _atq_pm_cols = [c for c in ["atq_avg","atq_green","atq_resilient","atq_competitive",
                                                 "atq_well_governed","atq_inclusive","atq_integrated"]
                                    if c in _risk_summary.columns]
                    _rs_show = [c for c in ([_pid_col,"sector","country","capex_usd",
                                             "inpv_mean","inpv_std","inpv_worst","impact_sharpe",
                                             "wacc_adj","mean_dep","wwf_water","oci_pct","bc_mult"]
                                            + _atq_pm_cols)
                                if c in _risk_summary.columns]
                    _rs_grad_green = [c for c in (["inpv_mean","inpv_worst","impact_sharpe"] + _atq_pm_cols) if c in _risk_summary.columns]
                    _rs_grad_red   = [c for c in ["mean_dep","wwf_water","oci_pct","bc_mult","inpv_std"] if c in _risk_summary.columns]
                    st.dataframe(
                        _risk_summary[_rs_show].style
                            .background_gradient(subset=_rs_grad_green, cmap="RdYlGn")
                            .background_gradient(subset=_rs_grad_red,   cmap="RdYlGn_r")
                            .format({c: "{:.3f}" for c in (["inpv_mean","inpv_std","inpv_worst",
                                                            "impact_sharpe","wacc_adj","mean_dep",
                                                            "wwf_water","oci_pct","bc_mult"]
                                                           + _atq_pm_cols)
                                     if c in _risk_summary.columns}),
                        use_container_width=True,
                    )
                    st.caption(
                        "Impact Sharpe = mean(iNPV) / std(iNPV) across SSPs. "
                        "ATQ columns (green gradient): country-level EBRD 2024-25 scores — "
                        "Green dimension ↔ OCI; Resilient ↔ bc_deficit_mult. "
                        "Source: EBRD Transition Report 2024-25 · GFN NFA 2023."
                    )

                    # ── Summary KPIs ──────────────────────────────────────────
                    _kp1, _kp2, _kp3, _kp4 = st.columns(4)
                    if "inpv_mean" in _risk_summary.columns:
                        _kp1.metric("Aggregate mean iNPV", f"{_risk_summary['inpv_mean'].sum():.1f} M USD")
                    if "impact_sharpe" in _risk_summary.columns:
                        _kp2.metric("Portfolio impact Sharpe", f"{_risk_summary['impact_sharpe'].mean():.2f}")
                    if "mean_dep" in _risk_summary.columns:
                        _kp3.metric("Projects dep > 1.2", int((_risk_summary["mean_dep"] > 1.2).sum()))
                    if "oci_pct" in _risk_summary.columns:
                        _kp4.metric("Max OCI across portfolio", f"{_risk_summary['oci_pct'].max():.2f}%")

                # ── iNPV bar by project + SSP ──────────────────────────────────
                _pm_proj_labels = ", ".join(p["project_id"] for p in _port_projs)
                st.markdown(f"#### iNPV by project across SSP scenarios — {_pm_proj_labels} · {int(focus_yr)}")
                if _inpv_col2 and _pid_col in _port_df.columns:
                    _fig_pm_bar = px.bar(
                        _port_df, x=_pid_col, y=_inpv_col2, color="ssp",
                        barmode="group",
                        labels={_pid_col: "Project", _inpv_col2: "iNPV (USD)", "ssp": "SSP"},
                        title=f"iNPV by project × SSP — {_pm_proj_labels} · {int(focus_yr)}",
                        template=plotly_template,
                    )
                    _fig_pm_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_pm_bar, use_container_width=True)

                # ── Efficient frontier ─────────────────────────────────────────
                st.markdown(f"#### Impact efficient frontier — {_pm_proj_labels} · {int(focus_yr)}")
                if "inpv_mean" in _risk_summary.columns and "inpv_std" in _risk_summary.columns:
                    _ef_color = "atq_avg" if "atq_avg" in _risk_summary.columns else (
                                "mean_dep" if "mean_dep" in _risk_summary.columns else None)
                    _ef_cscale = "RdYlGn" if _ef_color == "atq_avg" else "RdYlGn_r"
                    _ef_fig = px.scatter(
                        _risk_summary, x="inpv_std", y="inpv_mean",
                        text=_pid_col,
                        color=_ef_color,
                        color_continuous_scale=_ef_cscale,
                        size="bc_mult" if "bc_mult" in _risk_summary.columns else None,
                        labels={"inpv_std": "iNPV volatility (USD)", "inpv_mean": "Mean iNPV (USD)",
                                "atq_avg": "ATQ Average", "mean_dep": "dep_factor"},
                        title=f"Impact Efficient Frontier — {_pm_proj_labels} · {int(focus_yr)}<br><sup>Colour = ATQ Average (green=high transition quality) · Bubble = bc_deficit_mult</sup>",
                        template=plotly_template,
                    )
                    _ef_fig.update_traces(textposition="top center")
                    _ef_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_ef_fig, use_container_width=True)
                    st.caption(
                        "Top-left = high mean iNPV + low SSP volatility = optimal. "
                        "Colour = ATQ Average (green = strong transition quality → lower political/regulatory risk). "
                        "Bubble size = bc_deficit_mult (biocapacity overshoot penalty)."
                    )

                # ── Scenario VaR ──────────────────────────────────────────────
                st.markdown("#### Scenario Value-at-Risk (iNPV at SSP5-8.5)")
                if _inpv_col2 and "ssp" in _port_df.columns:
                    _var_df = _port_df[_port_df["ssp"] == "SSP5-8.5"][[_pid_col, _inpv_col2]].copy() if "SSP5-8.5" in _port_df["ssp"].values else _port_df.groupby(_pid_col)[_inpv_col2].min().reset_index()
                    _var_df = _var_df.sort_values(_inpv_col2)
                    st.dataframe(
                        _var_df.style.background_gradient(subset=[_inpv_col2], cmap="RdYlGn"),
                        hide_index=True, use_container_width=True,
                    )
                    _total_var = _var_df[_inpv_col2].sum()
                    st.caption(f"Portfolio iNPV at SSP5-8.5 (worst-case): {_total_var:.1f} M USD. Most negative project = highest climate tail risk.")

                # ── OCI by project ────────────────────────────────────────────
                st.markdown("#### Overshoot Contribution Index by project (SSP2-4.5)")
                if "oci_pct" in _port_df.columns and "ssp" in _port_df.columns:
                    _oci_df = _port_df[_port_df["ssp"] == "SSP2-4.5"][[_pid_col, "sector", "oci_pct",
                                                                         "ef_carbon_gha", "bc_deficit_mult"]].copy() \
                              if "SSP2-4.5" in _port_df["ssp"].values else _port_df[[_pid_col, "oci_pct"]].drop_duplicates()
                    _fig_oci_pm = px.bar(
                        _oci_df.sort_values("oci_pct", ascending=False),
                        x=_pid_col, y="oci_pct",
                        color="bc_deficit_mult" if "bc_deficit_mult" in _oci_df.columns else None,
                        color_continuous_scale="RdYlGn_r",
                        labels={_pid_col: "Project", "oci_pct": "OCI (%)",
                                "bc_deficit_mult": "bc_deficit_mult"},
                        title="Overshoot Contribution Index by project (% of host biocapacity)",
                        template=plotly_template,
                    )
                    _fig_oci_pm.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_oci_pm, use_container_width=True)
                    st.caption("OCI = (EF_carbon + EF_land) / BC_total × 100. Source: GFN NFA 2023. bc_deficit_mult amplifies dep_factor for ecologically stressed countries.")

                # ── OCI vs iNPV scatter ───────────────────────────────────────
                st.markdown("#### OCI vs iNPV — biocapacity-return quadrant map")
                _view_pm = (_port_df[_port_df["ssp"] == ssp_sel].copy()
                            if "ssp" in _port_df.columns and ssp_sel in _port_df["ssp"].values
                            else _port_df.copy())
                if "oci_pct" in _view_pm.columns and _inpv_col2:
                    _fig_quad = px.scatter(
                        _view_pm, x="oci_pct", y=_inpv_col2,
                        size="capex_usd" if "capex_usd" in _view_pm.columns else None,
                        color="bc_deficit_mult" if "bc_deficit_mult" in _view_pm.columns else None,
                        hover_name=_pid_col,
                        color_continuous_scale="RdYlGn_r",
                        labels={"oci_pct": "OCI (%)", _inpv_col2: "iNPV (M USD)",
                                "bc_deficit_mult": "BC deficit mult"},
                        title=f"OCI vs iNPV — {ssp_sel} (bubble = CAPEX, colour = bc_deficit_mult)",
                        template=plotly_template,
                    )
                    _fig_quad.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(_fig_quad, use_container_width=True)
                    st.caption("Bottom-left = low OCI + high iNPV = optimal (high societal return, low biocapacity pressure). Top-right = high risk / low return.")

    # ── Compliance Specialist: Regulatory Mapping ─────────────────────────────
    elif active_role == "Compliance Specialist":
        st.subheader("Regulatory Mapping")
        st.info(
            "**Compliance Specialist view** — Select a regulatory framework from the sidebar to "
            "see which model fields are mapped to disclosure requirements and whether the "
            "current project passes each threshold. "
            "SFDR/Taxonomy/CSRD checks PAI indicators and Taxonomy alignment; "
            "TCFD checks scenario analysis and physical risk disclosure; "
            "TNFD checks the LEAP framework (Locate, Evaluate, Assess, Prepare) using "
            "dep_factor and OCI as nature-risk proxies; "
            "EBRD ATQ checks the project's host-country transition quality against the "
            "Bank's minimum deployment thresholds; "
            "AIIB EP checks environmental and social standard alignment."
        )
        st.caption(
            "Regulatory matrix: `REGULATORY_MATRIX` constant in app.py — hardcoded field/threshold "
            "mappings drawn from: EU SFDR Annex I (2022/1288), EU Taxonomy Regulation 2020/852, "
            "CSRD ESRS E1/E4, UK FCA TCFD rules PS21/24, US SEC Climate Rule (17 CFR §229.1500), "
            "TNFD v1.0 (2023), EBRD ATQ 2024-25, AIIB ESF 2021. "
            "Model fields are computed live; thresholds are fixed policy values. "
            "Pass/Fail is indicative — formal compliance requires legal review."
        )
        _juris = st.session_state.get("reg_juris", JURISDICTIONS[0])
        _reqs  = REGULATORY_MATRIX.get(_juris, {})

        st.markdown(f"**Framework: {_juris}**")
        if not _reqs:
            st.info("No requirements defined for this jurisdiction.")
        else:
            _req_rows = []
            for _field, _spec in _reqs.items():
                _val   = metrics.get(_field) or eo_single.get(_field)
                _thr   = _spec.get("threshold")
                _label = _spec.get("label", _field)
                _unit  = _spec.get("unit", "")
                if _val is not None and _thr is not None:
                    _pass = _val >= _thr if _spec.get("direction", "ge") == "ge" else _val <= _thr
                    _status = "Pass" if _pass else "Fail"
                else:
                    _status = "N/A"
                    _pass   = None
                _req_rows.append({
                    "Requirement": _label,
                    "Model field":  _field,
                    "Value":        f"{_val:.3f} {_unit}" if isinstance(_val, float) else str(_val or "—"),
                    "Threshold":    f"{_thr} {_unit}" if _thr is not None else "—",
                    "Status":       _status,
                })

            def _colour_status(v):
                if v == "Pass":  return "background-color:#1a7a3a;color:white"
                if v == "Fail":  return "background-color:#8b1a1a;color:white"
                return ""

            _req_df = pd.DataFrame(_req_rows)
            st.dataframe(
                _req_df.style.map(_colour_status, subset=["Status"]),
                hide_index=True, use_container_width=True,
            )

        st.divider()
        st.markdown("**GHG Supply-Chain Summary**")
        _ghg_total = raw_sums.get("GHG_tCO2e", 0.0)
        _avoided   = proj["avoided_co2"]
        _net       = _ghg_total - _avoided
        _ghg_rows = [
            ("Supply-chain GHG (construction)", f"{_ghg_total:,.0f} tCO₂e"),
            ("Avoided CO₂ (operational/yr)",    f"{_avoided:,} tCO₂e/yr"),
            ("Net GHG (construction − avoided)", f"{_net:+,.0f} tCO₂e"),
            ("EF carbon this project (gha)",    f"{eo_single.get('ef_carbon_gha', 0.0):.4f}"),
            ("OCI (%)",                         f"{eo_single.get('oci_pct', 0.0):.2f}%"),
            ("bc_deficit_mult",                 f"{eo_single.get('bc_deficit_mult', 1.0):.4f}×"),
        ]
        st.dataframe(pd.DataFrame(_ghg_rows, columns=["Metric","Value"]),
                     hide_index=True, use_container_width=True)
