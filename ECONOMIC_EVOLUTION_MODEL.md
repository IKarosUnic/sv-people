# ECONOMIC EVOLUTION MODEL (PHASE 1.11)
## Structural Economic Transitions, Multi-Sectoral Production, Enterprise Solvency, Endogenous Crises, and Inequality Dynamics

**System**: SALTBOR Synthetic-Human Society Simulation Platform  
**Subsystem**: Economic Civilization Core (`saltbor.civilization.economy`)  
**Language / Environment**: Python 3.12–3.14 (Validated on Python 3.14.5, Windows 11)  
**Status**: ACTIVE PRODUCTION SPECIFICATION  

---

### 1. Executive Summary

The Economic Civilization Engine [economy.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/economy.py) models structural economic transformations across multi-generational time horizons. Rather than modeling economic development as an arbitrary monotonic increase in wealth or GDP, the engine simulates dynamic shifts between productive sectors, enterprise lifecycles, market concentration, endogenous debt crises, and intergenerational wealth inequality.

Crucially, the foundational rule of SALTBOR economics is preserved: **Accounting Conservation is Absolute** ($\sum \text{Debits} = \sum \text{Credits}$). No money, agricultural harvest, or physical capital is ever materialized out of thin air to engineer a desired economic outcome.

---

### 2. Sectoral Structure of the Economy

Production and employment are distributed across eight distinct economic sectors:

```python
class EconomicSector(str, Enum):
    AGRICULTURE = "agriculture"                # Staple crops: milpa (maize, beans, squash), sorghum, coffee
    FISHING = "fishing"                        # Coastal and estuarine artisanal fisheries
    INFORMAL_COMMERCE = "informal_commerce"    # Tiendas, pulperías, street vendors, rural tianguis
    ARTISANAL = "artisanal"                    # Pottery, weaving, carpentry, metalworking
    MANUFACTURING = "manufacturing"            # Light processing, food packaging, agro-industrial mills
    SERVICES = "services"                      # Transportation (mototaxis, pickups), repair, domestic labor
    PUBLIC_COMMUNAL = "public_communal"        # ADESCO maintenance, municipal infrastructure, health/schools
    FINANCIAL_COMMUNAL = "financial_communal"  # Informal cuchubales, credit cooperatives, fiado credit
```

#### Sectoral Transformation Mechanisms

As a civilization evolves:
- **Agrarian Baseline**: Early or rural settlements concentrate 70–80% of labor in `AGRICULTURE`.
- **Commercial Specialization**: Settlements with high road connectivity and market squares transition toward `INFORMAL_COMMERCE` and `SERVICES`.
- **Artisanal & Manufacturing Emergence**: As practical innovations (metal silos, looms, mechanical presses) diffuse, secondary production expands.
- **De-industrialization / Primarization**: Severe crises or infrastructure breakdown can force an economy to revert from specialized commerce back to subsistence agriculture.

---

### 3. Enterprise Lifecycle and Solvency Dynamics

Enterprises are autonomous economic entities owned by individuals, families, or worker cooperatives.

```python
class EnterpriseStatus(str, Enum):
    ACTIVE = "active"              # Solicitous, trading, solvent
    DISTRESSED = "distressed"      # Operating at negative net margins, drawing down capital reserves
    INSOLVENT = "insolvent"        # Cash reserves exhausted, unable to meet debt or payroll obligations
    LIQUIDATED = "liquidated"      # Closed, assets auctioned or repossessed, employees dismissed
```

#### 3.1 Enterprise Data Schema

```python
@dataclass
class Enterprise:
    enterprise_id: str
    name: str
    sector: EconomicSector
    founder_id: str
    owner_id: str
    capital_usd: float
    annual_revenue_usd: float = 0.0
    annual_costs_usd: float = 0.0
    employees_ids: List[str] = field(default_factory=list)
    location_settlement_id: str = ""
    status: EnterpriseStatus = EnterpriseStatus.ACTIVE
    consecutive_loss_years: int = 0
    debt_usd: float = 0.0
```

#### 3.2 Operating Solvency & Payroll Mechanics

During each annual step, an enterprise computes:
1. **Gross Revenue**: Derived from local consumer purchasing power, trade volume, and sector productivity.
2. **Operating Costs**: Derived from input materials, asset maintenance, and employee wages.
3. **Net Margin**: $\Pi = \text{Revenue} - \text{Costs}$.
4. **Cash Reserve Update**: $\text{Capital}_{t+1} = \text{Capital}_t + \Pi$.

If $\text{Capital}_{t+1} < 0$, the business enters `DISTRESSED` status and seeks informal credit or informal forbearance (*fiado*). If losses continue for consecutive years and debt cannot be refinanced, the business is declared `INSOLVENT` and liquidated.

#### 3.3 Liquidation with Accounting Conservation

Upon liquidation:
1. Remaining physical or liquid capital is gathered: $C_{\text{rem}}$.
2. Outstanding debt $D$ is paid to creditors: $\text{Repayment} = \min(C_{\text{rem}}, D)$.
3. If $C_{\text{rem}} > D$, residual equity $C_{\text{rem}} - D$ is transferred to the owner's personal wealth.
4. If $C_{\text{rem}} < D$, creditors absorb the loss as bad debt write-off.
5. All employees are released into the labor pool as unemployed.

---

### 4. Endogenous Economic Crises and Recovery

Crises emerge endogenously through multiple plausible mechanisms:
- **Supply Disruptions**: Extreme drought destroys agricultural yield, depriving agro-processors of raw inputs.
- **Resource Scarcity**: Depletion of local water tables forces irrigation networks to cease operation.
- **Indebtedness Cascades**: Widespread default on informal credit (*fiado*) freezes local commerce.
- **Infrastructure Collapse**: Road or bridge failure isolates rural producers from urban markets.

```mermaid
flowchart LR
    Drought["Severe Drought (Water < 0.20)"] --> CropLoss["Agricultural Yield Drops 60%"]
    CropLoss --> IncomeLoss["Household Incomes Collapse"]
    IncomeLoss --> Default["Consumers Default on Fiado Dues"]
    Default --> TiendaFailure["Retail Tiendas Go Insolvent"]
    TiendaFailure --> Unemployment["Employees Dismissed"]
    Unemployment --> Exodus["Out-Migration to Secondary Settlements"]
```

Recovery is never guaranteed. Recovery requires active human adaptation: either technological innovation (drip irrigation, organic compost), capital restructuring via communal *cuchubales*, or labor reallocation into resilient sectors.

---

### 5. Intergenerational Inequality Dynamics

The engine tracks wealth distribution continuously using standard econometric indices:

#### 5.1 Gini Coefficient of Wealth

$$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |w_i - w_j|}{2 n \sum_{i=1}^n w_i}$$

Where $w_i$ is the total wealth of individual $i$, and $n$ is the total living population.

#### 5.2 Palma Ratio

$$\text{Palma} = \frac{\text{Share of Wealth of Top 10\%}}{\text{Share of Wealth of Bottom 40\%}}$$

Inequality trajectories exhibit realistic Kuznets-like cycles:
- **Agrarian Equality**: Early settlements with equal parcel sizes exhibit low Gini ($G \approx 0.25 - 0.35$).
- **Commercial Divergence**: As successful merchants accumulate commercial capital and acquire multiple parcels, Gini rises ($G \approx 0.50 - 0.65$).
- **Inheritance Dispersion**: Probate partitions across large families disperse dynastic fortunes, moderating runaway inequality across generations.
