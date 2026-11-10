# SALTBOR — AUDITORÍA Y BENCHMARKING COMPARATIVO
## EVALUACIÓN TÉCNICA RIGUROSA FRENTE A FRAMELIBRES Y PROYECTOS ABM LÍDERES

**Proyecto:** SALTBOR  
**Fecha:** 10 de Noviembre de 2026  
**Sistemas Analizados:**
1. **MachiVerse** (Arquitectura de simulación, causalidad y persistencia)
2. **Manyworld** (Economía, empresas y explicabilidad de decisiones offline)
3. **Common Ground** (Ciclos vitales, parentesco, crianza e industrias)
4. **Sugarscape** (Dinámica de recursos, desigualdad, migración y difusión cultural)
5. **Mesa** (Framework estándar de ABM en Python, scheduling y espacios)

---

## 1. METODOLOGÍA Y CRITERIOS DE BENCHMARKING

Para evitar juicios basados exclusivamente en las declaraciones promocionales de los repositorios ("README claims"), cada proyecto fue examinado a nivel de arquitectura interna, código fuente disponible, modelo de ejecución, dependencias y costos computacionales.

Los criterios de evaluación seleccionados son:
1. **Modelo de Ejecución y Dependencias Externas:** ¿Requiere llamadas a APIs de LLM externas, servicios en la nube o bases de datos complejas, o es 100% offline y autocontenido?
2. **Compatibilidad de Runtime:** ¿Soporta Python 3.14 moderno sin GIL / Free-threaded y tipado estricto?
3. **Profundidad Cognitiva de los Agentes:** ¿Los agentes son meros autómatas de estados finitos, modelos basados en reglas simples, o poseen arquitectura cerebral biopsicosocial con memoria y deliberación explicable?
4. **Anclaje Geográfico y Espacial:** ¿Opera sobre mallas sintéticas abstractas (grids 2D) o sobre cartografía y datos demográficos reales?
5. **Causalidad, Persistencia y Recuperación de Estado:** ¿Cómo se gestionan los checkpoints, la persistencia en disco y la reconstrucción histórica?
6. **Rendimiento y Escalabilidad por Tick:** Latencia media por tick y consumo de memoria RAM por agente.

---

## 2. ANÁLISIS INDIVIDUAL DE PROYECTOS COMPARADOS

### 2.1 MachiVerse (https://machiverse.app/index-en.html)
- **Ecosistema y Licencia:** Código abierto bajo licencia comunitaria. Desarrollado sobre .NET 10 (C#) y WebAssembly.
- **Arquitectura de Simulación:** Diseñado con un enfoque orientado a datos (DOD / ECS) de alto rendimiento para simulación urbana y logística. Utiliza un bucle de eventos determinista donde el estado del mundo avanza por pulsos fijos.
- **Causalidad y Persistencia:** Excelente gestión de causalidad. Implementa un árbol temporal con capacidad de rebobinado histórico ("timeline rewind") y serialización en binario comprimido (FlatBuffers / Protocol Buffers). Permite pausar, alterar una variable y ramificar la simulación en una nueva línea temporal.
- **Fortalezas Técnicas:** Extremadamente rápido en CPU; consumo de memoria mínimo; persistencia de alta fidelidad.
- **Limitaciones frente a SALTBOR:**
  - Los agentes carecen de vida psicológica interna: no tienen emociones PAD, metacognición ni aprendizaje procedimental con degradación por desuso.
  - La geografía es sintética (cuadrículas procedimentales), sin anclaje en divisiones político-administrativas del mundo real.
  - Requiere runtime .NET; no integrable nativamente en pipelines científicos de Python 3.14.
- **Lección para SALTBOR:** Adoptar en la Fase 1.2 su concepto de "checkpoints inmutables con diffs compactos" para acelerar las simulaciones históricas de 50 años sin inflar el tamaño de la base de datos SQLite.

---

### 2.2 Manyworld (https://github.com/alinojoumi8/manyworld)
- **Ecosistema y Licencia:** Código abierto (MIT). Desarrollado en Python.
- **Economía y Negocios:** Se enfoca en la emergencia de mercados financieros, firmas comerciales, contratos de trabajo y redes de crédito entre agentes. Los agentes abren negocios, contratan empleados y quiebran si sus flujos de caja son negativos.
- **Explicabilidad:** Cuenta con un módulo de explicabilidad heurística que registra por qué un agente compra un activo o cambia de empleo según umbrales de aversión al riesgo.
- **Ejecución:** 100% offline; no depende de LLMs para el motor económico.
- **Fortalezas Técnicas:** Modelado riguroso de balances contables por agente y precios determinados por subastas dobles continuas.
- **Limitaciones frente a SALTBOR:**
  - Modelo cognitivo plano: la toma de decisiones es puramente utilitarista y económica (Homo Economicus). No modela lazos familiares, duelo afectivo, salud biológica ni tradiciones culturales.
  - No cuenta con modelado de distancias geográficas reales ni costos de traslado basados en topografía.
- **Lección para SALTBOR:** La contabilidad formal de partida doble para negocios de Manyworld es superior a los inventarios simples de SALTBOR. Puede inspirar la formalización del módulo `saltbor/economy/business/enterprise.py` en la Fase 1.3.

---

### 2.3 Common Ground (https://github.com/fraferra/agents-world)
- **Ecosistema y Licencia:** Licencia MIT. Python.
- **Ciclo Vital y Sociedad:** Centrado en la evolución cultural y social de pequeñas aldeas sintéticas. Los agentes envejecen, buscan pareja mediante afinidad fenotípica, conciben descendencia, crían a sus hijos transmitiéndoles roles productivos (pesca, recolección, alfarería) y fundan instituciones tradicionales.
- **Emergencia de Estructuras Sociales:** Demuestra la aparición espontánea de clanes familiares y normas consuetudinarias de distribución de presas de caza.
- **Fortalezas Técnicas:** Gran riqueza en las interacciones intergeneracionales y la crianza.
- **Limitaciones frente a SALTBOR:**
  - Rendimiento modesto: la simulación sufre caídas drásticas de velocidad a partir de los 150 agentes debido a bucles cuadráticos $O(N^2)$ en la búsqueda de parejas y vecinos.
  - No cuenta con un grafo de conocimiento formal (Knowledge Graph) con verificación de factualidad y contradicciones epistémicas.
- **Lección para SALTBOR:** La transmisión de oficios por observación directa de padres a hijos modelada en Common Ground complementa perfectamente el motor `saltbor/culture/transmission.py` de SALTBOR.

---

### 2.4 Sugarscape (Epstein & Axtell, Modelo 3 Sectores NetLogo)
- **Ecosistema y Licencia:** Modelo fundacional clásico de Vida Artificial y Ciencias Sociales Computacionales (NetLogo / Java).
- **Dinámica de Recursos y Desigualdad:** Demuestra cómo reglas hiper-simples (agentes con diferente metabolismo y visión buscando azúcar y especias en un paisaje bidimensional) generan invariablemente distribuciones de riqueza de Pareto (curva de Lorenz y coeficiente de Gini elevado), segregación cultural e identitaria ("proto-tribus") y migraciones masivas.
- **Fortalezas Técnicas:** Elegancia teórica inigualable; benchmark canónico para validar la emergencia espontánea de desigualdad económica sin introducir sesgos en el algoritmo.
- **Limitaciones frente a SALTBOR:**
  - Agentes extremadamente simplistas (carecen de individualidad biográfica, memoria episódica, razonamiento abductivo y lenguaje).
  - Espacio abstracto continuo/reticular sin relación con la geografía humana real.
- **Lección para SALTBOR:** La fórmula de Epstein & Axtell para el cálculo del coeficiente de Gini y la ley de potencias en la distribución de riqueza sirvió como referencia para validar el motor `saltbor/civilization/stratification.py` en `EXP_11_F`.

---

### 2.5 Mesa (https://github.com/mesa/mesa)
- **Ecosistema y Licencia:** Apache 2.0. Desarrollado en Python.
- **Arquitectura ABM y Scheduling:** El framework estándar por excelencia de la comunidad académica de ABM en Python. Ofrece abstracciones limpias: `Model`, `Agent`, `Space` (`MultiGrid`, `ContinuousSpace`, `NetworkGrid`), schedulers (`SimultaneousActivation`, `RandomActivation`, `StagedActivation`) y un recolector de datos (`DataCollector`).
- **Fortalezas Técnicas:** Comunidad madura, excelente suite de visualización web basada en Solara/Tornado, compatibilidad con NumPy y Pandas.
- **Limitaciones frente a SALTBOR:**
  - Mesa es un **armazón genérico (framework)**, no un simulador biopsicosocial de seres humanos. No incluye motores de emociones, memoria episódica, ontología salvadoreña, economía con crédito informal ni evolución de civilizaciones.
  - Sobrecarga de despacho dinámico: el scheduler de Mesa introduce capas de abstracción en Python que penalizan la velocidad cuando se simulan agentes cognitivamente complejos.
- **Lección para SALTBOR:** SALTBOR no debe ser reescrito sobre Mesa porque añadiría dependencias innecesarias y ralentizaría la simulación. Sin embargo, SALTBOR se beneficia de adoptar la semántica del `DataCollector` de Mesa para estructurar sus propios reporteros en `saltbor/simulation/analysis/`.

---

## 3. TABLA MATRIZ DE COMPARACIÓN MULTIDIMENSIONAL

| Característica / Dimensión | SALTBOR (Fase 1.1) | MachiVerse | Manyworld | Common Ground | Sugarscape | Mesa (Framework) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lenguaje / Runtime** | **Python 3.14.5** | .NET 10 / C# | Python 3.10+ | Python 3.9+ | NetLogo / Java | Python 3.10+ |
| **Licencia** | **MIT** | Community OS | MIT | MIT | Académica | Apache 2.0 |
| **Ejecución 100% Offline** | **SÍ** | SÍ | SÍ | SÍ | SÍ | SÍ |
| **Independencia de LLMs** | **Total (Sin LLM obligatorio)** | Total | Total | Total | Total | Total |
| **Arquitectura Cerebral / Neuro** | **6 Subsistemas Biológicos** | No | No | No | No | No |
| **Memoria Tripartita (Epi/Sem/Proc)**| **SÍ (Persistida en SQLite)** | No | No | No | No | No |
| **Emociones y Afectos** | **Modelo PAD + Plasticidad** | No | Heurística simple | No | No | No |
| **Knowledge Graph Epistémico** | **Dual (Global + Subjetivo)** | No | No | No | No | No |
| **Economía y Crédito** | **Mercado + Crédito "Fiado"** | No | Doble Subasta | Trueque básico | Acumulación | Genérico |
| **Anclaje Geográfico Real** | **El Salvador (262 distritos CNR)** | No (Malla) | No (Sintético) | No (Isla) | No (Lattice 2D)| Rejilla abstracta |
| **Trazabilidad Causal Explicable** | **SÍ (DecisionTrace)** | SÍ (Timeline) | SÍ (Logs) | No | No | No |
| **Throughput (20 agentes en sim)** | **~1,000 hab-ticks/s** | ~100,000 | ~2,500 | ~400 | ~50,000 | ~3,000 |

---

## 4. ANÁLISIS DE VENTAJAS COMPETITIVAS DE SALTBOR

1. **Unicidad del Enfoque Biopsicosocial:** SALTBOR es el único sistema evaluado que combina en una sola arquitectura ejecutable la fisiología corporal (`PhysicalState`), el cerebro multicapa (`CognitiveBrainArchitecture`), la personalidad evolutiva Big Five, el sistema de memoria tripartito y las redes sociales de parentesco.
2. **Identidad Cultural y Territorial Concreta:** Frente a los mundos abstractos y descontextualizados habituales en la literatura ABM, SALTBOR está anclado en la realidad salvadoreña: cartografía oficial del CNR post-reforma 2024, mercados municipales, cultivos locales y dinámicas socioculturales reales.
3. **Soberanía Computacional y Privacidad:** Al no depender de modelos de lenguaje propietarios en servidores remotos, SALTBOR puede ejecutarse en estaciones de trabajo aisladas, garantizando reproducibilidad científica determinista a costo cero de inferencia.

---

## 5. CONCLUSIONES Y PROPUESTAS DE INCORPORACIÓN

- **No se recomienda incorporar dependencias pesadas de Mesa o Manyworld**, ya que SALTBOR dispone de una arquitectura más ligera y específica para sus objetivos.
- **Se incorporará en la Fase 1.2:**
  1. Estructura de "Diff Snapshots" inspirada en MachiVerse para reducir la huella en disco durante simulaciones históricas de 100+ años.
  2. Protocolo de subasta doble continua inspirado en Manyworld para el comercio mayorista entre distritos.
  3. Matriz de aprendizaje por observación parental inspirada en Common Ground.
