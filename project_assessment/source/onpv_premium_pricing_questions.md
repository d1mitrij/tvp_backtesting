# ONPV Knowledge Series — Premium Pricing for Overshoot-Positive Products

**Purpose:** Structured agenda of open questions on the revenue-side mirror of the ONPV scarcity premium. When a product is associated with a natural capital indicator that is in overshoot, and the product produces, restores, or substitutes for that resource, it can command a higher price. These questions map that logic to the IFC/EBRD Knowledge Series session structure, parallel to the liability-side questions in the companion document.

**Companion document:** `onpv_knowledge_series_questions.md`

---

## The Mirror Principle

The corrected ONPV formula applies a convex scarcity premium to the **cost side**: when a resource is in overshoot, the variable cost of using that resource rises, compressing the contribution margin and degrading NPV. The same scarcity logic operates symmetrically on the **revenue side**: when a product generates, restores, or substitutes for a resource that is in overshoot, the scarcity of that resource increases the product's market value.

**Cost side** (liability):
```
V_natural_i rises when O_i > 0  →  CM compresses  →  NPV falls
```

**Revenue side** (opportunity):
```
P_product_i rises when O_i > 0  →  CM expands  →  NPV rises
```

The premium revenue formula mirrors the cost formula:

```
P_premium_i = Physical_Unit_positive_i
            × VF_i × f_scarcity(O_i, S_revenue_i)
            × EF_market_i
            × CR_i
            × AF_direct
```

Where:

| Term | Definition |
|---|---|
| `Physical_Unit_positive_i` | Units of indicator `i` produced, restored, or substituted by the product (tCO₂e sequestered, m³ water restored, ha habitat recovered, kg PM₂.₅ avoided …) |
| `VF_i` | Value factor for indicator `i` — same library as cost side (€/unit) |
| `f_scarcity(O_i, S_revenue_i)` | Convex scarcity function — same form as cost side; amplifies premium as overshoot deepens |
| `EF_market_i` | Market Exposure Factor (0–1): how developed, liquid, and accessible is the market willing to pay the premium for this indicator |
| `CR_i` | Certification and Verification Requirement (0–1): the degree to which the premium claim is independently verified and therefore credible to buyers |
| `AF_direct` | Attribution factor: the share of the premium attributable to this product/project as distinct from counterfactual |

This premium term is additive to the conventional financial revenue stream — it represents the uplift in `P` (price per unit) that a product commands because it addresses an overshoot condition, rather than contributing to it.

---

## Annex Session
*The valuation model is defined by its use: who buys the premium, at which market level, and what verification is required?*

### Market Structure and System Boundary

**A.1** The liability-side formula operates at the project or entity level because costs fall on the producer. The premium-side formula requires a willing buyer. At which market level does the premium materialise — voluntary carbon/biodiversity markets, mandatory compliance markets, green procurement specifications, sustainability-linked loan pricing, or green bond coupon differentials? Different markets have different `EF_market_i` scores and different `CR_i` requirements. Is a unified framework possible, or does each market type require a separate premium pathway?

**A.2** Capital allocation on the revenue side happens differently from the liability side. A project that sequesters carbon sells the credit once; a project that restores a water basin may receive ongoing ecosystem service payments over the project's life. A product with a lower ecological footprint may command a price premium at point of sale for its entire commercial lifetime. These are structurally different revenue streams. How does the formula handle the temporal profile of premium revenue — is it a one-time uplift, an annuity, or a declining stream as overshoot is resolved and the scarcity premium erodes?

**A.3** Who are the buyers of premium-priced overshoot-positive products? Proposed typology requiring confirmation:

| Buyer | Premium mechanism | Indicator addressed |
|---|---|---|
| Carbon market participant | Carbon credit purchase | GHG / carbon |
| Corporate sustainability officer | Insetting, supply chain premium | GHG, water, biodiversity |
| Government / public procurer | Green public procurement specification | All indicators |
| DFI / blended finance investor | Concessionality, first-loss, greenium | All indicators |
| Consumer / end-user | Ecolabel price premium | Food, fiber, energy |
| Bank / insurer | Sustainability-linked loan / insurance discount | All indicators |

Are these the right buyers? What is the size of each market and does it scale to absorb the premium volume that overshoot-positive infrastructure would generate?

**A.4** Infrastructure projects are intermediary between product/site level and corporate entity level. The premium on a renewable energy project (avoided GHG per kWh) accrues differently depending on whether it is captured as a higher electricity tariff, a carbon credit, a green bond greenium, or a concessional loan. How does the formula map the same `Physical_Unit_positive_i` to multiple simultaneous premium channels without double-counting? What is the hierarchy when multiple channels claim the same physical unit?

**A.5** What is the minimum verified data package required for a product to claim a premium under this framework? The premium formula requires: physical units positive (measured or modelled), value factor (library), O_i (external dataset for the specific geographic scope), `EF_market_i` (market readiness assessment), and `CR_i` (third-party verification of delivery). Is there a minimum viable premium claim that requires fewer inputs — and if so, does it carry a discount to the full premium to reflect the verification uncertainty?

---

## Session 1 — Introduction: How Does Overshoot Determine Premium Eligibility?

*Reference: Wackernagel et al. (2021), Global Footprint Network six dimensions, Stockholm Resilience Centre planetary boundaries*

### The Overshoot Gate for Revenue

**1.1** The companion document flags the binary vs. continuous O tension for the cost side. On the revenue side, the binary question is different: should the premium **require** O = 1 (only available when the resource is in deficit), or should there be a graduated premium even when the resource is within limits? Two positions:

- **Overshoot-only premium**: the premium is only available when `O_i = 1`. A product that conserves water in a water-abundant basin earns no premium; the same product in a water-stressed basin earns the full premium. This maintains the scarcity logic but creates a geographic arbitrage — the same product has different revenue depending on where it is deployed.
- **Graduated premium**: any product that produces a positive indicator earns *some* premium, scaled by how close the resource is to its overshoot threshold. This rewards preventive action before the crisis but may dilute the signal that overshoot creates.

Which position does the Knowledge Series adopt, and does it differ by indicator?

**1.2** The Wackernagel framework identifies two responses to biocapacity deficit: liquidating local assets (overshoot) and net biocapacity import (financial substitution). A product that enables net biocapacity import — for example, a financial product that funds conservation in a resource-rich country to offset consumption in a resource-poor country — is not producing the biocapacity locally but is enabling its import. Does this product qualify for a premium under the same formula as a product that directly produces the indicator? If yes, does it carry the same `CR_i` or a lower one to reflect the uncertainty of import-based claims?

**1.3** The Social Cost of Carbon moves from a flat fee to a dynamic price as the carbon budget depletes. The same logic applies to premium revenue: the premium a carbon sequestration product can charge rises as the remaining carbon budget shrinks. But this creates a perverse dynamic — the more successfully the market reduces emissions, the lower the premium becomes, reducing the financial incentive for sequestration. How does the formula handle this self-defeating scarcity dynamic? Is there a floor on the scarcity premium to maintain incentive even as overshoot is progressively resolved?

**1.4** The six Global Footprint Network dimensions (cropland, grazing, forest, fishing, built-up land, carbon) each support different overshoot-positive products. For infrastructure specifically: a port project occupies built-up land (cost-side footprint), but if it incorporates a marine restoration zone it produces fishing grounds (revenue-side premium). How does the formula net these two — the overshoot cost on built-up land against the overshoot premium on fishing grounds — when they are not the same indicator? Is netting permissible, or must each indicator be reported and priced separately?

**1.5** At the entity level versus the project level: a company may operate in a sector that is a net contributor to overshoot (fossil fuels, high-water industry) but have a specific product line that addresses it (carbon capture, water recycling services). The premium accrues to the product but the liability accrues to the entity. How does the entity-level ONPV handle a portfolio of products with mixed overshoot positions — some generating premiums, some generating liabilities — when the insolvency cap is applied at the entity level?

---

## Session 2 — Mapping of Impact Approaches on the Infrastructure Project

*Reference: IFC Performance Standards; EBRD Just Transition Initiative; ENCORE; Global Footprint Network*

### Certifying and Pricing the Positive

**2.1** ENCORE maps sectors and products to natural capital dependencies on the cost side. What is the equivalent mapping on the revenue side — which infrastructure project types are associated with which positive indicator outputs? Proposed mapping requiring validation:

| Project type | Positive indicator produced | Premium mechanism |
|---|---|---|
| Renewable energy (solar, wind) | GHG avoided (tCO₂e) | Carbon credit, green tariff, green bond |
| Reforestation / agroforestry | Carbon sequestered, biodiversity (ha), water retained | Carbon credit, biodiversity credit, watershed payment |
| Water treatment / efficiency | Water restored (m³), water pollution reduced | Water stewardship certificate, utility premium |
| Sustainable agriculture | Cropland within limits, soil carbon | Ecolabel, sustainable supply chain premium |
| Marine / coastal infrastructure | Fishing grounds restored, blue carbon | Blue carbon credit, marine biodiversity credit |
| Green building | GHG avoided, energy efficiency, air quality | Green building certification premium, energy savings |
| Nature-based urban infrastructure | Biodiversity, air quality, urban cooling | Ecosystem service payment, municipal procurement |

Is this mapping complete? What project types are missing? Are all the premium mechanisms listed liquid and accessible at investment-grade scale?

**2.2** `CR_i` (Certification and Verification Requirement) is the factor that makes the premium credible to buyers. What are the agreed certification standards for each indicator? Proposed mapping:

| Indicator | Certification standard | `CR_i` score if certified | `CR_i` score if uncertified |
|---|---|---|---|
| GHG sequestered | Gold Standard, Verra VCS, REDD+ | 1.0 | 0.2 |
| Biodiversity restored | TNFD, Biodiversity Net Gain (UK), IUCN NNL | 0.8 | 0.1 |
| Water restored | Alliance for Water Stewardship (AWS), SBTfw | 0.7 | 0.15 |
| Sustainable land use | Rainforest Alliance, FSC, RSPO | 0.8 | 0.2 |
| Air quality improvement | Verified health impact assessment | 0.5 | 0.05 |

Are these standards agreed? What happens to the premium formula when no recognised certification scheme exists for a given indicator — is the premium set to zero, estimated with a large discount, or flagged as speculative?

**2.3** `EF_market_i` (Market Exposure Factor) captures how liquid and accessible the premium market is. Carbon markets are relatively mature; biodiversity credit markets are nascent; water stewardship payments are geographically patchy. What is the agreed `EF_market_i` scale, and who maintains it? Should it be updated annually as markets develop? Importantly: what is the `EF_market_i` floor — below which the premium is so theoretical that it should not be included in the financial model without a specific buyer commitment?

**2.4** The session frames VR (Vulnerability Readiness) against IFC Performance Standards. On the premium revenue side, the equivalent concept is **premium eligibility readiness** — the degree to which the product meets the conditions to claim the premium. How does the premium eligibility score differ from VR? Specifically: VR reduces liability exposure; premium eligibility increases revenue access. Are they the same score applied in different directions, or structurally different assessments?

**2.5** Local vs. global overshoot for premium claims: a reforestation project in a country that is within its national biocapacity but contributes to global carbon sequestration claims a premium based on global O (global carbon budget depletion). A water restoration project in a water-stressed basin claims a premium based on local O (basin stress level). Should the geographic scope of O for premium claims match the geographic scope of the buyer — i.e., a global carbon buyer triggers global O, a local municipality paying for watershed services triggers basin-level O?

**2.6** When a project operates in a location where the country has a binding restoration plan (`BF_i > 0`), the cost-side liability is reduced. On the revenue side, the same binding restoration plan may indicate that the resource will be restored by government action regardless of the project — reducing the Additionality of the project's premium claim. How does `BF_i` affect `CR_i` or the Additionality assessment on the revenue side? Does a strong national restoration plan make the project's positive contribution less additional and therefore less premium-eligible?

---

## Session 3 — Analysis of User Needs and Indicator Gaps

*Reference: GRI 401, GRI 413; FASTInfra gaps; indicator coverage*

### Attribution and Data for Premium Claims

**3.1** `AF_direct` on the revenue side attributes the premium to the product or project. For infrastructure financed by a DFI, multiple parties contribute to the positive outcome: the project company designs the restoration, the DFI provides finance and imposes sustainability conditions, the government provides permits and regulatory support. How is the premium attribution split between these parties? Is the full premium attributed to the project company (with DFI receiving a share via its loan terms), or does each party receive a direct attribution share?

**3.2** The engagement multiplier that increases liability on the cost side (when a DFI fails to engage) has a positive equivalent on the revenue side: when a DFI actively enables a project to achieve premium-eligible design — through technical assistance, concessional pricing, or covenant requirements — does the DFI's engagement multiplier increase its share of the premium attribution? If so, how is "enabling engagement" defined and verified?

**3.3** The companion document identifies GRI 401 and GRI 413 as filling FASTInfra social data gaps on the cost side. On the revenue side, what social indicators have positive premium potential that are not currently covered in standard infrastructure frameworks? Candidates:

| Social indicator | Positive premium mechanism |
|---|---|
| Local employment above living wage | Supply chain premium; ILO Decent Work certification |
| Gender-equitable hiring | Gender-lens investment premium; sustainability-linked loan conditions |
| Community land rights respected | FPIC certification; indigenous rights premium in green bond framework |
| Inclusive access (last-mile infrastructure) | SDG-aligned investment premium; DFI additionality score |

Are these premium markets real and liquid, or aspirational? What `EF_market_i` score applies to each?

**3.4** The `Q_historical` problem on the cost side (new projects have zero history, so `L_legal = 0` at inception) has a revenue-side equivalent: a new project has no track record of delivering positive indicators. Carbon sequestration projects, for example, require permanence verification over many years before full credits are issued. How does the formula handle **forward-looking premium claims** — revenue anticipated from future positive delivery — versus **retrospective premium claims** — revenue from verified past delivery? Should the NPV model discount forward-looking premiums more heavily than conventional revenue streams to reflect the delivery and verification risk?

**3.5** The `Interaction_penalty` on the cost side captures the multiplicative compounding of simultaneous adverse indicator shocks. Is there an equivalent **interaction bonus** on the revenue side? For example: a project that simultaneously sequesters carbon, restores water, and improves biodiversity may command a premium from each market independently, but may also qualify for bundled certification schemes (e.g., integrated landscape approaches, blue-green infrastructure certifications) that offer a premium above the sum of individual credits. How does the formula handle this positive compounding?

**3.6** Indicator gaps on the positive side: which natural capital benefits that infrastructure generates are not yet covered by any monetised premium market? Candidates requiring discussion:

| Positive indicator | Market status | Gap? |
|---|---|---|
| GHG sequestration | Liquid carbon markets | No gap |
| Biodiversity restoration | Nascent market, patchy | Partial gap |
| Water quality restoration | Very patchy, mostly regulatory | Significant gap |
| Soil carbon / land restoration | Emerging market | Significant gap |
| Urban heat island reduction | No market | Full gap |
| Noise reduction | No market | Full gap |
| Pollinator habitat | No market outside voluntary | Full gap |

For indicators with a full market gap, should the ONPV formula include the societal value (VF × Physical_Unit_positive) as a non-monetised positive impact reported alongside the premium revenue, or should it be excluded from the financial model entirely?

---

## Session 4 — Investment Case Analysis: Compare and Contrast (NPV and ONPV with Premium)

*Reference: EU Just Transition Mechanism; OECD Finance for a Just Transition; CERC; Delta BCR*

### Premium Revenue in the Investment Case

**4.1** The Delta BCR on the cost side is `BCR_ONPV − BCR_standard`, where the difference reflects liabilities that standard BCR ignores. On the revenue side, there is a second Delta BCR: `BCR_ONPV_premium − BCR_ONPV_cost_only`, where the difference reflects premium revenues that standard BCR ignores. Should the investment case present all three BCR figures:

```
BCR_standard        = conventional financial analysis
BCR_ONPV_cost       = standard + liability-side corrections (L_legal, scarcity costs)
BCR_ONPV_full       = standard + liability-side + premium revenue-side
```

If `BCR_ONPV_full > BCR_standard` significantly, the project has a stronger concessionality case. If `BCR_ONPV_cost < BCR_standard` but `BCR_ONPV_full > BCR_standard`, the project destroys conventional value but creates net societal value — what is the DFI's mandate response to this situation?

**4.2** The CERC logic applies a higher Scarcity Premium `S` to wealthy countries for the cost side because they have consumed more than their fair share of the planetary budget. The revenue-side equivalent would apply a **lower premium** to projects in wealthy countries — because the wealthy country should bear more of the cost of transition itself rather than receiving concessional finance for it. Does this logic hold? A wealthy country solar project that avoids carbon emissions has the same physical premium value as an identical project in a poor country, but the equity argument suggests the poor country should receive a higher ONPV revenue credit. How is this differential encoded — in `AF_direct`, in `S_revenue_i`, or through a separate equity weighting factor?

**4.3** The scarcity premium is self-defeating: if all producers of overshoot-positive products succeed, the overshoot resolves, `O_i` returns to zero, and the premium disappears. This is a revenue cliff that does not exist on the cost side (costs do not disappear just because everyone reduces them simultaneously — the liability for historical use remains). How does the financial model handle the scenario where premium revenue is material at appraisal but collapses mid-project life as the overshoot is resolved? Is a sunset clause built into the premium revenue forecast, or is this treated as a standard market risk in the sensitivity analysis?

**4.4** Concessionality justification using ONPV premium: if a project has a high `BCR_ONPV_full` driven largely by premium revenue, the DFI may argue that the premium revenue will allow the project to service market-rate debt — removing the justification for concessional terms. The tension is that premium markets are not yet liquid enough for lenders to rely on them for debt service. How does the formula distinguish between:
- Premium revenue that is **contracted** (e.g., power purchase agreement with green tariff, signed carbon offtake agreement): bankable, reduces concessionality need
- Premium revenue that is **market-dependent** (e.g., voluntary carbon market spot price, ecolabel retail premium): speculative, supports concessionality argument

**4.5** The insolvency cap on the cost side (`L_legal_effective ≤ IV`) means that companies with thin asset bases pay less than the full social cost of their damage. The revenue-side equivalent is that companies with thin asset bases also have limited capacity to invest in premium-eligible production — the capital required to achieve and maintain certification, to install monitoring systems, to engage third-party verifiers, and to access premium markets may be beyond the reach of projects in lower-income countries. Should the formula include a **capacity constraint factor** on `CR_i` that reflects whether the project company has the organisational capacity to maintain premium eligibility over the project life?

**4.6** When the `Interaction_penalty` fires on the cost side (simultaneous adverse shocks multiply damage), the symmetrical **interaction bonus** on the revenue side should also multiply the premium. A project that simultaneously addresses water scarcity, biodiversity loss, and carbon sequestration in a region where all three indicators are in overshoot should command a bundled premium greater than the sum of individual credits. What is the multiplier, and is there evidence from existing bundled certification schemes (e.g., The Nature Conservancy debt-for-nature swaps, REDD+ integrated programmes) that this bundling premium is real and quantifiable?

---

## Session 5 — Conclusion: Outputs, Technical Note and Executive Brief

*Reference: TCFD/TNFD; Minimum Viable ONPV; greenium evidence*

### Minimum Viable Premium Specification and Governance

**5.1** The Minimum Viable ONPV for the cost side requires at minimum: physical units, value factor, binary O gate, and the insolvency-capped `L_legal`. What is the Minimum Viable premium specification? Proposed minimum requiring confirmation:

| Term | Omittable? | Reason |
|---|---|---|
| `Physical_Unit_positive_i` | No | Without it there is no premium claim |
| `VF_i` | No | Required to monetise the unit |
| `f_scarcity` (O gate only) | Binary gate acceptable short-term | Full convex function preferred |
| `EF_market_i` | No — zero if no market exists | Without this, theoretical premiums inflate BCR |
| `CR_i` | No — zero if uncertified | Without this, greenwash premiums inflate BCR |
| Interaction bonus | Omittable short-term | No agreed multiplier yet |
| Sunset clause | Recommended | Revenue cliff risk must be disclosed |

The most important minimum viable rule: **`EF_market_i = 0` by default unless a specific, accessible buyer market is identified**. This prevents inflating BCR with premium revenue that has no realistic route to monetisation.

**5.2** TCFD/TNFD alignment for premium revenue: TCFD requires disclosure of climate-related risks and opportunities. The premium revenue term is a climate-related opportunity. Should the Technical Note require that DFI-financed projects disclose their ONPV premium revenue forecast alongside their conventional financial projections, using the same scenario analysis structure — ordered, transition scenario, physical scenario — that applies to the cost side?

**5.3** The greenium (15–20 basis points below conventional infrastructure debt pricing) documented in the Pflichtenheft is an observed market outcome, not a formula input. How is the relationship between `BCR_ONPV_full` and the size of the greenium established? Is there a formula — for example, a 1 point increase in `BCR_ONPV_full` maps to X basis points of greenium — or is the greenium set by market conditions independently of the ONPV calculation?

**5.4** The `Liability_Gap` on the cost side is a signal for mandatory insurance. The revenue-side equivalent is the **Premium Gap** — the difference between the societal value of the positive indicator (VF × Physical_Unit_positive) and the premium actually captured by the market (`EF_market_i × CR_i × VF × Physical_Unit_positive`). The Premium Gap represents positive societal value that is being generated but not financially rewarded. Should the Technical Note recommend that this gap be reported — as a parallel to the Liability Gap — to make the case for market development, public payment schemes, or blended finance mechanisms that would close it?

**5.5** The Executive Brief for the premium revenue side needs to communicate one central insight that is the positive mirror of the insolvency cap insight. Proposed message: *"A product that addresses a resource in overshoot is worth more than its conventional price suggests — but only if the market to capture that value exists and the delivery is verified. The gap between what a product is worth to society and what the market currently pays for it is the measure of how much public investment in market development is still required to make the sustainability transition commercially self-sustaining."* Is this the right message for each audience:

| Audience | Message emphasis |
|---|---|
| DFI board | The premium gap justifies continued concessional finance until markets mature |
| Project sponsor | Invest in certification now; the premium market is coming and first movers capture the highest prices |
| Government / finance ministry | Public payment for ecosystem services closes the premium gap where markets cannot yet reach |
| Carbon / biodiversity market participants | The formula provides a consistent method to price the premium across indicators and jurisdictions |

**5.6** Governance: the premium pricing framework requires two things the liability framework does not — ongoing market price feeds (`EF_market_i` updates) and ongoing certification standard recognition (`CR_i` updates). Who maintains these? Proposed governance:
- `EF_market_i`: maintained by the Transitionvaluation working group, updated annually, sourced from observable market data (carbon price indices, green bond issuance data, procurement premium studies)
- `CR_i`: maintained by VBA in partnership with recognised standard bodies (Gold Standard, Verra, AWS, TNFD), updated when new standards achieve critical mass

Is this governance structure agreed, and what is the process for adding new markets or new certification schemes as they emerge?

---

## Cross-Cutting Questions

The following questions do not belong to a single session but must be resolved for the premium pricing framework to function alongside the liability framework.

**X.1 — Netting:** Should cost-side ONPV impact and revenue-side ONPV premium be netted into a single figure, or reported separately? A project that causes GHG damage worth €50M but sequesters carbon worth €30M has a net negative of €20M. A project that causes water damage worth €10M but restores biodiversity worth €40M has a net positive of €30M. The net figure is simpler to communicate but hides the gross flows that regulators, insurers, and litigation analysts need. Recommended position: report gross and net, consistent with double materiality.

**X.2 — Temporal mismatch:** The liability on the cost side is partially retrospective (`Q_historical`). The premium on the revenue side is partially forward-looking (future delivery of sequestration, restoration). Within a single project ONPV, historical liabilities and future premiums appear in the same discounted cash flow. Is the discount rate the same for both, or should future premium revenue be discounted at a higher rate to reflect delivery and market risk?

**X.3 — The perverse incentive:** A company that is currently an overshoot contributor has a financial incentive to remain in overshoot — because the premium market pays more when the resource is scarcer, and transition away from dependency would reduce the premium available to competitors who provide the positive. This is the mirror of the perverse incentive on the cost side (staying small to limit IV). How does the framework prevent a market dynamic where overshoot contributors delay transition to keep scarcity premiums elevated for adjacent premium markets?

**X.4 — Double counting with voluntary carbon / biodiversity markets:** If a project already sells carbon credits through Verra VCS and receives the market price, and the ONPV formula also includes the premium via `VF × f_scarcity × EF_market × CR`, is the same physical unit being counted twice? The formula must have an explicit rule: premium revenue that has already been monetised through a recognised market transaction is removed from the ONPV formula to avoid double counting. Only the **gap** between the market price received and the full societal value (VF × f_scarcity) remains in the ONPV as an unmonetised positive impact.

---

## Sources

- Wackernagel, M., Hanscom, L., Jayasinghe, P. et al. (2021). "The importance of resource security for poverty eradication." *Nature Sustainability* 4, 731–738. https://doi.org/10.1038/s41893-021-00708-4
- Wetzer, T., Stuart-Smith, R. & Dibley, A. (2024). "Climate risk assessments must engage with the law." *Science* 383(6679), 152–154. DOI: 10.1126/science.adj0598
- Global Footprint Network. *Biocapacity Lens.* https://www.wackernagel.info/post/the-biocapacity-lens
- Greenings / Value Balancing Alliance (2024). *Transitionvaluation Project.* github.com/Greenings/transitionvaluation
- VBA / Pflichtenheft (2025). *Infrastructure Impact Measurement and Valuation Service v1.0*
- GRESB (2025). *Infrastructure Assessment Indicators Summary*
- FAST-Infra (2024). *Sustainable Infrastructure Label v2.0*
- Stockholm Resilience Centre. *Planetary Boundaries Framework.*
- IPBES (2019). *Global Assessment Report on Biodiversity and Ecosystem Services*
- EU Nature Restoration Law (2024). Regulation (EU) 2024/1991
