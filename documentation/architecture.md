# Saltbor Cognitive & Simulation Architecture (Phase 0.2)

## 1. Executive Summary

Saltbor is an agentic, modular synthetic human and society simulation written in pure Python 3.14, NumPy, and Pydantic, backed by a persistent Write-Ahead-Logging (WAL) SQLite database.

Phase 0.2 marks the transition of the settlement's 20 initial inhabitants from rule-following agents into **evolving synthetic individuals**. Inhabitants develop emotions, memories, personality traits, personal values, procedural competencies, autonomous objectives, and directional interpersonal relationships over time.

Crucially, the entire core cognitive simulation executes algorithmically and deterministically without requiring per-tick Large Language Model (LLM) calls, achieving sub-millisecond tick latencies (~0.68 ms) and maintaining an extremely compact memory footprint (~0.57 KB per individual).

---

## 2. Core Architectural Pillars

### 2.1 Identity Continuity vs. Dynamic Mutability
- **HumanIdentity**: Immutable ontological anchor (`uid`, `serial`, `data_source`). Identity is permanent and never alters across simulation lifecycles.
- **Dynamic State**: Personality traits, emotions, memories, physical vitality, skills, and social bonds evolve continuously based on lived experiences.

### 2.2 Compositional Agent Aggregate Root
Every `SyntheticHuman` encapsulates distinct functional software engines:
```
SyntheticHuman
├── HumanIdentity (immutable UUID + serial)
├── Demographics (age, gender, occupation, income)
├── PhysicalState (energy, hunger, health, money, location, current activity)
├── PersonalityEngine
│   ├── 8 Trait Dimensions (OCEAN + risk_tolerance, patience, persistence)
│   ├── Dual Base / Current Fluctuation & Drift
│   ├── Biological Temperament Anchors
│   ├── Personal Values (Schwartz priorities: security, benevolence, achievement, tradition, autonomy)
│   ├── Learned Behavioral Patterns (coping heuristics)
│   └── Evolution Audit Log (causal provenance for baseline shifts)
├── EmotionalEngine
│   ├── 15 Discrete Emotion Channels (Joy, Sadness, Fear, Anger, Affection, Shame, Guilt,
│   │   Curiosity, Frustration, Anxiety, Satisfaction, Disappointment, Loneliness, Excitement, Motivation)
│   ├── Dynamic Decay Rates modulated by Regulation Capacity
│   ├── Expressiveness Threshold (should_express_externally)
│   └── Decision Weight Modulation (novelty, safety, social seeking, avoidance)
├── MemoryEngine
│   ├── WorkingMemory (Miller 7 ± 2 capacity buffer)
│   ├── EpisodicMemory (active salient memories + dormant historical archive)
│   ├── SemanticMemory (generalized world knowledge, verification, and contradiction tracking)
│   ├── ProceduralMemory (skills with power-law learning, confidence, atrophy, cross-skill transfer)
│   ├── Associative Store (emotional charges linked to locations and individuals)
│   └── MemoryConsolidator (accessibility decay, routine compression into semantic facts, dormant archiving)
├── CognitiveEngine (sensory perception, personality-biased selective attention)
├── LearningEngine (skill practice, knowledge distillation, failure adaptation)
├── AutonomyEngine
│   ├── Intrinsic Need-to-Goal Generation (biological, financial, skill, social, reconciliation)
│   └── Goal Lifecycle (planning steps, progress tracking, procrastination, modification, abandonment)
└── DecisionEngine
    ├── Multi-Attribute Utility Evaluation (needs, personality, emotions, goals, memory aversion/affinity)
    ├── Bounded Rationality & Personality-Modulated Exploration Noise
    └── DecisionTrace Recording (dominant factors and alternatives for auditability)
```

---

## 3. Cognitive Systems in Phase 0.2

### 3.1 Emotional Engine
- **15 Distinct Channels**: Supports joy, sadness, fear, anger, affection, shame, guilt, curiosity, frustration, anxiety, satisfaction, disappointment, loneliness, excitement, and motivation.
- **Coexistence & Independent Dynamics**: Multiple emotions coexist simultaneously with individual decay rates (e.g. anger decays rapidly, grief/sadness decays slowly).
- **Regulation Capacity**: Individual differences modulate emotional recovery speeds. Highly regulated individuals damp emotional distress faster.
- **Expressiveness Threshold**: Internal emotional intensity must surpass an individual's expressiveness threshold before being externalized in social interactions.
- **Decision Steering**: Emotional states dynamically modulate utility evaluations:
  - High Anxiety / Fear increases rest/safety drive and penalizes high-risk tasks.
  - High Loneliness amplifies socialization utility.
  - High Curiosity amplifies study and exploration utility.

### 3.2 Advanced Memory Engine
- **Dormant History Preservation**: Forgetting never deletes historical data. Inactive or routine memories undergo accessibility decay; when accessibility drops below retrieval thresholds, memories transition to a persistent dormant archive while preserving complete historical provenance.
- **Semantic Compression**: Repetitive routine events (e.g. eating at Comedor Doña María) are compressed into consolidated semantic beliefs with verification counters.
- **Associative Memory**:
  - Traumatic or unpleasant events record negative emotional associations with specific locations, producing measurable **location aversion** in future decision-making.
  - Positive experiences produce **place affinity**, increasing likelihood of revisiting.
- **Procedural Skills**:
  - Model: Proficiency level, experience points, practice count, learning rate, retention, and confidence.
  - **Diminishing Returns**: Power-law learning curve models realistic skill mastery.
  - **Skill Atrophy**: Extended disuse causes slight proficiency decay protected by retention.
  - **Cross-Skill Transfer**: Practicing a skill transfers 15% synergy XP to related skills within the same category.

### 3.3 Personality Evolution Engine
- **Four-Tier Architecture**:
  1. *Innate Temperament*: Immutable biological anchor.
  2. *Baseline Personality*: Evolving long-term trait configuration.
  3. *Current State*: Dynamic fluctuations driven by recent experiences that drift back toward baseline.
  4. *Personal Values & Patterns*: Schwartz value priorities and learned behavioral heuristics.
- **Causal Audit Log**: Every permanent base shift records its causal event type, magnitude, and tick in `evolution_history`.
- **Stress & Instability**: Accumulated stress increases personality volatility, allowing realistic behavioral regressions under severe adversity.
- **Social Influence**: Sustained interactions with respected peers gently nudge traits toward the peer's traits.

### 3.4 Autonomy & Goal Lifecycle
Inhabitants autonomously generate, plan, and evaluate personal objectives:
1. **Deficit / Aspiration Identification**: Deficits in physiological needs (hunger, fatigue), psychological needs (social, achievement), or financial resources trigger goal candidate generation.
2. **Feasibility Evaluation**: Assesses resource constraints, personality suitability, and competing demands.
3. **Structured Plan Formation**: Generates sequential actionable steps (e.g. `['travel_to_learning_center', 'study_technique', 'practice_and_master']`).
4. **Execution & Evaluation**: Advances step indices as progress accumulates.
5. **Procrastination & Adaptation**: Obstacles trigger hesitation (procrastination) or structural plan adjustments (modification). Insurmountable roadblocks lead to rational abandonment with recorded rationale.

### 3.5 Bounded Rationality Decision Engine
- Evaluates candidate actions (sleep, rest, eat/cook, work, socialize, study, shop, exercise, relax) using multi-attribute utility equations.
- Incorporates active goals (utility boosts for matching actions), location memory aversion/affinity, and emotional weights.
- Applies softmax action selection modulated by personality exploration noise (high openness/risk increases exploration; high conscientiousness/patience increases deterministic exploitation).
- Emits detailed `DecisionTrace` explanations recording dominant factors and rejected alternatives.

---

## 4. Social Engine & Directional Dynamics

- **Directional Attitudes (`DirectionalAttitude`)**: Person A's perception of Person B is decoupled from Person B's perception of Person A.
  - Tracks asymmetric trust, affinity, respect, familiarity, and rivalry.
- **Dynamic Arcs**:
  - Cooperative interactions progressively build trust and respect.
  - Conflicts and betrayals trigger severe trust erosion and spike rivalry.
  - Unilateral outreach (e.g. apologies) creates directional asymmetry.
  - Sincere reconciliation restores mutual bonds over time.
- **Complete Interaction History**: Every interpersonal exchange records tick, type, outcome, and intensity.

---

## 5. Settlement Geography & World Integration

Saltbor settlement spans a 500m × 500m spatial layout with 16 functional buildings:

| Location | Category | Capacity | Schedule | Key Activities |
|---|---|---|---|---|
| Plaza Mayor de Saltbor | Public Space | 60 | 24/7 | Socialize, Relax, Transit |
| Mercado Municipal | Commercial | 25 | 06:00–19:00 | Shop, Socialize, Work |
| Comedor Doña María | Commercial | 20 | 06:00–21:00 | Eat, Socialize, Work |
| Escuela Comunal | Educational | 35 | 07:00–16:00 | Study, Socialize, Work |
| Taller El Roble | Workplace | 12 | 07:00–17:00 | Work (Carpentry/Welding) |
| Cooperativa Agrícola | Workplace | 18 | 06:00–17:00 | Work, Shop, Socialize |
| Clínica de Salud | Workplace | 15 | 07:00–19:00 | Work, Rest |
| Parque La Ceiba | Recreational | 50 | 05:00–22:00 | Exercise, Relax, Socialize |
| Casa Comunal | Public Space | 40 | 08:00–22:00 | Socialize, Study, Organize |
| Casas Residenciales (1–6) | Residential | 5 each | 24/7 | Sleep, Rest, Cook, Eat |
| Colinas y Sendero del Río | Natural | 100 | 05:00–18:00 | Exercise, Relax |

Pathfinding uses Dijkstra's shortest-path algorithm over the road network, calculating travel times at standard adult walking speeds (~1.4 m/s).

---

## 6. Event-Driven Architecture & Persistence

- **Simulation Clock**: 1 tick = 15 simulated minutes (96 ticks = 24 simulated hours).
- **Pub/Sub EventBus**: Fully decoupled event dispatch with causal provenance tracing (`cause_event_id`).
- **SQLite Persistence**: Central database operating in Write-Ahead-Logging (WAL) mode. Saves full cognitive state (identity, demographics, physical vitality, personality traits, temperament, values, patterns, active emotions, regulation parameters, procedural skills, episodic records, and autonomous goals).

---

## 7. Performance & Resource Consumption

Measurements recorded on standard workstation hardware with 20 individuals:
- **Tick Latency**: 0.65 – 0.75 ms per tick (Target < 50 ms: **PASS**)
- **Simulation Speed**: ~800 – 1,000 ticks/second (> 8 simulated days per real second)
- **Memory Footprint**: ~0.57 KB per human (Target < 1,024 KB: **PASS**)
- **External Dependency**: 0 mandatory LLM API calls. Fully autonomous and offline capable.

---

## 8. Real Geographic World & El Salvador Integration (Phase 0.8)

In Phase 0.8, the settlement geography is expanded into the sovereign territory of **El Salvador**:
- **Official Political-Administrative Structure**: 14 departments, 44 municipalities, 262 districts (May 2024 legislative decree).
- **Cartographic Provenance**: CNR map platform integration (95 spatial layers, SIRGAS ES2007 projection), authorized Google Maps Platform client (zero scraping), and OSM (ODbL).
- **Establishment Directory**: Real commercial, public service, cultural, and productive facilities with 7 validation states (`CONFIRMADO`, `PENDIENTE_VALIDACION`, `DESACTUALIZADO`, `CERRADO`, `TRASLADADO`, `DUPLICADO`, `INFORMACION_INSUFICIENTE`).
- **Spatial Indexing & Navigation**: Pure Python 2D spatial grid index (<0.02 ms lookup) with Dijkstra multimodal routing along CA-1, CA-2, CA-4, and bridges over Río Lempa.
- **Socio-Economic & Cognitive Integration**: Commodity freight pricing, pupusería unit economics, walking-radius fiado microcredit, individual epistemic spatial belief states, and social rumor debunking.
- **Validation**: 20/20 empirical experiments passed (`EXP_08_A` to `EXP_08_T`). See [`documentation/phase08_real_geographic_world.md`](file:///c:/GIT%20HUB/sv%20people/documentation/phase08_real_geographic_world.md) for complete technical specifications.
