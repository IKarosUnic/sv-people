# SALTBOR — PHASE 1.5 SYSTEM SPECIFICATION
## Human Daily Life, Autonomous Consumption, Labor Market, Housing & Socioeconomic Dynamics

---

### 1. Executive Summary & Vision

Phase 1.5 elevates the SALTBOR synthetic civilization platform from mechanical routines and deterministic transactions into an authentic, emergent simulation of human daily life in El Salvador. Agents are not merely biological clockworks executing survival loops; they possess autonomous agency, distinct preferences, competing motivations, imperfect decision-making, and social entanglements.

Key capabilities introduced in Phase 1.5:
1. **Commercial Dynamics & Autonomous Consumption**: Distinguishes verified real-world GIS establishments from simulated microenterprises; models consumer intents spanning window shopping, browsing, price comparison, purchasing, and dining out; guarantees zero-purchase visits ($0 spend) when conditions or budgets do not warrant buying.
2. **Dynamic Labor Market**: Realistic job requisitions, candidate evaluations by skill and merit, reservation wage dynamics, formal and informal contract types, insolvency-driven resignations, dismissals, and informal day labor (jornaleros) funded strictly through enterprise liquidity.
3. **Housing, Tenancy & Precarity**: 7 realistic tenure types (owner-occupied, rental, shared family, informal mesón, temporary accommodation, shelter, homeless); daily rent collection with strict currency conservation, rent arrears accrual, eviction thresholds, and protective buffers allowing recovery.
4. **Household Living Costs & Double-Entry Accounting**: Eliminates artificial flat deductions; pools domestic utilities into a community infrastructure treasury; decouples cooking expenses to consume pantry inventory rather than cash.
5. **Everyday Life, Leisure & Autonomous Invitations**: 27 new activities covering leisure, sports, social visits, and civic life; social invitations evaluated autonomously based on energy, budget, trust, and personality traits without deterministic participation.

---

### 2. Core Domain Architecture & Type Definitions

#### 2.1 Housing Tenure Regimes (`HousingTenureType`)
```python
class HousingTenureType(str, enum.Enum):
    OWNER_OCCUPIED = "owner_occupied"              # Outright ownership of dwelling
    RENTAL = "rental"                              # Formal lease with regular rent payment
    SHARED_FAMILY = "shared_family"                # Multi-generational or extended family cohabitation
    INFORMAL_HOUSING = "informal_housing"          # Mesón room, tenement, or informal settlement
    TEMPORARY_ACCOMMODATION = "temporary_accommodation" # Couch-surfing with relatives/friends
    SHELTER = "shelter"                            # Emergency community or municipal shelter
    HOMELESS = "homeless"                          # Living in public spaces / street
```

#### 2.2 Employment Status & Contract Types
```python
class EmploymentStatus(str, enum.Enum):
    UNEMPLOYED = "unemployed"
    EMPLOYED_FORMAL = "employed_formal"
    EMPLOYED_INFORMAL = "employed_informal"
    SELF_EMPLOYED = "self_employed"
    EMPLOYER = "employer"
    RETIRED = "retired"
    STUDENT = "student"

class ContractType(str, enum.Enum):
    FORMAL_PERMANENT = "formal_permanent"
    FORMAL_TEMPORARY = "formal_temporary"
    INFORMAL_WAGE = "informal_wage"
    DAY_LABOR = "day_labor"
```

#### 2.3 Extended Activity Catalog (27 New Activities)
```python
# Commercial & Consumer Activities
WINDOW_SHOPPING = "window_shopping"
BROWSE_STORE = "browse_store"
COMPARE_PRICES = "compare_prices"
PURCHASE_GOODS = "purchase_goods"
DINE_OUT = "dine_out"
SEEK_ENTERTAINMENT = "seek_entertainment"

# Leisure & Relational Activities
VISIT_PARK = "visit_park"
VISIT_FRIEND = "visit_friend"
VISIT_RELATIVE = "visit_relative"
ATTEND_EVENT = "attend_event"
PARTICIPATE_IN_HOBBY = "participate_in_hobby"
PLAY_SPORT = "play_sport"
EXPLORE_LOCATION = "explore_location"

# Labor Market Activities
SEARCH_EMPLOYMENT = "search_employment"
APPLY_FOR_JOB = "apply_for_job"
ATTEND_INTERVIEW = "attend_interview"
NEGOTIATE_SALARY = "negotiate_salary"
ACCEPT_JOB = "accept_job"
REJECT_JOB = "reject_job"
RESIGN = "resign"
START_BUSINESS = "start_business"
CLOSE_BUSINESS = "close_business"

# Housing & Assistance Activities
SEEK_HOUSING = "seek_housing"
RENT_HOUSING = "rent_housing"
SEEK_SHELTER = "seek_shelter"
REQUEST_ASSISTANCE = "request_assistance"
OFFER_ASSISTANCE = "offer_assistance"
```

---

### 3. Subsystem Specifications

#### 3.1 Commercial Engine (`CommercialEngine`)
- **Verified vs. Simulated Distinction**: Establishments flag `is_verified_real: bool`. Verified entities reflect real-world GIS coordinates (e.g. `Mercado Central`, `Comedor Doña María`), while simulated enterprises represent emergent microbusinesses (`Tienda San Pedro`).
- **Consumer Visit Intents**:
  - `WINDOW_SHOP`: Inspects items from outside, builds product familiarity, updates internal price beliefs. Spends $0.00.
  - `BROWSE`: Explores store aisles out of curiosity or habit. Generates social encounters with other shoppers. Spends $0.00.
  - `COMPARE_PRICES`: Inspects unit prices across catalogs to optimize future shopping efficiency. Spends $0.00.
  - `PURCHASE`: Purchases staple foods, household items, or tools only if the item satisfies urgency, unit price $\le$ budget, and stock is available. Buyer cash transfers strictly to establishment cash box.
  - `DINE`: Consumes prepared meals at comedores or pupuserías, restoring hunger and happiness. Customer cash transfers strictly to comedor cash box.
- **Double-Entry Discipline**: For every purchase of amount $X$, buyer physical state decreases by $X$, and store `cash_box_usd` increases by $X$. No fiat money is minted or evaporated.

#### 3.2 Dynamic Labor Market (`LaborMarketEngine`)
- **Vacancy Lifecycle**: Enterprises publish `JobVacancy` with required skills, minimum skill thresholds, and offered daily wages.
- **Reservation Wage Filtering**: Agents calculate a personal reservation wage:
  $$W_{\text{res}} = \max(4.0, 10.0 - (\text{hunger} \times 4.0) - (\text{low\_money\_discount}))$$
  Agents will reject vacancies or job offers that pay below their reservation wage unless under severe distress.
- **Evaluation & Hiring**: Employers sort applicants by required skill proficiency and hire the highest-merit candidate, creating an active `EmploymentContract`.
- **Payroll Disbursement**: Daily payroll loop iterates over active contracts. If enterprise liquidity $\ge$ wage, cash transfers from business reserve to employee. If the enterprise lacks funds, a missed payday is logged; after 2 consecutive missed paydays, the employee autonomously resigns due to insolvency.
- **Informal Day Labor**: Unemployed or cash-depleted agents can perform day labor (`jornalero`) earning immediate cash ($3.00 to $8.00) in exchange for physical energy and hunger accumulation.

#### 3.3 Housing, Tenancy & Precarity (`HousingEngine`)
- **Housing Stock**: Tracks residential units with capacity, location, habitability quality, and daily rent.
- **Rent Collection & Arrears**: Active leases charge daily rent. If the tenant possesses sufficient cash, rent transfers directly to the landlord's personal balance. If insolvent, rent arrears accrue and consecutive unpaid days increase.
- **Eviction Threshold**: Tenants exceeding the eviction threshold (default 4 days of unpaid rent) are evicted, terminating the lease and transitioning tenure to `TEMPORARY_ACCOMMODATION`, `SHELTER`, or `HOMELESS`.
- **Protective Buffers & Recovery**: Unhoused or evicted agents can seek refuge in community shelters or with family. Once an unhoused agent accumulates sufficient savings (e.g. $\ge \$12.00$ via day labor), they autonomously search for affordable rental units or mesones and recover into stable housing.

#### 3.4 Everyday Social & Leisure Engine (`EverydaySocialEngine`)
- **Autonomous Invitations**: Agents send `SocialInvitation` to friends or family for shared activities (dining out, visiting parks, playing sports).
- **Non-Deterministic Evaluation**: Invitations are not automatically accepted. The invitee evaluates:
  1. *Physical Exhaustion*: If $\text{energy} < 0.20$, declines to rest.
  2. *Financial Solvency*: If the outing has cost (e.g. dining) and the inviter did not offer to treat, cash-strapped agents decline.
  3. *Interpersonal Relational Trust*: Negative affection or rival status leads to refusal.
  4. *Personality Traits*: High extraversion increases acceptance probability; high introversion prefers solitude.

#### 3.5 Household Economy & Living Overhead (`HouseholdLedger`)
- **Consumption-Based Overhead**: Replaces artificial per-individual charges with a consolidated household ledger.
- **Utility Pooling**: Domestic water and electricity charges are paid by the designated household head or shared among working adults and deposited into the `community_utility_treasury`.
- **Pantry Food Cooking**: Cooking uses accumulated pantry inventory (corn, beans, cheese) without deducting cash.

---

### 4. REST API & Web UI Observability

The platform exposes complete Phase 1.5 telemetry across 7 REST endpoints and dedicated UI panels:
- `GET /api/labor/vacancies`: Open/filled requisitions, required skills, offered daily wages.
- `GET /api/labor/contracts`: Active contracts, daily payroll liabilities, cumulative wages paid.
- `GET /api/housing/units`: Housing inventory, occupancy rate, 7-tenure distribution.
- `GET /api/housing/leases`: Active leases, accumulated arrears, eviction history.
- `GET /api/commerce/establishments`: Verified GIS vs simulated businesses, cash boxes, daily sales.
- `GET /api/commerce/visits`: Real-time visit log, zero-purchase ratios, intent distribution.
- `GET /api/lifestyle/summary`: Social invitations, autonomous rejection reasons, community utility treasury.
- `Individual Explorer`: Displays individual housing tenure, employment status, and reservation wage badges.
