# Data Protocol: MDB Impact Dashboard

**Version:** 1.0  
**Scope:** All data inputs, intermediate variables, and model outputs consumed or produced by `integrated_finance/app.py`  
**Source taxonomy:**
- **Primary** — data collected directly from the project client or investment team; no third-party intermediary
- **Secondary (reported)** — published data from external institutions, databases, or regulatory bodies; taken as-given
- **Modelled** — derived computationally within the system from primary or secondary inputs; reproducible given the same inputs

---

## 1. Project Identification

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| Project ID (`pid`) | string | Primary | Investment Officer | Unique within registry; alphanumeric, no spaces | Internal reference key used across all tabs and cache keys |
| Project name | string | Primary | Investment Officer | Non-empty; max 80 chars | Human-readable project label for display and export |
| Country (`country`) | ISO-3166-1 alpha-2 | Primary | Investment Officer | Must exist in `COUNTRY_REGION_MAP`; if absent defaults to region-level lookup | Country where the project infrastructure is located or majority of economic activity occurs |
| Region (`region`) | Enum: `Europe / Asia / LATAM / Africa` | Modelled | System | Auto-derived from `COUNTRY_REGION_MAP[country]`; required for EXIOBASE regional IO tables | Four-region grouping used to select the correct EXIOBASE 3.8 regional satellite |
| Sector (`sector`) | Controlled vocabulary | Primary | Investment Officer | Must exist in `ALL_SECTORS`; drives NACE mapping and ENCORE materiality lookup | Broad economic sector of the investment; maps to NACE Rev. 2 code via `PROJECT_SECTOR_TO_NACE` |
| NACE code (`nace`) | NACE Rev. 2 | Modelled | System | Auto-derived from `PROJECT_SECTOR_TO_NACE[sector]`; fallback `"Q"` | Used for WifOR H5 value-factor file lookup |

---

## 2. Financial Inputs

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| CAPEX (`capex_usd`) | USD (integer) | Primary | Investment Officer / Project Developer | > 0; entered in USD millions with 3 d.p. precision; internally stored as integer USD | Total capital expenditure of the project; the base denominator for IO intensity calculations |
| Revenue yield (`revenue_yield`) | % of CAPEX per year | Primary | Investment Officer | Range 0–30 %; represents blended annual revenue as a share of initial investment | Proxy for annual project revenue used in cashflow and NPV modelling when detailed revenue schedule is unavailable |
| OPEX ratio (`opex_ratio`) | % of CAPEX per year | Primary | Investment Officer | Range 0–20 % | Annual operating cost as a share of CAPEX; deducted from revenue yield to derive annual net cashflow before impact |
| WACC base (`wacc_base`) | % per annum | Primary | Investment Officer / Finance Team | Range 1–20 %; reflects blended cost of capital before ESG adjustment | Pre-ESG weighted average cost of capital used as the financial discount rate; adjusted downward by ESG greenium |
| Bond lifetime (`bond_years`) | Integer years | Primary | Investment Officer | Range 1–30; must be ≤ project lifetime (`B_eff = min(bond_years, project_years)`) | Duration of the financing instrument; cumulative bond payment is computed over `B_eff` years |
| Project lifetime (`project_years`) | Integer years | Primary | Project Developer | Range 5–50 | Operational lifetime of the infrastructure asset; defines the cashflow horizon |
| Focus year (`focus_year`) | Integer (YYYY) | Primary | Investment Officer / Analyst | Range 2020–2050; global across all projects in a session | Reference year for WifOR value-factor H5 file lookup; changing this year changes all monetisation coefficients |
| Default SSP scenario (`scenario`) | Enum: SSP1-1.9 / SSP2-4.5 / SSP3-7.0 / SSP4-3.4 / SSP5-8.5 | Primary | Investment Officer | Must exist in `ALL_SSPS` | IPCC AR6 Shared Socioeconomic Pathway used as the single-scenario baseline for NPV and iNPV; all five scenarios are computed in the SSP comparison tab |

---

## 3. Project Impact Inputs

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| Avoided CO₂ (`avoided_co2`) | tCO₂e per year | Primary | Project Developer / Environmental Advisor | ≥ 0; annual operational figure; enter 0 if not a climate-mitigation project | Annual greenhouse gas emissions avoided relative to a counterfactual baseline; directly monetised via `c_ghg` value factor |
| Innovation level | Score 0–10 | Primary | Investment Officer | Required for AIMM market outcome score; entered manually in IO scoring panel | Self-assessed level of innovation introduced by the project relative to market practice |
| Scalability level | Score 0–10 | Primary | Investment Officer | Required for AIMM market outcome score | Self-assessed potential for the project model to be replicated or scaled across the market |
| Project outcome score | Score 0–10 | Primary | Investment Officer | Required for AIMM total score | Direct project-level outcome score per IFC AIMM guidance; combines stakeholder, economic, and environmental effects |
| SFB intensity indicators | Score 0–1 per indicator | Primary | Investment Officer | One value per indicator in `SFB_SECTORS[sector]`; default 0.5 | Sector Framework Brief intensity scores used in ETI calculation; measure the ambition level of each project output |
| Strategic uplifts | Multi-select | Primary | Investment Officer | Subset of `UPLIFT_ETI_DELTA` keys | EBRD-style additive uplifts applied to ETI base score: Local currency, Equity, SME focus, Climate-aligned, Inclusion focus |

---

## 4. Supply-Chain Model Inputs (EXIOBASE 3.8)

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| EXIOBASE sector multipliers | tCO₂e / M USD · FTE / M USD · m³ / M USD (by tier) | Secondary (reported) | WifOR / EXIOBASE consortium | Pre-computed via `tvp_io_lib`; read-only; accessed through `_run_io(capex_usd, sector, region)` | Multi-regional input-output satellite accounts; provides supply-chain emission, employment, and water intensity per unit of final demand |
| Tier 0 GHG intensity (`tier0_ghg`) | tCO₂e per year | Modelled | System | Computed as `EXIOBASE_GHG_multiplier[sector, region] × capex_usd`; cached by `(capex_usd, sector, region)` | Direct (on-site) greenhouse gas emissions attributable to the project's own production process |
| Tier 1 GHG intensity (`tier1_ghg`) | tCO₂e per year | Modelled | System | First-order upstream supply chain; computed via `tier1_impact()` in `tvp_io_lib` | GHG emissions from direct suppliers of the project (one step back in the supply chain) |
| Tier 2–10 GHG intensity | tCO₂e per year | Modelled | System | Computed via `tier_impact()` for tiers 2–10; displayed as aggregate in IO tab | Extended upstream supply-chain GHG beyond tier 1 |
| Tier 0 employment (`tier0_emp`) | FTE per year | Modelled | System | EXIOBASE employment satellite; `tier0_impact(capex_usd, sector, region, "employment")` | Direct jobs supported by the project's own operations |
| Tier 1 employment (`tier1_emp`) | FTE per year | Modelled | System | First-order upstream employment | Jobs in direct supplier firms attributable to the project |
| Tier 0 water intensity | m³ per year | Modelled | System | EXIOBASE water-use satellite | Direct freshwater use in project operations |

---

## 5. WifOR Value Factors

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| GHG shadow price — Nordhaus DICE (`c_ghg`) | USD per tCO₂e | Secondary (reported) | WifOR GmbH | Read from WifOR H5 file keyed by `(iso3, nace, focus_year)`; fallback to regional average if country not present | Social cost of carbon calibrated to the Nordhaus DICE integrated assessment model; used as the conservative GHG monetisation coefficient |
| GHG shadow price — Paris-aligned (`c_ghg_paris`) | USD per tCO₂e | Secondary (reported) | WifOR GmbH | Same H5 lookup as `c_ghg`; higher value reflecting Paris 1.5 °C abatement cost trajectory | Paris-aligned marginal abatement cost; used for sensitivity comparison and SSP1-1.9 scenario monetisation |
| Water value factor (`c_water`) | USD per m³ | Secondary (reported) | WifOR GmbH | H5 lookup by `(iso3, nace, focus_year)` | Monetised social value of freshwater use/savings; sector- and country-specific reflecting local water scarcity and productivity |
| GVA / labour-hour living-wage proxy (`c_gva`) | USD per FTE per year | Secondary (reported) | WifOR GmbH | H5 lookup by `(iso3, nace, focus_year)`; reflects country-specific GVA per working hour × living-wage adjustment | Employment monetisation coefficient; converts FTE count to USD economic value using a GVA/labour-hour approach anchored to national living-wage levels |

---

## 6. SSP Scenario Transmission Factors

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| GHG intensity adjustment ratio (`adj_ratio_ghg`) | Dimensionless | Modelled | WifOR / IPCC AR6 | Loaded via `_load_all_ssp_factors(region, focus_year)`; one value per `(region, ssp, focus_year)` | Multiplicative scalar applied to tier GHG intensities to reflect the projected decarbonisation trajectory under each SSP scenario |
| Employment adjustment ratio (`adj_ratio_emp`) | Dimensionless | Modelled | WifOR / IPCC AR6 | Same H5 source as `adj_ratio_ghg` | Scalar reflecting changes in labour productivity and employment intensity under each SSP scenario |
| Water intensity adjustment ratio (`adj_ratio_water`) | Dimensionless | Modelled | WifOR / IPCC AR6 | Same H5 source | Scalar reflecting projected changes in water-use efficiency under each SSP scenario |

---

## 7. Nature Dependency Inputs

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| ENCORE materiality score | Ordinal: None / Low / Medium / High / Very High | Secondary (reported) | NCFA / ENCORE database | Looked up by `(sector, stressor_type)`; stressors include GHG, water, land, biodiversity; read-only | Natural Capital Finance Alliance materiality matrix; maps each sector's operational dependency on specific ecosystem services |
| WWF Water Risk Filter score (`wwf_score`) | Scale 1–5 | Secondary (reported) | WWF / DEG | Looked up by `(region.lower())`; keys must be lowercase; sourced from WWF Water Risk Filter tool | Regional water scarcity and water-risk score; high scores indicate elevated physical risk from water stress for project operations |
| Dependency factor (`dep_factor`) | Dimensionless [0.33, 1.67] | Modelled | System | Computed by `_dep_factor(sector, sourcing_region, wwf_by_region)`; neutral = 1.0; capped to [0.33, 1.67] | Composite nature-dependency score combining ENCORE sector materiality and WWF regional water risk; used to adjust WACC and weight nature costs/benefits |
| ESG greenium — water discount | Basis points | Modelled | System | Sub-component of WACC adjustment; max contribution = 5 bp | WACC reduction attributable to avoided water risk, conditional on low wwf_score and project water-saving credentials |
| ESG greenium — dependency discount | Basis points | Modelled | System | Sub-component of WACC adjustment; total ESG_MAX = 10 bp | WACC reduction attributable to low nature dependency (dep_factor < 1.0); reflects market green-bond premium |
| WACC adjusted (`wacc_adj`) | % per annum | Modelled | System | `WACC_adj = WACC_base − (water_discount + dep_discount)` | Post-ESG greenium discount rate used for all DCF and iNPV calculations |

---

## 8. Computed Financial and Impact Outputs

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| Financial NPV (`npv_usd`) | USD | Modelled | System | Computed by `_compute_npv_fn(cashflows, wacc_adj)`; cashflows = `(revenue_yield − opex_ratio) × capex_usd` per year | Conventional discounted cashflow NPV; excludes all social and environmental monetisation |
| Nature debt (`nature_debt_usd`) | USD | Modelled | System | Computed at t=0 (construction phase); `nature_debt = dep_factor × capex_usd × stressor_cost_rate` | One-time construction-phase social cost of nature dependency; treated as a negative cashflow at project inception |
| Nature dividend (`nature_dividend_usd`) | USD per year | Modelled | System | Annual operational saving; discounted over project lifetime; positive when dep_factor < 1.0 | Annual monetised environmental and social benefit from nature-positive operations; computed from tier GHG, employment, and water stressor values × WifOR VFs × SSP adjustment ratios |
| iNPV (`inpv_usd`) | USD | Modelled | System | `iNPV = NPV + PV(nature_dividend) − nature_debt`; positive iNPV is investment-grade on integrated basis | Integrated Net Present Value; adds the present value of all monetised social and environmental cashflows to the financial NPV |
| Societal IRR (`s_irr`) | % per annum | Modelled | System | Computed as the discount rate that sets iNPV = 0; `None` if cashflows are monotone | Internal rate of return on the integrated (financial + social + environmental) cashflow stream |
| ETI score (`eti_score`) | Dimensionless | Modelled | Investment Officer | `eti_score = country_gap × Σ(intensity_inputs) × (1 + Σ uplifts)`; requires IO to enter intensity and select uplifts | Expected Transition Impact score per EBRD TOMS methodology; higher = greater contribution to market-economy transition |
| AIMM score (`aimm_score`) | Score 0–20 | Modelled | Investment Officer | `aimm = (project_outcome + market_outcome) × risk_factor`; risk_factor ∈ {0.5, 1.0}; requires IO to enter all three inputs | IFC Anticipated Impact Measurement and Monitoring total score; sum of project and market outcome components adjusted for delivery risk |
| Impact-adjusted Sharpe ratio | Dimensionless | Modelled | System | `sharpe = mean(iNPV across 5 SSPs) / std(iNPV across 5 SSPs)`; `None` if std = 0 (single scenario) | Portfolio risk-efficiency metric; analogous to CFA Sharpe ratio but denominated in impact space; higher = better expected impact per unit of scenario uncertainty |
| iNPV scenario VaR | USD | Modelled | System | `var = iNPV at SSP5-8.5`; tail risk under worst-case climate trajectory | Scenario-based value at risk for integrated NPV; equivalent to TCFD severe-stress-case financial impact |

---

## 9. ATQ / Country Diagnostic Data

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| ATQ country score | Score 0–1 per indicator | Secondary (reported) | EBRD TOMS / Strategy Economist | Currently populated from `ATQ_STUB_DATA`; target source: EBRD TOMS API or annual ATQ dataset CSV | Normalised score (0 = no progress, 1 = at frontier) for each of the Competitive, Green, Well-Governed etc. sub-indicators |
| ATQ frontier score | Score 1.0 per indicator | Secondary (reported) | EBRD | Fixed at 1.0 (best-in-class peer); frontier country noted per indicator in `Indicators_Overview_Upgraded.md` | Reference upper bound for each ATQ indicator; defines the gap against which country progress is measured |
| Country ATQ gap | Score 0–1 | Modelled | System | `gap = 1 − ATQ_country_score`; averaged over selected Transition Quality sub-dimensions | Magnitude of country transition gap relative to frontier; primary input to the ETI country-gap adjustment |

---

## 10. HIPSO Monitoring Data

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| HIPSO target values | Varies by indicator | Primary | Portfolio Manager / Investment Officer | Set at appraisal; stored in session state; one value per HIPSO indicator code (EN-01, CC-02, TA-07, etc.) | Ex-ante expected output/outcome values agreed at investment approval; defines the performance baseline for monitoring |
| HIPSO actual values | Varies by indicator | Primary (reported) | Project Developer / Client | Reported annually; entered manually in `st.data_editor` grid or uploaded via CSV | Realised output/outcome values as measured and reported by the project company; triggers variance flag if `(actual/target)−1 < −0.15` |
| HIPSO variance | Dimensionless | Modelled | System | `variance = (actual / target) − 1`; flagged in red if < −15% | Proportional deviation of actual performance from target; standard portfolio monitoring signal |

---

## 11. FAST-Infra Label Data

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| FAST-Infra criterion status | Boolean per criterion | Primary | Compliance Specialist | All 14 criteria must be assessed; all Baseline Requirements must be `True` before label can be generated | Confirms that each FAST-Infra criterion (Biodiversity, Climate Mitigation, … Climate Adaptation) is met at or above IFC Performance Standards baseline |
| Positive contribution evidence | File (PDF/DOCX/XLSX) | Primary | Compliance Specialist / Project Developer | At least one criterion must have evidence of contribution beyond baseline | Supporting documents demonstrating measurable positive contribution; attached via `st.file_uploader`; stored locally in session |
| FAST-Infra label status | Categorical: Pending / Certified | Modelled | System | `Certified` only when all 14 baseline criteria = True AND ≥ 1 positive contribution evidenced | Computed eligibility status for the FAST-Infra Sustainable Infrastructure Label |

---

## 12. Regulatory Reference Data

| Name | Unit | Source | Responsibility | Requirements | Description |
|:-----|:-----|:-------|:---------------|:-------------|:------------|
| Regulatory threshold values | Varies per requirement | Secondary (reported) | Compliance Specialist / Legal | Defined in `REGULATORY_MATRIX`; update when regulations change; version-controlled in file | Numeric or qualitative thresholds from SFDR, EU Taxonomy, TCFD, TNFD, SEC, AIIB EP against which model outputs are tested |
| Regulatory gap status | Categorical: Met / Review required / Data gap | Modelled | System | Computed per requirement by comparing model field value against threshold | Compliance coverage flag for each regulatory disclosure requirement; drives the gap report export |
| Jurisdiction | Controlled vocabulary | Primary | Compliance Specialist | One of: EU (SFDR/Taxonomy/CSRD), UK (TCFD), US (SEC Climate), TNFD, AIIB EP | Selected jurisdiction determines which regulatory checklist is rendered |

---

## 13. Data Quality and Update Protocol

| Data category | Update trigger | Minimum frequency | Validation rule | Responsible party |
|:--------------|:---------------|:------------------|:----------------|:------------------|
| Project financial inputs (CAPEX, WACC, etc.) | Project appraisal; material change event | At appraisal; annually for monitoring | Values within allowed ranges; `bond_years ≤ project_years` | Investment Officer |
| WifOR H5 value factors | New WifOR dataset release | Annual | Spot-check against prior year: change > 20% triggers manual review | Data team / WifOR |
| EXIOBASE IO multipliers | New EXIOBASE version release | Per EXIOBASE release cycle (~2 years) | Recompute portfolio to verify direction of tier 0/1 changes | Data team |
| SSP scenario factors | IPCC AR6 update cycle | Per IPCC release | Compare SSP2-4.5 adj_ratio_ghg to previous version; flag > 10% shift | Data team |
| ENCORE materiality | ENCORE database update | Annual | Sector-level comparison to prior version; escalate category changes | Compliance Specialist |
| WWF Water Risk Filter | WWF annual update | Annual | Regional score comparison; flag if any region changes by ≥ 1 point | Compliance Specialist / Environmental Advisor |
| ATQ country scores | EBRD TOMS annual publication | Annual | Cross-check radar chart against EBRD published report | Strategy Economist |
| HIPSO actuals | Annual client reporting | Annual; per reporting cycle | Check for biologically implausible values; variance > −50% triggers escalation | Portfolio Manager |
| Regulatory thresholds | Regulatory update / new jurisdiction | As regulations change | Legal sign-off before merging updated `REGULATORY_MATRIX` | Compliance Specialist / Legal |

---

## 14. Lineage Map (Input → Computation → Output)

```
PRIMARY INPUTS                  SECONDARY INPUTS              MODELLED INTERMEDIATES         OUTPUTS
──────────────────────────────────────────────────────────────────────────────────────────────────────
capex_usd ──────────────────→ _run_io() ──────────────────→ tier0_ghg, tier1_ghg
sector, region                  (EXIOBASE 3.8)                tier0_emp, tier1_emp

country ──────────────────────→ COUNTRY_REGION_MAP ──────→ region, iso3
                                COUNTRY_ISO2_TO_ISO3

iso3, nace, focus_year ───────→ _load_value_factors() ───→ c_ghg, c_ghg_paris,       ─→ nature_dividend_usd
                                (WifOR H5)                   c_water, c_gva

region, focus_year ───────────→ _load_all_ssp_factors() ─→ adj_ratio_ghg,            ─→ SSP-adjusted iNPV
                                (WifOR/IPCC H5)              adj_ratio_emp

sector, region ───────────────→ _compute_dep_context() ──→ dep_factor,               ─→ wacc_adj
                                (ENCORE + WWF)               wwf_score                ─→ nature_debt_usd

wacc_adj, cashflows ──────────→ _compute_npv_fn() ───────→ npv_usd
npv_usd + monetised flows ────→ _compute_metrics() ──────→ inpv_usd, s_irr           ─→ Dashboard display
                                                                                       ─→ Risk Dashboard
                                                                                       ─→ Regulatory gap matrix

country_gap + intensity ──────→ _compute_eti_score() ────→ eti_score                 ─→ IO scorecard export
project_out + market_out ─────→ _compute_aimm_score() ───→ aimm_score

portfolio (N projects × 5 SSP) → _run_multi_project() ──→ risk_summary DataFrame    ─→ CFA Risk Dashboard
                                                            (inpv_mean, inpv_std,
                                                             impact_sharpe, corr)

model outputs + thresholds ───→ REGULATORY_MATRIX ───────→ gap_status per req.       ─→ Gap report CSV
```

---

*Protocol covers 60 named data elements across 14 categories. All modelled outputs are deterministic given the same primary and secondary inputs. Secondary data sources (WifOR H5, EXIOBASE, ENCORE, WWF) are read-only within the application; updates require replacement of the underlying files by the responsible data team.*
