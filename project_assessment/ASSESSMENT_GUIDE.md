# S4 Portfolio Assessment — Guide

How to run the integrated impact assessment for the nine S4 infrastructure
projects (Health, Energy, Transport) across Africa, Asia, Europe, and LATAM.

---

## What the assessment does

Four independent analytical passes over the same project inputs
(`project_assessment/modeled_input_data/`):

| Pass | Tool | What it measures |
|------|------|-----------------|
| 1 | **tvp_dbio** | Supply-chain GHG, employment, water use, and value added (tiers 0–5) |
| 2 | **tvp_scenario** | SSP1–5 scenario GHG adjustment factors for 2025 / 2030 / 2040 |
| 3 | **tvp_dependency** | Nature-related dependency risk (ENCORE, WWF, InVEST, TNFD LEAP) |
| 4 | **GHG transition-risk** | Avoided vs supply-chain GHG monetised under UBA and REMIND-MAgPIE |

---

## Prerequisites

### Python environment

The simplest setup uses a single conda environment that satisfies all three
submodules. From the repository root:

```bash
conda env create -f tvp_dbio/environment.yml
conda activate env_dbio
pip install -r tvp_scenario/osemosys/requirements.txt
pip install pandas numpy
```

For the dependency pipeline only:

```bash
pip install pandas numpy
# InVEST (optional — only needed to execute biophysical models):
pip install natcap.invest
```

### Scenario results (optional pre-step)

The OSeMOSYS scenario results are **already committed** in
`tvp_scenario/osemosys/results/`. If you need to regenerate them:

```bash
cd tvp_scenario/osemosys
pip install -r requirements.txt
python run_simulation.py          # all 5 SSPs, ~45 s
cd ../..
```

GCAM and MESSAGEix alternatives require compiled C++ / GAMS installations;
see `tvp_scenario/doc/` for full instructions. `assess.py` uses OSeMOSYS
results by default.

---

## Running the assessment

### Full run (recommended)

From the repository root:

```bash
python assess.py
```

This runs all three passes and writes results to `results/`.

### Skip dependency re-run (faster)

The dependency pipeline outputs are already in
`tvp_dependency/assessment_output/`. To load them without re-running:

```bash
python assess.py --skip-dependency
```

### Custom tier range

By default, supply-chain tiers 0–5 are computed (captures >99% of the
upstream signal). To change:

```bash
python assess.py --tiers 0 8    # all tiers including deep upstream
python assess.py --tiers 0 2    # quick run: direct + first two upstream rounds
```

---

## Outputs

All files are written to `results/`:

| File | Description |
|------|-------------|
| `supply_chain.csv` | Tier-by-tier breakdown: sector, GHG, employment, water, value added |
| `supply_chain_summary.csv` | Project totals (tiers summed) |
| `scenario_adjustment.csv` | OSeMOSYS GHG intensity factors per region × scenario × year |
| `scenario_ghg_adjusted.csv` | Scenario-adjusted GHG per project × scenario (pivot table) |
| `dependency_summary.csv` | Merged WWF risk scores and TNFD stress-test table |
| `final_analysis.md` | Narrative synthesis: findings, compounding risks, priority actions |

Additional outputs from the dependency pipeline are in
`tvp_dependency/assessment_output/` (ENCORE materiality tables,
InVEST configs, heatmap).

---

## Running individual passes manually

### Supply-chain only (tvp_dbio)

```python
import sys
sys.path.insert(0, "tvp_dbio")
import tvp_io_lib as io

# Tier-by-tier breakdown for Rail_EU_DEV
df = io.tier_impact(
    invest_usd  = 1_998_000_000,
    sector_code = "Rail_Dev",
    country     = "Europe",
    database    = "exiobase",
    tier_from   = 0,
    tier_to     = 5,
)
print(df.groupby("tier")[["GHG_tCO2e", "Employment_FTE"]].sum())
```

### Scenario factors only (tvp_scenario)

```python
import pandas as pd
factors = pd.read_csv("tvp_scenario/osemosys/results/tvpdbio_intensity_factors.csv")
europe = factors[factors["region"] == "Europe"]
print(europe.pivot_table(index="scenario", columns="year", values="adj_ratio_ghg"))
```

### Dependency pipeline only (tvp_dependency)

```bash
cd tvp_dependency
python -m dependency_profiler.pipeline
# or
python dependency_profiler/pipeline.py
```

---

## Project inputs

All three passes read the same three CSV files:

```
project_assessment/modeled_input_data/
├── assumptions.txt                  Methodology and sector assumptions
├── hospitals_finance_input.csv      Proj_001 (LATAM), Proj_002 (Africa), Proj_003 (Europe)
├── hydro_finance_input.csv          Hydro_AF, Hydro_AS, Hydro_EU
└── rail_finance_input.csv           Rail_EU_DEV, Rail_EU_OP1, Rail_EU_OP2
```

To add or modify projects, edit these CSVs; `assess.py` and the dependency
pipeline both read them at runtime.

---

---

## GHG transition-risk analysis (Pass 4)

### Notebooks and scripts

| File | Purpose |
|------|---------|
| `ghg_avoided_vs_supply_chain.ipynb` | Core GHG backtesting — avoided vs supply-chain, UBA and REMIND-MAgPIE valuation across all 6 IPCC AR6 scenarios |
| `ghg_communication_figures.ipynb` | Investor-facing communication figures (worst/best per project, sector, country) |
| `ghg_communication_figures.py` | Standalone script version of the communication figures |

### Methodology

1. **Avoided GHG** — self-reported annual avoided emissions (tCO₂e/yr) from
   `greenings_backtesting/03_monetisation_inputs.csv`.

2. **Supply-chain GHG** — Tier-0 + Tier-1 footprint per project from
   Exiobase 3.8.1 via `tvp_io_lib.tier0_impact` / `tier1_impact`.

3. **UBA Central baseline** — monetised at 412.50 USD/tCO₂e (UBA
   Methodological Convention 4.0, 2030, CO₂_CO₂eq, PRTP 1 %, EUR × 1.10).

4. **REMIND-MAgPIE country weighting** — R5 regional multipliers from IPCC
   AR6 WG3 Ch. 3 / Annex III applied to WifOR global 2030 coefficients and
   to the UBA Central price to produce country-specific forward-looking
   values for six IPCC scenarios (C1/SSP1-1.9 through C8/SSP5-8.5).

### Running the GHG analysis

```bash
# Full notebook (core analysis + all figures)
jupyter notebook project_assessment/ghg_avoided_vs_supply_chain.ipynb

# Communication figures notebook
jupyter notebook project_assessment/ghg_communication_figures.ipynb

# Communication figures as a script
python project_assessment/ghg_communication_figures.py
```

### Communication figure outputs

All saved to `greenings_backtesting/`:

| File | Description |
|------|-------------|
| `comm_fig1_per_project.png` | Dot-range chart — worst/UBA/best per project |
| `comm_fig2_sector.png` | Grouped bars — worst/UBA/best per sector |
| `comm_fig3_geography.png` | Range bands — worst-to-best per country |

---

## Submodule reference

| Submodule | Path | Purpose |
|-----------|------|---------|
| tvp_dbio | `tvp_dbio/` | MRIO supply-chain library (`tvp_io_lib.py`) |
| tvp_scenario | `tvp_scenario/` | OSeMOSYS / GCAM / MESSAGEix SSP simulations |
| tvp_dependency | `tvp_dependency/` | ENCORE / WWF / InVEST / TNFD pipeline |
| transitionvaluation | `transitionvaluation/` | UBA value-factor tables (submodule) |
