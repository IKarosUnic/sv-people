# SALTBOR — PHASE 1.5
## FORENSIC AUDIT OF ECONOMIC ROUTINES, CONSUMPTION & SOCIOECONOMIC ARCHITECTURE

**System:** SALTBOR Multi-Agent Digital Civilization Platform  
**Target:** El Salvador Digital Twin — Human Daily Life, Labor Market & Socioeconomic Dynamics  
**Audit Date:** November 2026  
**Status:** FORENSIC AUDIT COMPLETE & RESTRUCTURING ARCHITECTURE APPROVED  

---

## 1. EXECUTIVE SUMMARY & INVESTIGATION OF RECENT ECONOMIC CHANGES

An exhaustive audit of the economic routines, decision engine heuristics, and transaction pipelines in `saltbor/` was conducted to investigate four specific recent economic mechanisms identified in the Phase 1.5 specification:

1. **$2.50 daily household maintenance deduction**
2. **$0.75 cooking expense**
3. **$0.90 per work tick**
4. **COMMERCE_BUY destination selection and purchase coupling**

The audit revealed critical accounting anomalies, double deductions, and unrealistic macro-assumptions that violated conservation of money and constrained individual autonomy.

---

## 2. DETAILED FORENSIC FINDINGS

### Finding 1: The $2.50 Daily Household Maintenance Deduction
- **Code Location:** `saltbor/simulation/runner.py:931-933`
  ```python
  if self.clock.tick_of_day == 0:
      for h in self.population.get_all():
          h.physical_state.money = max(0.0, round(h.physical_state.money - 2.50, 2))
  ```
- **Forensic Diagnosis:**
  - **Misattribution:** The deduction was charged to *every individual agent* rather than to the *household unit*. In a 4-person household (e.g., two parents, a child, and an elder), this blindly deducted $10.00/day rather than a realistic domestic overhead.
  - **Unaccounted Leakage:** The deducted $2.50 was destroyed into a void. It was never paid to utility providers, landlords, or municipal services.
  - **Regressive Distortion:** Agents with $0.00 had no debt recorded, while impoverished agents lost their remaining cents regardless of rent status or homeownership.
- **Remediation Plan:**
  - Remove the blind individual loop from `runner.py:931`.
  - Shift housing, utility, and upkeep costs to `HouseholdLedger.execute_daily_overhead()`, scaled by household size, dwelling type (owner-occupied vs rented vs informal), and paid by the household head or pooled savings. Unpaid obligations accrue as rent/utility arrears.

---

### Finding 2: The $0.75 Cooking Expense
- **Code Location:** `saltbor/world/activities/catalog.py:175`
  ```python
  ActivityType.COOK_MEAL: ActivityDefinition(
      default_duration_ticks=2,
      effects_per_tick=ActivityEffect(money_delta=-0.75, ...)
  )
  ```
- **Forensic Diagnosis:**
  - **Per-Tick Multiplication:** In `saltbor/population/human.py:240`, `eff.money_delta` is applied *on every tick* of the activity's duration. For a 2-tick activity, `money_delta=-0.75` deducted **$1.50** from the agent's wallet per meal.
  - **Double Charging:** If the agent previously bought groceries (corn, beans, eggs) at the corner store, they paid for the groceries with cash. Deducting an additional $1.50 at cooking time forced agents to pay twice for the same meal.
  - **Pantry Disconnect:** Cooking at home should consume physical food inventory from the household pantry (`HouseholdLedger.inventory`). Cash should only be spent if buying ready-to-eat street food or dining out (`DINE_OUT`).
- **Remediation Plan:**
  - Set `money_delta=0.0` for `COOK_MEAL` in `catalog.py`.
  - Cooking at home consumes raw pantry items (maíz, frijol, huevos). If the pantry lacks ingredients, the agent must either purchase groceries at a store (`COMMERCE_BUY` / `PURCHASE_GOODS`) or dine at an eatery (`DINE_OUT`).

---

### Finding 3: The $0.90 per Work Tick Wage
- **Code Location:** `saltbor/world/activities/catalog.py:201`
  ```python
  ActivityType.WORK: ActivityDefinition(
      default_duration_ticks=16,
      effects_per_tick=ActivityEffect(money_delta=+0.90, ...)
  )
  ```
- **Forensic Diagnosis:**
  - **Unbacked Fiat Minting:** Over a 16-tick work shift (4 hours), an agent earned $14.40 ($0.90 * 16). This currency was created from thin air. It was not disbursed from an employer's cash reserve or customer sales.
  - **Uniform Compensation:** A master carpenter, an apprentice, a vendor, and an unemployed agent all received the exact same $0.90/tick if they performed the `WORK` activity.
  - **Absence of Labor Solvency:** If an enterprise ran out of money or went insolvent, its workers still received wages from the sky.
- **Remediation Plan:**
  - Set base `money_delta=0.0` for `WORK` in `catalog.py`.
  - Earnings must derive from the **Dynamic Labor Market Engine**:
    - Formal/informal employment contracts with defined daily/hourly wages paid out of enterprise cash reserves.
    - Informal day labor / self-employment earning variable market returns based on customer demand and sales.
    - If an employer is insolvent, wages are unpaid, triggering employee grievances, lawsuits, or resignations.

---

### Finding 4: COMMERCE_BUY Market Selection & Rigid Purchasing
- **Code Location:** `saltbor/cognition/decision/engine.py:344`
  ```python
  target_store = "tienda_san_pedro" if context.current_money < 30.0 else "mercado_central"
  ```
- **Forensic Diagnosis:**
  - **Arbitrary Destination Selection:** Destination was chosen purely by `< $30.00` cash threshold, ignoring spatial distance, walking time, opening hours, and item availability.
  - **Forced Purchase Coupling:** In the existing architecture, visiting a commercial establishment unconditionally triggered a purchase. Agents could not browse, compare prices, or window shop without spending money.
  - **Double Deduction in Execution:** `COMMERCE_BUY` in `catalog.py` had `money_delta=-2.50`, while `SimulationRunner._on_commerce_event` ALSO called `conduct_purchase_transaction` and subtracted `total_spent_usd` from `human.physical_state.money`, creating accounting discrepancies.
- **Remediation Plan:**
  - Expand commercial activities into: `WINDOW_SHOPPING`, `BROWSE_STORE`, `COMPARE_PRICES`, `PURCHASE_GOODS`, `DINE_OUT`.
  - Establish a comprehensive `CommercialRegistry` with clear differentiation between verified real locations and simulated microenterprises.
  - Store visits evaluate budget, perceived value, urgency, and willingness to pay. If goods are overpriced, stock is empty, or funds are reserved for rent, the agent browses and leaves without spending a single cent ($0.00).

---

## 3. AUDIT OF CORE SUBSYSTEMS & INTEGRATION TARGETS

| Subsystem | Existing State | Phase 1.5 Target Architecture |
| :--- | :--- | :--- |
| **SyntheticHuman** | Static needs, basic wallet, home/work IDs | Personal preferences, housing tenure, employment contract, habits, budget constraints |
| **DecisionEngine** | 16 utility options, vital overrides | Multi-attribute utility with leisure, job search, housing, curiosity, social invitations |
| **ActivityType** | 20 civilization activities | 26 new Phase 1.5 activities (browsing, dining, job applications, housing, leisure) |
| **BusinessRegistry** | Dormant enterprise registry with basic payroll | Dynamic hiring, wage negotiation, market vacancies, daily solvency cycles |
| **InformalCommerce**| Corner store and fiado ledger | Multi-establishment browsing, price comparison, verified vs simulated tagging |
| **HouseholdLedger** | Basic inventory and shared savings | Full household cost of living (rent, utilities, pantry consumption, shared pooling) |
| **Labor Market** | None (wages minted in catalog) | Genuine labor ecosystem: vacancies, applications, interviews, wages, layoffs, informal work |
| **Housing System** | None (fixed home_location_id) | 7 tenure types, rental contracts, eviction risk, shelter, homelessness recovery |
| **Persistence** | SQLite checkpointing | Full ACID tables for vacancies, employment contracts, housing leases, commercial visits |
| **Observability** | Web UI with 10 panels | Dedicated Panels for Labor Market, Housing Precarity, Commerce Browsing, and Leisure |

---

## 4. CONSERVATION OF MONEY & DOUBLE-ENTRY DISCIPLINE

Under Phase 1.5, every financial flow in SALTBOR is strictly conserved:

$$\sum \Delta \text{Individual Cash} + \sum \Delta \text{Household Savings} + \sum \Delta \text{Enterprise Cash} + \sum \Delta \text{Institutional Funds} = \text{External Net Inflows (Remittances)}$$

1. **Wages:** Enterprise Cash $\longrightarrow$ Employee Cash (Net of taxes/contributions).
2. **Groceries:** Individual/Household Cash $\longrightarrow$ Store Cash Box.
3. **Dining Out:** Customer Cash $\longrightarrow$ Comedor/Pupusería Revenue.
4. **Rent:** Tenant Household $\longrightarrow$ Landlord Cash Reserve.
5. **Utilities:** Household Savings $\longrightarrow$ Municipal Utility Treasury.
6. **Debt Repayment:** Debtor Cash $\longrightarrow$ Creditor/Store Cash Box.

Zero currency is created from thin air during routine activities.

---

## 5. MIGRATION & BACKWARD COMPATIBILITY PLAN

1. **Enum Preservation:** All existing `ActivityType`, `EventType`, and `LocationType` enum values are strictly preserved. New Phase 1.5 types are appended.
2. **Catalog Integrity:** `ActivityCatalog.get()` supports all historical and new activity definitions.
3. **Test Suite Compatibility:** All 435 baseline tests from Phases 0.1 through 1.4 will continue to pass without modification.
4. **Database Migration:** SQLite schema automatically initializes new Phase 1.5 tables (`labor_vacancies`, `labor_contracts`, `housing_units`, `housing_leases`, `commercial_visits`) without altering existing tables.
