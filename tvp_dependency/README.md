# TVP Dependency — Nature-Related Risk Assessment Pipeline

A Python pipeline for nature-related dependency and risk profiling of investment portfolios, implementing **ENCORE** materiality screening, the **WWF Risk Filter Suite**, **InVEST** biophysical model configuration, and **TNFD LEAP**-aligned financial stress testing.

---

## Table of Contents

- [Background](#background)
- [Abbreviations](#abbreviations)
- [Pipeline Overview](#pipeline-overview)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Approaches in Detail](#approaches-in-detail)
  - [1 — Sector Mapping](#1--sector-mapping)
  - [2 — ENCORE Materiality Screening](#2--encore-materiality-screening)
  - [3 — WWF Risk Filter Suite](#3--wwf-risk-filter-suite)
  - [4 — InVEST Biophysical Model Configuration](#4--invest-biophysical-model-configuration)
  - [5 — Portfolio Aggregation & Financial Stress Testing](#5--portfolio-aggregation--financial-stress-testing)
- [Output Files](#output-files)
- [Portfolio Results Summary](#portfolio-results-summary)
- [Extending the Pipeline](#extending-the-pipeline)
- [Academic References](#academic-references)
- [License](#license)

---

## Background

Over half the world's GDP — approximately **USD 44 trillion** — is estimated to be moderately or highly dependent on nature and its services (WEF, 2020). As global ecosystems degrade, this dependency translates into measurable financial risk for organisations through three channels: **physical** (disrupted ecosystem service provision), **regulatory** (new disclosure and remediation requirements), and **reputational** (stakeholder and investor pressure).

This pipeline provides a reproducible, Python-based framework for identifying and quantifying these risks across three infrastructure sectors — health facilities, hydroelectric power, and rail transport — using four internationally recognised methodological approaches.

---

## Abbreviations

| Abbreviation | Full Term |
|---|---|
| **AET** | Actual Evapotranspiration — the amount of water actually evaporated and transpired from a surface |
| **BGCI** | Botanic Gardens Conservation International |
| **BII** | Biodiversity Intactness Index — measures average abundance of species relative to pre-human reference populations (Scholes & Biggs, 2005) |
| **BRF** | Biodiversity Risk Filter — the biodiversity component of the WWF Risk Filter Suite |
| **CAPEX** | Capital Expenditure — funds used to acquire or upgrade physical assets |
| **CRS** | Coordinate Reference System — defines how spatial data maps to real-world locations |
| **DEM** | Digital Elevation Model — a 3D representation of terrain height |
| **ENCORE** | Exploring Natural Capital Opportunities, Risks and Exposure — a UNEP-WCMC / UNEP FI / Global Canopy knowledge base mapping economic activities to ecosystem services |
| **ESG** | Environmental, Social, and Governance — criteria used to evaluate a company's sustainability practices |
| **ESRS** | European Sustainability Reporting Standards — mandatory EU disclosure standards for large companies |
| **ETO** | Reference Evapotranspiration — the evapotranspiration of a reference crop (grass) under optimal conditions |
| **EU WFD** | European Union Water Framework Directive — legislation requiring good ecological status for all EU water bodies |
| **GDAL** | Geospatial Data Abstraction Library — open-source library for reading and writing raster and vector geospatial data |
| **GDP** | Gross Domestic Product — total monetary value of goods and services produced in a country |
| **GICS** | Global Industry Classification Standard — sector taxonomy developed by MSCI and S&P |
| **GIS** | Geographic Information System — tools for capturing, managing, and analysing spatial data |
| **GHG** | Greenhouse Gas — gases that trap heat in the atmosphere (CO₂, CH₄, N₂O, etc.) |
| **IBAT** | Integrated Biodiversity Assessment Tool — provides access to IUCN Red List, WDPA, and KBA data |
| **IPBES** | Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services — the biodiversity equivalent of the IPCC |
| **IPCC** | Intergovernmental Panel on Climate Change |
| **ISIC** | International Standard Industrial Classification — the UN's standard for classifying economic activities (current revision: Rev.4) |
| **ITR** | Implied Temperature Rise — a forward-looking metric expressing the temperature pathway a company or portfolio is aligned with, in °C |
| **InVEST** | Integrated Valuation of Ecosystem Services and Tradeoffs — a suite of spatially explicit biophysical models by the Natural Capital Project (Sharp et al., 2020) |
| **Itr** | Implied Temperature Rise (shorthand) |
| **KBA** | Key Biodiversity Area — a site contributing significantly to the global persistence of biodiversity |
| **LEAP** | Locate, Evaluate, Assess, Prepare — the TNFD's four-phase framework for nature-related risk assessment |
| **LULC** | Land Use / Land Cover — a spatial classification of Earth's surface by human use and vegetation type |
| **MSCI** | Morgan Stanley Capital International — financial data and analytics provider |
| **NACE** | Nomenclature statistique des Activités économiques dans la Communauté Européenne — the EU's economic activity classification, derived from ISIC |
| **NatCap** | Natural Capital Project — Stanford-based partnership developing InVEST and related tools |
| **NDR** | Nutrient Delivery Ratio — an InVEST model quantifying nitrogen and phosphorus loading to water bodies |
| **NPV** | Net Present Value — the present value of future cash flows discounted at a required rate of return |
| **PAWC** | Plant Available Water Capacity — the amount of water a soil can hold that is accessible to plant roots |
| **PET** | Potential Evapotranspiration — the amount of water that would evaporate/transpire if water supply were unlimited |
| **PPP** | Purchasing Power Parity — adjusts monetary values to account for price differences across countries |
| **RaR** | Revenue-at-Risk — the portion of annual revenue exposed to potential loss from nature-related disruptions |
| **RiST** | Risk Stress Test — the World Bank's methodology for integrating natural disaster risk into project finance |
| **RRS** | Resilience Rating System — World Bank framework scoring project resilience to climate and natural hazard risk |
| **RUSLE** | Revised Universal Soil Loss Equation — an empirical model estimating annual soil erosion by rainfall (Renard et al., 1997) |
| **SBTN** | Science Based Targets Network — sets science-aligned corporate targets for nature |
| **SDG** | Sustainable Development Goal — 17 goals adopted by UN member states in 2015 |
| **SDR** | Sediment Delivery Ratio — the fraction of eroded soil that reaches a stream channel; also an InVEST model |
| **SECO** | Swiss State Secretariat for Economic Affairs |
| **STAR** | Species Threat Abatement and Restoration — an IBAT metric quantifying potential reduction in species extinction risk |
| **TCFD** | Task Force on Climate-related Financial Disclosures — recommends climate risk disclosures for financial institutions |
| **TNFD** | Taskforce on Nature-related Financial Disclosures — the nature-equivalent of TCFD, released final recommendations in September 2023 |
| **UNEP FI** | United Nations Environment Programme Finance Initiative |
| **UNEP-WCMC** | United Nations Environment Programme World Conservation Monitoring Centre |
| **WRF** | Water Risk Filter — the water component of the WWF Risk Filter Suite |
| **WDPA** | World Database on Protected Areas — the most comprehensive global database of marine and terrestrial protected areas |
| **WEF** | World Economic Forum |
| **WWF** | World Wide Fund for Nature |

---

## Pipeline Overview

```
Input CSVs (hospitals / hydro / rail)
         │
         ▼
[1] Sector Mapping          Internal / NACE / GICS codes → ISIC Rev.4 + ENCORE key
         │
         ▼
[2] ENCORE Screening        21 ecosystem services × dependency + impact ratings (VH–N)
         │
         ▼
[3a] WWF Risk Filter        32 WRF + 33 BRF indicators → composite scores (1–5)
[3b] InVEST Configs         natcap.invest execute(args) dictionaries per model
         │
         ▼
[4] Portfolio Aggregation   Revenue-at-Risk · Portfolio ITR · TNFD stress-test table
         │
         ▼
assessment_output/          CSV reports, JSON InVEST configs, plain-text summary
```

The four approaches operate as a **funnel**: ENCORE identifies *which* ecosystem services matter for each sector, the WWF Risk Filter determines *whether* those services are degraded at the project location, InVEST quantifies *how much* degradation exists at the site level, and the portfolio aggregator translates all of that into financial language.

---

## Project Structure

```
tvp_dependency/
│
├── dependency_profiler/           # Core pipeline package
│   ├── __init__.py
│   ├── sector_mapper.py           # ISIC / NACE / GICS translation
│   ├── encore_materiality.py      # ENCORE 2024 materiality matrix
│   ├── wwf_risk_filter.py         # WRF + BRF indicator scoring
│   ├── invest_config.py           # InVEST model args builders
│   ├── portfolio_aggregator.py    # RaR, ITR, heatmap, stress-test table
│   └── pipeline.py                # Orchestration entry point
│
├── modeled_input_data/            # Source data
│   ├── hospitals_finance_input.csv
│   ├── hydro_finance_input.csv
│   ├── rail_finance_input.csv
│   └── assumptions.txt
│
├── assessment_output/             # Generated on pipeline run
│   ├── encore_materiality_<ID>.csv
│   ├── wwf_risk_scores.csv
│   ├── dependency_heatmap.csv
│   ├── portfolio_stress_test.csv
│   ├── invest_execution_log.json
│   ├── pipeline_summary.txt
│   └── invest_configs/            # 18 JSON files (one per project × model)
│
├── DOCUMENTATION.md               # Full technical reference (954 lines)
├── LICENSE                        # Apache 2.0
└── README.md                      # This file
```

---

## Quickstart

### Environment

```bash
# Recommended: conda for binary geospatial dependencies
conda create -y -c conda-forge -n env_nature python=3.10
conda activate env_nature
conda install -y -c conda-forge gdal=3.4.1 geopandas rasterio pandas
pip install natcap.invest wwf-itr
```

> **Windows users:** Install [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) before `pip install` if any package requires compilation.

### Run the pipeline

```bash
git clone https://github.com/d1mitrij/tvp_dependency.git
cd tvp_dependency
python -m dependency_profiler.pipeline
```

Results land in `assessment_output/`. To execute InVEST biophysical models (requires geospatial input rasters):

```bash
INVEST_DRY_RUN=0 python -m dependency_profiler.pipeline
```

### Environment variables

| Variable | Default | Effect |
|---|---|---|
| `INVEST_DRY_RUN` | `"1"` | `"0"` runs InVEST models; any other value generates configs only |
| `INVEST_WORKSPACE` | `./assessment_output/invest_results` | Root directory for InVEST raster outputs |
| `INVEST_DATA_DIR` | `./modeled_input_data/invest_inputs` | Root directory for input rasters |

---

## Approaches in Detail

### 1 — Sector Mapping

**Module:** `sector_mapper.py`

Translates project-level sector codes into the canonical ISIC Rev.4 system required by ENCORE and the WWF Risk Filter.

Financial datasets use many different classification systems. ENCORE and the WWF suite use **ISIC Rev.4** (International Standard Industrial Classification, Fourth Revision — UN Statistics Division). This module resolves three source formats:

1. **Internal codes** (`Health_Social`, `Energy`, `Transport`) — project-specific labels used in the input CSVs
2. **NACE Rev.2 four-digit codes** (e.g., `86.10`, `35.11`) — the EU's classification derived from ISIC; largely aligned at the division level (two digits) but may diverge at the class level (four digits)
3. **ISIC prefix matching** — direct fallback for codes already in ISIC format

Each resolved sector returns a canonical dictionary containing the ISIC code, human-readable label, ENCORE sector key, and WWF industry category.

```python
from dependency_profiler.sector_mapper import map_sector

result = map_sector("Health_Social")
# → {"isic": "Q86", "encore_sector": "human_health_activities",
#    "wwf_industry": "Healthcare", ...}
```

**Portfolio mapping:**

| Project | Source Code | ISIC | ENCORE Sector |
|---|---|---|---|
| Proj_001–003 | Health_Social / Specialized / General | Q86 | human_health_activities |
| Hydro_AF / AS / EU | Energy | D3510 | electric_power_generation_hydro |
| Rail_EU_DEV / OP1 / OP2 | Transport | H4910 | rail_transport |

---

### 2 — ENCORE Materiality Screening

**Module:** `encore_materiality.py`  
**Source:** ENCORE v2024, UNEP-WCMC / UNEP FI / Global Canopy

ENCORE (Exploring Natural Capital Opportunities, Risks and Exposure) maps **271 economic activities** to **21 ecosystem services** across two dimensions — dependency and impact — using a five-point ordinal materiality scale:

| Rating | Score | Meaning |
|---|---|---|
| **VH** | 5 | Very High — direct, non-substitutable |
| **H** | 4 | High — significant, difficult to substitute |
| **M** | 3 | Medium — moderate |
| **L** | 2 | Low |
| **VL** | 1 | Very Low |
| **N** | 0 | Not Relevant |

A service is flagged **material** when either the dependency or impact score reaches H (4) or above. The 2024 update to ENCORE refined the "pathways" connecting economic activities to natural capital assets (atmosphere, water, minerals, species) and is grounded in ISIC Rev.4.

**Key sector findings:**

- **Health (Q86):** 6 material services. Top dependencies: `water_supply` (VH), `air_quality_regulation` (H), `climate_regulation` (H), `genetic_materials` (H — pharmaceutical feedstocks). Top impacts: `mediation_of_liquid_waste` (VH — pharmaceutical effluent), `mediation_of_solid_waste` (H — sharps/medical waste).
- **Hydro (D3510):** 8 material services — the highest in the portfolio. Water is simultaneously the primary input and the primary impact vector: `water_supply`, `water_flow_regulation`, and `freshwater_ecosystem_use` are all rated VH for both dependency and impact.
- **Rail (H4910):** 4 material services. Physical infrastructure stability drives the dependency profile: `flood_and_storm_protection` (H) and `erosion_control` (H). Top impact: `terrestrial_ecosystem_use` (VH — permanent land take along the corridor).

**API access (live ENCORE):**

```python
import requests
headers = {"X-Authentication-Token": "<your_token>"}
resp = requests.get(
    "https://www.encorenature.org/api/v1/materiality",
    headers=headers,
    params={"sector": "electric_power_generation_hydro"}
)
```

---

### 3 — WWF Risk Filter Suite

**Module:** `wwf_risk_filter.py`

The WWF Risk Filter Suite consists of two complementary tools that translate ENCORE's sector-level materiality ratings into location-specific risk scores.

#### Water Risk Filter (WRF) — 32 basin indicators

The WRF assesses the physical, regulatory, and reputational dimensions of water-related risk at the watershed (basin) level. All 32 indicators draw on peer-reviewed global datasets and are reviewed annually (WWF, 2023).

**Composite formula:**
```
WRF = (Physical × 0.50) + (Regulatory × 0.30) + (Reputational × 0.20)
```

Scores range from 1 (lowest) to 5 (highest). Projects with a composite score above **3.4** are classified as HIGH RISK.

**Physical indicators** include Baseline Water Stress, Blue Water Scarcity, interannual and seasonal variability, flood occurrence, drought severity, groundwater depletion, the Aridity Index, and freshwater biodiversity measures. **Regulatory indicators** include the SDG 6 institutional capacity score, water governance framework strength, and conflict frequency. **Reputational indicators** capture media scrutiny and civil society mobilisation.

#### Biodiversity Risk Filter (BRF) — 33 indicators

The BRF provides "Scape Risk" — a composite of landscape and seascape biodiversity condition. It was launched at the World Economic Forum in Davos in 2022 and integrates data from the IUCN Red List, the World Database on Protected Areas (WDPA), BirdLife International, and the Biodiversity Intactness Index (BII) published by the Natural History Museum London (Scholes & Biggs, 2005).

**Composite formula:**
```
BRF = (Species_Threat × 0.40) + (Ecosystem_Intactness × 0.35) + (Protected_Areas × 0.25)
```

**Sector sensitivity multipliers** are applied before aggregation. Hydroelectric projects receive a 1.20× amplification on WRF physical indicators (generation output scales directly with river discharge) and a 1.25× amplification on BRF freshwater indicators (dams interrupt fish migration and alter sediment regimes). Rail projects receive a 1.15× amplification on BRF terrestrial indicators (permanent corridor land take fragments habitat).

**Portfolio results:**

| Project | WRF | BRF | High Risk | Primary Driver |
|---|---|---|---|---|
| Proj_001 (LATAM) | 3.48 | **4.09** | Yes | Biodiversity hotspot (BRF) |
| Proj_002 (Africa) | **3.51** | **3.60** | Yes | Physical scarcity + species |
| Proj_003 (Europe) | 3.31 | 2.97 | No | EU regulation buffers risk |
| Hydro_AF | **3.89** | **3.99** | Yes | Seasonal rivers + species |
| Hydro_AS | **4.27** | **4.26** | Yes | Worst in portfolio: all drivers |
| Hydro_EU | **3.62** | 3.23 | Yes (WRF) | EU regulatory stringency |
| Rail_EU_DEV | 3.38 | 3.13 | No | Just below threshold |
| Rail_EU_OP1/2 | 3.38 | 3.13 | No | Maintenance only |

---

### 4 — InVEST Biophysical Model Configuration

**Module:** `invest_config.py`  
**Library:** `natcap.invest` — [github.com/natcap/invest](https://github.com/natcap/invest)

InVEST (Integrated Valuation of Ecosystem Services and Tradeoffs) is a suite of spatially explicit biophysical models developed by the Natural Capital Project at Stanford (Sharp et al., 2020). It is invoked after Stage 3 to provide *quantified*, *site-level* ecosystem service assessments for projects that have cleared both the ENCORE and WWF screening stages.

Every InVEST model follows a consistent Python API:
```python
import natcap.invest.<model_module> as model
model.execute(args: dict)   # args includes all input paths and parameters
```

**Sector-to-model dispatch:**

| Sector | InVEST Model | Biophysical Quantity |
|---|---|---|
| Hydroelectric | Annual Water Yield | Water volume available for generation (mm per watershed pixel) |
| Hydroelectric | Sediment Delivery Ratio (SDR) | Sediment flux reaching the reservoir (tonnes/year) |
| Health | Nutrient Delivery Ratio (NDR) | N and P loading to drinking water source (kg/year) |
| Health | Urban Flood Risk Mitigation | Stormwater retention by green infrastructure (m³) |
| Rail | Habitat Quality | Biodiversity condition index along corridor (0–1) |
| Rail | Carbon Storage | Carbon stock change from land conversion (tonnes C) |

**Model mechanics:**

- **Annual Water Yield** uses the Budyko hydro-climatic framework (Zhang et al., 2001), partitioning precipitation between actual evapotranspiration and runoff using the Zhang seasonality coefficient (set to ω = 5 in this pipeline, appropriate for seasonally variable tropical and sub-tropical regimes).
- **SDR** implements a modified **RUSLE** (Revised Universal Soil Loss Equation, Renard et al., 1997) to estimate gross erosion, then routes sediment downslope using a connectivity index to compute the fraction delivered to the channel network.
- **NDR** models the transport of dissolved nitrogen and phosphorus from source pixels (fertiliser application, urban runoff) through the landscape, accounting for interception by riparian buffers.
- **Habitat Quality** computes a degradation index by weighting landscape threats (roads, rail alignments, urban areas) by their sensitivity to each LULC (Land Use / Land Cover) class.
- **Carbon** uses a four-pool stock approach (above-ground biomass, below-ground biomass, soil organic carbon, dead organic matter) from the `carbon_pools.csv` biophysical table, valued at USD 50/tC (social cost of carbon proxy).

All 18 configuration dictionaries are saved as JSON files in `assessment_output/invest_configs/` for reproducibility. The pipeline runs in dry-run mode by default; set `INVEST_DRY_RUN=0` to execute models against real input rasters.

---

### 5 — Portfolio Aggregation & Financial Stress Testing

**Module:** `portfolio_aggregator.py`

This stage aggregates outputs from all prior stages into portfolio-level financial metrics aligned with the **TNFD LEAP** framework's Assess phase (Taskforce on Nature-related Financial Disclosures, 2023) and **SBTN** (Science Based Targets Network) reporting conventions.

#### Revenue-at-Risk (RaR)

Implements the WWF Revenue-at-Risk methodology:

```
RaR (binary)   = Σ Revenue_proxy_i  for all i where overall_high_risk = True
RaR (weighted) = Σ Revenue_proxy_i × (max(WRF_i, BRF_i) / 5.0)
```

Because operating revenues are not directly available in the input data, sector-specific proxies are derived:

| Sector | Proxy Formula | Basis |
|---|---|---|
| Health | `Investment × Multiplier × 8% operating margin` | OECD hospital benchmark; PPP-adjusted multipliers from input CSV |
| Hydro | `(Avoided_CO₂ × USD 51/tCO₂) + Capacity_Revenue` | World Bank social cost of carbon (2023); USD 0.06/kWh PPA price |
| Rail | `CAPEX × 3% annual toll ratio` | EU rail infrastructure charging framework |

**Portfolio RaR: USD 145.2M** (binary mode), representing 71% of total revenue proxy despite high-risk projects accounting for only 18% of total investment by count — a concentration effect driven by Proj_001 (LATAM hospital, USD 250M) and Hydro_AS (Asia hydro, USD 150M).

#### Implied Temperature Rise (ITR)

Derived from the carbon displacement data in `hydro_finance_input.csv` using a linear interpolation between the Paris Agreement 1.5°C target and the 3.2°C business-as-usual trajectory:

```
avoided_fraction = min(1.0, Avoided_CO₂_tons / 1,000,000)
ITR_i = 3.2 − avoided_fraction × (3.2 − 1.5)

Portfolio_ITR = Σ (Investment_i / Total_Investment) × ITR_i
```

**Portfolio ITR: 3.11°C** — above Paris alignment. Dominated by the large hospital and rail projects that report no direct avoided emissions. The Asian hydro project (834,000 tCO₂ avoided) achieves an individual ITR of ≈1.56°C but is outweighed by investment volume.

For full TCFD/MSCI-aligned ITR calculations, the `wwf-itr` library provides a complete implementation:
```python
from wwf_itr import ITRModel
itr = ITRModel()
result = itr.calculate_rating({"company_id": "Hydro_AS", "target_reduction": 0.834})
```

#### ENCORE Dependency Heatmap

Aggregates all project ENCORE profiles into a portfolio-wide view of ecosystem service exposure:

**Top portfolio dependencies:**

| Ecosystem Service | Max Score | Material Projects |
|---|---|---|
| Water supply | 5 (VH) | 6 / 9 — Health + Hydro |
| Climate regulation | 5 (VH) | 6 / 9 — Health + Hydro |
| Freshwater ecosystem use | 5 (VH) | 3 / 9 — Hydro only |
| Water flow regulation | 5 (VH) | 3 / 9 — Hydro only |
| Erosion control | 4 (H) | 6 / 9 — Hydro + Rail |
| Flood and storm protection | 4 (H) | 6 / 9 — Hydro + Rail |

`water_supply` and `climate_regulation` each affect 6 of the 9 projects at the highest dependency level — meaning a single hydrological shock (such as a multi-year drought amplified by climate change) would simultaneously impair hospital operations, reduce hydropower generation, and increase rail track washout frequency.

#### TNFD LEAP Stress-Test Table

`portfolio_stress_test.csv` consolidates all metrics into a single disclosure-ready table, one row per project, covering investment, revenue, ENCORE materiality, WRF/BRF scores, high-risk flags, revenue-at-risk, and the InVEST models required for site-level quantification.

---

## Output Files

| File | Description |
|---|---|
| `encore_materiality_<ID>.csv` | 21-row table per project: ecosystem service, dependency rating, impact rating, materiality flag |
| `wwf_risk_scores.csv` | WRF and BRF sub-scores and composites for all 9 projects |
| `dependency_heatmap.csv` | Portfolio-aggregated ENCORE scores: max, mean, n_material, projects affected |
| `portfolio_stress_test.csv` | TNFD LEAP Evaluate/Assess disclosure table |
| `invest_execution_log.json` | Status of each InVEST model run (dry_run / success / error) |
| `invest_configs/<ID>_<model>.json` | Complete InVEST `execute(args)` dict, ready to execute with real raster inputs |
| `pipeline_summary.txt` | Human-readable portfolio summary with key financial metrics |

---

## Portfolio Results Summary

```
Projects assessed     : 9 (3 Health, 3 Hydro, 3 Rail)
Total investment      : USD 2,530M
Projects at high risk : 5 / 9
Revenue at risk (RaR) : USD 145.2M
Portfolio ITR         : 3.11°C  (Paris target: 1.5°C)
Top dependency        : Water supply + Climate regulation (6/9 projects, score VH)
InVEST configs built  : 18 (ready to execute; supply input rasters to activate)
```

---

## Extending the Pipeline

### Adding a sector

1. `sector_mapper.py` → add entry to `INTERNAL_CODE_MAP` or `NACE_TO_ISIC`
2. `encore_materiality.py` → add ratings to `MATERIALITY_MATRIX`
3. `wwf_risk_filter.py` → add to `SECTOR_SENSITIVITY` (optional multipliers)
4. `invest_config.py` → add model factory function and register in `SECTOR_MODEL_MAP`

### Adding a region

Add to `REGIONAL_BASELINES` in `wwf_risk_filter.py`. Source values from:
- WRF physical: [Aqueduct Global Water Risk Atlas](https://www.wri.org/aqueduct) (WRI)
- WRF regulatory: World Bank SDG 6 monitoring data
- BRF species: [IUCN Red List spatial data](https://www.iucnredlist.org/resources/spatial-data-download)
- BRF ecosystem: [Biodiversity Intactness Index](https://www.nhm.ac.uk/our-science/data/biodiversity-indicators/biodiversity-intactness-index.html) (NHM London)
- BRF protected areas: [World Database on Protected Areas](https://www.protectedplanet.net/en/thematic-areas/wdpa)

### Live API integration

```python
# ENCORE live API
import requests
resp = requests.get(
    "https://www.encorenature.org/api/v1/materiality",
    headers={"X-Authentication-Token": "<token>"},
    params={"sector": "human_health_activities"}
)

# IBAT — species proximity and STAR scores
resp = requests.post(
    "https://www.ibatforbusiness.org/api/v1/star",
    json={"coordinates": [lon, lat], "radius": 5},
    headers={"X-Authentication-Token": "<token>"}
)
```

---

## Academic References

1. **WEF (2020).** *Nature Risk Rising: Why the Crisis Engulfing Nature Matters for Business and the Economy.* World Economic Forum, New Nature Economy Report Series. Geneva. Available at: [weforum.org](https://www.weforum.org/publications/nature-risk-rising-why-the-crisis-engulfing-nature-matters-for-business-and-the-economy/)

2. **Díaz, S., Settele, J., Brondízio, E.S., Ngo, H.T., et al. (eds.) (2019).** *Global Assessment Report on Biodiversity and Ecosystem Services of the Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services (IPBES).* IPBES Secretariat, Bonn, Germany. DOI: [10.5281/zenodo.3831673](https://doi.org/10.5281/zenodo.3831673)

3. **TNFD (2023).** *Guidance on the Identification and Assessment of Nature-Related Issues: The LEAP Approach.* Taskforce on Nature-related Financial Disclosures, v1.0, September 2023. Available at: [tnfd.global](https://tnfd.global/publication/additional-guidance-on-assessment-of-nature-related-issues-the-leap-approach/)

4. **UNEP FI / UNEP-WCMC / Global Canopy (2024).** *ENCORE: Exploring Natural Capital Opportunities, Risks and Exposure — Technical Documentation v2024.* United Nations Environment Programme Finance Initiative. Available at: [encorenature.org](https://www.encorenature.org) and [unepfi.org](https://www.unepfi.org/publications/exploring-natural-capital-opportunities-risks-and-exposure-a-practical-guide-for-financial-institutions/)

5. **WWF (2023).** *WWF Water Risk Filter: Methodology Documentation.* World Wide Fund for Nature, January 2023. Available at: [riskfilter.org](https://riskfilter.org/water/home)

6. **WWF / Climate & Company (2022).** *WWF Biodiversity Risk Filter: Methodology Documentation.* World Wide Fund for Nature. Available at: [riskfilter.org](https://cdn.kettufy.io/prod-fra-1.kettufy.io/documents/riskfilter.org/BiodiversityRiskFilter_Methodology.pdf)

7. **Dallison, R.J.H., Patil, S.D., Williams, A.P. (2022).** Using the WWF Water Risk Filter to screen existing and projected hydropower projects for climate and biodiversity risks. *Water, 14*(5), 721. DOI: [10.3390/w14050721](https://doi.org/10.3390/w14050721)

8. **Sharp, R., Tallis, H.T., Ricketts, T., Guerry, A.D., Wood, S.A., Chaplin-Kramer, R., et al. (2020).** *InVEST® User's Guide: Integrated Valuation of Ecosystem Services and Tradeoffs.* The Natural Capital Project, Stanford University. Available at: [storage.googleapis.com/releases.naturalcapitalproject.org/invest-userguide/latest/en/index.html](https://storage.googleapis.com/releases.naturalcapitalproject.org/invest-userguide/latest/en/index.html)

9. **Tallis, H., Ricketts, T., Guerry, A., Wood, S., Sharp, R., Nelson, E., et al. (2011).** *InVEST 2.2.2 User's Guide: Integrated Valuation of Ecosystem Services and Tradeoffs.* The Natural Capital Project, Stanford University.

10. **Chaplin-Kramer, R., Sharp, R.P., Weil, C., Bennett, E.M., Pascual, U., Arkema, K.K., et al. (2019).** Global modelling of nature's contributions to people. *Science, 366*(6462), 255–258. DOI: [10.1126/science.aaw3372](https://doi.org/10.1126/science.aaw3372)

11. **Scholes, R.J., Biggs, R. (2005).** A biodiversity intactness index. *Nature, 434*, 45–49. DOI: [10.1038/nature03289](https://doi.org/10.1038/nature03289) — Underpins the BII indicator used in the WWF BRF.

12. **Zhang, L., Dawes, W.R., Walker, G.R. (2001).** Response of mean annual evapotranspiration to vegetation changes at catchment scale. *Water Resources Research, 37*(3), 701–708. DOI: [10.1029/2000WR900325](https://doi.org/10.1029/2000WR900325) — The Budyko-based parametric equation underpinning InVEST's Annual Water Yield model.

13. **Renard, K.G., Foster, G.R., Weesies, G.A., McCool, D.K., Yoder, D.C. (1997).** *Predicting Soil Erosion by Water: A Guide to Conservation Planning with the Revised Universal Soil Loss Equation (RUSLE).* USDA Agricultural Handbook No. 703, Washington D.C. Available at: [tucson.ars.ag.gov](https://www.tucson.ars.ag.gov/unit/publications/pdffiles/775.pdf) — Foundational reference for the InVEST SDR model.

14. **SBTN (2023).** *Technical Guidance for the First Science-Based Targets for Nature: Step 1 — Assess.* Science Based Targets Network. Available at: [sciencebasedtargetsnetwork.org](https://sciencebasedtargetsnetwork.org/wp-content/uploads/2023/05/Technical-Guidance-2023-Step1-Assess-v1.pdf)

15. **MSCI (2023).** *Implied Temperature Rise: Methodology Summary.* MSCI ESG Research. Available at: [msci.com](https://www.msci.com/documents/1296102/31997292/Implied-Temperature-Rise-Methodology-Summary.pdf)

16. **Ruckelshaus, M., McKenzie, E., Tallis, H., Guerry, A., Daily, G., Kareiva, P., et al. (2014).** Notes from the field: Lessons learned from using ecosystem services approaches to inform real-world decisions. *Ecological Economics, 115*, 11–21. DOI: [10.1016/j.ecolecon.2013.07.009](https://doi.org/10.1016/j.ecolecon.2013.07.009)

---

## License

Copyright 2026 d1mitrij

Licensed under the **Apache License, Version 2.0**. You may not use this software except in compliance with the License. A copy of the License is included in this repository as [`LICENSE`](./LICENSE) and is also available at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software distributed under this License is distributed on an **"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND**, either express or implied.
