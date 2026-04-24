# Nature-Related Dependency & Risk Assessment Pipeline
## Technical Documentation

**Version:** 1.0  
**Assessment date:** 2026-04-09  
**Portfolio:** 9 projects — Health (3), Hydroelectric (3), Rail Transport (3)  
**Regulatory alignment:** TNFD LEAP, ENCORE 2024, WWF Risk Filter Suite

---

## Table of Contents

1. [Conceptual Framework](#1-conceptual-framework)
2. [Pipeline Architecture](#2-pipeline-architecture)
3. [Approach 1 — Sector Mapping (ISIC / NACE)](#3-approach-1--sector-mapping)
4. [Approach 2 — ENCORE Materiality Screening](#4-approach-2--encore-materiality-screening)
5. [Approach 3 — WWF Risk Filter Suite](#5-approach-3--wwf-risk-filter-suite)
6. [Approach 4 — InVEST Biophysical Model Configuration](#6-approach-4--invest-biophysical-model-configuration)
7. [Approach 5 — Portfolio Aggregation & Financial Stress Testing](#7-approach-5--portfolio-aggregation--financial-stress-testing)
8. [How the Approaches Interlink](#8-how-the-approaches-interlink)
9. [Output Files Reference](#9-output-files-reference)
10. [Extending the Pipeline](#10-extending-the-pipeline)
11. [Environment Setup](#11-environment-setup)

---

## 1. Conceptual Framework

### 1.1 Why nature-related risk matters

The global economy's dependence on functioning ecosystems is estimated at over **USD 44 trillion** in annual output — more than half of world GDP (WEF 2020). When ecosystems degrade, this dependency converts into financial risk through three channels:

| Risk Channel | Mechanism | Example |
|---|---|---|
| **Physical** | Reduced or disrupted ecosystem service provision | Drought cuts hydropower output by 30% |
| **Regulatory** | New rules requiring disclosure or remediation | EU Nature Restoration Law raises compliance costs |
| **Reputational** | Civil society or investor pressure | Hospital near deforested wetland faces community opposition |

This pipeline operationalises those three channels across two dimensions for each project:

- **Dependency** — what the project *receives* from nature (clean water, stable soil, genetic material)
- **Impact** — what the project *exerts* on nature (wastewater discharge, land conversion, noise)

### 1.2 TNFD LEAP alignment

The pipeline follows the **LEAP** process defined by the Taskforce on Nature-related Financial Disclosures:

```
L — Locate:   Where does the business interface with nature?
               → Sector mapping + regional asset coordinates

E — Evaluate: What are the dependencies and impacts?
               → ENCORE screening + WWF Risk Filter

A — Assess:   What are the resulting risks and opportunities?
               → Portfolio aggregation, Revenue-at-Risk, ITR

P — Prepare:  How should the organisation respond?
               → InVEST configs for site-level quantification
```

### 1.3 Five drivers of nature loss (IPBES)

All indicator selection in this pipeline is anchored to the five primary drivers of biodiversity loss recognised by the Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services:

1. Land / sea use change
2. Direct exploitation of organisms
3. Climate change
4. Pollution
5. Invasive alien species

---

## 2. Pipeline Architecture

```
modeled_input_data/
  hospitals_finance_input.csv
  hydro_finance_input.csv
  rail_finance_input.csv
  assumptions.txt
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 1  sector_mapper.py                                   │
│  Internal code / NACE / ISIC → canonical ENCORE sector key   │
└──────────────────────────┬───────────────────────────────────┘
                           │  encore_sector, isic, wwf_industry
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 2  encore_materiality.py                              │
│  ENCORE 2024 — 21-service × 3-sector materiality matrix      │
│  Outputs: dependency rating + impact rating per service       │
└──────────────────────────┬───────────────────────────────────┘
                           │  high_dependency_services
                           │  high_impact_services
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 3a  wwf_risk_filter.py                                │
│  WWF WRF (32 indicators) + BRF (33 indicators)               │
│  Region × Sector → composite risk scores (1–5 scale)         │
└──────────────────────────┬───────────────────────────────────┘
                           │  wrf_composite, brf_composite
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 3b  invest_config.py                                  │
│  Generates natcap.invest execute(args) configs per sector    │
│  Hydro → water_yield + SDR                                   │
│  Health → NDR + urban_flood                                  │
│  Rail   → habitat_quality + carbon                           │
└──────────────────────────┬───────────────────────────────────┘
                           │  JSON configs + dry-run execution
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 4  portfolio_aggregator.py                            │
│  Revenue-at-Risk · Portfolio ITR · ENCORE heatmap            │
│  TNFD LEAP stress-test table                                 │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
                   assessment_output/
```

All stages are orchestrated by `pipeline.py` which can be run directly:

```bash
python -m dependency_profiler.pipeline
```

To activate real InVEST model execution (requires input rasters):

```bash
INVEST_DRY_RUN=0 python -m dependency_profiler.pipeline
```

---

## 3. Approach 1 — Sector Mapping

**Module:** `dependency_profiler/sector_mapper.py`

### 3.1 The correspondence problem

Environmental knowledge bases (ENCORE, WWF Risk Filter) use **ISIC Rev.4** (International Standard Industrial Classification). Financial datasets use a variety of systems:

| System | Origin | Structure | Example |
|---|---|---|---|
| ISIC Rev.4 | UN Statistics | 4 levels, letters + digits | Q86 = Human health |
| NACE Rev.2 | Eurostat | Derived from ISIC, more granular | 86.10 = Hospital activities |
| GICS | MSCI/S&P | 11 sectors → 157 sub-industries | 35101010 = Electric utilities |
| Internal codes | Project-specific | Arbitrary | `Health_Social`, `Energy` |

### 3.2 Resolution hierarchy

The mapper attempts three lookups in order:

```
1. Internal code lookup     (Health_Social → Q86 / human_health_activities)
2. NACE 4-digit → ISIC      (8610 → Q86, 3511 → D3510, 4910 → H4910)
3. Direct ISIC prefix match (Q86xx → first matching entry)
```

### 3.3 Canonical sector dictionary

Every resolved sector returns a standardised dictionary:

```python
{
    "isic":         "Q86",
    "isic_label":   "Human health activities – primary/preventive care",
    "encore_sector":"human_health_activities",
    "wwf_industry": "Healthcare",
    "description":  "Large-reach primary/preventive health facilities...",
    "source_code":  "Health_Social"
}
```

### 3.4 Portfolio results

| Project | Source Code | ISIC | ENCORE Sector | WWF Industry |
|---|---|---|---|---|
| Proj_001 | Health_Social | Q86 | human_health_activities | Healthcare |
| Proj_002 | Health_Specialized | Q86 | human_health_activities | Healthcare |
| Proj_003 | Health_General | Q86 | human_health_activities | Healthcare |
| Hydro_AF | Energy | D3510 | electric_power_generation_hydro | Power & Utilities |
| Hydro_AS | Energy | D3510 | electric_power_generation_hydro | Power & Utilities |
| Hydro_EU | Energy | D3510 | electric_power_generation_hydro | Power & Utilities |
| Rail_EU_DEV | Transport | H4910 | rail_transport | Transportation & Logistics |
| Rail_EU_OP1 | Transport | H4910 | rail_transport | Transportation & Logistics |
| Rail_EU_OP2 | Transport | H4910 | rail_transport | Transportation & Logistics |

### 3.5 Adding new sectors

To add a new sector, insert an entry into `INTERNAL_CODE_MAP` or `NACE_TO_ISIC`:

```python
# sector_mapper.py
INTERNAL_CODE_MAP["agriculture_cereals"] = {
    "isic":          "A0111",
    "isic_label":    "Growing of cereals (except rice)",
    "encore_sector": "growing_of_cereals",
    "wwf_industry":  "Food & Beverage",
    "description":   "Cereal cultivation – rain-fed and irrigated",
}
```

---

## 4. Approach 2 — ENCORE Materiality Screening

**Module:** `dependency_profiler/encore_materiality.py`  
**Source:** ENCORE v2024, UNEP-WCMC / UNEP FI / Global Canopy  
**API equivalent:** `GET /api/v1/materiality` with `X-Authentication-Token` header

### 4.1 What ENCORE measures

ENCORE maps **271 economic activities** to **21 ecosystem services** across two dimensions:

```
Dependency  — the degree to which the activity relies on the service
Impact      — the degree to which the activity degrades the service
```

Both are rated on a five-point ordinal scale:

| Label | Score | Interpretation |
|---|---|---|
| VH | 5 | Very High — direct, non-substitutable dependency or severe impact |
| H | 4 | High — significant, difficult to substitute |
| M | 3 | Medium — moderate, some substitution possible |
| L | 2 | Low — minor |
| VL | 1 | Very Low — negligible |
| N | 0 | Not relevant / no established pathway |

### 4.2 The 21 ecosystem services

Organised by ENCORE's four natural capital asset classes:

**Water**
- Water supply, Ground water, Water flow regulation

**Atmosphere**
- Air quality regulation, Climate regulation, Mediation of gaseous waste

**Land**
- Erosion control, Flood and storm protection, Soil quality, Noise attenuation, Mediation of solid waste, Mediation of liquid waste, Terrestrial ecosystem use

**Biota**
- Pollination, Pest and disease control, Animal fibres/materials, Plant fibres/materials, Genetic materials, Marine and freshwater goods, Freshwater ecosystem use, Marine ecosystem use

### 4.3 Sector profiles

#### Human Health Activities (Q86)

| Ecosystem Service | Dependency | Impact | Materiality |
|---|---|---|---|
| Water supply | **VH** | M | Material |
| Air quality regulation | **H** | M | Material |
| Climate regulation | **H** | L | Material |
| Genetic materials | **H** | N | Material |
| Mediation of liquid waste | N | **VH** | Material (impact) |
| Mediation of solid waste | N | **H** | Material (impact) |

**Rationale:** Hospitals require large volumes of high-quality water for sterilisation, HVAC cooling towers, and surgical laundry. Air quality directly affects patient outcomes, particularly for respiratory conditions. Pharmaceutical development relies on biological genetic material. The dominant *impacts* are pharmaceutical effluent and sharps/medical waste discharged into water systems.

#### Hydroelectric Power Generation (D3510)

| Ecosystem Service | Dependency | Impact | Materiality |
|---|---|---|---|
| Water supply | **VH** | **VH** | Material (both) |
| Water flow regulation | **VH** | **VH** | Material (both) |
| Freshwater ecosystem use | **VH** | **VH** | Material (both) |
| Climate regulation | **VH** | M | Material |
| Flood and storm protection | **H** | **H** | Material (both) |
| Marine and freshwater goods | M | **VH** | Material (impact) |

**Rationale:** Water is the operational input — without river discharge, a hydroelectric plant generates nothing. Climate regulation matters because precipitation patterns determine annual generation volumes. Dams create severe *impacts*: they block fish migration, trap sediment, alter downstream flood regimes, and inundate terrestrial habitat. This sector has the highest number of material services (8) in the portfolio.

#### Rail Transport — Electrified Interurban (H4910)

| Ecosystem Service | Dependency | Impact | Materiality |
|---|---|---|---|
| Flood and storm protection | **H** | N | Material |
| Erosion control | **H** | M | Material |
| Terrestrial ecosystem use | M | **VH** | Material (impact) |
| Noise attenuation | L | **H** | Material (impact) |

**Rationale:** Electrified rail's primary physical dependencies are geomorphological stability: embankments fail under extreme rain (erosion) and tracks wash out during flooding. Unlike road transport or aviation, electrified rail has no direct fuel combustion, so air quality and climate regulation dependencies are low. The primary *impacts* are permanent land take along the corridor and noise affecting adjacent habitats.

### 4.4 Materiality threshold

A service is flagged as *material* when either the dependency score **≥ 4 (High)** or the impact score **≥ 4 (High)**. This threshold aligns with ENCORE's recommended "prioritisation" boundary for further site-level investigation.

### 4.5 Output format

Each project produces an `encore_materiality_<project_id>.csv`:

```
ecosystem_service,dependency_rating,dependency_score,impact_rating,impact_score,material
water_supply,VH,5,VH,5,True
water_flow_regulation,VH,5,VH,5,True
freshwater_ecosystem_use,VH,5,VH,5,True
flood_and_storm_protection,H,4,H,4,True
climate_regulation,VH,5,M,3,True
...
```

### 4.6 Programmatic access (live ENCORE API)

```python
import requests

headers = {"X-Authentication-Token": "<your_token>"}

# Fetch all materiality ratings
resp = requests.get(
    "https://www.encorenature.org/api/v1/materiality",
    headers=headers,
    params={"sector": "human_health_activities"}
)
ratings = resp.json()
```

For large portfolios, download the full ENCORE database in CSV/Excel from encorenature.org and join locally to avoid API latency.

---

## 5. Approach 3 — WWF Risk Filter Suite

**Module:** `dependency_profiler/wwf_risk_filter.py`  
**Tools:** Water Risk Filter (WRF) + Biodiversity Risk Filter (BRF)  
**Scale:** 1 (lowest risk) → 5 (highest risk). Threshold for HIGH RISK = **3.4**

### 5.1 Why a spatial filter is needed

ENCORE tells you *that* a sector depends on water. The WWF Risk Filter tells you *how much water risk actually exists at the location* where the asset operates. A pharmaceutical plant in Switzerland faces different water stress than the same plant in the Sahel. Sector-level screening alone cannot capture this geographic variation.

### 5.2 Water Risk Filter (WRF) — 32 indicators

The WRF assesses basin-level water risk across three pillars:

#### Physical indicators (12 indicators, 50% weight)

These measure the biophysical state of the watershed:

| Indicator | Metric | Relevance |
|---|---|---|
| Baseline Water Stress | Total withdrawals ÷ renewable supply | Absolute scarcity |
| Blue Water Scarcity | Consumptive use ÷ surface renewable | Consumption pressure |
| Interannual Variability | Coefficient of variation of annual runoff | Year-to-year reliability |
| Seasonal Variability | Wet/dry season runoff ratio | Supply predictability |
| Flood Occurrence | Historical flood frequency | Damage risk |
| Drought Severity | Palmer Drought Severity Index | Production loss risk |
| Upstream Storage Capacity | Reservoir volume ÷ annual runoff | Buffer against variability |
| Groundwater Depletion | Rate of aquifer drawdown | Long-term supply security |
| Aridity Index | Precipitation ÷ potential evapotranspiration | Structural water availability |
| Sediment Load Ratio | Measured vs. natural sediment flux | Reservoir/turbine degradation |
| Threatened Amphibians | IUCN threatened amphibian density | Indicator of watershed health |
| Freshwater Biodiversity | Fish species richness and threat level | Ecosystem integrity proxy |

#### Regulatory indicators (4 indicators, 30% weight)

These measure the governance environment:

| Indicator | Metric |
|---|---|
| Regulatory Framework Strength | SDG 6.5 institutional capacity score |
| SDG 6 Score | National water management performance |
| Water-related Conflict | Frequency of recorded water conflicts |
| Access to Water | % population with safe water access |

#### Reputational indicators (2 indicators, 20% weight)

| Indicator | Metric |
|---|---|
| Media Coverage | Volume of negative water-related press |
| Stakeholder Sensitivity | Civil society mobilisation index |

#### WRF composite formula

```
WRF_composite = (Physical × 0.50) + (Regulatory × 0.30) + (Reputational × 0.20)
```

Sector sensitivity multipliers are applied before aggregation. Hydroelectric projects receive a `1.20×` multiplier on physical indicators because generation volume is directly proportional to river discharge — a 20% increase in scarcity risk translates roughly linearly into a 20% generation shortfall.

### 5.3 Biodiversity Risk Filter (BRF) — 33 indicators

The BRF provides "Scape Risk" — an assessment of the landscape and seascape condition around an asset:

#### Species threat indicators (5 indicators, 40% weight)

| Indicator | Data Source |
|---|---|
| IUCN Threatened Species Density | IUCN Red List spatial data |
| Mammal Richness | IUCN range maps |
| Bird Richness | BirdLife International |
| Reptile Richness | IUCN range maps |
| Freshwater Fish Richness | FishBase + IUCN |

#### Ecosystem intactness indicators (4 indicators, 35% weight)

| Indicator | Data Source |
|---|---|
| Biodiversity Intactness Index (BII) | Natural History Museum London |
| Forest Loss Rate | Hansen et al. (Global Forest Watch) |
| Habitat Fragmentation | GLOBCOVER / ESA CCI Land Cover |
| Invasive Species Pressure | IUCN Invasive Species Database |

#### Protected areas indicators (3 indicators, 25% weight)

| Indicator | Data Source |
|---|---|
| Protected Area Proximity | World Database on Protected Areas (WDPA) |
| Key Biodiversity Area Overlap | IBAT / BirdLife KBA Database |
| Ramsar Wetland Proximity | Ramsar Convention Secretariat |

#### BRF composite formula

```
BRF_composite = (Species_Threat × 0.40) + (Ecosystem_Intactness × 0.35) + (Protected_Areas × 0.25)
```

### 5.4 Regional baseline scores used in this portfolio

| Region | WRF Physical | WRF Regulatory | BRF Species | BRF Ecosystem | Key Driver |
|---|---|---|---|---|---|
| Africa | 3.88 | 2.80 | 3.96 | 3.35 | Physical scarcity + weak governance |
| Asia | 4.03 | 3.44 | 4.50 | 3.55 | Monsoon variability + biodiversity richness |
| Europe | 2.77 | 4.50 | 2.56 | 3.48 | Regulatory stringency + fragmented habitat |
| LATAM | 3.24 | 2.75 | 4.80 | 3.50 | Biodiversity hotspot + ENSO variability |

### 5.5 Sector sensitivity multipliers

| Sector | WRF Physical | WRF Regulatory | BRF Freshwater | BRF Terrestrial |
|---|---|---|---|---|
| electric_power_generation_hydro | 1.20 | 1.10 | 1.25 | — |
| human_health_activities | 1.05 | 1.00 | — | — |
| rail_transport | 1.10 | 1.00 | — | 1.15 |

### 5.6 Portfolio WRF / BRF results

| Project | Region | WRF | BRF | High Risk | Key Driver |
|---|---|---|---|---|---|
| Proj_001 | LATAM | 3.48 | **4.09** | Yes | BRF: biodiversity hotspot |
| Proj_002 | Africa | **3.51** | **3.60** | Yes | WRF: scarcity + BRF: species |
| Proj_003 | Europe | 3.31 | 2.97 | No | Regulatory strength buffers risk |
| Hydro_AF | Africa | **3.89** | **3.99** | Yes | High physical + biodiversity |
| Hydro_AS | Asia | **4.27** | **4.26** | Yes | Worst in portfolio: all drivers elevated |
| Hydro_EU | Europe | **3.62** | 3.23 | Yes (WRF) | EU regulatory exposure pushes WRF over threshold |
| Rail_EU_DEV | Europe | 3.38 | 3.13 | No | Just below threshold; monitor |
| Rail_EU_OP1 | Europe | 3.38 | 3.13 | No | Operational maintenance only |
| Rail_EU_OP2 | Europe | 3.38 | 3.13 | No | Operational maintenance only |

### 5.7 Revenue-at-Risk integration

The `overall_high_risk` flag (True if WRF > 3.4 **or** BRF > 3.4) drives the binary Revenue-at-Risk calculation in Stage 4. This conservative "either/or" approach ensures that strong biodiversity risk (e.g., Proj_001 BRF = 4.09 despite borderline WRF) is not masked by a lower water risk score.

---

## 6. Approach 4 — InVEST Biophysical Model Configuration

**Module:** `dependency_profiler/invest_config.py`  
**Library:** `natcap.invest` (Natural Capital Project, Stanford)  
**Execution:** `INVEST_DRY_RUN=0` to activate; configs saved as JSON for audit

### 6.1 When to use InVEST

ENCORE provides *qualitative sector-level ratings*. The WWF Risk Filter provides *regional basin-level scores*. InVEST provides **site-specific quantified biophysical outputs** — rasters, watershed summaries, and monetary valuations. It is invoked when:

- A project has been flagged material by ENCORE **and** high-risk by the WWF filter
- Site coordinates and geospatial input datasets are available
- Regulatory disclosure or lender due diligence requires quantified evidence

### 6.2 InVEST model API

Every InVEST model follows the same interface:

```python
import natcap.invest.<model_module> as model
model.execute(args: dict)
```

The `args` dictionary is always built from:
- `workspace_dir` — output directory (mandatory)
- `results_suffix` — appended to all output filenames
- Paths to input rasters (`.tif`) and vectors (`.shp`)
- Biophysical parameter tables (`.csv`)
- Model-specific scalar parameters

### 6.3 Sector-to-model mapping

| Sector | InVEST Model | What it quantifies |
|---|---|---|
| Hydroelectric | Annual Water Yield | Water available for generation (mm/watershed) |
| Hydroelectric | Sediment Delivery Ratio | Sediment flux to reservoirs (tonnes/year) |
| Health | Nutrient Delivery Ratio | N and P loading to drinking water source |
| Health | Urban Flood Risk Mitigation | Stormwater retention by green infrastructure |
| Rail | Habitat Quality | Biodiversity value + corridor fragmentation (0–1 index) |
| Rail | Carbon Storage | Carbon stock change from land conversion (tC) |

### 6.4 Model details

#### Annual Water Yield (hydropower_water_yield)

**Purpose:** Estimates the volume of water that leaves a catchment as runoff, accounting for evapotranspiration. This is the water available for hydropower generation.

**Core equation (Budyko framework):**
```
AET_x = PET_x × [1 + (PET_x/P_x) - (1 + (PET_x/P_x)^ω)^(1/ω)]
Y_x = P_x - AET_x
```
Where: `P` = precipitation, `PET` = potential evapotranspiration, `ω` = Zhang seasonality coefficient (set to 5 for this portfolio), `Y` = water yield per pixel.

**Key inputs:**
```json
{
  "lulc_path": "land_use_land_cover.tif",
  "precipitation_path": "annual_precipitation.tif",
  "eto_path": "reference_evapotranspiration.tif",
  "depth_to_root_rest_layer_path": "soil_depth.tif",
  "pawc_path": "plant_avail_water_content.tif",
  "watersheds_path": "watersheds.shp",
  "biophysical_table_path": "biophysical_table.csv",
  "seasonality_constant": 5,
  "calc_water_scarcity": true
}
```

**Output for Hydro_AS:** A raster of water yield (mm) across the Asian watershed. Combined with the valuation table (USD/m³), this produces annual hydropower revenue exposure to water scarcity.

#### Sediment Delivery Ratio (sdr)

**Purpose:** Estimates the fraction of soil eroded by rainfall that actually reaches a stream, accounting for landscape position and vegetation cover. High sediment loads degrade turbine efficiency and reduce reservoir life.

**Core equation (modified RUSLE):**
```
E = R × K × LS × C × P
SDR_x = SDR_max / (1 + exp((IC_0 - IC_x) / k))
```
Where: `R` = rainfall erosivity, `K` = soil erodibility, `C` = land cover factor, `SDR` = sediment delivery ratio per pixel.

**Key inputs:**
```json
{
  "dem_path": "digital_elevation_model.tif",
  "erosivity_path": "rainfall_erosivity.tif",
  "erodibility_path": "soil_erodibility.tif",
  "lulc_path": "land_use_land_cover.tif",
  "threshold_flow_accumulation": 1000,
  "sdr_max": 0.8
}
```

#### Nutrient Delivery Ratio (ndr)

**Purpose:** Quantifies nitrogen and phosphorus loading from the watershed surrounding a health facility to the drinking water source. Elevated nutrient concentrations increase water treatment costs and can render source water unsuitable, a direct operational risk for hospitals.

**Key parameters:**
- `calc_n`: True — nitrogen loading from agricultural and urban runoff
- `calc_p`: True — phosphorus loading (often the binding constraint for eutrophication)
- `subsurface_eff_n: 0.8` — 80% of subsurface N removed by riparian buffers

#### Urban Flood Risk Mitigation

**Purpose:** Assesses the stormwater retention capacity of the landscape within a hospital's contributing catchment. Hospitals must maintain continuous operations during extreme weather; this model identifies the extent to which green infrastructure (parks, green roofs, permeable surfaces) buffers flood exposure.

**Key parameter:** `rainfall_depth: 50` mm — the 50-year return period design storm. Chosen based on the assumption that hospitals are "critical infrastructure" requiring resilience to at least the 1-in-50-year event.

#### Habitat Quality

**Purpose:** Produces a spatially explicit index (0 = degraded, 1 = pristine) of habitat condition along the rail corridor, accounting for sensitivity of each land cover type to the threat of linear infrastructure. The model also quantifies habitat degradation — the loss in quality from baseline to the with-rail scenario.

**Key inputs:**
- `lulc_cur_path` — current land cover (pre-construction)
- `lulc_fut_path` — modelled land cover with rail alignment and stations
- `sensitivity_table_path` — per-LULC sensitivity to each threat type
- `threats_table_path` — threat data (rail = primary; depots, roads as secondary)

#### Carbon Storage and Sequestration

**Purpose:** Quantifies the net change in carbon stocks caused by land conversion for the rail corridor. This serves two purposes: (1) regulatory disclosure of land-use change emissions; (2) identification of high-carbon habitats (e.g., peat, old-growth) that should be avoided in alignment selection.

**Key parameter:** `price_per_metric_ton_of_c: 50` USD — the social cost of carbon proxy used for monetising carbon stock changes in financial risk terms.

### 6.5 Config persistence

All 18 InVEST arg dictionaries are saved as JSON files for reproducibility and audit:

```
assessment_output/invest_configs/
  Hydro_AS_hydro_water_yield.json
  Hydro_AS_hydro_sdr.json
  Proj_001_health_ndr.json
  Proj_001_health_urban_flood.json
  Rail_EU_DEV_rail_habitat_quality.json
  Rail_EU_DEV_rail_carbon.json
  ... (18 files total)
```

To execute a specific model after supplying rasters:

```bash
INVEST_DRY_RUN=0 python -c "
import json, importlib
with open('assessment_output/invest_configs/Hydro_AS_hydro_water_yield.json') as f:
    args = json.load(f)
args.pop('_model_name', None)
import natcap.invest.hydropower.hydropower_water_yield as m
m.execute(args)
"
```

### 6.6 Raster alignment

Input rasters for InVEST must share the same coordinate reference system (CRS), resolution, and bounding box. The `pygeoprocessing` library (a dependency of `natcap.invest`) provides the alignment utility:

```python
import pygeoprocessing

pygeoprocessing.align_and_resize_raster_stack(
    base_raster_path_list=['land_use.tif', 'precip.tif', 'dem.tif'],
    target_raster_path_list=['lulc_aligned.tif', 'precip_aligned.tif', 'dem_aligned.tif'],
    resample_method_list=['near', 'bilinear', 'bilinear'],
    target_pixel_size=(30, -30),        # 30m resolution
    bounding_box_mode='intersection'    # clip to shared extent
)
```

---

## 7. Approach 5 — Portfolio Aggregation & Financial Stress Testing

**Module:** `dependency_profiler/portfolio_aggregator.py`

### 7.1 Revenue proxy derivation

Because the portfolio data provides investment amounts rather than operating revenues, a sector-specific proxy is derived:

#### Health facilities

```
Revenue_proxy = Investment × Multiplier_Benchmark × Operating_Margin
```

- `Multiplier_Benchmark` — from `hospitals_finance_input.csv` (1.8–2.1×, PPP-adjusted)
- `Operating_Margin` — OECD benchmark for hospital operations: **8%**
- Rationale: captures the annualised flow of value at risk if the facility is disrupted by ecosystem failure

#### Hydroelectric

```
Revenue_proxy = (Avoided_CO2_tons × Social_Cost_Carbon) + Capacity_Revenue
```

- `Social_Cost_Carbon` = **USD 51/tCO₂** (World Bank 2023)
- `Capacity_Revenue` = `(Investment ÷ 1,000 USD/kW) × 4,500 h/yr × 0.06 USD/kWh`
- Rationale: captures both the carbon value (climate benefit) and the power purchase revenue that disappears when low-water years reduce generation

#### Rail transport

```
Revenue_proxy = CAPEX_EUR × 0.03 × 1.08 (EUR→USD)
```

- `0.03` = European benchmark toll revenue as 3% of capital base per year (EU rail infrastructure charging framework)
- Rationale: operational rail revenue is primarily access charges paid by train operating companies

### 7.2 Revenue-at-Risk (RaR)

**Definition:** The annual revenue at risk of disruption from nature-related events, calculated for all projects flagged as high-risk.

**Binary mode (default):**
```
RaR = Σ Revenue_proxy_i   for all i where (WRF_i > 3.4 OR BRF_i > 3.4)
```

**Weighted mode (alternative):**
```
RaR = Σ Revenue_proxy_i × (max(WRF_i, BRF_i) / 5.0)
```

The weighted mode provides a more granular view — projects with composite scores of 4.5 contribute proportionally more than those just over the 3.4 threshold.

**Portfolio result:**

| Mode | Revenue-at-Risk | % of Total Revenue Proxy |
|---|---|---|
| Binary | **USD 145.2M** | 71% |
| Weighted | *(available via `rar_mode="weighted"`)* | — |

**High-risk investment share:** 5 of 9 projects flagged. These 5 represent 18% of total portfolio investment by USD value — but **71% of revenue proxy** — because the largest capital projects (Proj_001: USD 250M, Hydro_AS: USD 150M) are among the high-risk set.

### 7.3 Implied Temperature Rise (ITR)

The ITR quantifies the portfolio's alignment with the Paris Agreement temperature target. It is derived here from the hydropower carbon displacement data in `hydro_finance_input.csv`.

**Model:**
```
avoided_fraction = min(1.0, Avoided_CO2_tons / 1,000,000)
ITR_i = 3.2 - avoided_fraction × (3.2 - 1.5)
```

The formula interpolates linearly between:
- **1.5°C** — fully Paris-aligned (100% of baseline avoided)
- **3.2°C** — business-as-usual trajectory (no mitigation)

Non-hydro projects (hospitals, rail) default to the BAU trajectory because no direct avoided-emission figure is available.

**Portfolio ITR** is the investment-weighted average:
```
Portfolio_ITR = Σ (Investment_i / Total_Investment) × ITR_i
```

**Result: 3.11°C** — above the 1.5°C target. This is driven by the large hospital (USD 250M, no avoided emissions) and rail development (EUR 1.85B, indirect decarbonisation only) projects dominating the investment weight. The Asian hydro project (USD 150M, 834,000 tCO₂ avoided) pulls the ITR down toward 1.56°C on its own, but is outweighed.

### 7.4 Dependency heatmap aggregation

The heatmap aggregates ENCORE scores across all projects to identify systemic portfolio-level dependencies:

```python
For each ecosystem_service:
    max_dependency_score   = max score across all projects
    mean_dependency_score  = mean score across all projects
    n_material_projects    = count of projects where score ≥ 4
    projects_affected      = list of project IDs
```

**Top portfolio dependencies:**

| Ecosystem Service | Max Score | Material Projects | Breadth |
|---|---|---|---|
| water_supply | 5 (VH) | 6 | Health + Hydro |
| climate_regulation | 5 (VH) | 6 | Health + Hydro |
| freshwater_ecosystem_use | 5 (VH) | 3 | Hydro only |
| water_flow_regulation | 5 (VH) | 3 | Hydro only |
| erosion_control | 4 (H) | 6 | Hydro + Rail |
| flood_and_storm_protection | 4 (H) | 6 | Hydro + Rail |
| air_quality_regulation | 4 (H) | 3 | Health only |
| genetic_materials | 4 (H) | 3 | Health only |

`water_supply` and `climate_regulation` are the two services affecting the most projects (6/9) at the highest dependency scores. This means a single climate-driven hydrological shock — such as a multi-year drought — would simultaneously impair hospital operations, reduce hydropower generation, and increase rail track damage rates.

### 7.5 TNFD LEAP stress-test table

The final output table (`portfolio_stress_test.csv`) consolidates all four stages into a single row per project, structured for direct use in TNFD LEAP Phase A (Assess) disclosures:

| Column | Description |
|---|---|
| `project_id` | Unique project identifier |
| `region` | Geographic region |
| `sector` | Source sector code |
| `investment_usd_m` | Capital deployed (USD millions) |
| `revenue_proxy_usd_m` | Annual revenue proxy (USD millions) |
| `encore_n_material` | Number of material ecosystem services |
| `top_dependency` | Highest-rated ecosystem dependency |
| `top_impact` | Highest-rated ecosystem impact |
| `wrf_composite` | WWF Water Risk Filter composite (1–5) |
| `brf_composite` | WWF Biodiversity Risk Filter composite (1–5) |
| `wrf_high_risk` | Boolean: WRF > 3.4 |
| `brf_high_risk` | Boolean: BRF > 3.4 |
| `overall_high_risk` | Boolean: either filter high |
| `revenue_at_risk_usd_m` | RaR contribution (0 if not high risk) |
| `invest_models_required` | InVEST models needed for site-level quantification |

---

## 8. How the Approaches Interlink

The five approaches form a funnel — each stage narrows the analysis from broad portfolio screening to site-level quantification:

```
STAGE 1: Sector Mapping
  Purpose : Creates a common language between financial data and
            environmental knowledge bases.
  Input   : Raw sector codes (arbitrary, NACE, GICS)
  Output  : ISIC code + ENCORE sector key
  Feeds   : Stages 2, 3, 4
  ─────────────────────────────────────────────────────────────

STAGE 2: ENCORE Screening
  Purpose : Identifies WHICH ecosystem services matter for each sector.
  Input   : ENCORE sector key
  Output  : Materiality ratings (21 services × dependency + impact)
  Feeds   : Stage 5 (dependency heatmap)
  Does NOT tell you: whether those services are degraded at your location.
  ─────────────────────────────────────────────────────────────

STAGE 3a: WWF Risk Filter
  Purpose : Identifies WHETHER those ecosystem services are at risk
            at the specific basin/region of each project.
  Input   : Region + ENCORE sector (for sensitivity multiplier)
  Output  : WRF/BRF composite scores → high_risk flag
  Does NOT tell you: the exact quantity of water/biodiversity at risk.
  ─────────────────────────────────────────────────────────────

STAGE 3b: InVEST Config
  Purpose : Prepares the site-level models to quantify HOW MUCH of
            each service is present/degraded at the exact asset location.
  Input   : Region + ENCORE sector + geospatial input rasters
  Output  : Biophysical rasters (water yield mm, sediment t/yr, etc.)
  Requires: Field-collected or satellite-derived spatial datasets.
  ─────────────────────────────────────────────────────────────

STAGE 4: Portfolio Aggregation
  Purpose : Translates biophysical risk into financial language.
  Input   : All prior stage outputs + financial data
  Output  : Revenue-at-Risk, ITR, TNFD stress-test table
```

### Decision logic for escalation

```
All projects → Sector mapping (Stage 1)          [always]
     │
     ▼
All projects → ENCORE screening (Stage 2)         [always]
     │
     ├── No material services? → Low priority, periodic re-screening
     │
     ▼
Material projects → WWF Risk Filter (Stage 3a)    [always for material]
     │
     ├── Not high risk? → Monitor; include in portfolio heatmap
     │
     ▼
High-risk projects → InVEST config (Stage 3b)     [on-demand, site-level]
     │
     └── Requires geospatial data. Supply rasters → execute models
```

---

## 9. Output Files Reference

All outputs written to `assessment_output/`:

| File | Format | Generated by | Contents |
|---|---|---|---|
| `encore_materiality_<ID>.csv` | CSV | Stage 2 | 21-row table: service, dep rating, impact rating, materiality flag |
| `wwf_risk_scores.csv` | CSV | Stage 3a | One row per project: WRF/BRF sub-scores, composites, high-risk flags |
| `invest_configs/<ID>_<model>.json` | JSON | Stage 3b | Complete InVEST `execute(args)` dict, ready to run |
| `invest_execution_log.json` | JSON | Stage 3b | Status of each model execution (dry_run / success / error) |
| `dependency_heatmap.csv` | CSV | Stage 4 | Portfolio-aggregated ENCORE: max/mean scores, n_material, affected projects |
| `portfolio_stress_test.csv` | CSV | Stage 4 | TNFD LEAP table: one row per project, all metrics combined |
| `pipeline_summary.txt` | Text | pipeline.py | Human-readable portfolio summary with key metrics |

---

## 10. Extending the Pipeline

### Adding a new sector

1. Add to `INTERNAL_CODE_MAP` in `sector_mapper.py`
2. Add a materiality profile to `MATERIALITY_MATRIX` in `encore_materiality.py`
3. Add regional baselines to `REGIONAL_BASELINES` in `wwf_risk_filter.py` (if new region)
4. Add sector sensitivity multipliers to `SECTOR_SENSITIVITY` in `wwf_risk_filter.py`
5. Add InVEST model factories to `invest_config.py` and register in `SECTOR_MODEL_MAP`

### Adding a new region

In `wwf_risk_filter.py`, add a new key to `REGIONAL_BASELINES` with all 18 indicator values (12 WRF physical, 4 WRF regulatory, 2 WRF reputational, 5 BRF species, 4 BRF ecosystem, 3 BRF protected areas). Source values from:

- WRF physical: Aqueduct Global Water Risk Atlas (WRI)
- WRF regulatory: World Bank SDG 6 monitoring data
- BRF species: IUCN Red List spatial data + BirdLife
- BRF ecosystem: Biodiversity Intactness Index (NHM London)
- BRF protected areas: World Database on Protected Areas (WDPA)

### Connecting to live APIs

Replace the embedded regional baselines with live API calls:

```python
# wwf_risk_filter.py — production pattern
import requests

def fetch_wrf_basin_score(lat: float, lon: float, token: str) -> dict:
    """Fetch live basin scores from WWF Water Risk Filter API."""
    resp = requests.get(
        "https://api.waterriskfilter.org/v2/basin",
        params={"lat": lat, "lon": lon},
        headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()
```

For IBAT (biodiversity gold standard):

```python
import requests

def fetch_ibat_star_score(lat: float, lon: float, radius_km: float, token: str) -> dict:
    """Fetch STAR species threat abatement score from IBAT API."""
    resp = requests.post(
        "https://www.ibatforbusiness.org/api/v1/star",
        json={"coordinates": [lon, lat], "radius": radius_km},
        headers={"X-Authentication-Token": token}
    )
    return resp.json()
```

### Using a weighted ITR model (wwf-itr library)

```python
from wwf_itr import ITRModel

itr = ITRModel()
result = itr.calculate_rating({
    "company_id":       "Hydro_AS",
    "base_year":        2020,
    "target_reduction": 0.834    # 83.4% = 834,000 / 1,000,000 ton baseline
})
print(f"ITR: {result.value}°C")
```

---

## 11. Environment Setup

### Recommended installation

```bash
# Create isolated environment with binary geospatial libraries via conda
conda create -y -c conda-forge -n env_nature python=3.10
conda activate env_nature
conda install -y -c conda-forge gdal=3.4.1 geopandas rasterio pandas
pip install natcap.invest wwf-itr

# Verify
python -c "import natcap.invest; import geopandas; print('OK')"
```

### From GitHub (latest InVEST)

```bash
pip install "git+https://github.com/natcap/invest.git@main#egg=natcap.invest"
```

### Windows note

Install "Build Tools for Visual Studio" before pip-installing compiled packages. The conda route avoids most compilation issues by providing pre-built binaries.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `INVEST_DRY_RUN` | `"1"` | Set to `"0"` to execute InVEST models |
| `INVEST_WORKSPACE` | `./assessment_output/invest_results` | Root directory for model outputs |
| `INVEST_DATA_DIR` | `./modeled_input_data/invest_inputs` | Root directory for input rasters |

---

*Documentation generated from pipeline source code and portfolio run of 2026-04-09.*  
*Methodology references: ENCORE 2024 (UNEP-WCMC/UNEP FI/Global Canopy), WWF Risk Filter Suite v3, natcap.invest v3.14, TNFD LEAP v1.1, IPBES Global Assessment 2019.*
