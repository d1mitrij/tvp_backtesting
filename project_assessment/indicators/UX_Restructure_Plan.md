# UX Restructure Plan: Role-Based MDB Impact Dashboard (v3)

**Target file:** `integrated_finance/app.py` (currently 2,464 lines)  
**Reference specs:** `indicators/Overview_Different_Roles.md`, `indicators/Indicators_Overview_Upgraded.md`, `indicators/ebrd_atq_methodology.md`, `indicators/EarthOvershoot_Integration.md`  
**Goal:** Four role-specific analytical views, each with cross-project/cross-country comparison capability, built on a shared multi-project computation core. Existing single-project engine is unchanged.

**v3 changes vs v2:**
- ATQ radar now loads real 2024-25 scores from `indicators/ebrd_atq_scores_2024_25.csv` (6 genuine transition quality dimensions, 1–10 scale).
- EarthOvershoot context (OCI, EF/BC per capita, `bc_deficit_mult`) wired into multi-project runner, Country Canvas, Country Comparison, Portfolio risk factors, and TNFD regulatory mapping.

---

## Core Architecture — Cross-Project Comparison Matrix

All four role views read from a shared **multi-project results DataFrame**. The four roles are different visual slices of the same underlying matrix.

| Role                 | Axis fixed       | Axis varied       | Primary output                                   |
|:---------------------|:-----------------|:------------------|:-------------------------------------------------|
| Strategy Economist   | Country          | Sector            | Aggregate country impact + dependency mix        |
| Investment Officer   | Sector           | Country           | Cross-country comparative iNPV/S-IRR ranking     |
| Portfolio Manager    | Portfolio (all)  | SSP scenario      | CFA-style risk-adjusted iNPV distribution        |
| Compliance Specialist| Project / Country| Regulation        | Disclosure gap matrix per jurisdiction           |

### Shared runner function

```python
@st.cache_data(show_spinner="Running multi-project analysis…")
def _run_multi_project(
    project_specs: tuple[tuple],   # hashable: ((pid, country, sector, capex, avoided_co2), ...)
    focus_year: int,
    ssps: tuple[str],
) -> pd.DataFrame:
    """
    Run _compute_metrics for every (project × SSP) combination.
    Returns a flat DataFrame with columns:
        pid, project_name, country, sector, region, capex_usd,
        ssp, inpv_usd, s_irr, wacc_adj, dep_factor, wwf_score,
        tier0_ghg, tier1_ghg, tier0_emp, tier1_emp,
        c_ghg, c_gva, c_water,          # WifOR VFs used
        adj_ratio_ghg, adj_ratio_emp,   # SSP transmission factors
        nature_debt_usd, nature_dividend_usd
    """
    rows = []
    for spec in project_specs:
        pid, country, sector, capex_usd, avoided_co2 = spec
        base = PROJECT_BY_ID[pid]
        region = COUNTRY_REGION_MAP.get(country, base["region"])
        iso3   = COUNTRY_ISO2_TO_ISO3.get(country, "DEU")
        nace   = PROJECT_SECTOR_TO_NACE.get(sector, "H49")
        p = dict(base, country=country, sector=sector, region=region,
                 capex_usd=capex_usd, avoided_co2=avoided_co2)
        vf  = _load_value_factors(iso3, nace, focus_year)
        dep = _compute_dep_context(capex_usd, sector, region)
        for ssp in ssps:
            ssp_f = _load_all_ssp_factors(region, focus_year).get(ssp, {})
            m     = _compute_metrics(p, vf, dep, ssp_f)
            rows.append({
                "pid": pid, "project_name": base["name"],
                "country": country, "sector": sector, "region": region,
                "capex_usd": capex_usd, "ssp": ssp,
                **m,   # inpv_usd, s_irr, wacc_adj, dep_factor, dep_factor_adj, wwf_score,
                       # tier0_ghg, tier1_ghg, tier0_emp, tier1_emp,
                       # c_ghg, c_gva, c_water, adj_ratio_ghg, adj_ratio_emp,
                       # nature_debt_usd, nature_dividend_usd,
                       # ef_carbon_gha, ef_land_gha, oci_pct, bc_deficit_mult,
                       # ef_per_capita_host, bc_per_capita_host, deficit_host_gha
            })
    return pd.DataFrame(rows)
```

`_compute_metrics` must be extended to return the full flat dict above (most fields are already computed internally — they just need to be surfaced in the return value). Overshoot fields (`ef_carbon_gha`, `ef_land_gha`, `oci_pct`, `bc_deficit_mult`, `dep_factor_adj`, `ef_per_capita_host`, `bc_per_capita_host`, `deficit_host_gha`) are produced by `_run_overshoot_context` (see `EarthOvershoot_Integration.md §9`) and merged into the runner output. `dep_factor_adj = dep_factor × bc_deficit_mult` replaces raw `dep_factor` in WACC greenium and `nature_debt_usd` calculations.

---

## Step 1 — Role Selector in Sidebar

**Where:** Top of the sidebar, before the project picker.

```python
ROLES = [
    "Investment Officer",
    "Strategy Economist",
    "Portfolio Manager",
    "Compliance Specialist",
]

with st.sidebar:
    active_role = st.selectbox("Your role", options=ROLES, index=0, key="active_role")
```

---

## Step 2 — Tab Visibility Router

```python
# Tab index map (existing 10 tabs, 0-based)
# 0: Overview  1: IO Supply Chain  2: NPV/iNPV  3: S-IRR  4: WACC
# 5: Cash Flow  6: SSP Comparison  7: Project Profile  8: Methodology  9: Portfolio

ROLE_TABS: dict[str, list[int]] = {
    "Investment Officer":    [0, 2, 3, 4, 5, 6, 7, 8],
    "Strategy Economist":    [0, 6, 7, 8, 9],
    "Portfolio Manager":     [0, 5, 6, 9],
    "Compliance Specialist": [0, 7, 8],
}
```

Each role also gets one additional **role-specific tab** appended after the existing tabs:

```python
ROLE_EXTRA_TAB: dict[str, str] = {
    "Investment Officer":    "Country Comparison",
    "Strategy Economist":    "Country Canvas",
    "Portfolio Manager":     "Risk Dashboard",
    "Compliance Specialist": "Regulatory Mapping",
}
```

Build tabs dynamically:

```python
_visible_labels = [ALL_TAB_LABELS[i] for i in ROLE_TABS[active_role]]
_visible_labels.append(ROLE_EXTRA_TAB[active_role])
_tabs = st.tabs(_visible_labels)
# Last tab in _tabs is always the role-specific extra tab
_role_tab = _tabs[-1]
```

---

## Step 3 — Strategy Economist: Country Canvas

**Extra tab: "Country Canvas"**

The user selects a country and adds N hypothetical projects of different sectors. The runner computes all projects under all SSPs and aggregates at country level.

### 3a. Country Canvas Builder (sidebar panel, visible only for this role)

```python
if active_role == "Strategy Economist":
    st.sidebar.subheader("Country Canvas")
    canvas_country = st.sidebar.selectbox(
        "Country", options=_ALL_COUNTRY_LIST, key="canvas_country"
    )
    canvas_entries = st.sidebar.data_editor(
        pd.DataFrame([
            {"sector": "Rail",   "capex_m": 140.0, "avoided_co2": 0},
            {"sector": "Energy", "capex_m": 500.0, "avoided_co2": 50000},
        ]),
        column_config={
            "sector":      st.column_config.SelectboxColumn("Sector", options=ALL_SECTORS),
            "capex_m":     st.column_config.NumberColumn("CAPEX (USD M)", min_value=0.1),
            "avoided_co2": st.column_config.NumberColumn("Avoided CO₂/yr"),
        },
        num_rows="dynamic",
        key="canvas_entries",
    )
```

### 3b. Multi-sector Country Impact Aggregation

```python
with _role_tab:
    st.subheader(f"Country Impact Canvas — {canvas_country}")

    # Build spec tuples for the runner
    # Use a synthetic pid for canvas entries not in PROJECTS registry
    canvas_specs = tuple(
        (row["sector"], canvas_country, row["sector"],
         int(row["capex_m"] * 1e6), int(row["avoided_co2"]))
        for _, row in canvas_entries.iterrows()
        if row["capex_m"] > 0
    )
    if canvas_specs:
        df_canvas = _run_multi_project(canvas_specs, focus_yr, tuple(ALL_SSPS))

        # --- Tier 0/1 breakdown by sector ---
        st.subheader("Supply-chain impact by sector (median SSP)")
        df_mid = df_canvas[df_canvas["ssp"] == "SSP2-4.5"]
        tier_fig = px.bar(
            df_mid, x="sector", y=["tier0_ghg", "tier1_ghg"],
            barmode="group", title="GHG — Tier 0 vs Tier 1 (tCO₂e/yr)",
            labels={"value": "tCO₂e/yr", "variable": "Tier"},
        )
        st.plotly_chart(tier_fig, use_container_width=True)

        # --- Monetised impact by sector × SSP ---
        st.subheader("Monetised iNPV by sector across SSP scenarios")
        inpv_fig = px.box(
            df_canvas, x="sector", y="inpv_usd", color="ssp",
            title="iNPV distribution across SSPs",
        )
        st.plotly_chart(inpv_fig, use_container_width=True)

        # --- ENCORE / WWF dependency radar per sector ---
        st.subheader("Nature dependency profile by sector")
        dep_fig = _fig_dependency_radar(df_mid)   # new function — see below
        st.plotly_chart(dep_fig, use_container_width=True)

        # --- WifOR value factor comparison ---
        st.subheader("WifOR value factors applied")
        vf_cols = ["sector", "c_ghg", "c_gva", "c_water"]
        st.dataframe(df_mid[vf_cols].drop_duplicates().set_index("sector"))

        # --- SSP sensitivity: aggregate country iNPV ---
        agg = df_canvas.groupby("ssp")["inpv_usd"].sum().reset_index()
        agg_fig = px.bar(agg, x="ssp", y="inpv_usd",
                         title="Aggregate country iNPV by SSP scenario")
        st.plotly_chart(agg_fig, use_container_width=True)

        # --- Ecological Footprint / Biocapacity context (EarthOvershoot_Integration §3) ---
        st.subheader("Ecological Footprint context — host country")
        eo_row = df_mid.iloc[0] if not df_mid.empty else {}
        c_ef, c_bc, c_oci = st.columns(3)
        c_ef.metric("EF per capita (gha/cap)",
                    f"{eo_row.get('ef_per_capita_host', float('nan')):.2f}")
        c_bc.metric("BC per capita (gha/cap)",
                    f"{eo_row.get('bc_per_capita_host', float('nan')):.2f}",
                    delta=f"{'surplus' if eo_row.get('deficit_host_gha', -1) >= 0 else 'deficit'}")
        c_oci.metric("Max OCI across sectors (%)",
                     f"{df_mid['oci_pct'].max():.4f}")

        oci_fig = px.bar(
            df_mid.reset_index(), x="sector", y="oci_pct",
            title="Overshoot Contribution Index by sector (% of host BC)",
            labels={"oci_pct": "OCI (%)"},
            color="bc_deficit_mult",
            color_continuous_scale="RdYlGn_r",
        )
        st.plotly_chart(oci_fig, use_container_width=True)

        # ATQ radar (single country vs frontier — real 2024-25 scores)
        st.subheader("ATQ gap — Country vs Frontier")
        st.plotly_chart(_fig_atq_radar(canvas_country), use_container_width=True)
```

### 3c. Dependency Radar Function

```python
def _fig_dependency_radar(df: pd.DataFrame) -> go.Figure:
    """Polar chart: dep_factor and wwf_score per sector."""
    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row["dep_factor"], row["wwf_score"], row["dep_factor"]],
            theta=["ENCORE dep", "WWF water", "ENCORE dep"],
            name=row["sector"],
            fill="toself",
        ))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 2])))
    return fig
```

### 3d. ATQ Radar (Country vs Frontier)

Real 2024-25 scores loaded from `indicators/ebrd_atq_scores_2024_25.csv` (42 EBRD economies).
Dimensions are the six genuine ATQ transition qualities scored 1–10 (frontier = 10, per EBRD
methodology §4-5 in `ebrd_atq_methodology.md`). Countries not in the EBRD coverage set fall back
to a neutral 5.0 score per dimension with a "No ATQ data" label.

```python
# ATQ dimension names match column headers in ebrd_atq_scores_2024_25.csv
ATQ_DIMENSIONS = ["Competitive", "Well_Governed", "Green", "Inclusive", "Resilient", "Integrated"]
ATQ_FRONTIER   = {d: 10.0 for d in ATQ_DIMENSIONS}

# ISO2 → ATQ country name (subset; extend as needed from COUNTRY_REGION_MAP)
ATQ_ISO2_TO_NAME: dict[str, str] = {
    "PL": "Poland", "DE": "Germany", "TR": "Türkiye", "UA": "Ukraine",
    "EG": "Egypt", "MA": "Morocco", "KZ": "Kazakhstan", "GE": "Georgia",
    "RO": "Romania", "RS": "Serbia", "BG": "Bulgaria", "HR": "Croatia",
    "CZ": "Czechia", "HU": "Hungary", "SK": "Slovak Republic", "SI": "Slovenia",
    "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania",
    "AL": "Albania", "BA": "Bosnia and Herzegovina", "GR": "Greece",
    "XK": "Kosovo", "ME": "Montenegro", "MK": "North Macedonia",
    "AM": "Armenia", "AZ": "Azerbaijan", "MD": "Moldova",
    "UZ": "Uzbekistan", "KG": "Kyrgyz Republic", "TJ": "Tajikistan",
    "MN": "Mongolia", "TM": "Turkmenistan",
    "JO": "Jordan", "LB": "Lebanon", "TN": "Tunisia",
    "BJ": "Benin", "CI": "Côte d'Ivoire", "GH": "Ghana",
    "KE": "Kenya", "NG": "Nigeria", "SN": "Senegal",
}

@st.cache_data
def _load_atq_data() -> pd.DataFrame:
    return pd.read_csv(
        Path(__file__).parent / "../indicators/ebrd_atq_scores_2024_25.csv"
    ).set_index("Country")

def _fig_atq_radar(country_iso2: str) -> go.Figure:
    country_name = ATQ_ISO2_TO_NAME.get(country_iso2)
    df_atq = _load_atq_data()
    dims_display = ["Competitive", "Well Governed", "Green",
                    "Inclusive", "Resilient", "Integrated"]
    if country_name and country_name in df_atq.index:
        row = df_atq.loc[country_name]
        c_vals = [row[d] for d in ATQ_DIMENSIONS]
        label  = country_name
    else:
        c_vals = [5.0] * len(ATQ_DIMENSIONS)
        label  = f"{country_iso2} (no ATQ data)"
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[10.0] * len(ATQ_DIMENSIONS), theta=dims_display,
        name="Frontier (10)", line_color="gold",
    ))
    fig.add_trace(go.Scatterpolar(
        r=c_vals, theta=dims_display, name=label, fill="toself",
    ))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 10])))
    return fig
```

---

## Step 4 — Investment Officer: Country Comparison

**Extra tab: "Country Comparison"**

Fix sector + CAPEX; vary country. Ranks countries by iNPV, S-IRR, dep_factor, ESG greenium.

### 4a. Country Comparison Builder (sidebar)

```python
if active_role == "Investment Officer":
    st.sidebar.subheader("Country Comparison")
    compare_countries = st.sidebar.multiselect(
        "Compare countries",
        options=_ALL_COUNTRY_LIST,
        default=["DE", "PL", "TR"],
        key="compare_countries",
    )
    compare_sector = st.sidebar.selectbox(
        "Sector (fixed)", options=ALL_SECTORS,
        index=ALL_SECTORS.index(sector_sel), key="compare_sector"
    )
    compare_capex_m = st.sidebar.number_input(
        "CAPEX (USD M, fixed)", 1.0, 5000.0, 100.0, key="compare_capex"
    )
```

### 4b. Cross-country Ranking View

```python
with _role_tab:
    st.subheader(f"{compare_sector} — {compare_capex_m:.0f} M USD across countries")
    if compare_countries:
        cc_specs = tuple(
            (f"cc_{c}", c, compare_sector,
             int(compare_capex_m * 1e6), 0)
            for c in compare_countries
        )
        df_cc = _run_multi_project(cc_specs, focus_yr, tuple(ALL_SSPS))
        df_mid = df_cc[df_cc["ssp"] == "SSP2-4.5"].set_index("country")

        # --- Ranked table ---
        # dep_factor_adj = dep_factor × bc_deficit_mult (biocapacity-adjusted, per EarthOvershoot §5 Pass 3)
        rank_cols = ["inpv_usd", "s_irr", "dep_factor_adj", "wwf_score",
                     "wacc_adj", "tier0_ghg", "tier1_ghg", "c_gva",
                     "oci_pct", "bc_deficit_mult"]
        st.dataframe(
            df_mid[rank_cols]
            .sort_values("inpv_usd", ascending=False)
            .style.background_gradient(subset=["inpv_usd", "s_irr"], cmap="RdYlGn")
                  .background_gradient(subset=["dep_factor_adj", "wwf_score",
                                               "oci_pct", "bc_deficit_mult"], cmap="RdYlGn_r"),
            use_container_width=True,
        )

        # --- iNPV bar by country, grouped by SSP ---
        inpv_fig = px.bar(
            df_cc, x="country", y="inpv_usd", color="ssp", barmode="group",
            title="iNPV by country across SSP scenarios",
        )
        st.plotly_chart(inpv_fig, use_container_width=True)

        # --- Dep_factor vs iNPV scatter ---
        scatter_fig = px.scatter(
            df_mid.reset_index(), x="dep_factor", y="inpv_usd",
            text="country", size="capex_usd", color="wwf_score",
            color_continuous_scale="RdYlGn_r",
            title="Nature dependency vs iNPV — bubble size = CAPEX",
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

        # --- WifOR VF heatmap (c_ghg, c_gva, c_water by country) ---
        vf_fig = px.imshow(
            df_mid[["c_ghg", "c_gva", "c_water"]],
            title="WifOR value factors by country",
            color_continuous_scale="Blues",
            aspect="auto",
        )
        st.plotly_chart(vf_fig, use_container_width=True)

    # --- ETI / AIMM scoring (single-project, existing panels) ---
    # [ETI form, Uplift matrix, AIMM quadrant, Theory of Change, Download scorecard]
    # (same as original Step 4 — retained below)
```

### 4c. ETI / AIMM Scoring (retained from original plan)

```python
SFB_SECTORS: dict[str, list[str]] = {
    "Rail":         ["Modal shift (%)", "Passenger-km added", "GHG avoided (tCO₂e/yr)"],
    "Energy":       ["MWh generated", "New connections (#)", "Carbon intensity reduction (%)"],
    "Agribusiness": ["Farmers reached (#)", "Share female farmers (%)", "Yield increase (%)"],
    "Health":       ["Patients served (#)", "Beds added (#)", "Cost-per-DALY saved"],
    "Water":        ["m³ treated/yr", "New water connections (#)", "Water loss reduction (%)"],
}
UPLIFT_ETI_DELTA: dict[str, float] = {
    "Local currency": 0.05, "Equity": 0.08, "SME focus": 0.04,
    "Climate-aligned": 0.06, "Inclusion focus": 0.05,
}

def _compute_eti_score(country_gap: float, intensity_scores: list[float],
                       uplifts: list[str]) -> float:
    base = country_gap * sum(intensity_scores)
    return round(base * (1 + sum(UPLIFT_ETI_DELTA.get(u, 0) for u in uplifts)), 3)

def _compute_aimm_score(project_outcome: float, market_outcome: float,
                        risk_factor: float) -> float:
    return round((project_outcome + market_outcome) * risk_factor, 2)
```

Theory of Change `st.graphviz_chart` and `st.download_button` scorecard export as in original plan.

---

## Step 5 — Portfolio Manager: CFA-Style Risk Dashboard

**Extra tab: "Risk Dashboard"**

The portfolio is the full set of projects in `PROJECTS` (or a user-selected subset). Risk framework maps directly to CFA constructs.

### CFA concept → model variable mapping

| CFA Concept               | Model Variable                                  | Notes                                                    |
|:--------------------------|:------------------------------------------------|:---------------------------------------------------------|
| Expected return           | Mean iNPV across 5 SSPs                         | Impact-adjusted expected value                           |
| Return volatility         | Std dev of iNPV across SSPs                     | Scenario dispersion = climate transition risk            |
| Impact-adjusted Sharpe    | `mean(iNPV) / std(iNPV)` across SSPs            | Higher = better risk-adjusted impact                     |
| Systematic risk factor 1  | GHG transition risk: sensitivity of iNPV to c_ghg × adj_ratio_ghg | Co-movement with SSP trajectory |
| Systematic risk factor 2  | Water scarcity risk: wwf_score × sector ENCORE water materiality | Correlated within river basins |
| Systematic risk factor 3  | Employment formality risk: sensitivity of iNPV to c_gva × adj_ratio_emp | Country labour-market factor |
| Systematic risk factor 4  | Biocapacity deficit risk: `bc_deficit_mult` (1.0–1.5) for host country | Amplifies dep_factor and WACC for ecologically stressed countries; grounded in Wackernagel et al. 2019 macro-economic deficit evidence |
| Idiosyncratic risk        | `dep_factor_adj` − 1.0 (bc-adjusted deviation from neutral) | Project-specific nature dependency loading after biocapacity context |
| Diversification signal    | Correlation of iNPV across SSPs between projects | Low correlation = genuine portfolio diversification      |
| Scenario VaR              | iNPV at SSP5-8.5 (worst case)                   | Tail risk under severe climate scenario                  |
| Factor concentration      | Fraction of portfolio with wwf_score > 3.0      | Water-stress concentration risk                          |

### 5a. Portfolio Selector (sidebar)

```python
if active_role == "Portfolio Manager":
    st.sidebar.subheader("Portfolio")
    portfolio_pids = st.sidebar.multiselect(
        "Projects in portfolio",
        options=[p["id"] for p in PROJECTS],
        default=[p["id"] for p in PROJECTS],
        key="portfolio_pids",
    )
```

### 5b. Risk Dashboard Render

```python
with _role_tab:
    st.subheader("Portfolio Risk Dashboard — CFA-aligned impact framework")

    pf_specs = tuple(
        (pid, PROJECT_BY_ID[pid]["country"],
         PROJECT_BY_ID[pid]["sector"],
         PROJECT_BY_ID[pid]["capex_usd"],
         PROJECT_BY_ID[pid]["avoided_co2"])
        for pid in portfolio_pids
    )
    df_pf = _run_multi_project(pf_specs, focus_yr, tuple(ALL_SSPS))

    # --- Summary risk table ---
    risk_summary = (
        df_pf.groupby("pid")
        .agg(
            project_name=("project_name", "first"),
            country=("country", "first"),
            sector=("sector", "first"),
            inpv_mean=("inpv_usd", "mean"),
            inpv_std=("inpv_usd", "std"),
            inpv_worst=("inpv_usd", "min"),        # SSP5-8.5 proxy
            dep_factor=("dep_factor", "first"),
            wwf_score=("wwf_score", "first"),
            wacc_adj=("wacc_adj", "first"),
        )
        .assign(impact_sharpe=lambda d: d["inpv_mean"] / d["inpv_std"].replace(0, float("nan")))
        .reset_index()
    )
    st.dataframe(
        risk_summary.style
            .background_gradient(subset=["impact_sharpe"], cmap="RdYlGn")
            .background_gradient(subset=["dep_factor", "wwf_score"], cmap="RdYlGn_r")
            .background_gradient(subset=["inpv_worst"], cmap="RdYlGn"),
        use_container_width=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Aggregate iNPV (SSP2)", f"${risk_summary['inpv_mean'].sum()/1e6:.1f} M")
    col2.metric("Projects with dep > 1.2",
                int((risk_summary["dep_factor"] > 1.2).sum()))
    col3.metric("Portfolio impact Sharpe",
                f"{risk_summary['impact_sharpe'].mean():.2f}")

    # --- Efficient frontier: risk vs impact ---
    ef_fig = px.scatter(
        risk_summary, x="inpv_std", y="inpv_mean",
        text="project_name", color="dep_factor",
        color_continuous_scale="RdYlGn_r", size="dep_factor",
        title="Impact Efficient Frontier — mean iNPV vs SSP volatility",
        labels={"inpv_std": "iNPV volatility (USD)", "inpv_mean": "Mean iNPV (USD)"},
    )
    st.plotly_chart(ef_fig, use_container_width=True)

    # --- Correlation heatmap (iNPV co-movement across SSPs) ---
    st.subheader("iNPV correlation matrix (SSP scenario outcomes)")
    pivot = df_pf.pivot_table(index="ssp", columns="project_name", values="inpv_usd")
    corr_fig = px.imshow(
        pivot.corr(), color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Project iNPV correlation across SSP scenarios",
    )
    st.plotly_chart(corr_fig, use_container_width=True)

    # --- Systematic factor loadings ---
    st.subheader("Factor risk decomposition")
    factor_df = risk_summary[["project_name", "dep_factor_adj", "wwf_score",
                               "wacc_adj", "bc_deficit_mult"]].copy()
    factor_df["ghg_transition_loading"] = (
        df_pf.groupby("pid")["adj_ratio_ghg"].std().values
    )
    factor_df["emp_formality_loading"] = (
        df_pf.groupby("pid")["adj_ratio_emp"].std().values
    )
    # bc_deficit_mult is country-level, constant across SSPs per project
    factor_fig = px.bar(
        factor_df.melt(id_vars="project_name",
                       value_vars=["dep_factor_adj", "wwf_score",
                                   "ghg_transition_loading", "emp_formality_loading",
                                   "bc_deficit_mult"]),
        x="project_name", y="value", color="variable", barmode="group",
        title="Systematic risk factor loadings by project (4-factor model)",
    )
    st.plotly_chart(factor_fig, use_container_width=True)

    # --- OCI overshoot summary (EarthOvershoot_Integration §7 — HIPSO cross-cutting climate) ---
    st.subheader("Overshoot Contribution Index by project")
    oci_df = df_pf[df_pf["ssp"] == "SSP2-4.5"][["project_name", "oci_pct",
                                                   "ef_carbon_gha", "ef_land_gha"]]
    st.dataframe(oci_df.sort_values("oci_pct", ascending=False)
                 .style.background_gradient(subset=["oci_pct"], cmap="RdYlGn_r"),
                 use_container_width=True)

    # --- Scenario VaR table ---
    st.subheader("Scenario Value-at-Risk (iNPV at SSP5-8.5)")
    var_df = df_pf[df_pf["ssp"] == "SSP5-8.5"][["project_name", "inpv_usd", "dep_factor"]]
    st.dataframe(var_df.sort_values("inpv_usd").style
                 .background_gradient(subset=["inpv_usd"], cmap="RdYlGn"),
                 use_container_width=True)

    # --- HIPSO performance grid (existing plan, retained) ---
    st.subheader("HIPSO Monitoring Grid")
    # [ProgressColumn + variance flagging — same as original Step 5]
```

---

## Step 6 — Compliance Specialist: Regulatory Mapping

**Extra tab: "Regulatory Mapping"**

Maps computed model outputs to mandatory disclosure requirements across jurisdictions. The FAST-Infra checklist (original Step 6) becomes one panel within this broader regulatory context.

### 6a. Jurisdiction Selector

```python
JURISDICTIONS = ["EU (SFDR/Taxonomy/CSRD)", "UK (TCFD)", "US (SEC Climate)", "TNFD", "EBRD ATQ", "AIIB EP"]

REGULATORY_MATRIX: dict[str, dict[str, dict]] = {
    "EU (SFDR/Taxonomy/CSRD)": {
        "PAI — GHG intensity (SFDR Annex I #1)": {
            "model_field": "tier0_ghg",
            "description": "GHG emissions attributable to project per M USD invested",
            "threshold": None,
        },
        "PAI — Biodiversity (SFDR Annex I #7)": {
            "model_field": "dep_factor",
            "description": "ENCORE biodiversity materiality score",
            "threshold": 1.2,   # flag if dep_factor > 1.2
        },
        "PAI — Water intensity (SFDR Annex I #6)": {
            "model_field": "wwf_score",
            "description": "WWF Water Risk Filter score (1–5)",
            "threshold": 3.0,
        },
        "EU Taxonomy — Climate Mitigation (Art. 10)": {
            "model_field": "tier0_ghg",
            "description": "Substantial contribution: positive GHG impact required",
            "threshold": 0,   # tier0_ghg must be negative (avoided) to qualify
        },
        "EU Taxonomy — DNSH Water (Art. 17)": {
            "model_field": "wwf_score",
            "description": "Do No Significant Harm: wwf_score must not exceed 3.5",
            "threshold": 3.5,
        },
        "CSRD — Double Materiality": {
            "model_field": "inpv_usd",
            "description": "Financial materiality of nature risk: dep_factor deviation from 1.0",
            "threshold": None,
        },
    },
    "UK (TCFD)": {
        "TCFD — Physical Risk (scenario analysis)": {
            "model_field": "inpv_usd",
            "description": "iNPV range across SSP1-1.9 to SSP5-8.5 constitutes scenario analysis",
            "threshold": None,
        },
        "TCFD — Transition Risk": {
            "model_field": "adj_ratio_ghg",
            "description": "SSP-driven GHG intensity adjustment = transition risk factor",
            "threshold": None,
        },
    },
    "TNFD": {
        "TNFD LEAP — Locate (L)": {
            "model_field": "country",
            "description": "Country and region of operations identified",
            "threshold": None,
        },
        "TNFD LEAP — Evaluate (E)": {
            "model_field": "dep_factor",
            "description": "ENCORE dependency assessment completed (dep_factor computed)",
            "threshold": None,
        },
        "TNFD LEAP — Assess (A)": {
            "model_field": "wwf_score",
            "description": "WWF Water Risk Filter quantified",
            "threshold": None,
        },
        "TNFD LEAP — Prepare (P)": {
            "model_field": "nature_dividend_usd",
            "description": "Monetised nature dividend computed via WifOR VFs",
            "threshold": None,
        },
        "TNFD — Overshoot Contribution Index": {
            "model_field": "oci_pct",
            "description": "Project EF as % of host biocapacity; flag if OCI > 0.1 % (EarthOvershoot §4.3)",
            "threshold": 0.1,
        },
    },
    "US (SEC Climate)": {
        "SEC — Material GHG emissions": {
            "model_field": "tier0_ghg",
            "description": "Scope 1/2 GHG emissions of project operations",
            "threshold": None,
        },
        "SEC — Climate scenario analysis": {
            "model_field": "inpv_usd",
            "description": "Financial impact under at least one climate scenario",
            "threshold": None,
        },
    },
    "EBRD ATQ": {
        "ATQ Green — GHG transition quality": {
            "model_field": "tier0_ghg",
            "description": "GHG avoided as evidence for Green transition quality (ATQ 'Green' dimension; score from ebrd_atq_scores_2024_25.csv)",
            "threshold": 0,
        },
        "ATQ Green — OCI biophysical benchmark": {
            "model_field": "oci_pct",
            "description": "OCI as quantitative sub-indicator for Green transition quality gap (EarthOvershoot §7 / EBRD ATQ methodology §2)",
            "threshold": 0.1,
        },
        "ATQ Resilient — nature dependency": {
            "model_field": "dep_factor_adj",
            "description": "BC-adjusted nature dependency loading; contributes to financial-sector resilience scoring",
            "threshold": 1.2,
        },
    },
    "AIIB EP": {
        "AIIB EP Category A — biodiversity": {
            "model_field": "dep_factor",
            "description": "High-dependency projects (dep_factor > 1.4) require full ESIA",
            "threshold": 1.4,
        },
        "AIIB EP — Water risk": {
            "model_field": "wwf_score",
            "description": "wwf_score > 3.0 triggers Water Management Plan requirement",
            "threshold": 3.0,
        },
    },
}
```

### 6b. Regulatory Gap Matrix Render

```python
with _role_tab:
    juris = st.selectbox("Jurisdiction", options=JURISDICTIONS, key="reg_juris")
    req_map = REGULATORY_MATRIX.get(juris, {})

    st.subheader(f"Disclosure gap matrix — {juris}")
    rows = []
    for req_name, req_cfg in req_map.items():
        field   = req_cfg["model_field"]
        thresh  = req_cfg["threshold"]
        val     = proj.get(field) or metrics.get(field)   # live computed value
        if thresh is not None and val is not None:
            met = val <= thresh if field in ("wwf_score", "dep_factor") else val <= thresh
            status = "✅ Met" if met else "⚠️ Review required"
        else:
            status = "✅ Data available" if val is not None else "❌ Not computed"
        rows.append({
            "Requirement": req_name,
            "Model field": field,
            "Current value": f"{val:.3g}" if isinstance(val, float) else str(val),
            "Threshold": str(thresh) if thresh is not None else "—",
            "Status": status,
            "Description": req_cfg["description"],
        })
    reg_df = pd.DataFrame(rows)
    st.dataframe(reg_df, use_container_width=True)

    # Summary KPIs
    n_met   = reg_df["Status"].str.startswith("✅").sum()
    n_flag  = reg_df["Status"].str.startswith("⚠️").sum()
    n_miss  = reg_df["Status"].str.startswith("❌").sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Requirements met",     n_met)
    c2.metric("Review required",      n_flag, delta=f"-{n_flag}" if n_flag else None)
    c3.metric("Data gaps",            n_miss, delta=f"-{n_miss}" if n_miss else None)

    st.download_button(
        "Export Regulatory Gap Report (CSV)",
        data=reg_df.to_csv(index=False),
        file_name=f"reg_gap_{_pid}_{juris.split()[0]}.csv",
        mime="text/csv",
        key=f"dl_reg_{_pid}",
    )

    # FAST-Infra checklist (retained from original Step 6, as a sub-section)
    with st.expander("FAST-Infra Sustainable Infrastructure Label"):
        # [14-criteria checklist, validation gate, badge generator — unchanged from original]
        pass
```

---

## Step 7 — Header KPIs Adapt Per Role

```python
_role_kpis = {
    "Investment Officer":    [("iNPV", f"${metrics['inpv_usd']/1e6:.1f} M"),
                              ("ETI Score", f"{final_eti:.3f}"),
                              ("AIMM Score", f"{aimm:.2f}/20")],
    "Strategy Economist":    [("Country", canvas_country),
                              ("Sectors modelled", str(len(canvas_entries))),
                              ("Aggregate iNPV (SSP2)",
                               f"${df_canvas[df_canvas['ssp']=='SSP2-4.5']['inpv_usd'].sum()/1e6:.1f} M")],
    "Portfolio Manager":     [("Projects monitored", str(len(portfolio_pids))),
                              ("Variance flags", str(n_flagged_hipso)),
                              ("Portfolio impact Sharpe",
                               f"{risk_summary['impact_sharpe'].mean():.2f}")],
    "Compliance Specialist": [("Requirements met", f"{n_met}/{len(rows)}"),
                              ("Label status", "Certified" if all_fi_met else "Pending"),
                              ("Jurisdiction", juris.split()[0])],
}
cols = st.columns(3)
for col, (label, val) in zip(cols, _role_kpis[active_role]):
    col.metric(label, val)
```

---

## Step 8 — Computation Guard

```python
_needs_io = active_role in ("Investment Officer", "Strategy Economist")
io_result = _run_io(proj["capex_usd"], proj["sector"], proj["region"]) if _needs_io else None
```

---

## Step 9 — Session State Initialisation

```python
_ss_defaults = {
    "active_role":       ROLES[0],
    "canvas_country":    "DE",
    "canvas_entries":    None,
    "compare_countries": ["DE", "PL", "TR"],
    "portfolio_pids":    [p["id"] for p in PROJECTS],
    "reg_juris":         JURISDICTIONS[0],
    "hipso_actuals":     {},
}
for _k, _v in _ss_defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v
```

---

## Step 10 — Wrap Existing Tab Bodies

```python
_visible = ROLE_TABS[active_role]
for _tab_pos, _tab_idx in enumerate(_visible):
    with _tabs[_tab_pos]:
        if _tab_idx == 0:
            # Overview — always shown; role-specific KPIs injected at top (Step 7)
            pass   # existing overview code unchanged
        elif _tab_idx == 1:
            pass   # IO Supply Chain — unchanged
        # … all other existing tabs unchanged …

with _tabs[-1]:  # role-specific extra tab
    if active_role == "Strategy Economist":
        # Step 3 — Country Canvas
        pass
    elif active_role == "Investment Officer":
        # Step 4 — Country Comparison
        pass
    elif active_role == "Portfolio Manager":
        # Step 5 — Risk Dashboard
        pass
    elif active_role == "Compliance Specialist":
        # Step 6 — Regulatory Mapping
        pass
```

---

## Implementation Sequence

| #  | Action                                                        | Est. lines added |
|----|---------------------------------------------------------------|-----------------|
| 1  | `_run_multi_project` shared runner + extend `_compute_metrics` return dict | +80 |
| 2  | `ROLES`, `ROLE_TABS`, `ROLE_EXTRA_TAB` constants             | +25              |
| 3  | Role selector widget; dynamic `st.tabs` with extra tab       | +15              |
| 4  | Wrap existing tab bodies                                      | +20              |
| 5  | Session state init block                                      | +15              |
| 6  | `_run_overshoot_context` function + merge into runner output  | +60              |
| 7  | `ATQ_ISO2_TO_NAME` map + `_load_atq_data` + `_fig_atq_radar` (real CSV) + `_fig_dependency_radar` | +80 |
| 8  | Strategy Economist — Country Canvas sidebar + render (incl. OCI panel) | +140        |
| 9  | Investment Officer — Country Comparison sidebar + render (incl. OCI/bc_mult columns) | +115 |
| 10 | ETI/AIMM engine + uplift matrix + ToC + download             | +100             |
| 11 | Portfolio Manager — Risk Dashboard (Sharpe, corr, 4-factor, VaR, OCI summary) | +160 |
| 12 | HIPSO grid with ProgressColumn + variance flags              | +70              |
| 13 | `REGULATORY_MATRIX` constant (incl. EBRD ATQ + TNFD OCI entries) | +100         |
| 14 | Compliance Specialist — Regulatory Mapping render            | +90              |
| 15 | FAST-Infra checklist + badge generator                       | +80              |
| 16 | Header KPI routing                                           | +30              |
| 17 | Computation guard                                            | +5               |

**Total net addition: ~1,185 lines. Zero existing lines deleted.**

---

## Open Decisions (Require Human Input)

| # | Decision                             | Options                                                         | Default / Status               |
|---|--------------------------------------|-----------------------------------------------------------------|--------------------------------|
| 1 | ATQ country data source              | ~~(a) Stub dict~~, **(b) CSV file** `indicators/ebrd_atq_scores_2024_25.csv`, (c) live API | **Resolved: CSV** (file confirmed present; 42 economies) |
| 2 | Choropleth for SE view               | (a) `px.choropleth` (Plotly, no extra dep), (b) `st.pydeck_chart` | `px.choropleth`             |
| 3 | Canvas project IDs (SE view)         | (a) Re-use existing `PROJECTS` registry pids, (b) synthetic IDs for canvas entries | Synthetic IDs |
| 4 | CFA correlation: by SSP or by year   | (a) 5 SSPs as "scenarios" (implemented above), (b) annual cashflow time-series | 5 SSPs      |
| 5 | Regulatory threshold source          | (a) Hard-coded in `REGULATORY_MATRIX`, (b) editable CSV        | Hard-coded                     |
| 6 | HIPSO actuals data source            | (a) Manual entry in grid, (b) CSV upload                       | Manual entry                   |
| 7 | Role persistence across reloads      | (a) Session state only, (b) `st.query_params` URL encoding     | Session state                  |
| 8 | Label badge format                   | (a) HTML in-app, (b) PDF via `reportlab`                       | HTML                           |
| 9 | `_run_multi_project` caching key     | (a) Tuple of specs (hashable), (b) hash of DataFrame           | Tuple of specs                 |
| 10| Regulatory matrix completeness       | (a) Subset as above + EBRD ATQ, (b) extend with IDB, IsDB, NDB, AfDB | Subset (EU+UK+TNFD+US+EBRD ATQ+AIIB) |
| 11| EarthOvershoot data refresh cadence  | (a) Static 2023 baseline (current), (b) annual refresh via `earthovershoot01/scripts/calculate_overshoot.py` | Static 2023 baseline |
| 12| ATQ `iso2` → country name coverage gaps | (a) Fallback to 5.0 "no data" (current), (b) EBRD region mean imputation | Fallback to 5.0 |
| 13| OCI uncertainty reporting            | (a) Point estimate only, (b) range [AFCS−σ, AFCS+σ] per Mancini 2016 ±0.37 tC/ha/yr | Point estimate |

---

*Plan v3 — extends v2 with: (1) real EBRD ATQ 2024-25 scores replacing stub data (6 genuine transition quality dimensions, 1–10 scale, CSV-sourced); (2) EarthOvershoot biocapacity context (OCI, bc_deficit_mult, dep_factor_adj) wired into the multi-project runner and surfaced in all four role views; (3) EBRD ATQ added as a regulatory jurisdiction in the Compliance Specialist matrix. All new code is additive; no existing computation functions are modified.*
