# EBRD Assessment of Transition Qualities (ATQ) — Methodology Note

**Source:** EBRD Transition Report 2024-25, Chapter 5 (Structural Reform) and Methodological Notes  
**Data vintage:** 2024-25 scores; coverage spans 42 economies across 6 EBRD regions

---

## 1. Purpose

The ATQ framework measures how far EBRD economies have progressed toward the standards of a **sustainable market economy**. Scores are published annually in the EBRD Transition Report and serve as the primary structural reform benchmarking tool across the Bank's operations.

---

## 2. The Six Transition Qualities

Each economy is scored on six dimensions, each capturing a distinct aspect of market economy performance:

| Dimension | What it measures |
|---|---|
| **Competitive** | Openness of markets, SME development, innovation capacity, trade barriers |
| **Well Governed** | Rule of law, regulatory quality, anti-corruption, press freedom, corporate governance |
| **Green** | Greenhouse gas mitigation, renewable energy transition, climate adaptation, biodiversity |
| **Inclusive** | Labour market participation, gender equity, financial access, human capital, social protection |
| **Resilient** | Financial sector stability, energy sector liberalisation, macroeconomic shock absorption |
| **Integrated** | Trade and FDI openness, transport and digital infrastructure, logistics performance |

---

## 3. Data Sources

ATQ scores draw on a wide range of external and internal sources:

| Source | Examples of use |
|---|---|
| **World Bank** | WDI, Global Financial Development Database, Findex |
| **IMF** | Government Finance Statistics, Financial Soundness Indicators, Article IV reports |
| **UN agencies** | UNDESA (demographics), FAO (land use), UNODC (rule of law) |
| **WEF** | Global Competitiveness Index (innovation, infrastructure) |
| **Transparency International** | Corruption Perceptions Index |
| **OECD** | Education, health, and product market databases |
| **EBRD internal** | BEEPS (Business Environment and Enterprise Performance Survey), LiTS (Life in Transition Survey), country economist assessments |
| **National statistics** | Labour, energy, and financial data where no international equivalent exists |

---

## 4. Construction Steps

### Step 1 — Data Preparation
- Latest available observation used for each indicator.
- Gaps are imputed using the most recent prior observation or a regional mean.
- Outliers above the 98th percentile are replaced with the upper acceptable range value.

### Step 2 — Normalisation
Each raw indicator is rescaled to a **1–10 range** using **min-max normalisation**:

```
Normalised score = 1 + 9 × (value − min) / (frontier − min)
```

- The **frontier** (= 10) is set at the best observed performance across a peer group of advanced economies (Canada, Japan, Sweden, United States, and others).
- The **floor** (= 1) is set at the worst observed value globally.
- The same frontier values are fixed across years to enable **consistent time-series comparisons**.

### Step 3 — Aggregation
- Normalised indicators are aggregated into sub-components using **expert-determined weights**.
- Sub-components are then combined into a single composite score per dimension via **weighted averaging**.
- Internal EBRD weights reflect the relative importance of each sub-component to overall transition quality (e.g., Well Governed: 75% national governance / 25% corporate governance).

---

## 5. Scoring Scale

| Score | Interpretation |
|---|---|
| 10 | Frontier — matches best-practice advanced economy standard |
| 7–9 | Strong performer; minor gaps relative to frontier |
| 5–6 | Moderate performer; significant reform gaps remain |
| 3–4 | Weak performer; structural reform needs are substantial |
| 1–2 | Very weak; well below sustainable market economy standards |

---

## 6. Geographic Coverage (2024-25 Report)

| Region | Code | Economies |
|---|---|---|
| Central Europe and the Baltic States | CEB | Croatia, Czechia, Estonia, Hungary, Latvia, Lithuania, Poland, Slovak Republic, Slovenia |
| South-Eastern Europe | SEE | Albania, Bosnia and Herzegovina, Bulgaria, Greece, Kosovo, Montenegro, North Macedonia, Romania, Serbia, Türkiye |
| Eastern Europe and the Caucasus | EEC | Armenia, Azerbaijan, Georgia, Moldova, Ukraine |
| Central Asia | CA | Kazakhstan, Kyrgyz Republic, Mongolia, Tajikistan, Turkmenistan, Uzbekistan |
| Southern and Eastern Mediterranean | SEMED | Egypt, Jordan, Lebanon, Morocco, Tunisia, West Bank and Gaza |
| Sub-Saharan Africa (Comparators) | SSA | Benin, Côte d'Ivoire, Ghana, Kenya, Nigeria, Senegal |

> **Note:** The 2025-26 Transition Report extended coverage to **Iraq** (new investee economy) and added **Algeria** and **Libya** as comparators.

---

## 7. Limitations

- **Data lags:** Several underlying indicators are published with a 1–2 year delay, meaning ATQ scores reflect conditions from the prior year in some dimensions.
- **Expert judgement:** Weights are set by EBRD economists and are not derived algorithmically; they may reflect institutional priorities.
- **Comparator dependency:** The frontier is benchmarked against a fixed set of advanced economies; shifts in frontier performance can affect scores independently of domestic reform progress.
- **Conflict-affected economies:** Scores for Ukraine and West Bank and Gaza are constrained by data availability during active conflict.

---

## 8. Key References

- EBRD Transition Report 2024-25 — Chapter 5: Structural Reform  
  https://2024.tr-ebrd.com/structural-reform/
- EBRD Methodological Notes 2024-25  
  https://www.ebrd.com/content/dam/ebrd_dxp/assets/pdfs/office-of-the-chief-economist/transition-report-archive/transition-report-2024/chapters/Transition-Report-2024-25-Methodological-Notes.pdf
- EBRD Assessment of Transition Qualities (overview page)  
  https://www.ebrd.com/economic-research-and-data/transition-qualities-asses.html
- EBRD Transition Report 2025-26  
  https://www.ebrd.com/home/news-and-events/publications/economics/transition-reports/transition-report-2025-26.html
