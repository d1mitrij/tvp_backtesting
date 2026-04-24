# Analysis

## Overview of the simulation pipeline

```
modeled_input_data/*.csv
        │
        ▼
  derive_parameters.py       Reads CSVs → coal EFs, hydro GW, rail PJ
        │
        ▼
base.yaml + ssp*.yaml
        │
        ▼
  Model.from_yaml()          tz-osemosys: builds xarray dataset + linopy LP
        │
        ▼
  model.solve(solver_name="highs")   HiGHS LP solver (~7–8 s per scenario)
        │
        ▼
  model.solution                     xr.Dataset of 32 solution variables
        │
        ▼
  solution_to_iamc()          iamc_bridge.py → IAMC long-form CSV
        │
        ▼
  compute_tvp_dbio_intensity_factors()  adj_ratio_ghg, adj_ratio_employment
```

---

## Running the simulation

From `osemosys/`:

```bash
# Run all five SSP scenarios (default)
python run_simulation.py

# Run a single scenario
python run_simulation.py --scenario ssp1

# Run two specific scenarios
python run_simulation.py --scenario ssp1 ssp5

# Use a different solver
python run_simulation.py --solver highs
```

Typical runtime per scenario: ~7–8 s (LP build ~1.5 s, HiGHS solve < 0.1 s,
xarray extraction ~5 s). All five scenarios complete in under 60 s.

At startup, `run_simulation.py` logs the derived parameters from the project
CSVs for traceability:

```
Africa  : coal_ef=0.3964 Mt CO2/PJ, hydro_retro_max=0.030 GW
Asia    : coal_ef=0.4641 Mt CO2/PJ, hydro_retro_max=0.150 GW
Europe  : coal_ef=0.2775 Mt CO2/PJ, hydro_retro_max=0.002 GW, rail_elec=0.0990 PJ/yr
LATAM   : coal_ef=0.2200 Mt CO2/PJ, hydro_retro_max=0.000 GW
```

---

## Outputs

### results/iamc_all_scenarios.csv

Long-form IAMC-format table: **3,780 rows** = 27 variables × 4 regions ×
7 years × 5 scenarios.

Columns: `model`, `scenario`, `region`, `variable`, `unit`, `year`, `value`

**Energy variables (unit: EJ/yr)**

| Variable | Description |
|----------|-------------|
| `Secondary Energy\|Electricity` | Total electricity production |
| `Secondary Energy\|Electricity\|Coal` | Coal power plant output |
| `Secondary Energy\|Electricity\|Gas` | Gas CCGT output |
| `Secondary Energy\|Electricity\|Hydro` | Hydro (existing + retrofit combined) |
| `Secondary Energy\|Electricity\|Solar` | Solar PV output |
| `Secondary Energy\|Electricity\|Wind` | Wind output |

**Emission variables (unit: Mt CO2/yr)**

| Variable | Description |
|----------|-------------|
| `Emissions\|CO2\|Energy\|Supply\|Electricity` | Total fossil CO2 from power sector |
| `Emissions\|CO2\|Energy\|Supply\|Electricity\|Coal` | Coal-specific CO2 |
| `Emissions\|CO2\|Energy\|Supply\|Electricity\|Gas` | Gas-specific CO2 |
| `Emissions\|CO2\|Energy\|Supply\|Electricity\|Hydro` | Lifecycle CO2 from reservoirs |

**Capacity variables (unit: GW)**

| Variable | Description |
|----------|-------------|
| `Capacity\|Electricity\|<tech>` | Total installed capacity |
| `Capacity Additions\|Electricity\|<tech>` | New capacity added per period |

**Investment variables (unit: million US$2020/yr)**

| Variable | Description |
|----------|-------------|
| `Investment\|Energy Supply\|Electricity\|<tech>` | Undiscounted capital outlay |

### results/tvpdbio_intensity_factors.csv

**140 rows** (5 scenarios × 4 regions × 7 years). Key columns:

| Column | Description |
|--------|-------------|
| `grid_intensity_mt_ej` | Grid CO2 intensity [Mt CO2 / EJ electricity] |
| `adj_ratio_ghg` | GHG intensity relative to 2020 baseline (1.0 = unchanged) |
| `renewable_share` | Fraction of electricity from renewables |
| `adj_ratio_employment` | Labour intensity multiplier relative to fossil baseline |

---

## Reading outputs with pyam

```python
import pyam

df = pyam.IamDataFrame("osemosys/results/iamc_all_scenarios.csv")

# Filter for Europe electricity production under SSP1
elec_eur_ssp1 = df.filter(
    scenario="SSP1-1.9",
    region="Europe",
    variable="Secondary Energy|Electricity|*",
)
elec_eur_ssp1.plot.stack(title="Europe Electricity Mix — SSP1-1.9")

# Compare total CO2 across all 5 scenarios in Asia
co2 = df.filter(
    region="Asia",
    variable="Emissions|CO2|Energy|Supply|Electricity",
)
co2.plot(title="Asia Power Sector CO2 — All 5 SSPs")

# SSP4 inequality: compare Africa vs Europe decarbonisation rates
co2_ssp4 = df.filter(
    scenario="SSP4-6.0",
    region=["Africa", "Europe"],
    variable="Emissions|CO2|Energy|Supply|Electricity",
)
co2_ssp4.plot(title="SSP4-6.0: Divergent decarbonisation by development level")
```

---

## Applying factors to tvp_dbio

The intensity adjustment ratios in `tvpdbio_intensity_factors.csv` are used
to project the `tvp_dbio` supply-chain intensity matrix forward through time
under each SSP.

### Conceptual workflow

```python
import pandas as pd

# Load tvp_dbio base intensities (2020 calibration)
s_ghg_base = {
    "Energy_Utilities": 1.80,   # tCO2e / M$ (Africa baseline)
    # ... other sectors
}

# Load OSeMOSYS-derived adjustment factors
factors = pd.read_csv("osemosys/results/tvpdbio_intensity_factors.csv")

# Select region, scenario, year
row = factors[
    (factors["scenario"] == "SSP2-4.5") &
    (factors["region"]   == "Africa") &
    (factors["year"]     == 2040)
].iloc[0]

# Scale energy sector GHG intensity
s_ghg_2040 = s_ghg_base.copy()
s_ghg_2040["Energy_Utilities"] *= row["adj_ratio_ghg"]
# row["adj_ratio_ghg"] ≈ 0.201 → 80% reduction relative to 2020

# Scale employment intensity (renewables are more labour-intensive)
s_emp_2040["Energy_Utilities"] *= row["adj_ratio_employment"]
# row["adj_ratio_employment"] ≈ 1.20 → 20% more FTE per M$ of output
```

### Mathematical basis

Let $S(t)$ be the tvp_dbio intensity matrix at time $t$ and $S(0)$ the 2020
baseline. The OSeMOSYS-derived adjustment defines:

$$S_{\text{GHG}, \text{EU}}(t) = S_{\text{GHG}, \text{EU}}(0)
\times \frac{I_{\text{grid}}(r, t)}{I_{\text{grid}}(r, 0)}$$

where the grid carbon intensity is:

$$I_{\text{grid}}(r, t) = \frac{\text{Emissions}|\text{CO2}|\text{Energy}(r,t)}
{\text{Secondary Energy}|\text{Electricity}(r,t)}
\quad [\text{Mt CO2 / EJ}]$$

The supply-chain impact vector at tier $n$ then becomes:

$$\text{impact}_n(t) = S(t) \cdot \text{diag}(A^n \cdot y_0)$$

This allows a project assessed in 2024 to be re-evaluated under any SSP for
any future year, reflecting the decarbonisation of its supply-chain energy inputs.

---

## Interpreting scenario differences

### Solar PV capacity in 2050 [GW]

| Region | SSP1-1.9 | SSP2-4.5 | SSP3-7.0 | SSP4-6.0 | SSP5-8.5 |
|--------|----------|----------|----------|----------|----------|
| Africa | 643 | 979 | 1,334 | 468 | 1,702 |
| Asia   | 2,003 | 3,408 | 5,931 | 3,841 | 7,156 |
| Europe | 375 | 534 | 1,292 | 347 | 2,020 |
| LATAM  | 752 | 1,200 | 1,752 | 980 | 2,455 |

**Counter-intuitive result:** SSP3 and SSP5 require *more* solar than SSP1,
not because they decarbonise faster, but because they have much higher total
electricity demand. Once existing coal and gas retire by 2050, the cheapest
new investment is solar regardless of scenario — it just has to cover a much
larger load in high-demand pathways.

**SSP4 Africa (468 GW) vs SSP4 Asia (3,841 GW)** reflects the within-scenario
inequality: Africa's slow demand growth requires less new capacity even though
fossil plants also retire.

### Grid CO2 intensity adj_ratio_ghg (relative to 2020 baseline)

The table shows how fast the grid decarbonises relative to its 2020 intensity:

```
year             2020   2025   2030   2035   2040   2045   2050
scenario region
SSP1-1.9 Africa   1.0  0.710  0.041  0.030  0.022  0.000    0.0
         Asia     1.0  0.820  0.574  0.018  0.008  0.000    0.0
         Europe   1.0  0.610  0.313  0.168  0.084  0.000    0.0
         LATAM    1.0  0.783  0.566  0.336  0.113  0.032    0.0
SSP2-4.5 Africa   1.0  0.752  0.502  0.328  0.201  0.033    0.0
         Asia     1.0  0.799  0.536  0.348  0.209  0.027    0.0
         Europe   1.0  0.846  0.670  0.509  0.362  0.091    0.0
         LATAM    1.0  1.025  0.752  0.535  0.366  0.221    0.0
SSP3-7.0 Africa   1.0  0.771  0.500  0.316  0.190  0.083    0.0
         Asia     1.0  0.734  0.548  0.349  0.212  0.120    0.0
         Europe   1.0  0.913  0.829  0.633  0.472  0.207    0.0
         LATAM    1.0  1.116  0.789  0.548  0.370  0.229    0.0
SSP4-6.0 Africa   1.0  0.846  0.648  0.476  0.328  0.148    0.0
         Asia     1.0  0.806  0.523  0.332  0.196  0.094    0.0
         Europe   1.0  0.667  0.337  0.204  0.108  0.000    0.0
         LATAM    1.0  1.016  0.762  0.555  0.384  0.227    0.0
SSP5-8.5 Africa   1.0  0.768  0.482  0.298  0.178  0.076    0.0
         Asia     1.0  0.716  0.856  0.576  0.391  0.269    0.0
         Europe   1.0  0.924  0.842  0.769  0.595  0.308    0.0
         LATAM    1.0  1.142  0.772  0.512  0.336  0.204    0.0
```

**Key observations:**

- **SSP1 Africa 2030 = 0.041** — the strict 1.5°C carbon budget forces a near
  complete phase-out of coal by 2030, even in Africa.
- **SSP4 inequality signal** — at 2030: Africa=0.648 (slow) vs Europe=0.337
  (fast). This is the model's representation of the core SSP4 narrative where
  wealthy regions decarbonise rapidly while poor regions cannot.
- **SSP5 Asia 2030 = 0.856** — fossil intensity barely moves in the first decade
  under fossil-fuelled development; the loose CO2 cap ($3/tonne) allows
  continued coal expansion to serve the rapidly growing demand.
- **LATAM adj_ratio > 1.0 in 2025** (SSP2: 1.025, SSP3: 1.116, SSP5: 1.142):
  LATAM's existing hydro residual gives it a low 2020 baseline intensity. In
  the 2025 period, growing demand is partially met by fossil residuals, pushing
  the ratio briefly above 1 before renewables dominate.

### tvp_dbio supply-chain implications

For a hospital project with a significant `Energy_Utilities` supply-chain
component, applying the SSP factors shows:

| Assessment point | Region | Scenario | adj_ratio_ghg | Scope 3 reduction |
|------------------|--------|----------|--------------|-------------------|
| 2030 | Africa | SSP1-1.9 | 0.041 | –96% vs 2020 |
| 2030 | Africa | SSP4-6.0 | 0.648 | –35% vs 2020 |
| 2030 | Europe | SSP4-6.0 | 0.337 | –66% vs 2020 |
| 2040 | Africa | SSP2-4.5 | 0.201 | –80% vs 2020 |
| 2040 | Asia   | SSP5-8.5 | 0.391 | –61% vs 2020 |

The SSP4 row pair (Africa 0.648 vs Europe 0.337 in 2030) is particularly
relevant for multi-region projects: a project simultaneously deploying in
Africa and Europe under SSP4 would face very different supply-chain GHG
intensity trajectories in the two regions, reflecting the real-world
financing and institutional capacity gap.

---

## Extending the analysis

### Linking to pyam scenario databases

The IAMC output format is directly compatible with the IIASA AR6 Scenario
Explorer. To compare OSeMOSYS results against the full IAM ensemble:

```python
import pyam

# Load OSeMOSYS results
local = pyam.IamDataFrame("osemosys/results/iamc_all_scenarios.csv")

# Compare with AR6 ensemble (requires iiasa-ece-db connection)
# ar6 = pyam.read_iiasa("AR6", ...)

# All five scenarios are tagged with standard IAMC labels:
# SSP1-1.9, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5
local.filter(variable="Secondary Energy|Electricity").plot()
```

### Uncertainty quantification via MRIO backend sensitivity

Run the tvp_dbio Leontief decomposition for the same project under four MRIO
backends (EXIOBASE, Eora26, WIOD, OECD ICIO) before and after applying the
OSeMOSYS `adj_ratio_ghg`. The spread across backends represents irreducible
methodological uncertainty; the spread across SSPs represents scenario
uncertainty. Together they bracket the full uncertainty range for future
supply-chain GHG.

### Adding renewable energy storage

Add a `Storage` object linked to SOLAR_PV or WIND to model battery dispatch:

```yaml
# in base.yaml
storage:
  - id: BESS
    operating_life: 15
    capex:
      "*":
        "2025": 400
        "2030": 250
        "2035": 160
        "2040": 100
    # link via TechnologyToStorage / TechnologyFromStorage in operating_modes
```

---

## Social Cost of Carbon — damage cost analysis

### Overview

`scc_damage_analysis.py` (project root) monetises the electricity-sector CO2
emissions produced by all available simulation frameworks into annual damage
costs broken down by category.  Four named damage models are applied in
parallel, plus an equal-weight ensemble mean:

| Model | Reference | Key characteristic |
|-------|-----------|-------------------|
| **GIVE** | Rennert et al. (2022) *Nature* 610:687–692 | Highest central SCC; concentrates in Human Health (37 %) and Ecosystems (37 %) |
| **FUND** | Anthoff & Tol, FUND 3.9 (2014) | Broadest sector coverage; explicit Water Resources (16 %) |
| **META-2021** | Dietz et al. (2021) *Nature Climate Change* 11:557–564 | Meta-analytic; tipping-point amplification included |
| **DICE-2023R** | Nordhaus (2023) | Reduced-form quadratic; Agriculture + Human Health dominate |
| **Ensemble** | Equal-weight average of all four | Default when no model is specified |

### Shared scenario registry

`scenarios_registry.py` (project root) is the **single source of truth** for:

- `SSP_REGISTRY` — IAMC labels, RCP, description, warming target, SCC base values
- `SCC_BASE` / `SCC_GROWTH_RATE` / `SCC_BASE_YEAR` — DICE-2023R calibrated at 2.5 %/yr
- `DAMAGE_MODELS` — sector weights for all four models (assertions enforce sum = 1.0)
- `SCENARIO_ORDER` / `ANALYSIS_YEARS` — canonical ordering for pivot tables

All three simulation frameworks (`osemosys/`, `gcam/`, `messageix/`) and
`scc_damage_analysis.py` import their shared metadata from this registry.
Framework-specific fields (YAML paths, GCAM carbon prices) remain local.

```python
from scenarios_registry import (
    SSP_REGISTRY,          # use in run_simulation.py
    DAMAGE_MODELS,         # use in damage analysis
    SCC_BASE, SCC_GROWTH_RATE, SCC_BASE_YEAR,
    SCENARIO_ORDER, ANALYSIS_YEARS,
)
```

### Damage analysis pipeline

```
simulation results (IAMC CSV)
        │
        ▼
scc_damage_analysis.py
  ├── load_emissions()            Filter CO2|Energy|Supply|Electricity
  ├── scc(scenario, year)         SCC_BASE × (1 + 0.025)^(year − 2020)
  ├── build_damage_table()
  │     for each emission row:
  │       for each damage model (Ensemble + GIVE + FUND + META-2021 + DICE-2023R):
  │         weights = get_damage_weights(scenario, year, region, damage_model)
  │           ├── if ipcc_nexus_weights.csv present: AR6 nexus adjustment
  │           └── else: static model weights from scenarios_registry
  │         total_damage_B = co2_mt × 1e6 × scc / 1e9    [billion USD / yr]
  │         for each category: category_damage_B = total_damage_B × weight
  │
  ▼
results_scc_damage.csv           ~4 200 rows (5 models × 5 SSPs × 4 regions × 6 years × 7 cats)
```

### Output schema: `results_scc_damage.csv`

| Column | Type | Description |
|--------|------|-------------|
| `sim_model` | str | Simulation framework label (e.g. `OSeMOSYS\|tz-osemosys`) |
| `damage_model` | str | `Ensemble`, `GIVE`, `FUND`, `META-2021`, `DICE-2023R` |
| `scenario` | str | IAMC label (e.g. `SSP2-4.5`) |
| `region` | str | `Africa`, `Asia`, `Europe`, `LATAM` |
| `year` | int | Analysis year (2020–2045) |
| `scc_usd_per_tco2` | float | SCC at that year (2020 USD/tCO2) |
| `co2_mt_per_yr` | float | Electricity-sector CO2 (Mt CO2/yr) |
| `total_damage_B_usd` | float | Undivided total damage (billion USD/yr) |
| `damage_category` | str | `Agriculture`, `Human Health`, `Water Resources`, etc. |
| `weight_pct` | float | Category weight for this model (%) |
| `category_damage_B` | float | `total_damage_B_usd × weight_pct / 100` |

### Running the damage analysis

```bash
# Step 1: run any simulation framework
cd osemosys && python run_simulation.py && cd ..

# Step 2: (optional) extract AR6 nexus weights
python ipcc_nexus_weights.py --regions Africa Asia Europe LATAM

# Step 3: run damage analysis
python scc_damage_analysis.py
```

Sample output (OSeMOSYS / Ensemble / Europe):

```
SIM: OSeMOSYS|tz-osemosys  |  DAMAGE MODEL: Ensemble  |  REGION: Europe
Annual damage cost by category (billion USD 2020)   [electricity CO2 only]
══════════════════════════════════════════════════════════════════════════
  Category           SSP1-1.9      SSP2-4.5      SSP3-7.0      SSP4-6.0      SSP5-8.5
                  2020 2025 2030  2020 2025 2030  2020 2025 2030  2020 2025 2030  2020 2025 2030
  Agriculture       0.07 0.05 0.00  0.07 0.06 0.04  0.07 0.06 0.05  0.07 0.05 0.02  0.07 0.06 0.06
  Human Health      0.13 0.10 0.00  0.13 0.11 0.07  0.13 0.11 0.10  0.13 0.09 0.04  0.13 0.11 0.11
  ...
```

### Sector weight comparison across models

| Category | GIVE | FUND | META-2021 | DICE-2023R | Ensemble |
|----------|------|------|-----------|------------|----------|
| Agriculture | 10 % | 17 % | 20 % | 20 % | 17 % |
| Human Health | 37 % | 28 % | 32 % | 30 % | 32 % |
| Water Resources | 0 % | 16 % | 12 % | 15 % | 11 % |
| Coastal / SLR | 10 % | 11 % | 8 % | 5 % | 9 % |
| Ecosystems | 37 % | 13 % | 15 % | 15 % | 20 % |
| Energy Systems | 6 % | 10 % | 8 % | 10 % | 9 % |
| Other | 0 % | 5 % | 5 % | 5 % | 4 % |

GIVE and META-2021 produce the highest Human Health damage share, while GIVE
also concentrates the most damage in Ecosystems.  FUND is the only model with a
substantial Water Resources component.  DICE-2023R spreads damage most evenly
across Agriculture, Human Health, and Water Resources.
