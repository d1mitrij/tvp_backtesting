"""
Main orchestration pipeline.

Reads the three project CSV files, routes them through:
  1. Sector mapping        (sector_mapper)
  2. ENCORE screening      (encore_materiality)
  3. WWF Risk Filter       (wwf_risk_filter)
  4. InVEST config build   (invest_config)
  5. Portfolio aggregation (portfolio_aggregator)

Outputs:
  assessment_output/
    encore_materiality_<project>.csv     – per-ecosystem-service ratings
    wwf_risk_scores.csv                  – WRF/BRF composites
    invest_configs/<project>_<model>.json – InVEST args (ready to execute)
    portfolio_stress_test.csv            – TNFD LEAP Evaluate table
    dependency_heatmap.csv               – portfolio-wide ENCORE aggregation
    pipeline_summary.txt                 – human-readable summary
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Allow running from the project root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dependency_profiler.sector_mapper      import map_sector
from dependency_profiler.encore_materiality import screen_portfolio
from dependency_profiler.wwf_risk_filter    import score_portfolio
from dependency_profiler.invest_config      import (
    build_invest_configs, save_configs, execute_invest_models,
    DEFAULT_WORKSPACE,
)
from dependency_profiler.portfolio_aggregator import aggregate_portfolio

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR   = Path(__file__).parent.parent / "modeled_input_data"
OUTPUT_DIR = Path(__file__).parent.parent / "assessment_output"
INVEST_CFG = OUTPUT_DIR / "invest_configs"


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_hospitals() -> list[dict]:
    rows = []
    with open(DATA_DIR / "hospitals_finance_input.csv") as f:
        for row in csv.DictReader(f):
            rows.append({
                "project_id":       row["Project_ID"],
                "region":           row["Region"].lower(),
                "sector_code":      row["Sector_Code"],
                "beneficiaries":    int(row["Beneficiaries_H&S"]),
                "investment_usd":   float(row["Est_Investment_USD"]),
                "multiplier_benchmark": float(row["Multiplier_Benchmark"]),
                "stage":            row["Stage"],
                "sector":           row["Sector_Code"],   # alias for aggregator
            })
    return rows


def load_hydro() -> list[dict]:
    rows = []
    with open(DATA_DIR / "hydro_finance_input.csv") as f:
        for row in csv.DictReader(f):
            rows.append({
                "project_id":       row["Project_ID"],
                "region":           row["Region"].lower(),
                "sector_code":      row["Sector"],
                "sector":           row["Sector"],
                "avoided_co2_tons": float(row["Avoided_CO2_Tons"]),
                "investment_usd":   float(row["Est_Investment_USD"]),
                "impact_type":      row["Impact_Type"],
            })
    return rows


def load_rail() -> list[dict]:
    rows = []
    with open(DATA_DIR / "rail_finance_input.csv") as f:
        for row in csv.DictReader(f):
            reach_raw = row.get("Reach_Ppl_Yr", "0")
            capex_raw = row.get("Est_Capex_EUR", "0")
            rows.append({
                "project_id":   row["Project_ID"],
                "region":       row["Region"].lower(),
                "sector_code":  "Transport",
                "sector":       "Transport",
                "reach_ppl_yr": 0 if reach_raw == "N/A" else int(reach_raw.replace(",", "")),
                "pc_air_quality":   float(row.get("PC_Air_Quality", 0)),
                "pc_critical_infra": float(row.get("PC_Critical_Infra", 0)),
                "capex_eur":    float(capex_raw) if capex_raw else 0,
                "investment_usd": float(capex_raw) * 1.08 if capex_raw else 0,  # EUR→USD
                "stage":        row["Stage"],
            })
    return rows


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(verbose: bool = True) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INVEST_CFG.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if verbose:
            print(msg)

    # ------------------------------------------------------------------
    # 1. Ingest
    # ------------------------------------------------------------------
    log("\n[1/5] Loading project data ...")
    hospitals = load_hospitals()
    hydro     = load_hydro()
    rail      = load_rail()
    all_projects = hospitals + hydro + rail
    log(f"    {len(all_projects)} projects loaded "
        f"({len(hospitals)} hospitals, {len(hydro)} hydro, {len(rail)} rail)")

    # ------------------------------------------------------------------
    # 2. Sector mapping (ENCORE sector key resolution)
    # ------------------------------------------------------------------
    log("\n[2/5] Resolving sector codes → ISIC / ENCORE ...")
    for proj in all_projects:
        mapping = map_sector(proj["sector_code"])
        proj["isic"]         = mapping["isic"]
        proj["encore_sector"]= mapping["encore_sector"]
        proj["wwf_industry"] = mapping["wwf_industry"]
        log(f"    {proj['project_id']:15s}  {proj['sector_code']:25s}"
            f"  →  {mapping['isic']:8s}  [{mapping['encore_sector']}]")

    # ------------------------------------------------------------------
    # 3. ENCORE materiality screening
    # ------------------------------------------------------------------
    log("\n[3/5] ENCORE materiality screening ...")
    screened = screen_portfolio(all_projects)

    for proj in screened:
        pid = proj["project_id"]
        log(f"    {pid}: {proj['n_material_services']} material services  |  "
            f"top deps: {proj['high_dependency_services'][:3]}")

        # Write per-project materiality table
        mat_path = OUTPUT_DIR / f"encore_materiality_{pid}.csv"
        _write_csv(mat_path, proj["materiality_table"])

    # ------------------------------------------------------------------
    # 4. WWF Risk Filter scoring
    # ------------------------------------------------------------------
    log("\n[4/5] WWF Risk Filter scoring ...")
    wwf_results = score_portfolio(all_projects)

    wwf_rows = []
    for r in wwf_results:
        log(f"    {r.project_id:15s}  WRF={r.wrf.composite:.2f} "
            f"({'HIGH' if r.wrf.high_risk else 'LOW ':4s})  "
            f"BRF={r.brf.composite:.2f} "
            f"({'HIGH' if r.brf.high_risk else 'LOW ':4s})")
        wwf_rows.append({
            "project_id":         r.project_id,
            "region":             r.region,
            "sector_key":         r.sector_key,
            "wrf_physical":       r.wrf.physical,
            "wrf_regulatory":     r.wrf.regulatory,
            "wrf_reputational":   r.wrf.reputational,
            "wrf_composite":      r.wrf.composite,
            "wrf_high_risk":      r.wrf.high_risk,
            "brf_species_threat": r.brf.species_threat,
            "brf_ecosystem":      r.brf.ecosystem_intactness,
            "brf_protected_areas":r.brf.protected_areas,
            "brf_composite":      r.brf.composite,
            "brf_high_risk":      r.brf.high_risk,
            "overall_high_risk":  r.overall_high_risk,
        })

    _write_csv(OUTPUT_DIR / "wwf_risk_scores.csv", wwf_rows)

    # ------------------------------------------------------------------
    # 5. InVEST model config generation
    # ------------------------------------------------------------------
    log("\n[5a/5] Building InVEST model configurations ...")
    all_invest_configs = []
    for proj in all_projects:
        configs = build_invest_configs(
            project_id=proj["project_id"],
            region=proj["region"],
            encore_sector=proj["encore_sector"],
        )
        all_invest_configs.extend(configs)
        for cfg in configs:
            log(f"    {proj['project_id']:15s}  model={cfg['_model_name']}")

    saved_paths = save_configs(all_invest_configs, INVEST_CFG)
    log(f"    {len(saved_paths)} config files saved → {INVEST_CFG}")

    log("\n[5b/5] InVEST model execution ...")
    invest_results = execute_invest_models(all_invest_configs)
    for r in invest_results:
        log(f"    {r['model']:40s}  status={r['status']}")
    _write_json(OUTPUT_DIR / "invest_execution_log.json", invest_results)

    # ------------------------------------------------------------------
    # 6. Portfolio aggregation
    # ------------------------------------------------------------------
    log("\n[6/6] Portfolio aggregation and financial stress testing ...")
    report = aggregate_portfolio(
        projects_raw=    all_projects,
        wwf_results=     wwf_results,
        encore_profiles= screened,
        assumptions=     {},
        rar_mode=        "binary",
    )

    _write_csv(OUTPUT_DIR / "portfolio_stress_test.csv", report.stress_test_table)

    heatmap_rows = [
        {"ecosystem_service": svc, **vals}
        for svc, vals in report.dependency_summary.items()
    ]
    _write_csv(OUTPUT_DIR / "dependency_heatmap.csv", heatmap_rows)

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    n_high = sum(1 for p in report.projects if p.risk_flag)
    summary_lines = [
        "=" * 68,
        "  NATURE-RELATED DEPENDENCY & RISK ASSESSMENT – PORTFOLIO SUMMARY",
        "=" * 68,
        f"  Assessment date       : 2026-04-09",
        f"  Projects assessed     : {len(report.projects)}",
        f"  Total investment      : USD {report.total_investment_usd/1e6:,.1f}M",
        f"  Projects at high risk : {n_high} / {len(report.projects)} "
        f"({report.high_risk_share*100:.0f}% of investment)",
        f"  Revenue at risk (RaR) : USD {report.revenue_at_risk_usd/1e6:,.1f}M",
        f"  Portfolio ITR         : {report.weighted_itr}°C",
        "",
        "  TOP ECOSYSTEM DEPENDENCIES (portfolio-wide)",
        "  " + "-" * 55,
    ]
    for svc, vals in list(report.dependency_summary.items())[:8]:
        if vals["max_dependency_score"] >= 3:
            summary_lines.append(
                f"  {svc:<38s}  max={vals['max_dependency_score']}  "
                f"n_material={vals['n_material_projects']}"
            )

    summary_lines += [
        "",
        "  STRESS TEST TABLE (see portfolio_stress_test.csv for full detail)",
        "  " + "-" * 55,
    ]
    for row in report.stress_test_table:
        flag = "*** HIGH RISK ***" if row["overall_high_risk"] else ""
        summary_lines.append(
            f"  {row['project_id']:<18s} "
            f"WRF={row['wrf_composite']} "
            f"BRF={row['brf_composite']}  "
            f"RaR=USD{row['revenue_at_risk_usd_m']:.1f}M  {flag}"
        )

    summary_lines += [
        "",
        "  OUTPUT FILES",
        "  " + "-" * 55,
        f"  {OUTPUT_DIR}",
        "    encore_materiality_<project>.csv",
        "    wwf_risk_scores.csv",
        "    portfolio_stress_test.csv",
        "    dependency_heatmap.csv",
        "    invest_execution_log.json",
        "    invest_configs/<project>_<model>.json",
        "=" * 68,
    ]

    summary_text = "\n".join(summary_lines)
    log("\n" + summary_text)

    with open(OUTPUT_DIR / "pipeline_summary.txt", "w") as f:
        f.write(summary_text + "\n")

    return {
        "report":          report,
        "wwf_results":     wwf_results,
        "encore_screened": screened,
        "invest_configs":  all_invest_configs,
    }


if __name__ == "__main__":
    run_pipeline(verbose=True)
