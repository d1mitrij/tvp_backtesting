# MESSAGEix Analysis

## Architecture overview

MESSAGEix is a IIASA energy-economy model with a Python API (`message_ix`)
backed by `ixmp` (a scenario and data management library). GAMS solves the
MESSAGE linear/mixed-integer programme; ixmp manages scenario versioning in
a local database.

```
modeled_input_data/*.csv
        │
        ▼
  derive_parameters.py      CSV → coal EFs (Mt CO2/GWa), hydro bounds (GWa/yr)
        │
        ▼
  ixmp.Platform              Local database (ixmp4 SQLite or hsqldb)
        │
        ▼
  mix-models fetch snapshot-1  → MESSAGEix-GLOBIOM R11 baseline (from Zenodo)
        │
        ▼
  For each SSP:
    message_ix.Scenario.clone()
    check_out()
    base_params.apply()       Project-calibrated emission factors, hydro bounds
    ssp{N}.apply()            Carbon prices, emission caps, fossil growth limits
    commit()
        │
        ▼
  scenario.solve(model="MESSAGE")   GAMS MESSAGE LP (~5–30 min per scenario)
        │
        ▼
  iamc_bridge.py
    ├─ scen.var("ACT")    → Secondary Energy|Electricity [EJ/yr]
    ├─ scen.var("CAP")    → Capacity|Electricity [GW]
    ├─ scen.var("EMISS")  → Emissions|CO2 [Mt CO2/yr]
    └─ scen.var("CAP_NEW")→ Capacity Additions [GW]
        │   (or: Reporter.from_scenario → message::default)
        ▼
  compute_tvp_dbio_intensity_factors()  adj_ratio_ghg, adj_ratio_employment
```

---

## File map

```
messageix/
├── derive_parameters.py       Re-exports osemosys/ + adds MESSAGEix unit conversions
├── iamc_bridge.py             MESSAGEix variables → IAMC + tvp_dbio factors
├── run_simulation.py          Orchestrator: clone → configure → solve → extract
├── requirements.txt
└── scenarios/
    ├── __init__.py            Exports ALL dict and individual SSP modules
    ├── _param_utils.py        make_tax_df, make_bound_emission_df, make_growth_df
    ├── base_params.py         CSV-derived: emission_factor, bound_activity_up, demand
    ├── ssp1.py                SSP1-1.9 CARBON_PRICES, EMISSION_CAPS, FOSSIL_GROWTH
    ├── ssp2.py                SSP2-4.5  …
    ├── ssp3.py                SSP3-7.0  …
    ├── ssp4.py                SSP4-6.0  …
    └── ssp5.py                SSP5-8.5  …
```

---

## Running the simulation

```bash
cd messageix

# One-time setup: fetch MESSAGEix-GLOBIOM snapshot (~400 MB from Zenodo)
mix-models fetch snapshot-1

# Run all five SSPs (ixmp4 SQLite backend, no Java required)
python run_simulation.py

# Single scenario
python run_simulation.py --scenario ssp2

# Use hsqldb backend (requires Java 11+)
python run_simulation.py --backend hsqldb

# Clone and configure without running GAMS (for testing parameter setup)
python run_simulation.py --dry-run
```

Typical solve times per scenario:
- Tutorial-scale model (demo GAMS license): 5–15 min
- Full MESSAGEix-GLOBIOM snapshot: 30–90 min (requires full GAMS license)

---

## GAMS license limits

The **demonstration license** bundled with GAMS restricts model size to
roughly 2 000 rows × 2 000 columns. MESSAGEix tutorial scenarios (Westeros,
Dantzig) fit within this limit. The MESSAGEix-GLOBIOM R11 snapshot at full
resolution (~35 000 rows) requires a full license.

**Options for the demo license:**
1. Use the `--dry-run` flag to test parameter configuration without solving.
2. Work with the `tutorial` model included in `message_ix[tutorial]`.
3. Apply for an academic GAMS license (free for academic institutions).
4. Use the GAMS Cloud (per-solve pricing) for production runs.

---

## ixmp backends

| Backend | Java? | Notes |
|---------|-------|-------|
| `ixmp4` (SQLite) | No | Default; lightweight; no Java dependency |
| `hsqldb` | Yes (11+) | Full-featured; required for large snapshot models |

Switch via: `python run_simulation.py --backend hsqldb`

The database is stored at `results/ixmp4.db` (ixmp4) or `results/ixmp_db` (hsqldb).

---

## How policy parameters are applied

MESSAGEix is a **cost-minimisation** LP. Policy levers map directly to
named model parameters:

### `tax_emission` — Carbon price ($/tCO2)

The primary decarbonisation lever. MESSAGEix minimises total discounted system
cost including the carbon cost on all CO2-emitting technologies.

```python
# From scenarios/ssp1.py (SSP1, AFR node)
{2020: 80, 2025: 130, 2030: 210, 2035: 320, 2040: 440, 2045: 500, 2050: 500}
```

**SSP4 inequality signal** (tax_emission 2050):

| Node | SSP | USD/tCO2 | S4 Region |
|------|-----|----------|-----------|
| AFR  | SSP4 | 25 | Africa (poor region, weak enforcement) |
| WEU  | SSP4 | 500 | Europe (rich region, strong institutions) |
| WEU  | SSP1 | 800 | Europe (aggressive 1.5 °C pathway) |

### `bound_emission` — Annual emission cap (Mt CO2/yr)

A hard upper bound on total CO2 from the electricity sector, per node and year.
Applied as a complementary constraint alongside the carbon price.

```python
# SSP1 WEU: tight cap consistent with 1.5°C
{2020: 1950, 2025: 1330, 2030: 800, 2035: 420, 2040: 175, 2045: 55, 2050: 12}

# SSP5 WEU: essentially non-binding
{2020: 6000, 2025: 8500, ..., 2050: 37000}
```

### `growth_activity_up` — Technology growth rate ceiling

Maximum permitted period-over-period growth in technology activity. Used to
constrain runaway fossil deployment in low-policy scenarios and prevent the
optimizer from building unlimited coal in SSP3/SSP5.

```python
# SSP1: no new coal in any region
"coal_ppl": {node: 0.00 for node in all_nodes}

# SSP5: unrestricted fossil expansion
"coal_ppl": {node: 0.15 for node in all_nodes}  # 15% growth/period
```

### `emission_factor` — Project-calibrated coal EF (Mt CO2/GWa)

From `scenarios/base_params.py`, applied to all SSPs:

| Node | Coal EF (Mt CO2/GWa) | Source |
|------|---------------------|--------|
| AFR  | 12.50 | Hydro_AF 150 000 tCO2 / 30 MW |
| CPA/PAS/SAS | 14.64 | Hydro_AS 834 218 tCO2 / 150 MW |
| WEU/EEU/FSU | 8.75 | Hydro_EU 6 126 tCO2 / 2 MW |
| LAM  | 6.94 | No project; gas-heavy grid (estimated) |

### `bound_activity_up` — Hydro retrofit capacity (GWa/yr)

Maximum annual hydro activity from the retrofit projects:

```python
# AFR: 0.030 GW × 0.40 CF = 0.0120 GWa/yr
# SAS: 0.150 GW × 0.38 CF = 0.0570 GWa/yr
# WEU: 0.002 GW × 0.35 CF = 0.0007 GWa/yr
```

---

## MESSAGEix R11 node → S4 region aggregation

| S4 Region | MESSAGEix nodes | Notes |
|-----------|----------------|-------|
| Africa    | AFR | Sub-Saharan Africa |
| Asia      | CPA, PAS, SAS | China, Pacific Asia, South Asia |
| Europe    | WEU, EEU, FSU | Western/Eastern Europe, Former Soviet Union |
| LATAM     | LAM | Latin America |
| Excluded  | NAM, MEA, PAO | N. America, Mid. East, Pacific OECD |

`iamc_bridge.py` aggregates via `NODE_MAP` before computing regional totals.

---

## Outputs

Same format and model column as OSeMOSYS and GCAM:
- `model = "MESSAGEix|message-ix"`
- All IAMC variable names identical

### Cross-model comparison

```python
import pyam

# Load all three model outputs
osemosys  = pyam.IamDataFrame("osemosys/results/iamc_all_scenarios.csv")
gcam      = pyam.IamDataFrame("gcam/results/iamc_all_scenarios.csv")
messageix = pyam.IamDataFrame("messageix/results/iamc_all_scenarios.csv")

combined = pyam.concat([osemosys, gcam, messageix])

# model column: "OSeMOSYS|tz-osemosys" / "GCAM|pygcam" / "MESSAGEix|message-ix"
co2 = combined.filter(
    scenario="SSP4-6.0",
    variable="Emissions|CO2|Energy|Supply|Electricity",
    region=["Africa", "Europe"],
)
co2.plot(color="model", title="SSP4 CO2: three-model comparison")
```

### tvp_dbio factors

```python
factors = pd.read_csv("messageix/results/tvpdbio_intensity_factors.csv")

# SSP4 inequality — MESSAGEix version
ssp4 = factors[factors["scenario"] == "SSP4-6.0"].pivot(
    index="region", columns="year", values="adj_ratio_ghg"
)
print(ssp4)
# Africa row: slow decarbonisation (low tax, high coal EF)
# Europe row: fast decarbonisation (high tax, lower coal EF)
```

---

## MESSAGEix vs OSeMOSYS vs GCAM

| Aspect | OSeMOSYS | GCAM | MESSAGEix |
|--------|----------|------|-----------|
| Technology set | 6 (explicit) | 50+ | 20+ (from GLOBIOM snapshot) |
| Demand | Exogenous (YAML) | Endogenous | Exogenous (calibrated in snapshot) |
| Policy lever | CO2 caps | Carbon price + RES | Carbon price + emission cap + growth |
| Solver | HiGHS (pip) | GCAM C++ | GAMS (license) |
| Cross-sector | No | Energy-water-land | Energy only (electricity module) |
| Spatial | Custom 4 regions | 32 regions → 4 | R11 (8 mapped → 4) |
| Runtime | ~8 s/scenario | 15–30 min | 5–90 min (license-dependent) |
| Snapshot | Not applicable | Not applicable | Zenodo GLOBIOM R11 (400 MB) |

MESSAGEix is particularly valuable when you need:
1. An IIASA-provenance world model (directly comparable to IIASA published scenarios)
2. Technology learning and investment dynamics beyond OSeMOSYS's exogenous capex
3. Nuclear, CCS, and biomass technologies not in the S4 OSeMOSYS model
