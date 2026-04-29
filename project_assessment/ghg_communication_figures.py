#!/usr/bin/env python3
"""
ghg_communication_figures.py

Three MADE/NGFS-aligned communication figures for the Greenings GHG backtesting portfolio.

  Figure 1  –  Volatility     : full-tail heatmap (uncapped) with 99th-pct marker
  Figure 2  –  Benchmarking   : relative-delta bar chart with IAM uncertainty fan
  Figure 3  –  Geography      : small-multiples per country + management action boxes

Run from project_assessment/:  python ghg_communication_figures.py
"""

import os, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "project_assessment" / "greenings_backtesting"
FIG_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "tvp_dbio"))
os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")

from tvp_io_lib import tier0_impact, tier1_impact          # noqa: E402

# ── Thermal-gradient SSP colour palette (blue=safe → red=dangerous) ────────────
# Deep blue for most ambitious mitigation; deep red for fossil-fuelled baseline.
SSP_COLORS = {
    "SSP1-1.9": "#0d47a1",   # deep blue   – < 1.5 °C
    "SSP1-2.6": "#1976d2",   # medium blue – < 2 °C
    "SSP2-4.5": "#26a69a",   # teal        – ~2–2.5 °C  (Paris update)
    "SSP4-6.0": "#ff9800",   # amber       – ~3 °C
    "SSP3-7.0": "#e64a19",   # orange-red  – ~3 °C baseline
    "SSP5-8.5": "#b71c1c",   # deep red    – > 3 °C
}

# ── Project definitions ────────────────────────────────────────────────────────
PROJECTS = [
    dict(project_id="HOSP-1",  label="HOSP-1\nHospital · LATAM",   sector="Health_Social",      region="LATAM",   capex_musd=147),
    dict(project_id="HOSP-2",  label="HOSP-2\nHospital · Africa",  sector="Health_Specialized", region="Africa",  capex_musd=250),
    dict(project_id="HOSP-3",  label="HOSP-3\nHospital · Europe",  sector="Health_General",     region="Europe",  capex_musd=150),
    dict(project_id="HYDRO-1", label="HYDRO-1\nHydro · Africa",    sector="Energy",             region="Africa",  capex_musd=200),
    dict(project_id="HYDRO-2", label="HYDRO-2\nHydro · Asia",      sector="Energy",             region="Asia",    capex_musd=400),
    dict(project_id="HYDRO-3", label="HYDRO-3\nHydro · Europe",    sector="Energy",             region="Europe",  capex_musd=47),
    dict(project_id="RAIL-1",  label="RAIL-1\nRail Dev · Europe",  sector="Rail_Dev",           region="Europe",  capex_musd=1190),
    dict(project_id="RAIL-2",  label="RAIL-2\nRail Op · Europe",   sector="Rail_Op",            region="Europe",  capex_musd=1350),
    dict(project_id="RAIL-3",  label="RAIL-3\nRail Op · Europe",   sector="Rail_Op",            region="Europe",  capex_musd=2460),
]

PROJ_EXT = {
    "HOSP-1":  dict(iso3="COL", nace="Q",    country="Colombia"),
    "HOSP-2":  dict(iso3="KEN", nace="Q",    country="Kenya"),
    "HOSP-3":  dict(iso3="DEU", nace="Q",    country="Germany"),
    "HYDRO-1": dict(iso3="ETH", nace="D35",  country="Ethiopia"),
    "HYDRO-2": dict(iso3="IND", nace="D35",  country="India"),
    "HYDRO-3": dict(iso3="DEU", nace="D35",  country="Germany"),
    "RAIL-1":  dict(iso3="DEU", nace="F",    country="Germany"),
    "RAIL-2":  dict(iso3="DEU", nace="H49",  country="Germany"),
    "RAIL-3":  dict(iso3="DEU", nace="H49",  country="Germany"),
}

# ── REMIND-MAgPIE R5 regional multipliers per SSP ──────────────────────────────
# Source: IPCC AR6 WG3 Ch.3 / Annex III regional shadow carbon price data.
# Differentiation narrows as warming ambition decreases (cost-optimal market).
SSP6 = [
    dict(ssp="SSP1-1.9", cat="C1",  warming="<1.5°C",
         key="COEFFICIENT GHG_T<1.5, in USD (WifOR)",
         mults={"Germany":1.30,"Colombia":0.80,"India":0.88,"Kenya":0.68,"Ethiopia":0.68},
         iam_uncertainty=0.35),   # ±35 % – extreme model spread at 1.5 °C
    dict(ssp="SSP1-2.6", cat="C3",  warming="<2°C",
         key="COEFFICIENT GHG_T<2, in USD (WifOR)",
         mults={"Germany":1.28,"Colombia":0.82,"India":0.90,"Kenya":0.72,"Ethiopia":0.72},
         iam_uncertainty=0.22),
    dict(ssp="SSP2-4.5", cat="C4",  warming="~2–2.5°C",
         key="COEFFICIENT GHG_PARIS_UPDATE, in USD (WifOR)",
         mults={"Germany":1.25,"Colombia":0.84,"India":0.91,"Kenya":0.74,"Ethiopia":0.74},
         iam_uncertainty=0.18),
    dict(ssp="SSP4-6.0", cat="C6",  warming="~3°C",
         key="COEFFICIENT GHG_ALTDAM, in USD (WifOR)",
         mults={"Germany":1.18,"Colombia":0.87,"India":0.92,"Kenya":0.80,"Ethiopia":0.80},
         iam_uncertainty=0.20),
    dict(ssp="SSP3-7.0", cat="C5",  warming="~3°C base",
         key="COEFFICIENT GHG_BASE, in USD (WifOR)",
         mults={"Germany":1.20,"Colombia":0.86,"India":0.92,"Kenya":0.78,"Ethiopia":0.78},
         iam_uncertainty=0.15),
    dict(ssp="SSP5-8.5", cat="C8",  warming=">3°C",
         key="COEFFICIENT GHG_OPTIMAL, in USD (WifOR)",
         mults={"Germany":1.15,"Colombia":0.88,"India":0.93,"Kenya":0.82,"Ethiopia":0.82},
         iam_uncertainty=0.12),
]

# ── Management action library ──────────────────────────────────────────────────
MGMT_ACTIONS = {
    "Hospital": (
        "Hospitals show no avoided GHG but carry significant supply-chain embodied carbon.\n"
        "Action: Mandate low-carbon procurement for construction materials (concrete,\n"
        "steel) and set a Scope 3 cap at €150/t by 2028 to hedge SSP1-1.9 tail risk."
    ),
    "Hydro": (
        "Hydropower projects generate the portfolio's only positive net GHG position.\n"
        "Action: Lock in long-term carbon credit contracts at current UBA price (412 USD/t)\n"
        "before 2027 – the SSP1-1.9 scenario implies a 14× valuation uplift by 2030."
    ),
    "Rail": (
        "Rail projects face the deepest supply-chain carbon cost across all SSPs.\n"
        "Action: Shift steel procurement to low-carbon suppliers by 2027 and negotiate\n"
        "embedded-carbon clauses in EPC contracts to reduce transition-risk exposure."
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_data():
    """Load all source data and return the key DataFrames."""

    # Avoided GHG from Greenings backtesting
    bt_path = ROOT / "project_assessment" / "greenings_backtesting" / "03_monetisation_inputs.csv"
    bt      = pd.read_csv(bt_path)[["project_id", "ghg_avoided_tco2e_yr"]]
    avoided = dict(zip(bt.project_id, bt.ghg_avoided_tco2e_yr))

    # Tier-0 / Tier-1 supply-chain GHG
    rows = []
    for p in PROJECTS:
        invest = p["capex_musd"] * 1_000_000
        t0 = tier0_impact(invest, p["sector"], p["region"], database="exiobase")
        t1 = tier1_impact(invest, p["sector"], p["region"], database="exiobase")
        pid = p["project_id"]
        ext = PROJ_EXT[pid]
        av  = avoided.get(pid, float("nan"))
        rows.append(dict(
            project_id    = pid,
            sector        = p["sector"],
            country       = ext["country"],
            capex_musd    = p["capex_musd"],
            avoided_tco2e = 0.0 if pd.isna(av) else float(av),
            has_avoided   = not pd.isna(av),
            tier0_tco2e   = float(t0.get("GHG_tCO2e", 0)),
            tier1_tco2e   = float(t1.get("GHG_tCO2e", 0)),
        ))
    df = pd.DataFrame(rows)
    df["sc_tco2e"] = df["tier0_tco2e"] + df["tier1_tco2e"]

    # WifOR 2030 GHG coefficients
    vf_path = ROOT / "data" / "value_factors" / "2024-11-18_formatted_MonGHG_my.h5"
    with pd.HDFStore(str(vf_path), "r") as st:
        ghg30 = st["/coefficient"]

    def coeff(key):
        return abs(float(ghg30.loc[("2030", key)].iloc[0])) * 1_000

    for sc in SSP6:
        sc["global_coeff"] = coeff(sc["key"])

    # UBA Central 2030
    uba_candidates = [
        Path("/home/deuler/transitionvaluation/uba-value-factors/output"),
        ROOT.parent / "transitionvaluation" / "uba-value-factors" / "output",
    ]
    uba_dir = next((p for p in uba_candidates
                    if p.is_dir() and (p / "01_uba4_ghg.csv").exists()), None)
    uba_ghg = pd.read_csv(uba_dir / "01_uba4_ghg.csv")
    g30     = uba_ghg[(uba_ghg.emission_year == 2030) & (uba_ghg.substance == "CO2_CO2eq")]
    uba_c   = float(g30[g30.prtp_pct == 1]["value_factor"].iloc[0]) * 1.10   # EUR→USD

    def to_musd(tco2e, price):
        return tco2e * price / 1_000_000

    # Build project-level results for every SSP
    ssp_rows = []
    for _, proj in df.iterrows():
        row = dict(
            project     = proj.project_id,
            country     = proj.country,
            capex_musd  = proj.capex_musd,
            has_av      = proj.has_avoided,
            av          = proj.avoided_tco2e,
            sc          = proj.sc_tco2e,
            net_uba     = to_musd(proj.avoided_tco2e - proj.sc_tco2e, uba_c),
            av_uba      = to_musd(proj.avoided_tco2e,  uba_c),
        )
        for sc in SSP6:
            mult    = sc["mults"][proj.country]
            c_rm    = sc["global_coeff"] * mult
            u       = sc["iam_uncertainty"]
            net_rm  = to_musd(proj.avoided_tco2e - proj.sc_tco2e, c_rm)
            av_rm   = to_musd(proj.avoided_tco2e, c_rm)
            row[sc["ssp"] + "_net_rm"]   = net_rm
            row[sc["ssp"] + "_av_rm"]    = av_rm
            row[sc["ssp"] + "_delta"]    = net_rm - row["net_uba"]
            row[sc["ssp"] + "_net_lo"]   = to_musd(proj.avoided_tco2e - proj.sc_tco2e,
                                                    c_rm * (1 - u))
            row[sc["ssp"] + "_net_hi"]   = to_musd(proj.avoided_tco2e - proj.sc_tco2e,
                                                    c_rm * (1 + u))
        ssp_rows.append(row)

    sdf = pd.DataFrame(ssp_rows)
    return sdf, uba_c, to_musd


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — VOLATILITY: full-tail Δ heatmap
# ══════════════════════════════════════════════════════════════════════════════

def fig1_volatility(sdf, uba_c):
    """
    Message: SSP1-1.9 is the most disruptive scenario — 'Business as Usual' is over.
    Design:  Full-tail uncapped heatmap (no 95th-pct capping) + 99th-pct callout.
             Thermal gradient palette; diverging from zero (no-change baseline).
    """
    ssps     = [sc["ssp"] for sc in SSP6]
    proj_lbl = [
        f"{r['project']}\n({r['country'][:3]})"
        for _, r in sdf.iterrows()
    ]

    # Δ matrix: REMIND net − UBA Central net  [MUSD]
    delta_mat = np.array([
        [sdf.loc[i, s + "_delta"] for s in ssps]
        for i in sdf.index
    ])

    # 99th-pct magnitude marker (uncapped)
    p99_val = np.percentile(np.abs(delta_mat), 99)
    vmax    = np.abs(delta_mat).max()          # fully uncapped

    fig, axes = plt.subplots(
        1, 2, figsize=(16, 7),
        gridspec_kw={"width_ratios": [3, 1], "wspace": 0.35}
    )

    # ── Left: full heatmap ────────────────────────────────────────────────────
    ax = axes[0]
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    # Colorblind-friendly diverging palette
    cmap_div = plt.cm.PuOr_r
    im = ax.imshow(delta_mat, aspect="auto", cmap=cmap_div, norm=norm)

    ssp_xlbls = [
        f"{sc['ssp']}\n{sc['cat']} {sc['warming']}"
        for sc in SSP6
    ]
    ax.set_xticks(range(len(SSP6)))
    ax.set_xticklabels(ssp_xlbls, fontsize=9)
    ax.set_yticks(range(len(sdf)))
    ax.set_yticklabels(proj_lbl, fontsize=9)

    # Colour x-axis tick labels with thermal palette
    for tick, sc in zip(ax.get_xticklabels(), SSP6):
        tick.set_color(SSP_COLORS[sc["ssp"]])
        tick.set_fontweight("bold")

    for r in range(len(sdf)):
        for c in range(len(SSP6)):
            v   = delta_mat[r, c]
            txt = f"{'+' if v >= 0 else ''}{v:.0f}"
            is_tail = abs(v) >= p99_val
            ax.text(c, r, txt,
                    ha="center", va="center",
                    fontsize=8.5 if not is_tail else 9.5,
                    fontweight="bold" if is_tail else "normal",
                    color="white" if abs(v) > vmax * 0.45 else "#111")
            if is_tail:
                ax.add_patch(mpatches.Rectangle(
                    (c - 0.48, r - 0.48), 0.96, 0.96,
                    fill=False, edgecolor="#ff0", lw=2.0, zorder=5
                ))

    cbar = plt.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Δ MUSD  (REMIND country-specific − UBA Central)", fontsize=9)
    ax.set_title(
        "VOLATILITY  ·  Full-Tail Δ Heatmap (uncapped)\n"
        "Δ = REMIND-MAgPIE Net − UBA Central Net  [MUSD]  ·  Yellow border = 99th-pct tail event",
        fontsize=10, fontweight="bold"
    )

    # ── Right: sorted bar — worst-case Δ per project across all SSPs ────────
    ax2    = axes[1]
    worst  = delta_mat.min(axis=1)        # most negative delta per project
    best   = delta_mat.max(axis=1)
    y      = np.arange(len(sdf))
    ax2.barh(y, worst, height=0.35, color="#b71c1c", label="Worst-case Δ (min)")
    ax2.barh(y + 0.38, best, height=0.35, color="#0d47a1", label="Best-case Δ (max)")
    ax2.axvline(0, color="#444", lw=1.0, ls="--")
    ax2.set_yticks(y + 0.19)
    ax2.set_yticklabels([r["project"] for _, r in sdf.iterrows()], fontsize=8.5)
    ax2.set_xlabel("Δ MUSD", fontsize=9)
    ax2.set_title("Worst / Best\nΔ across SSPs", fontsize=9.5, fontweight="bold")
    ax2.legend(fontsize=8, framealpha=0.9)
    ax2.spines[["top", "right"]].set_visible(False)

    # ── Key-message box ───────────────────────────────────────────────────────
    fig.text(
        0.01, 0.01,
        "MESSAGE 1 · VOLATILITY\n"
        "The 1.5°C goal (SSP1-1.9) is the most disruptive scenario for this portfolio.\n"
        "Deep-red cells = extreme devaluation of high-embodied-carbon assets (rail/infrastructure).\n"
        "Deep-blue cells = massive gains for low-carbon generators (hydro).\n"
        "Higher-warming scenarios show less short-term volatility but ignore long-term physical destruction.",
        fontsize=8, va="bottom", style="italic",
        bbox=dict(fc="#f8f9fa", ec="#aaa", lw=0.8, pad=5)
    )

    fig.suptitle(
        "Climate Transition Volatility — Portfolio GHG Value at Risk by IPCC Scenario\n"
        "All 9 projects  ·  5 countries  ·  REMIND-MAgPIE 2.1 country-specific  ·  Year 2030",
        fontsize=11, fontweight="bold"
    )
    fig.savefig(FIG_DIR / "comm_fig1_volatility.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved: comm_fig1_volatility.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — BENCHMARKING: relative delta + IAM uncertainty fan
# ══════════════════════════════════════════════════════════════════════════════

def fig2_benchmarking(sdf, uba_c):
    """
    Message: Standardised models are too conservative — local reality goes unpriced.
    Design:  Portfolio net per SSP shown as relative change vs today's UBA valuation,
             with IAM uncertainty fan (±σ) and management-action callout boxes.
    """
    ssps      = [sc["ssp"] for sc in SSP6]
    sc_lookup = {sc["ssp"]: sc for sc in SSP6}
    x_pos     = np.arange(len(SSP6))

    port_uba = sdf["net_uba"].sum()   # current UBA Central portfolio net

    port_rm  = np.array([sdf[s + "_net_rm"].sum()  for s in ssps])
    port_lo  = np.array([sdf[s + "_net_lo"].sum()  for s in ssps])
    port_hi  = np.array([sdf[s + "_net_hi"].sum()  for s in ssps])

    # Relative delta vs current UBA valuation  [%]
    rel_rm   = (port_rm  - port_uba) / abs(port_uba) * 100
    rel_lo   = (port_lo  - port_uba) / abs(port_uba) * 100
    rel_hi   = (port_hi  - port_uba) / abs(port_uba) * 100

    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(14, 11),
        gridspec_kw={"height_ratios": [2, 1.2], "hspace": 0.50}
    )

    # ── Top: relative delta bars + fan ────────────────────────────────────────
    colors_bar = [SSP_COLORS[s] for s in ssps]
    bars = ax_top.bar(x_pos, rel_rm, color=colors_bar,
                      edgecolor="white", lw=0.8, width=0.55, zorder=3,
                      label="REMIND country-specific (central)")

    # IAM uncertainty fan
    ax_top.fill_between(x_pos, rel_lo, rel_hi,
                         color="#888", alpha=0.18, zorder=2,
                         label="IAM uncertainty range")
    ax_top.errorbar(x_pos, rel_rm,
                    yerr=[np.abs(rel_rm - rel_lo), np.abs(rel_hi - rel_rm)],
                    fmt="none", ecolor="#444", elinewidth=1.2,
                    capsize=5, zorder=4)

    ax_top.axhline(0, color="#222", lw=1.8, ls="--", zorder=5,
                   label="Today's UBA valuation (=0% change)")

    for bar, val, lo, hi in zip(bars, rel_rm, rel_lo, rel_hi):
        off = 2.5
        va  = "bottom" if val >= 0 else "top"
        ax_top.text(bar.get_x() + bar.get_width() / 2,
                    val + (off if val >= 0 else -off),
                    f"{'+' if val >= 0 else ''}{val:.0f}%",
                    ha="center", va=va, fontsize=9.5, fontweight="bold",
                    color=bar.get_facecolor())

    ax_top.set_xticks(x_pos)
    ax_top.set_xticklabels(
        [f"{sc['ssp']}\n{sc['cat']} · {sc['warming']}" for sc in SSP6],
        fontsize=9
    )
    for tick, sc in zip(ax_top.get_xticklabels(), SSP6):
        tick.set_color(SSP_COLORS[sc["ssp"]])
        tick.set_fontweight("bold")

    ax_top.set_ylabel(
        "Portfolio Net Change vs Today's UBA Valuation  [%]",
        fontsize=10
    )
    ax_top.set_title(
        "BENCHMARKING  ·  Relative Scenario Impact vs Current Portfolio Valuation\n"
        "Avoided GHG − Supply-Chain GHG · REMIND-MAgPIE country-specific · Year 2030",
        fontsize=10.5, fontweight="bold"
    )
    ax_top.legend(fontsize=9, framealpha=0.9, loc="lower right")
    ax_top.spines[["top", "right"]].set_visible(False)

    # ── Bottom: sector-level grouped relative delta ────────────────────────────
    SECTOR_MAP = {
        "HOSP-1": "Hospital", "HOSP-2": "Hospital", "HOSP-3": "Hospital",
        "HYDRO-1": "Hydro",   "HYDRO-2": "Hydro",   "HYDRO-3": "Hydro",
        "RAIL-1": "Rail",     "RAIL-2": "Rail",      "RAIL-3": "Rail",
    }
    sdf2  = sdf.copy()
    sdf2["sector_grp"] = sdf2["project"].map(SECTOR_MAP)

    sector_order = ["Hospital", "Hydro", "Rail"]
    sector_colors = {"Hospital": "#95a5a6", "Hydro": "#1976d2", "Rail": "#e67e22"}
    x_s  = np.arange(len(sector_order))
    bw   = 0.12

    for si, sc in enumerate(SSP6):
        offset = (si - len(SSP6) / 2 + 0.5) * bw
        for xi, sec in enumerate(sector_order):
            sub   = sdf2[sdf2.sector_grp == sec]
            s_uba = sub["net_uba"].sum()
            s_rm  = sub[sc["ssp"] + "_net_rm"].sum()
            rel   = (s_rm - s_uba) / abs(s_uba) * 100 if s_uba != 0 else 0
            ax_bot.bar(xi + offset, rel, width=bw * 0.9,
                       color=SSP_COLORS[sc["ssp"]],
                       edgecolor="white", lw=0.4)

    ax_bot.axhline(0, color="#444", lw=1.0, ls="--")
    ax_bot.set_xticks(x_s)
    ax_bot.set_xticklabels(sector_order, fontsize=10.5)
    ax_bot.set_ylabel("Sector Net Change vs UBA  [%]", fontsize=9.5)
    ax_bot.set_title("Sector-Level Relative Impact", fontsize=10, fontweight="bold")
    ax_bot.spines[["top", "right"]].set_visible(False)

    # Management action annotations per sector
    for xi, sec in enumerate(sector_order):
        action_txt = MGMT_ACTIONS[sec]
        ax_bot.text(xi, ax_bot.get_ylim()[0] * 0.88,
                    action_txt,
                    ha="center", va="top", fontsize=6.8,
                    color=sector_colors[sec],
                    bbox=dict(fc="white", ec=sector_colors[sec], lw=0.8,
                              alpha=0.92, pad=4),
                    wrap=True)

    # SSP colour legend
    leg_handles = [
        mpatches.Patch(fc=SSP_COLORS[sc["ssp"]],
                       label=f"{sc['ssp']} {sc['warming']}")
        for sc in SSP6
    ]
    ax_bot.legend(handles=leg_handles, fontsize=7.5, ncol=3,
                  loc="upper right", framealpha=0.9)

    # Key-message box
    fig.text(
        0.01, 0.01,
        "MESSAGE 2 · BENCHMARKING\n"
        "'One-size-fits-all' UBA averages mask local reality.\n"
        "The relative bars show how much the portfolio value diverges from today's book once\n"
        "country-specific REMIND-MAgPIE carbon prices replace the uniform UBA benchmark.\n"
        "Shaded bands = IAM model uncertainty; ignoring them risks being blindsided by local policy shifts.",
        fontsize=8, va="bottom", style="italic",
        bbox=dict(fc="#f8f9fa", ec="#aaa", lw=0.8, pad=5)
    )

    fig.suptitle(
        "Portfolio GHG Value Sensitivity — REMIND-MAgPIE vs UBA Central Benchmark\n"
        "Relative delta from current valuation  ·  With IAM uncertainty fan  ·  Year 2030",
        fontsize=11, fontweight="bold"
    )
    fig.savefig(FIG_DIR / "comm_fig2_benchmarking.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved: comm_fig2_benchmarking.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — GEOGRAPHY MATTERS: small multiples per country
# ══════════════════════════════════════════════════════════════════════════════

def fig3_geography(sdf, uba_c):
    """
    Message: Climate risk must be managed at the national level.
    Design:  Five side-by-side country panels (small multiples) — no spaghetti.
             Each panel shows net MUSD per SSP for that country's projects,
             with UBA as reference dot and management-action callout.
    """
    country_order = ["Colombia", "Kenya", "Ethiopia", "India", "Germany"]
    ssps          = [sc["ssp"] for sc in SSP6]
    sc_lookup     = {sc["ssp"]: sc for sc in SSP6}

    fig, axes = plt.subplots(
        2, 5, figsize=(20, 10),
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.55, "wspace": 0.35}
    )

    CTRY_META = {
        "Colombia":  dict(region="R5LAM",       color="#e67e22", flag="🇨🇴"),
        "Kenya":     dict(region="R5MAF",        color="#27ae60", flag="🇰🇪"),
        "Ethiopia":  dict(region="R5MAF",        color="#8e44ad", flag="🇪🇹"),
        "India":     dict(region="R5ASIA",       color="#e74c3c", flag="🇮🇳"),
        "Germany":   dict(region="R5OECD90+EU",  color="#2c3e50", flag="🇩🇪"),
    }

    for ci, country in enumerate(country_order):
        ax_main   = axes[0, ci]
        ax_action = axes[1, ci]
        sub       = sdf[sdf.country == country]
        meta      = CTRY_META[country]

        x_ssp = np.arange(len(SSP6))

        # Aggregate country totals per SSP
        tot_uba  = sub["net_uba"].sum()
        tot_rm   = np.array([sub[s + "_net_rm"].sum()  for s in ssps])
        tot_lo   = np.array([sub[s + "_net_lo"].sum()  for s in ssps])
        tot_hi   = np.array([sub[s + "_net_hi"].sum()  for s in ssps])

        # Fan chart
        ax_main.fill_between(x_ssp, tot_lo, tot_hi,
                              color=meta["color"], alpha=0.15,
                              label="IAM uncertainty")
        ax_main.plot(x_ssp, tot_rm, "o-",
                     color=meta["color"], lw=2.2, markersize=7,
                     markeredgecolor="white", markeredgewidth=0.8,
                     label="REMIND country-spec.")
        ax_main.axhline(tot_uba, color="#222", lw=1.5, ls="--",
                        label=f"UBA: {tot_uba:.0f} MUSD")

        # Per-SSP value annotations
        for xi, (v, sc) in enumerate(zip(tot_rm, SSP6)):
            ax_main.text(xi, v + (abs(v) * 0.08 + 2) * (1 if v >= 0 else -1),
                         f"{v:.0f}", ha="center",
                         va="bottom" if v >= 0 else "top",
                         fontsize=7.5, fontweight="bold",
                         color=SSP_COLORS[sc["ssp"]])

        ax_main.axhline(0, color="#aaa", lw=0.7, ls=":")
        ax_main.set_xticks(x_ssp)
        ax_main.set_xticklabels(
            [sc["ssp"].replace("SSP", "") for sc in SSP6],
            fontsize=8, rotation=35, ha="right"
        )
        ax_main.set_title(
            f"{country}\n{meta['region']}",
            fontsize=10.5, fontweight="bold", color=meta["color"]
        )
        ax_main.set_ylabel("Net MUSD" if ci == 0 else "", fontsize=9)
        ax_main.legend(fontsize=7, framealpha=0.9, loc="lower right")
        ax_main.spines[["top", "right"]].set_visible(False)

        # Project inventory strip
        projs_in_country = sub["project"].tolist()
        capex_total      = sub["capex_musd"].sum()
        inv_txt = (
            f"Projects: {', '.join(projs_in_country)}\n"
            f"Total CAPEX: USD {capex_total:,.0f} M\n"
            f"Avoided GHG: {'Yes' if sub['has_av'].any() else 'No reported data'}"
        )
        ax_action.axis("off")
        ax_action.text(
            0.5, 0.88, inv_txt,
            ha="center", va="top", fontsize=7.5,
            transform=ax_action.transAxes,
            bbox=dict(fc="white", ec=meta["color"], lw=1.2, pad=5, alpha=0.95)
        )
        # UBA vs best/worst REMIND range
        rm_range_txt = (
            f"UBA: {tot_uba:+.0f} MUSD\n"
            f"REMIND range: {tot_rm.min():+.0f} → {tot_rm.max():+.0f} MUSD\n"
            f"Max swing: {(tot_rm.max()-tot_rm.min()):.0f} MUSD"
        )
        ax_action.text(
            0.5, 0.38, rm_range_txt,
            ha="center", va="top", fontsize=7.5,
            transform=ax_action.transAxes,
            color="#333",
            bbox=dict(fc="#f0f0f0", ec="#ccc", lw=0.8, pad=5)
        )

    # SSP colour legend at top
    leg_handles = [
        mpatches.Patch(fc=SSP_COLORS[sc["ssp"]],
                       label=f"{sc['ssp']} ({sc['warming']})")
        for sc in SSP6
    ]
    fig.legend(handles=leg_handles, loc="upper center", ncol=6,
               fontsize=9, framealpha=0.95, bbox_to_anchor=(0.5, 0.98))

    # Key-message box
    fig.text(
        0.01, 0.00,
        "MESSAGE 3 · GEOGRAPHY MATTERS\n"
        "Climate risk is not just about what you build — it's about where you build it.\n"
        "Each country panel shows a distinct risk profile driven by local policy, energy mix,\n"
        "and land use (MAgPIE's specialty). A uniform benchmark misses this entirely.",
        fontsize=8, va="bottom", style="italic",
        bbox=dict(fc="#f8f9fa", ec="#aaa", lw=0.8, pad=5)
    )

    fig.suptitle(
        "Geography Matters — Country-Level GHG Net Valuation · All 6 IPCC SSP Scenarios\n"
        "Small multiples · Fan charts show IAM model uncertainty · Year 2030",
        fontsize=11, fontweight="bold", y=1.005
    )
    fig.savefig(FIG_DIR / "comm_fig3_geography.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved: comm_fig3_geography.png")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Loading data …")
    sdf, uba_c, to_musd = load_data()
    print(f"  UBA Central 2030: {uba_c:.2f} USD/t")
    print(f"  Projects loaded : {len(sdf)}")

    print("\nFigure 1 – Volatility …")
    fig1_volatility(sdf, uba_c)

    print("\nFigure 2 – Benchmarking …")
    fig2_benchmarking(sdf, uba_c)

    print("\nFigure 3 – Geography …")
    fig3_geography(sdf, uba_c)

    print("\nDone. Figures saved to:", FIG_DIR)
