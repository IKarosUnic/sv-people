# SALTBOR — FASE 1.9: AUDITORÍA DE ARQUITECTURA SOCIAL E INSTITUCIONAL
## Sociedad Emergente, Dinámicas Institucionales, Gobernanza Colectiva y Evolución Social

**Fecha de auditoría:** 13 de noviembre de 2026  
**Línea base:** SALTBOR Fase 1.8 (594/594 tests pasando, 100% verde)  
**Entorno de ejecución:** Windows 11 / AMD Ryzen 7 8700G (16 CPUs) / 32 GB DDR5 RAM / Python 3.14.5 / SQLite 3.49+ (WAL mode)  
**Autoridad:** Arquitecto Principal, Especialista en Sistemas Multiagente, Simulación Social, Economía Institucional y Vida Artificial de SALTBOR.

---

## 1. RESUMEN EJECUTIVO DE LA AUDITORÍA

Se ha llevado a cabo una inspección forense rigurosa de los 124 subsistemas y motores de SALTBOR, analizando contratos de interfaz, orquestación en [SimulationRunner](file:///C:/GIT%20HUB/sv%20people/saltbor/simulation/runner.py), adaptadores de [IntegratedWorldSimulationEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/simulation/integrated_world.py), [ExtensionRuntime](file:///C:/GIT%20HUB/sv%20people/saltbor/simulation/extension_runtime.py), persistencia en [schema.py](file:///C:/GIT%20HUB/sv%20people/saltbor/persistence/schema.py), endpoints en [api.py](file:///C:/GIT%20HUB/sv%20people/saltbor/visualization/api.py) y frontend en [app.js](file:///C:/GIT%20HUB/sv%20people/saltbor/visualization/web/app.js) e [index.html](file:///C:/GIT%20HUB/sv%20people/saltbor/visualization/web/index.html).

### Diagnóstico de la Fase 1.8 a la Fase 1.9

La Fase 1.8 logró con éxito la unificación física, cinemática y de vida cotidiana (tránsito real en OpenStreetMap sin teletransportación, aforos e inventarios en `PlaceProfile`, fases diurnas culturales y eventos causales ambientales). Sin embargo, en el plano de la **sociedad colectiva, las instituciones y la gobernanza**, la auditoría revela un estado fragmentado con módulos valiosos pero aislados:

1. **Fragmentación y Duplicación de Modelos Organizacionales e Institucionales:**
   - Existen definiciones redundantes de propuestas colectivas: `OrganizationalProposal` en [saltbor/social/organization/engine.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/organization/engine.py), `InstitutionalProposal` en [saltbor/social/institutions/assembly.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/institutions/assembly.py), y otro `InstitutionalProposal` en [saltbor/institutions/governance.py](file:///C:/GIT%20HUB/sv%20people/saltbor/institutions/governance.py).
   - Existen tres conceptos paralelos de agregaciones sociales: `Community` en [saltbor/social/community/engine.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/community/engine.py), `SocialInstitution` en [saltbor/institutions/model.py](file:///C:/GIT%20HUB/sv%20people/saltbor/institutions/model.py), y `EmergentInstitution` en [saltbor/social/institutions/emergent.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/institutions/emergent.py).
   - Ninguno de estos motores gestiona el **ciclo de vida evolutivo completo**: surgimiento condicional a necesidades y confianza, cambio de propósito (mission drift), pérdida de legitimidad, escisión (fisión), fusión con otra entidad o disolución operativa.

2. **Ausencia de Gestión Colectiva de Recursos Comunes (Elinor Ostrom / CPR):**
   - Actualmente, el agua y los recursos ambientales se modelan a nivel biofísico individual (`PhysicalState.hydration`, riesgos de contaminación o deslaves) o como gasto general de servicios (`utility_treasury`).
   - No existe un motor unificado de **Recursos de Uso Común (Common-Pool Resources - CPR)** que implemente los principios de diseño de Elinor Ostrom: reglas de apropiación y provisión, monitoreo mutuo, sanciones graduadas, trazabilidad estricta de extracciones y mantenimiento, ni la dinámica de la "tragedia de los comunes" frente a la gobernanza comunitaria sostenible.

3. **Estratificación Social Unidimensional:**
   - La posición socioeconómica de los agentes se mide predominantemente por dinero en efectivo (`money`) o salario (`offered_daily_wage`).
   - Carece de un modelo multidimensional que combine: ingresos, patrimonio acumulado (vivienda, herramientas, ahorros), régimen de tenencia de vivienda, nivel educativo, prestigio ocupacional, centralidad en redes sociales, reputación y poder/influencia institucional.
   - Falta el cómputo longitudinal de desigualdad (coeficiente de Gini, índice de Palma) y matrices de transición de movilidad social (ascendente, descendente, persistencia intergeneracional).

4. **Gobernanza Asimétrica y Dinámicas de Conflicto Interorganizacional:**
   - El motor de toma de decisiones colectivas asume que todos los votantes tienen igual propensión y tiempo para votar, sin modelar asimetrías de poder, manipulación de información, abstención estratégica, disenso persistente ni ruptura de pactos.
   - El motor de conflictos ([saltbor/social/conflict/engine.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/conflict/engine.py)) resuelve disputas entre pares individuales, pero no disputas entre colectivos (e.g. comerciantes informales vs formales, comunidades vecinas compitiendo por agua de un pozo, disputas laborales entre peones y talleres).

5. **Transmisión Imperfecta del Conocimiento y la Cultura:**
   - La cultura posee categorías ricas ([saltbor/social/culture/evolution.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/culture/evolution.py)), pero la transmisión pedagógica en escuelas y talleres no está directamente conectada con la ganancia de capacidades observables en la toma de decisiones cotidianas del agente.

---

## 2. INVENTARIO Y CLASIFICACIÓN DE SUBSISTEMAS SOCIALES E INSTITUCIONALES

De acuerdo con las reglas de auditoría, cada componente se clasifica en una de las 6 categorías:
- **IMPLEMENTED**: Código base escrito y funcional.
- **INTEGRATED**: Conectado directamente a `SimulationRunner.step()`, `ExtensionRuntime.step()` o `IntegratedWorldSimulationEngine.step()`.
- **OBSERVABLE**: Expuesto en endpoints de `api.py` y visualizable en el frontend.
- **VALIDATED**: Con cobertura de tests unitarios y experimentos reproducibles.
- **PARTIAL**: Operando pero con simplificaciones, atajos estáticos o dependencias externas no resueltas.
- **DORMANT**: Implementado en el repositorio pero no instanciado ni invocado durante el ciclo continuo de simulación.

| Componente / Subsistema | Archivo Fuente | Estado Actual | Diagnóstico y Brechas Detectadas |
|:---|:---|:---:|:---|
| **OrganizationalIntelligenceEngine** | `saltbor/social/organization/engine.py` | PARTIAL / DORMANT | Maneja propuestas y liderazgo, pero no se invoca en el tick del runner ni modela fisión/disolución. |
| **EmergentInstitutionEngine** | `saltbor/social/institutions/emergent.py` | PARTIAL / DORMANT | Formaliza desde comunidades, pero no tiene dinámica de costos operativos ni actualización en cada tick. |
| **SocialInstitution & Model** | `saltbor/institutions/model.py` | IMPLEMENTED / VALIDATED | Modelo rico con tesorería, cuotas y políticas, pero instanciado sólo estáticamente en tests. |
| **GovernanceEngine & VotingProtocol** | `saltbor/institutions/governance.py` | PARTIAL / VALIDATED | Soporta protocolos de votación y presupuesto, pero desconectado de asambleas dinámicas en el runner. |
| **CommunityAssembly** | `saltbor/social/institutions/assembly.py` | IMPLEMENTED / DORMANT | Duplica propuestas con `governance.py` y no se conecta al bucle de agentes. |
| **EnhancedSocialGroup** | `saltbor/social/institutions/group.py` | IMPLEMENTED / DORMANT | Estructura de roles estática sin reglas de evolución social ni persistencia en BD. |
| **CommunityFormationEngine** | `saltbor/social/community/engine.py` | INTEGRATED / PARTIAL | Corre al inicio del día (`tick_of_day == 0`), pero no modela gestión de recursos CPR ni fisión por conflicto. |
| **ADESCOEngine (Salvadoran)** | `saltbor/social/salvadoran/community.py` | INTEGRATED / OBSERVABLE | Ejecuta faenas y cuchubales vía orchestrator; requiere conectarse con recursos comunes e instituciones formales. |
| **CollectiveEconomyEngine** | `saltbor/social/economy/collective_economy.py` | PARTIAL / DORMANT | Soporta cooperativas y pupuserías familiares, pero no se sincroniza con el `LaborMarketEngine` ni el `CommercialEngine`. |
| **ConflictCooperationEngine** | `saltbor/social/conflict/engine.py` | INTEGRATED / PARTIAL | Gestiona disputas interindividuales; no maneja conflictos colectivos, huelgas, boicots ni rivalidad comunitaria. |
| **CulturalEvolutionEngine** | `saltbor/social/culture/evolution.py` | INTEGRATED / VALIDATED | Decae tradiciones no practicadas diariamente; falta vincularlo a normas institucionales formales e informales. |
| **DistributedEducationEngine** | `saltbor/institutions/education.py` | INTEGRATED / OBSERVABLE | Maneja contratos de aprendizaje y talleres; falta modelar pérdida de conocimientos si maestros emigran o mueren. |
| **JudicialTribunal & Code** | `saltbor/institutions/legal/court.py` | INTEGRATED / OBSERVABLE | Opera vía eventos en el orquestador; falta articularlo como instancia de apelación de normas comunitarias violadas. |
| **ReputationEngine** | `saltbor/social/reputation/reputation_system.py` | INTEGRATED / VALIDATED | Registra confianza y cumplimiento de acuerdos; base excelente para legitimidad institucional. |
| **SalvadoranTerritory & Geography** | `saltbor/datasets/salvadoran/territory_data.py` | IMPLEMENTED / VALIDATED | 14 departamentos, 44 municipios (D.L. 762), 262 distritos, cantones y caseríos; base cartográfica sólida. |
| **IntegratedWorldSimulationEngine** | `saltbor/simulation/integrated_world.py` | INTEGRATED / OBSERVABLE | Orquestador de Fase 1.8; punto de enlace ideal para orquestar la dinámica institucional y de recursos colectivos. |
| **Social Stratification Model** | *Inexistente como módulo unificado* | DORMANT / AUSENTE | Solo existen atributos dispersos (`money`, `rent_per_day`, `daily_wage`); sin cómputo de Gini ni movilidad. |
| **Common-Pool Resource Manager (CPR)**| *Inexistente como módulo unificado* | DORMANT / AUSENTE | Falta motor Ostrom para agua comunal, tierra ejidal, bosques y equipamiento compartido. |
| **SocialNormEvolutionEngine** | *Inexistente como módulo unificado* | DORMANT / AUSENTE | Normas dispersas como strings o reglas fijas; sin dinámica de emergencia, cumplimiento, sanción y desuetudo. |

---

## 3. PLAN DE CONTINUIDAD ARQUITECTÓNICA

Para cumplir con la premisa: **"No reconstruyas motores que ya funcionan. No crees sistemas paralelos para resolver problemas que ya tienen una solución funcional"**:

1. **Consolidar `EmergentOrganizationEngine`**:
   - Construir sobre [saltbor/social/organization/engine.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/organization/engine.py) y [saltbor/social/community/engine.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/community/engine.py).
   - Reutilizar `LeadershipProfile` y extender el ciclo vital: condiciones de emergencia, cambio de objetivos, fisión por facciones, absorción/fusión y disolución.

2. **Consolidar `InstitutionalEvolutionEngine`**:
   - Unificar [saltbor/social/institutions/emergent.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/institutions/emergent.py) y [saltbor/institutions/model.py](file:///C:/GIT%20HUB/sv%20people/saltbor/institutions/model.py).
   - Dotar a cada institución de: identidad histórica, ubicación territorial (distrito/cantón), capacidad operativa finita, presupuesto contable cerrado, personal activo, legitimidad dinámica e historial inmutable.

3. **Consolidar `GovernanceEngine` y Toma de Decisiones Colectivas**:
   - Integrar [saltbor/institutions/governance.py](file:///C:/GIT%20HUB/sv%20people/saltbor/institutions/governance.py) y [saltbor/social/institutions/assembly.py](file:///C:/GIT%20HUB/sv%20people/saltbor/social/institutions/assembly.py) en un único motor de deliberación colectiva.
   - Modelar: asimetrías de poder (influencia ponderada por redes y prestigio), abstención, disenso persistente, negociación de enmiendas y consecuencias directas en la economía o normas.

4. **Crear `SocialNormEvolutionEngine`**:
   - Ubicado en `saltbor/social/norms/norm_evolution.py`.
   - Modela normas explícitas e implícitas (turnos de agua, fiado comercial, respeto a asambleas, faenas comunitarias).
   - Dinámica de observancia, sanciones graduadas (reputación $\to$ multa $\to$ exclusión) y decaimiento por desuetudo.

5. **Crear `CollectiveResourceManager` (Ostrom CPR)**:
   - Ubicado en `saltbor/social/resources/cpr_manager.py`.
   - Modela pozos comunales, acequias de riego, tierras comunales, herramientas y reservas de grano.
   - Rastreo contable estricto: balance de masa/recurso, cuotas de extracción, registros de faenas de mantenimiento, sobreexplotación y colapso o sostenibilidad.

6. **Crear `SocialStratificationEngine`**:
   - Ubicado en `saltbor/social/stratification/mobility_engine.py`.
   - Evaluación multidimensional de clase social: ingresos, patrimonio, vivienda, educación, capital social (redes), reputación, influencia cívica.
   - Cálculo automático de Gini, Palma, y matrices de movilidad intergeneracional y longitudinal.

7. **Extender Conflictos a Nivel Intercolectivo**:
   - Ubicado en `saltbor/social/conflict/intergroup_engine.py`.
   - Conectar con `ConflictCooperationEngine` para resolver huelgas, disputas de linderos, conflictos de distribución hídrica y negociaciones inter-comunitarias.

---

## 4. IMPACTO EN PERSISTENCIA Y RETROCOMPATIBILIDAD

- Se mantiene el soporte para la versión 4 del esquema SQLite de SALTBOR.
- Se crean tablas adicionales o adaptadores sin alterar las tablas `humans`, `memories_*`, `relationships`, `events_log`, `geo_entities` ni `simulation_state`.
- Nuevas tablas de soporte opcional: `emergent_organizations`, `institutional_history`, `cpr_resources`, `social_norms`, `stratification_snapshots`.
- Garantía de funcionamiento 100% offline, determinismo estricto mediante generador RNG derivado y cero dependencias pesadas nuevas.
