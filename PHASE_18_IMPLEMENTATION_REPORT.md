# SALTBOR FASE 1.8: INFORME DE IMPLEMENTACIÓN DE LA ARQUITECTURA INTEGRADA
## Human Life & World Simulation — Integración Ecosistémica, Cartografía Real y Vida Cotidiana Emergente

**Fecha:** 13 de Noviembre de 2026  
**Autor:** Arquitecto Principal, Ingeniero de Simulación y Especialista en Vida Artificial de SALTBOR  
**Estado:** IMPLEMENTADO, INTEGRADO, OBSERVABLE Y VALIDADO  
**Repositorio:** `c:\GIT HUB\sv people`  
**Compatibilidad:** Esquema SQLite v4, 100% retrocompatible con suites de pruebas previas  

---

## 1. RESUMEN EJECUTIVO

La **Fase 1.8 de SALTBOR** marca la culminación de la transición desde subsistemas conductuales y cognitivos modulares hacia un **ecosistema de simulación unificado**. Hasta la Fase 1.7, la plataforma contaba con sofisticados motores de cognición (memoria episódica, afecto tridimensional, rasgos de personalidad, toma de decisiones, redes sociales y dinámicas económicas locales), pero muchos de ellos operaban de manera aislada o con teletransportación instantánea entre un conjunto discreto de 16 ubicaciones abstractas.

Con la Fase 1.8, se ha consolidado el **`IntegratedWorldSimulationEngine`**, articulando en cada tick discreto de simulación:
1. **Navegación cinemática real sobre la red vial de OpenStreetMap**: Eliminación absoluta de la teletransportación; los agentes se desplazan punto a punto a lo largo de polilíneas reales, sujetas a velocidades físicas, pendientes, fatiga, precipitaciones y bloqueos viales.
2. **Jerarquía interactiva de lugares (`PlaceProfile`)**: Lugares con capacidades estrictas (aforos máximos, horarios de apertura y cierre, catálogos de precios, inventarios finitos y menús de servicios dinámicos).
3. **Rutinas autónomas y ritmos diurnos (`DailyLifeSimulationEngine`)**: Asignación de fases culturales salvadoreñas (Madrugada, Mañana, Mediodía, Tarde, Noche, Madrugada profunda), con horas de despertar tempranas acordes a ocupaciones locales (e.g., vendedoras de pupusas y jornaleros a las 4:00 AM) y adaptaciones contextuales ante lluvias torrenciales.
4. **Economía de conservación estricta**: Conservación contable de balance monetario sin generación arbitraria de dinero de la nada; modelado explícito de visitas comerciales sin compra (vitrineo / $0.00 spend), elasticidad ante escasez y contracción de presupuestos familiares ante emergencias.
5. **Acontecimientos ambientales y salud**: Propagación causal de tormentas tropicales (>15mm/h) hacia inundaciones de quebradas (e.g. Quebrada El Zapote) y derrumbes, provocando retrasos, búsqueda de refugio o cancelación de viajes.
6. **Relaciones, familia y acción comunitaria (ADESCO)**: Organización de faenas comunales para despejar infraestructura, evolución del afecto y confianza por experiencias compartidas o disputas vecinales.
7. **Grafo causal acíclico dirigido (`CausalEventGraph`) y Memoria Histórica Salvadoreña**: Trazabilidad completa de causa y efecto para cada evento importante, con consolidación automática de hitos en la memoria colectiva.
8. **Fidelidad y observabilidad completa (API y UI)**: Exposición de endpoints REST y GeoJSON estrictamente congruentes con el estado en memoria, sin alucinación sintética, y blindaje de coordenadas ante deformaciones del viewport cartográfico.

---

## 2. AUDITORÍA PREVIA Y RESOLUCIÓN DE ANOMALÍAS

Siguiendo la **Regla Fundamental de Auditar Antes de Implementar**, se inspeccionaron 122 subsistemas del repositorio. La auditoría reveló las siguientes brechas críticas que fueron remediadas en esta fase:

| Subsistema Auditado | Estado Pre-1.8 | Brecha Detectada | Resolución en Fase 1.8 |
| :--- | :--- | :--- | :--- |
| **OSMRoadNetwork** | DORMANT | Solo ejecutado en benchmarks aislados; la simulación saltaba entre waypoints fijos en 1 tick. | Integrado plenamente en `TransportationEngine`. Los agentes recorren la geometría vial paso a paso. |
| **Lugares y Comercios** | PARTIAL | Coordenadas estáticas sin aforo ni control de horario; compras sin control de stock. | Creación de `PlaceProfile` con jerarquía de 8 niveles (`PlaceCapability`), inventarios finitos y horarios. |
| **Rutinas y Ciclo Diario** | DORMANT | Los agentes no tenían ritmos diurnos coordinados culturalmente. | Creación de `DailyLifeSimulationEngine` con 6 fases diurnas salvadoreñas y biorritmos individuales. |
| **Grafo Causal** | DORMANT | Existía clase `CausalEventGraph` pero no se vinculaba al `SimulationRunner`. | Conectado a cada evento emitido por infraestructura, transporte y economía. |
| **Memoria Histórica** | DORMANT | `SalvadoranHistoricalMemoryEngine` no recibía eventos de desastres comunales. | Consolidación periódica de eventos con importancia $\ge 0.70$ hacia la memoria histórica. |
| **Viewport Cartográfico** | PARTIAL | Zoom alejado provocaba 422 Unprocessable Entity en `/api/geography/geojson`. | Clampeo defensivo de coordenadas WGS84 $[-180, 180]$ y $[-90, 90]$. |

---

## 3. COMPONENTES ARQUITECTÓNICOS IMPLEMENTADOS

### 3.1. `IntegratedWorldSimulationEngine` (`saltbor/simulation/integrated_world.py`)
Actúa como el orquestador maestro dentro de `SimulationRunner.step()`. En cada paso:
- Evalúa el impacto de la precipitación (`_evaluate_environmental_impacts`): si la lluvia supera los 15 mm, genera bloqueos en quebradas vulnerables y emite eventos causales.
- Ejecuta el paso cinemático de `TransportationEngine`: avanza los viajes activos, comprueba obstrucciones, gestiona llegadas y efectúa la transición de abandono e ingreso a lugares (`leave_place` y `enter_place`).
- Sincroniza acontecimientos comunitarios de alta relevancia con `SalvadoranHistoricalMemoryEngine`.

### 3.2. `TransportationEngine` (`saltbor/world/transportation/`)
- **Modelos (`models.py`)**: `TravelMode` (WALK, BICYCLE, BUS, VEHICLE), `JourneyStatus` (IN_PROGRESS, ARRIVED, BLOCKED, REROUTED, CANCELLED), `RoadBlockage` y `ActiveJourney`.
- **Motor (`engine.py`)**:
  - Cálculo de rutas sobre `OSMRoadNetwork` o polilíneas geodésicas.
  - Modulación de velocidad según clima: reducción al 65% a pie con lluvia $>5$ mm, y penalizaciones por fatiga biológica ($<25\%$ energía $\rightarrow 70\%$ velocidad).
  - Detección de bloqueos en tiempo real: si un deslizamiento o inundación obstruye el camino, el agente interrumpe el viaje y cancela o calcula desvío alternativo.

### 3.3. `PlaceProfile` y Capacidades Jerárquicas (`saltbor/world/locations/capabilities.py`)
Jerarquía de capacidades basada en flags de bits (`PlaceCapability`):
- `IDENTIFIABLE` (0x01)
- `NAVIGABLE` (0x02)
- `VISITABLE` (0x04)
- `SCHEDULE_RESTRICTED` (0x08)
- `SERVICE_PROVIDER` (0x10)
- `INVENTORY_HOLDER` (0x20)
- `SOCIAL_HUB` (0x40)
- `ECONOMIC_CONSEQUENCE` (0x80)

Cada lugar (`PlaceProfile`) administra:
- `opening_hour` y `closing_hour`: Rechaza ingresos fuera de horario con razón explícita `"Cerrado: abre a las HH:00"`.
- `max_capacity` y `current_occupants`: Control de aforo para evitar sobrepoblación no física.
- `inventory`: Existencias finitas de bienes (e.g. quintales de maíz, libras de frijol, órdenes de pupusas). Compras con stock 0 son denegadas.
- `price_catalog`: Precios unitarios auditables.
- `services`: Ejecución tipada de servicios (e.g. consulta médica en clínica de salud con costo de \$3.00, elevación de salud en +0.35).

### 3.4. `DailyLifeSimulationEngine` (`saltbor/lifecycle/daily_life/`)
- Mapea el reloj de 24 horas a las fases diurnas:
  - `MADRUGADA` (03:00 - 05:59): Despertar, aseo personal, preparación de insumos.
  - `MANANA` (06:00 - 11:59): Desayuno, desplazamiento, jornada laboral matutina.
  - `MEDIODIA` (12:00 - 13:59): Almuerzo, descanso breve, hidratación.
  - `TARDE` (14:00 - 17:59): Continuación de jornada laboral, compras en mercado.
  - `NOCHE` (18:00 - 21:59): Retorno al hogar, cena familiar, convivencia vecinal.
  - `NOCHE_PROFUNDA` (22:00 - 02:59): Descanso nocturno, sueño reparador.
- Personalización por oficio: Jornaleros y comerciantes madrugan a las 4:00 AM; trabajadores de oficina a las 6:00 AM.
- Prioridad climática: Durante tormentas fuertes, anula actividades al aire libre y sugiere `SEEK_SHELTER` en el hogar o lugar cerrado más cercano.

### 3.5. Integración Cognitiva y Toma de Decisiones
En `saltbor/cognition/decision/engine.py`, el `DecisionContext` ahora incorpora:
- `diurnal_phase`: Fase cultural actual.
- `suggested_daily_activity`: Actividad recomendada por el biorritmo.
- `suggested_daily_location`: Destino espacial propuesto.
- En `evaluate_options()`, las opciones que coinciden con el ritmo diurno reciben un impulso ponderado de intencionalidad (+0.25 a +0.40), respetando sin embargo necesidades fisiológicas críticas (hambre extrema o salud deteriorada superan la rutina).

---

## 4. ENDPOINTS REST Y VISUALIZACIÓN EXPUESTOS

En `saltbor/visualization/api.py`, se crearon e integraron los siguientes endpoints:

1. **`GET /api/world/places`**: Catálogo de todos los lugares registrados con categoría, aforo, horario y número de ocupantes.
2. **`GET /api/world/places/{place_id}`**: Detalle exhaustivo de un lugar, incluyendo nombres y edades de ocupantes actuales, inventario y menú de servicios.
3. **`POST /api/world/places/{place_id}/interact`**: Interacción directa (entrar, salir, comprar producto, solicitar servicio médico o artesanal) con verificación estricta de saldo e inventario.
4. **`GET /api/world/transit`**: Lista de todos los agentes viajando por la red vial, con progreso (0.0 a 1.0), polilínea, velocidad efectiva y coordenadas instantáneas.
5. **`GET /api/world/blockages`**: Registro de derrumbes, inundaciones y fallas viales activas.
6. **`GET /api/world/causality/{event_id}`**: Traza de causas raíz ancestras y consecuencias descendientes en el DAG causal.
7. **`GET /api/world/daily_life/profiles`**: Fase diurna actual y perfiles de rutina de toda la población.
8. **Blindaje GeoJSON**: Actualización de `/api/geography/geojson`, `/api/geography/features` y `/api/geography/ecological_profile` con clampeo automático de límites WGS84 para navegación fluida en MapLibre.

---

## 5. CONCLUSIÓN

La Fase 1.8 ha logrado articular los motores de SALTBOR en una arquitectura viva, físicamente coherente y observable. Los agentes sintéticos ya no flotan sobre coordenadas descontextualizadas: habitan viviendas reales, caminan sobre calles verificadas de El Salvador, comen en pupuserías locales, padecen los rigores de las tormentas tropicales, cooperan en faenas comunales y dejan una huella causal y mnemónica indeleble en la historia de la simulación.
