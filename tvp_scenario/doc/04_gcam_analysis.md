# GCAM Analysis

## Architecture overview

GCAM (Global Change Analysis Model) is a multi-sector integrated assessment
model with a C++ core. In this project, **pygcam** manages the end-to-end
workflow: XML modification, scenario sandboxing, GCAM execution, and result
extraction.

```
modeled_input_data/*.csv
        │
        ▼
  derive_parameters.py       CSV → coal efficiencies, hydro capacity, rail demand
        │
        ▼
config/project.xml           pygcam project: 5 scenarios, steps, query references
        │
        ▼
  gt run (pygcam CLI)
    ├─ copies GCAM XML inputs into sandbox
    ├─ applies xml/project_params.xml   (project-calibrated parameters)
    └─ applies xml/ssp{N}_policy.xml    (SSP-specific carbon prices + RES targets)
        │
        ▼
  GCAM C++ binary                       Finds market equilibrium across energy-
  (internal solver)                     water-land sectors; ~15–30 min per scenario
        │
        ▼
  BaseX output database                 XML database of all solution variables
        │
        ▼
  gt query (pygcam CLI)
    ├─ config/queries/electricity_output.xml  → EJ/yr by subsector
    ├─ config/queries/co2_emissions.xml       → Mt CO2/yr by subsector
    ├─ config/queries/elec_capacity.xml       → GW by subsector
    └─ config/queries/elec_investment.xml     → bn US$2020/yr by subsector
        │
        ▼
  iamc_bridge.py
    ├─ aggregates 32 GCAM regions → Africa / Asia / Europe / LATAM
    ├─ maps subsectors to IAMC variable names
    └─ converts units (EJ→EJ, Mt CO2→Mt CO2, GW→GW, bn$→M$)
        │
        ▼
  compute_tvp_dbio_intensity_factors()  adj_ratio_ghg, adj_ratio_employment
```

---

## File map

```
gcam/
├── derive_parameters.py          Re-exports osemosys/derive_parameters.py
├── iamc_bridge.py                GCAM → IAMC + tvp_dbio conversion
├── run_simulation.py             Orchestrator: gt run → gt query → IAMC
├── requirements.txt
├── config/
│   ├── project.xml               pygcam project: groups, steps, queries, scenarios
│   └── queries/
│       ├── electricity_output.xml   EJ/yr by subsector
│       ├── co2_emissions.xml        Mt CO2/yr by subsector
│       ├── elec_capacity.xml        GW by subsector
│       └── elec_investment.xml      bn US$2020/yr by subsector
├── xml/
│   ├── project_params.xml        CSV-derived: coal efficiency, hydro cap, rail demand
│   ├── ssp1_policy.xml           SSP1-1.9 carbon prices + RES
│   ├── ssp2_policy.xml           SSP2-4.5 carbon prices + RES
│   ├── ssp3_policy.xml           SSP3-7.0 carbon prices + RES
│   ├── ssp4_policy.xml           SSP4-6.0 carbon prices + RES
│   └── ssp5_policy.xml           SSP5-8.5 carbon prices + RES
└── results/                      Generated outputs
    ├── iamc_ssp{1-5}.csv
    ├── iamc_all_scenarios.csv
    └── tvpdbio_intensity_factors.csv
```

---

## Prerequisites

GCAM has no pre-built Linux binary. On Linux:

1. **Compile** from source (see `doc/01_installation.md` — Step 1–2, ~30 min).
2. **Generate XML data** via the gcamdata R package (Step 3, ~2–3 h first run).
3. **Configure pygcam** via `~/.pygcam.cfg` (Step 5).

On Mac/Windows, download the release package from
[github.com/JGCRI/gcam-core/releases](https://github.com/JGCRI/gcam-core/releases)
and skip steps 1–2.

## Running the simulation

From `gcam/` (with `~/.pygcam.cfg` configured):

```bash
# All five SSPs
python run_simulation.py

# Single scenario
python run_simulation.py --scenario ssp2

# Two scenarios
python run_simulation.py --scenario ssp1 ssp5

# Dry run: print gt commands without executing GCAM
python run_simulation.py --dry-run
```

The orchestrator calls `gt run` then `gt query` for each scenario. pygcam
creates an isolated sandbox at `$GCAM_HOME/sandbox/{scenario}/` containing
a full copy of GCAM inputs with the XML modifications applied.

Typical runtime per scenario: **15–30 minutes** (GCAM solves ~235 market-
clearing problems per time step across 32 regions). All five scenarios can be
run in parallel if sufficient CPU cores are available.

---

## How policy parameters are applied

GCAM is a **market equilibrium** model. Rather than prescribing energy mixes
directly (as OSeMOSYS does with capacity constraints), GCAM is steered through:

### Carbon prices (GHG tax)

Defined in `ssp{N}_policy.xml` as `<policy-portfolio-standard type="GHG">`.
Each GCAM region has an independent carbon market price path. High prices make
coal and gas uncompetitive relative to solar, wind, and nuclear; the model
endogenously shifts the electricity mix.

```xml
<policy-portfolio-standard type="GHG" name="co2_tax_eu15">
  <market>EU-15</market>
  <constraint year="2020">120</constraint>   <!-- $/tonne CO2 -->
  <constraint year="2050">800</constraint>
</policy-portfolio-standard>
```

**SSP4 inequality signal** in carbon prices:
- Africa 2050: **$25/tCO2** (weak enforcement)
- Europe 2050: **$500/tCO2** (mirrors SSP1 institutional ambition)

### Renewable electricity standard

Defined as `<policy-portfolio-standard type="RES">`. This sets a minimum
fraction of electricity that must come from renewables (solar, wind, hydro,
geothermal, nuclear in GCAM's classification). It acts as a floor; the carbon
price can drive the share higher.

```xml
<policy-portfolio-standard type="RES" name="RPS_Europe">
  <market>Europe</market>
  <min-quantity year="2025">0.60</min-quantity>
  <min-quantity year="2050">0.99</min-quantity>
</policy-portfolio-standard>
```

### Project-calibrated coal efficiency (`project_params.xml`)

Applied to all policy scenarios. Modifies the thermal efficiency of each
region's coal fleet to match the implied value from avoided-CO2 data:

| Region | Implied efficiency | Source |
|--------|--------------------|--------|
| Africa | 24.0% | Hydro_AF 150 000 tCO2/yr / 30 MW |
| Asia   | 20.5% | Hydro_AS 834 218 tCO2/yr / 150 MW |
| Europe | 34.2% | Hydro_EU 6 126 tCO2/yr / 2 MW |
| LATAM  | 43.2% | No project; gas-heavy grid assumed |

Lower efficiency → more fuel burned per unit electricity → higher dispatch
cost at any given carbon price → earlier coal phase-out.

### Hydro retrofit fixed-output

The three hydro retrofit projects are modelled as small fixed-output additions
in GCAM's hydro subsector (from 2025 onward). These are very small relative
to GCAM's regional energy system scale but are included for consistency with
the OSeMOSYS model and project data traceability.

---

## GCAM region aggregation

GCAM uses 32 endogenous regions; query outputs cover all of them. `iamc_bridge.py`
aggregates to the four S4 macro-regions by summing across GCAM sub-regions:

| S4 Region | GCAM sub-regions included |
|-----------|--------------------------|
| Africa    | Africa_Eastern, Africa_Northern, Africa_Southern, Africa_Western |
| Asia      | China, India, South Korea, Japan, Southeast Asia, South Asia, Pakistan, Taiwan |
| Europe    | EU-15, EU-12, Europe Eastern, Europe Non-EU, Russia, Ukraine, Switzerland |
| LATAM     | Mexico, Central America and Caribbean, Brazil, South America (×2), Colombia, Argentina |

Unmatched GCAM regions (USA, Canada, Middle East, Australia) are excluded from
S4 outputs but remain in the full GCAM query CSVs for reference.

---

## Outputs

Same format as OSeMOSYS — the GCAM IAMC bridge produces identical column
structure so both outputs are directly comparable in pyam:

```python
import pyam

# Load both model outputs
gcam_df   = pyam.IamDataFrame("gcam/results/iamc_all_scenarios.csv")
osemosys_df = pyam.IamDataFrame("osemosys/results/iamc_all_scenarios.csv")

# Compare CO2 trajectories from the two models under SSP2
co2 = pyam.concat([gcam_df, osemosys_df]).filter(
    scenario="SSP2-4.5",
    region="Europe",
    variable="Emissions|CO2|Energy|Supply|Electricity",
)
co2.plot(title="Europe Power CO2 — SSP2-4.5: GCAM vs OSeMOSYS")
```

The `model` column distinguishes the two:
- OSeMOSYS outputs: `model = "OSeMOSYS|tz-osemosys"`
- GCAM outputs:     `model = "GCAM|pygcam"`

---

## GCAM vs OSeMOSYS: expected differences

| Metric | OSeMOSYS | GCAM |
|--------|----------|------|
| Policy lever | CO2 caps (hard constraint) | Carbon prices (soft, market-clearing) |
| Demand | Fixed exogenous trajectory | Endogenous (price-responsive) |
| Technology set | 6 (coal, gas, hydro_exist, hydro_retro, solar, wind) | 50+ (including nuclear, CCS, geothermal, biomass) |
| Cross-sector | Electricity only | Energy + water + land + agriculture |
| 2050 emissions | Driven to zero by CO2 cap + renewable mandate | Depends on carbon price magnitude |
| Solar 2050 (SSP3 Asia) | ~5,900 GW (residual demand after fossil retires) | Lower; nuclear and other options also compete |

GCAM results under high-carbon-price SSPs (SSP1, SSP4 Europe) should broadly
match OSeMOSYS because both are forced to near-zero fossil electricity. Under
low-carbon-price SSPs (SSP3, SSP5), GCAM retains more coal and gas through
2050 than OSeMOSYS (which retires residual capacity by mechanical decline).

---

## Applying GCAM factors to tvp_dbio

Identical to the OSeMOSYS workflow — `tvpdbio_intensity_factors.csv` contains
the same columns. Use the `model` column to distinguish GCAM from OSeMOSYS:

```python
factors = pd.read_csv("gcam/results/tvpdbio_intensity_factors.csv")

row = factors[
    (factors["scenario"] == "SSP4-6.0") &
    (factors["region"]   == "Africa") &
    (factors["year"]     == 2040)
].iloc[0]

# GCAM SSP4 Africa 2040: slow decarbonisation (low carbon price, poor region)
s_ghg_africa_2040 = s_ghg_base["Energy_Utilities"] * row["adj_ratio_ghg"]
```

For robust supply-chain GHG estimates, compute `adj_ratio_ghg` from both
models and report the range as model uncertainty alongside the SSP scenario
uncertainty.
