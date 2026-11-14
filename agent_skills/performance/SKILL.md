---
name: saltbor-performance
description: Performance optimization, profiling, latency benchmarking (ms/tick), memory RSS tracking, and vectorization.
---

# SKILL: Performance Optimization, Latency Benchmarking & Resource Profiling

## 1. Objetivo
Mantener a SALTBOR operando a máxima velocidad de ejecución y mínimo consumo de memoria RAM. Identificar cuellos de botella algorítmicos, optimizar la latencia por tick (ms/tick), monitorear el tamaño de residencia en memoria (RSS MB) y aplicar vectorización NumPy/Numba cuando sea pertinente.

## 2. Cuándo Utilizarla
- Tras implementar un nuevo subsistema o añadir lógica a los ticks frecuentes.
- Cuando la simulación experimente degradación en la tasa de ticks por segundo.
- Al preparar benchmarks formales comparativos entre fases.
- Al escalar la población a 500, 1,000 o 10,000 agentes.

## 3. Instrucciones de Trabajo
1. **Medir Antes de Optimizar**:
   - Nunca aplicar optimizaciones prematuras o adivinanzas. Utilizar `time.perf_counter()`, `cProfile` o scripts de benchmark dedicados.
2. **Diferenciar Pruebas Aisladas vs Integradas**:
   - Medir el subsistema nuevo de forma aislada para conocer su coste intrínseco (e.g. `run_social_layer_population` en `scripts/benchmark_phase19.py`).
   - Medir el `SimulationRunner` completo para evaluar el impacto sistémico global (con SQLite, EventBus y UI snapshots).
3. **Optimizar la Complejidad Algorítmica**:
   - Reemplazar búsquedas $O(N^2)$ por índices basados en diccionarios $O(1)$ o árboles espaciales $O(N \log N)$.
   - Vectorizar cálculos estadísticos (Gini, medias, varianzas) con NumPy en lugar de bucles `for` en Python puro.
4. **Monitoreo de Memoria y Recolección de Basura**:
   - Forzar `gc.collect()` antes de iniciar mediciones para evitar penalizaciones artificiales.
   - Medir RSS mediante `psutil.Process().memory_info().rss` para detectar fugas de memoria.

## 4. Procedimientos y Métodos
- **Métricas Clave de Rendimiento**:
  - `ms_per_tick_mean`: Tiempo promedio por ciclo completo de simulación.
  - `ms_per_tick_p95`: Percentil 95 de latencia (detección de picos aperiódicos).
  - `ms_per_agent_tick`: $\text{LatenciaPromedio} / N$ (coste unitario por individuo).
  - `ticks_per_second`: $1000.0 / \text{ms\_per\_tick\_mean}$.
- **Técnicas de Optimización Aprobadas**:
  - *Cognitive Level of Detail (LOD)*: Agentes distantes o en reposo no evalúan árboles cognitivos pesados cada tick.
  - *Amortización Temporal*: Tareas macro se ejecutan una vez al día (`tick_of_day == 0`).
  - *Estructuras Compactas*: Usar `__slots__` o dataclasses livianas para entidades instanciadas en decenas de miles.

## 5. Referencias y Repositorios Clave
- *High Performance Python* (Micha Gorelick & Ian Ozsvald).
- Repositorio de referencia: `numba/numba` (JIT compiler para funciones matemáticas puras).
- `scripts/benchmark_phase19.py`, `scripts/benchmark_phase17.py`.

## 6. Herramientas Requeridas
- `psutil` (Memory profiling).
- `cProfile`, `pstats` (CPU profiling).
- `numpy` (Vectorized arrays).

## 7. Criterios de Validación
- Capa social aislada: $<1.0$ ms/tick para 100 agentes; $<100$ ms/tick para 10,000 agentes.
- Simulador completo: $>100$ ticks/s para $N=20$; $>10$ ticks/s para $N=100$.
- Memoria RSS contenida ($<450$ MB a 10,000 agentes tras 50 ticks).

## 8. Limitaciones
- La optimización de rendimiento jamás puede comprometer la exactitud contable o el rigor científico de la simulación.
