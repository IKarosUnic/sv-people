# SALTBOR — PHASE 1.2.2 ARCHITECTURE AUDIT
## COMPREHENSIVE STRUCTURAL AUDIT, ENGINE INTEGRATION, TYPING & COUPLING ANALYSIS

**Fecha:** 10 de Noviembre de 2026  
**Auditoría:** Arquitectura de Software e Ingeniería de Sistemas Complejos  
**Repositorio:** `sv people` / Rama `master`  
**Estado del Código:** 100% Python 3.14.5 compatible, Pydantic v2 validado, SQLite WAL  
**Cobertura de Pruebas:** 359 tests (100% PASS en 9.94s)  

---

## 1. MAPA GENERAL DE LA ARQUITECTURA DE SALTBOR

El sistema SALTBOR se organiza en 9 subsistemas de dominio claramente demarcados, interactuando de manera desacoplada a través de interfaces tipadas y eventos de simulación:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MAPA DE CAPAS DE SALTBOR                                  │
├─────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 1. Core & Fundamentos   │ Types, Identity, Configuration, Clocks, Exceptions           │
│ 2. Cognición Individual │ Memory (Working/Episodic/Semantic/Procedural), Goals, Beliefs│
│ 3. Estructura Social    │ Relational Engine, Directional Attitudes, Communities, Faction│
│ 4. Economía y Recursos  │ Currency, Credit, In-Kind Settlement, Inventory, Caravans    │
│ 5. Geografía y Espacio  │ GIS Cartography, Topography, Settlement Hierarchy, Migration │
│ 6. Cultura y Saberes    │ Traditions, Values, Tech Discovery, Knowledge Graph, P2P     │
│ 7. Dinámica Civilizatoria│ Historical Memory, Vector 18D, Stratification, Crisis Relief│
│ 8. Persistencia y Datos │ SQLite WAL Engine, Transaction Isolation, Recovery Forensics │
│ 9. Banco Experimental   │ BaseExperiment, SimulationLaboratory, Runner, 100+ Tests    │
└─────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. AUDITORÍA DETALLADA POR MOTOR Y SUBSISTEMA

### 2.1 Subsistema de Cognición y Creatividad (`saltbor.cognition`)
- **Archivos Auditados:**
  - `saltbor/cognition/memory/engine.py`
  - `saltbor/cognition/creativity/engine.py`
  - `saltbor/cognition/epistemic/beliefs.py`
  - `saltbor/cognition/personality/engine.py`
- **Hallazgos Arquitectónicos:**
  - El motor de memoria consolida limpiamente memorias de trabajo en registros episódicos cuando la saliencia supera $0.15$.
  - En la Fase 1.2.2 se introdujo `DiscoveryCycleStage` con sus 12 fases bien delimitadas y la estructura `DiscoveryCycleTrace`.
  - La función `initiate_blind_discovery` desacopla completamente el problema experimental de cualquier etiqueta o nombre humano preexistente.
- **Acoplamiento e Invariantes:** Desacoplado; no realiza llamadas circulares a motores sociales ni económicos.

### 2.2 Subsistema Social y Comunitario (`saltbor.social`)
- **Archivos Auditados:**
  - `saltbor/social/engine.py`
  - `saltbor/social/relationship.py`
  - `saltbor/social/community/engine.py`
- **Hallazgos Arquitectónicos:**
  - `Relationship` mantiene la normalización de claves simétricas (`_key(a, b) = (min, max)`), previniendo duplicados bidireccionales.
  - La introducción de `DirectionalAttitude` en Fase 1.2 permite modelar asimetrías psicológicas (A confía en B, pero B desconfía de A).
  - En la Fase 1.2.2 se auditó y validó que `trigger_fission` redistribuye los miembros activos de manera conservativa (número total de agentes se preserva de forma estricta).
- **Puntos de Atención:** `_auto_promote` utiliza umbrales fijos para pasar de `ACQUAINTANCE` a `FRIEND`. Se sugiere parametrizar según rasgos de personalidad en Fase 1.3.

### 2.3 Subsistema Económico y de Trueque (`saltbor.economy`)
- **Archivos Auditados:**
  - `saltbor/economy/commodity/payment_in_kind.py`
  - `saltbor/economy/credit.py`
  - `saltbor/economy/inventory/container.py`
- **Hallazgos Arquitectónicos:**
  - `InKindPaymentEngine` opera como amortiguador de último recurso cuando la liquidez fiduciaria es nula.
  - Valora los bienes según precios de mercado locales, respetando la masa del inventario en kg y unidades volumétricas.
  - Evita el colapso sistémico del crédito sin romper las obligaciones contractuales.

### 2.4 Subsistema Civilizatorio y Territorial (`saltbor.civilization`)
- **Archivos Auditados:**
  - `saltbor/civilization/society_vector.py`
  - `saltbor/civilization/settlement.py`
  - `saltbor/civilization/technology.py`
  - `saltbor/civilization/history.py`
- **Hallazgos Arquitectónicos:**
  - `SocietalIdentityVector` se ha ampliado en la Fase 1.2.2 con cálculos tensoriales para distancias Manhattan ($L_1$), Euclidiana ($L_2$) y Mahalanobis ($D_M$), así como matrices de correlación $18 \times 18$.
  - `SettlementEvolutionEngine` modela la degradación y el abandono territorial como consecuencia estocástica de sequías y hambrunas.

### 2.5 Subsistema de Persistencia (`saltbor.persistence`)
- **Archivos Auditados:**
  - `saltbor/persistence/database.py`
- **Hallazgos Arquitectónicos:**
  - SQLite configurado en modo WAL (`PRAGMA journal_mode=WAL`), con checkpoints automáticos e índices optimizados en claves primarias y campos temporales (`tick`).
  - Capacidad probada de realizar 1,000 inserciones estructuradas en $< 4.0$ ms.
  - Comportamiento transaccional robusto: caídas intermedias son revertidas por el motor SQLite sin dejar inconsistencias lógicas.

---

## 3. MATRIZ DE INTERACCIÓN Y DEPENDENCIAS ENTRE MOTORES

```
                 [Cognición] ──> [Memoria] ──> [Creencias]
                      │
                      ▼
               [Social Engine] ──> [Relaciones Asimétricas]
                      │                     │
                      ▼                     ▼
               [Comunidades] <──> [Fisión y Mediación]
                      │
                      ▼
               [Asentamientos] <──> [Economía y Trueque]
                      │                     │
                      ▼                     ▼
               [Persistencia SQLite WAL (Física en Disco)]
```

- **Invocaciones Directas:** Reducidas a fachadas de alto nivel.
- **Puntos de Acoplamiento Débil:**
  - Transmisión cultural depende de la red social para determinar vecindad.
  - Dación en pago consulta el inventario individual sin modificar el libro mayor bancario global.
  - El vector societal lee métricas de múltiples motores pero es de solo lectura (inmutable tras construcción).

---

## 4. DETECCIÓN DE UMBRALES RÍGIDOS Y DEUDA DE DISEÑO

Durante la auditoría se identificaron las siguientes heurísticas fijas en el código:

1. **Umbral de saliencia mnémica ($0.15$):** En `MemoryEngine`, solo eventos con importancia $\ge 0.15$ se archivan en memoria episódica. Este umbral es fijo y no varía según el nivel de estrés o la personalidad del individuo.
2. **Bandas poblacionales de asentamientos:** `CASERIO` ($< 20$), `ALDEA` ($20-50$), `PUEBLO` ($50-150$), `VILLA` ($150-500$). Si bien son históricamente verosímiles, representan discontinuidades escalares rígidas.
3. **Bonificación de reacción puzolánica ($+15\%$):** En `EXP_122_C`, la sinergia mecánica está parametrizada con una constante multiplicativa en lugar de un cálculo termodinámico cinético continuo.

---

## 5. CUMPLIMIENTO DE ESTÁNDARES Y TIPADO

- **Tipado Estricto:** Código anotado al 100% con tipos PEP 484/526/585/604.
- **Pydantic v2:** Uso consistente de `BaseModel`, `Field(ge=..., le=...)` y validadores nativos.
- **Compatibilidad Python 3.14.5:** Cero uso de módulos obsoletos; compatibilidad verificada en la máquina del usuario.
- **Pruebas Automatizadas:** 359 tests ejecutados en $9.94$ segundos en Windows 11 sin advertencias críticas.
