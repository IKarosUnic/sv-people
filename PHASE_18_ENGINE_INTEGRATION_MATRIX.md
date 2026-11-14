# SALTBOR — FASE 1.8: MATRIZ DE INTEGRACIÓN DE MOTORES
## Ecosistema de Subsistemas, Dependencias, Flujos de Ejecución y Cobertura Observable

**Fecha:** 13 de noviembre de 2026  
**Criterio de clasificación estricto:**  
- **IMPLEMENTED:** Existe código funcional y clases importables.
- **INTEGRATED:** Participa activamente en el ciclo de ejecución `SimulationRunner.step()`, `ExtensionRuntime` o el orquestador sin atajos.
- **OBSERVABLE:** Sus métricas o estados pueden ser inspeccionados en la API REST y la UI frontend.
- **VALIDATED:** Posee pruebas unitarias e hipótesis experimentales verificadas con datos empíricos.
- **DORMANT:** Código implementado que NO se ejecuta en el loop activo de la simulación.
- **PARTIAL:** Participa en la simulación pero mediante simplificaciones sintéticas (p. ej., teletransportación o probabilidades abstractas sin restricciones físicas).

---

## 1. MATRIZ INTEGRAL DE SUBSISTEMAS

| Subsistema / Motor | Módulo | Estado Pre-1.8 | Estado Objetivo 1.8 | Desencadenador / Ciclo | Persistencia | Exposición API / UI |
|:---|:---|:---:|:---:|:---|:---|:---|
| **SyntheticHuman** | `saltbor/population/human.py` | INTEGRATED | INTEGRATED | Cada tick (secuencia planificada) | SQLite (`humans`) | API `/api/individuals/*`, Dossier completo |
| **PhysicalState** | `saltbor/population/physical_state.py` | INTEGRATED | INTEGRATED | Cada tick (degradación y consumo) | JSON en `humans` | Telemetría biofísica en roster e inspector |
| **PsychologicalState / Engine** | `saltbor/psychology/engine.py` | INTEGRATED | INTEGRATED | Cada tick (eventos OCC + LOD) | SQLite (`psychology_timeline`) + JSON | API `/api/psychology/*`, Panel psicológico UI |
| **Personality (Big Five)** | `saltbor/cognition/personality/traits.py` | INTEGRATED | INTEGRATED | Cada tick (deriva lenta y afrontamiento) | JSON en `humans` | Dossier del individuo |
| **EmotionState / OCC** | `saltbor/cognition/emotions/` | INTEGRATED | INTEGRATED | Evaluación OCC por evento | JSON en `humans` | Indicadores de valencia, afecto y emociones |
| **MemoryEngine (Asociativa)** | `saltbor/cognition/memory/` | INTEGRATED | INTEGRATED | Por evento + consolidación diaria | SQLite (`memories_*`) | Memoria reciente y recuerdos reconstruidos |
| **DecisionEngine (MAUT/GOAP)** | `saltbor/cognition/decision/engine.py` | INTEGRATED | INTEGRATED | Al terminar actividad / tick libre | En eventos de decisión | Trazas de decisión y razonamiento |
| **GoalAutonomyLifecycle** | `saltbor/cognition/goals/` | INTEGRATED | INTEGRATED | Generación por necesidades y metas | SQLite (`goals`) | Objetivos activos en dossier |
| **Individual / Collective KG** | `saltbor/knowledge/layers/` | PARTIAL | INTEGRATED | Eventos epistémicos y científicos | SQLite (`knowledge_triples`) | Visor de grafo de conocimiento |
| **SocialEngine / NetworkEngine** | `saltbor/social/engine.py` | INTEGRATED | INTEGRATED | Interacciones y decaimiento diario | SQLite (`relationships`, `social_edges`) | Matriz social, sociograma y amistades |
| **CommunityFormationEngine** | `saltbor/social/community/engine.py` | INTEGRATED | INTEGRATED | Evaluación diaria de afinidades | SQLite (`communities`) | Comunidades emergentes y ADESCOs |
| **RomanceEngine** | `saltbor/social/romance/engine.py` | INTEGRATED | INTEGRATED | Ciclo diario de cortejo e infidelidad | JSON en `phase15_extension` | Eventos románticos y estado de pareja |
| **FamilyCaregivingEngine** | `saltbor/lifecycle/family/caregiving.py`| INTEGRATED | INTEGRATED | Diario: cuidado de niños y enfermos | JSON en `phase15_extension` | Cargas de cuidado y redes de apoyo familiar |
| **LifeEventsCoordinator** | `saltbor/lifecycle/life_events.py` | INTEGRATED | INTEGRATED | Diario: nacimientos, uniones, duelo | JSON en `phase15_extension` | Registro demográfico e historial vital |
| **CommercialEngine** | `saltbor/economy/commerce/` | PARTIAL | INTEGRATED | Al visitar comercios (7 intenciones) | SQLite (`commercial_establishments`) | Puestos de mercado, pulperías y pupuserías |
| **LaborMarketEngine** | `saltbor/economy/labor/market.py` | INTEGRATED | INTEGRATED | Diario: nóminas, vacantes y jornadas | SQLite (`labor_contracts`, `vacancies`)| Panel de empleo, contratos y salarios |
| **HousingEngine** | `saltbor/economy/housing/engine.py` | INTEGRATED | INTEGRATED | Diario: cobro de renta, mora, desalojo| SQLite (`housing_units`, `leases`) | Unidades habitacionales y estado de tenencia |
| **HouseholdLedger** | `saltbor/economy/household/ledger.py` | INTEGRATED | INTEGRATED | Diario: gastos fijos de servicios | En memoria consolidada en tick diario | Balance de hogares y tesorería comunal |
| **InformalCommerceEngine** | `saltbor/economy/salvadoran/` | INTEGRATED | INTEGRATED | Por eventos de compra/fiado | SQLite (`businesses`) | Cuentas de fiado y pulperías |
| **RemittanceEngine** | `saltbor/economy/salvadoran/` | INTEGRATED | INTEGRATED | Periódico (cada 2880 ticks / 30 días) | JSON en `phase15_extension` | Perfiles de remesas familiares |
| **HealthEngine** | `saltbor/health/engine.py` | INTEGRATED | INTEGRATED | Diario: contagios, progresión clínica | JSON en `phase15_extension` | Condiciones activas, incapacidad y tratamientos |
| **MisfortuneEngine** | `saltbor/accidents/engine.py` | INTEGRATED | INTEGRATED | Diario: accidentes viales, laborales | JSON en `phase15_extension` | Registro de siniestros y contingencias |
| **EnvironmentEngine** | `saltbor/world/environment/weather.py` | INTEGRATED | INTEGRATED | Cada tick: temperatura, lluvia, clima | En memoria / `simulation_state` | Condiciones meteorológicas en UI |
| **SalvadoranClimateEngine** | `saltbor/world/salvadoran/climate.py` | INTEGRATED | INTEGRATED | Cada tick: estación seca vs lluviosa | En memoria | Clima estacional y riesgos hidrológicos |
| **GISEngine (STRtree)** | `saltbor/world/gis/engine.py` | INTEGRATED | INTEGRATED | Consultas espaciales de polígonos | Carga de GeoJSON pilot zone | Mapa 2.5D, capas vectoriales |
| **IngestedGeography (OSM)** | `saltbor/datasets/gis/pipeline.py` | INTEGRATED | INTEGRATED | Carga bajo demanda en viewport | SQLite (`geography.sqlite`) | Endpoints `/api/geography/*` |
| **OSMRoadNetwork (Dijkstra)** | `saltbor/world/geographic/osm_router.py`| DORMANT | INTEGRATED | Enrutamiento paso a paso de viajeros | En memoria desde `geography.sqlite` | Rutas viales reales, tiempos de viaje |
| **TransportationEngine** | *Nuevo en Fase 1.8* | NO EXISTÍA | INTEGRATED | Cada tick: progresión en tránsito vial | En memoria + persistencia de viaje | Trazas de desplazamiento en tiempo real |
| **WorldInteractionEngine** | `saltbor/world/interaction/` | PARTIAL | INTEGRATED | Interacción física y capacidades locales| JSON en `phase15_extension` | Jerarquía de lugares, horarios y servicios |
| **DailyLifeSimulationEngine** | *Consolidado Fase 1.8* | PARTIAL | INTEGRATED | Planificación diaria y biorritmos | En `SyntheticHuman` y decisión | Rutinas cotidianas y flexibilidad |
| **ADESCOEngine** | `saltbor/social/salvadoran/community.py`| INTEGRATED | INTEGRATED | Semanal (cuchubales) + asambleas | JSON en `phase15_extension` | Faenas comunales y círculos de ahorro |
| **JudicialTribunal** | `saltbor/institutions/legal/` | INTEGRATED | INTEGRATED | Por eventos de litigio o disputa | En memoria / `events_log` | Expedientes judiciales y acuerdos de mediación|
| **CausalEventGraph** | `saltbor/events/causal_graph.py` | INTEGRATED | INTEGRATED | Suscripción global a `EventBus` | JSON en `phase15_extension` | Trazabilidad causal de antecedentes y efectos |
| **HistoricalMemoryEngine** | `saltbor/knowledge/salvadoran/history.py`| DORMANT | INTEGRATED | Absorción de crisis y memoria oral | SQLite (`memories_semantic`) | Narrativas históricas transmitidas |
| **IntegratedWorldSimulationEngine**| *Consolidado Fase 1.8* | DORMANT | INTEGRATED | Orquestación causal unificada | SQLite + JSON | Supervisión integral de la simulación |

---

## 2. ANÁLISIS DE INTERFACES Y CONTRATOS DE INTEGRACIÓN

```
                        ┌─────────────────────────────────────────────────────────┐
                        │             SimulationRunner.step(tick)                 │
                        └───────────────────────────┬─────────────────────────────┘
                                                    │
            ┌───────────────────────────────────────┼────────────────────────────────────────┐
            ▼                                       ▼                                        ▼
┌─────────────────────────┐             ┌─────────────────────────┐              ┌─────────────────────────┐
│   EnvironmentEngine     │             │ TransportationEngine    │              │ DailyLifeSimulation     │
│   - Lluvia y tormentas  │────────────►│ - Avance en tramos OSM  │◄─────────────│ - Planificación diaria  │
│   - Bloqueos de vías    │             │ - Tráfico y obstáculos  │              │ - Biorritmo y rutinas   │
└───────────┬─────────────┘             └───────────┬─────────────┘              └───────────┬─────────────┘
            │                                       │                                        │
            ▼                                       ▼                                        ▼
┌─────────────────────────┐             ┌─────────────────────────┐              ┌─────────────────────────┐
│ WorldInteractionEngine  │             │     SyntheticHuman      │              │    CommercialEngine     │
│ - Lugares y jerarquías  │◄───────────►│ - Posición física real  │◄────────────►│ - Capacidad y horarios  │
│ - Servicios y recursos  │             │ - Biología, mente, casa │              │ - Compras y vitrineo    │
└─────────────────────────┘             └───────────┬─────────────┘              └─────────────────────────┘
                                                    │
            ┌───────────────────────────────────────┼────────────────────────────────────────┐
            ▼                                       ▼                                        ▼
┌─────────────────────────┐             ┌─────────────────────────┐              ┌─────────────────────────┐
│  LaborMarket & Housing  │             │ Health & Misfortune     │              │   PsychologicalEngine   │
│ - Salarios de reserva   │             │ - Clínicas y saturación │              │ - Estrés por bloqueos   │
│ - Alquileres y desalojo │             │ - Accidentes en ruta    │              │ - Afrontamiento y crisis│
└─────────────────────────┘             └─────────────────────────┘              └─────────────────────────┘
                                                    │
                                                    ▼
                                        ┌─────────────────────────┐
                                        │  CausalEventGraph &     │
                                        │  HistoricalMemoryEngine │
                                        └─────────────────────────┘
```

Esta arquitectura garantiza que ninguna acción humana ni perturbación climática ocurra en el vacío, sino que propague sus efectos a lo largo de toda la estructura social y económica del entorno salvadoreño.
