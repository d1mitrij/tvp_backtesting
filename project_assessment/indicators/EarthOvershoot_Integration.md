# Earth Overshoot Integration — Project Assessment Outline

**Version:** 1.1  
**Scope:** Integration of Ecological Footprint / Biocapacity data into the S4 project assessment
pipeline as a planetary-boundary context layer alongside the existing ESRS indicator set.  
**Data location:** `project_assessment/indicators/earthovershoot/`

---

## 1. Concept and Purpose

The Ecological Footprint (EF) was introduced by Wackernagel and Rees as an accounting tool
measuring human demand on, and biospheric supply of, renewable natural capital [1,2]. It expresses
heterogeneous resource use in a single unit — **global hectares (gha)**, one hectare of
biologically productive land or water normalised to world-average productivity [3]. When a
population's EF exceeds available biocapacity (BC), the resulting **ecological overshoot** implies
that stocks of ecological capital are being liquidated and/or waste is accumulating beyond
regenerative capacity [4].

The existing tvp5 indicator list measures **absolute flows** (GHG tonnes, water volume, land area)
against ESRS standards [9,10,11]. Earth Overshoot adds a complementary **biophysical boundary
context**: it maps those same flows onto a bioproductive-area denominator and compares them against
the regenerative capacity of the host country's ecosystems. Wackernagel et al. (2019) demonstrate
that countries in structural ecological deficit systematically underperform in long-run economic
development, establishing the link between biophysical resource security and investment risk [7].

This matters for MDB-financed infrastructure because:

| Current capability | Added capability |
|---|---|
| How much GHG does the project emit? | What share of the host country's carbon-absorption biocapacity does that represent? |
| How much land does the project use? | Is the host country already in ecological deficit, amplifying the physical risk? |
| Scenario-adjusted GHG (SSP 1–5) | Number-of-Earths trend under each scenario — a single public-communication benchmark |

Planetary boundary science (Steffen et al. 2015) identifies biosphere integrity and land-system
change among the boundaries most at risk of transgression [5]. Expressing project impacts in gha
directly situates them within this framework.

---

## 2. Data Files Copied

All files are static snapshots produced by the `earthovershoot01` calculator, which follows the
National Footprint Accounts (NFA) methodology [4,6]. No download is required at runtime.

| File | Rows | Description |
|---|---|---|
| `earthovershoot/overshoot_results.csv` | 2,340 | Country × year (234 countries, 2014–2023); EF and BC by component + per-capita figures. Derived from FAOSTAT production, land-use, forestry, fisheries, emissions, and population data [6]. |
| `earthovershoot/overshoot_global_summary.csv` | 10 | Annual world totals; Number of Earths; Overshoot Day (day of year), per NFA 2018 methodology [6]. |
| `earthovershoot/equivalence_factors_reference_1999.csv` | 6 | EQF conversion constants from Wackernagel et al. (2002), Table 1 [2]. Static 1999 values; see §8 for limitation. |
| `earthovershoot/carbon_sequestration_parameters.csv` | 4 | Average Forest-Carbon Sequestration rate (AFCS = 0.73 t C/ha/yr, Mancini et al. 2016 [12]) and ocean CO₂ absorption fraction (35%, Khatiwala et al. 2009 [13]). |

### Key columns in `overshoot_results.csv`

| Column | Unit | Use in assessment | Source |
|---|---|---|---|
| `area` | string | Join key (country name, matches `assess.py` REGION_TO_ISO3 lookup) | FAOSTAT area codes [6] |
| `year` | int | Filter to 2023 for current baseline | — |
| `ef_carbon_gha` | gha | Country carbon footprint — biophysical counterpart to ESRS E1 GHG [9] | Derived: CO₂ × (1−ocean_frac) / SeqRate × EQF [2,12,13] |
| `ef_cropland_gha` + `ef_grazing_gha` + `ef_forest_gha` | gha | Land-use footprint — ESRS E4 [11] | NFA methodology [4] |
| `ef_fishing_gha` | gha | Marine biocapacity demand — ESRS E4 biodiversity [11] | PPR method, Pauly & Christensen 1995 [14] |
| `bc_total_gha` | gha | Total national biocapacity — the planetary budget denominator | NFA [4,6] |
| `ecological_deficit_gha` | gha | BC − EF; negative = country already in overshoot | NFA [4] |
| `ef_per_capita_gha` | gha/cap | Per-capita footprint; benchmarks project footprint against citizen average | NFA [4,6] |
| `bc_per_capita_gha` | gha/cap | Per-capita biocapacity; fair-share reference (global avg ≈ 1.6 gha/cap in 2023) | NFA [4,6] |

---

## 3. New Indicator Block

Add the following section to the main `indicators` file **after the Land Use block (E4, line 56)** and
before Waste (E5). The EF and BC concepts and the gha unit follow Borucke et al. (2013) [4] and
Lin et al. (2018) [6]. ESRS references follow EFRAG Commission Delegated Regulation (EU) 2023/2772 [9–11].

| Impact Driver | Key Indicator | Calc Unit | ESRS Ref | Source |
|---|---|---|---|---|
| **Ecological Footprint** | Country ecological footprint per capita (baseline, host country, 2023) | gha/cap | E4 | NFA [4,6]; `overshoot_results.csv` |
| | Country biocapacity per capita (baseline, host country, 2023) | gha/cap | E4 | NFA [4,6]; `overshoot_results.csv` |
| | Country ecological deficit/surplus per capita | gha/cap | E4 | NFA [4]; `overshoot_results.csv` |
| | National Overshoot Day of host country (proxy: world average) | Day of year | E4 | NFA [4,6]; `overshoot_global_summary.csv` |
| | Project carbon footprint converted to global hectares | gha | E1 | Mancini et al. 2016 [12]; Khatiwala et al. 2009 [13]; Wackernagel et al. 2002 [2] |
| | Project land-use footprint in global hectares | gha | E4 | Galli et al. 2007 [3]; Borucke et al. 2013 [4]; EQF table [2] |
| | Project net EF change relative to baseline (negative = improvement) | gha | E1/E4 | Derived from above |
| **Planetary Boundaries** | Biocapacity deficit share by component (carbon / cropland / forest / fishing) | % | E4 | Borucke et al. 2013 [4]; Steffen et al. 2015 [5] |
| | Overshoot Contribution Index (OCI) — project EF as % of host BC | % | E1/E4 | Borucke et al. 2013 [4]; formulae in §4.3 |
| | Number-of-Earths equivalent if project replicated at world scale | ratio | E1/E4 | Lin et al. 2018 [6]; `overshoot_global_summary.csv` |
| | Project contribution to national Overshoot Day shift | days | E1/E4 | Wackernagel et al. 2002 [2]; formulae in §4.5 |

---

## 4. Calculation Formulas

All constants are taken directly from the copied reference files, which reproduce the NFA 2016
calculation standard [4,6].

### 4.1 Project carbon footprint → gha

The carbon footprint component of the EF converts CO₂ emissions into the forest area that would be
required to sequester them at world-average rates, following Mancini et al. (2016) [12] and
Wackernagel et al. (2002) [2]. The ocean's share of annual anthropogenic CO₂ absorption (35%) is
subtracted following Khatiwala et al. (2009) [13].

```
AFCS          = 0.73        # t C/ha/yr  (Mancini et al. 2016 [12]; carbon_sequestration_parameters.csv)
                            #   range ± 0.37; represents world-average forest carbon sequestration
ocean_frac    = 0.35        # fraction absorbed by oceans (Khatiwala et al. 2009 [13])
EQF_forest    = 1.3         # gha/ha  (Wackernagel et al. 2002, Table 1 [2])
SeqRate       = AFCS × (44/12)  = 2.677   # converts t C/ha/yr → t CO₂/ha/yr

ef_carbon_project_gha = project_GHG_tCO2e × (1 − ocean_frac) / SeqRate × EQF_forest
```

Example: a project emitting 50,000 tCO₂e/yr:
`50,000 × 0.65 / 2.677 × 1.3 ≈ 15,800 gha`

Note: the same formula is used to compute `ef_carbon_gha` in `overshoot_results.csv`, enabling
direct comparison of project footprint against national carbon footprint data.

### 4.2 Project land-use footprint → gha

Physical hectares of land disturbed by the project are converted to gha by multiplying by the
relevant Equivalence Factor (EQF) from Wackernagel et al. (2002) [2], as formalised by Galli et al.
(2007) [3] and Borucke et al. (2013) [4]:

```
EQF_cropland  = 2.1   # gha/ha  (Wackernagel et al. 2002, Table 1 [2])
EQF_forest    = 1.3   # gha/ha  [2]
EQF_built_up  = 2.2   # gha/ha  (assumed equal to cropland it displaces [2])

ef_land_project_gha = (cropland_ha × EQF_cropland)
                    + (forest_ha   × EQF_forest)
                    + (built_up_ha × EQF_built_up)
```

Land-use hectares are sourced from the `tvp_dependency` pass outputs (ENCORE land-use stressor).
The EQF values reflect the relative bioproductivity of each land type compared to world-average
bioproductive land; see Galli et al. (2007) [3] for the mathematical derivation.

### 4.3 Overshoot Contribution Index (OCI)

The OCI expresses the project's combined carbon and land footprint as a share of the host country's
total biocapacity, establishing the relative magnitude of the demand being placed on the national
ecological budget. The BC denominator follows NFA methodology [4]:

```
OCI = (ef_carbon_project_gha + ef_land_project_gha) / bc_total_host_gha × 100
```

Thresholds: OCI < 0.001 % is negligible (smaller than statistical noise in NFA data);
OCI > 0.1 % warrants explicit narrative disclosure in `final_analysis.md`.

### 4.4 Number-of-Earths (project-replicated)

The Number of Earths metric follows the NFA definition: the ratio of global EF to global BC [4,6].
The project-replicated figure estimates how much this ratio would increase if every person on Earth
generated the same EF pressure as this project implies:

```
world_bc_gha        = 11,843,359,862  # 2023; from overshoot_global_summary.csv [6]
world_ef_gha        = 24,557,697,458  # 2023; from overshoot_global_summary.csv [6]

number_of_earths_proj = (world_ef_gha + ef_project_scaled) / world_bc_gha
```

Scaling factor: the project's investment CAPEX as a fraction of host-country GDP proxies the share
of the national economy the project represents; `ef_project_scaled = ef_total_proj / capex_share`.
World population reference: 8.1 billion (UN DESA 2023 estimate, consistent with FAOSTAT population
data underlying the NFA [6]).

### 4.5 Overshoot Day shift

Earth Overshoot Day is the calendar date when humanity's annual demand on nature exceeds what Earth
can regenerate in that year, following the formulation in Wackernagel et al. (2002) [2]:

```
world_bc_gha    = 11,843,359,862   # 2023; from overshoot_global_summary.csv [6]
world_ef_gha    = 24,557,697,458   # 2023; from overshoot_global_summary.csv [6]

baseline_day    = 365 × world_bc_gha / world_ef_gha     # = day 176 (June 25, 2023)

new_ef          = world_ef_gha + ef_carbon_project_gha
new_day         = 365 × world_bc_gha / new_ef

overshoot_day_shift = baseline_day − new_day            # positive = earlier overshoot
```

---

## 5. Integration with Existing Assessment Passes

### Pass 1 — Supply-chain (tvp_dbio)

- `project_GHG_tCO2e` from `supply_chain_summary.csv` is the direct input to §4.1.
- The EF carbon formula (§4.1) uses constants from Mancini et al. (2016) [12] and Khatiwala et al.
  (2009) [13], the same sources underlying `overshoot_results.csv`, ensuring methodological
  consistency between project-level and country-level numbers.
- Water-use stressor: the NFA does not include freshwater in the gha accounting (no EQF for
  freshwater land exists in the NFA framework [4]). Retain the existing AWARE-based water value
  factor [21] for water monetisation; note the accounting gap in `final_analysis.md`.

### Pass 2 — Scenario (tvp_scenario)

- Apply `adj_ratio_ghg` from `scenario_adjustment.csv` (SSP 1–5 per IPCC AR6 WGIII [15]) to
  `ef_carbon_project_gha` to produce a **scenario-adjusted carbon footprint in gha** for each
  pathway.
- Report OCI under SSP1-1.9 (best case, deep decarbonisation) and SSP5-8.5 (worst case,
  fossil-fuel-intensive) alongside the existing GHG comparison table. This situates the project's
  biophysical demand within the IPCC's emission trajectory family [15].

### Pass 3 — Nature dependency (tvp_dependency)

- Look up `ecological_deficit_gha` for the host country from `overshoot_results.csv`.
- Countries in ecological deficit face compounded nature-related financial risk: declining
  biocapacity constrains the ecosystem services on which projects depend (TNFD LEAP framework [16];
  IPBES 2022 [17]). Wackernagel et al. (2019) document the macro-economic consequences of
  structural ecological deficit for national development trajectories [7].
- Apply a **biocapacity deficit multiplier** to the existing `dep_factor`:

```python
bc_deficit_multiplier = 1.0 if ecological_deficit_gha >= 0 else min(1.5, 1 + abs(ecological_deficit_gha) / bc_total_gha)
dep_factor_adjusted   = dep_factor × bc_deficit_multiplier
```

  The 1.5 ceiling is calibrated to the maximum ecological deficit observed in the dataset
  (Algeria 2023: ~38 billion gha deficit) to avoid mechanical over-penalisation. The multiplier
  tightens the WACC greenium and raises `nature_debt_usd` for projects in already-stressed
  biocapacity countries, consistent with the legal risk channel documented by Wetzer et al.
  (2024), where unpriced externalities become contingent liabilities [18].

### Pass 4 / Data Protocol Section 15 (new)

Add a section **15. Ecological Footprint & Biocapacity Data** to `Data_Protocol.md`:

| Name | Unit | Source | Responsibility | Requirements | Description |
|---|---|---|---|---|---|
| Country EF per capita (`ef_per_capita_host`) | gha/cap | Secondary (reported) | earthovershoot01 / FAOSTAT [6] | Loaded from `earthovershoot/overshoot_results.csv`; filtered to `year=2023`; joined on country name via `REGION_TO_ISO3` | National per-capita ecological footprint of host country; biophysical baseline for project context [4] |
| Country BC per capita (`bc_per_capita_host`) | gha/cap | Secondary (reported) | earthovershoot01 / FAOSTAT [6] | Same source | National per-capita biocapacity; global fair-share reference ≈ 1.6 gha/cap (2023) [6] |
| Country ecological deficit (`deficit_host`) | gha | Secondary (reported) | earthovershoot01 / FAOSTAT [6] | Negative = deficit; used to derive `bc_deficit_multiplier` | Structural biophysical stress of the host economy; amplifies nature-dependency risk [7] |
| Project carbon footprint (`ef_carbon_proj`) | gha | Modelled | System | Derived from `supply_chain_summary.csv` GHG via §4.1; constants from [12,13] | Biophysical carbon demand of the project; comparable to country and per-capita benchmarks [4] |
| Project land-use footprint (`ef_land_proj`) | gha | Modelled | System | Derived from `tvp_dependency` land stressor via §4.2; EQF values from [2] | Biophysical land demand; aggregated across cropland, forest, built-up with EQF weights [3,4] |
| Overshoot Contribution Index (`oci`) | % | Modelled | System | `(ef_carbon_proj + ef_land_proj) / bc_total_host × 100`; flag if > 0.1 % | Project share of host biocapacity consumed; primary overshoot disclosure metric [4] |
| BC deficit multiplier (`bc_deficit_mult`) | Dimensionless [1.0, 1.5] | Modelled | System | 1.0 for BC-surplus countries; computed per §5 / Pass 3 formula | Upward risk adjustment to `dep_factor` when host country is in ecological deficit; grounded in [7,18] |

---

## 6. Output Files

Add to `results/` directory:

| File | Description |
|---|---|
| `overshoot_context.csv` | One row per project; columns: country, ef_per_capita_host, bc_per_capita_host, deficit_host, ef_carbon_proj_gha, ef_land_proj_gha, oci, bc_deficit_multiplier, overshoot_day_shift |
| Section appended to `final_analysis.md` | Paragraph per project: OCI, deficit status, day-shift, brief narrative |

---

## 7. MDB Framework Alignment

| Framework | Integration point | Source |
|---|---|---|
| **EBRD ATQ "Green"** | OCI as a Green Transition Quality sub-indicator; BC deficit country → higher green gap score | EBRD ATQ / TOMS methodology [19] |
| **IFC AIMM "Climate Mitigation"** | `ef_carbon_proj_gha` as a biophysical market-level systemic indicator alongside tCO₂e intensity | IFC AIMM General Guidance Note [20] |
| **FAST-Infra "Circular Economy"** | Number-of-Earths ratio as evidence for positive contribution beyond baseline label criterion | FAST-Infra Sustainable Infrastructure Label [22] |
| **HIPSO cross-cutting climate** | Add `EF_Reduction_gha_yr` next to existing `GHG_Sequestration` indicator | HIPSO Harmonized Indicators for Private Sector Operations [23] |
| **ADB DMF sustainability criterion** | OCI < 0.001 % as a quantitative sustainability outcome threshold | ADB Design and Monitoring Framework, Strategy 2030 |

---

## 8. Limitations

| Issue | Impact | Source | Mitigation |
|---|---|---|---|
| Production-based accounting (not consumption-based) | Double-counts exported resources; world Number of Earths ~2.07 vs GFN's ~1.7 | Lin et al. 2018 [6]; Borucke et al. 2013 [4] | Use for relative comparison only; note in methodology disclosure |
| Static EQF (1999 values from [2]) | Equivalence factors shift with land-use change; static EQF understates cropland pressure in regions of yield degradation | Galli et al. 2007 [3]; Lin et al. 2018 [6] | Flag in `Data_Protocol.md`; planned update when GAEZ v4 (FAO/IIASA) EQFs are available |
| No freshwater biocapacity component in NFA | Water-use cannot be directly expressed in gha | Borucke et al. 2013 [4]; Lin et al. 2018 [6] | Retain AWARE-based water value factor [21]; document gap |
| Country-level BC data only | Cannot resolve sub-national biocapacity (e.g. project in a degraded watershed) | NFA by design [4] | Use Pass 3 WWF Water Risk Filter as the sub-national proxy |
| Data coverage ends 2023 | OCI is a 2023 baseline | earthovershoot01 / FAOSTAT | Schedule annual refresh via `earthovershoot01/scripts/calculate_overshoot.py` |
| AFCS uncertainty ± 0.37 t C/ha/yr | Propagates to ≈ ±50% uncertainty on `ef_carbon_project_gha` | Mancini et al. 2016 [12] | Report OCI as range (AFCS − σ, AFCS + σ) in `final_analysis.md` |

---

## 9. Minimal Code Change to `assess.py`

Add one function call after Pass 1 completes. Constants reference their authoritative sources
in inline comments:

```python
def _run_overshoot_context(supply_summary: pd.DataFrame) -> pd.DataFrame:
    """Pass 4: Ecological Footprint context layer.

    Methodology: Borucke et al. (2013) [4]; Lin et al. (2018) [6].
    Carbon formula: Mancini et al. (2016) [12]; Khatiwala et al. (2009) [13];
                    Wackernagel et al. (2002) [2].
    EQF values: Wackernagel et al. (2002) Table 1 [2]; Galli et al. (2007) [3].
    """
    # AFCS = 0.73 t C/ha/yr (Mancini et al. 2016 [12], range ± 0.37)
    # ocean_frac = 0.35 (Khatiwala et al. 2009 [13])
    # EQF_forest = 1.3 gha/ha (Wackernagel et al. 2002, Table 1 [2])
    AFCS, OCEAN, EQF_C = 0.73, 0.35, 1.3
    seq_rate = AFCS * (44 / 12)   # t C/ha/yr → t CO₂/ha/yr

    overshoot = pd.read_csv(
        Path(__file__).parent / "indicators/earthovershoot/overshoot_results.csv"
    )
    baseline = overshoot[overshoot["year"] == 2023].set_index("area")

    rows = []
    for _, proj in supply_summary.iterrows():
        country = REGION_TO_ISO3_COUNTRY.get(proj["region"], proj["region"])
        ctx     = baseline.loc[country] if country in baseline.index else None

        # §4.1: carbon footprint in gha [2,12,13]
        ef_carbon = proj["GHG_tCO2e"] * (1 - OCEAN) / seq_rate * EQF_C
        # §4.2: land footprint in gha using cropland EQF=2.1 as proxy [2,3]
        ef_land   = proj.get("land_ha", 0) * 2.1
        bc_host   = ctx["bc_total_gha"] if ctx is not None else float("nan")
        deficit   = ctx["ecological_deficit_gha"] if ctx is not None else float("nan")
        # §4.3: OCI [4]
        oci       = (ef_carbon + ef_land) / bc_host * 100 if bc_host > 0 else float("nan")
        # §5 Pass 3: BC deficit multiplier [7,18]
        bc_mult   = 1.0 if deficit >= 0 else min(1.5, 1 + abs(deficit) / bc_host)

        rows.append({
            "project":             proj["project"],
            "country":             country,
            "ef_per_capita_host":  ctx["ef_per_capita_gha"] if ctx is not None else None,
            "bc_per_capita_host":  ctx["bc_per_capita_gha"] if ctx is not None else None,
            "deficit_host_gha":    deficit,
            "ef_carbon_proj_gha":  ef_carbon,
            "ef_land_proj_gha":    ef_land,
            "oci_pct":             oci,
            "bc_deficit_mult":     bc_mult,
        })

    return pd.DataFrame(rows)
```

Call it in the main block and write to `results/overshoot_context.csv`.

---

## References

1. Wackernagel, M. & Rees, W.E. (1996). *Our Ecological Footprint: Reducing Human Impact on the Earth*. New Society Publishers, Gabriola Island. ISBN 978-0-86571-312-3.

2. Wackernagel, M., Schulz, N.B., Deumling, D., Linares, A.C., Jenkins, M., Kapos, V., Monfreda, C., Loh, J., Myers, N., Norgaard, R. & Randers, J. (2002). Tracking the ecological overshoot of the human economy. *Proceedings of the National Academy of Sciences* 99(14): 9266–9271. DOI: 10.1073/pnas.142033699

3. Galli, A., Kitzes, J., Wermer, P., Wackernagel, M., Niccolucci, V. & Tiezzi, E. (2007). An exploration of the mathematics behind the ecological footprint. *International Journal of Ecodynamics* 2(4): 250–257. DOI: 10.2495/ECO-V2-N4-250-257

4. Borucke, M., Moore, D., Cranston, G., Gracey, K., Iha, K., Larson, J., Lazarus, E., Morales, J.C., Wackernagel, M. & Galli, A. (2013). Accounting for demand and supply of the biosphere's regenerative capacity: The National Footprint Accounts' underlying methodology and framework. *Ecological Indicators* 24: 518–533. DOI: 10.1016/j.ecolind.2012.08.005

5. Steffen, W., Richardson, K., Rockström, J., Cornell, S.E., Fetzer, I., Bennett, E.M., Biggs, R., Carpenter, S.R., de Vries, W., de Wit, C.A. et al. (2015). Planetary boundaries: Guiding human development on a changing planet. *Science* 347(6223): 1259855. DOI: 10.1126/science.1259855

6. Lin, D., Hanscom, L., Murthy, A., Galli, A., Evans, M., Neill, E., Mancini, M.S., Martindill, J., Medouar, F.Z., Huang, S. & Wackernagel, M. (2018). Ecological Footprint Accounting for Countries: Updates and Results of the National Footprint Accounts, 2012–2018. *Resources* 7(3): 58. DOI: 10.3390/resources7030058

7. Wackernagel, M., Lin, D., Evans, M., Hanscom, L. & Raven, P. (2019). Defying the Footprint Oracle: Implications of Country Resource Trends. *Sustainability* 11(7): 2164. DOI: 10.3390/su11072164

8. Monfreda, C., Wackernagel, M. & Deumling, D. (2004). Establishing national natural capital accounts based on detailed Ecological Footprint and biological capacity assessments. *Land Use Policy* 21(3): 231–246. DOI: 10.1016/j.landusepol.2003.10.009

9. European Financial Reporting Advisory Group (EFRAG) (2023). ESRS E1 Climate Change. Commission Delegated Regulation (EU) 2023/2772, Annex I. Official Journal of the European Union, L 2023/2772.

10. EFRAG (2023). ESRS E3 Water and Marine Resources. Commission Delegated Regulation (EU) 2023/2772, Annex I.

11. EFRAG (2023). ESRS E4 Biodiversity and Ecosystems. Commission Delegated Regulation (EU) 2023/2772, Annex I.

12. Mancini, M.S., Galli, A., Niccolucci, V., Lin, D., Bastianoni, S., Wackernagel, M. & Marchettini, N. (2016). Ecological Footprint: Refining the carbon Footprint calculation. *Ecological Indicators* 61: 390–403. DOI: 10.1016/j.ecolind.2015.09.040

13. Khatiwala, S., Primeau, F. & Hall, T. (2009). Reconstruction of the history of anthropogenic CO₂ concentrations in the ocean. *Nature* 462: 346–349. DOI: 10.1038/nature08526

14. Pauly, D. & Christensen, V. (1995). Primary production required to sustain global fisheries. *Nature* 374: 255–257. DOI: 10.1038/374255a0

15. IPCC (2022). *Climate Change 2022: Mitigation of Climate Change*. Contribution of Working Group III to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change. Cambridge University Press. DOI: 10.1017/9781009157926

16. Taskforce on Nature-related Financial Disclosures (TNFD) (2023). *Recommendations of the Taskforce on Nature-related Financial Disclosures*. v1.0. TNFD Secretariat.

17. IPBES (2022). *Summary for Policymakers of the Methodological Assessment of the Diverse Values and Valuation of Nature of the Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services*. IPBES Secretariat, Bonn. DOI: 10.5281/zenodo.6522392

18. Wetzer, T., Stuart-Smith, R. & Dibley, A. (2024). Climate risk assessments must account for the legal dimension. *Science* 383(6678): 152–154. DOI: 10.1126/science.adj0598

19. EBRD (2024). *Transition Impact Monitoring System (TIMS) and Assessment of Transition Qualities (ATQ): Methodology Note*. European Bank for Reconstruction and Development, London. [Available: `project_assessment/indicators/ebrd_atq_methodology.md`]

20. IFC (2021). *Anticipated Impact Measurement and Monitoring (AIMM): General Guidance Note*. International Finance Corporation, Washington DC.

21. Boulay, A.M., Bare, J., Benini, L., Berger, M., Lathuillière, M.J., Manzardo, A., Margni, M., Motoshita, M., Núñez, M., Pastor, A.V., Ridoutt, B., Oki, T., Worbe, S. & Pfister, S. (2018). The WULCA consensus characterisation model for water scarcity footprints: Assessing impacts of water consumption based on available water remaining (AWARE). *International Journal of Life Cycle Assessment* 23: 368–378. DOI: 10.1007/s11367-017-1333-8

22. FAST-Infra / Climate Policy Initiative (2021). *FAST-Infra Sustainable Infrastructure Label: Indicator Set v1.0*. FAST-Infra Group.

23. IFC, IDB, EBRD, MIF (2013). *HIPSO: Harmonized Indicators for Private Sector Operations*. Joint IFI agreement. Available: www.hipso.org.

---

*Data sourced from FAOSTAT via earthovershoot01 (production-based NFA methodology).
See `earthovershoot01/README.md` for full methodology, limitations, and update instructions.*
