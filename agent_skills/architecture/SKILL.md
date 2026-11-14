---
name: saltbor-architecture
description: Software architecture, modular decoupling, engine consolidation, and state flow design for SALTBOR.
---

# SKILL: Software Architecture & Subsystem Decoupling

## 1. Objetivo
Guiar el diseño, descomposición y acoplamiento limpio de los motores y subsistemas de SALTBOR. Garantizar que la arquitectura evolucione de forma modular, extensible y de alto rendimiento, evitando dependencias circulares, código espagueti o duplicación innecesaria de sistemas funcionales.

## 2. Cuándo Utilizarla
- Al diseñar o incorporar un nuevo motor o subsistema en SALTBOR.
- Al refactorizar interfaces entre capas (e.g. cognición, sociedad, economía, geografía, persistencia).
- Cuando se detecte duplicación funcional o acoplamiento excesivo entre componentes.
- Durante revisiones arquitectónicas previas a nuevas fases evolutivas.

## 3. Instrucciones de Trabajo
1. **Identificar la Capa Correcta**: Ubicar el componente dentro del modelo de capas de SALTBOR:
   - Capa 0: Núcleo físico, tipos básicos, reloj y configuración (`saltbor/core/`).
   - Capa 1: Individuo (fisiología, psicología, cognición, memoria, roles) (`saltbor/cognition/`, `saltbor/psychology/`, `saltbor/population/`).
   - Capa 2: Espacio y Entorno (geografía, clima, caminos, lugares, recursos físicos) (`saltbor/world/`).
   - Capa 3: Relaciones y Redes (vínculos diádicos, actitudes direccionales, parentesco) (`saltbor/social/`).
   - Capa 4: Instituciones y Gobernanza (organizaciones, normas, CPR, asambleas, empresas) (`saltbor/social/`, `saltbor/institutions/`).
   - Capa 5: Orquestación y Runtime (`saltbor/simulation/runner.py`, `extension_runtime.py`).
   - Capa 6: Persistencia e Interfaces (`saltbor/data/`, `saltbor/visualization/`).
2. **Definir Contratos Explícitos**: Utilizar modelos Pydantic v2 o dataclasses inmutables para el intercambio de datos entre subsistemas. Nunca pasar referencias mutables globales.
3. **Comunicación Vía Bus de Eventos**: Desacoplar productores de consumidores mediante `EventBus`. Los motores no deben invocar métodos privados de otros motores directamente si la interacción representa un acontecimiento histórico o social observable.
4. **Verificar Leyes de Conservación**: Ninguna abstracción de alto nivel debe omitir las verificaciones contables o físicas subyacentes.

## 4. Procedimientos y Métodos
- **Principio de Responsabilidad Única (SRP)**: Cada motor gestiona una entidad u ontología específica (e.g., `SocialNormEvolutionEngine` solo gestiona normas y sanciones; no gestiona la tesorería de las organizaciones).
- **Patrón Facade / Mediador**: `SimulationRunner` actúa como mediador orquestador del ciclo de ticks, coordinando la ejecución en fases amortizadas (ticks diarios a medianoche vs ticks de 15 minutos).
- **Aislamiento de Persistencia**: La lógica de negocio no debe contener sentencias SQL directas; el guardado y carga se delega a adaptadores de estado (`_checkpoint_body()` / `Database`).

## 5. Referencias y Repositorios Clave
- *Clean Architecture: A Craftsman's Guide to Software Structure and Design* (Robert C. Martin).
- *Domain-Driven Design: Tackling Complexity in the Heart of Software* (Eric Evans).
- Repositorio de referencia: `projectmesa/mesa` (patrones de orquestación ABM, evaluado como referencia en `EXTERNAL_REPOSITORY_CATALOG.md`).

## 6. Herramientas Requeridas
- Python 3.12+ (Pydantic v2, dataclasses, typing).
- `scripts/benchmark_phase19.py` para verificar que la arquitectura no introduce sobrecarga en ms/tick.

## 7. Criterios de Validación
- Cero importaciones circulares en el grafo de módulos.
- El tiempo de inicialización de `SimulationRunner` permanece bajo ($<0.2$ s).
- Todas las dependencias entre módulos fluyen hacia abajo en la jerarquía de capas.
- Suite completa de regresión (`python -m pytest`) pasa al 100%.

## 8. Limitaciones
- No forzar sobre-ingeniería ni crear capas de indirección abstractas para problemas triviales.
- El desacoplamiento no debe comprometer la velocidad en el bucle caliente (hot path) de la simulación.
