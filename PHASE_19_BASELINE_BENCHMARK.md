# SALTBOR — FASE 1.9: BENCHMARK DE LÍNEA BASE
## Medición Empírica del Rendimiento Previo a la Implementación de la Fase 1.9

**Fecha de ejecución:** 13 de noviembre de 2026  
**Entorno de prueba:** AMD Ryzen 7 8700G (16 CPUs) / 32 GB DDR5 RAM / Windows 11 Pro 64-bit / Python 3.14.5  
**Motor de base de datos:** SQLite 3.49+ en modo WAL (Write-Ahead Logging)  
**Script de referencia:** `scripts/benchmark_phase17.py` ejecutado en caliente sobre la arquitectura unificada de Fase 1.8.

---

## 1. MEDIDAS AISLADAS DEL MOTOR COGNITIVO Y PSICOLÓGICO

Esta prueba evalúa el coste intrínseco de la actualización de estados psicológicos, evaluaciones cognitivas OCC, regulación emocional y LOD poblacional sin I/O de disco ni resolución de decisiones físicas complejas.

| Población ($N$) | Ticks Medidos | Tiempo Creación (s) | Media (ms/tick) | p95 (ms/tick) | Máx (ms/tick) | Coste (ms/agente/tick) | CPU ms/tick | RSS Final (MB) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **20** | 5 | 0.025 | 0.034 | 0.031 | 0.048 | 0.00170 | 0.0 | 67.2 |
| **100** | 5 | 0.056 | 0.551 | 0.844 | 1.057 | 0.00551 | 0.0 | 70.8 |
| **500** | 5 | 0.312 | 1.430 | 1.366 | 2.628 | 0.00286 | 0.0 | 87.0 |
| **1.000** | 5 | 0.653 | 4.277 | 5.021 | 6.009 | 0.00428 | 3.125 | 105.7 |
| **10.000** | 5 | 8.327 | **44.372** | 47.338 | 47.801 | **0.00444** | 43.750 | 447.9 |

### Observaciones de la Capa Cognitiva:
- La capa psicológica escala con extraordinaria eficiencia gracias al gestor LOD: a 10.000 individuos sintéticos, el cálculo insume únicamente **44.37 ms/tick** (menos de 4.5 microsegundos por agente).
- El consumo de memoria se mantiene estable en 447.9 MB para 10.000 agentes.

---

## 2. MEDIDAS DE LA SIMULACIÓN COMPLETA (`SimulationRunner`)

Esta prueba evalúa la arquitectura completa de SALTBOR consolidada en la Fase 1.8: reloj, clima dinámico, orquestador de eventos, tránsito cinemático en OpenStreetMap sin teletransportación, aforos e inventarios en `PlaceProfile`, economía comercial y laboral, vivienda, salud, psicología OCC, DAG causal y persistencia en SQLite/WAL.

| Población ($N$) | Ticks Medidos | Warmup | Tiempo Init (s) | Media (ms/tick) | p95 (ms/tick) | Coste (ms/agente/tick) | Ticks/seg | Checkpoint (s) | Tamaño SQLite | Tamaño WAL | Filas Timeline |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **20** | 96 (1 día sim.) | 12 | 0.127 | **9.47** | 17.94 | 0.4734 | 105.62 | 0.105 | 4.38 MB | 5.05 MB | 436 |
| **100** | 48 (½ día sim.) | 12 | 0.137 | **91.39** | 163.90 | 0.9139 | 10.94 | 1.063 | 24.43 MB | 20.94 MB | 2.952 |

### Latencias de Consulta para Observabilidad y API REST (Población = 100):
- **Overview psicológico global (`/api/psychology/overview`):** 0.075 ms mediana.
- **Dossier snapshot individual (`/api/individuals/{uid}`):** 0.292 ms mediana.

---

## 3. IDENTIFICACIÓN DE CUELLOS DE BOTELLA PREVIOS A LA FASE 1.9

1. **Gestión de Relaciones Sociales e Índices Multidimensionales:**
   - A medida que las organizaciones crecen en membresía, calcular métricas de red $O(N^2)$ dentro del tick ralentizaría el runner.
   - **Requisito de Escalabilidad para Fase 1.9:**
     - Utilizar identificadores referenciales en índices `dict[str, ...]`.
     - Implementar **LOD Organizacional**: actualizar métricas de cohesión interna, legitimidad y tesorería en cadencias discretas (e.g. cada 24 a 96 ticks) en lugar de cada tick de 15 minutos, a menos que un evento directo (renuncia, malversación, elección) lo dispare.
     - Caché de estratificación social (cálculo de Gini y distribución por quintiles cada 96 ticks / 1 día simulado).

2. **Gestión de Recursos Comunes (CPR):**
   - El cómputo de regeneración hídrica y degradación de suelos debe procesarse como un paso agregado vectorial por recurso, no con iteraciones anidadas sobre todos los humanos.

3. **Gobernanza y Asambleas Deliberativas:**
   - La resolución de propuestas de votación debe operar por fases (`DEBATE` $\to$ `VOTING` $\to$ `RESOLVED`), procesando los votos en lotes durante asambleas programadas para no sobrecargar el bucle principal.
