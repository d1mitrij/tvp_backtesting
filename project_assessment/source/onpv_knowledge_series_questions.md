# ONPV Knowledge Series — Open Questions by Session

**Purpose:** Structured agenda of unresolved questions arising from the ONPV formula correction work, the Natural Capital NPV Sensitivity Framework, and the Wetzer et al. (2024) legal risk analysis, mapped to the IFC/EBRD Knowledge Series session structure.

---

## Annex Session
*The valuation model is defined by its use: who uses the model for which decision and in which context?*

### System Level and Boundary Questions

**A.1** At which system level does ONPV operate — the infrastructure project, the corporate entity, the holding company, or the portfolio? The formula as corrected operates on a single project's physical units. But the insolvency cap (`IV = V_liquidation − D_senior`) requires entity-level balance sheet data. How is this boundary crossed without conflating project-level impact measurement with entity-level financial liability?

**A.2** Infrastructure projects are an intermediary step between product/site level and corporate entity level. When a DFI finances a project through a special purpose vehicle (SPV), the SPV's `IV` is typically minimal by design. Does the insolvency cap apply to the SPV, the sponsor company, or the consolidated entity? What are the implications for `Liability_Gap` attribution when the SPV is the legal counterparty but the economic exposure sits with the parent?

**A.3** Capital allocation happens at the corporate entity level, the holding company, or the division of a multinational. ONPV is currently specified at the project level. What aggregation rules govern the roll-up from project ONPV to portfolio ONPV? Specifically: does the `Interaction_penalty` (cross-indicator compounding) apply within a single project, across projects in a portfolio, or both — and who is responsible for calculating it?

**A.4** Who are the primary decision-users of ONPV, and what decision does each user take? Proposed typology requiring confirmation:

| User | Decision | Critical formula component |
|---|---|---|
| DFI investment officer | Approve / structure / price a loan | BCR, Delta BCR, `L_legal_effective` vs. IV |
| Portfolio risk manager | Stress test, provisioning, concentration limits | `Interaction_penalty`, `Liability_Gap` |
| Corporate sustainability officer | Disclosure, target-setting, transition planning | VR score, BF score, channel-specific EF |
| Regulator / supervisor | Macro-prudential assessment, mandatory insurance requirements | `Σ Liability_Gap` across portfolio |
| Project company / sponsor | Capex justification, green bond structuring | Delta BCR, ONPV greenium (15–20 bps) |

Are these the right users? What decisions are missing? What formula outputs does each user actually need versus what the current specification produces?

**A.5** What is the minimum data requirement to produce a usable ONPV at project level? The corrected formula requires: physical units (reported), value factors (library), O_i (continuous — external datasets), EF decomposed into three channels (ENCORE + NDC tracker + litigation database), VR (third-party verified), BF (jurisdiction-level policy assessment), `V_liquidation` and `D_senior` (entity balance sheet), `Q_historical` (retrospective reporting), and `P_litigation` (probabilistic estimate). Is this feasible for an IFC/EBRD investment officer at deal origination? Where does the data burden exceed practical capacity and what simplifications are permissible without invalidating the output?

---

## Session 1 — Introduction: How Does Overshoot Come Into Transition Valuation? ONPV? Infrastructure Project and Entity Level

*Reference: Wackernagel et al. (2021), Global Footprint Network, Stockholm Resilience Centre planetary boundaries*

### The Binary vs. Continuous O Question

**1.1 Direct tension to resolve:** The session framing states that planetary boundaries "justify why O (the Overshoot toggle) must be a binary." The formula correction (P1) argues the opposite — that a binary toggle creates an indefensible cliff edge and must be replaced by a continuous overshoot intensity score `O_i ∈ [0, ∞)`. These two positions need to be reconciled before the formula is finalised.

The session argument for binary: in 2026, humanity operates at ~2.0 Earths. From a planetary boundary perspective, we are already in overshoot globally. Any project that adds to that load is operating in a deficit regime; any project that subtracts from it is operating in an abundance regime. The binary toggle encodes this categorical reality — you are either adding to a problem that already exists or you are not.

The formula correction argument for continuous: the *severity* of adding to an existing deficit differs by three orders of magnitude depending on how deep into the deficit the specific resource already is. A water project in a basin at 102% of safe yield and one at 400% of safe yield should not receive the same scarcity premium.

**Proposed resolution for discussion:** retain the binary `O ∈ {0, 1}` as a **gate** (does the scarcity premium apply at all?), but apply a continuous **intensity multiplier** `O_intensity ∈ [1, ∞)` within the overshoot regime. This preserves the categorical framing while introducing proportionality:

```
f_scarcity = 1                           if O = 0  (within limits)
f_scarcity = (1 + S)^O_intensity         if O = 1  (in overshoot, intensity-adjusted)
```

Is this resolution acceptable to both the session framing and the formula logic?

**1.2** How is `O_intensity` calibrated for each of the six Global Footprint Network dimensions (cropland, grazing land, forest, fishing grounds, built-up land, carbon)? What is the reference dataset and update frequency? Who is responsible for maintaining it within the ONPV framework?

**1.3** The Wackernagel biocapacity framework identifies two responses to a biocapacity deficit: ecological overshoot (liquidating local natural assets) and net biocapacity import (using financial wealth to buy resources and waste absorption from other regions). How does the formula distinguish between a company operating in a country that is in biocapacity deficit but importing (financially solvent, lower physical risk) versus one in a country liquidating local assets (immediate physical risk, higher `EF_physical`)? Does this distinction affect the `BF` (Biocapacity Factor) or `EF_physical` term, or both?

**1.4** Biocapacity is described as the economy's most limiting physical resource — more constraining than physical availability of fossil fuels or minerals. If this is the theoretical anchor, should VF (the value factor) for biocapacity-constrained resources be treated as a floor rather than a point estimate — i.e., the value factor can only rise, never fall, as overshoot deepens? What are the implications for long-term NPV modelling over a 25–30 year project horizon?

**1.5** Finance capacity (the ability to import biocapacity using financial wealth) is the alternative supply mechanism. At what point does a country's finance capacity become insufficient to maintain net biocapacity imports — i.e., at what external debt level, current account position, or reserve adequacy does the financial substitution mechanism break down and convert a transition risk (managed import dependency) into a physical risk (actual resource unavailability)? This threshold is currently not encoded in the formula. Should it be a country-level parameter in `EF_transition`?

**1.6** The session introduces the Scarcity Premium `S` as converting the Social Cost of Carbon from a flat fee to a dynamic price that increases as the remaining global carbon budget is depleted. What is the functional form? Is it:
- A linear depletion schedule (S rises proportionally as budget is consumed)?
- A convex schedule (S accelerates as the budget approaches zero, consistent with the corrected `f_scarcity`)?
- A step function tied to IPCC carbon budget categories (1.5°C, 2°C)?
- An auction-derived market price (ETS-linked)?

The choice of functional form has large implications for NPV calculations over a 25-year project life.

**1.7** At the infrastructure project level, the entity making the ONPV calculation (DFI) is not the entity generating the physical units (project company). How is the formula handed off between the project level (where physical units are measured) and the entity level (where `V_liquidation`, `D_senior`, and `AF_direct` live)? Is there a defined interface or does the DFI combine both in a single calculation?

---

## Session 2 — Mapping of Impact Approaches on the Infrastructure Project

*Reference: IFC Performance Standards 1, 2, 5, 7; EBRD Just Transition Initiative; ENCORE; Global Footprint Network six dimensions*

### EF Decomposition and ENCORE Mapping

**2.1** EF has been decomposed into three channels (`EF_physical`, `EF_transition`, `EF_legal`). ENCORE provides natural capital dependency data that maps naturally to `EF_physical`. What data sources are confirmed for `EF_transition` and `EF_legal` respectively? Specifically:
- `EF_transition`: is it derived from NDC sector coverage assessments, NGFS scenario transition scores, EU taxonomy alignment, or a combination?
- `EF_legal`: is it derived from the Wetzer five-method assessment framework, the Sabin Center global climate litigation tracker, IPCC attribution confidence levels, or a bespoke scoring?

**2.2** The six Global Footprint Network dimensions (cropland, grazing, forest, fishing, built-up land, carbon) do not map one-to-one to the ENCORE dependency categories or the Pflichtenheft indicator set. What crosswalk exists or needs to be developed between these three classification systems? Which system takes precedence when there is a conflict?

**2.3** VR (Vulnerability Readiness) is defined as a management transition score but the session frames it against IFC Performance Standards and the EBRD Just Transition Initiative. Which specific IFC PS clauses correspond to VR improvement? Proposed mapping requiring validation:

| IFC Performance Standard | VR-relevant requirement |
|---|---|
| PS1 (Assessment and Management) | Management plan existence and quality → VR base score |
| PS2 (Labour) | ILO Decent Work compliance → VR social sub-component |
| PS5 (Land Acquisition) | Resettlement action plan → VR for land/biodiversity indicator |
| PS7 (Indigenous Peoples) | Free, prior, informed consent → VR for community-facing indicators |

Is this mapping agreed? What is the scoring algorithm that converts PS compliance levels into VR scores between 0 and 1?

**2.4** The formula correction introduces `VR_min = 0.3` as the credibility threshold below which no legal attenuation applies. Is 0.3 the right value? How was it derived? Should it be differentiated by indicator — for example, a lower threshold for GHG (where attribution science and litigation are most mature) versus biodiversity (where legal precedent is less developed)?

**2.5** `BF` (Biocapacity Factor) is a new term representing the jurisdiction's binding restoration plan. For infrastructure projects spanning multiple jurisdictions (cross-border pipelines, regional power grids, international transport corridors), how is `BF_i` calculated? Is it the minimum across jurisdictions, a weighted average by asset footprint, or does each segment receive a separate ONPV calculation?

**2.6** The session addresses the local vs. global overshoot conflict: if a project is in a water-stressed basin (local O = 1) but the global indicator is within limits (global O = 0), how does the formula resolve this? The corrected formula uses `O_i` at the indicator level, but does not specify the geographic scope at which O is assessed. Should O be assessed at:
- Global level (planetary boundary)?
- National level (country biocapacity)?
- Basin/watershed/airshed level (local ecosystem boundary)?
- Project-specific level (operational footprint)?

This is a fundamental design choice. A project that uses water from an over-stressed local basin but sits in a country that is overall water-surplus could be classified as O = 0 at national level and O = 1 at basin level. The financial implications are material.

---

## Session 3 — Analysis of User Needs and Indicator Gaps

*Reference: GRI 401 (Employment), GRI 413 (Local Communities), FASTInfra gaps*

### Attribution Factor and Engagement Multiplier

**3.1** `AF` has been split into `AF_direct` (ownership-weighted) and `AF_engagement` (influence-weighted, applied only to `L_legal`). For DFI-financed infrastructure, the DFI often holds no equity — it is a lender. How is `AF_direct` calculated for a lender versus an equity investor? Does the DFI's share of `L_legal_effective` correspond to its share of the loan book, its share of total project financing, or something else?

**3.2** The session describes an "engagement multiplier" — the degree to which the DFI influenced the project's green design. This is qualitatively different from equity or loan proportion. How is meaningful engagement operationalised? Specifically:
- What constitutes engagement sufficient to activate the engagement multiplier (and thereby increase ONPV credit)?
- What constitutes engagement that was available but not exercised (and thereby increases `AF_engagement` liability under the Wetzer framework)?
- Who makes this determination — the DFI itself, an independent verifier, or a regulator?

**3.3** GRI 401 (Employment) and GRI 413 (Local Communities) are identified as filling gaps in social data that FASTInfra misses. What specific datapoints from GRI 401 and 413 are needed to complete the `Physical_Unit` inputs for the social indicators in the ONPV formula (job-years, community investment €, grievance rates)? Are these datapoints already collected by IFC/EBRD-financed projects as part of E&S monitoring, or does a new data collection requirement need to be introduced?

**3.4** Living wage gap (`S2.8` in the Pflichtenheft) is currently not covered in FASTInfra. Is there agreement that it should be included in ONPV? If yes, what is the `VF` (value factor) for living wage — i.e., the societal cost per € of wage gap per worker — and what is its source?

**3.5** For the `Interaction_penalty` term, the correlation matrix `ρ_ij` across indicators under adverse scenarios is currently unspecified. For infrastructure project assessment, what is the agreed set of correlated indicator pairs that should receive a non-zero `ρ_ij`? Candidates identified from the physical risk analysis:
- Water and crop yield (drought scenario): high positive correlation
- Energy and cooling demand (heat wave scenario): high positive correlation
- GHG and carbon border adjustment costs (policy scenario): direct linkage
- Biodiversity loss and agricultural productivity (physical scenario): medium positive correlation

Is there an agreed correlation matrix, or does this need to be developed? Who is the methodological owner?

**3.6** The formula currently applies `Q_historical` (cumulative historical quantity) for the `L_legal` term. For newly constructed infrastructure projects, `Q_historical` is zero at financial close. Does this mean new projects carry no `L_legal` exposure at inception? If so, at what point does a project's historical accumulation become material enough to trigger `P_litigation > 0`? Is there a minimum operating history threshold, or is `P_litigation` non-zero from day one based on sector-level precedent regardless of project age?

---

## Session 4 — Investment Case Analysis: Compare and Contrast (NPV and ONPV with Overshoot)

*Reference: EU Just Transition Mechanism; OECD Finance for a Just Transition; Climate Equity Reference Calculator (CERC)*

### Delta BCR and Concessionality

**4.1** Delta BCR is defined as `BCR_ONPV − BCR_standard`. The BCR thresholds in the Pflichtenheft are:

| BCR | Standard interpretation |
|---|---|
| > 3.0 | Exceptional |
| 2.0–3.0 | Strong |
| 1.5–2.0 | Good |
| 1.0–1.5 | Marginal |
| < 1.0 | Negative net value |

Under the corrected ONPV with the insolvency cap, `BCR_ONPV` can differ from `BCR_standard` in either direction: ONPV can be *higher* (positive externalities dominate) or *lower* (uncompensated liability gap dominates). What is the agreed Delta BCR threshold that justifies concessionality — cheaper loans, blended finance, or first-loss guarantees? Is there a minimum Delta BCR below which concessionality is not warranted even if the project is financially viable?

**4.2** The session proposes using CERC logic to apply a higher Scarcity Premium `S` for projects in wealthy countries on the grounds that those nations have consumed more than their fair share of the planetary budget. This introduces an equity-weighted `S` that varies by country income level and historical cumulative footprint. How does this interact with the `BF` term? A wealthy country with a strong Nature Restoration Plan might have both a high `S` (historical debt) and a high `BF` (current restoration effort). Should these compound, offset, or be treated as independent?

**4.3** The insolvency cap (`L_legal_effective ≤ IV`) means that a project with a high `Liability_Gap` may still show a positive `BCR_ONPV` if the uncompensated externalities are stripped out by the cap. Is this the correct behaviour? Should `Liability_Gap` be deducted from `BCR_ONPV` even though it is legally unrecoverable — on the grounds that it represents real societal cost that simply happens to be borne by others? If so, a second BCR metric is needed:

```
BCR_ONPV_gross = (Benefits + ONPV positive) / (Costs + L_legal_effective)
BCR_ONPV_true  = (Benefits + ONPV positive) / (Costs + Σ_i L_legal_i_uncapped)
```

The gap between `BCR_ONPV_gross` and `BCR_ONPV_true` is the measure of how much societal cost the project externalises beyond its ability to pay. Should both metrics be reported?

**4.4** The Additionality test asks whether the DFI's money is doing unique good that would not happen without it. Currently Additionality is assessed qualitatively. Can `Delta BCR` replace or supplement the qualitative Additionality assessment? Specifically: if `BCR_ONPV > BCR_standard` by a material margin, does this constitute evidence that the DFI's sustainability conditions (which generated the ONPV premium) are what makes the project additional?

**4.5** The formula requires `V_liquidation` for the insolvency cap. At investment appraisal stage, the project does not yet exist. For greenfield infrastructure, `V_liquidation` is estimated from comparable assets and construction cost. How is the insolvency cap applied prospectively — as a sensitivity scenario ("if liquidation value turns out to be X, what is the effective L_legal?") or as a hard constraint on the ONPV calculation at financial close?

**4.6** When multiple indicators simultaneously exceed their overshoot thresholds — the scenario that activates the `Interaction_penalty` — the combined NPV deterioration is multiplicative. The CFA worst-case scenario analysis produced NPV deterioration approximately 2.8 times the sum of individual shocks. Does the ONPV framework adopt this multiplier, derive its own from the indicator correlation matrix, or leave it as a sensitivity scenario to be run separately by the user?

---

## Session 5 — Conclusion: Insights, Outputs, Technical Note and Executive Brief

*Reference: TCFD/TNFD reporting standards; Minimum Viable ONPV*

### Outputs and Minimum Viable Formula

**5.1** The session proposes a "Minimum Viable ONPV" for immediate use. Based on the formula corrections, what is the minimum set of terms that cannot be omitted without producing a materially misleading result? Proposed minimum viable set requiring confirmation:

| Term | Omittable? | Reason |
|---|---|---|
| `Physical_Unit × VF` | No — this is the base | Cannot omit |
| `f_scarcity` with continuous O | Debated — see Q1.1 | Binary gate may be acceptable minimum |
| `EF_physical` only (drop transition and legal) | Possibly — simpler | Loses the Wetzer channel entirely |
| `g_readiness` with threshold | Partially — threshold critical | Linear `(1−VR)` is wrong but may be initial approximation |
| `BF` | Omittable short-term | Data availability issue; flag as missing |
| `L_legal` | No — Wetzer shows omission creates material misrepresentation | Must include at least as a qualitative flag |
| Insolvency cap | No — uncapped L_legal is technically incoherent | Must include |
| `Liability_Gap` reporting | No — core governance output | Must report even if formula is simplified |
| `Interaction_penalty` | Omittable short-term | Replace with scenario sensitivity note |

Is this prioritisation agreed? What is the timeline for moving from minimum viable to full specification?

**5.2** The `Liability_Gap` is identified as the most important output for regulators and for financial system stability assessment. Should the Technical Note recommend that DFIs report aggregate `Liability_Gap` across their infrastructure portfolio to their supervisory authority — analogous to how banks report non-performing loan ratios? If yes, what is the reporting frequency and the threshold above which disclosure becomes mandatory?

**5.3** TCFD/TNFD alignment requires scenario analysis. The corrected formula produces three distinct risk outputs: transition risk ONPV (early NDC action), physical risk ONPV (late action), and legal risk ONPV (Wetzer attribution channel). Should the Technical Note require that all three scenarios be run for every project above a materiality threshold, with the results presented as a range rather than a single point estimate?

**5.4** The "Number of Earths" framing is proposed as a calibration tool for future infrastructure. Concretely: if humanity currently operates at 2.0 Earths, and infrastructure investment is the primary driver of locked-in resource demand over 25–30 year asset lifetimes, what is the implied maximum `Physical_Unit × VF` per infrastructure investment dollar that is consistent with a pathway back to 1.0 Earth by 2050? Is this a useful metric to include in the Technical Note as a reference anchor — a "planetary budget per dollar invested"?

**5.5** The Executive Brief needs to communicate the insolvency cap and the `Liability_Gap` to non-technical audiences (DFI boards, finance ministers, sovereign wealth fund trustees). The non-technical summary produced alongside this framework offers one approach. What specific messages must the Executive Brief convey? Candidates:
- A company cannot pay more than it owns, but the damage is still real — it just gets paid by someone else (taxpayers, communities, future generations)
- The gap between what a company can pay and what it owes is a hidden subsidy that conventional financial analysis does not see
- DFIs that do not price this gap are not managing their portfolio risk — they are passing it on

Are these the right messages? What does each institutional audience (IFC board, EBRD supervisory board, central bank governor) need to hear differently?

**5.6** The Knowledge Series concludes with a Technical Note. What is the agreed governance process for adopting the corrected formula as the official ONPV specification? Specifically:
- Who has sign-off authority (VBA, Greenings, IFC, EBRD, all jointly)?
- What validation process is required before the corrected formula replaces the original?
- Is a pilot calculation on one or more live infrastructure projects required before the Technical Note is finalised?
- What is the relationship between this Technical Note and the Pflichtenheft v1.0 — does the Technical Note supersede, supplement, or feed back into a Pflichtenheft v2.0?
