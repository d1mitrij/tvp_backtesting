"""
derive_parameters.py
====================
Reads the three project finance CSVs and derives every region-specific
OSeMOSYS model parameter that is grounded in observed project data.

Run standalone to inspect derived values:
    python derive_parameters.py

Imported by run_simulation.py to ensure a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "modeled_input_data"

# ── Physical constants ────────────────────────────────────────────────────────
CAPEX_PER_KW_USD  = 1_000        # $/kW — hydro retrofit benchmark (assumptions.txt)
H_PER_YEAR        = 8_760        # hours per year
MWH_TO_TWH        = 1e-6         # MWh → TWh
TWH_TO_PJ         = 3.6          # TWh → PJ
MW_TO_GW          = 1e-3         # MW → GW


@dataclass
class RegionParams:
    """All derived model parameters for one region."""
    region: str

    # From hydro project data (if present)
    hydro_project_id: str | None = None
    hydro_investment_usd: float = 0.0        # USD
    hydro_avoided_co2_t: float = 0.0         # t CO2/yr
    hydro_retro_mw: float = 0.0              # MW of new capacity
    hydro_retro_gw: float = 0.0              # GW (= hydro_retro_mw / 1000)
    hydro_cf: float = 0.40                   # capacity factor
    coal_ef_mt_pj: float = 0.247             # Mt CO2/PJ electricity (fallback)

    # From hospital project data (if present)
    hospital_projects: list = field(default_factory=list)
    total_hospital_investment_usd: float = 0.0

    # From rail project data (if present)
    rail_capex_eur: float = 0.0
    rail_passengers_yr: float = 0.0
    rail_elec_demand_pj: float = 0.0          # PJ/yr additional electricity

    def derive_from_hydro(
        self,
        project_id: str,
        investment_usd: float,
        avoided_co2_t: float,
        cf: float,
    ) -> None:
        """Derive coal emission factor and retrofit capacity from one hydro project."""
        self.hydro_project_id    = project_id
        self.hydro_investment_usd = investment_usd
        self.hydro_avoided_co2_t  = avoided_co2_t
        self.hydro_cf             = cf

        # Capacity from budget at benchmark cost
        self.hydro_retro_mw = investment_usd / (CAPEX_PER_KW_USD * 1_000)  # MW
        self.hydro_retro_gw = self.hydro_retro_mw * MW_TO_GW

        # Additional generation from retrofitted capacity
        gen_mwh = self.hydro_retro_mw * H_PER_YEAR * cf           # MWh/yr
        gen_pj  = gen_mwh * MWH_TO_TWH * TWH_TO_PJ                # PJ/yr

        # Implied coal emission factor = avoided CO2 / additional renewable output
        # (grid intensity of the coal plant displaced by the hydro output)
        avoided_mt = avoided_co2_t / 1e6                           # Mt CO2/yr
        self.coal_ef_mt_pj = avoided_mt / gen_pj if gen_pj > 0 else 0.247

    def derive_from_rail(
        self,
        capex_eur: float,
        passengers_yr: float,
        kwh_per_passenger: float = 5.0,
    ) -> None:
        """Estimate incremental rail electricity demand from electrified rail project.

        kwh_per_passenger: kWh per passenger journey (EU rail ≈ 0.08 kWh/pkm × 50 km ≈ 4–5 kWh)
        """
        self.rail_capex_eur       = capex_eur
        self.rail_passengers_yr   = passengers_yr
        elec_kwh = passengers_yr * kwh_per_passenger               # kWh/yr
        # 1 kWh = 3.6e-9 PJ
        self.rail_elec_demand_pj = elec_kwh * 3.6e-9              # PJ/yr

    def summary(self) -> str:
        lines = [f"  Region: {self.region}"]
        if self.hydro_project_id:
            lines += [
                f"  Hydro project: {self.hydro_project_id}",
                f"    Investment:        ${self.hydro_investment_usd/1e6:.1f}M",
                f"    Avoided CO2:       {self.hydro_avoided_co2_t:,.0f} t/yr",
                f"    Retrofit capacity: {self.hydro_retro_mw:.0f} MW = {self.hydro_retro_gw:.3f} GW",
                f"    Derived coal EF:   {self.coal_ef_mt_pj:.4f} Mt CO2/PJ_elec",
            ]
        if self.hospital_projects:
            lines.append(
                f"  Hospital investment: ${self.total_hospital_investment_usd/1e6:.0f}M "
                f"({len(self.hospital_projects)} project(s))"
            )
        if self.rail_capex_eur:
            lines += [
                f"  Rail capex: €{self.rail_capex_eur/1e9:.2f}B, "
                f"{self.rail_passengers_yr/1e6:.1f}M pax/yr",
                f"    Rail elec demand: {self.rail_elec_demand_pj*1000:.1f} TJ/yr "
                f"= {self.rail_elec_demand_pj:.4f} PJ/yr",
            ]
        return "\n".join(lines)


# ── Capacity factors by region (used in hydro derivation) ────────────────────
HYDRO_CF = {
    "Africa": 0.40,
    "Asia":   0.38,
    "Europe": 0.35,
    "LATAM":  0.45,
}


def load_project_data() -> dict[str, RegionParams]:
    """
    Read CSVs and return a dict of RegionParams keyed by region name.
    Region names match the CSV values exactly: Africa, Asia, Europe, LATAM.
    """
    regions = ["Africa", "Asia", "Europe", "LATAM"]
    params  = {r: RegionParams(region=r, hydro_cf=HYDRO_CF[r]) for r in regions}

    # ── Hydro projects ─────────────────────────────────────────────────────────
    hydro_df = pd.read_csv(DATA_DIR / "hydro_finance_input.csv")
    for _, row in hydro_df.iterrows():
        r = row["Region"]
        if r in params:
            params[r].derive_from_hydro(
                project_id    = row["Project_ID"],
                investment_usd= row["Est_Investment_USD"],
                avoided_co2_t = row["Avoided_CO2_Tons"],
                cf            = HYDRO_CF[r],
            )

    # LATAM has no hydro project — apply default coal EF for LATAM
    # (Andean / Brazilian gas-heavy marginal grid, estimated)
    params["LATAM"].coal_ef_mt_pj = 0.220

    # ── Hospital projects ──────────────────────────────────────────────────────
    hosp_df = pd.read_csv(DATA_DIR / "hospitals_finance_input.csv")
    for _, row in hosp_df.iterrows():
        r = row["Region"]
        if r in params:
            params[r].hospital_projects.append(
                {
                    "project_id":   row["Project_ID"],
                    "investment":   row["Est_Investment_USD"],
                    "beneficiaries":row["Beneficiaries_H&S"],
                    "sector":       row["Sector_Code"],
                    "multiplier":   row["Multiplier_Benchmark"],
                }
            )
            params[r].total_hospital_investment_usd += row["Est_Investment_USD"]

    # ── Rail projects ──────────────────────────────────────────────────────────
    rail_df = pd.read_csv(DATA_DIR / "rail_finance_input.csv")
    for _, row in rail_df.iterrows():
        r = row["Region"]
        if r in params and row["Stage"] == "Dev":
            # Development-stage project = new electrified line
            pax = float(str(row["Reach_Ppl_Yr"]).replace("N/A", "0") or 0)
            params[r].derive_from_rail(
                capex_eur     = row["Est_Capex_EUR"],
                passengers_yr = pax,
            )

    return params


# ── Exported constants for use in run_simulation.py ──────────────────────────
def get_coal_emission_factors() -> dict[str, float]:
    """Return {region: Mt CO2/PJ} coal emission factors derived from avoided CO2 data."""
    params = load_project_data()
    return {r: p.coal_ef_mt_pj for r, p in params.items()}


def get_hydro_retro_gw() -> dict[str, float]:
    """Return {region: GW} maximum HYDRO_RETRO new capacity from project budgets."""
    params = load_project_data()
    return {r: p.hydro_retro_gw for r, p in params.items()}


def get_rail_elec_demand_pj() -> dict[str, float]:
    """Return {region: PJ/yr} incremental electricity demand from rail electrification."""
    params = load_project_data()
    return {r: p.rail_elec_demand_pj for r, p in params.items()}


if __name__ == "__main__":
    params = load_project_data()
    print("=" * 60)
    print("Derived OSeMOSYS model parameters from project finance data")
    print("=" * 60)
    for r, p in params.items():
        print()
        print(p.summary())

    print()
    print("─" * 60)
    print("COAL_PP emission_activity_ratio [Mt CO2/PJ_electricity]:")
    for r, ef in get_coal_emission_factors().items():
        print(f"  {r:8s}: {ef:.4f}")

    print()
    print("HYDRO_RETRO capacity_additional_max [GW]:")
    for r, gw in get_hydro_retro_gw().items():
        print(f"  {r:8s}: {gw:.3f}")

    print()
    print("Rail electricity demand increment [PJ/yr → EUR only]:")
    for r, pj in get_rail_elec_demand_pj().items():
        if pj > 0:
            print(f"  {r:8s}: {pj:.4f} PJ/yr ({pj*1000:.1f} TJ/yr)")
