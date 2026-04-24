# Configuration

The model is defined in a two-layer YAML system: a **base file** that
specifies the energy system structure (technologies, costs, capacity) and
**scenario overlay files** that provide SSP-specific demand, emission limits,
and renewable targets. The two layers are merged at runtime by `Model.from_yaml()`.

A companion Python module, `derive_parameters.py`, reads the three project
finance CSVs and derives every region-specific model parameter that is
grounded in observed project data — coal emission factors, hydro retrofit
capacities, and rail electricity demand. This ensures the model is calibrated
to the actual S4 portfolio rather than generic literature values.

---

## File map

```
osemosys/
├── derive_parameters.py   Reads CSVs → region-specific model parameters
├── run_simulation.py      Orchestrates all 5 SSPs; calls iamc_bridge.py
├── iamc_bridge.py         Converts xr.Dataset solution to IAMC + tvp_dbio factors
└── model/
    ├── base.yaml          Technology library, regions, impacts — shared across SSPs
    ├── ssp1.yaml          SSP1-1.9  Sustainability        (1.5 °C)
    ├── ssp2.yaml          SSP2-4.5  Middle of the Road    (2 °C)
    ├── ssp3.yaml          SSP3-7.0  Regional Rivalry      (3–4 °C)
    ├── ssp4.yaml          SSP4-6.0  Inequality            (3 °C, polarised)
    └── ssp5.yaml          SSP5-8.5  Fossil-Fueled Growth  (4–5 °C)
```

---

## derive_parameters.py — project-calibrated inputs

`derive_parameters.py` reads the three CSVs in `modeled_input_data/` and
derives the key model parameters listed below. Region names match the CSV
values exactly: **Africa, Asia, Europe, LATAM**.

### Derived coal emission factors (Mt CO2/PJ electricity)

Derived from the avoided-CO2 data in `hydro_finance_input.csv` using:

```
EF = avoided_CO2_t / 1e6 / (capacity_MW × H_per_year × CF × 1e-6 × 3.6)
```

| Region | Project | Avoided CO2 | Capacity | CF | Coal EF (Mt CO2/PJ) |
|--------|---------|-------------|----------|----|---------------------|
| Africa | Hydro_AF | 150,000 t/yr | 30 MW | 0.40 | **0.3964** |
| Asia   | Hydro_AS | 834,218 t/yr | 150 MW | 0.38 | **0.4641** |
| Europe | Hydro_EU | 6,126 t/yr   | 2 MW   | 0.35 | **0.2775** |
| LATAM  | (no project) | — | — | — | **0.2200** (estimated) |

Africa and Asia show higher coal emission factors than Europe, reflecting
the coal-heavy marginal grids in those regions.

### Derived HYDRO_RETRO capacity limits (GW)

Derived from project budgets at the $1,000/kW refurbishment benchmark:

| Region | Project | Budget | Max capacity |
|--------|---------|--------|--------------|
| Africa | Hydro_AF (refurbishment)   | $30 M  | 0.030 GW |
| Asia   | Hydro_AS (large-scale)     | $150 M | 0.150 GW |
| Europe | Hydro_EU (efficiency tweak)| $2 M   | 0.002 GW |
| LATAM  | (no project)               | —      | 0.000 GW |

### Derived rail electricity demand (PJ/yr)

From `rail_finance_input.csv`, the Rail_EU_DEV project (development stage,
Europe, 5.5 M passengers/yr, ~5 kWh/passenger):

```
0 PJ for Africa, Asia, LATAM (no electrified rail project)
Europe: 5,500,000 × 5 kWh × 3.6e-9 PJ/kWh = 0.099 PJ/yr
```

This increment is embedded in the European electricity demand trajectories
in each SSP file (2025 and beyond).

---

## base.yaml — model structure

### Temporal horizon

```yaml
time_definition:
  id: td
  years: [2020, 2025, 2030, 2035, 2040, 2045, 2050]
```

Seven time steps at 5-year intervals align with REMIND-MAgPIE output
resolution and IPCC AR6 mitigation pathway benchmarks.

### Regions

```yaml
regions:
  - id: Africa   # Sub-Saharan Africa (Proj_002 hospital, Hydro_AF)
  - id: Asia     # South/Southeast Asia (Hydro_AS)
  - id: Europe   # Europe (Proj_003 hospital, Hydro_EU, Rail_EU_DEV)
  - id: LATAM    # Latin America (Proj_001 hospital)
```

Region names match the `modeled_input_data/` CSV column values exactly.

### Commodities

A single commodity (`ELC`, electricity) is modelled. Upstream fuel supply
chains are represented implicitly through `opex_variable` and
`emission_activity_ratio`.

### Impacts — background carbon price

```yaml
impacts:
  - id: CO2
    penalty:
      Africa: {"*": 15}    # M$/Mt CO2 = $/tonne CO2
      Asia:   {"*": 20}
      Europe: {"*": 60}
      LATAM:  {"*": 25}
```

The base penalty is a background carbon price. Per-scenario emission
constraints (`constraint_annual` in the SSP files) are the binding lever;
the penalty influences dispatch order within those constraints.

### Technology library

Six technology types are defined with region-specific parameters.

#### Unit conventions

| Parameter | Unit | Notes |
|-----------|------|-------|
| `capacity_activity_unit_ratio` | PJ / (GW · yr) | 31.536; converts GW to PJ/yr at 100% CF |
| `capex` | M$ / GW | Overnight capital cost |
| `opex_fixed` | M$ / (GW · yr) | Annual fixed O&M |
| `opex_variable` | M$ / PJ | Variable O&M + implied fuel cost |
| `emission_activity_ratio` | Mt CO2 / PJ | CO2 intensity of electricity output |
| `residual_capacity` | GW | Pre-existing installed capacity by region and year |
| `capacity_additional_max` | GW | Upper bound on new investment per period |

#### COAL_PP — Coal power plant

Project-calibrated emission factors (one per region) from hydro avoided-CO2 data:

```yaml
emission_activity_ratio:
  Africa: {"CO2": {"*": 0.3964}}
  Asia:   {"CO2": {"*": 0.4641}}
  Europe: {"CO2": {"*": 0.2775}}
  LATAM:  {"CO2": {"*": 0.2200}}
```

Residual capacity (2020 baseline, linear retirement over 30-year operating life):

| Region | 2020 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 |
|--------|------|------|------|------|------|------|------|
| Africa | 65 GW | 54.2 | 43.3 | 32.5 | 21.7 | 10.8 | 0 |
| Asia   | 350 GW | 291.7 | 233.3 | 175.0 | 116.7 | 58.3 | 0 |
| Europe | 100 GW | 83.3 | 66.7 | 50.0 | 33.3 | 16.7 | 0 |
| LATAM  | 35 GW | 29.2 | 23.3 | 17.5 | 11.7 | 5.8 | 0 |

#### GAS_PP — Gas combined cycle (CCGT)

Emission factor: 56 g CO2/MJ / 0.55 efficiency = 0.102 Mt CO2/PJ. Capacity
factor 0.45; residual retires over 25 years (to zero by 2045).

#### HYDRO_EXIST — Existing hydro fleet

60-year operating life; residual capacity declines slowly (~1/60 per year).
`capacity_additional_max = 0` prevents the optimiser from treating the
near-zero capex (0.001 M$/GW) as a free investment option.

```yaml
capacity_additional_max:
  "*": {"*": 0.0}    # no new builds; modelled via residual_capacity only
```

> **Critical constraint:** Without this, the optimiser builds unlimited
> "existing hydro" to exploit the near-zero capex, suppressing all fossil
> dispatch and zeroing CO2 emissions unrealistically.

Residual capacity (2020 → 2050, linear decline):

| Region | 2020 | 2050 |
|--------|------|------|
| Africa | 40 GW | 30 GW |
| Asia   | 150 GW | 112.5 GW |
| Europe | 220 GW | 170 GW |
| LATAM  | 185 GW | 140.6 GW |

#### HYDRO_RETRO — Hydro retrofit (project-linked)

Capex 1,000 M$/GW ($1,000/kW). Maximum new capacity is project-budget-derived:

```yaml
capacity_additional_max:
  Africa: {"2020": 0.0, "2025": 0.030, …}   # Hydro_AF: $30M
  Asia:   {"2020": 0.0, "2025": 0.150, …}   # Hydro_AS: $150M
  Europe: {"2020": 0.0, "2025": 0.002, …}   # Hydro_EU: $2M
  LATAM:  {"*": 0.0}                         # no project
```

#### SOLAR_PV — Utility-scale solar PV

Learning-curve capex (M$/GW):

| Year | 2020 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 |
|------|------|------|------|------|------|------|------|
| M$/GW | 1,200 | 850 | 600 | 480 | 400 | 360 | 340 |

Capacity factors: Africa 0.25, Asia 0.22, Europe 0.15, LATAM 0.23.

#### WIND — Onshore wind

| Year | 2020 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 |
|------|------|------|------|------|------|------|------|
| M$/GW | 1,600 | 1,250 | 1,000 | 850 | 750 | 700 | 670 |

Capacity factors: Africa 0.32, Asia 0.27, Europe 0.30, LATAM 0.29.

---

## SSP scenario overlay files

Each SSP file provides three top-level YAML keys: `commodities` (demand),
`impacts` (emission limits + carbon prices), and `renewable_production_target`.
Because `Model.from_yaml()` performs a shallow dict merge, the SSP file must
supply **complete** sections (not partial overrides).

### Electricity demand (ELC demand_annual, PJ/yr) — 2050 values

| Region | 2020 | SSP1 | SSP2 | SSP3 | SSP4 | SSP5 |
|--------|------|------|------|------|------|------|
| Africa | 2,500 | 5,450 | 8,100 | 10,900 | 4,070 | 13,800 |
| Asia   | 10,000 | 15,250 | 25,000 | 42,500 | 28,000 | 51,000 |
| Europe | 12,000 | 10,200 | 15,400 | 21,500 | 10,800 | 24,600 |
| LATAM  | 4,500 | 7,450 | 10,700 | 14,700 | 9,100 | 19,800 |

**SSP narratives:**
- **SSP1** — efficiency gains moderate growth; Europe demand falls.
- **SSP2** — current trends continue; moderate growth everywhere.
- **SSP3** — high population growth in Global South; weak efficiency.
- **SSP4** — Africa/LATAM slow (poverty trap); Asia moderate; Europe stable (efficiency).
- **SSP5** — fossil-fuelled growth; very high demand everywhere.

### CO2 emission limits (constraint_annual, Mt CO2/yr)

The limits are calibrated to AR6 carbon budget allocations for each SSP-RCP.

**Africa CO2 limits:**

| Year | SSP1-1.9 | SSP2-4.5 | SSP3-7.0 | SSP4-6.0 | SSP5-8.5 |
|------|----------|----------|----------|----------|----------|
| 2020 | 950 | 1,000 | 2,100 | 1,600 | 3,000 |
| 2030 | 520 | 880 | 3,500 | 2,100 | 8,000 |
| 2050 | 20 | 410 | 9,400 | 4,600 | 32,000 |

**SSP4 inequality signature** — same year, same metric, opposite directions:
- Europe 2050: **105 Mt** (strict decarbonisation, penalty = 100 M$/Mt)
- Africa 2050: **4,600 Mt** (virtually unconstrained, penalty = 8 M$/Mt)

**SSP5 near-absence of policy:**
- Asia 2050: **80,000 Mt** (essentially non-binding)
- Carbon price: Africa/Asia 3 M$/Mt = $3/tonne CO2

### Renewable production target (minimum fraction of electricity from renewables)

| Region | SSP1 2050 | SSP2 2050 | SSP3 2050 | SSP4 2050 | SSP5 2050 |
|--------|-----------|-----------|-----------|-----------|-----------|
| Africa | 0.98 | 0.75 | 0.31 | 0.30 | 0.22 |
| Asia   | 0.97 | 0.72 | 0.27 | 0.75 | 0.20 |
| Europe | 0.99 | 0.89 | 0.50 | 0.98 | 0.42 |
| LATAM  | 0.99 | 0.83 | 0.47 | 0.76 | 0.46 |

Note: SSP4 Europe (0.98) and Africa (0.30) illustrate the within-scenario
polarisation that distinguishes SSP4 from SSP3 (where all regions are low).

---

## Adding a new technology

Add a new entry to the `technologies` list in `base.yaml` following the same
parameter structure. Ensure the new technology has `output_activity_ratio` for
`ELC` so the supply-demand balance constraint is satisfied. If it is a
renewable, add `include_in_joint_renewable_target: {"*": {"*": true}}`.
