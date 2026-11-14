# CULTURAL EVOLUTION MODEL (PHASE 1.11)
## Cultural Traditions, Desuetudo Decay, Generational Transmission, Extinction, and Pluralism

**System**: SALTBOR Synthetic-Human Society Simulation Platform  
**Subsystem**: Cultural Evolution (`saltbor.social.culture.evolution`)  
**Language / Environment**: Python 3.12–3.14 (Validated on Python 3.14.5, Windows 11)  
**Status**: ACTIVE PRODUCTION SPECIFICATION  

---

### 1. Executive Summary

Culture in SALTBOR is not a decorative aesthetic layer; it is an active evolutionary system of shared meanings, rituals, culinary customs, norms, and organizational forms that coordinate collective action and social solidarity.

The `CulturalEvolutionEngine` [evolution.py](file:///c:/GIT%20HUB/sv%20people/saltbor/social/culture/evolution.py) models the lifecycle of cultural traditions. Traditions emerge from community life, diffuse through social networks, reinforce communal cohesion, and gradually decay through lack of practice (**desuetudo**) or become permanently **extinct** when their human practitioners perish.

---

### 2. Cultural Tradition Taxonomy

Traditions are organized into eleven distinct categories reflecting Salvadoran rural and urban culture:

```python
class CulturalCategory(str, Enum):
    CULINARY_PRACTICE = "culinary_practice"            # Pupusas, atole shuco, tamales, artisanal curing
    COMMERCIAL_CUSTOM = "commercial_custom"            # "La rebaja" bargaining, fiado trust, marketplace days
    COMMUNAL_TRADITION = "communal_tradition"          # Patronal festivals, Día de la Cruz, agricultural blessings
    AGRICULTURAL_TECHNIQUE = "agricultural_technique"  # Traditional lunar planting calendars, terrace cropping
    ARTISANAL_CRAFT = "artisanal_craft"                # Morro carving, Ilobasco clay miniatures, loom textiles
    LANGUAGE_EXPRESSION = "language_expression"        # Salvadoran caliche idioms, Nahuat-pipil loanwords
    TEACHING_SYSTEM = "teaching_system"                # Family apprenticeships, community elder storytelling
    SOCIAL_NORM = "social_norm"                        # Compadrazgo (godparenting), mutual aid expectations
    ORGANIZATION_FORM = "organization_form"            # ADESCO communal assemblies, cuchubales, cooperative faenas
    ENVIRONMENTAL_KNOWLEDGE = "environmental_knowledge"  # Water source identification, medicinal herbs
    ARTS_RECREATION = "arts_recreation"                # Danza del Venado, traditional marimba, Torito Pinto
```

---

### 3. Cultural Tradition Data Structure

```python
@dataclass
class CulturalTradition:
    tradition_id: str
    name: str
    category: CulturalCategory
    origin_community_id: str
    description: str
    adopters: set[str] = field(default_factory=set)
    utility_score: float = 0.75                        # Practical or psychological benefit
    sacredness: float = 0.50                           # Emotional reverence / norm resistance to change
    fidelity: float = 1.0                              # Purity of practice relative to origin
    parameters: dict[str, float] = field(default_factory=dict)
    parent_tradition_id: Optional[str] = None          # For syncretic or evolved sub-traditions
    variation_notes: list[str] = field(default_factory=list)
    created_tick: int = 0
    last_practiced_tick: int = 0
    is_active: bool = True
    is_extinct: bool = False
```

---

### 4. Practice Frequency, Dormancy, and Desuetudo Decay

A cultural tradition survives only through continuous, active human enactment. When communities fail to organize patronal festivals, cook traditional foods, or observe communal customs, traditions experience legal and cultural **desuetudo** (decay from non-use).

#### 4.1 Dormancy Mechanics (`decay_unpracticed_traditions`)

Every tradition tracks `last_practiced_tick`. If the elapsed time since its last practice exceeds a dormancy threshold ($\Delta t_{\text{dormancy}} > 4000$ ticks, equivalent to ~40 simulated days):
1. `is_active` is flagged `False`.
2. The tradition transitions into **dormant status**.
3. Communal cohesion benefits associated with the tradition are temporarily deactivated.

#### 4.2 Cultural Revitalization
If a dormant tradition is celebrated again before extinction occurs (e.g., an inspired community leader organizes a revival patronal festival), `is_active` is restored to `True`, and `last_practiced_tick` is updated.

---

### 5. Cultural Extinction Mechanics (`check_cultural_extinction`)

When demographic transitions or epidemics decimate human cohorts, traditions face the risk of **permanent cultural extinction**:

$$\text{Living Practitioners} = \text{Adopters} \cap \text{AliveInhabitants}$$

If:
$$\left| \text{Living Practitioners} \right| = 0$$

The tradition transitions permanently:
- `is_active = False`
- `is_extinct = True`

Once a tradition is marked extinct, it cannot be revived through casual imitation, as the oral repertoire, tactile technique, or sacred formulas have vanished from living human memory.

---

### 6. Pluralism and Syncretism

Different settlements can develop distinct, localized cultural repertoires:
- Coastal settlements develop fishing rituals, boat-blessing customs, and seafood-curing traditions.
- Highland agrarian caseríos develop corn-harvest ceremonies, terracing faenas, and rain-petition prayers.

When individuals migrate between settlements:
- They introduce their origin traditions to new communities.
- Syncretic variations emerge (`parent_tradition_id` references ancestral customs while `variation_notes` record local adaptations).
- Cultural diversity index ($H_{\text{culture}} = -\sum p_i \ln p_i$) is continuously monitored across the territory.
