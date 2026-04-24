"""
Stage 3 – WWF Risk Filter Suite scoring

Implements a Python representation of the Water Risk Filter (WRF) and
Biodiversity Risk Filter (BRF) indicator logic.

Architecture follows the document:
  WRF: 32 basin indicators → Physical / Regulatory / Reputational
  BRF: 33 indicators       → Scape Risk (Landscape + Seascape)

For each project we assign scores based on:
  1. The project's region (mapped to representative basin conditions)
  2. The project's sector (some indicators are sector-sensitive)

Scores are on the 1–5 WWF scale; >3.4 = "High Risk".

Reference datasets embedded here are representative regional defaults
for the three regions in the portfolio (Africa, Asia, Europe, LATAM).
In a production deployment these would be fetched from the WWF API or
pre-downloaded GeoTIFFs intersected with asset coordinates.
"""

from __future__ import annotations
from dataclasses import dataclass, field

HIGH_RISK_THRESHOLD = 3.4

# ---------------------------------------------------------------------------
# Representative basin-level indicator scores by region
# Source: WWF WRF/BRF global dataset regional aggregates (illustrative)
# Each tuple: (WRF_physical, WRF_regulatory, WRF_reputational,
#              BRF_species, BRF_ecosystem, BRF_protected_areas)
# ---------------------------------------------------------------------------
REGIONAL_BASELINES: dict[str, dict] = {
    "africa": {
        # Sub-Saharan / East African context: high physical water stress,
        # weak regulatory frameworks, elevated biodiversity sensitivity
        "wrf": {
            "physical": {
                "baseline_water_stress":        4.2,  # High (arid/semi-arid belts)
                "blue_water_scarcity":          4.0,
                "interannual_variability":       4.5,  # Seasonal rivers
                "seasonal_variability":          4.5,
                "flood_occurrence":              3.8,
                "drought_severity":              4.3,
                "upstream_storage_capacity":     2.5,
                "groundwater_depletion":         3.6,
                "aridity_index":                 3.9,
                "sediment_load_ratio":           3.2,
                "threatened_amphibians":         4.0,
                "freshwater_biodiversity":       4.2,
            },
            "regulatory": {
                "regulatory_framework_strength": 2.1,  # Weak
                "sdg6_score":                    2.3,
                "water_related_conflict":        3.8,
                "access_to_water":               3.0,
            },
            "reputational": {
                "media_coverage_water":          2.8,
                "stakeholder_sensitivity":       3.5,
            },
        },
        "brf": {
            "species_threat": {
                "iucn_threatened_species_density": 4.3,
                "mammal_richness":                  3.8,
                "bird_richness":                    4.0,
                "reptile_richness":                 3.6,
                "freshwater_fish_richness":         4.1,
            },
            "ecosystem_intactness": {
                "biodiversity_intactness_index":    3.2,
                "forest_loss_rate":                 3.5,
                "habitat_fragmentation":            3.8,
                "invasive_species_pressure":        2.9,
            },
            "protected_areas": {
                "protected_area_proximity":         3.5,
                "key_biodiversity_area_overlap":    3.8,
                "ramsar_wetland_proximity":         2.8,
            },
        },
    },
    "asia": {
        # South/Southeast Asia hydro corridor: extreme seasonal variability,
        # high downstream population dependency, rich freshwater biodiversity
        "wrf": {
            "physical": {
                "baseline_water_stress":        3.5,
                "blue_water_scarcity":          3.8,
                "interannual_variability":       4.8,  # Monsoon dependent
                "seasonal_variability":          4.9,
                "flood_occurrence":              4.5,
                "drought_severity":              3.7,
                "upstream_storage_capacity":     4.2,
                "groundwater_depletion":         4.0,
                "aridity_index":                 2.8,
                "sediment_load_ratio":           4.5,  # High sediment rivers
                "threatened_amphibians":         4.2,
                "freshwater_biodiversity":       4.8,
            },
            "regulatory": {
                "regulatory_framework_strength": 2.8,
                "sdg6_score":                    3.0,
                "water_related_conflict":        3.2,
                "access_to_water":               3.5,
            },
            "reputational": {
                "media_coverage_water":          3.5,
                "stakeholder_sensitivity":       4.0,
            },
        },
        "brf": {
            "species_threat": {
                "iucn_threatened_species_density": 4.5,
                "mammal_richness":                  4.0,
                "bird_richness":                    4.3,
                "reptile_richness":                 4.1,
                "freshwater_fish_richness":         4.8,
            },
            "ecosystem_intactness": {
                "biodiversity_intactness_index":    2.8,
                "forest_loss_rate":                 4.2,
                "habitat_fragmentation":            4.0,
                "invasive_species_pressure":        3.2,
            },
            "protected_areas": {
                "protected_area_proximity":         4.0,
                "key_biodiversity_area_overlap":    4.2,
                "ramsar_wetland_proximity":         4.0,
            },
        },
    },
    "europe": {
        # Western/Central Europe: regulated basins, high reputational risk,
        # moderately impacted but legally protected ecosystems
        "wrf": {
            "physical": {
                "baseline_water_stress":        2.8,
                "blue_water_scarcity":          2.5,
                "interannual_variability":       2.3,
                "seasonal_variability":          2.4,
                "flood_occurrence":              2.9,
                "drought_severity":              2.7,
                "upstream_storage_capacity":     3.8,  # Heavily dammed
                "groundwater_depletion":         2.2,
                "aridity_index":                 1.8,
                "sediment_load_ratio":           2.5,
                "threatened_amphibians":         3.0,
                "freshwater_biodiversity":       2.8,
            },
            "regulatory": {
                "regulatory_framework_strength": 4.5,  # EU WFD, GDPR for infra data
                "sdg6_score":                    4.2,
                "water_related_conflict":        1.5,
                "access_to_water":               4.8,
            },
            "reputational": {
                "media_coverage_water":          3.8,  # High civil society scrutiny
                "stakeholder_sensitivity":       4.2,
            },
        },
        "brf": {
            "species_threat": {
                "iucn_threatened_species_density": 2.5,
                "mammal_richness":                  2.2,
                "bird_richness":                    2.8,
                "reptile_richness":                 2.3,
                "freshwater_fish_richness":         3.0,
            },
            "ecosystem_intactness": {
                "biodiversity_intactness_index":    3.5,  # Long-modified landscapes
                "forest_loss_rate":                 1.8,
                "habitat_fragmentation":            3.8,  # Dense infrastructure
                "invasive_species_pressure":        3.0,
            },
            "protected_areas": {
                "protected_area_proximity":         4.0,  # Natura 2000 dense network
                "key_biodiversity_area_overlap":    3.5,
                "ramsar_wetland_proximity":         3.2,
            },
        },
    },
    "latam": {
        # Latin America: high biodiversity, variable water stress by sub-region,
        # emerging regulatory landscape
        "wrf": {
            "physical": {
                "baseline_water_stress":        3.0,
                "blue_water_scarcity":          3.2,
                "interannual_variability":       4.0,  # ENSO driven
                "seasonal_variability":          4.2,
                "flood_occurrence":              3.5,
                "drought_severity":              3.3,
                "upstream_storage_capacity":     3.5,
                "groundwater_depletion":         3.0,
                "aridity_index":                 3.0,
                "sediment_load_ratio":           3.5,
                "threatened_amphibians":         4.5,  # Hotspot
                "freshwater_biodiversity":       4.6,
            },
            "regulatory": {
                "regulatory_framework_strength": 2.5,
                "sdg6_score":                    2.8,
                "water_related_conflict":        3.0,
                "access_to_water":               3.2,
            },
            "reputational": {
                "media_coverage_water":          3.2,
                "stakeholder_sensitivity":       4.0,
            },
        },
        "brf": {
            "species_threat": {
                "iucn_threatened_species_density": 4.8,
                "mammal_richness":                  4.5,
                "bird_richness":                    4.9,
                "reptile_richness":                 4.6,
                "freshwater_fish_richness":         4.9,
            },
            "ecosystem_intactness": {
                "biodiversity_intactness_index":    3.0,
                "forest_loss_rate":                 4.5,
                "habitat_fragmentation":            3.8,
                "invasive_species_pressure":        2.5,
            },
            "protected_areas": {
                "protected_area_proximity":         3.8,
                "key_biodiversity_area_overlap":    4.5,
                "ramsar_wetland_proximity":         3.5,
            },
        },
    },
}

# Sector-specific sensitivity multipliers applied on top of regional baselines
# Values > 1.0 amplify risk for sectors with higher physical dependency
SECTOR_SENSITIVITY: dict[str, dict] = {
    "electric_power_generation_hydro": {
        "wrf_physical": 1.20,   # Generation directly tied to basin hydrology
        "wrf_regulatory": 1.10,
        "brf_freshwater": 1.25, # Dams have outsized freshwater biodiversity impact
    },
    "human_health_activities": {
        "wrf_physical": 1.05,   # Water quality matters for clinical operations
        "wrf_regulatory": 1.00,
        "brf_freshwater": 1.00,
    },
    "rail_transport": {
        "wrf_physical": 1.10,   # Flood/erosion risk to infrastructure
        "wrf_regulatory": 1.00,
        "brf_freshwater": 1.00,
        "brf_terrestrial": 1.15, # Corridor land take
    },
}


@dataclass
class WRFScore:
    physical: float
    regulatory: float
    reputational: float
    composite: float
    high_risk: bool
    indicator_details: dict = field(default_factory=dict)


@dataclass
class BRFScore:
    species_threat: float
    ecosystem_intactness: float
    protected_areas: float
    composite: float
    high_risk: bool
    indicator_details: dict = field(default_factory=dict)


@dataclass
class RiskFilterResult:
    project_id: str
    region: str
    sector_key: str
    wrf: WRFScore
    brf: BRFScore
    overall_high_risk: bool


def _mean(values: dict) -> float:
    v = list(values.values())
    return round(sum(v) / len(v), 3) if v else 0.0


def _apply_sensitivity(score: float, multiplier: float) -> float:
    """Cap at 5.0 after applying sector multiplier."""
    return min(5.0, round(score * multiplier, 3))


def score_project(project_id: str, region: str, encore_sector: str) -> RiskFilterResult:
    """
    Score a single project using WWF WRF + BRF logic.

    Parameters
    ----------
    project_id   : portfolio identifier
    region       : one of africa, asia, europe, latam
    encore_sector: ENCORE sector key (from sector_mapper)
    """
    region_key = region.lower()
    if region_key not in REGIONAL_BASELINES:
        raise ValueError(
            f"Region '{region}' not in baselines. "
            "Available: " + ", ".join(REGIONAL_BASELINES.keys())
        )

    baseline = REGIONAL_BASELINES[region_key]
    sens = SECTOR_SENSITIVITY.get(encore_sector, {})

    # --- WRF ---
    phys_raw  = _mean(baseline["wrf"]["physical"])
    reg_raw   = _mean(baseline["wrf"]["regulatory"])
    rep_raw   = _mean(baseline["wrf"]["reputational"])

    phys  = _apply_sensitivity(phys_raw,  sens.get("wrf_physical",    1.0))
    reg   = _apply_sensitivity(reg_raw,   sens.get("wrf_regulatory",  1.0))
    rep   = _apply_sensitivity(rep_raw,   1.0)

    wrf_composite = round((phys * 0.5 + reg * 0.3 + rep * 0.2), 3)

    wrf = WRFScore(
        physical=phys,
        regulatory=reg,
        reputational=rep,
        composite=wrf_composite,
        high_risk=wrf_composite > HIGH_RISK_THRESHOLD,
        indicator_details={
            "physical_indicators": baseline["wrf"]["physical"],
            "regulatory_indicators": baseline["wrf"]["regulatory"],
            "reputational_indicators": baseline["wrf"]["reputational"],
        },
    )

    # --- BRF ---
    sp_raw  = _mean(baseline["brf"]["species_threat"])
    eco_raw = _mean(baseline["brf"]["ecosystem_intactness"])
    pa_raw  = _mean(baseline["brf"]["protected_areas"])

    sp   = _apply_sensitivity(sp_raw,  sens.get("brf_freshwater", 1.0))
    eco  = _apply_sensitivity(eco_raw, sens.get("brf_terrestrial", 1.0))
    pa   = pa_raw

    brf_composite = round((sp * 0.4 + eco * 0.35 + pa * 0.25), 3)

    brf = BRFScore(
        species_threat=sp,
        ecosystem_intactness=eco,
        protected_areas=pa,
        composite=brf_composite,
        high_risk=brf_composite > HIGH_RISK_THRESHOLD,
        indicator_details={
            "species_threat_indicators": baseline["brf"]["species_threat"],
            "ecosystem_intactness_indicators": baseline["brf"]["ecosystem_intactness"],
            "protected_areas_indicators": baseline["brf"]["protected_areas"],
        },
    )

    return RiskFilterResult(
        project_id=project_id,
        region=region,
        sector_key=encore_sector,
        wrf=wrf,
        brf=brf,
        overall_high_risk=wrf.high_risk or brf.high_risk,
    )


def score_portfolio(projects: list[dict]) -> list[RiskFilterResult]:
    """
    Score a list of project dicts.
    Each dict must have: project_id, region, encore_sector.
    """
    return [
        score_project(p["project_id"], p["region"], p["encore_sector"])
        for p in projects
    ]
