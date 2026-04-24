"""
Stage 4 – Portfolio-level aggregation and financial stress metrics

Implements:
  1. Revenue-at-Risk (RaR) calculation following WWF methodology:
       RaR = Σ (Asset_Revenue_i × Risk_Flag_i)
     where Risk_Flag is binary (>3.4 threshold) or weighted intensity.

  2. Climate–Nature nexus: Implied Temperature Rise (ITR) alignment proxy
     derived from reported emission reductions (hydro displacement data).

  3. Portfolio-level ENCORE dependency heatmap aggregation.

  4. Natural Capital Stress Test (NaST) summary table aligned with
     TNFD LEAP output format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math

HIGH_RISK_THRESHOLD = 3.4

# ---------------------------------------------------------------------------
# ITR proxy constants
# Based on IEA 1.5°C Compatible Pathway; USD social cost of carbon = $51/tCO2
# (World Bank 2023 reference value)
# ---------------------------------------------------------------------------
SOCIAL_COST_CARBON_USD_PER_TON = 51.0
BASELINE_GRID_INTENSITY = {          # kgCO2/kWh by region (regional grid mix)
    "africa": 0.62,
    "asia":   0.75,   # coal-heavy marginal (assumptions.txt)
    "europe": 0.23,
    "latam":  0.35,
}
PARIS_ALIGNED_TEMP_RISE = 1.5        # °C target
BUSINESS_AS_USUAL_TEMP_RISE = 3.2   # °C trajectory if no action

# Simple linear interpolation: 100% avoided → 1.5°C; 0% → 3.2°C
def _implied_temperature_rise(avoided_fraction: float) -> float:
    """avoided_fraction in [0, 1]"""
    avoided_fraction = max(0.0, min(1.0, avoided_fraction))
    itr = BUSINESS_AS_USUAL_TEMP_RISE - avoided_fraction * (
        BUSINESS_AS_USUAL_TEMP_RISE - PARIS_ALIGNED_TEMP_RISE
    )
    return round(itr, 2)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProjectFinancials:
    project_id:        str
    region:            str
    sector:            str
    investment_usd:    float
    revenue_proxy_usd: float         # estimated annual revenue or NPV proxy
    wrf_composite:     float
    brf_composite:     float
    avoided_co2_tons:  Optional[float] = None
    beneficiaries:     Optional[int]   = None
    capex_eur:         Optional[float] = None

    @property
    def risk_flag(self) -> bool:
        return self.wrf_composite > HIGH_RISK_THRESHOLD or \
               self.brf_composite > HIGH_RISK_THRESHOLD

    @property
    def risk_intensity(self) -> float:
        """Weighted risk score (0–5) used for partial revenue-at-risk."""
        return round(max(self.wrf_composite, self.brf_composite), 3)


@dataclass
class PortfolioReport:
    projects:               list[ProjectFinancials]
    total_investment_usd:   float = 0.0
    revenue_at_risk_usd:    float = 0.0
    high_risk_share:        float = 0.0    # % of portfolio by investment
    weighted_itr:           float = 0.0
    dependency_summary:     dict  = field(default_factory=dict)
    stress_test_table:      list  = field(default_factory=list)


# ---------------------------------------------------------------------------
# Revenue proxy derivation per sector
# ---------------------------------------------------------------------------

def _derive_revenue_proxy(proj_financials: dict, assumptions: dict) -> float:
    """
    Estimate the annual revenue (or equivalent NPV flow) that could be
    at risk if nature-related disruptions occur.

    Health  : investment × multiplier × operating_margin (OECD benchmark 8%)
    Hydro   : avoided_CO2_tons × social_cost_carbon + capacity_revenue_proxy
    Rail    : capex × toll_revenue_ratio (European benchmark: 3% of CAPEX/yr)
    """
    sector  = proj_financials.get("sector", "").lower()
    inv_usd = float(proj_financials.get("investment_usd", 0))

    if "health" in sector:
        multiplier    = float(proj_financials.get("multiplier_benchmark", 2.0))
        operating_margin = 0.08
        return round(inv_usd * multiplier * operating_margin, 2)

    elif sector == "energy":
        co2_tons = float(proj_financials.get("avoided_co2_tons", 0))
        carbon_value = co2_tons * SOCIAL_COST_CARBON_USD_PER_TON
        # Capacity revenue: refurb CAPEX/kW × capacity × dispatch hours
        capex_per_kw = 1000
        capacity_kw  = inv_usd / capex_per_kw
        hours_yr     = 4500          # ~51% capacity factor
        price_kwh    = 0.06          # USD/kWh average PPA
        capacity_rev = capacity_kw * hours_yr * price_kwh
        return round(carbon_value + capacity_rev, 2)

    elif sector == "transport" or "rail" in sector:
        capex = float(proj_financials.get("capex_eur", inv_usd * 0.92))
        toll_ratio = 0.03
        return round(capex * toll_ratio, 2)

    # Fallback: 10% return on investment
    return round(inv_usd * 0.10, 2)


# ---------------------------------------------------------------------------
# Aggregation functions
# ---------------------------------------------------------------------------

def build_financials(
    projects_raw: list[dict],
    wwf_results: list,          # list of RiskFilterResult from wwf_risk_filter
    assumptions: dict,
) -> list[ProjectFinancials]:
    """Merge raw project data with WWF scores into ProjectFinancials."""
    wwf_map = {r.project_id: r for r in wwf_results}
    financials = []

    for proj in projects_raw:
        pid     = proj["project_id"]
        wwf_res = wwf_map.get(pid)
        wrf_c   = wwf_res.wrf.composite if wwf_res else 0.0
        brf_c   = wwf_res.brf.composite if wwf_res else 0.0

        rev = _derive_revenue_proxy(proj, assumptions)

        financials.append(ProjectFinancials(
            project_id=        pid,
            region=            proj.get("region", "unknown"),
            sector=            proj.get("sector", proj.get("sector_code", "unknown")),
            investment_usd=    float(proj.get("investment_usd", proj.get("est_investment_usd",
                               proj.get("est_capex_eur", 0)))),
            revenue_proxy_usd= rev,
            wrf_composite=     wrf_c,
            brf_composite=     brf_c,
            avoided_co2_tons=  proj.get("avoided_co2_tons"),
            beneficiaries=     proj.get("beneficiaries"),
            capex_eur=         proj.get("capex_eur"),
        ))
    return financials


def calculate_revenue_at_risk(
    financials: list[ProjectFinancials],
    mode: str = "binary",
) -> tuple[float, float]:
    """
    Calculate Revenue-at-Risk.
    mode='binary'   : RaR = sum of revenue where risk_flag is True
    mode='weighted' : RaR = sum(revenue × risk_intensity / 5)

    Returns (revenue_at_risk_usd, high_risk_share_of_total_investment).
    """
    total_investment = sum(p.investment_usd for p in financials)
    high_risk_investment = sum(
        p.investment_usd for p in financials if p.risk_flag
    )

    if mode == "binary":
        rar = sum(p.revenue_proxy_usd for p in financials if p.risk_flag)
    else:  # weighted
        rar = sum(
            p.revenue_proxy_usd * (p.risk_intensity / 5.0)
            for p in financials
        )

    share = high_risk_investment / total_investment if total_investment else 0.0
    return round(rar, 2), round(share, 4)


def calculate_portfolio_itr(financials: list[ProjectFinancials]) -> float:
    """
    Weighted-average Implied Temperature Rise for the portfolio.
    Weights by investment size. Non-hydro projects get BAU temperature.
    """
    total_weight = sum(p.investment_usd for p in financials)
    if total_weight == 0:
        return BUSINESS_AS_USUAL_TEMP_RISE

    weighted_itr = 0.0
    for p in financials:
        weight = p.investment_usd / total_weight
        if p.avoided_co2_tons and p.avoided_co2_tons > 0:
            # Fraction of regional BAU emissions displaced (normalised to 1M tons)
            fraction = min(1.0, p.avoided_co2_tons / 1_000_000)
            itr = _implied_temperature_rise(fraction)
        else:
            itr = BUSINESS_AS_USUAL_TEMP_RISE
        weighted_itr += weight * itr

    return round(weighted_itr, 2)


def build_dependency_heatmap(encore_profiles: list[dict]) -> dict[str, dict]:
    """
    Aggregate ENCORE ratings across all projects into a portfolio heatmap.
    Returns {ecosystem_service: {max_dep, mean_dep, n_material, projects_affected}}.
    """
    heatmap: dict[str, list] = {}

    for proj in encore_profiles:
        pid = proj["project_id"]
        for row in proj.get("materiality_table", []):
            svc = row["ecosystem_service"]
            if svc not in heatmap:
                heatmap[svc] = []
            heatmap[svc].append({
                "project_id":        pid,
                "dependency_score":  row["dependency_score"],
                "impact_score":      row["impact_score"],
                "material":          row["material"],
            })

    summary = {}
    for svc, entries in heatmap.items():
        dep_scores = [e["dependency_score"] for e in entries]
        summary[svc] = {
            "max_dependency_score":  max(dep_scores),
            "mean_dependency_score": round(sum(dep_scores) / len(dep_scores), 2),
            "n_material_projects":   sum(1 for e in entries if e["material"]),
            "projects_affected":     [e["project_id"] for e in entries if e["material"]],
        }

    return dict(sorted(
        summary.items(),
        key=lambda x: x[1]["max_dependency_score"],
        reverse=True,
    ))


def build_stress_test_table(
    financials: list[ProjectFinancials],
    encore_profiles: list[dict],
    wwf_results: list,
) -> list[dict]:
    """
    TNFD LEAP-aligned stress test table (Evaluate phase output).
    One row per project summarising dependency exposure, risk scores,
    revenue at risk, and model coverage.
    """
    wwf_map  = {r.project_id: r for r in wwf_results}
    enc_map  = {p["project_id"]: p for p in encore_profiles}

    table = []
    for pf in financials:
        pid = pf.project_id
        wwf = wwf_map.get(pid)
        enc = enc_map.get(pid, {})

        table.append({
            "project_id":              pid,
            "region":                  pf.region,
            "sector":                  pf.sector,
            "investment_usd_m":        round(pf.investment_usd / 1e6, 2),
            "revenue_proxy_usd_m":     round(pf.revenue_proxy_usd / 1e6, 2),
            "encore_n_material":       enc.get("n_material_services", 0),
            "top_dependency":          enc.get("high_dependency_services", [None])[0],
            "top_impact":              enc.get("high_impact_services", [None])[0],
            "wrf_composite":           wwf.wrf.composite if wwf else "N/A",
            "brf_composite":           wwf.brf.composite if wwf else "N/A",
            "wrf_high_risk":           wwf.wrf.high_risk  if wwf else False,
            "brf_high_risk":           wwf.brf.high_risk  if wwf else False,
            "overall_high_risk":       pf.risk_flag,
            "revenue_at_risk_usd_m":   round(pf.revenue_proxy_usd / 1e6, 2)
                                        if pf.risk_flag else 0.0,
            "invest_models_required":  _models_required(pf.sector),
        })

    return table


def _models_required(sector: str) -> list[str]:
    sector = sector.lower()
    if "health" in sector:
        return ["ndr (water quality)", "urban_flood_risk_mitigation"]
    elif "energy" in sector:
        return ["hydropower_water_yield", "sdr (sediment delivery)"]
    elif "rail" in sector or "transport" in sector:
        return ["habitat_quality", "carbon_storage"]
    return ["tbd"]


def aggregate_portfolio(
    projects_raw: list[dict],
    wwf_results: list,
    encore_profiles: list[dict],
    assumptions: dict,
    rar_mode: str = "binary",
) -> PortfolioReport:
    """Top-level aggregation function that returns a PortfolioReport."""
    financials = build_financials(projects_raw, wwf_results, assumptions)
    rar, high_risk_share = calculate_revenue_at_risk(financials, mode=rar_mode)
    portfolio_itr = calculate_portfolio_itr(financials)
    heatmap = build_dependency_heatmap(encore_profiles)
    stress_table = build_stress_test_table(financials, encore_profiles, wwf_results)

    return PortfolioReport(
        projects=             financials,
        total_investment_usd= sum(p.investment_usd for p in financials),
        revenue_at_risk_usd=  rar,
        high_risk_share=      high_risk_share,
        weighted_itr=         portfolio_itr,
        dependency_summary=   heatmap,
        stress_test_table=    stress_table,
    )
