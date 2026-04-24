import json

def code_cell(src):
    return {"cell_type": "code", "metadata": {}, "source": src,
            "outputs": [], "execution_count": None,
            "id": "placeholder"}

def md_cell(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src,
            "id": "placeholder"}

# ─────────────────────────────────────────────────────────────────────────────
C1_PARAMS = """\
# ══════════════════════════════════════════════════════════════════
# PARAMETERS  ← edit here, then Run All
# ══════════════════════════════════════════════════════════════════
CAPEX_USD   = 100_000_000
COUNTRY     = "DE"
SECTOR      = "Rail_Dev"       # Health_Social | Energy | Rail_Dev | Rail_Op
DATABASE    = "exiobase"
SCENARIO    = "SSP2-4.5"       # None for baseline
FOCUS_YEAR  = 2030
COMPARE_SSPS = True
from pathlib import Path
RESULTS_DIR = Path("results")
REPO_ROOT   = Path(".").resolve().parent
TOP_N       = 5
"""

# ─────────────────────────────────────────────────────────────────────────────
C2_IMPORTS = """\
# ══════════════════════════════════════════════════════════════════
# IMPORTS, COLOUR PALETTES, DEP CONSTANTS
# ══════════════════════════════════════════════════════════════════
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from IPython.display import display, HTML

sys.path.insert(0, str(REPO_ROOT / "tvp_dbio"))
sys.path.insert(0, str(REPO_ROOT / "tvp_dependency"))

from tvp_io_lib import (
    tier0_impact, tier1_impact, tier_impact,
    ISO2_TO_REGION, SECTOR_ALLOC,
)
from dependency_profiler.encore_materiality import (
    MATERIALITY_MATRIX, RATING_SCALE, ECOSYSTEM_SERVICES,
    get_materiality_profile,
)
from dependency_profiler.wwf_risk_filter import (
    score_project, REGIONAL_BASELINES, HIGH_RISK_THRESHOLD,
)

# ── Colour palettes ────────────────────────────────────────────────────────
TIER_NODE = {"t0": "#4e79a7", "t1": "#f28e2b", "t2": "#59a14f", "t3": "#b07aa1"}
TIER_LINK = {
    "t0": "rgba(78,121,167,0.35)", "t1": "rgba(242,142,43,0.35)",
    "t2": "rgba(89,161,79,0.35)",  "t3": "rgba(176,122,161,0.35)",
}
INTER  = {"t0": "#aec7e8", "t1": "#ffbb78", "t2": "#98df8a", "t3": "#c5b0d5"}
STRESSORS = [
    ("GHG_tCO2e",      "GHG",        "tCO2e",   "#d62728", "[-]"),
    ("Employment_FTE", "Employment", "FTE",      "#2ca02c", "[+]"),
    ("Water_1000m3",   "Water",      "000 m3",   "#1f77b4", "[-]"),
]
ALL_SSPS   = ["SSP1-1.9","SSP2-4.5","SSP3-7.0","SSP4-6.0","SSP5-8.5"]
SSP_COLORS = {
    "SSP1-1.9":"#1a9641","SSP2-4.5":"#a6d96a",
    "SSP3-7.0":"#fdae61","SSP4-6.0":"#f46d43","SSP5-8.5":"#d73027",
}
INTENSITY_CSV = REPO_ROOT / "tvp_scenario" / "osemosys" / "results" / "tvpdbio_intensity_factors.csv"

# ── Dependency constants (mirrored from assess.py) ─────────────────────────
PROJECT_SECTOR_TO_ENCORE = {
    "Health_Social":      "human_health_activities",
    "Health_Specialized": "human_health_activities",
    "Health_General":     "human_health_activities",
    "Energy":             "electric_power_generation_hydro",
    "Rail_Dev":           "rail_transport",
    "Rail_Op":            "rail_transport",
}
STRESSOR_ECOSYSTEM_MAP = {
    "GHG_tCO2e":      ["climate_regulation", "mediation_of_gaseous_waste"],
    "Employment_FTE": ["terrestrial_ecosystem_use", "soil_quality", "erosion_control"],
    "Water_1000m3":   ["water_supply", "water_flow_regulation", "freshwater_ecosystem_use"],
    "ValueAdded_M$":  ["water_supply", "climate_regulation", "terrestrial_ecosystem_use"],
}
STRESSOR_WWF_COL = {
    "GHG_tCO2e":      "brf_ecosystem",
    "Employment_FTE": "brf_ecosystem",
    "Water_1000m3":   "wrf_physical",
    "ValueAdded_M$":  "wrf_composite",
}
SC_SECTOR_DEP = {
    "Construction":        {"water":3.0,"ghg":3.0,"land":4.0,"va":3.3},
    "Energy_Utilities":    {"water":5.0,"ghg":5.0,"land":3.0,"va":4.3},
    "Manufacturing":       {"water":4.0,"ghg":3.0,"land":3.0,"va":3.3},
    "Transport_Logistics": {"water":2.0,"ghg":3.0,"land":4.0,"va":3.0},
    "Health_Social":       {"water":5.0,"ghg":4.0,"land":2.0,"va":3.7},
    "Agriculture":         {"water":5.0,"ghg":5.0,"land":5.0,"va":5.0},
    "Mining_Extraction":   {"water":5.0,"ghg":3.0,"land":5.0,"va":4.3},
    "Water_Waste":         {"water":5.0,"ghg":3.0,"land":4.0,"va":4.0},
}
STRESSOR_SC_KEY = {
    "GHG_tCO2e":"ghg","Employment_FTE":"land",
    "Water_1000m3":"water","ValueAdded_M$":"va",
}
DEP_NEUTRAL   = 3.0
DEP_THRESHOLD = 3.4   # WWF high-risk

# ── Utility ────────────────────────────────────────────────────────────────
COUNTRY_NAMES = {
    "germany":"DE","france":"FR","uk":"GB","united kingdom":"GB",
    "spain":"ES","italy":"IT","netherlands":"NL","poland":"PL",
    "sweden":"SE","norway":"NO","switzerland":"CH","turkey":"TR",
    "brazil":"BR","mexico":"MX","argentina":"AR","colombia":"CO",
    "chile":"CL","peru":"PE","south africa":"ZA","nigeria":"NG",
    "kenya":"KE","ethiopia":"ET","ghana":"GH","egypt":"EG","morocco":"MA",
    "china":"CN","india":"IN","japan":"JP","south korea":"KR",
    "indonesia":"ID","thailand":"TH","vietnam":"VN",
    "russia":"RU","united states":"US","usa":"US","canada":"CA","australia":"AU",
}

def resolve(country):
    u = country.strip().upper()
    if u in ISO2_TO_REGION: return ISO2_TO_REGION[u]
    rm = {r.upper(): r for r in ("Europe","LATAM","Africa","Asia","Global")}
    if u in rm: return rm[u]
    iso2 = COUNTRY_NAMES.get(country.strip().lower())
    return ISO2_TO_REGION.get(iso2, "Global") if iso2 else "Global"

def fmt_capex(v):
    return f"${v/1e9:.2f}B" if v >= 1e9 else f"${v/1e6:.1f}M" if v >= 1e6 else f"${v:,.0f}"

REGION       = resolve(COUNTRY)
ENCORE_SECTOR = PROJECT_SECTOR_TO_ENCORE.get(SECTOR, "rail_transport")
DEP_REGION   = REGION.lower() if REGION.lower() in REGIONAL_BASELINES else "europe"
print(f"Country: {COUNTRY} -> Region: {REGION}  |  ENCORE: {ENCORE_SECTOR}")
"""

# ─────────────────────────────────────────────────────────────────────────────
C3_IO = """\
# ══════════════════════════════════════════════════════════════════
# IO ANALYSIS  (Leontief tiers 0-10)
# ══════════════════════════════════════════════════════════════════
print("[1/4] Tier 0 ...", end=" ", flush=True)
t0_res = tier0_impact(CAPEX_USD, SECTOR, REGION, DATABASE)
print(f"GHG {t0_res['GHG_tCO2e']:,.0f}")

print("[2/4] Tier 1 bilateral ...", end=" ", flush=True)
t1_res = tier1_impact(CAPEX_USD, SECTOR, REGION, DATABASE)
print(f"GHG {t1_res['GHG_tCO2e']:,.0f}")

print("[3/4] Tier 2 ...", end=" ", flush=True)
t2_raw = tier_impact(CAPEX_USD, SECTOR, REGION, DATABASE, tier_from=2, tier_to=2)
print(f"{len(t2_raw)} rows")

print("[4/4] Tier 3-10 ...", end=" ", flush=True)
t3_raw = tier_impact(CAPEX_USD, SECTOR, REGION, DATABASE, tier_from=3, tier_to=10)
print(f"{len(t3_raw)} rows")

PID = f"{SECTOR}_{REGION}_{fmt_capex(CAPEX_USD)}"

def _t0_df():
    rows = [{"project_id":PID,"supplying_sector":sec,
             **{k:v for k,v in vals.items() if k!="spend_M$"}}
            for sec,vals in t0_res["impact_by_sector"].items()]
    return pd.DataFrame(rows)

def _t1_df():
    rows = [{"project_id":PID,"supplying_sector":sec,"sourcing_region":reg,
             **{k:v for k,v in rv.items() if k not in ("share","spend_M$")}}
            for sec,regions in t1_res["tier1_by_sector"].items()
            for reg,rv in regions.items()]
    return pd.DataFrame(rows)

t0 = _t0_df(); t1 = _t1_df()
t2 = t2_raw.copy(); t2["project_id"] = PID
t3 = t3_raw.copy(); t3["project_id"] = PID

COLS_SC = ["GHG_tCO2e","Employment_FTE","Water_1000m3","ValueAdded_M$"]
print(f"\\n{'Stressor':<22} {'T0':>10} {'T1':>10} {'T2':>10} {'T3-10':>10} {'Total':>12}")
print("-"*70)
for c in COLS_SC:
    v = [df[c].sum() if c in df.columns else 0 for df in [t0,t1,t2,t3]]
    print(f"  {c:<20} {v[0]:>10,.0f} {v[1]:>10,.0f} {v[2]:>10,.0f} {v[3]:>10,.0f} {sum(v):>12,.0f}")
"""

# ─────────────────────────────────────────────────────────────────────────────
C4_DEP = """\
# ══════════════════════════════════════════════════════════════════
# SCENARIO FACTORS + DEPENDENCY SETUP
# ══════════════════════════════════════════════════════════════════
def _load_factors(region, scenario, year):
    if not INTENSITY_CSV.exists() or scenario is None: return None
    df  = pd.read_csv(INTENSITY_CSV)
    row = df[(df["region"]==region)&(df["scenario"]==scenario)&(df["year"]==float(year))]
    if row.empty: return None
    r  = row.iloc[0]
    rs = float(r.get("renewable_share", 0.5))
    return {
        "GHG_tCO2e":      float(r["adj_ratio_ghg"]),
        "Employment_FTE": float(r["adj_ratio_employment"]),
        "Water_1000m3":   float(rs * 0.15 + (1 - rs) * 1.0),
        "ValueAdded_M$":  float(r["adj_ratio_employment"]),
    }

def _apply(val, col, factors):
    return val * factors[col] if (factors and col in factors) else val

FACTORS     = _load_factors(REGION, SCENARIO, FOCUS_YEAR)
ALL_FACTORS = {s: _load_factors(REGION, s, FOCUS_YEAR) for s in ALL_SSPS}
sc_label    = f"{SCENARIO} {FOCUS_YEAR}" if SCENARIO and FACTORS else "Baseline"

# ── ENCORE dependency scores for this project sector ──────────────────────
enc_mat = MATERIALITY_MATRIX.get(ENCORE_SECTOR, {})
ENCORE_DEP = {}
for stressor, svcs in STRESSOR_ECOSYSTEM_MAP.items():
    scores = [RATING_SCALE.get(enc_mat.get(s, ("N","N"))[0], 0) for s in svcs]
    ENCORE_DEP[stressor] = sum(scores) / max(len(scores), 1)

# ── WWF scores per region (preloaded or embedded defaults) ────────────────
WWF_DEFAULTS = {
    "europe": {"wrf_physical":2.93,"wrf_regulatory":3.87,"wrf_reputational":4.00,
               "wrf_composite":3.41,"brf_species_threat":2.69,
               "brf_ecosystem":3.30,"brf_protected_areas":3.23,"brf_composite":3.12},
    "africa": {"wrf_physical":4.38,"wrf_regulatory":2.85,"wrf_reputational":3.15,
               "wrf_composite":3.70,"brf_species_threat":4.46,
               "brf_ecosystem":3.35,"brf_protected_areas":3.37,"brf_composite":3.80},
    "asia":   {"wrf_physical":4.97,"wrf_regulatory":2.90,"wrf_reputational":3.75,
               "wrf_composite":4.27,"brf_species_threat":5.00,
               "brf_ecosystem":3.55,"brf_protected_areas":4.07,"brf_composite":4.26},
    "latam":  {"wrf_physical":3.79,"wrf_regulatory":2.65,"wrf_reputational":3.60,
               "wrf_composite":3.48,"brf_species_threat":4.74,
               "brf_ecosystem":3.45,"brf_protected_areas":3.93,"brf_composite":4.09},
}
WWF_BY_REGION = dict(WWF_DEFAULTS)
wwf_csv = REPO_ROOT / "tvp_dependency" / "assessment_output" / "wwf_risk_scores.csv"
if wwf_csv.exists():
    _wr = pd.read_csv(wwf_csv)
    _wr["dep_region"] = _wr["region"].str.lower()
    _cols = ["wrf_physical","wrf_regulatory","wrf_reputational","wrf_composite",
             "brf_species_threat","brf_ecosystem","brf_protected_areas","brf_composite"]
    _agg = _wr.groupby("dep_region")[_cols].mean().to_dict(orient="index")
    WWF_BY_REGION.update(_agg)

def get_wwf(region_str):
    key = (region_str or "").lower()
    return WWF_BY_REGION.get(key, WWF_DEFAULTS["europe"])

# ── dep_factor: three-component formula from assess.py ────────────────────
def dep_factor(stressor, sourcing_region, supplying_sector):
    enc  = ENCORE_DEP.get(stressor, DEP_NEUTRAL)
    wwf  = get_wwf(sourcing_region).get(STRESSOR_WWF_COL[stressor], DEP_NEUTRAL)
    sc   = SC_SECTOR_DEP.get(supplying_sector, {}).get(STRESSOR_SC_KEY[stressor], DEP_NEUTRAL)
    base = (enc/DEP_NEUTRAL + wwf/DEP_NEUTRAL) / 2.0
    return (base + sc/DEP_NEUTRAL) / 2.0

# ── Tier-level weighted mean dep_factor ───────────────────────────────────
TIER_DEP = {}
for tier_key, df, region_col in [
    ("t0", t0, None),
    ("t1", t1, "sourcing_region"),
    ("t2", t2, None),
    ("t3", t3, None),
]:
    TIER_DEP[tier_key] = {}
    for st in COLS_SC:
        if st not in df.columns or df.empty:
            TIER_DEP[tier_key][st] = 1.0
            continue
        weights = np.abs(df[st].values) + 1e-9
        factors = [
            dep_factor(st,
                       row.get(region_col, REGION) if region_col else REGION,
                       row["supplying_sector"])
            for _, row in df.iterrows()
        ]
        TIER_DEP[tier_key][st] = float(np.average(factors, weights=weights))

# ── Three-layer summary per tier ──────────────────────────────────────────
def _raw(df, c):  return df[c].sum() if c in df.columns else 0.0
def _adj(df, c):  return _apply(_raw(df, c), c, FACTORS)
def _dep(raw_adj, tk, c): return raw_adj * TIER_DEP[tk][c]

TIER_DEFS   = [("t0","Tier 0  Direct",t0),
               ("t1","Tier 1  Bilateral",t1),
               ("t2","Tier 2  Upstream",t2),
               ("t3","Tier 3-10  Deep",t3)]

SUMMARY = {}
for tk,_,df in TIER_DEFS:
    SUMMARY[tk] = {
        "raw": {c: _raw(df,c) for c in COLS_SC},
        "adj": {c: _adj(df,c) for c in COLS_SC},
        "dep": {c: _dep(_adj(df,c), tk, c) for c in COLS_SC},
    }
GRAND = {
    layer: {c: sum(SUMMARY[tk][layer][c] for tk,*_ in TIER_DEFS)
            for c in COLS_SC}
    for layer in ["raw","adj","dep"]
}

print(f"Scenario: {sc_label}")
if FACTORS:
    for k,v in FACTORS.items(): print(f"  {k:<22} x{v:.4f}")
print("\\nDependency factors (tier x stressor):")
for tk,label,_ in TIER_DEFS:
    vals = "  ".join(f"{c.split('_')[0]}={TIER_DEP[tk][c]:.3f}" for c in COLS_SC)
    print(f"  {label:<22} {vals}")
"""

# ─────────────────────────────────────────────────────────────────────────────
C5_LEGEND = """\
# ══════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════
def _badge(col, label, extra=""):
    return (f"<span style='background:{col};color:white;"
            f"padding:2px 7px;border-radius:3px'>{label}</span>{extra}")

display(HTML(f\"\"\"
<div style='font-family:Arial;font-size:12px;padding:9px 14px;
            background:#f5f5f5;border-radius:5px;margin:8px 0'>
<b>Investment:</b> {fmt_capex(CAPEX_USD)} &nbsp;·&nbsp;
<b>Country:</b> {COUNTRY} ({REGION}) &nbsp;·&nbsp;
<b>Sector:</b> {SECTOR} &nbsp;·&nbsp;
<b>ENCORE:</b> {ENCORE_SECTOR} &nbsp;·&nbsp;
<b>Layer:</b> {sc_label}
<br><br>
{_badge('#4e79a7','Tier 0','&nbsp;')}
{_badge('#f28e2b','Tier 1','&nbsp;')}
{_badge('#59a14f','Tier 2','&nbsp;')}
{_badge('#b07aa1','Tier 3-10','&emsp;')}
<b>dep_factor neutral=1.0</b> &nbsp;
<span style='color:#d62728'>&gt;1.0 amplifies</span> /
<span style='color:#2ca02c'>&lt;1.0 dampens</span> nature-related risk
</div>
\"\"\"))
"""

# ─────────────────────────────────────────────────────────────────────────────
C6_ENCORE = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 1 — ENCORE MATERIALITY HEATMAP
# Shows ecosystem dependency (left) and impact (right) for the
# project sector, sorted by combined materiality score.
# ══════════════════════════════════════════════════════════════════
profile = get_materiality_profile(ENCORE_SECTOR)
mat     = profile.summary_table()   # sorted by dep+impact score

svc_labels = [r["ecosystem_service"].replace("_"," ").title() for r in mat]
dep_scores = [r["dependency_score"]  for r in mat]
imp_scores = [r["impact_score"]      for r in mat]
dep_labels = [r["dependency_rating"] for r in mat]
imp_labels = [r["impact_rating"]     for r in mat]
material   = [r["material"]          for r in mat]

# Heatmap: rows = ecosystem services, cols = [Dependency, Impact]
Z    = [[d, i] for d, i in zip(dep_scores, imp_scores)]
TEXT = [[f"<b>{dl}</b>", f"<b>{il}</b>"] for dl, il in zip(dep_labels, imp_labels)]

svc_colors = ["#fff3cd" if m else "#f8f9fa" for m in material]  # highlight material rows

fig_enc = go.Figure()
fig_enc.add_trace(go.Heatmap(
    z=Z, x=["Dependency", "Impact"], y=svc_labels,
    text=TEXT, texttemplate="%{text}",
    textfont=dict(size=10),
    colorscale=[
        [0.0,  "#f0f0f0"],
        [0.2,  "#c7e9c0"],
        [0.4,  "#74c476"],
        [0.6,  "#fdae6b"],
        [0.8,  "#e6550d"],
        [1.0,  "#7f0000"],
    ],
    zmin=0, zmax=5,
    colorbar=dict(title="Score (0-5)", tickvals=[0,1,2,3,4,5],
                  ticktext=["N","VL","L","M","H","VH"]),
))

# Stressor-relevant services
for stressor, svcs in STRESSOR_ECOSYSTEM_MAP.items():
    for svc in svcs:
        label = svc.replace("_"," ").title()
        if label in svc_labels:
            idx = svc_labels.index(label)

fig_enc.update_layout(
    title=dict(
        text=(f"<b>ENCORE Materiality — {ENCORE_SECTOR.replace('_',' ').title()}</b>"
              f"<br><span style='font-size:11px;color:#555'>"
              f"Yellow rows = material (dep or impact >= High). "
              f"Stressor-relevant services are marked by their score color.</span>"),
        x=0.01, xanchor="left", font=dict(size=14)),
    height=620,
    margin=dict(l=220, r=120, t=90, b=40),
    yaxis=dict(autorange="reversed"),
    paper_bgcolor="#fafafa", font=dict(family="Arial", size=10),
)
display(HTML(fig_enc.to_html(full_html=False, include_plotlyjs="cdn")))
"""

# ─────────────────────────────────────────────────────────────────────────────
C7_WWF = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 2 — WWF RISK BY SOURCING REGION
# WRF (Water Risk) + BRF (Biodiversity Risk) per region:
# main investment region + all T1 bilateral sourcing regions.
# Red dashed line = high-risk threshold (3.4).
# ══════════════════════════════════════════════════════════════════
# Collect regions to show: main + T1
_t1_regions = (t1["sourcing_region"].unique().tolist()
               if not t1.empty else [])
_all_regions = [REGION] + [r for r in _t1_regions if r != REGION]
_all_regions = _all_regions[:6]   # cap at 6 for readability

WRF_KEYS = ["wrf_physical","wrf_regulatory","wrf_reputational"]
BRF_KEYS = ["brf_species_threat","brf_ecosystem","brf_protected_areas"]
WRF_LABELS = ["Physical","Regulatory","Reputational"]
BRF_LABELS = ["Species Threat","Ecosystem Intactness","Protected Areas"]
RISK_COLORS = ["#e6550d","#fdae6b","#74c476","#31a354","#006d2c"]

fig_wwf = make_subplots(
    rows=1, cols=2,
    subplot_titles=["Water Risk Filter (WRF) — Physical/Reg/Rep",
                    "Biodiversity Risk Filter (BRF) — Species/Eco/PA"],
    shared_yaxes=False,
)

reg_colors = ["#4e79a7","#f28e2b","#59a14f","#b07aa1","#e15759","#76b7b2"]

for ri, reg in enumerate(_all_regions):
    wdata = get_wwf(reg)
    rc    = reg_colors[ri % len(reg_colors)]
    wrf_v = [wdata.get(k, 0) for k in WRF_KEYS]
    brf_v = [wdata.get(k, 0) for k in BRF_KEYS]
    flag  = "(main)" if reg == REGION else f"(T1)"

    fig_wwf.add_trace(go.Bar(
        name=f"{reg} {flag}", x=WRF_LABELS, y=wrf_v,
        marker_color=rc, opacity=0.82,
        text=[f"{v:.2f}" for v in wrf_v],
        textposition="outside", textfont=dict(size=8),
        legendgroup=reg,
    ), row=1, col=1)

    fig_wwf.add_trace(go.Bar(
        name=f"{reg} {flag}", x=BRF_LABELS, y=brf_v,
        marker_color=rc, opacity=0.82,
        text=[f"{v:.2f}" for v in brf_v],
        textposition="outside", textfont=dict(size=8),
        legendgroup=reg, showlegend=False,
    ), row=1, col=2)

# High-risk threshold line
for col in [1, 2]:
    fig_wwf.add_hline(
        y=DEP_THRESHOLD, line_dash="dash", line_color="red",
        line_width=1.5, annotation_text="High Risk 3.4",
        annotation_font=dict(color="red", size=9),
        row=1, col=col,
    )

fig_wwf.update_layout(
    title=dict(
        text=(f"<b>WWF Risk Filter Scores by Region</b>"
              f"<br><span style='font-size:11px;color:#555'>"
              f"{COUNTRY} ({REGION}) · {SECTOR} · {sc_label}</span>"),
        x=0.01, xanchor="left", font=dict(size=14)),
    barmode="group",
    height=420,
    yaxis=dict(range=[0, 5.8], title="Score (1-5)"),
    yaxis2=dict(range=[0, 5.8], title="Score (1-5)"),
    legend=dict(orientation="h", y=1.12),
    margin=dict(l=60, r=40, t=100, b=50),
    paper_bgcolor="#fafafa", font=dict(family="Arial", size=10),
)
display(HTML(fig_wwf.to_html(full_html=False, include_plotlyjs="cdn")))
"""

# ─────────────────────────────────────────────────────────────────────────────
C8_DEP_FACTOR = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 3 — DEPENDENCY FACTOR BY TIER × STRESSOR
# dep_factor = (ENCORE/3 + WWF/3 + SC-sector/3) / 3  (neutral=1.0)
# >1.0: nature conditions amplify the stressor's risk exposure.
# <1.0: low dependency / low regional risk — dampening effect.
# ══════════════════════════════════════════════════════════════════
_tier_keys    = ["t0","t1","t2","t3"]
_tier_names   = ["Tier 0  Direct","Tier 1  Bilateral",
                 "Tier 2  Upstream","Tier 3-10  Deep"]
_tier_colors  = ["#4e79a7","#f28e2b","#59a14f","#b07aa1"]
_str3 = [("GHG_tCO2e","GHG","#d62728"),
         ("Employment_FTE","Employment","#2ca02c"),
         ("Water_1000m3","Water","#1f77b4")]

fig_df = go.Figure()
for sc_col, sc_name, sc_color in _str3:
    x_labels, y_vals, bar_colors = [], [], []
    for tk, tn in zip(_tier_keys, _tier_names):
        df_val = TIER_DEP[tk][sc_col]
        x_labels.append(tn)
        y_vals.append(df_val)
        bar_colors.append(
            "#d62728" if df_val > 1.15 else
            "#fdae6b" if df_val > 1.0  else
            "#74c476" if df_val < 0.9  else "#aec7e8"
        )
    fig_df.add_trace(go.Bar(
        name=sc_name, x=x_labels, y=y_vals,
        marker_color=sc_color, opacity=0.80,
        text=[f"{v:.3f}" for v in y_vals],
        textposition="outside",
        textfont=dict(size=9),
    ))

fig_df.add_hline(
    y=1.0, line_dash="dot", line_color="#333",
    line_width=2,
    annotation_text="Neutral (1.0)", annotation_position="top right",
    annotation_font=dict(size=9, color="#333"),
)
fig_df.add_hrect(y0=1.0, y1=1.67, fillcolor="#ffe0e0", opacity=0.15,
                  annotation_text="Amplifying zone",
                  annotation_position="top right",
                  annotation_font=dict(size=8, color="#c00"))
fig_df.add_hrect(y0=0.33, y1=1.0, fillcolor="#e0ffe0", opacity=0.15,
                  annotation_text="Dampening zone",
                  annotation_position="bottom right",
                  annotation_font=dict(size=8, color="#060"))

fig_df.update_layout(
    title=dict(
        text=(f"<b>Dependency Factor by Tier</b>"
              f"<br><span style='font-size:11px;color:#555'>"
              f"Three-component dep_factor (ENCORE + WWF + SC-sector) — "
              f"neutral=1.0, range approx 0.33-1.67</span>"),
        x=0.01, xanchor="left", font=dict(size=14)),
    barmode="group",
    yaxis=dict(title="dep_factor", range=[0, max(
        max(TIER_DEP[tk][c] for c,*_ in _str3) for tk in _tier_keys
    ) * 1.25 + 0.05]),
    height=400,
    legend=dict(orientation="h", y=1.10),
    margin=dict(l=70, r=60, t=100, b=70),
    paper_bgcolor="#fafafa", font=dict(family="Arial", size=11),
)
display(HTML(fig_df.to_html(full_html=False, include_plotlyjs="cdn")))
"""

# ─────────────────────────────────────────────────────────────────────────────
C9_SANKEY = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 4 — DEPENDENCY-WEIGHTED SANKEY
# Same 3-stressor, 4-tier structure as investment_sankey.ipynb,
# but link/node values carry the dep_factor weight:
#   flow = scenario_adj × dep_factor(row)
# Node colour intensity darkens when dep_factor > 1.0.
# ══════════════════════════════════════════════════════════════════
def _top_n(s, n=TOP_N):
    s = s[s > 0]
    if len(s) <= n: return s
    top  = s.nlargest(n)
    rest = s[~s.index.isin(top.index)].sum()
    return pd.concat([top, pd.Series({"Other": rest})]) if rest > 0 else top

def _dep_sankey(col):
    nodes, nc = [], []
    src_l, tgt_l, val_l, lc_l = [], [], [], []

    def node(lbl, color):
        if lbl not in nodes: nodes.append(lbl); nc.append(color)
        return nodes.index(lbl)

    meta   = next(m for m in STRESSORS if m[0] == col)
    sname, sunit, s_col, ssign = meta[1], meta[2], meta[3], meta[4]

    # Per-row dep-weighted values ────────────────────────────────────
    def _dw_row(df, sreg_col=None):
        if df.empty or col not in df.columns: return pd.Series(dtype=float)
        rows = []
        for _, row in df.iterrows():
            sreg = row.get(sreg_col, REGION) if sreg_col else REGION
            sec  = row.get("supplying_sector", "Unknown")
            dw   = _apply(row[col], col, FACTORS) * dep_factor(col, sreg, sec)
            rows.append((sec, dw))
        s = pd.Series(dict(rows))
        return s.groupby(s.index).sum()

    def _dw_grouped(df, group_col, sreg_col=None):
        if df.empty or col not in df.columns: return pd.Series(dtype=float)
        result = {}
        for _, row in df.iterrows():
            key  = row.get(group_col, "Unknown")
            sreg = row.get(sreg_col, REGION) if sreg_col else REGION
            sec  = row.get("supplying_sector", "Unknown")
            dw   = _apply(row[col], col, FACTORS) * dep_factor(col, sreg, sec)
            result[key] = result.get(key, 0) + dw
        return pd.Series(result)

    t0_dw = _dw_row(t0)
    t1_dw = _dw_grouped(t1, "sourcing_region", "sourcing_region")
    t2_dw = _dw_row(t2)
    t3_dw = _dw_row(t3)

    grand = sum(s.sum() for s in [t0_dw, t1_dw, t2_dw, t3_dw] if not s.empty)

    df0 = TIER_DEP["t0"][col]
    df1 = TIER_DEP["t1"][col]
    df2 = TIER_DEP["t2"][col]
    df3 = TIER_DEP["t3"][col]

    def _darken(hex_col, factor):
        import re
        h = hex_col.lstrip("#")
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        r = min(255, max(0, int(r * (2 - factor))))
        g = min(255, max(0, int(g * (2 - factor))))
        b = min(255, max(0, int(b * (2 - factor))))
        return f"#{r:02x}{g:02x}{b:02x}"

    i0 = node("Tier 0\\nDirect CAPEX",      _darken(TIER_NODE["t0"], df0))
    i1 = node("Tier 1\\nBilateral",         _darken(TIER_NODE["t1"], df1))
    i2 = node("Tier 2\\nUpstream",          _darken(TIER_NODE["t2"], df2))
    i3 = node("Tier 3-10\\nDeep Upstream",  _darken(TIER_NODE["t3"], df3))
    term = node(f"{sname}\\n{grand:,.0f} {sunit}\\n(dep-weighted)", s_col)

    def add_flows(tier_idx, breakdown, tk):
        for name, v in _top_n(breakdown).items():
            mid = node(name, INTER[tk])
            src_l.extend([tier_idx, mid]); tgt_l.extend([mid, term])
            val_l.extend([v, v]);          lc_l.extend([TIER_LINK[tk]]*2)

    add_flows(i0, t0_dw, "t0")
    add_flows(i1, t1_dw, "t1")
    if t2_dw.sum() > 0: add_flows(i2, t2_dw, "t2")
    if t3_dw.sum() > 0: add_flows(i3, t3_dw, "t3")

    return dict(nodes=nodes, nc=nc, src=src_l, tgt=tgt_l, val=val_l, lc=lc_l,
                grand=grand, sname=sname, sunit=sunit, s_col=s_col, ssign=ssign)

n_s, gap = len(STRESSORS), 0.03
w = (1.0 - gap*(n_s-1)) / n_s
fig_sk = go.Figure()

for i, (col, *_) in enumerate(STRESSORS):
    d   = _dep_sankey(col)
    x0  = i*(w+gap); x1 = x0+w
    fig_sk.add_trace(go.Sankey(
        domain=dict(x=[x0,x1], y=[0,0.90]),
        arrangement="snap",
        node=dict(label=d["nodes"], color=d["nc"], pad=14, thickness=18,
                  line=dict(color="white", width=0.4)),
        link=dict(source=d["src"], target=d["tgt"],
                  value=d["val"], color=d["lc"]),
    ))
    fig_sk.add_annotation(
        x=(x0+x1)/2, y=1.0, xref="paper", yref="paper",
        text=(f"<b>{d['ssign']} {d['sname']}</b><br>"
              f"<span style='font-size:11px;color:{d['s_col']}'>"
              f"{d['grand']:,.0f} {d['sunit']} dep-wtd</span>"),
        showarrow=False, font=dict(size=13), align="center")

fig_sk.update_layout(
    title=dict(
        text=(f"<b>Dependency-Weighted Supply-Chain Sankey — {sc_label}</b>"
              f"<br><span style='font-size:11px;color:#555'>"
              f"Flow values = scenario_adj x dep_factor(tier,region,sector) | "
              f"Darker nodes = higher dep_factor</span>"),
        x=0.01, xanchor="left", font=dict(size=14)),
    height=600,
    margin=dict(l=20, r=20, t=105, b=20),
    paper_bgcolor="#fafafa", font=dict(family="Arial", size=10),
)
display(HTML(fig_sk.to_html(full_html=False, include_plotlyjs="cdn")))
"""

# ─────────────────────────────────────────────────────────────────────────────
C10_THREELAYER = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 5 — THREE-LAYER TIER COMPARISON
# For each tier: Raw | Scenario-Adjusted | Dependency-Weighted
# GHG (bars, left axis) + Employment (line, right axis).
# ══════════════════════════════════════════════════════════════════
_tier_keys  = ["t0","t1","t2","t3"]
_tier_short = ["T0 Direct","T1 Bilateral","T2 Upstream","T3-10 Deep"]
_layers = [
    ("raw", "Raw (Baseline)",        0.45, "///"),
    ("adj", f"Adj ({sc_label})",     0.70, None),
    ("dep", "Dep-Weighted",          1.00, None),
]
_layer_offsets = [-0.22, 0, 0.22]
_ghg_bar_colors = ["#aec7e8", "#6baed6", "#2171b5"]
_emp_marker_symbols = ["circle-open", "circle", "diamond"]

fig_3l = make_subplots(specs=[[{"secondary_y": True}]])

for li, (layer, lname, alpha, pattern) in enumerate(_layers):
    ghg_vals = [SUMMARY[tk][layer]["GHG_tCO2e"] for tk in _tier_keys]
    emp_vals = [SUMMARY[tk][layer]["Employment_FTE"] for tk in _tier_keys]

    fig_3l.add_trace(go.Bar(
        name=lname,
        x=_tier_short,
        y=ghg_vals,
        marker_color=_ghg_bar_colors[li],
        opacity=alpha,
        text=[f"{v:,.0f}" if v > 0 else "" for v in ghg_vals],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=8, color="white"),
        offsetgroup=li,
    ), secondary_y=False)

    fig_3l.add_trace(go.Scatter(
        name=f"Employment {lname}",
        x=_tier_short, y=emp_vals,
        mode="lines+markers+text",
        line=dict(color=["#a1d99b","#41ab5d","#006d2c"][li],
                  width=2, dash=["dash","dot","solid"][li]),
        marker=dict(size=8, symbol=_emp_marker_symbols[li]),
        text=[f"{v:,.0f}" if v > 0 else "" for v in emp_vals],
        textposition="top center", textfont=dict(size=8),
        showlegend=True,
    ), secondary_y=True)

fig_3l.update_layout(
    title=dict(
        text=(f"<b>Three-Layer Tier Comparison</b>"
              f"<br><span style='font-size:11px;color:#555'>"
              f"GHG bars [-] (left) · Employment lines [+] (right) · "
              f"{fmt_capex(CAPEX_USD)} · {COUNTRY}</span>"),
        x=0.01, xanchor="left", font=dict(size=14)),
    barmode="group",
    height=440,
    legend=dict(orientation="h", y=1.14, font=dict(size=9)),
    margin=dict(l=80, r=80, t=110, b=60),
    paper_bgcolor="#fafafa", font=dict(family="Arial", size=11),
)
fig_3l.update_yaxes(title_text="GHG tCO2e [-]", secondary_y=False, title_font_color="#d62728")
fig_3l.update_yaxes(title_text="Employment FTE [+]", secondary_y=True, title_font_color="#2ca02c")
display(HTML(fig_3l.to_html(full_html=False, include_plotlyjs="cdn")))
"""

# ─────────────────────────────────────────────────────────────────────────────
C11_BILATERAL = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 6 — T1 BILATERAL SOURCING × NATURE RISK
# Bars = dep-weighted GHG by sourcing region.
# Bar colour = WRF physical score (green-yellow-red scale).
# Scatter = raw GHG (open circles) to show dep amplification.
# ══════════════════════════════════════════════════════════════════
if t1.empty or "sourcing_region" not in t1.columns:
    print("No Tier 1 bilateral data available.")
else:
    _t1_raw_by_reg  = (t1.groupby("sourcing_region")["GHG_tCO2e"]
                         .sum()
                         .apply(lambda v: _apply(v, "GHG_tCO2e", FACTORS)))
    _t1_dep_by_reg  = {}
    for reg, grp in t1.groupby("sourcing_region"):
        dw = sum(
            _apply(row["GHG_tCO2e"], "GHG_tCO2e", FACTORS)
            * dep_factor("GHG_tCO2e", reg, row["supplying_sector"])
            for _, row in grp.iterrows()
        )
        _t1_dep_by_reg[reg] = dw
    _t1_dep_ser = pd.Series(_t1_dep_by_reg).sort_values(ascending=True)

    _wrf_scores = {reg: get_wwf(reg).get("wrf_physical", DEP_NEUTRAL)
                   for reg in _t1_dep_ser.index}
    _max_wrf    = max(_wrf_scores.values()) or 1

    def _wrf_color(score):
        t = min(1.0, score / 5.0)
        r = int(255 * t);  g = int(180 * (1 - t)); b = 50
        return f"rgb({r},{g},{b})"

    bar_colors = [_wrf_color(_wrf_scores[r]) for r in _t1_dep_ser.index]

    fig_bil = go.Figure()
    fig_bil.add_trace(go.Bar(
        name="Dep-Weighted GHG",
        x=_t1_dep_ser.values, y=_t1_dep_ser.index,
        orientation="h",
        marker_color=bar_colors, marker_line_color="white", marker_line_width=1,
        text=[f"{v:,.0f}" for v in _t1_dep_ser.values],
        textposition="outside",
        textfont=dict(size=9),
    ))
    # Raw GHG overlay
    _raw_aligned = _t1_raw_by_reg.reindex(_t1_dep_ser.index, fill_value=0)
    fig_bil.add_trace(go.Scatter(
        name="Adj GHG (no dep)",
        x=_raw_aligned.values, y=_t1_dep_ser.index,
        mode="markers",
        marker=dict(symbol="line-ns", size=14, color="#333",
                    line=dict(width=2, color="#333")),
    ))

    # Colourbar legend
    fig_bil.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker=dict(
            colorscale=[[0,"#00b450"],[0.5,"#fdae00"],[1.0,"#d62728"]],
            showscale=True,
            colorbar=dict(title="WRF Physical", x=1.02,
                          tickvals=[0,2.5,5], ticktext=["Low","Med","High"]),
            cmin=0, cmax=5,
            color=[_wrf_scores[r] for r in _t1_dep_ser.index],
            size=8,
        ),
        showlegend=False,
    ))

    fig_bil.update_layout(
        title=dict(
            text=(f"<b>Tier 1 Bilateral × Nature Risk</b>"
                  f"<br><span style='font-size:11px;color:#555'>"
                  f"Bar = dep-weighted GHG | Bar colour = WRF physical score | "
                  f"Vertical line = adj GHG without dep weight</span>"),
            x=0.01, xanchor="left", font=dict(size=14)),
        xaxis_title="GHG tCO2e",
        height=360,
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=100, r=80, t=100, b=50),
        paper_bgcolor="#fafafa", font=dict(family="Arial", size=11),
    )
    display(HTML(fig_bil.to_html(full_html=False, include_plotlyjs="cdn")))
"""

# ─────────────────────────────────────────────────────────────────────────────
C12_DASH = """\
# ══════════════════════════════════════════════════════════════════
# SECTION 7 — STATIC SUMMARY DASHBOARD  (Matplotlib)
# Three-layer tiered funnel (raw / adj / dep-weighted) + 4 panels.
# ══════════════════════════════════════════════════════════════════
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Polygon
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

TIER_COLORS_MPL = ["#4e79a7","#f28e2b","#59a14f","#b07aa1"]
LAYER_COLORS    = {"raw": "#aec7e8", "adj": "#4e79a7", "dep": "#08306b"}
LAYER_LABELS    = {"raw": "Raw", "adj": f"Adj ({sc_label})", "dep": "Dep-Weighted"}
_tier_keys  = ["t0","t1","t2","t3"]
_tier_short = ["Tier 0\nDirect","Tier 1\nBilateral","Tier 2\nUpstream","Tier 3-10\nDeep"]

# ── Layout ─────────────────────────────────────────────────────────────────
fig_d = plt.figure(figsize=(18, 9), facecolor="#fafafa")
fig_d.suptitle(
    (f"Dependency-Extended Impact Dashboard  |  {fmt_capex(CAPEX_USD)}  |  "
     f"{COUNTRY} ({REGION})  |  {SECTOR}  |  {sc_label}"),
    fontsize=11, fontweight="bold", y=0.99, color="#2c3e50",
)
gs = gridspec.GridSpec(
    2, 3, figure=fig_d,
    left=0.04, right=0.97, top=0.93, bottom=0.07,
    hspace=0.52, wspace=0.40,
    width_ratios=[1.6, 1, 1],
)
ax_funnel = fig_d.add_subplot(gs[:, 0])   # left full-height: three-layer funnel
ax_df     = fig_d.add_subplot(gs[0, 1])   # top-mid: dep factor by tier
ax_ssp    = fig_d.add_subplot(gs[0, 2])   # top-right: SSP comparison
ax_enc    = fig_d.add_subplot(gs[1, 1])   # bot-mid: ENCORE top-6 dep
ax_bilat  = fig_d.add_subplot(gs[1, 2])   # bot-right: T1 bilateral

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 1 — Three-Layer Tiered GHG Funnel
# For each tier: three horizontally-grouped bars (raw / adj / dep-weighted)
# sorted T0 at top.
# ═══════════════════════════════════════════════════════════════════════════
_col = "GHG_tCO2e"
_ghg_max = max(
    SUMMARY[tk][layer][_col]
    for tk in _tier_keys for layer in ["raw","adj","dep"]
) or 1

ax_funnel.set_xlim(-1.15, 1.15)
ax_funnel.set_ylim(-1.1, len(_tier_keys) + 0.3)
ax_funnel.axis("off")
ax_funnel.set_title("GHG Three-Layer Tiered Funnel  [-]",
                     fontsize=10, fontweight="bold", pad=4, color="#333", loc="left")

# y positions: T0 at top
y_base = list(range(len(_tier_keys)-1, -1, -1))
bar_h  = 0.20
layer_offsets = {"raw": 0.20, "adj": 0, "dep": -0.20}

# Trapezia using dep-weighted widths (widest = dep, to emphasise risk)
dep_widths = [(SUMMARY[tk]["dep"][_col] / _ghg_max) * 0.88
               for tk in _tier_keys]
for i in range(len(_tier_keys) - 1):
    yi_top = y_base[i]   + layer_offsets["dep"] - bar_h/2
    yi_bot = y_base[i+1] + layer_offsets["dep"] + bar_h/2 + 0.01
    hw_hi  = dep_widths[i]
    hw_lo  = dep_widths[i+1]
    trap = Polygon(
        [(-hw_hi, yi_top),( hw_hi, yi_top),
         ( hw_lo, yi_bot),(-hw_lo, yi_bot)],
        closed=True, facecolor="#dde", edgecolor="none", alpha=0.3, zorder=0
    )
    ax_funnel.add_patch(trap)

for yi, tk, tc in zip(y_base, _tier_keys, TIER_COLORS_MPL):
    label = _tier_short[y_base.index(yi)]
    ax_funnel.text(-1.12, yi, label,
                   ha="left", va="center", fontsize=8.5, color="#444")
    for layer, offset in layer_offsets.items():
        v  = SUMMARY[tk][layer][_col]
        hw = (v / _ghg_max) * 0.88
        lc = LAYER_COLORS[layer]
        rect = FancyBboxPatch(
            (-hw, yi + offset - bar_h/2), 2*hw, bar_h,
            boxstyle="round,pad=0.01",
            facecolor=lc, edgecolor="white", linewidth=1.2,
            alpha=0.90, zorder=1,
        )
        ax_funnel.add_patch(rect)
        if hw > 0.18:
            ax_funnel.text(0, yi + offset,
                           f"{v:,.0f}",
                           ha="center", va="center",
                           fontsize=7.5, color="white",
                           fontweight="bold", zorder=2)

# Legend
for layer, lc in LAYER_COLORS.items():
    ax_funnel.add_patch(
        mpatches.Patch(facecolor=lc, label=LAYER_LABELS[layer], alpha=0.90)
    )
ax_funnel.legend(loc="upper right", fontsize=8, framealpha=0.7,
                  bbox_to_anchor=(1.0, 1.0))

ax_funnel.axhline(-0.52, xmin=0.04, xmax=0.96, color="#aaa", linewidth=0.9, linestyle="--")
grand_dep = GRAND["dep"][_col]
grand_adj = GRAND["adj"][_col]
ax_funnel.text(0, -0.78,
               f"Dep-Weighted Total: {grand_dep:,.0f}  /  Adj Total: {grand_adj:,.0f} tCO2e",
               ha="center", va="center", fontsize=9, fontweight="bold", color="#08306b")

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 2 — Dep Factor by Tier
# ═══════════════════════════════════════════════════════════════════════════
_str3_pairs = [("GHG_tCO2e","#d62728"),("Employment_FTE","#2ca02c"),("Water_1000m3","#1f77b4")]
_x     = np.arange(len(_tier_keys))
_width = 0.25

for si, (sc, sc_col) in enumerate(_str3_pairs):
    df_vals = [TIER_DEP[tk][sc] for tk in _tier_keys]
    ax_df.bar(_x + si*_width, df_vals, _width,
              color=sc_col, alpha=0.80, label=sc.split("_")[0])

ax_df.axhline(1.0, color="#333", linewidth=1.5, linestyle="--", label="Neutral")
ax_df.set_xticks(_x + _width)
ax_df.set_xticklabels(["T0","T1","T2","T3-10"], fontsize=8.5)
ax_df.set_ylabel("dep_factor", fontsize=8)
ax_df.set_title("Dep Factor by Tier", fontsize=10, fontweight="bold")
ax_df.legend(fontsize=7.5, loc="upper right")
ax_df.spines[["top","right"]].set_visible(False)
ax_df.axhspan(1.0, ax_df.get_ylim()[1] if ax_df.get_ylim()[1] > 1.0 else 1.5,
               alpha=0.06, color="red")

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 3 — SSP GHG Comparison (dep-weighted)
# ═══════════════════════════════════════════════════════════════════════════
_ssps_ok = [s for s in ALL_SSPS if ALL_FACTORS.get(s)]
if COMPARE_SSPS and _ssps_ok:
    def _dep_total(col, f):
        return sum(
            _apply(df[col].sum() if col in df.columns else 0, col, f)
            * TIER_DEP[tk][col]
            for (tk, _, df) in TIER_DEFS
        )
    _ssp_lbl = ["Baseline"] + _ssps_ok
    _ssp_dep = ([_dep_total("GHG_tCO2e", None)] +
                [_dep_total("GHG_tCO2e", ALL_FACTORS[s]) for s in _ssps_ok])
    _ssp_adj = ([GRAND["adj"]["GHG_tCO2e"]] +
                [sum(_apply(df["GHG_tCO2e"].sum() if "GHG_tCO2e" in df.columns else 0,
                            "GHG_tCO2e", ALL_FACTORS[s])
                     for _,_,df in TIER_DEFS)
                 for s in _ssps_ok])
    _ssp_clr = ["#7f7f7f"] + [SSP_COLORS[s] for s in _ssps_ok]
    x_ssp = np.arange(len(_ssp_lbl))

    ax_ssp.bar(x_ssp - 0.18, _ssp_adj, 0.36, color=_ssp_clr, alpha=0.55, label="Adj")
    ax_ssp.bar(x_ssp + 0.18, _ssp_dep, 0.36, color=_ssp_clr, alpha=0.90, label="Dep-Wtd")
    ax_ssp.set_xticks(x_ssp)
    ax_ssp.set_xticklabels(_ssp_lbl, fontsize=6.5, rotation=22, ha="right")
    ax_ssp.set_ylabel("GHG tCO2e [-]", fontsize=8, color="#d62728")
    ax_ssp.set_title(f"SSP GHG (Adj vs Dep-Wtd) at {FOCUS_YEAR}", fontsize=10, fontweight="bold")
    ax_ssp.legend(fontsize=8)
    ax_ssp.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"{x:,.0f}"))
    ax_ssp.spines[["top","right"]].set_visible(False)
else:
    ax_ssp.text(0.5, 0.5, "No scenario\ndata", ha="center", va="center",
                transform=ax_ssp.transAxes, fontsize=11, color="#aaa")
    ax_ssp.axis("off")

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 4 — ENCORE Top-6 Dependency Services
# ═══════════════════════════════════════════════════════════════════════════
_enc_profile = get_materiality_profile(ENCORE_SECTOR)
_enc_table   = _enc_profile.summary_table()[:6]  # already sorted desc
_enc_labels  = [r["ecosystem_service"].replace("_"," ").title()[:28]
                for r in reversed(_enc_table)]
_enc_dep     = [r["dependency_score"] for r in reversed(_enc_table)]
_enc_imp     = [r["impact_score"]     for r in reversed(_enc_table)]

_enc_colors  = ["#e6550d" if d >= 4 else "#fdae6b" if d >= 3 else "#74c476"
                for d in _enc_dep]
ax_enc.barh(_enc_labels, _enc_dep, color=_enc_colors, alpha=0.88, label="Dependency")
ax_enc.barh(_enc_labels, _enc_imp, color="#aaa", alpha=0.35, label="Impact", left=[0]*len(_enc_dep))
ax_enc.axvline(3.0, color="#555", linewidth=0.8, linestyle="--")
ax_enc.axvline(4.0, color="#d62728", linewidth=0.8, linestyle=":")
ax_enc.set_xlabel("ENCORE Score (1-5)", fontsize=8)
ax_enc.set_title("ENCORE Top-6 Dep Services", fontsize=10, fontweight="bold")
ax_enc.set_xlim(0, 5.5)
ax_enc.legend(fontsize=7.5, loc="lower right")
ax_enc.tick_params(axis="y", labelsize=7.5)
ax_enc.spines[["top","right"]].set_visible(False)

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 5 — T1 Bilateral Dep-Weighted GHG (top 6)
# ═══════════════════════════════════════════════════════════════════════════
if not t1.empty and "sourcing_region" in t1.columns:
    _t1d = {}
    for reg, grp in t1.groupby("sourcing_region"):
        _t1d[reg] = sum(
            _apply(row["GHG_tCO2e"], "GHG_tCO2e", FACTORS)
            * dep_factor("GHG_tCO2e", reg, row["supplying_sector"])
            for _, row in grp.iterrows()
        )
    _t1d_ser = pd.Series(_t1d).sort_values(ascending=True).tail(6)
    _wrf_v   = [get_wwf(r).get("wrf_physical", DEP_NEUTRAL) for r in _t1d_ser.index]
    _bil_c   = sns.color_palette("Blues_d", len(_t1d_ser))
    ax_bilat.barh(_t1d_ser.index, _t1d_ser.values, color=_bil_c, alpha=0.88)
    for i, (n, v) in enumerate(_t1d_ser.items()):
        ax_bilat.text(v*1.02, i, f"{v:,.0f} (WRF:{_wrf_v[i]:.1f})",
                      va="center", fontsize=7.5, color="#333")
    ax_bilat.set_xlabel("Dep-Weighted GHG tCO2e [-]", fontsize=8)
    ax_bilat.set_title("T1 Bilateral Dep-Weighted (top 6)", fontsize=10, fontweight="bold")
    ax_bilat.tick_params(axis="y", labelsize=8)
    ax_bilat.spines[["top","right"]].set_visible(False)
else:
    ax_bilat.text(0.5, 0.5, "No T1 data", ha="center", va="center",
                  transform=ax_bilat.transAxes, color="#aaa")
    ax_bilat.axis("off")

# ── Save ───────────────────────────────────────────────────────────────────
_slug = (f"dep_dashboard_{SECTOR}_{REGION}_"
         f"{fmt_capex(CAPEX_USD).replace('$','').replace('.','p')}"
         f"{'_'+SCENARIO.replace('.','').replace('-','') if SCENARIO else ''}.png")
RESULTS_DIR.mkdir(exist_ok=True)
fig_d.savefig(RESULTS_DIR / _slug, dpi=150, bbox_inches="tight", facecolor="#fafafa")
plt.tight_layout()
plt.show()
print(f"Dashboard saved -> results/{_slug}")
"""

# ─────────────────────────────────────────────────────────────────────────────
cells = [
    md_cell("# Investment Dependency Analysis\n\n"
            "Extends the supply-chain IO analysis with the full three-component "
            "nature-related dependency layer:\n\n"
            "- **ENCORE** — ecosystem service dependency of the project sector\n"
            "- **WWF Risk Filter** — WRF / BRF scores for each sourcing region\n"
            "- **SC-sector sensitivity** — per-supplying-sector nature dependency profile\n\n"
            "**dep_factor = (ENCORE/3 + WWF/3 + SC/3) / 3** — neutral = 1.0, "
            "range ≈ 0.33–1.67.  "
            "Each tier's stressors are multiplied by this factor to yield "
            "**dependency-weighted impacts**.\n\n"
            "Sections 1-6 use Plotly (interactive exploration); "
            "Section 7 is a static Matplotlib dashboard."),
    code_cell(C1_PARAMS),
    code_cell(C2_IMPORTS),
    code_cell(C3_IO),
    code_cell(C4_DEP),
    code_cell(C5_LEGEND),
    code_cell(C6_ENCORE),
    code_cell(C7_WWF),
    code_cell(C8_DEP_FACTOR),
    code_cell(C9_SANKEY),
    code_cell(C10_THREELAYER),
    code_cell(C11_BILATERAL),
    code_cell(C12_DASH),
]

import uuid
for i, c in enumerate(cells):
    c["id"] = str(uuid.uuid4())[:8]

nb = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
        "language_info": {"name":"python","version":"3.11.0"},
    },
    "cells": cells,
}

with open("/home/deuler/tvp5/project_assessment/investment_dependency.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

print("Notebook written.")
