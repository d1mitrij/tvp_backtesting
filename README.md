# TVP Backtesting — Impact & Transition-Risk Assessment

Multi-pass impact and climate transition-risk assessment for a blended-finance
infrastructure portfolio of nine projects (hospitals, hydropower, rail) across
Colombia, Kenya, Ethiopia, India, and Germany.

---

## Central research question

> Does a uniform carbon value factor fairly price the climate transition risk
> of a geographically diversified impact investment portfolio, or does
> country- and scenario-specific pricing reveal material misvaluation —
> and what are the portfolio management implications?

---

## Repository structure

```
tvp_backtesting/
├── project_assessment/          Main analysis notebooks and scripts
│   ├── ghg_avoided_vs_supply_chain.ipynb   GHG backtesting (core analysis)
│   ├── ghg_communication_figures.ipynb     Investor communication figures
│   ├── ghg_communication_figures.py        Standalone script version
│   ├── dependency_country_comparison.ipynb Country nature-dependency comparison
│   ├── portfolio_assessment.ipynb          Integrated portfolio view
│   ├── greenings_backtesting/              Output figures (PNG)
│   └── ASSESSMENT_GUIDE.md                Full methodology guide
├── tvp_dbio/                    MRIO supply-chain library (Exiobase 3.8.1)
├── tvp_scenario/                OSeMOSYS / GCAM / MESSAGEix SSP simulations
├── tvp_dependency/              ENCORE / WWF / InVEST / TNFD pipeline
├── transitionvaluation/         UBA value-factor tables (submodule)
├── data/                        Value factors and inputs (gitignored)
└── assess.py                    Full-run entry point
```

---

## Portfolio

Nine anonymised projects — HOSP-1/2/3, HYDRO-1/2/3, RAIL-1/2/3 — totalling
USD 6.2 B CAPEX across five countries and three sectors.

| Sector | Projects | Countries | CAPEX |
|--------|----------|-----------|-------|
| Hospital | HOSP-1, HOSP-2, HOSP-3 | Colombia, Kenya, Germany | USD 547 M |
| Hydropower | HYDRO-1, HYDRO-2, HYDRO-3 | Ethiopia, India, Germany | USD 647 M |
| Rail | RAIL-1, RAIL-2, RAIL-3 | Germany (×3) | USD 5,000 M |

---

## Analytical layers

### 1 · Supply-chain GHG footprint (`tvp_dbio`)
Tier-0 and Tier-1 supply-chain GHG (tCO₂e) per project from Exiobase 3.8.1
MRIO, compared against self-reported avoided emissions from project monitoring.

### 2 · UBA baseline valuation
Monetised at the UBA Methodological Convention 4.0 Central value factor:
**412.50 USD/tCO₂e** (2030, CO₂_CO₂eq, PRTP 1 %, EUR × 1.10).

### 3 · REMIND-MAgPIE scenario weighting
Six IPCC AR6 scenarios (C1–C8) applied via country-specific R5 regional
multipliers from IPCC AR6 WG3 Ch. 3 / Annex III.  Multipliers are applied to
both the WifOR global 2030 coefficients and the UBA Central value factor to
produce country-specific forward-looking prices.

| Scenario | IPCC Cat | Warming | Global coeff (USD/t) |
|----------|----------|---------|----------------------|
| SSP1-1.9 | C1 | < 1.5 °C | 5 736 |
| SSP1-2.6 | C3 | < 2 °C   | 121 |
| SSP2-4.5 | C4 | ~2–2.5 °C | 96 |
| SSP4-6.0 | C6 | ~3 °C    | 191 |
| SSP3-7.0 | C5 | ~3 °C base | 105 |
| SSP5-8.5 | C8 | > 3 °C   | 79 |

### 4 · Nature dependency (`tvp_dependency`)
ENCORE materiality scores, WWF freshwater risk, and TNFD LEAP stress-test
per project and country.

---

## Quick start

```bash
# Full assessment (all passes)
python assess.py

# GHG analysis only — open notebook
jupyter notebook project_assessment/ghg_avoided_vs_supply_chain.ipynb

# Communication figures
jupyter notebook project_assessment/ghg_communication_figures.ipynb
# or as a script
python project_assessment/ghg_communication_figures.py
```

See `ASSESSMENT_GUIDE.md` for full setup and individual-pass instructions.

---

## Key outputs

| File | Description |
|------|-------------|
| `greenings_backtesting/comm_fig1_per_project.png` | Per-project worst/best IPCC range |
| `greenings_backtesting/comm_fig2_sector.png` | Sector worst/UBA/best grouped bars |
| `greenings_backtesting/comm_fig3_geography.png` | Country-level valuation range |
| `results/final_analysis.md` | Narrative synthesis |
| `results/supply_chain.csv` | Tier-by-tier supply-chain breakdown |
| `results/scenario_ghg_adjusted.csv` | Scenario-adjusted GHG per project |
