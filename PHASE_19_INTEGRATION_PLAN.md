# SALTBOR — FASE 1.9: PLAN DE INTEGRACIÓN Y DESARROLLO ARQUITECTÓNICO
## Hoja de Ruta para la Implementación de Dinámicas Sociales Emergentes y Evolución Institucional

**Fecha:** 13 de noviembre de 2026  
**Línea base:** SALTBOR Fase 1.8  
**Autor:** Arquitecto Principal de SALTBOR  

---

## 1. PRINCIPIOS DE DISEÑO E INTEGRACIÓN

1. **Reutilización y Consolidación sobre Reinvención:**
   - Aprovechar las estructuras probadas de [OrganizationalIntelligenceEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/social/organization/engine.py), [EmergentInstitutionEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/social/institutions/emergent.py), [GovernanceEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/institutions/governance.py), [CommunityFormationEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/social/community/engine.py), [CollectiveEconomyEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/social/economy/collective_economy.py) y [ADESCOEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/social/salvadoran/community.py).
   - Eliminar duplicidades de modelos de propuestas y asambleas mediante una interfaz de gobernanza unificada.

2. **Causalidad Circular y Doble Vía (Bottom-Up & Top-Down):**
   - Las necesidades individuales y la escasez ambiental impulsan la autoorganización comunitaria (*bottom-up*).
   - Las normas e instituciones formalizadas imponen restricciones presupuestarias, turnos de uso de recursos y sanciones a los individuos (*top-down*).

3. **Sin Dinero de la Nada ni Resultados Moralmente Sesgados:**
   - Toda tesorería institucional, fondo común o cooperativa se alimenta exclusivamente de cuotas de miembros, donaciones o ingresos de ventas reales.
   - Las asambleas pueden estancarse, polarizarse o aprobar decisiones ineficientes; la democracia no garantiza la prosperidad ni la equidad por defecto.

4. **Trazabilidad Causal e Histórica Estricta:**
   - Cada evento social de relevancia (fundación de cooperativa, cisma interno, huelga laboral, colapso de pozo comunal, enmienda estatutaria) se enlaza al `CausalEventGraph` y se conserva en el historial inmutable de la institución.

---

## 2. ETAPAS DE IMPLEMENTACIÓN

### Etapa 1: Motores Fundacionales de Dinámica Social Colectiva
- **1.1. `EmergentOrganizationEngine` (`saltbor/social/organization/emergent_engine.py`):**
  - Fusión y extensión de dinámicas organizacionales: evaluación de viabilidad de formación según necesidad y confianza, adaptación de estatutos, cisma/fisión ante faccionalismo, fusiones y disolución.
- **1.2. `InstitutionalEvolutionEngine` (`saltbor/social/institutions/institutional_evolution.py`):**
  - Modelo institucional holístico: 11 dominios institucionales (salud, educación, justicia, comercio, CPR, etc.), capacidad operativa cuantitativa, presupuesto auditado, personal designado, índice de legitimidad dinámico e historial evolutivo.
- **1.3. `CollectiveGovernanceEngine` (`saltbor/social/governance/collective_decision.py`):**
  - Asambleas deliberativas, protocolos de votación (mayoría simple, calificada, consenso, junta directiva), ponderación de influencia cívica, asimetrías de información, disenso persistente y enmiendas.
- **1.4. `SocialNormEvolutionEngine` (`saltbor/social/norms/norm_evolution.py`):**
  - Normas formales e informales, tasa de cumplimiento comunal, sanciones graduadas (reputación, multa, suspensión, ostracismo) y desuetudo.
- **1.5. `CollectiveResourceManager` (`saltbor/social/resources/cpr_manager.py`):**
  - Gestión de recursos comunes según Elinor Ostrom: balance hídrico, parcelas ejidales, leña forestal, infraestructura y fondos de emergencia; métricas de sobreexplotación (Tragedia de los Comunes) y mantenimiento.
- **1.6. `SocialStratificationEngine` (`saltbor/social/stratification/mobility_engine.py`):**
  - Estratificación multidimensional (7 vectores socioeconómicos), cálculo de Gini, Palma, quintiles y matrices de transición de movilidad social longitudinal.
- **1.7. `IntergroupConflictEngine` (`saltbor/social/conflict/intergroup_engine.py`):**
  - Conflictos intercolectivos (tierras, agua, comercio, huelgas laborales), escalada, mediación neutral, pactos y rupturas.

### Etapa 2: Integración en el Ciclo Principal de Simulación
- Conectar los nuevos subsistemas en [SimulationRunner](file:///C:/GIT%20HUB/sv%20people/saltbor/simulation/runner.py) y [IntegratedWorldSimulationEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/simulation/integrated_world.py).
- Modificar [saltbor/population/human.py](file:///C:/GIT%20HUB/sv%20people/saltbor/population/human.py) para que los agentes evalúen pertenencia a organizaciones, contribuyan a recursos CPR, asistan a asambleas y cumplan o violen normas según su personalidad e incentivos.
- Sincronizar el subsistema comercial y laboral ([CommercialEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/economy/commerce/commercial_engine.py) y [LaborMarketEngine](file:///C:/GIT%20HUB/sv%20people/saltbor/economy/labor/market.py)) con las organizaciones de productores y empresas familiares.

### Etapa 3: Persistencia y Compatibilidad
- Incorporar tablas o adaptadores JSON en [saltbor/persistence/schema.py](file:///C:/GIT%20HUB/sv%20people/saltbor/persistence/schema.py) para organizaciones emergentes, instituciones evolutivas, recursos CPR y estratificación social sin quebrar el esquema v4 ni invalidar checkpoints anteriores.

### Etapa 4: Observabilidad y Endpoints de API
- En [saltbor/visualization/api.py](file:///C:/GIT%20HUB/sv%20people/saltbor/visualization/api.py), publicar rutas REST:
  - `GET /api/social/organizations`: Directorio de organizaciones, fundadores, miembros y recursos.
  - `GET /api/social/organizations/{org_id}`: Perfil completo, facciones internas, historial y estado operativo.
  - `GET /api/social/institutions`: Lista de instituciones, capacidad operativa, legitimidad y presupuestos.
  - `GET /api/social/governance/proposals`: Asambleas activas, propuestas en debate, votaciones y disenso.
  - `GET /api/social/resources/cpr`: Estado de recursos comunes (agua, tierra, herramientas, fondos) y balances de extracción/faena.
  - `GET /api/social/stratification/overview`: Coeficiente de Gini, ratio de Palma, distribución por quintiles y movilidad social.
  - `GET /api/social/norms`: Normas comunitarias vigentes, grado de cumplimiento y sanciones aplicadas.
  - `GET /api/social/conflicts/intergroup`: Disputas interorganizacionales activas, mediaciones y acuerdos.

### Etapa 5: Interfaz de Usuario y Vistas Especializadas
- Ampliar la vista social y de civilización en [index.html](file:///C:/GIT%20HUB/sv%20people/saltbor/visualization/web/index.html) y [app.js](file:///C:/GIT%20HUB/sv%20people/saltbor/visualization/web/app.js) para renderizar tarjetas interactivas de organizaciones, medidores de legitimidad institucional, gráficas de distribución de riqueza y trazabilidad de recursos comunes.

### Etapa 6: Suite de 24 Experimentos Científicos Reproducibles (EXP_19_A a EXP_19_X)
- Implementar en `saltbor/simulation/experiments/phase19_experiments.py` los 24 experimentos estipulados en la especificación, con hipótesis verificables, mediciones cuantitativas, semillas múltiples y controles.
- Crear tests automatizados en `tests/test_experiments/test_phase19_experiments.py` asegurando 100% de ejecución satisfactoria.

### Etapa 7: Benchmarks y Documentación de Cierre
- Ejecutar pruebas sostenidas de rendimiento y escalabilidad (20, 100, 1.000 y 10.000 agentes).
- Generar los informes técnicos obligatorios de cierre.
