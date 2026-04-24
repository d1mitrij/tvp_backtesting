# S4 Scenarios — REMIND-MAgPIE IPCC Simulation Suite

Integrated climate-finance scenario modelling for sustainable infrastructure
investment. Combines two independent regional energy system models — OSeMOSYS
and GCAM — with all five IPCC AR6 Shared Socioeconomic Pathways (SSP1–SSP5)
to produce time-varying supply-chain intensity factors for the `tvp_dbio`
infrastructure assessment framework.

Model parameters are calibrated to the actual S4 project portfolio:
hospital, hydro, and rail projects in Africa, Asia, Europe, and LATAM.
Coal emission factors, hydro retrofit capacities, and rail electricity demand
are derived directly from the finance CSVs in `modeled_input_data/`.

---

## Simulation frameworks

| Framework | Solver | Runtime | Energy detail | Use case |
|-----------|--------|---------|---------------|----------|
| **OSeMOSYS** (tz-osemosys) | HiGHS LP (pip) | ~8 s/scenario | 6 technologies | Rapid iteration, transparent parameters |
| **GCAM** (pygcam) | GCAM C++ (compiled) | 15–30 min/scenario | 50+ technologies, cross-sector | Full energy-water-land nexus |
| **MESSAGEix** (message-ix) | GAMS (demo license) | 5–90 min/scenario | 20+ (GLOBIOM snapshot) | IIASA-provenance, technology learning |

All produce identical IAMC output columns (`model` field distinguishes them)
so results are directly comparable in pyam.

---

## Repository layout

```
s4_scenarios/
├── scenarios_registry.py        Single source of truth: SSP metadata, SCC params, DAMAGE_MODELS
├── scc_damage_analysis.py       Damage cost breakdown (GIVE / FUND / META-2021 / DICE-2023R)
├── ipcc_nexus_weights.py        AR6 Water / Land / Social shadow-price weights (optional)
│
├── modeled_input_data/          Project finance inputs (shared by both models)
│   ├── assumptions.txt
│   ├── hospitals_finance_input.csv   Proj_001–003 (LATAM, Africa, Europe)
│   ├── hydro_finance_input.csv       Hydro_AF, Hydro_AS, Hydro_EU
│   └── rail_finance_input.csv        Rail_EU_DEV, Rail_EU_OP1, Rail_EU_OP2
│
├── osemosys/                    OSeMOSYS energy system simulation
│   ├── derive_parameters.py     CSV → coal EFs, hydro GW, rail PJ
│   ├── iamc_bridge.py           xr.Dataset → IAMC + tvp_dbio factors
│   ├── run_simulation.py        CLI runner (all 5 SSPs, ~45 s total)
│   ├── requirements.txt
│   ├── model/
│   │   ├── base.yaml            Technology library (6 techs, 4 regions)
│   │   ├── ssp1.yaml … ssp5.yaml   SSP-specific demand + CO2 caps + RES targets
│   └── results/
│       ├── iamc_ssp{1-5}.csv
│       ├── iamc_all_scenarios.csv   (3,780 rows)
│       └── tvpdbio_intensity_factors.csv   (140 rows)
│
├── gcam/                        GCAM energy system simulation (pygcam)
│   ├── derive_parameters.py     Re-exports osemosys/derive_parameters.py
│   ├── iamc_bridge.py           GCAM query CSV → IAMC + tvp_dbio factors
│   ├── run_simulation.py        Orchestrator: gt run → gt query → IAMC
│   ├── requirements.txt
│   ├── config/
│   │   ├── project.xml          pygcam project: 5 scenarios, steps, queries
│   │   └── queries/             GCAM output query XML files (4 queries)
│   ├── xml/
│   │   ├── project_params.xml   CSV-derived: coal efficiency, hydro, rail
│   │   └── ssp{1-5}_policy.xml  Carbon prices + RES standards per SSP
│   └── results/                 Generated outputs (same format as osemosys/)
│
├── source/                      Reference literature
│   ├── integrated_mrio_ssp_synthesis.md
│   ├── ipbes/
│   └── wg6/
│
├── messageix/                   MESSAGEix energy system simulation (message-ix)
│   ├── derive_parameters.py     Re-exports osemosys/derive_parameters.py
│   ├── iamc_bridge.py           MESSAGEix vars → IAMC + tvp_dbio factors
│   ├── run_simulation.py        Orchestrator: clone → configure → solve → extract
│   ├── requirements.txt
│   └── scenarios/               SSP parameter modules (ssp1–ssp5 + base_params)
│
└── doc/                         Technical documentation
    ├── 01_installation.md       OSeMOSYS + GCAM + MESSAGEix installation
    ├── 02_configuration.md      OSeMOSYS YAML system + derive_parameters.py
    ├── 03_analysis.md           OSeMOSYS outputs, pyam, tvp_dbio
    ├── 04_gcam_analysis.md      GCAM workflow, policy XML, region mapping
    └── 05_messageix_analysis.md MESSAGEix workflow, ixmp, GAMS, R11 nodes
```

---

## Quick start

### OSeMOSYS (no external dependencies)

```bash
cd osemosys
pip install -r requirements.txt
python run_simulation.py                       # all 5 SSPs (~45 s)
python run_simulation.py --scenario ssp4 ssp5  # two scenarios
```

### GCAM (compile from source on Linux; release package on Mac/Windows)

```bash
# Prerequisites: compile GCAM, generate XML data (~2–3 h first run)
# See doc/01_installation.md for full build instructions
cd gcam
pip install -r requirements.txt
python run_simulation.py                       # all 5 SSPs (~2 h)
python run_simulation.py --dry-run             # print gt commands only
```

### MESSAGEix (requires GAMS demo license + Zenodo snapshot)

```bash
cd messageix
pip install "message-ix[report,tutorial]" message-ix-models gamspy
mix-models fetch snapshot-1                    # ~400 MB from Zenodo (once)
python run_simulation.py --dry-run             # validate params, no GAMS solve
python run_simulation.py                       # all 5 SSPs (~5–90 min)
```

### Damage cost analysis (any framework, run from project root)

```bash
# After at least one simulation framework has produced results:
python scc_damage_analysis.py
# Outputs: results_scc_damage.csv  (~4 200 rows)
# Prints:  SCC schedule, CO2 emissions summary, damage pivot tables by model
```

---

## Scenario coverage

| Scenario | IAMC label | Narrative | Temp. |
|----------|-----------|-----------|-------|
| ssp1 | SSP1-1.9 | Sustainability — global cooperation, efficiency | 1.5 °C |
| ssp2 | SSP2-4.5 | Middle of the Road — current trends | ~2 °C |
| ssp3 | SSP3-7.0 | Regional Rivalry — fragmented, fossil-heavy | 3–4 °C |
| ssp4 | SSP4-6.0 | Inequality — rich regions decarbonise, poor lag | ~3 °C |
| ssp5 | SSP5-8.5 | Fossil-Fueled Development — high growth | 4–5 °C |

---

## Key output: tvp_dbio GHG intensity adjustment ratios

`results/tvpdbio_intensity_factors.csv` — `adj_ratio_ghg` scales the
`tvp_dbio` `s_ghg[Energy_Utilities]` intensity to project future supply-chain
GHG under each SSP.

**OSeMOSYS — Europe adj_ratio_ghg (relative to 2020):**

| Scenario | 2025 | 2030 | 2040 | 2050 |
|----------|------|------|------|------|
| SSP1-1.9 | 0.61 | 0.31 | 0.08 | 0.00 |
| SSP2-4.5 | 0.85 | 0.67 | 0.36 | 0.00 |
| SSP3-7.0 | 0.91 | 0.83 | 0.47 | 0.00 |
| SSP4-6.0 | 0.67 | 0.34 | 0.11 | 0.00 |
| SSP5-8.5 | 0.92 | 0.84 | 0.60 | 0.00 |

**SSP4 inequality signal** (OSeMOSYS, 2030):

| Region | adj_ratio_ghg | Interpretation |
|--------|--------------|----------------|
| Africa | 0.648 | Slow (low carbon price, limited capital) |
| Europe | 0.337 | Fast (high carbon price, Rail_EU_DEV institutions) |

**Cross-model comparison**: Run both frameworks and report the range:
```python
import pyam

osemosys = pyam.IamDataFrame("osemosys/results/iamc_all_scenarios.csv")
gcam     = pyam.IamDataFrame("gcam/results/iamc_all_scenarios.csv")
combined = pyam.concat([osemosys, gcam])
# model column distinguishes "OSeMOSYS|tz-osemosys" vs "GCAM|pygcam"
```

---

## Shared scenario registry

`scenarios_registry.py` (project root) is the **single source of truth** for
SSP metadata, SCC parameters, and damage-model sector weights.  All three
simulation frameworks and `scc_damage_analysis.py` import from it; a change
to any label or value propagates everywhere.

```python
from scenarios_registry import SSP_REGISTRY, DAMAGE_MODELS, SCC_BASE
```

---

## Damage cost analysis

`scc_damage_analysis.py` monetises electricity-sector CO2 from all available
simulation frameworks into annual damage costs using four named IAM damage
models applied in parallel:

| Model | Reference | Distinguishing feature |
|-------|-----------|------------------------|
| **GIVE** | Rennert et al. (2022) *Nature* | Highest Ecosystems share (37 %) |
| **FUND** | Anthoff & Tol, FUND 3.9 (2014) | Explicit Water Resources (16 %) |
| **META-2021** | Dietz et al. (2021) *Nature CC* | Tipping-point amplification |
| **DICE-2023R** | Nordhaus (2023) | Reduced-form quadratic; Agriculture + Health dominant |

SCC base values are calibrated to IPCC AR6 WG3 Chapter 2 SSP warming
trajectories (real 2020 USD/tCO2, 2.5 %/yr DICE-2023R growth rate):

| Scenario | 2020 SCC | Rationale |
|----------|----------|-----------|
| SSP1-1.9 | $130/t | Steep early mitigation caps future exposure |
| SSP2-4.5 | $190/t | Central US EPA (2023) estimate |
| SSP3-7.0 | $310/t | High warming → convex damage acceleration |
| SSP4-6.0 | $260/t | Regional inequality amplifies vulnerability |
| SSP5-8.5 | $420/t | Highest warming; tail-risk damages dominant |

Output: `results_scc_damage.csv` — `sim_model × damage_model × scenario ×
region × year × category` rows (≈ 4 200 rows with OSeMOSYS only).

---

## References

- IPCC AR6 WGI/WGII/WGIII/SYR — `source/wg6/`
- IPBES Global Assessment 2022 — `source/ipbes/`
- Integrated MRIO-SSP synthesis — `source/integrated_mrio_ssp_synthesis.md`
- tz-osemosys: https://github.com/transition-zero/tz-osemosys
- GCAM: https://github.com/JGCRI/gcam-core
- pygcam: https://pygcam.readthedocs.io
- pyam: https://pyam-iamc.readthedocs.io
