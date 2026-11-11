# SALTBOR — PHASE 1.2.2 TECHNICAL DEBT
## COMPREHENSIVE TECHNICAL DEBT REGISTER, ARCHITECTURAL FRICTION & MITIGATION STRATEGY

**Fecha:** 10 de Noviembre de 2026  
**Auditoría:** Arquitectura de Software e Integridad de Código  
**Repositorio:** `sv people` / Rama `master`  
**Alcance:** Fases 0.1 a 1.2.2  

---

## 1. INTRODUCCIÓN Y METODOLOGÍA DEL REGISTRO

A lo largo de las fases de desarrollo (desde la génesis de agentes individuales en 0.1 hasta la validación civilizatoria adversarial en 1.2.2), el sistema ha crecido de forma sostenida manteniendo 359 tests en verde. Sin embargo, el rápido ritmo de investigación y extensión ha generado capas de deuda técnica que deben ser catalogadas y gestionadas para garantizar la escalabilidad futura.

Este documento establece el inventario formal de deuda técnica clasificado en cinco dimensiones críticas:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIMENSIONES DE LA DEUDA TÉCNICA                                 │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│ 1. Deuda Arquitectónica y Acoplamiento │ Dispersión de enums, firmas históricas        │
│ 2. Deuda Computacional y Rendimiento   │ Bucles O(N^2) en redes densas, GIL de Python  │
│ 3. Deuda en Modelado Cognitivo         │ Saliencia fija en memoria, heurísticas fijas  │
│ 4. Deuda de Persistencia y Serialización│ Esquema SQL manual sin migraciones declarativas│
│ 5. Deuda en Infraestructura de Pruebas │ Tiempos de ejecución en suites longitudinales │
└────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 2. INVENTARIO DETALLADO DE DEUDA TÉCNICA

### 2.1 Deuda Arquitectónica y de Tipos
- **TD-ARQ-01: Redundancia en Enums de Dominio**:
  - *Descripción:* Coexisten enums con terminología solapada en distintos paquetes (e.g., `HistoricalCategory` vs `EventType`, o nombres de biomas en geografía vs recursos de asentamiento).
  - *Impacto:* Requiere mapeos manuales en los puntos de integración y puede inducir a errores sutiles de conversión.
  - *Prioridad:* Media.
- **TD-ARQ-02: Parámetros Históricos en Constructores de Agentes**:
  - *Descripción:* Dataclasses y modelos Pydantic como `SyntheticHuman` han acumulado campos auxiliares para compatibilidad con fases antiguas (`given_name`, `family_name`, `legacy_traits`).
  - *Impacto:* Aumenta la complejidad ciclomática de las funciones fábrica de agentes.
  - *Prioridad:* Baja.

### 2.2 Deuda Computacional y Algorítmica
- **TD-PERF-01: Complejidad Cuadrática en Grafos Sociales Densos ($O(N^2)$)**:
  - *Descripción:* En poblaciones pequeñas ($N \le 100$), el cálculo de distancias y actitudes entre pares es instantáneo ($< 1$ ms). Sin embargo, en poblaciones grandes ($N \ge 10,000$), el cálculo completo de vecindades sin particionado espacial o filtrado de grafo saturaría el hilo principal de Python.
  - *Mitigación:* Implementar un `LOD (Level of Detail)` social o k-d trees relacionales ya introducidos conceptualmente en Phase 0.7.
  - *Prioridad:* Alta para Phase 2.0.
- **TD-PERF-02: Ausencia de Paralelismo Multi-Núcleo en Sweeps de Simulación**:
  - *Descripción:* Actualmente, los barridos contrafactuales multi-semilla (`EXP_122_A`) se ejecutan secuencialmente en un único proceso.
  - *Mitigación:* Integrar `multiprocessing` o `concurrent.futures` para distribuir semillas en hilos de hardware independientes.
  - *Prioridad:* Media.

### 2.3 Deuda en Modelado Cognitivo y Epistémico
- **TD-COG-01: Umbrales Estáticos en Consolidación de Memoria**:
  - *Descripción:* La transferencia de memoria de trabajo a episódica utiliza un corte fijo de importancia $\ge 0.15$. En seres humanos reales, la saliencia mnémica es plástica y se modula por el nivel de cortisol, arousal emocional y privación física.
  - *Mitigación:* Hacer que el umbral de consolidación sea una función dinámica del estado emocional: $\theta_{\text{salience}}(t) = 0.15 - 0.05 \cdot \text{arousal}(t)$.
  - *Prioridad:* Media.
- **TD-COG-02: Máquina de Estados Estructurada en Descubrimiento Científico**:
  - *Descripción:* El ciclo de 12 etapas en `DiscoveryCycleTrace` avanza en secuencia estricta. No permite retrocesos heurísticos, saltos intuitivos o errores metodológicos de confirmación.
  - *Mitigación:* Modelar la trayectoria de investigación como un paseo aleatorio en un grafo epistémico dirigido con sesgo bayesiano.
  - *Prioridad:* Media.

### 2.4 Deuda de Persistencia y Base de Datos
- **TD-DB-01: Gestión de Esquema SQLite sin Herramienta de Migración**:
  - *Descripción:* El DDL de la base de datos en `saltbor/persistence/database.py` se inicializa mediante scripts SQL en texto plano dentro de código Python. No hay un versionado declarativo tipo Alembic/Flyway.
  - *Impacto:* Dificulta cambios estructurales en esquemas existentes sin reiniciar o recrear los archivos `.db`.
  - *Prioridad:* Media.
- **TD-DB-02: Serialización Parcial en JSON de Atributos Complejos**:
  - *Descripción:* Ciertas propiedades complejas de inventario o creencias se almacenan como cadenas JSON en columnas `TEXT` de SQLite en lugar de tablas relacionales normalizadas.
  - *Impacto:* Dificulta consultas analíticas directas con SQL puro sobre subcampos de creencias.
  - *Prioridad:* Baja.

### 2.5 Deuda en Infraestructura de Pruebas
- **TD-TEST-01: Falta de Pruebas de Estrés con Larga Duración en CI (10,000+ Ticks)**:
  - *Descripción:* La suite completa se ejecuta en $9.94$ segundos, lo cual es excelente para desarrollo rápido, pero los experimentos longitudinales (`EXP_122_J`) limitan su horizonte a 120 ticks para mantener la rapidez de ejecución.
  - *Mitigación:* Crear una suite de prueba nocturna (`nightly_stress_suite.py`) que ejecute simulaciones de 10,000 a 50,000 ticks.
  - *Prioridad:* Alta.

---

## 3. MATRIZ DE RIESGO Y CRONOGRAMA DE MITIGACIÓN

| Código Deuda | Categoría | Severidad | Probabilidad de Impacto | Fase Propuesta de Mitigación |
|---|---|---|---|---|
| **TD-PERF-01** | Algorítmica | Alta | Alta en $N > 1,000$ | **Fase 1.3** |
| **TD-TEST-01** | Pruebas | Alta | Media | **Fase 1.3** |
| **TD-COG-01** | Cognitiva | Media | Media | **Fase 1.3** |
| **TD-COG-02** | Cognitiva | Media | Baja | **Fase 2.0** |
| **TD-DB-01** | Persistencia | Media | Media | **Fase 1.3** |
| **TD-ARQ-01** | Arquitectura | Baja | Alta | **Fase 1.3** |
| **TD-ARQ-02** | Arquitectura | Baja | Baja | **Fase 2.0** |
| **TD-DB-02** | Persistencia | Baja | Baja | **Fase 2.0** |

---

## 4. CONCLUSIÓN DE AUDITORÍA

La deuda técnica de SALTBOR está **completamente acotada, identificada y bajo control**. Ninguna de las deudas inventariadas compromete la exactitud matemática de los 359 tests ni la reproducibilidad de los 12 experimentos de la Fase 1.2.2.
