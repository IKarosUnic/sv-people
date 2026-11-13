# SALTBOR — PHASE 1.3-V SPECIFICATION
## INTERACTIVE VISUAL SIMULATION ENVIRONMENT, DIGITAL SOCIETY OBSERVABILITY & COGNITIVE EXPLORER

**Date:** November 10, 2026  
**Phase:** Phase 1.3-V  
**Status:** Implemented, Tested, Integrated (405/405 Tests PASSED)  
**Compatibility:** Python 3.14.5 (64-bit), SQLite WAL Mode, Pydantic v2, FastAPI/Uvicorn, HTML5 Canvas 2D  
**Reference Hardware:** AMD Ryzen 7 8700G, 32 GB DDR5-6000, AMD Radeon 780M, Windows 11  

---

## 1. OBJETIVO Y VISIÓN ARQUITECTÓNICA

La Fase 1.3-V transforma SALTBOR de un motor de simulación orientado prioritariamente a consola y archivos en una **plataforma visual interactiva de observabilidad científica**. 

El sistema permite a investigadores, sociólogos computacionales y modeladores cognitivos:
1. Observar la dinámica territorial de El Salvador en tiempo real con datos geográficos verificados.
2. Seguir a individuos sintéticos autónomos e inspeccionar sus estados biológicos, psicológicos y mnémicos.
3. Descomponer la arquitectura cerebral en sus 6 subsistemas funcionales y auditar la traza causal de cada decisión.
4. Visualizar la evolución del grafo de conocimiento, la deriva epistémica y la pérdida o mutación de saberes.
5. Inspeccionar la topología de la red social, las relaciones asimétricas multidimensionales y la formación de ADESCOs.
6. Monitorear las series temporales de demografía, desigualdad económica (Gini), resiliencia cultural y ciclos climáticos.
7. Controlar la ejecución de la simulación (Play, Pausa, Paso discreto, Escalas de velocidad 1×..1000×, Escenarios y Checkpoints).

---

## 2. ARQUITECTURA DE LA PLATAFORMA

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ARQUITECTURA VISUAL SALTBOR FASE 1.3-V                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                       SIMULATION CONTROL CENTER (Barra Superior)                       │
│  [Play/Pausa] [⏭ +1 Tick] [1×|10×|100×|1000×] [Tick: 142] [Día 2, 11:30] [Pop: 20]     │
│  [Escenario: Sequía/Comercio/Línea Base] [Guardar/Cargar] [Tema: Dark/Light] [SSE: Live]│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ NAVEGACIÓN Y 10 EXPLORADORES INTERACTIVOS:                                             │
│ 1. World Explorer:                                                                     │
│    - Renderizado Canvas 2D acelerado por GPU (AMD Radeon 780M @ 60 FPS)                │
│    - 14 Departamentos, 44 Municipios, 262 Distritos (WGS84 real, elevaciones)          │
│    - Red Vial Nacional (CA-1, CA-2, CA-4, puentes y caminos vecinales)                 │
│    - Directorio verificado de establecimientos (CONFIRMADO, PENDIENTE, DESACTUALIZADO) │
│    - Avatares dinámicos en movimiento con ocupación, actividad y modo seguimiento      │
│ 2. Individual Explorer:                                                                │
│    - Vitas biológicas (energía, hambre, salud, dinero)                                 │
│    - Perfil de personalidad de 8 rasgos (Big Five + riesgo, paciencia, persistencia)   │
│    - Estado afectivo (dial de ánimo -1..+1, regulación y cargas emocionales activas)   │
│    - Ciclo de metas autónomas con planes HTN/GOAP y progreso porcentual                │
│    - Memoria episódica indexada por valencia e importancia estelar                     │
│    - Perfil cognitivo dinámico de 14 capacidades con presupuesto de 8.40 puntos        │
│ 3. Cognitive Architecture Explorer:                                                    │
│    - 6 Subsistemas funcionales: Frontal, Hipocampal, Límbico, Temporal, Parietal,      │
│      Cerebeloso con responsabilidades, inputs, outputs y métricas operativas           │
│    - Pipeline Causal: OBSERVACIÓN → NECESIDADES → RECUPERACIÓN → RAZONAMIENTO →        │
│      PLANIFICACIÓN → DECISIÓN → ACCIÓN → RESULTADO con valores empíricos reales        │
│ 4. Knowledge Graph Explorer:                                                           │
│    - Grafo de fuerzas Canvas con 8 estados epistémicos (Verificado, Provisional,       │
│      Hipótesis, Creencia, Rumor, Contradictorio, Refutado, Extinto)                    │
│    - Búsqueda, filtros por dominio (gastronomía, artesanía, agroecología, ciencia)     │
│ 5. Social Network Explorer:                                                            │
│    - Relaciones multidimensionales (familia, amistad, confianza, comercio, conflicto)  │
│    - Grosor de arista según confianza y afinidad diádica; detección de ADESCOs         │
│ 6. Civilization Dashboard:                                                             │
│    - Gráficos vectoriales SVG responsivos de series temporales (Demografía, Gini,      │
│      Tradiciones vivas, Temperatura y precipitación)                                   │
│ 7. Economy & Resources:                                                                │
│    - Tableros de precios (maíz, frijol, café pacamara, artesanía, telares)             │
│    - Directorio de empresas y talleres; libros de crédito, deuda y fiado informal      │
│ 8. Historical Timeline:                                                                │
│    - Flujo cronológico de eventos con filtrado multi-criterio y salto a entidades      │
│ 9. Simulation Laboratory:                                                              │
│    - Banco de pruebas con ejecución interactiva en 1 clic de experimentos A-H y 04-13 │
│ 10. Reports & Validation:                                                              │
│    - Visor de informes científicos y auditorías forenses                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ CAPA DE COMUNICACIÓN Y PERSISTENCIA (BACKEND):                                         │
│ - SimulationController desacoplado en hilo de ejecución autónomo                       │
│ - API REST FastAPI para consultas de estado por demanda                                │
│ - Stream Server-Sent Events (SSE) a 20 Hz con reconexión automática tolerante a fallos │
│ - Motor SQLite WAL con transacciones atómicas y checkpoints programados                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. LOS 10 EXPLORADORES EN DETALLE

### 3.1 World Explorer (Explorador Territorial de El Salvador)
- **Marco de Coordenadas:** WGS84 en el rectángulo delimitador `[13.10° N, -90.15° W]` a `[14.48° N, -87.65° W]`.
- **Estructura Administrativa:**
  - 14 Departamentos clasificados en 4 Zonas (Occidental, Central, Paracentral, Oriental).
  - 44 Municipios consolidados (Ley de Reestructuración Municipal 2024).
  - 262 Distritos con coordenadas de cabecera y elevaciones métricas reales.
- **Topografía e Infraestructura:**
  - Red vial completa: Carretera Panamericana (CA-1), Carretera del Litoral (CA-2), Troncal del Norte (CA-4), puentes estratégicos (Puente Cuscatlán, Puente de Oro).
  - Accidentes físicos mayores: Volcanes (Santa Ana, Izalco, San Salvador, San Vicente, Chaparrastique) y Lagos (Coatepeque, Ilopango, Güija).
- **Directorio de Establecimientos:**
  - Puntos reales con estado de validación: `CONFIRMADO` (verde esmeralda), `PENDIENTE_VALIDACION` (amarillo ámbar), `DESACTUALIZADO` (naranja), `CERRADO` (rojo).
- **Entidades Dinámicas:**
  - Agentes sintéticos representados por círculos cromáticos según género, con halo de selección para el agente enfocado y etiqueta de ocupación/actividad.
  - Cámara de seguimiento continuo ("Modo Seguimiento") que centra suavemente el visor sobre el agente mientras transita entre asentamientos.
- **Level of Detail (LOD):**
  - `Zoom < 1.4×`: Fronteras departamentales, carreteras troncales, volcanes y lagos mayores.
  - `Zoom 1.4× - 2.8×`: Cabeceras distritales, red vial secundaria, establecimientos y asentamientos.
  - `Zoom > 2.8×`: Nombres completos de establecimientos, avatares individuales con indicadores de actividad y dirección.

---

### 3.2 Individual Explorer (Dossier del Agente Sintético)
- **Identidad:** UID único (UUIDv4), número de serie correlativo, nombre y apellido, género, edad, etapa de vida y nivel educativo.
- **Vitas Biológicas:**
  - Energía $[0.0, 1.0]$, Hambre $[0.0, 1.0]$, Salud $[0.0, 1.0]$ y Liquidez financiera en USD.
  - Actividad en curso y conteo regresivo de ticks restantes.
- **Personalidad (8 Rasgos):**
  - Apertura, Responsabilidad, Extraversión, Amabilidad, Neuroticismo, Tolerancia al Riesgo, Paciencia y Persistencia.
  - Visualización dual de nivel base, nivel actual y deriva adaptativa ($\Delta \text{drift}$).
- **Perfil Emocional:**
  - Dial de ánimo afectivo $[-1.0, +1.0]$, capacidad de autorregulación y cargas activas (Alegría, Miedo, Enojo, Tristeza, Curiosidad).
- **Metas Autónomas (HTN/GOAP):**
  - Categorías: biológica, financiera, social, destreza, seguridad.
  - Progreso porcentual y visualización del paso concreto del plan en ejecución.
- **Competencias Procedimentales:**
  - Habilidades adquiridas con nivel de dominio y número acumulado de prácticas.
- **Memoria Episódica:**
  - Registros recientes con marca de tiempo (Tick), resumen semántico, valencia afectiva e importancia valorada con estrellas.

---

### 3.3 Cognitive Architecture Explorer (Arquitectura Cerebral Funcional)
- **Principio Fundamental:** Se descartan gráficos de ondas biológicas ficticias o métricas neuronales inventadas; los 6 subsistemas son **analogías funcionales computacionales rigurosas**:
  1. **Frontal (Ejecutivo):** Planificación, inhibición de impulsos, arbitraje de metas, replanificación GOAP/HTN.
  2. **Hipocampal (Memoria):** Buffer de trabajo (7 ítems), memoria episódica indexada, degradación logarítmica de Ebbinghaus.
  3. **Límbico (Afectivo):** Estado de ánimo, modulación del riesgo ante miedo ($1.0 - 0.5 \cdot \text{miedo}$), incentivo exploratorio por curiosidad.
  4. **Temporal (Semántico):** Conceptos del mundo, grafo ontológico de saberes, evaluación de certeza epistémica.
  5. **Parietal (Espacial):** Coordenadas, distancias topológicas, costes de transporte y viabilidad de vados/puentes.
  6. **Cerebeloso (Procedimental):** Rutinas automatizadas, hábitos consolidados y curvas de práctica no lineales.
- **Traza Causal de Deliberación:**
  $$\text{OBSERVACIÓN} \rightarrow \text{NECESIDADES} \rightarrow \text{RECUPERACIÓN} \rightarrow \text{RAZONAMIENTO} \rightarrow \text{PLANIFICACIÓN} \rightarrow \text{DECISIÓN} \rightarrow \text{ACCIÓN} \rightarrow \text{RESULTADO}$$
  Cada paso expone los valores exactos computados en el último ciclo de actualización del agente.

---

### 3.4 Knowledge Graph Explorer (Red Epistémica y Proveniencia)
- **Nodos:** Conceptos, técnicas artesanales, recetas tradicionales, prácticas agroecológicas e hipótesis científicas.
- **8 Estados Epistémicos:**
  - `VERIFIED_KNOWLEDGE` (Verde esmeralda): Saberes probados empíricamente o de arraigo ancestral.
  - `PROVISIONAL_KNOWLEDGE` (Azul cielo): Conclusiones preliminares sujetas a replicación.
  - `HYPOTHESIS` (Violeta): Proposiciones formuladas autónomamente por agentes en proceso de experimentación.
  - `PERSONAL_BELIEF` (Ámbar): Creencias individuales basadas en experiencias acotadas.
  - `RUMOR` (Naranja): Informaciones transmitidas diádicamente con posible distorsión.
  - `CONTRADICTORY_INFO` (Rosa): Proposiciones en conflicto con evidencia observada.
  - `REFUTED_KNOWLEDGE` (Rojo): Hipótesis que fracasaron en ensayos experimentales.
  - `FORGOTTEN_KNOWLEDGE` (Gris pizarra): Saberes extintos por mortalidad de artesanos sin sucesores.
- **Proveniencia:**
  - Identificación del agente originador, historial de transmisiones maestro-aprendiz, notas de modificación y conteo de verificación.

---

### 3.5 Social Network Explorer (Red Social & Comunidades ADESCO)
- **Nodos:** Individuos sintéticos y colectivos (ADESCOs, cooperativas, talleres).
- **Tipos de Arista:** Familia, Amistad, Confianza, Comercio, Mentoría, Conflicto.
- **Métricas Visualizadas:**
  - Grosor de arista proporcional a la fuerza combinada $(\text{confianza} + \text{afinidad}) / 2$.
  - Resaltado de red egocéntrica al seleccionar un individuo para evitar saturación visual.
  - Indicadores de liderazgo y roles comunitarios.

---

### 3.6 Civilization Dashboard (Tablero Macroscópico)
- **Monitoreo Longitudinal:**
  - Curvas temporales vectoriales SVG con renderizado progresivo a partir del buffer de 2000 instantáneas históricas.
  - Demografía: Evolución de población viva, pirámide etaria simplificada y tasas de transición vital.
  - Economía: Coeficiente de Gini calculado formalmente:
    $$\text{Gini} = \frac{2 \sum_{i=1}^n i \cdot y_i}{n \sum_{i=1}^n y_i} - \frac{n+1}{n}$$
  - Cultura: Número de tradiciones vivas vs. pérdidas culturales irreversibles.
  - Medio Ambiente: Temperatura diurna/nocturna y regímenes de precipitación estacional.

---

### 3.7 Economy and Resources (Micro y Macroeconomía)
- **Precios de Referencia:** Pizarra de cotizaciones de productos salvadoreños clave (maíz blanco, frijol rojo de seda, café de altura, artesanías en barro de Ilobasco y mantas de San Sebastián).
- **Ecosistema Empresarial:** Registro de microempresas y talleres con saldo en caja y estatus operativo.
- **Crédito y Fiado:** Libro contable de contratos formales de crédito con tasa de interés y morosidad, junto con cuentas de fiado tradicional en tienditas de barrio.

---

### 3.8 Historical Timeline (Línea de Tiempo Interactiva)
- **Registro Cronológico:**
  - Eventos salientes del mundo (nacimientos, fallecimientos, descubrimientos, transacciones mayores, disputas, desastres climáticos).
  - Filtrado por importancia ($\ge 0.65$), tipo de evento o texto libre.
  - Navegación bidireccional: un clic en un evento resalta al agente o la ubicación en el mapa.

---

### 3.9 Simulation Laboratory (Banco Experimental)
- **Catálogo de Experimentos:**
  - Acceso directo a los experimentos automatizados de las Fases A-H, 04, 05, 06, 07, 08, 09, 10, 11, 12 y 13.
  - Lanzamiento con 1 clic con retorno asíncrono de estatus, tiempo de ejecución, métricas cuantitativas y resumen analítico.
- **Inyección de Escenarios:**
  - Activación inmediata de choques: Sequía severa, Bonanza comercial, Renacimiento cultural o Auge cafetalero.

---

### 3.10 Reports and Validation (Informes Científicos)
- **Visor Forense:**
  - Renderizado directo de los informes de validación empírica, tablas de benchmarking y análisis de causalidad.

---

## 4. CONTROL DE SIMULACIÓN Y OBSERVABILIDAD EN VIVO

### 4.1 Modos de Ejecución y Preajustes de Velocidad
- **Pausa / Paso a Paso:** Avance controlado de 1 tick (+15 minutos simulados) para inspección forense detallada.
- **Velocidades:**
  - `1×`: 1 tick por segundo (inspección pausada).
  - `10×`: 10 ticks por segundo (2.5 horas simuladas por segundo).
  - `100×`: 100 ticks por segundo (más de 1 día simulado por segundo).
  - `1000×`: Desacoplado al máximo rendimiento del hardware (>150 ticks/segundo en Ryzen 8700G).

### 4.2 Arquitectura SSE Desacoplada
- El motor de simulación opera en un hilo dedicado (`SimulationController._run_loop`).
- Si el navegador se congela, suspende la pestaña o experimenta demoras en el renderizado Canvas, el motor de simulación **no se ralentiza ni se bloquea**.
- Las colas de distribución SSE (`queue.Queue(maxsize=150)`) descartan paquetes obsoletos si un cliente no consume a tiempo, garantizando invariabilidad temporal en el servidor.
- Reconexión automática con retroceso exponencial ante desconexiones de red.
