# SALTBOR — FASE 1.0: EVOLUCIÓN CIVILIZATORIA, SOCIEDAD MULTIGENERACIONAL Y EMERGENCIA HISTÓRICA

## 1. Resumen Ejecutivo de la Fase 1.0
La Fase 1.0 de **SALTBOR** trasciende la simulación de agentes y grupos comunitarios aislados para consolidar un simulador de **civilizaciones históricas emergentes**, autónomas y multigeneracionales. Las civilizaciones en SALTBOR no están preprogramadas ni siguen una teleología obligatoria de progreso: nacen, se consolidan, se expanden territorialmente, sufren crisis o desastres, se transforman, se fragmentan en facciones independientes o desaparecen como consecuencia causal directa de las acciones individuales, redes de parentesco, instituciones y geografías de sus habitantes.

---

## 2. Auditoría e Integración de Fases Anteriores
- **Inspección Integral**: Se auditaron todos los subsistemas preexistentes: Biological Lifecycle, Genetics, Genealogy, Cognition & Reasoning (Fase 0.7), Territorial Geography (Fase 0.8 con 262 municipios salvadoreños), Social Complexity (Fase 0.9) y Simulation Laboratory.
- **Retrocompatibilidad**: Todas las interfaces de las fases previas se preservaron íntegramente. La suite completa de 261 pruebas preexistentes continúa aprobando al 100%, sumando ahora un total de **295 pruebas automatizadas aprobadas**.

---

## 3. Arquitectura de Motores Desarrollados (Paquete `saltbor.civilization`)

### 3.1. Master Civilization Evolution Engine (`saltbor.civilization.engine`)
- **Estado multidimensional**: Coordina identidad colectiva, territorio, demografía acumulada, asentamientos constituyentes, instituciones formales, trayectoria económica, capital acumulado, cohesión social y fase histórica (`EMERGING`, `GROWING`, `CONSOLIDATED`, `EXPANDING`, `TRANSFORMING`, `FRAGMENTED`, `DECLINING`, `RECOVERED`, `EXTINCT`).
- **Procesos causales**: Transiciones de estado condicionadas por demografía activa, cohesión y desastres.
- **Fragmentación e Integración**: Capacidad de escisión autónoma de asentamientos separatistas en nuevas entidades civilizatorias (`fragment_civilization`) con relaciones diplomáticas inmediatas.

### 3.2. Historical Memory Engine (`saltbor.civilization.history`)
Diferenciación epistemológica estricta en 6 capas:
1. **Ground Truth Histórico**: Acontecimientos objetivos exactos ocurridos en la simulación con coordenadas, fecha, actores, causas, consecuencias y nivel de incertidumbre.
2. **Registro Institucional**: Archivos formales, estatutos y actas municipales con grados medibles de completitud y fidelidad jurídica.
3. **Recuerdos Individuales**: Percepción filtrada por vivencia directa.
4. **Narrativas Culturales**: Transmisión oral o simbólica intergeneracional sujeta a deriva semántica (`drift_factor`) acumulativa con cada iteración.
5. **Interpretaciones Culturales**: Encuadres colectivos heroicos, trágicos, admonitorios o sagrados.
6. **Incertidumbre y Olvido**: Acontecimientos lejanos sin narrativas activas o significancia suficiente se desvanecen gradualmente de la memoria colectiva.

### 3.3. Multi-Generational Demographics Bridge (`saltbor.civilization.multigenerational`)
- Conecta el ciclo biológico y el árbol genealógico (`GenealogicalGraph`) con cohortes generacionales a largo plazo (Gen 0 a Gen N).
- Traza linajes familiares extensos, profundidad generacional, transmisión de habilidades y reorganización sucesoria tras defunciones.
- Desacoplamiento estricto del determinismo genético: las trayectorias de los descendientes emergen de su contexto social y oportunidades, no de su ADN.

### 3.4. Settlement Evolution Engine (`saltbor.civilization.settlement`)
- Tipologías territoriales adaptativas: *Caseríos, Comunidades Rurales, Aldeas, Barrios, Colonias, Centros Urbanos, Ciudades, Núcleos Comerciales y Zonas Productivas*.
- Transiciones emergentes basadas en umbrales de población, capacidad habitacional, red de caminos, acceso al agua y desarrollo infraestructural.
- Absorción e integración metropolitana de asentamientos vecinos menores.

### 3.5. Migration & Population Dynamics Engine (`saltbor.civilization.migration`)
- Modelado multifactorial de propensión migratoria (empuje ambiental, costo de traslado, oportunidades en destino, redes de parentesco).
- Tipos de migración: rural-urbana, urbana-rural, interdepartamental, desplazamiento por desastre o conflicto, y migración de retorno.
- Flujos de remesas hacia asentamientos de origen y conservación/debilitamiento de lazos comunitarios.

### 3.6. Economic Civilization Evolution Engine (`saltbor.civilization.economy`)
- 14 sectores productivos contextualizados (agricultura, pesca, comercio informal, manufactura, construcción, transporte, turismo, educación, salud, empresas familiares, tecnología).
- Dinámica macroeconómica no lineal: producción dependiente de capital, trabajo, shocks climáticos/financieros, depreciación y reinversión.
- Transmisión sucesoria de negocios e historiales de patrimonio y endeudamiento familiar.

### 3.7. Technological and Knowledge Evolution Engine (`saltbor.civilization.technology`)
- 10 dominios de conocimiento (práctico, científico, técnico, agrícola, comercial, médico, arquitectónico, organizativo, ambiental, cultural).
- Restricciones materiales indispensables: ninguna tecnología se descubre sin insumos físicos o conocimientos previos requeridos.
- Difusión geográfica entre asentamientos, posibilidad de olvido técnico por aislamiento o despoblación, y posterior redescubrimiento archivístico.

### 3.8. Social Stratification and Mobility Engine (`saltbor.civilization.stratification`)
- Perfil multidimensional: patrimonio, ingresos, educación, capital social e influencia cívica.
- Estratos emergentes: *Vulnerable, Lower, Middle-Lower, Middle, Middle-Upper, Prosperous*.
- Cálculo formal del coeficiente de **Gini de riqueza** para medir la dispersión socioeconómica.

### 3.9. Civilization Resilience Engine (`saltbor.civilization.resilience`)
- Choques ambientales y antrópicos: sequías, inundaciones, deslaves, epidemias simuladas, bloqueos comerciales.
- Mecanismos de respuesta adaptativa: redistribución de recursos, migración de emergencia, adaptación tecnológica, reestructuración o abandono de asentamientos.

### 3.10. Multi-Society Interaction Engine (`saltbor.civilization.interaction`)
- Relaciones diplomáticas: alianza, asociación comercial, neutralidad, dependencia asimétrica, tensión y conflicto abierto.
- Dinámica bilateral de confianza comercial y volumen de intercambio, preparada para expandirse a nivel mesoamericano e internacional.

### 3.11. Historical Knowledge Graph (`saltbor.civilization.graph`)
- Entidades históricas tipadas (`PERSON`, `FAMILY`, `SETTLEMENT`, `HISTORICAL_EVENT`, `INNOVATION`, `CIVILIZATION`).
- Aristas temporales explícitas (`FOUNDED`, `INHERITED_FROM`, `TRANSMITTED_TO`, `MIGRATED_TO`, etc.) con providencia temporal e indexación de adyacencia directa.
- Consultas de causalidad histórica sin invención retrospectiva.

---

## 4. Validación Experimental: Suite EXP_10 (EXP_10_A a EXP_10_X)

Los 24 experimentos obligatorios de la Fase 1.0 fueron implementados e integrados en `SimulationLaboratory`:

| Experimento | Nombre | Estado | Métricas Clave Observadas |
|---|---|---|---|
| **EXP_10_A** | Continuidad multigeneracional | **PASÓ** | 4 cohortes sucesivas, profundidad de linaje = 4 |
| **EXP_10_B** | Evolución demográfica generacional | **PASÓ** | Reemplazo generacional: 17 vivos, 8 fallecidos |
| **EXP_10_C** | Evolución de asentamientos | **PASÓ** | Transición de Caserío a Aldea/Barrio por población e infraestructura |
| **EXP_10_D** | Migración entre territorios | **PASÓ** | Propensión > 0.5, Remesas acumuladas al origen = $120.0 |
| **EXP_10_E** | Estructuras familiares | **PASÓ** | Ramificación de linaje con 5+ miembros y 3 generaciones |
| **EXP_10_F** | Transmisión intergeneracional de conocimientos | **PASÓ** | Transferencia artesanal registrada en el Grafo de Conocimiento |
| **EXP_10_G** | Evolución de tradiciones culturales | **PASÓ** | Deriva semántica oral = 0.45 tras 5 transmisiones |
| **EXP_10_H** | Aparición y difusión de innovaciones | **PASÓ** | Riego solar descubierto y difundido a 3 asentamientos |
| **EXP_10_I** | Transformación económica | **PASÓ** | Acumulación de capital y sucesión generacional exitosa |
| **EXP_10_J** | Movilidad social intergeneracional | **PASÓ** | Movilidad ascendente de estrato vulnerable a medio-alto |
| **EXP_10_K** | Transformación institucional | **PASÓ** | Promulgación y archivo fidedigno de ordenanza municipal |
| **EXP_10_L** | Evolución de desigualdades | **PASÓ** | Coeficiente de Gini calculado empíricamente > 0.40 |
| **EXP_10_M** | Respuesta ante crisis ambientales | **PASÓ** | Adaptación técnica adoptada ante sequía extrema |
| **EXP_10_N** | Resiliencia económica | **PASÓ** | Rebote de capital productivo tras shock macroeconómico |
| **EXP_10_O** | Fragmentación de comunidades | **PASÓ** | Escisión de asentamiento separatista en nueva civilización |
| **EXP_10_P** | Formación de identidades colectivas | **PASÓ** | Rasgos culturales y narrativa comunitaria fundacional consolidados |
| **EXP_10_Q** | Relaciones entre sociedades | **PASÓ** | Comercio bilateral eleva la relación a socios estratégicos |
| **EXP_10_R** | Pérdida y recuperación de conocimientos | **PASÓ** | Técnica olvidada por aislamiento y recuperada por archivo |
| **EXP_10_S** | Transformación histórica profunda | **PASÓ** | Caserío costero evoluciona a Ciudad de 850 habitantes |
| **EXP_10_T** | Continuidad institucional generacional | **PASÓ** | Supervivencia de estatutos jurídicos tras fallecimiento de fundadores |
| **EXP_10_U** | Tecnología condicionada por recursos | **PASÓ** | Fracaso sin insumos materiales y éxito al obtenerlos |
| **EXP_10_V** | Comparación contrafáctica de escenarios | **PASÓ** | Sociedad resiliente absorbe crisis con pérdidas sustancialmente menores |
| **EXP_10_W** | Extinción o disolución de sociedad | **PASÓ** | Sociedad clasificada como extinta tras despoblación total |
| **EXP_10_X** | Evolución civilizatoria a largo plazo | **PASÓ** | Simulación de 25 años multidecenales culminada exitosamente |

---

## 5. Rendimiento y Escalabilidad Multidecenal
Ejecutado sobre la plataforma de referencia (Ryzen 7 8700G, DDR5, Python 3.14):
- **Horizontes temporales evaluados**: 1 año, 5 años, 10 años, 25 años, 50 años y 100 años virtuales.
- **Rendimiento**: Menos de **0.0003 segundos por año virtual simulado**, permitiendo simular siglos completos en fracciones de segundo mediante abstracción LOD macro-demográfica y procesamiento por lotes sin sobrecargar la memoria RAM.
- **Suite completa**: 295 pruebas automatizadas ejecutadas en **7.02 segundos**.

---

## 6. Estado de Clasificación de Entregables
- **Implementado y Validado Experimentalmente**: Civilizaciones emergentes, memoria histórica multinivel, transiciones de asentamientos, dinámicas migratorias y remesas, ciclos macroeconómicos intergeneracionales, difusión tecnológica condicionada por materiales, estratificación y Gini, resiliencia ante desastres, diplomacia inter-civilizatoria, grafo de conocimiento histórico y suite EXP_10_A a EXP_10_X.
- **Limitaciones Conocidas**: La interacción internacional entre civilizaciones está estructurada a nivel de tratados y flujos de comercio/conflicto, requiriendo en la siguiente fase mapas topográficos continuos para fronteras porosas compartidas.
- **Propuesta para la Siguiente Fase (Fase 1.1)**: Modelado de rutas de transporte transfronterizas terrestres y marítimas, y federaciones de municipios regionales.
