"""
Stage 2 – ENCORE Materiality Screening

Embeds the ENCORE dependency and impact materiality matrix for the three
ISIC sectors present in the portfolio.  Ratings follow the 2024 ENCORE
five-point scale:
  VH = Very High  (5)
  H  = High       (4)
  M  = Medium     (3)
  L  = Low        (2)
  VL = Very Low   (1)
  0  = Not Relevant / No Pathway

Source: ENCORE v2024 methodology, UNEP-WCMC / UNEP FI / Global Canopy.
The ratings below are derived from published ENCORE sector profiles for
Q86, D3510, and H4910.

API equivalent:
  GET /api/v1/materiality?sector=<encore_sector_key>
  Header: X-Authentication-Token: <token>
"""

from __future__ import annotations
from dataclasses import dataclass, field

RATING_SCALE = {"VH": 5, "H": 4, "M": 3, "L": 2, "VL": 1, "N": 0}
LABEL_SCALE  = {v: k for k, v in RATING_SCALE.items()}

# ---------------------------------------------------------------------------
# 21 ENCORE Ecosystem Services
# ---------------------------------------------------------------------------
ECOSYSTEM_SERVICES = [
    "water_supply",
    "ground_water",
    "water_flow_regulation",
    "flood_and_storm_protection",
    "erosion_control",
    "soil_quality",
    "pollination",
    "pest_and_disease_control",
    "air_quality_regulation",
    "climate_regulation",
    "noise_attenuation",
    "animal_fibres_materials",
    "plant_fibres_materials",
    "genetic_materials",
    "mediation_of_solid_waste",
    "mediation_of_liquid_waste",
    "mediation_of_gaseous_waste",
    "marine_and_freshwater_goods",
    "terrestrial_ecosystem_use",
    "freshwater_ecosystem_use",
    "marine_ecosystem_use",
]

# ---------------------------------------------------------------------------
# Materiality Matrix
# Keys: encore_sector_key → ecosystem_service → (dependency_rating, impact_rating)
# ---------------------------------------------------------------------------
MATERIALITY_MATRIX: dict[str, dict[str, tuple[str, str]]] = {

    # ------------------------------------------------------------------
    # Q86 – Human Health Activities
    # Dependencies: clean water (sterilisation, cooling towers, HVAC),
    #   air quality (patient outcomes, infection control),
    #   climate regulation (heat-health burden), genetic materials (pharma R&D).
    # Impacts: liquid-waste discharge (pharmaceuticals, pathogens),
    #   solid-waste (medical/sharps), land use for facility footprint.
    # ------------------------------------------------------------------
    "human_health_activities": {
        "water_supply":              ("VH", "M"),  # sterilisation, cooling, laundry
        "ground_water":              ("M",  "L"),
        "water_flow_regulation":     ("L",  "L"),
        "flood_and_storm_protection":("M",  "N"),  # infrastructure resilience
        "erosion_control":           ("L",  "L"),
        "soil_quality":              ("L",  "N"),
        "pollination":               ("N",  "N"),
        "pest_and_disease_control":  ("M",  "L"),  # vector-borne disease exposure
        "air_quality_regulation":    ("H",  "M"),  # patient respiratory outcomes
        "climate_regulation":        ("H",  "L"),  # heat stress / disease burden
        "noise_attenuation":         ("L",  "N"),
        "animal_fibres_materials":   ("L",  "N"),
        "plant_fibres_materials":    ("L",  "N"),
        "genetic_materials":         ("H",  "N"),  # pharmaceutical feedstock
        "mediation_of_solid_waste":  ("N",  "H"),  # medical/sharps waste generated
        "mediation_of_liquid_waste": ("N",  "VH"), # pharmaceutical effluent
        "mediation_of_gaseous_waste":("N",  "M"),  # anaesthetic gases, incinerators
        "marine_and_freshwater_goods":("N", "N"),
        "terrestrial_ecosystem_use": ("L",  "M"),  # facility land footprint
        "freshwater_ecosystem_use":  ("M",  "M"),
        "marine_ecosystem_use":      ("N",  "N"),
    },

    # ------------------------------------------------------------------
    # D3510 – Electric Power Generation (Hydroelectric)
    # Dependencies: water supply and flow regulation are CRITICAL —
    #   generation volume is directly proportional to river discharge.
    #   Climate regulation affects precipitation patterns.
    # Impacts: significant river fragmentation (dams), sediment disruption,
    #   freshwater ecosystem alteration.
    # ------------------------------------------------------------------
    "electric_power_generation_hydro": {
        "water_supply":              ("VH", "VH"), # intake volume is the product
        "ground_water":              ("M",  "L"),
        "water_flow_regulation":     ("VH", "VH"), # dam alters downstream flow
        "flood_and_storm_protection":("H",  "H"),  # reservoir changes flood regime
        "erosion_control":           ("M",  "H"),  # sediment trapping behind dam
        "soil_quality":              ("L",  "M"),  # reservoir inundation
        "pollination":               ("N",  "N"),
        "pest_and_disease_control":  ("L",  "M"),  # stagnant water → vectors
        "air_quality_regulation":    ("L",  "N"),
        "climate_regulation":        ("VH", "M"),  # rainfall variability = output risk
        "noise_attenuation":         ("N",  "L"),
        "animal_fibres_materials":   ("N",  "N"),
        "plant_fibres_materials":    ("N",  "N"),
        "genetic_materials":         ("N",  "N"),
        "mediation_of_solid_waste":  ("N",  "M"),  # construction waste
        "mediation_of_liquid_waste": ("N",  "M"),  # turbine lubricants
        "mediation_of_gaseous_waste":("N",  "N"),
        "marine_and_freshwater_goods":("M", "VH"), # fish passage blockage
        "terrestrial_ecosystem_use": ("M",  "H"),  # reservoir inundation area
        "freshwater_ecosystem_use":  ("VH", "VH"), # core operational medium
        "marine_ecosystem_use":      ("L",  "M"),  # altered river mouth sediment
    },

    # ------------------------------------------------------------------
    # H4910 – Passenger Rail Transport (Electrified, interurban)
    # Dependencies: land stability (earthworks, embankments),
    #   flood & storm protection (track washouts), climate regulation.
    #   Electrified rail has low direct water/air dependency.
    # Impacts: land fragmentation, noise, habitat corridors bisected.
    # ------------------------------------------------------------------
    "rail_transport": {
        "water_supply":              ("L",  "L"),
        "ground_water":              ("L",  "M"),  # tunnel dewatering
        "water_flow_regulation":     ("M",  "M"),  # bridges, culverts alter flow
        "flood_and_storm_protection":("H",  "N"),  # track washouts = service loss
        "erosion_control":           ("H",  "M"),  # embankment stability
        "soil_quality":              ("M",  "M"),  # contaminated ballast
        "pollination":               ("N",  "N"),
        "pest_and_disease_control":  ("L",  "N"),
        "air_quality_regulation":    ("M",  "N"),  # passengers benefit; low impact
        "climate_regulation":        ("M",  "N"),  # heat track buckling risk
        "noise_attenuation":         ("L",  "H"),  # rail noise a significant impact
        "animal_fibres_materials":   ("N",  "N"),
        "plant_fibres_materials":    ("N",  "N"),
        "genetic_materials":         ("N",  "N"),
        "mediation_of_solid_waste":  ("N",  "M"),  # maintenance waste
        "mediation_of_liquid_waste": ("N",  "M"),  # depot wash water
        "mediation_of_gaseous_waste":("N",  "L"),  # brake dust (mostly electric)
        "marine_and_freshwater_goods":("N", "N"),
        "terrestrial_ecosystem_use": ("M",  "VH"), # permanent land take / corridor
        "freshwater_ecosystem_use":  ("M",  "M"),
        "marine_ecosystem_use":      ("N",  "N"),
    },
}


@dataclass
class MaterialityProfile:
    """Full materiality profile for one sector."""
    sector_key: str
    ratings: dict[str, dict[str, int]] = field(default_factory=dict)
    high_dependency_services: list[str] = field(default_factory=list)
    high_impact_services: list[str] = field(default_factory=list)

    def summary_table(self) -> list[dict]:
        rows = []
        for svc, scores in self.ratings.items():
            dep_score = scores["dependency_score"]
            imp_score = scores["impact_score"]
            rows.append({
                "ecosystem_service": svc,
                "dependency_rating": LABEL_SCALE.get(dep_score, "N"),
                "dependency_score":  dep_score,
                "impact_rating":     LABEL_SCALE.get(imp_score, "N"),
                "impact_score":      imp_score,
                "material":          dep_score >= 4 or imp_score >= 4,
            })
        return sorted(rows, key=lambda r: r["dependency_score"] + r["impact_score"], reverse=True)


def get_materiality_profile(encore_sector_key: str) -> MaterialityProfile:
    """
    Return a MaterialityProfile for the given sector.
    Raises KeyError if sector is not in the embedded matrix.
    """
    if encore_sector_key not in MATERIALITY_MATRIX:
        raise KeyError(
            f"Sector '{encore_sector_key}' not in embedded ENCORE matrix. "
            "Available: " + ", ".join(MATERIALITY_MATRIX.keys())
        )

    raw = MATERIALITY_MATRIX[encore_sector_key]
    profile = MaterialityProfile(sector_key=encore_sector_key)

    for svc in ECOSYSTEM_SERVICES:
        dep_label, imp_label = raw.get(svc, ("N", "N"))
        dep_score = RATING_SCALE[dep_label]
        imp_score = RATING_SCALE[imp_label]
        profile.ratings[svc] = {
            "dependency_rating": dep_label,
            "dependency_score":  dep_score,
            "impact_rating":     imp_label,
            "impact_score":      imp_score,
        }
        if dep_score >= 4:
            profile.high_dependency_services.append(svc)
        if imp_score >= 4:
            profile.high_impact_services.append(svc)

    return profile


def screen_portfolio(projects: list[dict]) -> list[dict]:
    """
    Apply ENCORE screening to a list of project dicts.
    Each dict must have keys: project_id, encore_sector.
    Returns projects enriched with materiality metadata.
    """
    results = []
    for proj in projects:
        profile = get_materiality_profile(proj["encore_sector"])
        results.append({
            **proj,
            "high_dependency_services": profile.high_dependency_services,
            "high_impact_services":     profile.high_impact_services,
            "materiality_table":        profile.summary_table(),
            "n_material_services":      sum(
                1 for r in profile.summary_table() if r["material"]
            ),
        })
    return results
