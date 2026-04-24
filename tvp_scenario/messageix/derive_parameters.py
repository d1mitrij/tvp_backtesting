"""
derive_parameters.py  (MESSAGEix version)
==========================================
Re-exports the shared CSV-reading logic from osemosys/derive_parameters.py
and adds MESSAGEix-specific unit conversions.

Run standalone to inspect derived values:
    python derive_parameters.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load osemosys/derive_parameters.py under a distinct module name to avoid
# circular import (both files share the name 'derive_parameters').
_osemosys_dp_path = Path(__file__).parent.parent / "osemosys" / "derive_parameters.py"
_spec = importlib.util.spec_from_file_location("_osemosys_derive_parameters", _osemosys_dp_path)
_osemosys_dp = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("_osemosys_derive_parameters", _osemosys_dp)
_spec.loader.exec_module(_osemosys_dp)

RegionParams            = _osemosys_dp.RegionParams
load_project_data       = _osemosys_dp.load_project_data
get_coal_emission_factors = _osemosys_dp.get_coal_emission_factors
get_hydro_retro_gw      = _osemosys_dp.get_hydro_retro_gw
get_rail_elec_demand_pj = _osemosys_dp.get_rail_elec_demand_pj
HYDRO_CF                = _osemosys_dp.HYDRO_CF

__all__ = [
    "RegionParams",
    "load_project_data",
    "get_coal_emission_factors",
    "get_hydro_retro_gw",
    "get_rail_elec_demand_pj",
    "coal_ef_to_message_units",
    "hydro_retro_to_message_units",
]

# ── MESSAGEix unit system ─────────────────────────────────────────────────────
# MESSAGEix activity unit: GWa  (gigawatt-years of energy output)
# Emission factor unit  : Mt CO2/GWa
# Capacity unit         : GW
# Investment cost unit  : million USD/GW  (or MUSD/GWa)
#
# Conversion: 1 GWa = 31.536 PJ  (same as OSeMOSYS capacity_activity_unit_ratio)
#   → emission_factor [Mt CO2/GWa] = coal_ef [Mt CO2/PJ] × 31.536 [PJ/GWa]
#
# In MESSAGEix's parameter `emission_factor`, the value represents
#   emissions per unit of technology *activity* (energy output).
# So for a coal plant producing 1 GWa of electricity:
#   Africa:  0.3964 × 31.536 = 12.50  Mt CO2/GWa
#   Asia:    0.4641 × 31.536 = 14.64  Mt CO2/GWa
#   Europe:  0.2775 × 31.536 =  8.75  Mt CO2/GWa
#   LATAM:   0.2200 × 31.536 =  6.94  Mt CO2/GWa

PJ_PER_GWA = 31.536   # PJ per GW-year (= 1 GW × 8760 h/yr × 3.6 GJ/MWh ÷ 1000)


def coal_ef_to_message_units(coal_ef_mt_pj: float) -> float:
    """
    Convert coal emission factor [Mt CO2/PJ_elec] to MESSAGEix unit [Mt CO2/GWa].

    MESSAGEix emission_factor parameter is expressed per unit of technology
    activity (GWa of electricity output). This conversion assumes activity
    represents electrical energy output (not primary energy input).
    """
    return coal_ef_mt_pj * PJ_PER_GWA  # Mt CO2/PJ × PJ/GWa = Mt CO2/GWa


def hydro_retro_to_message_units(
    hydro_retro_gw: float,
    cf: float,
) -> float:
    """
    Convert HYDRO_RETRO capacity [GW] to MESSAGEix bound_activity_up [GWa/yr].

    MESSAGEix activity upper bounds represent annual energy output (GWa/yr).
    For a hydro plant with given capacity factor:
        GWa/yr = GW × CF × 1 yr  (1 GW at CF produces CF × 31.536 PJ/yr = CF GWa/yr)
    """
    return hydro_retro_gw * cf   # GW × CF = GWa/yr


if __name__ == "__main__":
    params = load_project_data()
    efs    = get_coal_emission_factors()

    print("=" * 65)
    print("MESSAGEix-derived parameters from project finance data")
    print("=" * 65)
    for r, p in params.items():
        ef_msg = coal_ef_to_message_units(efs[r])
        act_ub = hydro_retro_to_message_units(p.hydro_retro_gw, p.hydro_cf)
        print(f"\n  {r}")
        print(f"    Coal EF (input)  : {efs[r]:.4f} Mt CO2/PJ_elec")
        print(f"    Coal EF (MESSAGEix): {ef_msg:.4f} Mt CO2/GWa_elec")
        print(f"    HYDRO_RETRO cap  : {p.hydro_retro_gw:.3f} GW")
        print(f"    HYDRO_RETRO act  : {act_ub:.5f} GWa/yr  (activity upper bound)")
        if p.rail_elec_demand_pj > 0:
            rail_gwa = p.rail_elec_demand_pj / PJ_PER_GWA
            print(f"    Rail elec demand : {p.rail_elec_demand_pj:.4f} PJ/yr"
                  f" = {rail_gwa:.6f} GWa/yr")
