# ONPV Impact Formula — Corrected Specification

**Status:** Revised
**Basis:** Natural Capital NPV Sensitivity Framework · Wetzer et al. (2024) *Science* adj0598 · CFA Leverage Analysis · Pflichtenheft Value Factor Library

---

## Original Formula

```
ONPV Impact = Σ [ Physical Unit
                × (VF × (1 + (O × S)))
                × EF_exposure
                × (1 − VR)
                × AF ]
```

| Term | Label | Original Definition |
|---|---|---|
| Physical Unit | Impact Driver Quantity | Reported or measured project data (tCO₂e, m³, ha, kg PM₂.₅, job-years …) |
| VF | Value Factor | Base monetised societal cost (€/unit), sourced from Pflichtenheft Value Factor Library |
| O | Overshoot Toggle | Binary: 0 = within planetary limits; 1 = in overshoot |
| S | Scarcity Premium | Fractional uplift applied to VF when O = 1 |
| EF_exposure | Exposure Factor | Sector- and geography-weighted dependency score (0–1+), ENCORE mapping |
| VR | Vulnerability Readiness | Management transition score (0–1): 0 = fully exposed, 1 = fully managed |
| AF | Attribution Factor | Investor's share of impact, scaled by ownership control tier and collective engagement influence |

---

## Problems Identified

### P1 — O is binary but overshoot is a gradient

`O ∈ {0, 1}` creates a cliff edge. A basin at 99% of sustainable yield scores identically to one at 50%; a basin at 101% triggers the full scarcity premium identically to one at 300%. No natural resource system behaves this way. WRI Aqueduct scores run 0–5 continuously; carbon budgets are tracked as percentage exceedance of a remaining budget; soil organic carbon depletion is measured on a spectrum.

### P2 — The scarcity premium is linear but resource damage is convex

`(1 + (O × S))` applies a flat proportional uplift. This is inconsistent with the leverage analysis: when a resource approaches its physical threshold, the degree of operating leverage (DOL) spikes non-linearly. The marginal unit consumed at near-zero safe yield carries disproportionately large societal cost. Environmental economics documents this as a convex damage function — the same reason the social cost of carbon accelerates with cumulative emissions.

### P3 — EF_exposure is a single number but the three risk channels have different exposure profiles

Physical exposure, transition exposure, and legal exposure are structurally different:

- **Physical**: geographic and operational dependency on the resource
- **Transition**: how far ahead of or behind a policy curve the sector and jurisdiction are
- **Legal**: whether the causal chain from this company's resource use to specific damages is scientifically demonstrable (Wetzer: attribution science maturity, litigation precedent)

A mining company in a country with no carbon pricing has high physical exposure but low transition exposure. A fossil fuel company under an established ETS with active climate litigation has all three simultaneously. Collapsing these into one score loses the information needed to distinguish which scenario is active.

### P4 — VR linearly reduces impact but legal exposure is threshold-gated

`(1 − VR)` assumes smooth proportional protection as management readiness improves. This is incorrect for the legal channel. Wetzer shows that claimants succeed specifically against companies that were aware of their exposure but took insufficient action. Partial acknowledgement without credible verified action may worsen legal exposure relative to no plan at all, because it creates a paper trail of awareness without protection.

Additionally, `VR` captures only the company-level management plan. The framework establishes a second independent escape condition — a binding country or jurisdiction plan to increase the biocapacity of the specific resource — which is entirely absent from the original formula.

### P5 — L_legal is entirely absent

The attribution-based legal liability identified by Wetzer et al. is not in the formula. It is structurally different from the physical damage term:

- It is **retrospective** — based on historical cumulative use, not current-period physical units
- It is **probabilistic** — depends on the state of attribution science and litigation precedent in the jurisdiction
- It is **additive** to the current-period impact, not a multiplier of it

Chevron's $8.5T estimated exposure is not derived by multiplying current emissions by a value factor. It is derived by summing historical emissions, attributing a causal share of global climate damages to that company, and converting that into present-value liability using the social cost of carbon. The formula cannot reproduce this result without a dedicated term.

### P6 — Σ assumes additivity but combined indicator shocks are multiplicative

The formula sums impacts across indicators. When multiple indicators degrade simultaneously — the norm in a physical risk scenario, where drought reduces water availability *and* increases cooling demand *and* reduces yields *and* increases heat stress — the combined effect on the contribution margin is multiplicative, not additive. The DOL analysis demonstrates this: when both price and variable cost move adversely at the same time, the contribution margin denominator collapses far faster than the sum of individual shocks predicts.

### P7 — AF conflates two methodologically distinct attribution types

Direct ownership attribution (proportional financial claim on company cash flows) and collective engagement attribution (investor influence exercised or withheld) are legally and financially different. Merging them into one `AF` incorrectly attributes legal liability to passive minority investors without meaningful control, and may understate liability for active large shareholders who declined to push for transition.

### P8 — L_legal is uncapped and can exceed the insolvency value of the company

An uncapped `L_legal` can assign a liability that exceeds everything the company owns. In law, a defendant cannot pay more than its distributable value in insolvency. The excess is extinguished — it represents real societal damage that is never compensated. This liability gap must be tracked explicitly: it is the structural signal of a company that has socialised its natural capital costs beyond its ability to internalise them, and the precise condition that Wetzer identifies as creating systemic risk in financial markets.

---

## Corrected Formula

```
ONPV Impact = Σ_i [
    Physical_Unit_i
    × VF_i × f_scarcity(O_i, S_i)
    × (w_p × EF_physical_i  +  w_t × EF_transition_i  +  w_l × EF_legal_i)
    × g_readiness(VR_i, BF_i)
    × AF_direct
  ]
  + Σ_i [ L_legal_i_effective × AF_engagement ]
  + Interaction_penalty
```

---

## Component Definitions

### f_scarcity — Convex Scarcity Function

Replaces `(1 + (O × S))`.

```
f_scarcity(O_i, S_i) = (1 + S_i)^(1 + O_i)
```

Where `O_i ∈ [0, ∞)` is a continuous overshoot intensity score, not a binary toggle:

| O_i value | Meaning | f_scarcity result |
|---|---|---|
| 0 | Resource within planetary limits | `(1 + S)^1` — base premium only |
| 1 | Resource at tipping threshold | `(1 + S)^2` — squared amplification |
| 2 | Severe overshoot | `(1 + S)^3` — cubic, reflecting accelerating damage |

The overshoot score `O_i` is sourced from continuous datasets: WRI Aqueduct (water, 0–5), IPCC remaining carbon budget exceedance (GHG), IPBES habitat intactness index (biodiversity), WHO exceedance ratio (air quality).

---

### EF — Decomposed Exposure Factors

Replaces single `EF_exposure`. Three separate scores:

| Factor | What it measures | Data source |
|---|---|---|
| `EF_physical_i` | Geographic and operational dependency on resource `i`; proximity to degraded resource | ENCORE natural capital mapping; WRI Aqueduct; IPCC hazard maps |
| `EF_transition_i` | Regulatory and policy exposure; how far the sector and jurisdiction are ahead of or behind the policy trajectory for resource `i` | NDC coverage assessment; carbon price schedules; TNFD requirements; EU taxonomy sector classifications |
| `EF_legal_i` | Attribution probability; maturity of attribution science for indicator `i`; number of active and successful precedent cases in this sector and jurisdiction | Wetzer five-method assessment; global climate litigation tracker; IPCC attribution confidence levels |

Channel weights `w_p`, `w_t`, `w_l` are scenario-configurable. Default is equal weighting `(1/3, 1/3, 1/3)`. Under a physical risk scenario the weights shift toward `w_p`; under an active litigation environment toward `w_l`.

---

### g_readiness — Threshold-Gated Readiness Function

Replaces `(1 − VR)`.

```
g_readiness(VR_i, BF_i) = (1 − max(VR_i − VR_min, 0) / (1 − VR_min)) × (1 − BF_i)
```

Where:

| Term | Definition |
|---|---|
| `VR_i` | Vulnerability Readiness score for indicator `i` (0–1): verified management plan quality, independently assured |
| `VR_min` | Minimum credibility threshold (recommended: 0.3). Below this score, no legal attenuation is granted. A vague commitment without verified milestones provides zero protection under the legal channel |
| `BF_i` | Biocapacity Factor (0–1): the extent to which the jurisdiction's binding restoration plan reduces system-level exposure for indicator `i` independently of company action |

The two terms compound multiplicatively: a strong company plan in a jurisdiction with a strong restoration plan achieves the greatest reduction. Neither alone eliminates the exposure.

**Examples of BF_i evidence:**

- Biodiversity: national Nature Restoration Plan under EU Nature Restoration Law 2024, covering the specific habitat type material to the company
- Water: binding national basin restoration plan with enforced abstraction limits for the specific catchment
- GHG: NDC with sector-specific binding cap and enforcement mechanism for the company's NACE sector
- Air quality: designated Clean Air Zone with verified trajectory for the specific pollutant type

---

### L_legal — Attribution-Based Legal Liability

New additive term. Entirely absent from the original formula.

#### Step 1 — Uncapped liability per indicator

```
L_legal_i = P_litigation_i × Attribution_share_i × SCC_i × Q_historical_i
```

| Term | Definition |
|---|---|
| `P_litigation_i` | Probability that attribution litigation is filed and successful for indicator `i` in the relevant jurisdiction; informed by Wetzer's five assessment methods; scales with number of successful precedent cases |
| `Attribution_share_i` | Company's attributable fraction of total sector or global damage for indicator `i`; derived from market share of historical production or emissions relative to sector total |
| `SCC_i` | Social cost of indicator `i` (€/tCO₂e, €/m³, €/ha, €/kg PM₂.₅ …); per Pflichtenheft Value Factor Library and international databases |
| `Q_historical_i` | Cumulative historical quantity of indicator `i` used or emitted; retrospective; not the current-period Physical Unit |

#### Step 2 — Insolvency cap

A company cannot pay more than its distributable value in insolvency. The cap is applied at the aggregate level across all indicator-driven claims:

```
IV = max(0,  V_liquidation − D_senior)
```

| Term | Definition |
|---|---|
| `IV` | Net distributable insolvency value |
| `V_liquidation` | Forced-sale liquidation value of all company assets; distress-discounted; not going-concern enterprise value |
| `D_senior` | All claims senior to unsecured litigation in the insolvency waterfall: secured debt, tax authorities, employee wages, pension obligations |

When the sum of uncapped claims across all indicators exceeds `IV`, each claim is pro-rated:

```
L_legal_i_effective = L_legal_i × min(1,  IV / max(IV,  Σ_i L_legal_i))
```

This ensures:

```
Σ_i L_legal_i_effective  ≤  IV
```

#### Step 3 — Liability gap (report separately)

```
Liability_Gap_i     = L_legal_i − L_legal_i_effective

Σ_i Liability_Gap_i = max(0,  Σ_i L_legal_i − IV)
```

The liability gap is not a rounding artefact. It is real attributable societal damage that the legal system cannot recover from this company because the company does not hold sufficient value to pay for it. It must be reported as a separate output, not silently absorbed into the formula.

**Interpretations of the liability gap:**

| Audience | Meaning |
|---|---|
| Regulators | Case for mandatory environmental liability insurance, decommissioning bonds, or security requirements — analogous to nuclear liability funds and offshore oil spill security |
| Investors in financial system | Systemic underpricing of natural capital risk; the Wetzer "flying blind" condition at portfolio level, not just company level |
| ONPV framework | Flag that negative externalities are structurally uncompensated; the project has socialised its natural capital costs and privatised its profits |
| Credit analysts | Signal that insolvency risk is entangled with environmental liability; traditional solvency ratios will understate true exposure |

**Perverse incentive flag:**

The insolvency cap creates an incentive to reduce `V_liquidation` rather than reduce actual impact — keeping assets offshore, distributing profits as dividends before liability materialises, or operating through thin-capitalised subsidiaries. The framework should flag any significant decline in `V_liquidation` relative to prior periods alongside a widening `Liability_Gap`, as these are indicators of liability-avoidance behaviour rather than genuine impact management.

---

### AF — Split Attribution Factors

Replaces single `AF`.

| Factor | Applies to | Definition |
|---|---|---|
| `AF_direct` | Current-period physical and transition damage terms | Ownership-weighted: investor's proportional equity or debt claim on company cash flows, modulated by control tier |
| `AF_engagement` | `L_legal_i_effective` only | Influence-weighted: reflects the extent to which the investor exercised or withheld meaningful engagement after becoming aware of the climate risk exposure; binary credibility threshold applied (meaningful engagement vs. no engagement) |

The separation matters because legal liability does not flow strictly through ownership percentage. A 2% shareholder with no voting engagement carries different legal exposure than a 2% shareholder that voted against a climate resolution and declined to engage with management on transition risk.

---

### Interaction_penalty — Cross-Indicator Compounding Term

New term. Addresses the fact that simultaneous adverse shocks across correlated indicators are multiplicative in their effect on the contribution margin, not additive.

```
Interaction_penalty = Σ_{i≠j} ρ_ij × Impact_i × Impact_j × δ_correlated
```

Where:

| Term | Definition |
|---|---|
| `ρ_ij` | Known correlation between indicator `i` and indicator `j` under the adverse scenario (e.g., drought simultaneously degrades water availability *and* energy availability *and* crop yield) |
| `δ_correlated` | Binary flag: 1 if indicators `i` and `j` both operate through the same contribution margin constraint for this sector; 0 if they affect separate cost lines |

In practice, when three or more primary indicators are simultaneously in overshoot for the same sector, a scenario multiplier is applied consistent with the CFA worst-case scenario analysis, where simultaneous adverse inputs produced NPV of −$25,632 versus the approximately −$9,136 sum of individual shocks — a factor of approximately 2.8x.

---

## Full Variable Reference

| Symbol | Label | Definition | Correction |
|---|---|---|---|
| `Physical_Unit_i` | Impact Driver Quantity | Reported or measured data for indicator `i` (tCO₂e, m³, ha, kg PM₂.₅, job-years …) | Unchanged |
| `VF_i` | Value Factor | Base monetised societal cost (€/unit); Pflichtenheft Value Factor Library | Unchanged |
| `O_i` | Overshoot Intensity | Continuous score [0, ∞); resource deficit relative to planetary limit for indicator `i` | Was binary 0/1 |
| `S_i` | Scarcity Premium | Fractional uplift to VF under resource deficit | Unchanged definition; now enters convex function |
| `f_scarcity(O_i, S_i)` | Scarcity Function | `(1 + S_i)^(1 + O_i)`; convex amplification | Replaces `(1 + O×S)` |
| `EF_physical_i` | Physical Exposure Factor | Geographic and operational resource dependency | Decomposed from single EF |
| `EF_transition_i` | Transition Exposure Factor | Regulatory and policy exposure for indicator `i` | New |
| `EF_legal_i` | Legal Exposure Factor | Attribution probability; litigation maturity for indicator `i` | New |
| `w_p, w_t, w_l` | Channel Weights | Scenario-configurable weighting of three exposure channels; default 1/3 each | New |
| `VR_i` | Vulnerability Readiness | Verified management plan quality for indicator `i` (0–1) | Unchanged definition |
| `VR_min` | Readiness Threshold | Minimum credibility floor below which no legal attenuation applies (recommended: 0.3) | New |
| `BF_i` | Biocapacity Factor | Jurisdiction's binding restoration plan coverage for indicator `i` (0–1) | New |
| `g_readiness(VR_i, BF_i)` | Readiness Function | Threshold-gated; incorporates both company plan and country plan | Replaces `(1−VR)` |
| `AF_direct` | Direct Attribution Factor | Ownership-weighted; applied to current-period damage terms | Split from single AF |
| `AF_engagement` | Engagement Attribution Factor | Influence-weighted; applied to legal liability term only | Split from single AF |
| `P_litigation_i` | Litigation Probability | Probability of successful attribution claim for indicator `i` in relevant jurisdiction | New |
| `Attribution_share_i` | Attribution Share | Company's causal fraction of total sector or global damage for indicator `i` | New |
| `SCC_i` | Social Cost | Societal cost per unit of indicator `i` (€/tCO₂e, €/m³, €/ha …) | New |
| `Q_historical_i` | Historical Quantity | Cumulative historical use or emissions for indicator `i`; retrospective | New |
| `L_legal_i` | Uncapped Legal Liability | `P_litigation_i × Attribution_share_i × SCC_i × Q_historical_i` | New additive term |
| `V_liquidation` | Liquidation Value | Forced-sale asset value; distress-discounted | New |
| `D_senior` | Senior Claims | Secured debt, tax, wages, pensions ranking above litigation in insolvency waterfall | New |
| `IV` | Insolvency Value | `max(0, V_liquidation − D_senior)` | New |
| `L_legal_i_effective` | Capped Legal Liability | `L_legal_i × min(1, IV / max(IV, Σ_i L_legal_i))` | New |
| `Liability_Gap_i` | Uncompensable Residual | `L_legal_i − L_legal_i_effective`; reported separately | New output |
| `Interaction_penalty` | Cross-Indicator Compounding | `Σ_{i≠j} ρ_ij × Impact_i × Impact_j × δ_correlated` | New |

---

## Sources

- Wetzer, T., Stuart-Smith, R. & Dibley, A. (2024). "Climate risk assessments must engage with the law." *Science* 383(6679), 152–154. DOI: 10.1126/science.adj0598
- CFA Institute (2022). *CFA Program Curriculum Level I, Volume 4* — Reading 32: Measures of Leverage
- Kaplan Schweser (2020). *CFA Level II Notes, Book 2* — Capital Budgeting and Sensitivity Analysis
- Greenings / Value Balancing Alliance (2024). *Transitionvaluation Project* — github.com/Greenings/transitionvaluation
- WifOR Institute (2024). *Value Factors: Economic Impact Coefficients*
- VBA / Pflichtenheft (2025). *Infrastructure Impact Measurement and Valuation Service v1.0*
- GRESB (2025). *Infrastructure Assessment Indicators Summary*
- FAST-Infra (2024). *Sustainable Infrastructure Label v2.0*
- IPBES (2019). *Global Assessment Report on Biodiversity and Ecosystem Services*
- EU Nature Restoration Law (2024). Regulation (EU) 2024/1991
