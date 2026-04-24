# Overview of Development Finance Frameworks — earth02

This document provides a structured overview of all impact measurement and results frameworks stored in this repository. The frameworks span seven multilateral development banks (MDBs), one proprietary ESG service framework, and two cross-institutional standards (FAST-Infra, HIPSO).

---

## Table of Contents

1. [IFC — AIMM (Anticipated Impact Measurement and Monitoring)](#1-ifc--aimm)
2. [ADB — DMF (Design and Monitoring Framework)](#2-adb--dmf)
3. [AIIB — RMF (Results Monitoring Framework)](#3-aiib--rmf)
4. [EBRD — TOMS/TIMS (Transition Impact)](#4-ebrd--tomstims)
5. [IDB — 2024–2030 Impact Framework](#5-idb--20242030-impact-framework)
6. [IsDB — Realigned Strategy 2023–2025](#6-isdb--realigned-strategy-20232025)
7. [NDB — General Strategy 2022–2026](#7-ndb--general-strategy-20222026)
8. [Lastenheft_Infra — ESG Service Framework](#8-lastenheft_infra--esg-service-framework)
9. [FAST-Infra — Sustainable Infrastructure Label](#9-fast-infra--sustainable-infrastructure-label)
10. [HIPSO — Harmonized Indicators for Private Sector Operations](#10-hipso--harmonized-indicators-for-private-sector-operations)
11. [Cross-Framework Comparison](#11-cross-framework-comparison)

---

## 1. IFC — AIMM

**Folder:** `aimm_framework_complete/`
**Institution:** International Finance Corporation (World Bank Group)
**Scope:** Global private sector investments

### Core Logic

AIMM measures additionality and development impact for IFC's private sector operations. Every project is scored on two components:

```
Total AIMM Score = (Project Outcome Score × Likelihood) + (Market Creation Score × Likelihood)
```

Scores range 0–100 with four final ratings: **Excellent** (86–100), **Good** (51–85), **Satisfactory** (31–50), **Low** (0–30).

The "Potential" rating (Very Strong / Strong / Moderate / Minimal) is derived from a **Gap × Intensity matrix**, where:
- **Gap** = development need in the country/sector (Low → Very Large)
- **Intensity** = how much the project addresses that need (Below Average → Significantly Above Average)

A **likelihood multiplier** (High=0.90, Medium=0.75, Low=0.60) then adjusts for delivery risk.

### Sector-Specific Framework Briefs (SFBs)

AIMM's most distinctive feature: each sector has a tailored framework brief defining gap indicators and impact benchmarks.

| Sector | Document |
|---|---|
| Agribusiness | `aimm-sfb-agribusiness-consultation.md` |
| Capital Markets | `aimm-sfb-capital-markets.md` |
| DARP (Distressed Asset Recovery) | `aimm-sfb-darp-consultation.md` |
| Education | `aimm-sfb-education-consultation.md` |
| Health | `aimm-sector-framework-brief-health.md` |
| Housing | `aimm-sfb-housing-consultation.md` |
| Insurance & Pension Funds | `aimm-sfb-insurance-pf-consultation.md` |
| Manufacturing | `aimm-sfb-manufacturing-consultation.md` |
| Mining | `aimm-mining-consultation.md` |
| Oil & Gas | `aimm-oil-and-gas-consultation.pdf` |
| Ports | `aimm-sfb-ports.md` |
| Power | `aimm-power-consultation.pdf` |
| Private Equity Funds | `aimm-sfb-private-equity-funds-consultation.md` |
| Retail | `aimm-sfb-retail-consultation.pdf` |
| Roads | `aimm-sfb-roads.md` |
| SME Finance | `aimm-sme-consultation.md` |
| TMT (Tech, Media, Telecom) | `aimm-sfb-tmt.md` |
| Tourism | `aimm-sfb-tourism-consultation.md` |
| Transportation | `aimm-sfb-transportation-consultation.pdf` |
| Venture Capital & Direct | `aimm-sfb-vc-direct-consultation.md` |
| Water & Wastewater | `aimm-sfb-water-waste-water-consultation.pdf` |
| Advisory Services | `aimm-advisory-services-consultation.pdf` |

**Special Guidance:** Carbon pricing integration is covered separately in `carbon-pricing-guidance-note.pdf`.

**Inclusion Bonus:** Projects targeting underserved populations (women, low-income, rural, refugees) can receive an upward intensity rating adjustment.

### Key Source Documents
- `AIMM-General-Guidance-Note-Project-Assessment-and-Scoring-Guidance-Note.pdf` — foundational methodology
- `AIMM_Scoring_System_Overview.md` — scoring logic summary
- `AIMM_Indicators_Overview.md` — cross-sector indicator catalogue

---

## 2. ADB — DMF

**Folder:** `adb_framework_complete/`
**Institution:** Asian Development Bank
**Scope:** Asia-Pacific sovereign and non-sovereign operations

### Core Logic

The **Design and Monitoring Framework (DMF)** is ADB's primary tool for project design, implementation, and evaluation. It tracks a logic chain: **Inputs → Activities → Outputs → Outcomes → Impact**, aligned with **Strategy 2030**.

**Seven Operational Priorities (Strategy 2030):**
1. Addressing remaining poverty and reducing inequalities
2. Accelerating progress in gender equality
3. Tackling climate change and disaster resilience
4. Making cities more livable
5. Promoting rural development and food security
6. Strengthening governance and institutional capacity
7. Fostering regional cooperation and integration

**Scoring:** 4-point ex-post rating scale using OECD-DAC criteria (Relevance, Coherence, Effectiveness, Efficiency, Impact, Sustainability).

**Gender requirement:** A mandated percentage of projects must include gender-responsive outcomes.

### Key Source Documents
- `defr-rfw-indicator-definitions-mar2025.pdf` — Results Framework indicator definitions (March 2025)
- `defr-tracking-indicator-definitions-mar2025.pdf` — Tracking indicator definitions (March 2025)
- `ADB_Indicators_Overview.md`, `ADB_Scoring_System_Overview.md`, `Summary_ADB_Framework.md`

---

## 3. AIIB — RMF

**Folder:** `aiib_framework_complete/`
**Institution:** Asian Infrastructure Investment Bank
**Scope:** Global infrastructure (primarily Asia), sovereign and private sector

### Core Logic

AIIB's mission is "Financing Infrastructure for Tomorrow." Its **Results Monitoring Framework (RMF)** uses SMART indicators linked to **Project Development Objectives (PDO)** and **Intermediate Results Indicators (IRI)**.

**Four Thematic Priorities:**
1. **Green Infrastructure** — climate mitigation and adaptation
2. **Connectivity and Regional Cooperation** — cross-border infrastructure
3. **Technology-enabled Infrastructure** — digital transformation
4. **Private Capital Mobilization** — leveraging private investment

**Quality at Entry:** Assessed via the **Project Prioritization and Quality (PPQ)** framework.
**Climate Target:** 50% climate finance by 2025.
**Accountability:** Independent Learning and Evaluation Policy; annual Impact Reports with public disclosure.

### Key Source Documents
- `AIIB-Results-Architecture.pdf` — foundational architecture document
- `aiib-results-architecture.md` — full results architecture
- `aiib-environmental-social-framework.md` — mandatory E&S standards
- `aiib-learning-evaluation-policy.md` — evaluation and accountability
- `aiib-sustainable-development-bonds-impact-report-2024.md` — 2024 impact data
- `AIIB_Corporate_Scorecard_Summary.md` — corporate KPI tracking

---

## 4. EBRD — TOMS/TIMS

**Folder:** `ebrd_framework_complete/`
**Institution:** European Bank for Reconstruction and Development
**Scope:** Emerging Europe, Central Asia, MENA, sub-Saharan Africa

### Core Logic

The EBRD's mandate is fostering transition toward **open, market-oriented economies**. Since 2016, this is operationalized through **Six Transition Qualities** assessed via TOMS (appraisal) and tracked via TIMS (monitoring).

**Six Transition Qualities:**
1. **Competitive** — innovation, efficiency, market entry
2. **Well-governed** — institutions, corporate standards
3. **Green** — low-carbon and environmentally sustainable growth
4. **Inclusive** — women, youth, disadvantaged regions
5. **Resilient** — financial systems and energy security
6. **Integrated** — connectivity and trade links

**ETI Score (0–100)** is calculated at project entry using three pillars:
- **Ambition** — scale and depth of transition objectives, benchmarked vs. the Compendium of Indicators (CoI)
- **Context (Transition Gap)** — country-level ATQ scores adjust the multiplier; higher gap = higher uplift
- **Likelihood** — risk-adjusted delivery probability

**ETI Rating Bands:**
| Score | Rating |
|---|---|
| 80–100 | Exceptional |
| 70–79 | Strong |
| 60–69 | Good |
| 50–59 | Satisfactory |
| <50 | Below threshold |

**Portfolio Transition Impact (PTI)** tracks actual delivery throughout project lifecycle.

**Uplifts/Bonuses:** Green Economy Transition (GET) projects, equity investments, policy dialogue, first-of-a-kind innovations.

**Sectoral Transition Challenges** are documented in `EBRD_Sectoral_Transition_Challenges.md`.

### Key Source Documents
- `ebrd-transition-concept.md` — historical evolution and mandate
- `ebrd-transition-impact.md` — assessment framework overview
- `ebrd-impact-management.md` — internal impact management processes
- `EBRD_ETI_Methodology_Deep_Dive.md` — detailed ETI formula
- `EBRD_Transition_Mission_Framework.md` — country-level "Transition Mission" linkage
- `EBRD_Indicators_Overview.md` — Compendium of Indicators (CoI) by quality

---

## 5. IDB — 2024–2030 Impact Framework

**Folder:** `idb_framework_complete/`
**Institution:** Inter-American Development Bank
**Scope:** Latin America and the Caribbean

### Core Logic

The IDB's **2024–2030 Impact Framework** shifts from output measurement to outcome and impact measurement. Annual results are published in the **Development Effectiveness Overview (DEO)**.

**Three Core Pillars:**
1. **Social Progress** — healthcare, education, social protection
2. **Economic Growth** — innovation, productivity, regional integration
3. **Climate Action** — mitigation and adaptation in LAC

**Scoring:** Ex-ante/ex-post balance, impact-driven results-based lending, standardized indicators.

### Key Source Documents
- `IDB_Indicators_Overview.md` — standardized development effectiveness indicators
- `IDB_Scoring_System_Overview.md` — DEO framework and rating scale
- `Summary_IDB_Framework.md` — strategic synthesis

---

## 6. IsDB — Realigned Strategy 2023–2025

**Folder:** `isdb_framework_complete/`
**Institution:** Islamic Development Bank
**Scope:** 57 Member Countries (OIC), focus on Muslim-majority developing nations

### Core Logic

IsDB's framework is unique in integrating **Islamic finance principles (Shari'ah compliance)** with development impact. All financing must be interest-free and aligned with **Maqasid al-Shari'ah** (objectives of Islamic law: preservation of life, dignity, and sustainable development).

**Three Strategic Objectives (Realigned Strategy 2023–2025):**
1. **Boosting Recovery** — from pandemic and external shocks
2. **Tackling Poverty** — building resilience in vulnerable populations
3. **Driving Green Economic Growth** — sustainable development

**SDG Alignment:** All results are mapped to UN Sustainable Development Goals.
**Performance Assessment:** Shari'ah compliance rating combined with standard project success criteria.

### Key Source Documents
- `IsDB_Indicators_Overview.md` — 10-Year Strategy and SDG-aligned indicators
- `IsDB_Scoring_System_Overview.md` — performance ratings and thematic priorities
- `Summary_IsDB_Framework.md` — mission-driven approach synthesis

---

## 7. NDB — General Strategy 2022–2026

**Folder:** `ndb_framework_complete/`
**Institution:** New Development Bank (BRICS Bank)
**Scope:** BRICS member states and invited emerging economies

### Core Logic

The NDB focuses exclusively on **sustainable infrastructure and private sector development**. Its **General Strategy 2022–2026** centers on transitioning member countries to a sustainable future.

**Five Thematic Priorities:**
1. **Clean Energy and Energy Efficiency**
2. **Transport Infrastructure**
3. **Water, Sanitation and Social Infrastructure**
4. **Digital Infrastructure**
5. **Environmental Protection and Sustainable Development**

**Assessment:** Mandate alignment (sustainable infrastructure focus) + standard project success criteria, all SDG-aligned.

### Key Source Documents
- `NDB-Evaluation-Manual.pdf` — official evaluation methodology
- `NDB_Indicators_Overview.md` — strategy and SDG-aligned indicators
- `NDB_Scoring_System_Overview.md` — project performance ratings
- `Summary_NDB_Framework.md` — strategic synthesis

---

## 8. Lastenheft_Infra — ESG Service Framework

**Folder:** `Lastenheft_Infra/`
**Type:** Proprietary service and compliance framework
**Scope:** Infrastructure project ESG self-assessment and certification

### Core Logic

A three-service ESG assessment and certification framework designed for infrastructure projects, structured around three pillars:

1. **Environmental Monitoring Self-Assessment** (`Service_1_Environmental_Monitoring_Self_Assessment.md`)
2. **Social & Labor Standards Self-Assessment** (`Service_2_Social_Labor_Standards_Self_Assessment.md`)
3. **Governance & Supply Chain Self-Assessment** (`Service_3_Governance_Supply_Chain_Self_Assessment.md`)

Additional components include:
- `Advanced_Checklist_Framework.md` / `.pdf` — detailed compliance checklist
- `Service_Labels_Certificate.md` — certification and labeling criteria
- `Verification_Report_Three_Services.md` — third-party verification methodology
- `Suggested_References.md` — reference standards and sources
- `Lastenheft/` and `Fidic/` subfolders — contractual requirements and FIDIC contract templates

---

## 9. FAST-Infra — Sustainable Infrastructure Label

**Folder:** `fastinfra_framework_complete/`
**Institution:** FAST-Infra (Finance to Accelerate the Sustainable Transition – Infrastructure)
**Scope:** All infrastructure sectors globally; project-level sustainability label

### Core Logic

FAST-Infra uses a universal indicator set covering **4 Dimensions · 14 Criteria · ~220 indicators**. Every indicator carries a permanent alphanumeric ID. Label eligibility requires satisfying **8 Minimum Safeguards** as a prerequisite, meeting all **Baseline Requirements** under all 14 criteria, and demonstrating at least one **Positive Contribution**. Two label types exist: Self-Assessed (valid 24 months) and Verified (valid 36 months with annual surveillance). Time-series indicators use `.A` (historical) and `.B` (forecast) suffixes for longitudinal tracking.

**Four Dimensions:** Environmental (E1–E4) · Adaptation & Resilience (R5) · Social (S6–S10) · Governance (G11–G14)

### Key Source Documents
- `68a44d2347380f7f25d23d24_ST01_V2_05.12.2024.pdf` — ST01 Dimensions, Criteria and Indicators v2.0 (Dec 2024)
- `6966363e6cf7c15024fea040_ST02_Methodology_20.11.2024.pdf` — ST02 Methodology v1.0 (Nov 2024)
- `6966364778f8be6f4bbef979_RQ01_FASTInfraLabel_Verification_Labelling_Requirements_2025.pdf` — RQ01 Verification Requirements v0.2 (2025)
- `67581e70ec0f49f4356a8644_Glossary_V1_05.12.2024.pdf` — Glossary v1.0 (Dec 2024)
- `FAST-Infra_Indicator_Overview.md` — full indicator catalogue with sub-indicators

---

## 10. HIPSO — Harmonized Indicators for Private Sector Operations

**Folder:** `HIPSO_framework_completed/`
**Institution:** IFI Partnership (IFC, EBRD, AfDB, ADB, IDB, EIB, IsDB and others)
**Scope:** Private sector investment operations across all sectors

### Core Logic

HIPSO is a joint initiative of major DFIs to define a common set of output and outcome indicators for private sector operations. Unlike MDB-specific scoring systems, HIPSO defines **what** to measure — not how to score it. All indicators carry standardized IDs and are mapped to UN SDG targets. Institutions report against the same definitions, enabling cross-portfolio comparison.

**Coverage:** 14 sectors (Energy, Agribusiness, Education, Health, Housing, Industry & Services, ICT, Mining, Oil/Gas, PE & Investment Funds, PSD Firm/Market Level, Transportation, Water/Waste/Sanitation, Financial Intermediation) + cross-cutting infrastructure + 4 thematic categories (Gender, Jobs, Environment, Community)

**Total indicators:** ~177

### Key Source Documents
- `Energy.md`, `Agribusiness.md`, `Health.md`, `Education.md`, etc. — sector-specific indicator definition sheets
- `HIPSO Mapping.pdf` / `HIPSO Mapping.md` — SDG alignment for all indicators
- `Cross-Cutting_All_Infrastructure_Services_Sub-Sectors.md` — CC-01/02 meters and jobs
- `THEMATIC_AREA.md` — TA-01 through TA-19 (Gender, Jobs, Environment, Community)

---

## 11. Cross-Framework Comparison

| Feature | IFC/AIMM | ADB/DMF | AIIB/RMF | EBRD/TOMS | IDB | IsDB | NDB | FAST-Infra | HIPSO |
|---|---|---|---|---|---|---|---|---|---|
| **Primary Focus** | Additionality & private sector impact | Poverty reduction (Asia-Pacific) | Sustainable infrastructure | Market transition | Regional development (LAC) | Islamic finance + development | BRICS sustainable infra | Infrastructure sustainability label | Harmonized output/outcome definitions for PS ops |
| **Scoring Scale** | 0–100 (weighted) | 4-point ex-post | PPQ (strategic/design) | ETI 0–100 | Ex-ante/ex-post | SDG/Shari'ah compliance | Mandate alignment | Baseline + Positive Contribution; no aggregate score | No scoring — common definitions only |
| **Sector Specificity** | Very high (20+ SFBs) | Moderate (7 priorities) | Moderate (4 themes) | High (6 qualities × sectors) | Moderate (3 pillars) | Moderate (3 objectives) | High (5 themes) | Universal (all infra); 14 criteria | Very high (14 sectors + thematic; ~177 indicators) |
| **Climate Target** | 40% by 2030 | Integrated in Strategy 2030 | 50% by 2025 | GET program | Core pillar | Green Growth pillar | Core priority | E2 (mitigation) + R5 (adaptation) criteria | TA-11/12 GHG; EN-02 renewable |
| **Private Sector** | Primary focus | Partial | Explicit priority | Core mandate | Partial | Partial | Explicit | All infrastructure projects | Primary focus (PS operations only) |
| **Geographic Focus** | Global | Asia-Pacific | Global (Asia focus) | Europe/MENA/CA | Latin America | OIC member states | BRICS + emerging | Global | Global |
| **Unique Feature** | Gap × Intensity matrix; 20+ SFBs | DMF logic chain | PPQ quality at entry | Transition Gap multiplier; ATQ scores | DEO annual reporting | Shari'ah compliance layer | BRICS-focused mandate | Permanent alphanumeric IDs; NbS qualifying element; 8 MS gate | Cross-MDB harmonization; SDG-mapped; institution-agnostic |

### Methodological Similarities

All frameworks share:
- **Theory of Change logic:** Inputs → Outputs → Outcomes → Impact
- **Ex-ante scoring** with ex-post verification
- **SDG alignment** as a common reference
- **Likelihood/risk adjustment** on projected outcomes
- **Annual public reporting** on portfolio performance

### Key Differentiators

- **AIMM** is the most sector-granular, with 20+ tailored SFBs and an explicit gap-intensity matrix
- **EBRD** uniquely adjusts scores by country-level transition gap (ATQ), incentivizing operations in frontier markets
- **IsDB** is the only framework integrating a religious/ethical compliance layer (Shari'ah)
- **ADB** has the most explicit gender mainstreaming mandate
- **AIIB** has the most aggressive near-term climate finance target (50% by 2025)
- **NDB** is the only framework exclusively focused on BRICS/emerging economies without a regional development bank mandate
- **FAST-Infra** is the only framework using permanent alphanumeric indicator IDs with explicit time-series tracking and an 8-indicator Minimum Safeguards gate; NbS can qualify as a Positive Contribution across all non-governance criteria
- **HIPSO** is the only cross-institutional standard without a scoring model — it functions as a shared measurement vocabulary, enabling direct portfolio-level comparison across MDBs; it is the common backbone referenced by EBRD, IFC, AfDB, ADB, IDB, EIB, and IsDB for private sector reporting

---

*Last updated: March 2026*
*Sources: documents in respective subfolders. See each folder's `README.md` for detailed file index.*
