---
name: saltbor-simulation
description: Discrete-time simulation loops, tick scheduling, state checkpoints, and emergent agent execution.
---

# SKILL: Simulation Core, Tick Scheduling & State Lifecycles

## 1. Objetivo
Dominar la ejecución, sincronización temporal, control de estados y persistencia transaccional del simulador SALTBOR. Garantizar determinismo estricto, reproducibilidad con semillas fijas y avance eficiente del tiempo sintético.

## 2. Cuándo Utilizarla
- Al modificar el bucle principal de `SimulationRunner.step()`.
- Al programar eventos periódicos (ciclos circadianos, días, cosechas anuales).
- Al implementar o depurar mecanismos de checkpointing y reanudación de estado.
- Al optimizar la tasa de simulación (ticks por segundo).

## 3. Instrucciones de Trabajo
1. **Comprender la Escala Temporal**:
   - 1 Tick = 15 minutos de tiempo simulado.
   - 96 Ticks = 1 Día simulado (24 horas).
   - 35,040 Ticks = 1 Año solar simulado (365 días).
2. **Respetar la Fase Diaria (Amortización Temporal)**:
   - Tareas pesadas (cálculo de Gini, cobro de cuotas, decaimiento de normas, balance institucional) deben programarse estrictamente al inicio del día (`tick_of_day == 0`), no en cada tick de 15 minutos.
3. **Mantener Determinismo del RNG**:
   - Todo número aleatorio debe provenir del `master_rng` (`np.random.default_rng(seed)`) del runner o del generador local de la entidad derivado de su semilla.
   - Inicializar siempre `random.seed(seed)` al crear un `SimulationRunner` para evitar divergencias entre ejecuciones.
4. **Persistencia Transaccional**:
   - El estado de la simulación se serializa en SQLite v4 bajo transacciones protegidas con WAL.
   - Guardar el estado en blobs JSON estruturados (`simulation_state`) para permitir reanudar la simulación exactamente en el tick donde se detuvo.

## 4. Procedimientos y Métodos
- **Orden de Ejecución en `step()`**:
  1. Avance del reloj (`SimulationClock.tick()`).
  2. Actualización de clima y entorno físico.
  3. Ejecución de decisiones y movilidad de agentes activos (con Cognitive LOD).
  4. Procesamiento de interacciones espaciales y encuentros.
  5. Evaluación psicológica y consolidación de memoria.
  6. Si es medianoche (`tick_of_day == 0`): ciclo social e institucional diario.
  7. Despacho y registro de eventos en el `EventBus`.
  8. Emisión de snapshots para la visualización UI.

## 5. Referencias y Repositorios Clave
- *Simulating Social Phenomena* (Epstein & Axtell, Growing Artificial Societies).
- Repositorio de referencia: `projectmesa/mesa` (modelos de `RandomActivation` y `StagedActivation`).
- Repositorio de referencia: `simpy/simpy` (gestión de colas de eventos).

## 6. Herramientas Requeridas
- `saltbor.core.clock.SimulationClock`
- `saltbor.simulation.runner.SimulationRunner`
- `scripts/benchmark_phase19.py`

## 7. Criterios de Validación
- Semilla idéntica produce estados idénticos en dos instancias separadas (`test_phase11_experiments.py::Experiment11_B`).
- Throughput $>100$ ticks/segundo con 20 agentes en hardware estándar.
- Checkpoint de SQLite recuperable al 100% tras reiniciar el proceso.

## 8. Limitaciones
- Evitar saltos de tiempo no físicos (e.g. teletransportación de agentes sin registrar ticks de viaje).
- No ejecutar operaciones de I/O de disco bloqueantes dentro de los ticks de 15 minutos.
