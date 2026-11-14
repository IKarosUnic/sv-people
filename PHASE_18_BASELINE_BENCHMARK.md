# SALTBOR — FASE 1.8: BENCHMARK DE LÍNEA BASE
## Medición Empírica del Rendimiento Previo a la Integración de la Fase 1.8

**Fecha de ejecución:** 13 de noviembre de 2026  
**Entorno de prueba:** AMD Ryzen 7 8700G con gráficos Radeon 780M / 32 GB DDR5 RAM / Windows 11 Pro 64-bit / Python 3.14.5  
**Motor de base de datos:** SQLite 3.49+ en modo WAL (Write-Ahead Logging)  
**Script de referencia:** `scripts/benchmark_phase17.py` ejecutado en caliente.

---

## 1. MEDIDAS AISLADAS DEL MOTOR COGNITIVO Y PSICOLÓGICO

Esta prueba aísla el coste intrínseco de la actualización de estados psicológicos, evaluaciones cognitivas OCC, regulación emocional y LOD poblacional sin I/O de disco ni resolución de decisiones complejas.

| Población ($N$) | Ticks Medidos | Tiempo Creación (s) | Media (ms/tick) | p95 (ms/tick) | Máx (ms/tick) | Coste (ms/agente/tick) | CPU ms/tick | Checkpoint Chars |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **20** | 5 | 0.027 | 0.033 | 0.031 | 0.043 | 0.00165 | 0.0 | 31.387 |
| **100** | 5 | 0.062 | 0.171 | 0.207 | 0.220 | 0.00171 | 0.0 | 155.627 |
| **500** | 5 | 0.345 | 1.167 | 1.195 | 2.314 | 0.00233 | 0.0 | 776.827 |
| **1.000** | 5 | 0.734 | 3.783 | 3.903 | 4.898 | 0.00378 | 3.125 | 1.553.327 |
| **10.000** | 5 | 9.477 | 56.122 | 57.439 | 57.795 | 0.00561 | 53.125 | 15.530.327 |

### Observaciones del Motor Cognitivo Aislado:
- El motor escala de forma sublineal a moderadamente lineal gracias a la arquitectura LOD (FULL en tick 1, ROUTINE en tick 2, MACRO en tick 8, DORMANT en tick 24).
- A 10.000 agentes, el motor psicológico toma únicamente **56.12 ms/tick** (0.0056 ms por agente), lo que demuestra que la cognición por sí sola no es el cuello de botella.

---

## 2. MEDIDAS DE LA SIMULACIÓN COMPLETA (`SimulationRunner`)

Esta prueba evalúa el ciclo de vida completo de SALTBOR: reloj, clima ambiental, orquestador, comercio, vivienda, mercado laboral, salud física, psicología OCC, árbol causal de eventos, persistencia en SQLite/WAL y serialización de checkpoints.

| Población ($N$) | Ticks Medidos | Ticks Warmup | Tiempo Init (s) | Media (ms/tick) | p95 (ms/tick) | Coste (ms/agente/tick) | Ticks/seg | Checkpoint (s) | Tamaño SQLite | Tamaño WAL | Filas Timeline |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **20** | 96 (1 día sim.) | 12 | 0.132 | **8.35** | 15.87 | 0.4175 | 119.74 | 0.074 | 3.73 MB | 4.39 MB | 358 |
| **100** | 48 (½ día sim.) | 12 | 0.162 | **76.08** | 127.61 | 0.7608 | 13.14 | 0.960 | 20.39 MB | 17.81 MB | 2.280 |
| **10.000** | 3 | 1 | 7.186 | **68.102,5** | 83.175,7 | 6.8102 | 0.015 | 17.492 | 237.96 MB | 239.99 MB | 2.462 |

### Latencias de Consulta para Observabilidad y API REST (Población = 100):
- **Overview psicológico global (`/api/psychology/overview`):** 0.073 ms mediana.
- **Dossier snapshot individual (`/api/individuals/{uid}`):** 0.264 ms mediana.

---

## 3. CUELLOS DE BOTELLA Y ANÁLISIS FORENSE PREVIO A LA FASE 1.8

1. **Superlinealidad en Escala Masiva (100 $\to$ 10.000 agentes):**
   - Mientras que la población se multiplica por 100, el tiempo por tick se multiplica por ~895 (de 76 ms a 68,1 s).
   - El coste por agente sube de 0.76 ms a 6.81 ms.
   - **Causa raíz:** En `SimulationRunner.step()`, la construcción del índice de ubicación y la resolución de co-ubicación (`get_at_location`) junto con la serialización incremental de SQLite para miles de agentes sin partición espacial geográfica genera contención de memoria e iteraciones redundantes.

2. **Coste de Checkpoint en SQLite:**
   - A 10.000 agentes, el guardado en base de datos toma **17.49 segundos**, y el archivo WAL alcanza los 240 MB.
   - Es indispensable optimizar los upserts mediante lotes transaccionales estructurados (`executemany`) y evitar escrituras de entidades inactivas que no cambiaron de estado.

3. **Retos de la Fase 1.8:**
   - La introducción de trayectorias de viaje reales paso a paso sobre la red vial OSM (121.344 tramos) podría aumentar drásticamente el coste por tick si se recalcula la ruta Dijkstra en cada paso.
   - **Solución arquitectónica requerida:** Caché de caminos precalculados, interpolación cinemática lineal sobre la polilínea del tramo vial y actualización espacial basada en eventos para agentes que no han cambiado de tramo.
