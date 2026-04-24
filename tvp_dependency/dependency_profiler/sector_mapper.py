"""
Stage 1 – Sector mapping: translates project-level sector codes
(custom, NACE, or GICS-style) to ISIC Rev.4 codes used by ENCORE
and to WWF Risk Filter industry categories.

Supported source systems:
  - Internal codes  (Health_Social, Health_Specialized, Health_General, Energy, Transport)
  - NACE 4-digit (e.g. "86.10", "35.11", "49.10")
  - ISIC Rev.4 directly

ENCORE sectors represented here are those relevant to the three
project types in the modeled_input_data folder:
  Q86  – Human health activities (hospitals)
  D35  – Electricity, gas, steam supply (hydro power)
  H49  – Land transport (rail)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Internal code → (ISIC_code, ISIC_label, ENCORE_sector_key, WWF_industry)
# ---------------------------------------------------------------------------
INTERNAL_CODE_MAP: dict[str, dict] = {
    # Health sector variants
    "health_social": {
        "isic": "Q86",
        "isic_label": "Human health activities – primary/preventive care",
        "encore_sector": "human_health_activities",
        "wwf_industry": "Healthcare",
        "description": "Large-reach primary/preventive health facilities serving regional populations",
    },
    "health_specialized": {
        "isic": "Q86",
        "isic_label": "Human health activities – tertiary/surgical care",
        "encore_sector": "human_health_activities",
        "wwf_industry": "Healthcare",
        "description": "High-intensity specialised surgical centres with lower patient volumes",
    },
    "health_general": {
        "isic": "Q86",
        "isic_label": "Human health activities – general hospital",
        "encore_sector": "human_health_activities",
        "wwf_industry": "Healthcare",
        "description": "Operational general hospitals in high-income markets",
    },
    # Energy / hydro
    "energy": {
        "isic": "D3510",
        "isic_label": "Electric power generation, transmission and distribution",
        "encore_sector": "electric_power_generation_hydro",
        "wwf_industry": "Power & Utilities",
        "description": "Hydroelectric power generation (refurbishment and greenfield)",
    },
    # Rail transport
    "transport": {
        "isic": "H4910",
        "isic_label": "Passenger rail transport, interurban",
        "encore_sector": "rail_transport",
        "wwf_industry": "Transportation & Logistics",
        "description": "Electrified passenger rail infrastructure and operations",
    },
}

# ---------------------------------------------------------------------------
# NACE 4-digit → ISIC Rev.4 (partial, for the three sectors above)
# ---------------------------------------------------------------------------
NACE_TO_ISIC: dict[str, str] = {
    "8610": "Q86",   # Hospital activities
    "8620": "Q86",   # Medical and dental practice activities
    "8690": "Q86",   # Other human health activities
    "3511": "D3510",  # Production of electricity
    "3512": "D3510",  # Transmission of electricity
    "3513": "D3510",  # Distribution of electricity
    "4910": "H4910",  # Passenger rail transport, interurban
    "4920": "H4920",  # Freight rail transport
}


def clean_code(code: str | float) -> str:
    """Normalise any code to uppercase string with no dots/spaces."""
    return str(code).replace(".", "").replace(" ", "").strip().upper()


def map_sector(raw_code: str | float) -> dict:
    """
    Resolve *raw_code* (internal, NACE, or ISIC) to a canonical sector dict.

    Returns a dict with keys: isic, isic_label, encore_sector,
    wwf_industry, description, source_code.
    Raises KeyError if the code cannot be resolved.
    """
    code = clean_code(raw_code)
    lower = code.lower()

    # 1. Try internal codes first (most common in the project CSVs)
    if lower in INTERNAL_CODE_MAP:
        result = dict(INTERNAL_CODE_MAP[lower])
        result["source_code"] = raw_code
        return result

    # 2. Try NACE 4-digit → ISIC → internal lookup by ISIC prefix
    if code in NACE_TO_ISIC:
        isic = NACE_TO_ISIC[code]
        # Find the first internal entry that matches this ISIC
        for entry in INTERNAL_CODE_MAP.values():
            if entry["isic"].startswith(isic.replace("D", "D").replace("H", "H")):
                result = dict(entry)
                result["source_code"] = raw_code
                result["nace_resolved"] = code
                return result

    # 3. Direct ISIC prefix match
    for entry in INTERNAL_CODE_MAP.values():
        if entry["isic"].startswith(code[:3]):
            result = dict(entry)
            result["source_code"] = raw_code
            result["isic_direct"] = True
            return result

    raise KeyError(
        f"Cannot resolve sector code '{raw_code}'. "
        "Add a mapping to INTERNAL_CODE_MAP or NACE_TO_ISIC."
    )
