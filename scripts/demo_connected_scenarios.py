"""Demonstration of Three Connected Territorial Scenarios (Commercial, Educational, Healthcare).

Executes the cross-sector cascade on the EXACT SAME individuals and territory:
- Territory: Cantón San José Las Flores, San Vicente Sur
- Shared Cohort:
  * Familia Henríquez (José: day laborer, Mateo: 15yo student)
  * Familia Vásquez (Carmen: Tiendita owner, Rosa: 72yo hypertensive elder, Lucía: 11yo child)
- Shared Infrastructure:
  * Rural Unpaved Road Link
  * Centro Escolar San José Las Flores
  * UCSF San José Las Flores
  * Tiendita Doña Carmen

Usage:
    python scripts/demo_connected_scenarios.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from saltbor.territory.connected_scenarios import ConnectedTerritorialScenariosDemonstrator


def main():
    print("=" * 86)
    print("SALTBOR PHASE 1.14: DEMONSTRATION OF THREE CONNECTED SECTORAL SCENARIOS")
    print("Cross-Sector Interdependence: Commercial <--> Education <--> Healthcare")
    print("Shared Territory: Cantón San José Las Flores, San Vicente Sur (D.L. 762)")
    print("=" * 86)

    demo = ConnectedTerritorialScenariosDemonstrator(random_seed=42)
    snapshots = demo.run_full_demonstration()

    for idx, snap in enumerate(snapshots, 1):
        print(f"\n[{snap.stage_name.upper()}]")
        print(f"Summary: {snap.description}")
        print("-" * 86)
        print("  1. COMMERCIAL & TRANSPORT (Tiendita & Road Corridor):")
        print(f"     * Road Friction Multiplier : {snap.road_friction_multiplier:.1f}x")
        print(f"     * Wholesale Price (Maize)  : ${snap.wholesale_food_price_usd:.2f} / lb")
        print(f"     * Retail Price at Tiendita : ${snap.retail_food_price_usd:.2f} / lb")
        print(f"     * Customer Footfall Factor : {snap.tiendita_footfall_factor:.2f}")
        print(f"     * Tiendita Cash Balance    : ${snap.tiendita_cash_usd:.2f} (Solvent: {snap.is_tiendita_solvent})")

        print("  2. HOUSEHOLD FINANCES (Familia Henríquez - José & Mateo):")
        print(f"     * José's Liquid Cash       : ${snap.jose_cash_balance_usd:.2f}")
        print(f"     * Daily Food Expenditure   : ${snap.daily_food_expenditure_usd:.2f} / day")
        print(f"     * Food Share of Daily Wage : {snap.food_budget_share_pct:.1f}%")
        print(f"     * Informal Fiado Debt      : ${snap.informal_credit_fiado_usd:.2f}")

        print("  3. EDUCATION (Centro Escolar & Mateo Henríquez, Age 15):")
        print(f"     * Mateo's Attendance Rate  : {snap.mateo_school_attendance_pct:.1f}%")
        print(f"     * Mateo's Dropout Risk     : {snap.mateo_dropout_risk:.2f} (High Risk Threshold > 0.35)")
        print(f"     * Engaged in Child Labor   : {snap.mateo_is_working_informal}")
        print(f"     * Overall School Attendance: {snap.school_overall_attendance_pct:.1f}%")

        print("  4. HEALTHCARE (UCSF Clinic & Health Status):")
        print(f"     * Clinic Queue Wait Time   : {snap.clinic_waiting_time_hours:.2f} hours")
        print(f"     * José's Lost Work Days    : {snap.jose_lost_work_days} days")
        print(f"     * Out-of-Pocket Medicine   : ${snap.out_of_pocket_medical_usd:.2f}")
        print(f"     * Rosa's Health Index      : {snap.rosa_health_status:.2f} / 1.00")
        print(f"     * José's Health Index      : {snap.jose_health_status:.2f} / 1.00")

    print("\n" + "=" * 86)
    print("DEMONSTRATION CONCLUSION:")
    print("1. Commercial transport shock doubled food costs, consuming 74% of household wages.")
    print("2. The same household had to pull Mateo from school into child labor to survive.")
    print("3. An acute health shock and clinic overload drove the household into $0 cash & fiado,")
    print("   draining Tiendita's capital to $32 and causing commercial insolvency.")
    print("4. Only an INTEGRATED multi-sector territorial project restored all three domains.")
    print("=" * 86)


if __name__ == "__main__":
    main()
