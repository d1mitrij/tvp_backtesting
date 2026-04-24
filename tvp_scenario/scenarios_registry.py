"""
scenarios_registry.py — S4 Shared Scenario and Damage-Model Registry
=====================================================================
Single source of truth for:

  1. SSP scenario metadata       — IAMC labels, RCP, narrative, SCC base values
  2. SCC growth parameters       — DICE-2023R discount-rate calibration
  3. Named damage models         — sector weights for GIVE, FUND, META-2021, DICE
  4. Scenario ordering constants — SCENARIO_ORDER, ANALYSIS_YEARS

All three simulation frameworks (OSeMOSYS, GCAM, MESSAGEix) import their
shared scenario metadata from here so that label changes propagate once.
The SCC damage analysis (scc_damage_analysis.py) imports DAMAGE_MODELS and
SCC parameters from here.

Usage
-----
    from scenarios_registry import SSP_REGISTRY, DAMAGE_MODELS, SCC_BASE
    meta = SSP_REGISTRY["ssp1"]          # iamc_label, rcp, description, ...
    weights = DAMAGE_MODELS["GIVE"]      # sector-weight dict
    base_scc = SCC_BASE["SSP2-4.5"]     # USD / tCO2 in 2020

Framework-specific parameters (GCAM XML policy values, MESSAGEix R11 node
mappings, OSeMOSYS YAML paths) remain in each framework's run_simulation.py.
"""

from __future__ import annotations

# ── Analysis time horizon ─────────────────────────────────────────────────────
ANALYSIS_YEARS: list[int] = [2020, 2025, 2030, 2035, 2040, 2045]

# ── Canonical SSP scenario metadata ──────────────────────────────────────────
# All three simulation frameworks read iamc_label, description, and rcp from
# here.  scc_base_usd_t and warming_target_c drive the damage analysis layer.
#
# SCC base values: IPCC AR6 WG3 Chapter 2 synthesis, calibrated to SSP warming
# trajectories (real 2020 USD/tCO2).
#   SSP1-1.9   $130/t  — steep early mitigation caps future exposure
#   SSP2-4.5   $190/t  — central US EPA (2023) estimate
#   SSP3-7.0   $310/t  — high warming → convex damage acceleration
#   SSP4-6.0   $260/t  — regional inequality amplifies vulnerability in poor regions
#   SSP5-8.5   $420/t  — highest warming; tail-risk damages dominant
SSP_REGISTRY: dict[str, dict] = {
    "ssp1": {
        "iamc_label":       "SSP1-1.9",
        "description":      "Sustainability — 1.5 °C pathway",
        "rcp":              "1.9",
        "warming_target_c": 1.5,
        "scc_base_usd_t":   130.0,
    },
    "ssp2": {
        "iamc_label":       "SSP2-4.5",
        "description":      "Middle of the Road — ~2 °C pathway",
        "rcp":              "4.5",
        "warming_target_c": 2.0,
        "scc_base_usd_t":   190.0,
    },
    "ssp3": {
        "iamc_label":       "SSP3-7.0",
        "description":      "Regional Rivalry — 3–4 °C pathway",
        "rcp":              "7.0",
        "warming_target_c": 3.5,
        "scc_base_usd_t":   310.0,
    },
    "ssp4": {
        "iamc_label":       "SSP4-6.0",
        "description":      "Inequality — polarised 3 °C pathway",
        "rcp":              "6.0",
        "warming_target_c": 3.0,
        "scc_base_usd_t":   260.0,
    },
    "ssp5": {
        "iamc_label":       "SSP5-8.5",
        "description":      "Fossil-Fueled Development — 4–5 °C pathway",
        "rcp":              "8.5",
        "warming_target_c": 4.5,
        "scc_base_usd_t":   420.0,
    },
}

# Ordered list of IAMC scenario labels (used for consistent pivot ordering)
SCENARIO_ORDER: list[str] = [m["iamc_label"] for m in SSP_REGISTRY.values()]

# ── SCC growth parameters ─────────────────────────────────────────────────────
# Real growth rate per year, anchored to DICE-2023R at 2.5 % discount rate.
SCC_BASE: dict[str, float] = {
    m["iamc_label"]: m["scc_base_usd_t"] for m in SSP_REGISTRY.values()
}
SCC_GROWTH_RATE: float = 0.025    # 2.5 %/yr
SCC_BASE_YEAR:   int   = 2020

# ── Named damage models — sector weights ─────────────────────────────────────
# Each entry maps damage-category name → fraction of total SCC allocated to
# that category.  Weights must sum to 1.0 for each model (asserted below).
#
# Sources
# -------
#   GIVE      — Rennert et al. (2022) Nature 610:687–692.  Sector-resolved
#               Monte Carlo damage functions; sector shares from Table ED1.
#               Mortality (→ Human Health) and amenity (→ Ecosystems)
#               dominate; Water Resources not separately modelled.
#
#   FUND      — Anthoff & Tol, FUND 3.9 (2014).  Six-sector reduced-form
#               model; most widely used pre-AR6 reference; calibrated against
#               AR6 WG2 Ch. 16 sector attribution.
#
#   META-2021 — Dietz et al. (2021) Nature Climate Change 11:557–564.
#               Meta-analytic damage function combining Burke et al.
#               agriculture, Carleton et al. mortality, and tipping-point
#               amplification.  Weights from Table 1 attribution.
#
#   DICE-2023R — Nordhaus (2023).  Single-sector quadratic reduced-form;
#                sector proxies derived from WG2 Ch. 16 attribution table.
DAMAGE_MODELS: dict[str, dict[str, float]] = {
    "GIVE": {
        "Agriculture":      0.10,
        "Human Health":     0.37,
        "Water Resources":  0.00,
        "Coastal / SLR":    0.10,
        "Ecosystems":       0.37,
        "Energy Systems":   0.06,
        "Other":            0.00,
    },
    "FUND": {
        "Agriculture":      0.17,
        "Human Health":     0.28,
        "Water Resources":  0.16,
        "Coastal / SLR":    0.11,
        "Ecosystems":       0.13,
        "Energy Systems":   0.10,
        "Other":            0.05,
    },
    "META-2021": {
        "Agriculture":      0.20,
        "Human Health":     0.32,
        "Water Resources":  0.12,
        "Coastal / SLR":    0.08,
        "Ecosystems":       0.15,
        "Energy Systems":   0.08,
        "Other":            0.05,
    },
    "DICE-2023R": {
        "Agriculture":      0.20,
        "Human Health":     0.30,
        "Water Resources":  0.15,
        "Coastal / SLR":    0.05,
        "Ecosystems":       0.15,
        "Energy Systems":   0.10,
        "Other":            0.05,
    },
}

for _model, _w in DAMAGE_MODELS.items():
    assert abs(sum(_w.values()) - 1.0) < 1e-9, f"DAMAGE_MODELS[{_model!r}] does not sum to 1"
