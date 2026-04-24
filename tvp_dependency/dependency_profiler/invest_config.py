"""
Stage 3b – InVEST Model Configuration Builder

Generates the `args` dictionaries required by natcap.invest model execute()
calls, tailored to each project sector:

  Sector              → InVEST Model
  ─────────────────────────────────────────────────────────
  Hydro / Energy      → Annual Water Yield (hydropower_water_yield)
                        + Sediment Delivery Ratio (sdr)
  Health Facilities   → Urban Flood Risk Mitigation (urban_flood_risk_mitigation)
                        + Nutrient Delivery Ratio (ndr) [water quality]
  Rail Transport      → Habitat Quality (habitat_quality)
                        + Carbon Storage and Sequestration (carbon)

All paths are templated with a {workspace_dir} root and a {data_dir} root
so the configs are portable across environments.  The execute() calls are
wrapped in a dry_run guard so the module is importable without natcap.invest
installed; set INVEST_DRY_RUN=0 to actually run models.

Reference: natcap.invest API – every model exposes execute(args: dict).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

INVEST_DRY_RUN = os.getenv("INVEST_DRY_RUN", "1") != "0"

# Default workspace and data roots (override via env vars or arguments)
DEFAULT_WORKSPACE = Path(os.getenv("INVEST_WORKSPACE", "./assessment_output/invest_results"))
DEFAULT_DATA_DIR  = Path(os.getenv("INVEST_DATA_DIR",  "./modeled_input_data/invest_inputs"))


# ---------------------------------------------------------------------------
# Per-sector model config factories
# ---------------------------------------------------------------------------

def hydro_water_yield_args(
    project_id: str,
    region: str,
    workspace: Path = DEFAULT_WORKSPACE,
    data_dir:  Path = DEFAULT_DATA_DIR,
) -> dict:
    """
    Annual Water Yield model args.
    Critical for hydroelectric projects: quantifies the volume of water
    available for power generation, accounting for evapotranspiration.
    """
    ws = workspace / project_id / "water_yield"
    dd = data_dir / region.lower()
    return {
        "workspace_dir":                  str(ws),
        "results_suffix":                 project_id,
        "lulc_path":                      str(dd / "land_use_land_cover.tif"),
        "depth_to_root_rest_layer_path":  str(dd / "soil_depth.tif"),
        "precipitation_path":             str(dd / "annual_precipitation.tif"),
        "pawc_path":                      str(dd / "plant_avail_water_content.tif"),
        "eto_path":                       str(dd / "reference_evapotranspiration.tif"),
        "watersheds_path":                str(dd / "watersheds.shp"),
        "sub_watersheds_path":            str(dd / "sub_watersheds.shp"),
        "biophysical_table_path":         str(dd / "biophysical_table.csv"),
        "seasonality_constant":           5,      # Zhang coefficient
        "calc_water_scarcity":            True,
        "demand_table_path":              str(dd / "water_demand_by_lulc.csv"),
        "valuation_table_path":           str(dd / "hydropower_valuation.csv"),
        # Sub-model toggles
        "calc_scarcity":                  True,
        "calc_valuation":                 True,
    }


def hydro_sdr_args(
    project_id: str,
    region: str,
    workspace: Path = DEFAULT_WORKSPACE,
    data_dir:  Path = DEFAULT_DATA_DIR,
) -> dict:
    """
    Sediment Delivery Ratio model args.
    Assesses sediment load risk for hydroelectric dams – high sediment
    reduces reservoir life and turbine efficiency.
    """
    ws = workspace / project_id / "sdr"
    dd = data_dir / region.lower()
    return {
        "workspace_dir":          str(ws),
        "results_suffix":         project_id,
        "dem_path":               str(dd / "digital_elevation_model.tif"),
        "erosivity_path":         str(dd / "rainfall_erosivity.tif"),
        "erodibility_path":       str(dd / "soil_erodibility.tif"),
        "lulc_path":              str(dd / "land_use_land_cover.tif"),
        "watersheds_path":        str(dd / "watersheds.shp"),
        "biophysical_table_path": str(dd / "biophysical_table.csv"),
        "threshold_flow_accumulation": 1000,
        "k_param":                2,
        "ic_0_param":             0.5,
        "sdr_max":                0.8,
    }


def health_ndr_args(
    project_id: str,
    region: str,
    workspace: Path = DEFAULT_WORKSPACE,
    data_dir:  Path = DEFAULT_DATA_DIR,
) -> dict:
    """
    Nutrient Delivery Ratio model args.
    Health facilities are sensitive to downstream water quality;
    this model quantifies N & P loading to surface water bodies
    from the surrounding watershed – a proxy for source-water risk.
    """
    ws = workspace / project_id / "ndr"
    dd = data_dir / region.lower()
    return {
        "workspace_dir":          str(ws),
        "results_suffix":         project_id,
        "dem_path":               str(dd / "digital_elevation_model.tif"),
        "lulc_path":              str(dd / "land_use_land_cover.tif"),
        "runoff_proxy_path":      str(dd / "annual_precipitation.tif"),
        "watersheds_path":        str(dd / "watersheds.shp"),
        "biophysical_table_path": str(dd / "biophysical_table_ndr.csv"),
        "calc_p":                 True,
        "calc_n":                 True,
        "threshold_flow_accumulation": 1000,
        "k_param":                2,
        "subsurface_critical_length_n": 150,
        "subsurface_eff_n":       0.8,
    }


def health_urban_flood_args(
    project_id: str,
    region: str,
    workspace: Path = DEFAULT_WORKSPACE,
    data_dir:  Path = DEFAULT_DATA_DIR,
) -> dict:
    """
    Urban Flood Risk Mitigation model args.
    Quantifies surface-water retention by green infrastructure in and
    around the hospital catchment, relevant for operational continuity
    under extreme precipitation events.
    """
    ws = workspace / project_id / "urban_flood"
    dd = data_dir / region.lower()
    return {
        "workspace_dir":               str(ws),
        "results_suffix":              project_id,
        "aoi_watersheds_path":         str(dd / "hospital_catchment.shp"),
        "rainfall_depth":              50,         # mm – design storm (50-yr return)
        "lulc_path":                   str(dd / "land_use_land_cover.tif"),
        "soils_hydrological_group_path": str(dd / "soil_hydrological_group.tif"),
        "curve_number_table_path":     str(dd / "cn_lookup.csv"),
        "infrastructure_file_path":    str(dd / "hospital_footprint.shp"),
    }


def rail_habitat_quality_args(
    project_id: str,
    region: str,
    workspace: Path = DEFAULT_WORKSPACE,
    data_dir:  Path = DEFAULT_DATA_DIR,
) -> dict:
    """
    Habitat Quality model args.
    Assesses biodiversity value along the rail corridor and the
    degradation caused by linear infrastructure fragmentation.
    Outputs a habitat quality raster (0–1) and a degradation index.
    """
    ws = workspace / project_id / "habitat_quality"
    dd = data_dir / region.lower()
    return {
        "workspace_dir":                 str(ws),
        "results_suffix":                project_id,
        "lulc_cur_path":                 str(dd / "land_use_land_cover.tif"),
        "lulc_fut_path":                 str(dd / "land_use_with_rail_corridor.tif"),
        "access_vector_path":            str(dd / "rail_alignment.shp"),
        "sensitivity_table_path":        str(dd / "habitat_sensitivity.csv"),
        "threats_table_path":            str(dd / "threat_data.csv"),
        "half_saturation_constant":      0.05,
    }


def rail_carbon_args(
    project_id: str,
    region: str,
    workspace: Path = DEFAULT_WORKSPACE,
    data_dir:  Path = DEFAULT_DATA_DIR,
) -> dict:
    """
    Carbon Storage and Sequestration model args.
    Quantifies carbon stock changes due to land conversion for the
    rail corridor (cut-and-fill, station footprints, depots).
    """
    ws = workspace / project_id / "carbon"
    dd = data_dir / region.lower()
    return {
        "workspace_dir":          str(ws),
        "results_suffix":         project_id,
        "lulc_cur_path":          str(dd / "land_use_land_cover.tif"),
        "lulc_fut_path":          str(dd / "land_use_with_rail_corridor.tif"),
        "carbon_pools_path":      str(dd / "carbon_pools.csv"),
        "calc_sequestration":     True,
        "lulc_redd_path":         None,   # No REDD scenario for this run
        "price_per_metric_ton_of_c": 50,  # USD/tC  – social cost of carbon proxy
        "discount_rate":          5,      # %
        "lulc_fut_year":          2026,
    }


# ---------------------------------------------------------------------------
# Sector dispatcher
# ---------------------------------------------------------------------------

SECTOR_MODEL_MAP: dict[str, list[callable]] = {
    "electric_power_generation_hydro": [hydro_water_yield_args, hydro_sdr_args],
    "human_health_activities":         [health_ndr_args, health_urban_flood_args],
    "rail_transport":                  [rail_habitat_quality_args, rail_carbon_args],
}


def build_invest_configs(project_id: str, region: str, encore_sector: str) -> list[dict]:
    """
    Return all InVEST model arg dicts for a project.
    Each dict also carries a '_model_name' key for identification.
    """
    factories = SECTOR_MODEL_MAP.get(encore_sector, [])
    configs = []
    for fn in factories:
        args = fn(project_id=project_id, region=region)
        args["_model_name"] = fn.__name__.replace("_args", "")
        configs.append(args)
    return configs


def save_configs(configs: list[dict], output_dir: Path) -> list[Path]:
    """Persist each config as a JSON file for reproducibility / audit."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for cfg in configs:
        model_name = cfg.get("_model_name", "unknown")
        proj_id    = Path(cfg.get("workspace_dir", "unknown")).parts[-2]
        fname = output_dir / f"{proj_id}_{model_name}.json"
        with open(fname, "w") as f:
            json.dump(cfg, f, indent=2)
        paths.append(fname)
    return paths


def execute_invest_models(configs: list[dict]) -> list[dict]:
    """
    Execute InVEST models if INVEST_DRY_RUN is not set.
    Returns a list of execution results (dry-run stubs otherwise).
    """
    results = []
    for cfg in configs:
        model_name = cfg.get("_model_name", "unknown")
        if INVEST_DRY_RUN:
            results.append({
                "model":    model_name,
                "status":   "dry_run",
                "workspace": cfg.get("workspace_dir"),
                "message":  "Set INVEST_DRY_RUN=0 and supply input rasters to execute.",
            })
            continue

        # Dynamic import only when actually executing
        try:
            import importlib
            module_map = {
                "hydro_water_yield":      "natcap.invest.hydropower.hydropower_water_yield",
                "hydro_sdr":              "natcap.invest.sdr.sdr",
                "health_ndr":             "natcap.invest.ndr.ndr",
                "health_urban_flood":     "natcap.invest.urban_flood_risk_mitigation.urban_flood_risk_mitigation",
                "rail_habitat_quality":   "natcap.invest.habitat_quality",
                "rail_carbon":            "natcap.invest.carbon",
            }
            module_path = module_map[model_name]
            mod = importlib.import_module(module_path)
            # Strip internal metadata key before passing to InVEST
            clean_args = {k: v for k, v in cfg.items() if not k.startswith("_")}
            Path(clean_args["workspace_dir"]).mkdir(parents=True, exist_ok=True)
            mod.execute(clean_args)
            results.append({"model": model_name, "status": "success",
                             "workspace": cfg["workspace_dir"]})
        except Exception as exc:
            results.append({"model": model_name, "status": "error",
                             "error": str(exc), "workspace": cfg.get("workspace_dir")})

    return results
