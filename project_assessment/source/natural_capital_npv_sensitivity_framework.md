# Natural Capital NPV Sensitivity Framework

**Integrating:** Wetzer et al. (2024) *Science* adj0598 · Transitionvaluation (Greenings/VBA) · Lastenheft Indicators (GRESB/FASTInfra/WifOR) · CFA Capital Budgeting Sensitivity Analysis

---

## 1. Conceptual Foundation

### 1.1 The Expanded Risk Triad

Standard climate risk frameworks distinguish two channels:

| Channel | Trigger | Timing |
|---|---|---|
| **Physical risk** | Direct resource damage/unavailability from climate change | Late, sudden, often irreversible |
| **Transition risk** | Policy, regulation, technology shifts repricing assets | Early, gradual, manageable if anticipated |

Wetzer et al. (2024) establish a third channel that **bridges and amplifies** both:

| Channel | Trigger | Timing |
|---|---|---|
| **Legal risk** | Attribution science + litigation translating historical resource use into liability | Concurrent with transition; accelerates into physical phase |

The legal channel matters for NPV because it transforms **externalities into internal costs** — exactly the mechanism the Transitionvaluation framework monetises. The social cost of carbon, water scarcity shadow prices, VSL-weighted air pollution damage, and ecosystem service loss that WifOR and VBA compute are not merely reporting metrics: under Wetzer's framework, they are **contingent liability estimates** that a court-ordered attribution analysis can convert into cash outflows.

> *"Legal actions determine the allocation and magnitude of climate-related financial risk exposures. Current climate risk assessments misrepresent the distribution and scale of climate-related financial risks."*
> — Wetzer, Stuart-Smith & Dibley, *Science* 383, 152–154 (2024)

---

## 2. NPV Sensitivity Mechanics for Natural Capital Inputs

### 2.1 The Natural Capital Cash Flow Model

Rewrite the standard NPV cash flow expression to make natural capital dependencies explicit:

```
Operating Income = Q × (P − V_market − V_natural) − F − L_legal
```

Where:
- `Q`         = units of output
- `P`         = output price per unit
- `V_market`  = conventional variable cost per unit (labour, energy, logistics)
- `V_natural` = natural capital cost per unit = Σ [Resource_i × Shadow_Price_i(t)]
- `F`         = fixed operating costs (unchanged by resource scenario)
- `L_legal`   = expected value of litigation liability in period t
              = Attribution_share × Social_Cost_of_Indicator_i × Quantity_used

The **contribution margin** that drives DOL and NPV becomes:

```
CM per unit = P − V_market − V_natural
```

Natural capital inputs compress CM from below — silently at first (no market price), then suddenly when legal or regulatory price materialisation triggers the scenario.

### 2.2 The Three-Channel Sensitivity Coefficient

For each natural capital indicator `i`, define:

```
Sensitivity_i = (dNPV / d Indicator_i) × Indicator_i / NPV_base
```

This coefficient is non-linear and amplified by leverage (DOL × DFL) as derived from CFA:

```
DOL_natural = Q(P − V_market − V_natural) / [Q(P − V_market − V_natural) − F]
```

When V_natural rises (resource price materialises), the denominator collapses — exactly as in the Ferndale example where price↓20% pushed NPV from +$11,871 to −$8,678. The mechanism is identical: a compressed contribution margin against fixed costs.

**Three sensitivity coefficients operate simultaneously:**

| Coefficient | Driver | Formula |
|---|---|---|
| `S_physical` | Resource unavailability (scarcity, degradation) | ΔV_natural from supply constraint |
| `S_transition` | Regulatory price (carbon tax, water tariff, land levy, biodiversity credit) | ΔV_natural from policy |
| `S_legal` | Attribution-based liability (social cost approach, Wetzer et al.) | ΔL_legal from litigation exposure |

When all three fire simultaneously — the Wetzer worst-case scenario — the NPV deterioration is multiplicative, not additive, because each compresses the same contribution margin.

---

## 3. Indicator-by-Indicator Scenario Mapping

### 3.1 Indicator Registry with Sensitivity Channels

The table below maps each natural capital indicator from the Transitionvaluation and Lastenheft frameworks to its three sensitivity channels, the applicable Wetzer assessment method, and the NPV transmission mechanism.

---

#### GROUP A — CLIMATE / ENERGY INDICATORS

**GHG Emissions** (GH1 / E2 / VF-01)
- Unit: tCO₂e/year
- Lastenheft code: GH1 (GRESB), E2.Q8W (FAST-Infra), E2 (CSRD/ESRS)
- WifOR shadow price: $/tCO₂e (country-sector, 2014–2100)

| Channel | Mechanism | Wetzer Method |
|---|---|---|
| Physical | Temperature-driven asset impairment; stranded fossil assets | Attribution of damages |
| Transition | Carbon price (ETS, carbon tax, CBAM); NDC-driven policy tightening | Social cost of carbon |
| Legal | Attribution science links Scope 1+2+3 emissions to quantified damages; Chevron precedent ($8.5T) | Social cost of carbon + market-impact analysis |

**NPV Transmission:**
Carbon price P_CO2 enters directly as V_natural = Scope1+2 × P_CO2 per unit output. A 20% rise in P_CO2 replicates the "price sensitivity" in the Ferndale table — for a carbon-intensive producer with thin margins, NPV flips negative. For Chevron, Wetzer calculates that historical Scope 1+2+3 emissions priced at the social cost of carbon yield liability ($8.5T) that **exceeds 29 years of cumulative profit** ($291B, 1990–2019), rendering the business "potentially net value-destroying."

**Dependency escape conditions:**
1. Company: Approved Science-Based Target (SBTi), credible decarbonisation pathway, internal carbon price ≥ regulatory floor
2. Country/site: NDC includes binding sectoral emission cap with enforcement mechanism

---

**Energy Consumption / Intensity** (EN1 / E3)
- Unit: MWh/year, kWh per unit output
- Lastenheft code: EN1 (GRESB)

| Channel | Mechanism |
|---|---|
| Physical | Extreme heat reduces cooling efficiency; drought reduces hydropower availability |
| Transition | Energy price volatility; renewable mandate increases OPEX for non-compliant sites |
| Legal | Indirect — embedded in GHG Scope 2 attribution chain |

**NPV Transmission:**
Energy is a variable cost (V_market component). An energy-intensive sector with high operating leverage (high F/V ratio) will see DOL spike when energy price rises simultaneously with carbon pricing — double compression of CM.

---

#### GROUP B — WATER INDICATORS

**Water Inflows / Withdrawals** (WT1 / E3.QK5)
- Unit: m³/year
- Shadow price: WRI Aqueduct scarcity factor × World Bank water tariff
- Lastenheft code: WT1, E3.1 (Pflichtenheft), E3.QK5 (FAST-Infra)

| Channel | Mechanism | Wetzer Method |
|---|---|---|
| Physical | Basin depletion, drought frequency increase; production halted at zero-water sites | Attribution of damages |
| Transition | Water pricing reform; abstraction permits; Water Stewardship certification requirements | Social cost approach (scarcity premium) |
| Legal | Litigation by downstream users, municipalities, or states for water table depletion (growing case law, e.g., Nestlé water abstraction suits) | Attribution of climate change damages |

**NPV Transmission:**
Water enters as V_natural = Volume_used × Shadow_Price_water(scarcity_factor, location).
For water-intensive sectors (agriculture, beverages, semiconductors, textiles, mining) in high-stress basins (WRI Aqueduct Risk Score > 3.0):
- Physical: Q_output must fall proportionally to water availability → revenue loss
- Transition: V_natural rises, compressing CM
- Legal: Contingent liability for historical over-abstraction

**Breakeven shift:**
If scarcity doubles the water shadow price, Q_BE = (F + C) / (P − V_market − 2×V_water). At thin margins, this pushes the breakeven above current production volume — the company loses money at its current operating level without producing fewer units.

**Dependency escape conditions:**
1. Company: ISO 14046 water management plan; Science-Based Targets for Water (SBTfw); closed-loop water recycling with documented reduction trajectory
2. Country/site: National Water Restoration Plan designating biocapacity increase for specific basin; legal Water Use Entitlement not subject to curtailment

---

**Water Outflows / Discharges** (WT2 / E4.7BL)
- Unit: m³/year discharged; pollutant load (BOD, COD, nitrogen)
- Lastenheft code: WT2, E4.2 (Pflichtenheft)

| Channel | Mechanism |
|---|---|
| Physical | Reduced dilution in low-flow conditions increases pollutant concentrations → breach of permits |
| Transition | Tightening discharge standards; effluent charges |
| Legal | Water pollution liability (EEA damage cost framework, ExternE) |

---

#### GROUP C — AIR QUALITY INDICATORS

**Air Pollution** (AP1 / E4 / VF-07)
- Unit: µg/m³ PM2.5; tons NOx, SOx per year
- Damage valuation: VSL (Value of Statistical Life) × mortality cases; 15 asthma cases per 1 µg/m³ PM2.5 per 100k population
- Lastenheft code: AP1 (GRESB), E4.1 (Pflichtenheft)

| Channel | Mechanism | Wetzer Method |
|---|---|---|
| Physical | Regulatory action triggered by breaching WHO guideline values; direct permit revocation | Attribution of damages |
| Transition | CBAM embeds air quality co-benefit pricing; ESRS E2 mandatory disclosure from 2025 | Social cost approach |
| Legal | PM2.5 litigation growing (UK's ClientEarth vs. steel plants; Dutch NOx cases); VSL methodology directly applicable | Attribution + market-impact analysis |

**NPV Transmission:**
Air pollution costs enter L_legal = (Pollution_tons × VSL_per_ton × Attribution_share). For a cement plant or coal-fired power station:
- VF-07 coefficient: 15 asthma cases per µg/m³ PM2.5 per 100k population
- VF-01: 0.025 deaths avoided per GWh of clean energy (inverse: deaths per GWh of dirty energy)
- These physical damage coefficients, combined with Wetzer's attribution science, convert emissions data into quantifiable cash liabilities

**Dependency escape conditions:**
1. Company: Approved BAT (Best Available Technology) plan with binding retrofit timeline; third-party verified emission reduction roadmap
2. Country/site: Designated Clean Air Zone with verified biocapacity/dispersion improvement (e.g., urban greening plan that demonstrably reduces local PM2.5)

---

#### GROUP D — LAND USE / BIODIVERSITY INDICATORS

**Land Siting & Land Use** (BI1 / E5 / E5.1 / E5.2)
- Unit: hectares; ecosystem service value (€/ha/year)
- Valuation: Natural Capital Protocol; IUCN; national land registries × FAO productivity factor
- Lastenheft code: BI1 (GRESB), E5.1, E5.2 (Pflichtenheft), E4 (CSRD/ESRS)

| Channel | Mechanism | Wetzer Method |
|---|---|---|
| Physical | Habitat loss reduces ecosystem services on which production depends (pollination, soil fertility, flood buffer); species loss triggers regulatory closure | Attribution of damages |
| Transition | EU Biodiversity Strategy; TNFD disclosure; No Net Loss / Net Gain requirements (UK Infrastructure Act); biodiversity credit markets | Social cost approach + accelerated mitigation |
| Legal | Ecocide law proposals (EU, Pacific); deforestation liability (EU EUDR effective 2025 for supply chains); TNFD-disclosed dependencies create attribution chain | Qualitative + attribution analysis |

**NPV Transmission:**
Land use enters as V_natural = Area × Land_Value × Productivity_Factor × Ecosystem_Service_multiplier.
For sectors with direct land dependencies (agribusiness, forestry, mining, infrastructure):
- EUDR compliance failure = market access loss (export bans) → immediate revenue shock (Q↓)
- Biodiversity credit obligation = new variable cost per unit of land disturbed
- Physical: pollinator loss alone can reduce crop yields 10–15% in exposed sectors (documented in IPBES assessment)

**Biocapacity condition (critical for this indicator):**
The escape condition is uniquely local and bilateral for land/biodiversity:
- *Company*: Approved Biodiversity Management Plan (BMP) with measurable restoration targets; engagement with Taskforce on Nature-related Financial Disclosures (TNFD)
- *Country/site*: Designated biodiversity net gain zone; protected area expansion plan; national Nature Restoration Plan (EU NRP obligatory under EU Nature Restoration Law 2024) that demonstrably increases biocapacity of the specific habitat type on which the company's production system depends

---

#### GROUP E — WASTE INDICATORS

**Waste Generation** (WS1 / E4.BR3 / VF-05)
- Unit: tonnes/year; recycling rate (%)
- Climate linkage: 0.5–1.5 tCO₂e avoided per tonne diverted from landfill (methane)
- Lastenheft code: WS1 (GRESB), E4.BR3 (FAST-Infra)

| Channel | Mechanism |
|---|---|
| Physical | Landfill methane under physical risk from higher temperatures (accelerated decomposition) |
| Transition | Extended Producer Responsibility (EPR) legislation; Circular Economy Action Plan; waste levies |
| Legal | Contaminated site liability (long-tailed; analogous to asbestos precedent); PFAS litigation |

---

#### GROUP F — SOCIAL / OCCUPATIONAL CAPITAL INDICATORS

**Occupational Health & Safety** (HS1–4 / S7 / S2.5)
- Unit: LTIFR (Lost Time Injury Frequency Rate); fatalities
- Damage valuation: ILO injury cost framework; national safety regulator benchmarks
- Lastenheft code: HS1–HS4 (GRESB), S7 (FAST-Infra)

| Channel | Mechanism | Wetzer Method |
|---|---|---|
| Physical | Heat stress incidents increase with WBGT exceedance; supply chain disruption from climate-extreme events increases contractor risk | Attribution of damages |
| Transition | ISO 45001 mandatory in procurement; ESRS S1 disclosure from 2025 | Qualitative |
| Legal | OHS litigation; director liability for climate-induced heat stress (growing legal exposure, particularly in Gulf and South/Southeast Asia) | Market-impact analysis |

---

**Fair Wages / Living Wage Gap** (S2.8)
- Unit: Living Wage premium (%); workers below living wage
- Lastenheft code: S2.8 (Pflichtenheft)

| Channel | Mechanism |
|---|---|
| Transition | Supply chain due diligence laws (CSDDD EU, German LkSG); living wage mandates |
| Legal | Supply chain liability; reputational damage triggers investor divestment (market-impact channel) |

---

**Employment and Training** (S5.1 / SE2)
- Unit: job-years; training hours; multiplier effect on GDP
- WifOR value factor: I-O multiplier (country-sector specific)
- Lastenheft code: S5.1, SE2 (GRESB)

This indicator is **positively sensitive**: companies with strong training and employment creation have higher value factors in the TVP model — meaning the NPV of their positive externalities increases, supporting green bond pricing advantages (15–20 bps inside conventional infrastructure, per Package 3).

---

## 4. The Dependency-Sensitivity Decision Tree

The following logic governs whether a given company's NPV is materially sensitive to an indicator scenario:

```
For each Indicator_i tracked for Company_j in Sector_s:

Step 1: DEPENDENCY CHECK
  Does production of Company_j require Indicator_i as a material input?
  (i.e., Is Indicator_i in the top-3 variable cost drivers OR a
   critical production constraint for Sector_s?)

  NO  → Sensitivity_i ≈ 0 (indicator immaterial to NPV)
  YES → Proceed to Step 2

Step 2: SCENARIO CHECK
  Is Indicator_i subject to an active adverse scenario?
  (Physical degradation | Regulatory price materialisation | Legal attribution)

  NO  → Sensitivity_i = Low (monitor; re-evaluate annually)
  YES → Proceed to Step 3

Step 3: MANAGEMENT PLAN CHECK
  Does Company_j hold a VERIFIED management plan that:
  (a) Quantifiably reduces dependency on Indicator_i
      (e.g., SBTi, SBTfw, BMP with measurable trajectories), AND
  (b) Has a credible, time-bound implementation pathway?

  YES → Sensitivity_i = REDUCED
        (scenario still tracked; residual risk remains)
  NO  → Proceed to Step 4

Step 4: BIOCAPACITY / LOCATION PLAN CHECK
  Does the country/municipality where Company_j operates have:
  (a) A binding plan to increase biocapacity of Indicator_i
      (e.g., EU Nature Restoration Plan for biodiversity;
       national basin restoration plan for water;
       net-zero building code for energy), AND
  (b) The plan covers the specific sub-type of Indicator_i
      relevant to Company_j?

  YES → Sensitivity_i = PARTIALLY REDUCED
        (company benefits from systemic improvement;
         residual dependency gap must still be tracked)
  NO  → Proceed to Step 5

Step 5: RISK CLASSIFICATION
  Has Company_j or Country addressed this via NDC or
  equivalent policy commitment?

  YES, EARLY (NDC includes sector, timeline credible):
    → Classify as TRANSITION RISK
    → Risk is priced gradually; NPV sensitivity spread over
       transition period; breakeven shift manageable

  NO / LATE:
    → Classify as PHYSICAL RISK
    → Risk materialises suddenly; NPV sensitivity concentrated;
       breakeven shift may exceed current production volume;
       legal liability amplifies through Wetzer attribution channel
```

---

## 5. NPV Sensitivity Quantification by Risk Classification

### 5.1 Transition Risk Pathway (Early NDC Action)

When dependency is addressed early via NDC or equivalent:

- V_natural rises **gradually** along a policy trajectory (e.g., carbon price schedule: €25/t → €150/t by 2035)
- DOL rises incrementally; manageable within normal capex planning cycles
- Legal risk remains **latent** — Wetzer's flywheel has not spun up for this sector
- NPV sensitivity is analogous to CFA's "base case scenario" with controlled parameter drift

**Financial expression:**
```
NPV_transition = Σ [Q(P − V_market − V_natural(t_policy)) − F − L_latent] / (1+r)^t
```
Where V_natural(t_policy) follows a known schedule, enabling hedging and phased capex replacement.

**Example — Sector: Manufacturing / Indicator: GHG**
If an EU manufacturer already operates under ETS with an internal carbon price of €80/t CO₂e:
- V_natural is already internalised into operational budgeting
- SBTi-aligned capex reduces Scope 1 over 5–10 years
- L_legal remains low: attribution science less likely to be applied to a company with visible decarbonisation trajectory (Wetzer: "claimants are becoming more successful" — but against laggards, not movers)

### 5.2 Physical Risk Pathway (Late or No Action)

When dependency is not addressed and the scenario materialises physically:

- V_natural rises **suddenly** (resource unavailability, not just price)
- If the resource is a **production constraint** (water in drought, land under EUDR ban), Q drops simultaneously with V_natural rising — **double compression of CM**
- Legal liability activates: attribution science, now well-developed per Wetzer, links historical resource use to quantified damages
- DTL spikes: DOL × DFL both rise because CM denominator collapses against unchanged fixed costs

**Financial expression:**
```
NPV_physical = Σ [Q_constrained × (P − V_market − V_natural_shock) − F − L_attributed] / (1+r)^t
```
Where Q_constrained < Q_base AND V_natural_shock >> V_natural_base AND L_attributed > 0.

**Worst-case cascade (analogous to CFA scenario analysis worst case):**

| Variable | Base | Physical shock | Change |
|---|---|---|---|
| Q (units/output) | 100% | −20% (resource constraint) | −20% |
| P (output price) | Base | ±0 (commodity, inelastic demand) | 0% |
| V_natural (resource cost) | Base | +40% (scarcity premium + legal reserve) | +40% |
| F (fixed costs) | Base | +0% (unchanged) | 0% |
| L_legal | 0 | +Added (attribution liability) | NEW |
| **CM per unit** | High | Severely compressed | **−50% to −80%** |
| **DOL** | 2–4x | 8–15x | **Spike** |
| **NPV** | Positive | **Negative** | **Sign reversal** |

This is the Chevron scenario in miniature: a company that profited for decades while externalising natural capital costs faces attribution-based liability that exceeds its cumulative profit.

---

## 6. Sector–Indicator Dependency Matrix

The following matrix indicates, by sector, which natural capital indicators create material NPV sensitivity under the Wetzer scenario. A filled cell means the indicator is a **primary production dependency** for that sector.

| Sector | GHG | Water | Land/Bio | Air | Waste | Energy | Living Wage |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fossil fuels / Utilities** | ●● | ○ | ○ | ●● | ○ | ●● | ○ |
| **Agriculture / Forestry** | ● | ●● | ●● | ○ | ● | ○ | ●● |
| **Mining / Extractives** | ●● | ●● | ●● | ●● | ●● | ● | ● |
| **Cement / Concrete** | ●● | ● | ●● | ●● | ●● | ●● | ● |
| **Chemicals / Pharma** | ●● | ●● | ○ | ●● | ●● | ●● | ○ |
| **Textiles / Apparel** | ● | ●● | ● | ● | ●● | ● | ●● |
| **Food & Beverage** | ● | ●● | ●● | ○ | ●● | ● | ● |
| **Transport / Logistics** | ●● | ○ | ○ | ●● | ● | ●● | ● |
| **Real estate / Construction** | ● | ● | ●● | ● | ●● | ●● | ● |
| **Renewable Energy** | ○ | ● | ● | ○ | ● | ○ | ○ |
| **Digital Infra / TMT** | ● | ●● | ○ | ○ | ●● | ●● | ○ |
| **Financial Services** | ○ | ○ | ○ | ○ | ○ | ○ | ● |

**Legend:**
●● = Primary dependency (NPV materially sensitive under scenario)
● = Secondary dependency (NPV sensitive under combined/worst-case scenario)
○ = Indirect only (monitor; immaterial in isolation)

**Note on Financial Services:** Exposure is not operational but through **portfolio/loan book** — the Wetzer attribution channel affects borrowers, which flows back through credit risk and asset quality to the lending institution's NPV.

---

## 7. The NDC Timing Argument: Transition vs. Physical Risk

The user's framing is directly supported by the combined logic of Wetzer et al. and the CFA leverage framework:

### 7.1 Early Transition (NDC-led)

- Sector-level dependency on Indicator_i is **acknowledged in national NDC** or sectoral transition plan
- Policy mechanism introduced: carbon price, water pricing reform, biodiversity net gain requirement
- V_natural rises on a **known, forecastable trajectory**
- Companies that hedge early:
  - Reduce exposure by shifting away from dependent inputs (reduce V_natural over time)
  - Retain optionality to pass costs through to price (P) before competitors do — price elasticity advantage
  - Avoid Wetzer's legal flywheel: proactive companies have lower attribution exposure because their mitigation trajectory weakens the causal chain
- NPV impact: **Transition risk, early, priced, spreads over time** → manageable DOL; NPV remains positive with capex reallocation

### 7.2 Late / No Action (Physical + Legal Channel)

- Sector dependency on Indicator_i is **not addressed** in NDC, or NDC covers it but enforcement lags
- Physical degradation of resource accelerates beyond the transition price signal
- Simultaneously:
  - Q_output falls (resource physically unavailable)
  - V_natural spikes (emergency procurement, remediation costs)
  - L_legal activates (attribution science now links the company's historical extraction to the degradation → Wetzer flywheel)
- The **breakeven point rises above current production volume** — the company is structurally loss-making:

```
Q_BE_physical = (F + C) / (P − V_market − V_natural_shock)
```

Where V_natural_shock >> V_natural_base, driving Q_BE above achievable production levels.

- NPV turns negative; the business may be "net value-destroying" even before the first lawsuit is filed

### 7.3 The NDC as a Natural Capital Management Hedge

Under the dependency-sensitivity framework, a country's NDC that explicitly addresses a sector's resource dependency performs the function of the **"management plan"** in Step 3 of the decision tree — but at the systemic level:

- NDC commits to expanding biocapacity (afforestation, water basin restoration, clean air zone) → reduces S_physical for all companies operating in that jurisdiction
- NDC establishes a transition schedule (carbon price pathway, permit scheme) → converts S_legal from contingent to priced, reducing litigation probability
- NDC links to TNFD/TCFD reporting requirements → creates the data infrastructure for companies to demonstrate management plans, reducing individual legal exposure

**Conversely:** A company operating in a country whose NDC does NOT address the sector dependency faces both a higher S_physical (no systemic protection) and a higher S_legal (attribution chain is unbroken — no policy signal to attenuate causality).

---

## 8. Integration with the Transitionvaluation ONPV Framework

The Transitionvaluation framework's **Opportunity Net Present Value (ONPV)** model is the positive-side complement to the NPV sensitivity framework above:

```
ONPV = NPV_financial + PV(positive externalities) − PV(negative externalities)
     = NPV_financial + Σ [Domain_Value_i] − Σ [L_legal_i]
```

Where:
- **PV(positive externalities)** = WifOR I-O multiplier outputs: GDP contribution, employment, clean air avoided health costs, carbon sequestration value
- **PV(negative externalities)** = natural capital damages: water overuse × shadow price, GHG × social cost, land conversion × ecosystem service loss, PM2.5 × VSL
- **L_legal** = Wetzer attribution liability = Attribution_share_i × Social_Cost_i × Historical_quantity_i

A company that:
1. Eliminates material resource dependencies (Steps 3–4 of decision tree), AND
2. Generates net positive externalities (employment multiplier, clean energy, water efficiency)

achieves **ONPV > NPV_financial** — its green bond can price inside conventional infrastructure (documented 15–20 bps advantage in Package 3 examples), precisely because it has converted S_legal and S_physical from liabilities to advantages.

**BCR thresholds under the legal risk scenario (Pflichtenheft):**

| BCR | Interpretation under natural capital scenario |
|---|---|
| > 3.0 | Company has eliminated dependencies AND generates net biocapacity — litigation-proof |
| 2.0–3.0 | Strong management plans in place; residual transition risk remains |
| 1.5–2.0 | Partial dependency reduction; physical risk exposure remains at tail |
| 1.0–1.5 | Marginal; breakeven vulnerable to resource price shock |
| < 1.0 | Structural loss-making under adverse scenario; legal liability likely exceeds equity value |

---

## 9. Summary: The Unified Sensitivity Statement

> **A company operating in a sector that depends on a tracked natural capital resource will have its NPV, BCR, and operating breakeven materially affected by an adverse scenario for that resource — unless it holds a verified management plan that credibly reduces that dependency, OR operates in a jurisdiction with a binding plan to increase the biocapacity of that specific resource.**

> **If the dependency is addressed early through the company's own transition plan or through the country's NDC, the sensitivity manifests as transition risk: forecastable, priceable, and spreadable over time. If it is not addressed, the same underlying dependency will materialise as physical risk — resource unavailability compressing the contribution margin — and subsequently as legal risk, when attribution science translates historical resource use into contingent liability, as established by Wetzer et al. (2024).**

> **The compounding mechanism is operating and financial leverage: fixed costs do not adjust to resource shocks. When the contribution margin is compressed by simultaneous resource price rises and volume constraints, the DOL and DTL spike, transforming small percentage changes in the resource indicator into large percentage changes in net income and NPV — potentially crossing the breakeven threshold and rendering the business structurally loss-making at its current scale.**

---

## 10. Sources

- Wetzer, T., Stuart-Smith, R. & Dibley, A. (2024). "Climate risk assessments must engage with the law." *Science* 383(6679), 152–154. DOI: 10.1126/science.adj0598
- CFA Institute (2022). *CFA Program Curriculum Level I, Volume 4* — Reading 32: Measures of Leverage
- Kaplan Schweser (2020). *CFA Level II Notes, Book 2* — Study Session 7: Capital Budgeting
- Greenings / Value Balancing Alliance (2024). *Transitionvaluation Project* — github.com/Greenings/transitionvaluation
- WifOR Institute (2024). *Value Factors: Economic Impact Coefficients* — 8 indicators × 188 countries × NACE sectors
- GRESB (2025). *Infrastructure Assessment Indicators Summary* — resources-2025-infrastructure-indicators-summary
- FAST-Infra (2024). *Sustainable Infrastructure Label: Dimensions, Criteria and Indicators v2.0*
- VBA / Pflichtenheft (2025). *Infrastructure Impact Measurement and Valuation Service v1.0*
- Gold Standard (2025). *Requirements for Monitoring Indicator Selection v1.0*
- IPBES (2019). *Global Assessment Report on Biodiversity and Ecosystem Services*
- EU Nature Restoration Law (2024). Regulation (EU) 2024/1991
