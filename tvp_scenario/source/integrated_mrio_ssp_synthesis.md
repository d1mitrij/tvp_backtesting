# Integrated Multi-Regional Input-Output Analysis and Global Climate-Socioeconomic Pathways: A Technical Synthesis for Sustainable Investment and Policy Simulation

The integration of granular infrastructure project assessments with global macroeconomic and climate trajectories represents one of the most significant challenges in modern sustainable finance. The tvp_dbio library addresses this by providing a robust framework for estimating supply-chain impacts across eight essential supplying sectors, utilizing a Leontief power-series decomposition to trace effects from Tier 0 direct procurement through Tier 10 deep-chain convergence [tvp_dbio]. This framework is built upon four core indicators—greenhouse gas (GHG) emissions, employment (FTE), water use, and value added—and is further extensible through optional metrics such as energy use, nitrogen oxide (NOx) emissions, skill-level employment, and labor income [tvp_dbio]. To ensure these project-level estimates remain relevant in a rapidly changing world, they must be harmonized with the Shared Socioeconomic Pathways (SSPs) and Representative Concentration Pathways (RCPs) established by the Intergovernmental Panel on Climate Change (IPCC) and operationalized through Integrated Assessment Models (IAMs) such as REMIND-MAgPIE, MESSAGEix-GLOBIOM, and GCAM.

---

## Mathematical and Theoretical Foundations of the tvp_dbio Framework

At the core of the tvp_dbio methodology is the utilization of a calibrated 8-sector global model that employs a Leontief power-series decomposition to calculate the supply-chain output vector $y_n$ for a given tier $n$. The model assumes that a project's initial investment, expressed in millions of dollars (M$), is allocated across the eight supplying sectors, creating a tier-zero output vector $y_0$. The subsequent supply-chain impacts are modeled as:

$$y_n = A^n \cdot y_0$$

In this equation, $A$ represents the technology matrix (direct requirements matrix) and $y_n$ is the gross output per sector at tier $n$. The total stressor impacts at each tier are then derived using an intensity matrix $S$, which defines the stressor per unit of gross output for each of the eight sectors:

$$impact_n = S \cdot diag(y_n)$$

The cumulative impact across all tiers (typically calculated up to $n=10$ to ensure convergence) approximates the full Leontief inverse $(I - A)^{-1}$, capturing the entirety of upstream embodied effects [tvp_dbio]. This approach allows for a granular decomposition of Scope 3 emissions and other social stressors, facilitating a distinction between direct suppliers (Tier 0) and deeper supply-chain segments.

---

## Multi-Layer Intensity Calibration

The accuracy of this framework relies on two multiplicative calibration layers that adjust base intensities to reflect specific database conventions and regional economic structures. The first layer, database calibration, ensures alignment with the methodological nuances of the chosen Multi-Regional Input-Output (MRIO) backend, such as EXIOBASE's focus on environmental satellites or Eora26's coverage of the Global South. The second layer, the regional multiplier, scales these intensities to account for variations in technology, such as grid carbon intensity, labor productivity, and resource efficiency [tvp_dbio].

| Sector Code | Infrastructure Role |
|-------------|---------------------|
| Construction | Building and civil works; dominant for CAPEX-heavy projects |
| Energy_Utilities | Electricity, gas, heat, and refining; critical for rail and hydro |
| Manufacturing | Metals, machinery, and electronics; includes turbines and rolling stock |
| Transport_Logistics | Freight, shipping, and warehousing; materials delivery focused |
| Health_Social | Hospitals and medical services; primary for health infrastructure |
| Agriculture | Crops, forestry, and fisheries; embedded in food supply chains |
| Mining_Extraction | Ore processing and quarrying; provides raw materials for manufacturing |
| Water_Waste | Water supply, sewerage, and waste treatment |

The regional multipliers are particularly significant for greenhouse gas emissions and labor. For instance, the Energy_Utilities sector in Africa carries a multiplier of 1.90×, reflecting the continent's heavy reliance on coal and diesel for electricity generation, whereas Europe's multiplier is 0.52×, indicating a high penetration of low-carbon energy sources [tvp_dbio]. This regional specificity is essential for avoiding aggregation bias, particularly when assessing investments in emerging markets where technological efficiency may differ substantially from global averages.

---

## Core Environmental and Social Indicators

The tvp_dbio framework computes four core indicators for every database, providing a consistent baseline for comparison across different environmental and social dimensions.

### Greenhouse Gas Emissions and AR6 Consistency

The GHG emissions indicator (`GHG_tCO2e`) measures total emissions associated with gross output, expressed in tonnes of CO₂-equivalent. The library is strictly aligned with the IPCC Sixth Assessment Report (AR6) GWP100 factors, which represent the most current scientific consensus on the warming potential of various gases over a century.

| Gas | GWP100 (AR6) | Note |
|-----|-------------|------|
| Carbon Dioxide (CO₂) | 1 | Baseline |
| Methane (CH₄) | 27.9 | Non-fossil and fossil averages |
| Nitrous Oxide (N₂O) | 273 | Agriculture and process emissions |
| HFCs / PFCs | 100–12,400 | Sector-average for fluorinated gases |

The calibrated base intensities reveal that Manufacturing (380 tCO2e/M$) and Mining_Extraction (320 tCO2e/M$) are the primary drivers of supply-chain emissions, owing to the energy-intensive nature of smelting, chemical production, and ore processing [tvp_dbio]. The inclusion of Tier 10 convergence allows for the tracking of Scope 3 Category 1 (purchased goods and services) emissions deep into the upstream chain, which is vital for aligning with the Paris Agreement's mitigation targets.

### Employment and Labor Productivity

The `Employment_FTE` indicator captures total employment induced by the investment, converted into full-time equivalents. The global base intensities indicate that Agriculture (25 FTE/M$) and Health_Social (18 FTE/M$) are the most labor-intensive sectors [tvp_dbio]. However, these figures are subject to significant regional variation. European multipliers for construction and agriculture (0.68×) reflect high levels of mechanization, whereas Africa's multiplier (1.58×) highlights a labor-intensive economic structure where capital substitutes for labor at a lower rate.

A critical limitation of this indicator is that it measures induced employment rather than net new job creation; it does not model the displacement effects that may occur when new investments replace existing economic activities. Furthermore, it does not distinguish between formal and informal employment, though the latter is captured to some extent in the Eora26 backend.

### Water Withdrawal and the Water-Waste Sector

Water use is measured in terms of withdrawal (`Water_1000m3`), encompassing both blue and grey water while excluding green water. Agriculture is the dominant global consumer of water due to irrigation demands, reflected in a base intensity of 5.00 (1000 m³/M$). Interestingly, the Water_Waste sector exhibits the highest operational throughput intensity at 8.00 (1000 m³/M$), although its contribution to the total footprint of most infrastructure projects is relatively minor [tvp_dbio].

The regional multipliers for water use are influenced by climatic zones and infrastructure efficiency. Africa's multiplier of 1.65× for agriculture and energy reflects the challenges of arid zones and inefficient cooling or irrigation systems. It is important to note that withdrawal is not synonymous with consumption; the model does not account for the portion of water returned to the local watershed, nor does it weight the volume based on local water stress—a gap that can be addressed by integrating MESSAGEix-GLOBIOM nexus data.

### Value Added and Economic Contribution

Value added represents the sector's contribution to GDP, calculated as gross output minus the cost of intermediate inputs. This indicator is expressed as a ratio (`ValueAdded_M$`) and is used to estimate the income (wages, profits, and taxes) generated by the project's supply chain [tvp_dbio].

| Sector | VA/GO Ratio | Notes |
|--------|-------------|-------|
| Health_Social | 0.70 | High wage component; service-dominated |
| Energy_Utilities | 0.64 | Capital-intensive; high profit component |
| Manufacturing | 0.42 | Lowest ratio; high intermediate input share |
| Agriculture | 0.76 | High in developing regions |
| Construction | 0.48 | Moderate; high share of materials inputs |

Unlike environmental or labor indicators, value added does not utilize a regional multiplier in the tvp_dbio model. This is based on the empirical observation that the VA/GO ratio remains relatively stable (within ±5%) across regions in an 8-sector aggregation, even as the distribution of that value between labor and capital shifts significantly [tvp_dbio].

---

## Optional and Database-Specific Indicators

Optional indicators allow for deeper analysis when specific MRIO backends are employed, providing insights into energy transition exposure, air quality impacts, and social welfare.

### Energy Use and NOx Emissions

Energy use (`Energy_TJ`) and NOx emissions (`NOx_t`) are available primarily through EXIOBASE. The `Energy_TJ` indicator is vital for identifying segments of the supply chain vulnerable to rising carbon prices or those that could benefit most from energy efficiency mandates [tvp_dbio]. The Energy_Utilities sector shows the highest intensity at 8.50 TJ/M$, driven by self-consumption in generation and refining.

NOx emissions are a key proxy for air quality and human health co-benefits, particularly in urban infrastructure projects. Transport_Logistics is the leading source of supply-chain NOx (2.80 t/M$), primarily due to road freight diesel combustion. The regional multipliers for NOx (e.g., 0.68× for Europe) reflect the impact of stringent emission standards like Euro VI and the presence of catalytic converters [tvp_dbio].

### Skill-Level Employment and Labor Income

WIOD 2016 provides the basis for disaggregating employment into three skill bands based on the ISCED 1997 classification. The Health_Social sector stands out for its high-skill intensity (8.10 FTE/M$), while Agriculture remains the largest generator of low-skill employment (17.50 FTE/M$). This disaggregation is essential for assessing the degree of technology transfer and professional development required for different project types.

Labor income (`LaborIncome_M$`), available via Eora26 and OECD ICIO, measures the share of value added that accrues to workers. Combined with total employment, it allows for the calculation of the average supply-chain wage per FTE. For example, a European health project might generate an average wage of ~$24,000 per FTE per year, whereas projects in Africa show a multiplier of 0.65× for labor income, reflecting lower formal wages and a higher share of capital or subsistence income [tvp_dbio].

---

## Comparative Analysis of MRIO Databases

The selection of an MRIO database is a strategic decision that depends on the project's geographic focus and the specific impact categories of interest.

### EXIOBASE 3: The Environmental Benchmark

EXIOBASE 3 is widely regarded as the premier database for environmental footprinting due to its 163-sector resolution and 48+ satellite rows. Its primary strength lies in its detailed accounting of 6 greenhouse gases and various energy carriers, materials, and land-use types. However, its geographic resolution is EU-centric; much of the Global South is grouped into "rest-of-world" aggregates, which can mask country-specific technological differences. The library uses the 2018 data year for consistency, though it does not reflect post-2020 disruptions like the COVID-19 pandemic or the energy crisis.

### Eora26: Comprehensive Global Coverage

Eora26 is the only MRIO that provides individual coverage for 190 countries, making it the indispensable tool for projects in Africa, Latin America, and small island nations. Its inclusion of informal sector data provides a more realistic picture of economic activity in developing regions, although its coarse 26-sector aggregation can lead to significant aggregation bias. The 2015 data year used in the library is the oldest among the backends and may not reflect the rapid structural shifts following the Paris Agreement [tvp_dbio].

### WIOD 2016 and OECD ICIO v2021

WIOD 2016 is primarily valued for its Socio-Economic Accounts, which remain the most detailed public resource for labor-market analysis [tvp_dbio]. Its coverage is limited to 43 countries, mostly OECD members. In contrast, the OECD ICIO v2021 provides the most current data (2018) and covers 66 countries. It is deeply integrated with the Trade in Value Added (TiVA) database, allowing for a sophisticated decomposition of gross trade into domestic and foreign value-added content.

---

## The Scenario Landscape: IPCC SSPs and RCPs

To future-proof project assessments, the static intensities of the tvp_dbio framework must be projected onto the SSP and RCP scenarios that underpin the IPCC AR6 reports. These scenarios combine narrative socioeconomic storylines (SSPs) with trajectories of atmospheric greenhouse gas concentrations (RCPs).

### Narratives of the Shared Socioeconomic Pathways

The five SSPs describe alternative futures of societal development, each presenting different challenges to climate change mitigation and adaptation.

- **SSP1 (Sustainability):** A "green" pathway characterized by a shift toward human well-being, reduced inequality, and lower resource intensity. It assumes rapid technological change and global cooperation.
- **SSP2 (Middle of the Road):** A world where current trends continue, with moderate population growth and uneven progress toward sustainability.
- **SSP3 (Regional Rivalry):** A fragmented world with slow economic growth, high population in developing regions, and high barriers to trade and technology transfer.
- **SSP4 (Inequality):** A world of stark contrasts between high-tech, capital-intensive regions and labor-intensive, low-income areas.
- **SSP5 (Fossil-Fueled Development):** Rapid economic growth driven by fossil fuels and high investment in human capital, leading to high mitigation challenges but increased adaptive capacity.

### Radiative Forcing and RCPs

The RCPs define the level of radiative forcing (e.g., 1.9, 2.6, 4.5, 8.5 W/m²) by the year 2100. For example, the SSP1-1.9 scenario represents the most ambitious mitigation pathway, aiming to limit global warming to below 1.5°C. Plugging these into the tvp_dbio indicators requires adjusting the intensity matrix $S$ over time to reflect the decarbonization of the grid, improvements in labor productivity, and shifts in water availability projected by each scenario.

---

## Integrated Assessment Model Engines: The Source of Dynamic Indicators

IAMs simulate the interactions between human and natural systems, providing the quantitative data needed to drive the tvp_dbio sectors under different SSP-RCP combinations. Three models are particularly relevant for this integration: REMIND-MAgPIE, MESSAGEix-GLOBIOM, and GCAM.

### REMIND-MAgPIE: Welfare Optimization and Land Use

REMIND is an intertemporal general equilibrium model that optimizes welfare by balancing consumption and investment in the energy system and the broader economy. It is coupled with MAgPIE, a global land-use allocation model that accounts for demand for agricultural commodities, production costs, and water constraints. This engine is the primary marker model for SSP5 and is excellent for projecting shifts in the `GHG_tCO2e` intensity of the Energy_Utilities and Agriculture sectors.

### MESSAGEix-GLOBIOM: The Water-Energy-Land Nexus

MESSAGEix-GLOBIOM is a cost-optimization framework that recently introduced a "nexus module" to improve the representation of water systems. This module uses a spatially resolved representation of 210 river basins to map water availability and infrastructure assumptions with the energy and land systems. This provides a dynamic basis for adjusting the `Water_1000m3` indicator in tvp_dbio, moving beyond static multipliers to account for the biophysical impacts of climate change on water resources.

### GCAM: Technological Change and Resource Extraction

The Global Change Analysis Model (GCAM) is a partial equilibrium model that represents the evolution of energy, economy, and land-use systems. It is particularly strong in modeling technological change and resource extraction costs across different SSPs. GCAM's detailed assumptions regarding the capital costs of renewables, nuclear, and CCS can be used to derive time-varying multipliers for the `Energy_TJ` and `NOx_t` indicators in the Manufacturing and Mining sectors.

---

## Mapping IAMC Variables to tvp_dbio Sectors

The bridge between the IAM results and the tvp_dbio indicators is the mapping of IAMC-format variables to the eight supplying sectors. The IAMC timeseries format is a standard for exchanging scenario data, utilizing a "Variable" and "Region" template.

| tvp_dbio Sector | Primary IAMC Variable Proxies | Rationale |
|-----------------|-------------------------------|-----------|
| Construction | `Capital|Investment` | Infrastructure formation rates |
| Energy_Utilities | `Secondary Energy|Electricity`, `Emissions|CO2|Energy` | Grid carbon and energy output |
| Manufacturing | `Final Energy|Industry`, `GDP` | Industrial energy intensity |
| Transport_Logistics | `Final Energy|Transportation`, `Emissions|CO2|Transport` | Freight energy and emissions |
| Health_Social | `Population`, `Education` | Demand driver and skill proxy |
| Agriculture | `Agricultural Production`, `Emissions|CH4` | Biomass and enteric fermentation |
| Mining_Extraction | `Primary Energy|Coal/Oil/Gas`, `Production` | Upstream resource intensity |
| Water_Waste | `Water|Withdrawal`, `Water|Consumption` | Basin-level stress |

The mapping process involves extracting these variables from scenario databases (e.g., the IIASA Scenario Explorer) and calculating the relative change in intensity compared to the 2018 base year. These ratios can then be applied to the tvp_dbio intensity matrix $S$ for future time steps (e.g., 2030, 2040, 2050).

---

## Python Libraries for Scenario Simulation and Integration

Establishing a simulation to plug SSP/RCP scenarios into the tvp_dbio indicators requires a suite of Python tools for data processing, MRIO manipulation, and visualization.

### pyam: Scenario Analysis and Visualization

`pyam` is the standard library for working with IAMC-format timeseries data. It provides a suite of tools for analyzing and visualizing the output of IAMs, macro-energy scenarios, and sectoral studies. Its interface, similar to pandas, allows for easy filtering and validation of scenario results against reference data.

```python
import pyam
df = pyam.IamDataFrame(data='ssp_results.csv')
# Filter for Energy sector GHG intensity in Africa under SSP1
ghg_intensity = df.filter(variable='Emissions|CO2|Energy|Supply', region='Africa')
```

### pymrio: MRIO Data Tasks

`pymrio` provides a high-level abstraction layer for global EE MRIO databases, simplifying common tasks like footprint calculation and region/sector aggregation. It includes automated download functions for EXIOBASE, WIOD, OECD, and Eora26. In a simulation context, pymrio can be used to update the technology and intensity matrices based on scenario-derived multipliers and then re-run the `calc_all()` method to generate new footprints.

### iopy: Backend Data Access

The `iopy` library provides streamlined access to MRIO backends with an auto-download mechanism. It is particularly useful for extracting the A matrix, Leontief inverse (L), and value-added (V) rows for EXIOBASE and OECD. While it does not currently expose the full satellite matrix (F) via its API, it serves as an efficient tool for retrieving the core economic structures needed for the tvp_dbio power-series decomposition.

---

## Technical Synthesis: Building the Simulation Pipeline

A typical simulation pipeline would follow a recursive structure, where the outputs of an IAM are used to calibrate the tvp_dbio model for each decade of a project's lifecycle.

1. **Baseline Generation:** Load the project investment vector $y_0$ and the calibrated 8-sector model using tvp_dbio with a backend like `exiobase_file` or `eora26_file`.
2. **Scenario Parameterization:** Use `pyam` to query the IIASA AR6 Scenario Explorer for the desired SSP-RCP pathway (e.g., SSP2-4.5) and the relevant regions.
3. **Intensity Adjustment:** Calculate the intensity change factors for each of the eight sectors. For example, if the IAM projects a 30% reduction in the carbon intensity of electricity in the project region by 2030, the `s_ghg` factor for Energy_Utilities is multiplied by 0.7.
4. **Supply-Chain Re-evaluation:** Use `pymrio` or the tvp_dbio core logic to recalculate the Tier 0–10 impacts using the updated intensity matrix $S(t)$.
5. **Uncertainty Quantification:** Run the simulation across all four tvp_dbio backends (EXIOBASE, Eora, WIOD, OECD) to establish a confidence interval for the results, reflecting the irreducible methodological uncertainty in global MRIO modeling [tvp_dbio].

This approach allows for the identification of "future exposure" risks. A project might show low GHG emissions today but could be highly vulnerable if its supply chain remains energy-intensive in a world of rapidly rising carbon prices—an insight that only becomes clear when project-level indicators are plugged into global mitigation pathways.

---

## Nuanced Insights and Future Outlook

The integration of tvp_dbio with IPCC scenarios reveals that the "regional responsibility" for environmental change shifts significantly between SSPs. In SSP1, the focus is on "green" procurement and the health co-benefits of reduced NOx and PM emissions. In contrast, SSP3 scenarios highlight the risks of supply-chain fragmentation and the importance of localized employment and resource security.

The role of the water-energy-land nexus is particularly critical. As demonstrated by the MESSAGEix nexus module, water scarcity can act as a binding constraint on energy and land-use decisions, potentially driving up the costs of thermal cooling or irrigation and thereby altering the value-added ratios of those sectors. Analysts should therefore view the tvp_dbio indicators not as static constants but as dynamic variables that respond to the systemic interactions of the global economy.

In conclusion, the tvp_dbio library provides a powerful, multi-sectoral foundation for sustainability assessment, but its true value is realized when it is integrated into the broader architecture of climate and socioeconomic modeling. By utilizing IAM engines as the "dynamic drivers" of project-level indicators, investors and policymakers can gain a sophisticated understanding of how their decisions contribute to, and are affected by, the transition to a low-carbon, resilient global economy.
