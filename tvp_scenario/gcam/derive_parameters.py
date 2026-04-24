"""
derive_parameters.py  (GCAM version)
=====================================
Reads the three project finance CSVs and derives every region-specific
GCAM model parameter that is grounded in observed project data.

Identical logic to osemosys/derive_parameters.py; path adjusted so that
this module can be imported standalone from the gcam/ directory.

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
sys.modules["_osemosys_derive_parameters"] = _osemosys_dp
_spec.loader.exec_module(_osemosys_dp)

RegionParams          = _osemosys_dp.RegionParams
load_project_data     = _osemosys_dp.load_project_data
get_coal_emission_factors = _osemosys_dp.get_coal_emission_factors
get_hydro_retro_gw    = _osemosys_dp.get_hydro_retro_gw
get_rail_elec_demand_pj = _osemosys_dp.get_rail_elec_demand_pj
HYDRO_CF              = _osemosys_dp.HYDRO_CF
DATA_DIR              = _osemosys_dp.DATA_DIR
CAPEX_PER_KW_USD      = _osemosys_dp.CAPEX_PER_KW_USD
H_PER_YEAR            = _osemosys_dp.H_PER_YEAR
MWH_TO_TWH            = _osemosys_dp.MWH_TO_TWH
TWH_TO_PJ             = _osemosys_dp.TWH_TO_PJ
MW_TO_GW              = _osemosys_dp.MW_TO_GW

__all__ = [
    "RegionParams",
    "load_project_data",
    "get_coal_emission_factors",
    "get_hydro_retro_gw",
    "get_rail_elec_demand_pj",
]

# ── Additional GCAM-specific conversions ──────────────────────────────────────
PJ_TO_EJ       = 1e-3          # PJ → EJ (GCAM energy unit)
GW_TO_EJ_YR    = 31.536e-3     # GW at 100% CF → EJ/yr
KGCO2_PER_GJ   = 1e-3          # kgCO2/GJ → tCO2/GJ → kgCO2/MJ (unit check)

# GCAM coal emission coefficient baseline [kgCO2/GJ of coal, HHV]
GCAM_COAL_COEF_KG_GJ = 95.0   # standard bituminous coal


def coal_ef_to_gcam_efficiency(coal_ef_mt_pj: float) -> float:
    """
    Convert derived coal emission factor [Mt CO2/PJ_electricity] to the
    implied thermal efficiency of the regional coal fleet.

    GCAM fixes the fuel emission coefficient at GCAM_COAL_COEF_KG_GJ;
    efficiency is the lever that controls how much coal is burned per
    unit of electricity output, and therefore the effective output EF.

    Formula:
        efficiency = (GCAM_COAL_COEF / 1000) / (coal_ef_mt_pj × 1000)
                   = coal_coef_kg_gj / (coal_ef_mt_pj × 1e6 kgCO2/Mt × 1e-9 PJ/GJ)

    Returns
    -------
    float
        Thermal efficiency (fraction, 0–1). Clipped to realistic range [0.20, 0.50].
    """
    # coal_ef_mt_pj  [Mt CO2/PJ_elec]
    # → kgCO2/GJ_elec:  × (1e9 kg/Mt) × (1 PJ / 1e6 GJ) = × 1e3
    coal_ef_kg_gj_elec = coal_ef_mt_pj * 1e3  # Mt CO2/PJ_elec → kgCO2/GJ_elec
    # efficiency = fuel_coef [kgCO2/GJ_fuel] / output_coef [kgCO2/GJ_elec]
    eff = GCAM_COAL_COEF_KG_GJ / coal_ef_kg_gj_elec
    return max(0.20, min(0.50, eff))


def hydro_retro_gw_to_ej(hydro_retro_gw: float, cf: float) -> float:
    """
    Convert HYDRO_RETRO capacity [GW] to GCAM fixed output [EJ/yr].

    GCAM electricity quantities are in EJ/yr. A fixed-output entry in GCAM
    constrains the technology to produce exactly this much energy per year.

    Parameters
    ----------
    hydro_retro_gw : float   Maximum new GW from the retrofit project
    cf             : float   Hydro capacity factor (region-specific)
    """
    return hydro_retro_gw * GW_TO_EJ_YR * cf   # EJ/yr


if __name__ == "__main__":
    params = load_project_data()
    efs    = get_coal_emission_factors()

    print("=" * 65)
    print("GCAM-derived parameters from project finance data")
    print("=" * 65)
    for r, p in params.items():
        eff  = coal_ef_to_gcam_efficiency(efs[r])
        gw   = p.hydro_retro_gw
        ej   = hydro_retro_gw_to_ej(gw, p.hydro_cf)
        print(f"\n  {r}")
        print(f"    Coal EF:              {efs[r]:.4f} Mt CO2/PJ_elec")
        print(f"    Implied coal eff:     {eff:.3f}  ({eff*100:.1f} %)")
        print(f"    HYDRO_RETRO cap:      {gw:.3f} GW")
        print(f"    HYDRO_RETRO output:   {ej*1000:.4f} PJ/yr = {ej:.6f} EJ/yr")
        if p.rail_elec_demand_pj > 0:
            print(f"    Rail elec demand:     {p.rail_elec_demand_pj*PJ_TO_EJ:.7f} EJ/yr")
