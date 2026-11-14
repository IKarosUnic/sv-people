---
name: saltbor-orchestration
description: Hierarchical multi-agent loop orchestration, cost-aware dynamic model routing, and review-and-fix workflows for SALTBOR.
---

# SKILL: Multi-Agent Loop Orchestration & Cost-Aware Model Routing

## 1. Objetivo
Estructurar, coordinar y ejecutar flujos de trabajo multi-agente reproducibles y eficientes en costos para el desarrollo, auditoría y evolución de SALTBOR. Asignar dinámicamente modelos de lenguaje según la complejidad del problema, evitando el uso indiscriminado de modelos de alto costo computacional y garantizando una estricta segregación de responsabilidades.

## 2. Cuándo Utilizarla
- Al implementar nuevas características, motores de simulación o refactorizaciones complejas que involucren especificación, codificación y auditoría.
- Al coordinar tareas compuestas que requieran investigación de literatura científica, redacción de documentación y pruebas automatizadas.
- Para ejecutar bucles cerrados de revisión y corrección (*Review-and-Fix Loops*) de forma desatendida y segura.
- Al orquestar subagentes o equipos en Swarm sobre componentes independientes del repositorio sin colisiones de archivos.

## 3. Instrucciones de Trabajo
1. **Inspección Previa de Graphify**:
   - Antes de iniciar cualquier tarea de código, ejecutar `python -m graphify query "<concepto>"` para ubicar los nodos afectados y sus relaciones de dependencia en `graphify-out/graph.json`.
2. **Clasificación de Complejidad y Selección de Modelo**:
   - **Baja Complejidad (Writer)**: Modelos ligeros (`flash_lite` o `gemini-3.8-flash-low`). Tareas de documentación, comentarios, formateo JSON, normalización de esquemas.
   - **Complejidad Moderada (Implementer / Auditor Estándar)**: Modelos medianos (`flash` o `gemini-3.8-flash-medium`). Programación estructurada, tests unitarios en Pytest, refactorizaciones y revisión de código estándar.
   - **Alta Complejidad (Research / Auditor Crítico / Orchestrator)**: Máximo razonamiento con **Gemini 3.8 Flash (High)** (`model="inherit"` en dynamic workflows o `gemini-3.8-flash-high` en Swarm). Descomposición de arquitectura, deducción causal, análisis de leyes de conservación y arbitraje final. *(El tier `pro` queda estrictamente excluido por su inferioridad de capacidad frente a Flash 3.8 High).*
3. **Segregación Estricta de Roles**:
   - El *Writer* nunca modifica lógica de simulación ni motores nucleares.
   - El *Implementer* programa contra especificaciones y escribe pruebas unitarias.
   - El *Auditor* evalúa el código de forma independiente (prohibido que el autor se audite a sí mismo).
   - El *Orchestrator* evalúa la aceptación global y controla la terminación del flujo.
4. **Delimitación de Bucles y Presupuestos**:
   - Todo bucle de revisión-corrección debe contar con un límite máximo estricto (`max_iterations <= 3`).
   - Aplicar `with_budget(..., max_seconds=180)` o timeouts explícitos para impedir ejecuciones colgadas.
5. **Verificación y Actualización Post-Implementación**:
   - Correr la suite de pruebas Pytest (`python -m pytest tests/<subsystem>/ -v`).
   - Si se modificó la topología del código, ejecutar la actualización incremental de Graphify (`python -m graphify update .`).

## 4. Procedimientos y Métodos
- **Patrón de Flujo de Trabajo Secuencial con Bucle de Corrección**:
  ```
  ORCHESTRATOR (Descomposición y Criterios de Aceptación)
       ↓
  RESEARCH (Revisión Teórica / Estado del Arte - si aplica)
       ↓
  WRITER (Especificación Formal de Requisitos)
       ↓
  IMPLEMENTATION (Generación de Código + Tests Unitarios)
       ↓
  AUDITOR (Auditoría Estricta e Independiente)
       ↓
  [¿Aprobado?]
    ├── NO → Retroalimentación al IMPLEMENTATION (máx 3 iteraciones)
    └── SÍ → ORCHESTRATOR (Revisión Final y Validación de Integración)
  ```
- **Ejecución Paralela Disyunta**:
  - Tareas en paralelo solo se permiten si operan sobre archivos o ramas disyuntas (`workspace="branch"` o `workspace="share"`).
  - Nunca permitir que dos agentes editen el mismo archivo simultáneamente.

## 5. Referencias y Repositorios Clave
- [AGENT_ORCHESTRATION_ARCHITECTURE.md](file:///c:/GIT%20HUB/sv%20people/AGENT_ORCHESTRATION_ARCHITECTURE.md)
- [MODEL_ROUTING_POLICY.md](file:///c:/GIT%20HUB/sv%20people/MODEL_ROUTING_POLICY.md)
- [AGENT_ROLE_REGISTRY.md](file:///c:/GIT%20HUB/sv%20people/AGENT_ROLE_REGISTRY.md)
- [LOOP_EXECUTION_POLICY.md](file:///c:/GIT%20HUB/sv%20people/LOOP_EXECUTION_POLICY.md)
- [AGENT_EVALUATION_REPORT.md](file:///c:/GIT%20HUB/sv%20people/AGENT_EVALUATION_REPORT.md)
- `C:\Users\PC\.gemini\antigravity\builtin\skills\run-workflow\SKILL.md`
- `C:\Users\PC\.gemini\antigravity\builtin\skills\native_swarm\SKILL.md`

## 6. Herramientas Requeridas
- Python 3.12+ (Python 3.14.5 nativo en el entorno).
- Antigravity Dynamic Workflows (`run_workflow` con `agent`, `parallel`, `pipeline`, `with_budget`, `tokens_used`).
- Graphify (`python -m graphify`).
- Pytest (`python -m pytest`).

## 7. Criterios de Validación
- 100% de los agentes operan con esquemas de salida tipados (`finish` JSON Schema).
- Cero bucles infinitos en ejecución.
- Reducción medible del consumo de tokens en tareas repetitivas al usar tiers ligeros.
- Cumplimiento estricto de las directivas de conservación y ejecución offline de SALTBOR.

## 8. Limitaciones
- No escalar a modelos superiores a menos que el agente de nivel inferior falle repetidamente o el auditor reporte ambigüedad arquitectónica insalvable.
- No ejecutar agentes autónomos sin supervisión en modificaciones del núcleo contable o de persistencia SQLite de SALTBOR sin previa aprobación del Orchestrator.
