# SALTBOR — FASE 1.8: PLAN DE IMPLEMENTACIÓN E INTEGRACIÓN
## Simulación Humana y Territorial Integrada: Interacción Real, Arquitectura Unificada y Vida Cotidiana Emergente

**Fecha:** 13 de noviembre de 2026  
**Responsable:** Arquitecto Principal e Ingeniero de Simulación de SALTBOR  
**Estado:** Aprobado para ejecución tras auditoría arquitectónica

---

## 1. PRINCIPIOS Y DIRECTRICES ESTRATÉGICAS

1. **Integración Real sobre Creación Artificial:**
   No se inventarán subsistemas redundantes. Se conectarán causalmente los motores ya existentes (`SyntheticHuman`, `PsychologicalEngine`, `HealthEngine`, `CommercialEngine`, `LaborMarketEngine`, `HousingEngine`, `OSMRoadNetwork`, `CausalEventGraph`, etc.).

2. **Causalidad Circular y Consecuencias Propagadas:**
   Toda acción individual o evento territorial debe poder propagarse de forma bidireccional. Un fenómeno climático debe tener consecuencias en el transporte, el trabajo, el presupuesto familiar, la psicología y la memoria histórica comunitaria.

3. **Territorio Físico Utilizable:**
   Se elimina la teletransportación. Los humanos se desplazan a través de la red vial OSM real de El Salvador con tiempos de viaje calculados según el medio de transporte, clima, inclinación y obstáculos físicos (derrumbes o inundaciones).

4. **Lugares con Jerarquía de Capacidades Verificables:**
   Cada ubicación (tienda, pupusería, taller, clínica, vivienda) tiene capacidades explícitas: horarios de atención, aforo máximo, inventario de productos/insumos, personal laboral requerido y consecuencias socioeconómicas.

5. **Conservación Contable Estricta:**
   No se crea ni destruye dinero de forma arbitraria. Cada transacción económica responde a un intercambio legítimo con emisor, receptor, causa y registro contable balanceado.

6. **Experimentos con Escenarios Adversos:**
   Los experimentos no estarán prediseñados para triunfar siempre. Incluirán desempleo involuntario, colapso de ingresos, escasez de alimentos, rechazo amoroso, saturación de clínicas y aislamiento social.

---

## 2. ETAPAS DE IMPLEMENTACIÓN

### Etapa 1: Consolidación de la Arquitectura Geográfica y de Transporte
- **Módulo:** `saltbor/world/transportation/engine.py` y ampliación de `saltbor/world/geographic/osm_router.py`.
- **Acción:**
  - Crear `TransportationEngine` que gestione el viaje continuo de los agentes tick a tick.
  - Conectar `OSMRoadNetwork` al ciclo de vida de los desplazamientos.
  - Añadir soporte para bloqueos de vías viales por inundaciones o derrumbes.
  - Implementar búsqueda de rutas alternativas o cancelación/retraso del desplazamiento si no hay paso.

### Etapa 2: Jerarquía de Capacidades de Lugares y Entorno Físico
- **Módulo:** `saltbor/world/interaction/world_human_engine.py` y `saltbor/world/locations/capabilities.py`.
- **Acción:**
  - Extender las ubicaciones para incluir: horarios de apertura, capacidad de ocupación, personal presente, servicios ofrecidos e inventario de suministros.
  - Modelar clínicas con capacidad finita de atención y centros comerciales con comercios internos.
  - Viviendas con habitaciones, capacidad familiar y condiciones de habitabilidad.

### Etapa 3: Motor de Vida Cotidiana y Biorritmos Autónomos
- **Módulo:** `saltbor/lifecycle/daily_life/engine.py` o integración en `saltbor/cognition/decision/`.
- **Acción:**
  - Organizar las rutinas cotidianas según necesidades biológicas, compromisos laborales, responsabilidades familiares, clima y recursos económicos.
  - Permitir heterogeneidad: descanso, compras, aseo, improvisación, ocio, no hacer nada productivo, retrasos involuntarios.
  - Eliminar el uso del módulo estándar `random` en la toma de decisiones para garantizar reproducibilidad exacta por semilla.

### Etapa 4: Economía Cotidiana, Comercio Integrado y Contabilidad
- **Módulo:** `saltbor/economy/commerce/` y `saltbor/economy/household/ledger.py`.
- **Acción:**
  - Conectar visitas de vitrineo, comparación de precios e inventario en tiempo real.
  - Ajuste de precios por oferta y demanda local (escasez por vía bloqueada eleva precios de granos básicos).
  - Conservación contable integral entre hogares, comercios, empresas y tesorería comunal.

### Etapa 5: Causalidad Ambiental, Salud y Accidentes
- **Módulo:** `saltbor/world/interaction/environmental_hazards.py`, `saltbor/health/` y `saltbor/accidents/`.
- **Acción:**
  - Lluvias torrenciales provocan anegamiento de calles y riesgo de accidentes viales.
  - Accidentes de tránsito interrumpen el viaje y generan lesiones físicas que requieren atención clínica.
  - Saturación de clínicas retrasa la recuperación y eleva el estrés psicológico del paciente y sus cuidadores.

### Etapa 6: Redes Sociales, Familia, Conflicto y Apoyo Comunitario
- **Módulo:** `saltbor/social/`, `saltbor/psychology/support.py` y `saltbor/social/salvadoran/community.py`.
- **Acción:**
  - Conflictos interpersonales por deudas o incumplimientos que escalan a mediación vecinal o ruptura de relaciones.
  - Reacción comunitaria solidaria ante desastres locales (faena comunal de despeje de vías convocada por ADESCO).

### Etapa 7: Sistema Unificado de Eventos y Trazabilidad Histórica
- **Módulo:** `saltbor/events/causal_graph.py` y `saltbor/knowledge/salvadoran/history.py`.
- **Acción:**
  - Enlazar cada evento derivado con su evento causal originario.
  - Transmisión de acontecimientos comunitarios mayores a la memoria histórica colectiva de la población.

### Etapa 8: Motor Unificado `IntegratedWorldSimulationEngine` y `SimulationRunner`
- **Módulo:** `saltbor/simulation/integrated_world.py` y actualización de `saltbor/simulation/runner.py`.
- **Acción:**
  - Orquestar todos los motores en una secuencia causal libre de dependencias circulares y sin duplicación de estado.

### Etapa 9: Interfaz Visual y API REST
- **Módulo:** `saltbor/visualization/api.py`, `saltbor/visualization/web/app.js` y `index.html`.
- **Acción:**
  - Endpoints para inspección detallada de lugares (`/api/world/places/*`), rutas activas (`/api/world/transit/*`), grafo causal completo (`/api/events/causality/*`).
  - Actualización de frontend: visualización de viajeros en movimiento sobre la red vial, inspector de establecimientos y visor de árbol causal.
  - Corrección de límites de viewport en `/api/geography/geojson`.

### Etapa 10: Suite Experimental EXP_18_A a EXP_18_T y Benchmarks Sostenidos
- **Módulo:** `saltbor/simulation/experiments/phase18_experiments.py` y `tests/test_experiments/test_phase18_experiments.py`.
- **Acción:**
  - Ejecutar y validar los 20 experimentos exigidos por la especificación de la Fase 1.8.
  - Medir rendimiento a 20, 100, 500, 1.000 y 10.000 agentes.
  - Generar todos los informes de entrega requeridos.
