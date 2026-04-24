# ONPV Knowledge Series — Session Asks

**Purpose:** This document converts the open questions from the liability-side (`onpv_knowledge_series_questions.md`) and premium-side (`onpv_premium_pricing_questions.md`) documents into actionable asks — decisions to make, outputs to produce, data to confirm, and governance to establish — for each session in the IFC/EBRD Knowledge Series.

Each session entry answers: *What must be resolved in this session for the ONPV framework to be usable, and what does this session hand over to the next?*

**Companion documents:** `onpv_formula_corrected.md` · `onpv_knowledge_series_questions.md` · `onpv_premium_pricing_questions.md` · `natural_capital_npv_sensitivity_framework.md`

---

## Annex Session — Model Governance, System Boundaries, and User Typology

*These anchors must be agreed before the Knowledge Series opens. None of the five sessions can proceed without them.*

### A1 — Decision: System level and formula boundary

**Make a decision** on which system level the ONPV formula operates at and how boundaries are crossed:

- At project level, the formula measures physical units. At entity level, the insolvency cap (`IV = V_liquidation − D_senior`) requires a balance sheet. These are not the same object.
- **Decide**: Does ONPV operate at project level only? Or is there a defined roll-up from project to entity level? If both, what is the aggregation rule and who performs it?
- **Decide**: For SPV-structured infrastructure (where the SPV's `IV` is minimal by design), which entity's insolvency value applies — the SPV, the sponsor, or the consolidated group?
- **Output**: Written system boundary statement for inclusion as the scope section of the Technical Note.

### A2 — Decision: User typology and decision supported

**Confirm or revise** the user typology table and confirm what each user needs from the formula output:

| User | Decision supported | Critical formula output |
|---|---|---|
| DFI investment officer | Approve / structure / price a loan | BCR, Delta BCR, `L_legal_effective` vs. IV |
| Portfolio risk manager | Stress testing, provisioning, concentration limits | `Interaction_penalty`, `Liability_Gap` |
| Corporate sustainability officer | Disclosure, target-setting, transition planning | VR score, BF score, channel-specific EF |
| Regulator / supervisor | Macro-prudential, mandatory insurance requirements | `Σ Liability_Gap` across portfolio |
| Project company / sponsor | Capex justification, green bond structuring | Delta BCR, greenium (15–20 bps) |
| Carbon / biodiversity market participant | Premium pricing, credit issuance | `EF_market_i`, `CR_i`, Premium Gap |

**Output**: Confirmed user typology table, written into the Annex of the Technical Note.

### A3 — Decision: Minimum data requirement at deal origination

**Agree what data is feasibly required** to produce a valid ONPV when an investment officer initiates a deal:

The full corrected formula requires: physical units, value factors, continuous `O_i`, three-channel EF decomposition, independently verified VR, jurisdiction-level BF, entity balance sheet (`V_liquidation`, `D_senior`), retrospective `Q_historical`, and probabilistic `P_litigation`.

- **Decide**: What is the minimum feasible input set at deal origination?
- **Decide**: Which inputs may be placeholder-estimated with a documented uncertainty flag, and which cannot be omitted without producing a materially misleading ONPV?
- **Output**: Minimum viable data checklist, referenced in the Session 5 minimum viable specification.

### A4 — Decision: Premium market scope

**Decide** whether the premium pricing mirror formula operates at the same system boundary as the liability formula, or requires separate market-level definition:

- The liability formula falls on the producer. The premium formula requires a willing buyer and an accessible market.
- **Decide**: Which premium channels are in scope — voluntary markets, mandatory compliance markets, green procurement, green bond coupon differential, sustainability-linked loan pricing?
- **Output**: Premium market scope statement, written into the Annex alongside the liability boundary.

### A5 — Output: Pre-session briefing documents

**Produce** a one-page briefing for each session convener before the Knowledge Series opens, stating:

- What the session must decide (not just discuss)
- Which input documents participants must have read
- What output the session must hand over to the next session

---

## Session 1 — Overshoot in Transition Valuation / ONPV / Infrastructure Level

*Session 1 must resolve the foundational overshoot debate and confirm the scarcity premium functional form. Without these, the formula cannot be applied consistently across any indicator.*

### 1.1 — Decision: Binary vs. continuous O (liability side) — SEQUENCE CRITICAL

**Resolve the binary vs. continuous O tension.** This is the highest-priority decision in the framework. Later sessions cannot produce consistent outputs until it is resolved.

Three options, one of which must be adopted:

1. **Fully continuous**: `O_i ∈ [0, ∞)` — per corrected formula (`onpv_formula_corrected.md`)
2. **Binary gate only**: `O ∈ {0, 1}` — per original session framing (planetary overshoot is categorical)
3. **Hybrid**: binary gate `O ∈ {0, 1}` as a scarcity switch, plus continuous intensity multiplier `O_intensity ∈ [1, ∞)` within the overshoot regime:

```
f_scarcity = 1                             if O = 0  (within planetary limits)
f_scarcity = (1 + S)^O_intensity           if O = 1  (in overshoot, intensity-adjusted)
```

**Output**: Formula decision record stating which option is adopted, the rationale, and the agreed functional form.

### 1.2 — Data: O_intensity reference datasets

**Confirm the reference datasets** for calibrating O_intensity per indicator and assign a maintenance owner:

| Indicator | Proposed dataset | Scale |
|---|---|---|
| Water | WRI Aqueduct | 0–5 |
| GHG / Carbon | IPCC remaining budget exceedance ratio | % |
| Biodiversity | IPBES habitat intactness index | 0–1 |
| Air quality | WHO exceedance ratio (PM₂.₅) | µg/m³ above guideline |
| Land / Soil | WRI Global Soil Database or ESDAC | % depletion |
| Fisheries | FAO stock assessment (% of MSY) | % |

**Decide**: Who is responsible for maintaining these datasets within the ONPV framework, and at what update frequency?

### 1.3 — Decision: Scarcity premium functional form (liability side)

**Confirm or revise** the scarcity premium functional form from four candidates:

1. Linear depletion: S rises proportionally as budget depletes
2. Convex: `f_scarcity = (1 + S)^(1 + O_i)` — consistent with corrected formula
3. Step function tied to IPCC carbon budget thresholds (1.5°C, 2°C)
4. Market-linked: ETS carbon price or equivalent

**Decide** whether the functional form is consistent across all indicators or indicator-specific. Note: choice 2 is implicit in `onpv_formula_corrected.md`; if a different form is adopted, the formula must be updated.

### 1.4 — Decision: Premium overshoot gate (premium side)

**Decide** whether the scarcity premium on the revenue side requires `O_i = 1` to be earned, or whether a graduated premium applies even below the overshoot threshold:

- **Overshoot-only**: premium available only when `O_i = 1` — maintains scarcity logic, creates geographic arbitrage
- **Graduated**: premium available below the threshold, scaled by proximity to overshoot — rewards preventive action, dilutes signal

**Decide** whether this choice is consistent across all indicators or varies by indicator.

### 1.5 — Decision: Biocapacity import vs. liquidation distinction

**Decide** whether the formula distinguishes between two types of biocapacity deficit:

- A country in deficit that is substituting through financial biocapacity imports (lower immediate physical risk)
- A country in deficit that is liquidating local natural assets (higher immediate physical risk, higher `EF_physical`)

**Decide** whether this distinction is encoded in `BF_i`, `EF_physical_i`, or both.

### 1.6 — Decision: Finance capacity breakdown threshold

**Decide** whether the formula includes a country-level parameter encoding the point at which financial substitution of biocapacity breaks down and converts managed transition risk into acute physical risk:

- Candidate variables: external debt/reserves ratio, current account position, IMF external vulnerability index
- If yes: **decide** which variable and assign it to `EF_transition_i`

### 1.7 — Output: Session 1 → Session 2 handover

**Produce** a confirmed formula extract showing the agreed O specification and `f_scarcity` functional form, ready for EF decomposition mapping in Session 2.

---

## Session 2 — Mapping of Impact Approaches on the Infrastructure Project

*Session 2 must confirm EF data sources, agree the classification crosswalk, establish VR and CR_i scoring, and resolve the geographic scope of O.*

### 2.1 — Data: EF decomposition data sources

**Confirm one primary and one secondary data source** per channel per indicator:

| Channel | Proposed primary source | Decision required |
|---|---|---|
| `EF_physical_i` | ENCORE natural capital mapping, WRI Aqueduct, IPCC hazard maps | Confirm |
| `EF_transition_i` | NDC sector coverage / NGFS / EU taxonomy | Choose among options |
| `EF_legal_i` | Wetzer five-method framework / Sabin Center tracker / IPCC attribution confidence | Choose among options |

**Output**: Data source registry, included in Technical Note as reference table.

### 2.2 — Data: Indicator classification crosswalk

**Produce the crosswalk** between the three classification systems used in the framework:

- Global Footprint Network six dimensions (cropland, grazing, forest, fishing, built-up land, carbon)
- ENCORE dependency categories
- Pflichtenheft / Lastenheft indicator set (GHG, water, land/biodiversity, air, waste, OHS, employment)

**Decide** which system takes precedence when two systems assign different scores for the same physical dependency.

### 2.3 — Data: Premium product mapping

**Validate and complete** the positive indicator output mapping for infrastructure project types:

| Project type | Positive indicator produced | Premium mechanism |
|---|---|---|
| Renewable energy | GHG avoided (tCO₂e) | Carbon credit, green tariff, green bond |
| Reforestation / agroforestry | Carbon sequestered, biodiversity (ha), water retained | Carbon credit, biodiversity credit, watershed payment |
| Water treatment / efficiency | Water restored (m³), pollution reduced | Water stewardship certificate, utility premium |
| Sustainable agriculture | Cropland within limits, soil carbon | Ecolabel, sustainable supply chain premium |
| Marine / coastal infrastructure | Fishing grounds restored, blue carbon | Blue carbon credit, marine biodiversity credit |
| Green building | GHG avoided, air quality improved | Green building certification premium, energy savings |
| Nature-based urban infrastructure | Biodiversity, urban cooling, air quality | Ecosystem service payment, municipal procurement |

**Confirm** which premium mechanisms are liquid at investment-grade scale. **Add** any project types missing from this list.

### 2.4 — Decision: VR scoring algorithm

**Agree the scoring algorithm** converting IFC Performance Standard compliance into VR scores (0–1):

| IFC PS | VR-relevant requirement | VR sub-component |
|---|---|---|
| PS1 (Assessment and Management) | Management plan existence and quality | VR base score |
| PS2 (Labour) | ILO Decent Work compliance | VR social component |
| PS5 (Land Acquisition) | Resettlement action plan quality | VR land/biodiversity indicator |
| PS7 (Indigenous Peoples) | FPIC documentation | VR community-facing indicators |

**Decide** whether VR is a single composite score or a per-indicator score (one `VR_i` per indicator).

### 2.5 — Decision: VR_min threshold

**Agree the value of `VR_min`** — the credibility floor below which no legal attenuation is granted:

- A single value of 0.3 is recommended in `onpv_formula_corrected.md`
- **Decide** whether it is differentiated by indicator (e.g., lower for GHG where legal precedent is mature, higher for biodiversity where legal precedent is still developing)

**Output**: `VR_min` specification table by indicator, included in Technical Note.

### 2.6 — Decision: CR_i certification standards

**Confirm or revise** the certification standard mapping for each indicator:

| Indicator | Standard | CR_i if certified | CR_i if uncertified |
|---|---|---|---|
| GHG sequestered | Gold Standard, Verra VCS, REDD+ | 1.0 | 0.2 |
| Biodiversity restored | TNFD, Biodiversity Net Gain (UK), IUCN NNL | 0.8 | 0.1 |
| Water restored | Alliance for Water Stewardship (AWS), SBTfw | 0.7 | 0.15 |
| Sustainable land use | Rainforest Alliance, FSC, RSPO | 0.8 | 0.2 |
| Air quality improved | Verified health impact assessment | 0.5 | 0.05 |

**Decide** what the formula does when no recognised certification scheme exists for an indicator — zero premium, estimated with uncertainty discount, or flagged as speculative.

### 2.7 — Decision: Geographic scope of O assessment — SEQUENCE CRITICAL

**Resolve the geographic scope question** for both liability and premium:

| Option | Description | Implication |
|---|---|---|
| Global | Planetary boundary level | Same O for all projects globally using same resource |
| National | Country biocapacity | Same O for all projects in one country |
| Basin / watershed / airshed | Local ecosystem boundary | O varies between sites in the same country |
| Project footprint | Operational boundary | Most granular; highest data requirement |

A project using water from a stressed local basin in a nationally water-surplus country scores `O = 0` at national level and `O = 1` at basin level. The financial implications are material.

**Decide** whether the scope differs between cost side (O for liability) and revenue side (O for premium eligibility). **Decide** whether premium scope follows the buyer's geography.

### 2.8 — Decision: BF effect on premium additionality

**Decide** how a binding national restoration plan (`BF_i > 0`) affects premium revenue claims:

- Liability side: `BF_i > 0` reduces exposure — beneficial
- Revenue side: `BF_i > 0` may indicate the government will restore the resource regardless, reducing the project's Additionality
- **Decide**: Does `BF_i` reduce `CR_i` on the revenue side? If yes, by what mechanism and what factor?

### 2.9 — Output: Session 2 → Session 3 handover

**Produce**: confirmed EF data source registry, VR scoring algorithm, `VR_min` table by indicator, O geographic scope rule, and `CR_i` table — ready for attribution analysis in Session 3.

---

## Session 3 — Analysis of User Needs and Indicator Gaps

*Session 3 must confirm attribution methodology, resolve social indicator gaps, agree the interaction penalty correlation matrix, and address the new-project L_legal problem.*

### 3.1 — Decision: AF_direct for lender vs. equity investor

**Decide** how `AF_direct` is calculated for a DFI acting as lender (no equity):

- Option A: proportional to share of total project financing
- Option B: proportional to loan book exposure relative to project total debt
- Option C: tiered by covenant control (covenants with sustainability conditions = higher attribution)

**Decide** separately for the liability side (cost attribution) and the premium side (positive impact credit attribution).

### 3.2 — Decision: AF_engagement operationalisation

**Agree the engagement criteria** that constitute "meaningful engagement" for the engagement multiplier:

- What actions qualify? (Voting record, written board communication, sustainability covenant, technical assistance provision?)
- What does engagement available but not exercised look like? (Abstention, silence, waiver of covenant?)
- Who determines whether engagement has occurred — DFI internal record, independent verifier, or regulator?

**Output**: Engagement criteria checklist, included in Technical Note as the engagement attribution protocol.

### 3.3 — Data: Social indicator data gaps

**Confirm** for each social indicator whether data is already collected in IFC/EBRD E&S monitoring or requires a new data collection requirement:

| Indicator | Pflichtenheft code | Currently collected? | Gap? |
|---|---|---|---|
| Job-years (employment multiplier) | S5.1 / SE2 | ? | ? |
| Living wage gap | S2.8 | ? | ? |
| Community investment | GRI 413 | ? | ? |
| Grievance rate | HS1-4 / S7 | ? | ? |
| Gender-equitable hiring | GRI 401 | ? | ? |
| FPIC documentation | PS7 | ? | ? |

**Decide** for each identified gap: include in ONPV with estimated value factor, exclude pending further research, or flag as a qualitative indicator.

### 3.4 — Data: Living wage value factor

**Confirm the VF for living wage** — the societal cost per € of wage gap per worker — and its source.

If no agreed value exists, decide whether to:
- Use a WifOR-derived proxy (employment multiplier applied to wage gap)
- Exclude from ONPV pending further research and document the gap
- Include as a qualitative flag only alongside quantitative indicators

### 3.5 — Data: Correlation matrix for interaction penalty

**Agree the correlation matrix** `ρ_ij` for indicator pairs under adverse scenarios. Minimum required pairs:

| Pair | Scenario | ρ_ij value |
|---|---|---|
| Water and crop yield | Drought | To be agreed |
| Energy demand and cooling demand | Heat wave | To be agreed |
| GHG and carbon border adjustment cost | Carbon pricing scenario | To be agreed |
| Biodiversity loss and agricultural productivity | Physical scenario | To be agreed |

**Decide** who is the methodological owner of the correlation matrix and at what frequency it is updated.

### 3.6 — Decision: Interaction bonus for premium side

**Decide** whether the formula includes a positive compounding term (interaction bonus) for projects simultaneously addressing multiple overshoot indicators:

- Evidence base: bundled certification schemes (TNC debt-for-nature swaps, REDD+ integrated programmes)
- **Decide**: Is a bundling premium above the sum of individual credits empirically demonstrable? If yes, what is the multiplier and how is it calculated?

### 3.7 — Decision: L_legal for new projects

**Resolve the new-project inception problem** for `L_legal`:

- New projects have `Q_historical_i = 0` at financial close, giving `L_legal = 0` by construction
- **Decide**: Should `P_litigation` carry a non-zero sector-level baseline regardless of project age (sector precedent effect)?
- **Decide**: At what operating history threshold does project-specific `Q_historical` become material enough to dominate the sector baseline?

### 3.8 — Decision: Premium Gap as mandatory output

**Decide** whether the framework tracks a "Premium Gap" — the difference between the full societal value of positive indicators and the premium actually captured by the market:

```
Premium_Gap_i = VF_i × Physical_Unit_positive_i − (EF_market_i × CR_i × VF_i × Physical_Unit_positive_i)
```

- This is the revenue-side mirror of `Liability_Gap`
- **Decide**: Is `Premium_Gap` a mandatory output alongside `Liability_Gap`, or optional?
- **Decide**: For indicators with no market (urban heat island, noise, pollinator habitat), should societal value be reported as a non-monetised positive alongside the financial model, or excluded entirely?

### 3.9 — Output: Session 3 → Session 4 handover

**Produce**: confirmed attribution protocol (`AF_direct`, `AF_engagement` criteria checklist), confirmed social indicator list with VF sources, confirmed or provisional correlation matrix, and `Liability_Gap` / `Premium_Gap` reporting requirement — ready for investment case construction in Session 4.

---

## Session 4 — Investment Case Analysis: NPV vs. ONPV with Overshoot

*Session 4 must confirm the BCR structure, concessionality thresholds, and insolvency cap application. Its primary deliverable is a worked investment case example.*

### 4.1 — Decision: Three-BCR presentation structure

**Confirm** the three-BCR investment case structure:

```
BCR_standard         = conventional financial analysis only
BCR_ONPV_cost        = standard + liability-side corrections (L_legal, scarcity costs)
BCR_ONPV_full        = standard + liability-side + premium revenue-side
```

**Decide** additionally whether the investment case reports both:

```
BCR_ONPV_gross       = uses L_legal_effective (insolvency-capped)
BCR_ONPV_true        = uses Σ L_legal_i uncapped
```

The gap between `BCR_ONPV_gross` and `BCR_ONPV_true` is the measure of externalised societal cost that the company cannot pay. Both figures reveal different things to different users.

### 4.2 — Decision: Delta BCR concessionality threshold

**Agree the Delta BCR thresholds** that govern concessionality decisions:

- What minimum `Delta BCR = BCR_ONPV_full − BCR_standard` constitutes a material ONPV premium justifying concessional terms?
- Is there a maximum Delta BCR above which the project is self-financing and concessionality is not warranted?
- **Decide** the DFI mandate response when `BCR_ONPV_cost < BCR_standard` but `BCR_ONPV_full > BCR_standard` — the project destroys conventional financial value but creates net societal value.

### 4.3 — Decision: CERC equity weighting

**Decide** whether Scarcity Premium `S` is equity-weighted by country income level and historical cumulative footprint (CERC logic):

- Liability side: higher `S` for wealthy countries (larger historical debt to planetary budget)
- Premium side: lower ONPV revenue credit for wealthy countries (should self-finance transition)
- **Decide** where equity weighting is encoded: in `AF_direct`, in `S_i`, or a separate equity factor
- **Decide** how equity-weighted `S` and `BF_i` interact (additive, multiplicative, or independent)

### 4.4 — Decision: Additionality via Delta BCR

**Decide** whether a positive `Delta BCR` can replace or supplement the qualitative Additionality test:

- If `BCR_ONPV > BCR_standard` by the threshold confirmed in 4.2, does this constitute quantitative evidence that the DFI's sustainability conditions are what makes the project additional?
- **Decide** the complementary role of qualitative assessment when Delta BCR is already positive.

### 4.5 — Decision: Insolvency cap application at appraisal

**Decide** how the insolvency cap is operationalised for greenfield projects where `V_liquidation` must be estimated:

- Option A: sensitivity scenario range (low / base / high `V_liquidation` → range of `L_legal_effective`)
- Option B: hard constraint at financial close, using construction-cost-based comparable
- Option C: covenant trigger — if `V_liquidation` falls below a defined threshold post-close, mandatory liability insurance is required

**Decide** which option governs and how it appears in the investment appraisal report.

### 4.6 — Decision: Contracted vs. market-dependent premium

**Agree the evidentiary standard** for classifying premium revenue:

- **Contracted premium** (signed PPA with green tariff, carbon offtake agreement, biodiversity credit pre-purchase): bankable, treated as committed revenue, reduces concessionality case
- **Market-dependent premium** (voluntary carbon spot, ecolabel retail premium, nascent biodiversity credit): speculative, treated as upside scenario, supports concessionality case

**Decide**: What evidence of market access (term sheet, LOI, exchange listing, buyer commitment) is required to classify a premium as contracted?

### 4.7 — Decision: Sunset clause for premium revenue

**Decide** whether a sunset clause is built into the premium revenue forecast:

- As overshoot is resolved, `O_i` decreases and the scarcity premium erodes (self-defeating dynamic)
- Is there a floor on the scarcity premium to maintain incentive after overshoot is partially resolved?
- Is the sunset clause a mandatory disclosure in the base case, or treated as a standard market risk in sensitivity analysis?

### 4.8 — Output: Worked investment case example

**Produce** a worked example applying all confirmed formula components to one real or hypothetical infrastructure project:

The example must show:
- `BCR_standard` vs. `BCR_ONPV_cost` vs. `BCR_ONPV_full`
- `L_legal_effective` vs. `Liability_Gap` vs. `Premium_Gap`
- Three scenarios: early NDC action (transition risk), late action (physical risk), no action (legal risk)
- Channel weight shifts under each scenario (`w_p`, `w_t`, `w_l`)

**This is the primary deliverable of Session 4.** It is the basis from which the Technical Note's quantitative guidance is written.

---

## Session 5 — Conclusion: Outputs, Technical Note, and Executive Brief

*Session 5 must confirm the minimum viable ONPV specification, agree governance, finalise reporting requirements, and produce the Technical Note and Executive Brief.*

### 5.1 — Decision: Minimum viable ONPV specification

**Confirm the minimum viable specification** — the smallest term set that does not produce a materially misleading ONPV:

**Liability side:**

| Term | Omittable? | Condition |
|---|---|---|
| `Physical_Unit × VF` | No | Cannot omit — confirm |
| `f_scarcity` with O gate | No (binary gate acceptable minimum) | Confirm |
| `EF_physical` only | Acceptable short-term minimum | Must explicitly flag Wetzer channel as omitted |
| `g_readiness` with `VR_min` threshold | Threshold required | Confirm; linear `(1−VR)` is wrong |
| `BF_i` | Omittable short-term | Flag as missing input in output report |
| `L_legal` | No | At minimum a qualitative flag — cannot omit entirely |
| Insolvency cap | No | Uncapped `L_legal` is technically incoherent |
| `Liability_Gap` | No | Mandatory output even in minimum viable version |
| `Interaction_penalty` | Omittable short-term | Replace with scenario sensitivity note |

**Premium side:**

| Term | Omittable? | Condition |
|---|---|---|
| `Physical_Unit_positive × VF` | No | Cannot omit |
| `EF_market_i` | No | Zero if no market exists — prevents BCR inflation |
| `CR_i` | No | Zero if uncertified — prevents greenwash premiums |
| Interaction bonus | Omittable short-term | No agreed multiplier yet |
| Sunset clause disclosure | Recommended | Required risk disclosure |

**Critical minimum viable rule for premium**: `EF_market_i = 0` by default unless a specific, accessible buyer market is identified and documented. This prevents inflating BCR with theoretical premium revenue that has no realistic monetisation route.

**Output**: Minimum viable ONPV checklist, included in Technical Note.

### 5.2 — Decision: Liability_Gap and Premium_Gap reporting requirements

**Decide the mandatory reporting requirements for both gap metrics:**

- `Liability_Gap`: Should DFIs report aggregate `Σ Liability_Gap` across their infrastructure portfolio to their supervisory authority — analogous to non-performing loan ratios?
- `Premium_Gap`: Should projects disclose positive societal value not yet captured by any market, as a parallel to `Liability_Gap`?
- **Decide** reporting frequency (annual, at financial close, at each monitoring event) and the materiality threshold above which disclosure becomes mandatory.

### 5.3 — Decision: Three-scenario mandatory reporting

**Decide** whether all projects above a materiality threshold must run and disclose all three ONPV scenarios:

1. **Transition risk scenario** (early NDC action): foreseeable, spreadable cost
2. **Physical risk scenario** (late or no action): sudden, compounded damage
3. **Legal risk scenario** (Wetzer attribution channel): retrospective, probabilistic liability

**Decide** whether results are presented as a range (min/max/base) or as three discrete point estimates aligned with TCFD/TNFD scenario disclosure conventions.

### 5.4 — Output: Technical Note

**Produce** the Technical Note with the following mandatory sections:

1. Scope and system boundary (Annex decisions)
2. Confirmed formula specification with decision record (Sessions 1–3)
3. Minimum viable ONPV checklist (this session)
4. BCR presentation protocol and concessionality thresholds (Session 4)
5. Mandatory reporting requirements: `Liability_Gap`, `Premium_Gap`, three scenarios
6. Governance: sign-off authority, update frequency, pilot validation requirement
7. Relationship to Pflichtenheft v1.0: does the Technical Note supplement, supersede, or feed back into a Pflichtenheft v2.0?

### 5.5 — Output: Executive Brief

**Produce** the Executive Brief communicating two core messages, differentiated by audience:

**Core liability-side message:**
*A company cannot pay more than it owns, but the damage it has caused is still real — it is paid by someone else: taxpayers, communities, future generations. The gap between what a company can pay and what it owes is a hidden subsidy that conventional financial analysis does not see. DFIs that do not price this gap are not managing their portfolio risk — they are passing it on.*

**Core premium-side message:**
*A product that addresses a resource in overshoot is worth more than its conventional price — but only if the market to capture that value exists and delivery is verified. The gap between what a product is worth to society and what the market currently pays is the measure of how much public investment in market development is still needed to make the sustainability transition commercially self-sustaining.*

| Audience | Message emphasis | Specific ask |
|---|---|---|
| DFI board | `Liability_Gap` = unmanaged portfolio risk; `Premium_Gap` = case for continued concessionality | Approve mandatory `Liability_Gap` reporting |
| Project sponsor | Certify now; first movers capture highest premiums; thin capitalisation creates liability gap | Commit to VR ≥ VR_min and CR_i certification targets |
| Government / finance ministry | `Liability_Gap` signals mandatory insurance need; `Premium_Gap` signals public ecosystem service payment | Introduce mandatory environmental liability insurance |
| Carbon / biodiversity market | Formula provides consistent cross-indicator pricing method | Provide market data for `EF_market_i` calibration |
| Central bank governor | Aggregate `Liability_Gap` across DFI portfolio = systemic natural capital risk measure | Include in supervisory stress tests |

### 5.6 — Decision: Governance structure

**Agree the governance structure** before the Technical Note is published:

- **Sign-off authority**: Who holds final approval — VBA, Greenings, IFC, EBRD, or joint? What is the voting or consensus rule?
- **Validation requirement**: Is a pilot calculation on one or more live projects required before the Technical Note is published?
- **Update mechanism**: `EF_market_i` requires annual update from observable market data (carbon price indices, green bond issuance, procurement premium studies); `CR_i` requires update when new certification standards achieve critical mass — who maintains each?
- **Relationship to Pflichtenheft**: Does the Technical Note supplement v1.0, supersede it for infrastructure applications, or feed back into a Pflichtenheft v2.0?
- **Timeline**: What is the agreed publication date for the Technical Note and the Executive Brief?

---

## Cross-Cutting Asks

*These must be tracked as standing items throughout the Knowledge Series. They cannot be resolved in a single session but must be settled before the Technical Note is finalised.*

### X.1 — Netting rule

**Decide** whether cost-side ONPV impact and revenue-side premium are netted into a single figure or reported separately:

- A project that causes €50M GHG damage and sequesters €30M carbon has a net negative of €20M
- The net figure is simpler to communicate but hides the gross flows that regulators, insurers, and litigation analysts need
- **Recommended position**: report gross (cost side and revenue side separately) and net, consistent with TCFD/TNFD double materiality
- **Output**: Netting rule written into the Technical Note reporting protocol

### X.2 — Discount rate differential

**Decide** whether the same discount rate applies to both:
- Retrospective legal liability (`Q_historical`) — past costs, liability already accrued
- Forward-looking premium revenue — future positive delivery, delivery risk not yet resolved

**Recommended position**: higher discount rate for forward-looking premium revenue to reflect delivery and market risk.

**Output**: Discount rate protocol included in Technical Note financial model guidance.

### X.3 — Perverse incentive flags

**Agree the framework's response to two documented perverse incentives:**

- **Liability side**: companies may reduce `V_liquidation` (thin capitalisation, offshore asset transfer, pre-emptive dividend distribution) to widen the insolvency cap and reduce `L_legal_effective` without reducing actual impact
- **Premium side**: overshoot contributors may delay transition to maintain scarcity premiums elevated for adjacent premium markets

**Decide**: Are these flagged in formula output as warning conditions? If yes, what triggers the flag?
- Liability side: significant decline in `V_liquidation` while `Liability_Gap` widens
- Premium side: concentration of overshoot-positive market share in historically high-overshoot entities

### X.4 — Double-counting rule for premium

**Confirm and write into the formula specification** the double-counting rule:

Premium revenue already monetised through a recognised market transaction (Verra VCS credit sold at market price, AWS certificate issued) is **excluded** from the ONPV premium formula. Only the gap between the market price received and the full societal value (`VF × f_scarcity`) remains in ONPV as an unmonetised positive impact.

**Output**: Double-counting rule as a mandatory note in the premium formula specification, included in Technical Note.

### X.5 — Planetary budget per dollar invested

**Decide** whether the Technical Note includes a reference anchor metric: the implied maximum `Physical_Unit × VF` per infrastructure investment dollar consistent with a pathway back to 1.0 Earth by 2050 (currently at approximately 2.0 Earths):

- This is a macro-calibration tool for DFI portfolio composition, not a project-level constraint
- It would express the overshoot problem in a form directly actionable for portfolio-level investment officers
- **Decide**: Is this sufficiently robust to include as a directional reference in the Technical Note?

---

## Priority Order for Resolution

Items marked as sequence-critical must be resolved before later sessions can produce consistent outputs.

| Priority | Item | Session | Blocks |
|---|---|---|---|
| 1 | Binary vs. continuous O decision | 1.1 | All formula applications |
| 2 | System boundary and user typology | A.1, A.2 | All session deliverables |
| 3 | f_scarcity functional form | 1.3 | BCR calculations, premium pricing |
| 4 | Geographic scope of O | 2.7 | Local vs. global premium / liability |
| 5 | EF decomposition data sources | 2.1 | Scenario analysis, litigation exposure |
| 6 | VR_min threshold by indicator | 2.5 | Legal attenuation calculation |
| 7 | AF_direct for lender | 3.1 | Attribution on all projects |
| 8 | Insolvency cap at appraisal | 4.5 | Investment case presentation |
| 9 | Correlation matrix ρ_ij | 3.5 | Interaction_penalty calculation |
| 10 | Minimum viable specification | 5.1 | Technical Note |
| 11 | Governance structure | 5.6 | Technical Note publication |
| 12 | Netting rule | X.1 | Reporting protocol |
| 13 | Double-counting rule | X.4 | Premium formula validity |

---

*Compiled from: `onpv_formula_corrected.md` · `onpv_knowledge_series_questions.md` · `onpv_premium_pricing_questions.md` · `natural_capital_npv_sensitivity_framework.md` · `natural_capital_npv_sensitivity_summary.md` · Wetzer et al. (2024), Science 383:152–154 · Pflichtenheft v1.0 · Transitionvaluation Framework (Greenings/VBA)*
