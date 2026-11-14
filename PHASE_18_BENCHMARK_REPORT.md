# SALTBOR FASE 1.8: INFORME DE BENCHMARKS DE RENDIMIENTO Y ESCALABILIDAD
## Rendimiento Computacional, Consumo de Memoria y Latencia de Ruteo en Arquitectura Integrada

**Fecha de Medición:** 13 de Noviembre de 2026  
**Plataforma de Prueba:** AMD Ryzen 7 8700G (8 núcleos / 16 hilos @ 4.2 GHz), 32 GB RAM DDR5, Windows 11 AMD64  
**Entorno de Ejecución:** Python 3.14.5 (64-bit), SQLite 3.45 in-memory  
**Motores Activos Durante el Benchmark:**
- `SyntheticHuman` (Físico, Psicológico, Emocional, Decisional)
- `IntegratedWorldSimulationEngine`
- `TransportationEngine` (Navegación cinemática OSM, fatiga, clima)
- `WorldInteractionEngine` (Aforos, horarios, servicios, inventarios)
- `DailyLifeSimulationEngine` (Fases diurnas, biorritmos)
- `CausalEventGraph` (DAG de eventos acíclicos)
- `SocialEngine` (Redes y relaciones)

---

## 1. ESCALABILIDAD DE LA SIMULACIÓN COMPLETA

Se ejecutaron pruebas empíricas continuas sobre poblaciones crecientes para medir la latencia por tick (en milisegundos), la tasa de simulación en ticks por segundo (TPS) y el consumo de memoria física residente (RSS en MB).

### Tabla de Escalabilidad Empírica

| Población Activa | Latencia Media (ms) | Latencia Mediana (ms) | Percentil 95 (ms) | TPS Efectivo | Memoria RSS (MB) | Crecimiento Memoria (MB) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **20 agentes** | **7.56 ms** | 7.32 ms | 8.85 ms | **132.2 TPS** | 71.7 MB | +0.4 MB |
| **100 agentes** | **65.43 ms** | 64.12 ms | 74.20 ms | **15.3 TPS** | 92.7 MB | +1.8 MB |
| **500 agentes** | **446.64 ms** | 438.50 ms | 489.10 ms | **2.24 TPS** | 209.9 MB | +8.4 MB |
| **1.000 agentes** | **1,002.25 ms** | 985.40 ms | 1,120.60 ms | **1.00 TPS** | 343.8 MB | +18.2 MB |
| **10.000 agentes (LOD)** | **7.48 ms\*** | 7.10 ms | 8.20 ms | **133.7 TPS\*** | 412.0 MB | +12.5 MB |

*\*Nota para 10.000 agentes: A escala de 10K habitantes, el sistema aplica la arquitectura de Nivel de Detalle (LOD) establecida en la Fase 1.4: los agentes fuera del foco del observador ejecutan biorritmos y actualización estadística agregada (0.75 µs por agente), lo que permite mantener la interactividad sin saturación de CPU.*

---

## 2. LATENCIA DE RUTEO EN LA RED VIAL OSM

Para evaluar el impacto de la cartografía real de OpenStreetMap y asegurar que la navegación paso a paso no colapse el motor, se midieron 50 consultas de ruteo punto a punto aleatorias dentro del cuadrante urbano de San Salvador:
- **Tasa de Éxito de Rutas Halladas:** 100.0% (50/50)
- **Latencia Media de Ruteo A\*:** **22.78 ms**
- **Latencia Mediana:** 22.68 ms
- **Percentil 95 (P95):** 31.46 ms
- **Algoritmo:** A\* heurístico bidireccional sobre grafo ponderado por tipo de vía (`trunk`, `primary`, `secondary`, `residential`, `footway`).
- **Estrategia de Caché:** El motor almacena subredes locales y rutas recurrentes entre pares frecuentes de origen-destino (e.g. hogar $\leftrightarrow$ mercado central), reduciendo consultas repetidas a $<0.05$ ms.

---

## 3. IMPACTO DE LA FÍSICA Y EL CLIMA

El cálculo cinemático de los desplazamientos en `TransportationEngine.step()` incluye:
1. Interpolación de posición a lo largo de segmentos de polilínea WGS84.
2. Comprobación geométrica de zonas de bloqueo (derrumbe/inundación) mediante distancia euclidiana aproximada.
3. Modulación de velocidad por precipitación pluvial:
   - Clima seco ($0$ mm/h): Factor $\times 1.00$
   - Lluvia moderada ($0.5 - 5.0$ mm/h): Factor $\times 0.85$ (demora media $+17.6\%$)
   - Tormenta tropical ($>5.0$ mm/h): Factor $\times 0.65$ para peatones (demora media $+53.8\%$)
4. **Sobrecarga computacional:** La evaluación de 100 viajes activos en tránsito insume apenas **1.42 ms** por tick en la CPU, lo que representa menos del 2.2% del tiempo total de ciclo a escala de 100 agentes.

---

## 4. CUELLOS DE BOTELLA IDENTIFICADOS Y ESTRATEGIAS DE MITIGACIÓN

| Subsistema / Operación | Complejidad Previa | Cuello de Botella Detectado | Mitigación Aplicada en Fase 1.8 |
| :--- | :---: | :--- | :--- |
| **Búsqueda de Rutas OSM** | $\mathcal{O}(V \log V + E)$ | Llamadas repetidas a A\* en cada tick si el destino cambiaba. | Planificación diferida (`ActiveJourney` almacena la polilínea completa una sola vez al inicio). |
| **Evaluación Diurna** | $\mathcal{O}(N)$ | Llamadas redundantes a cálculo de rasgos de personalidad por tick. | Caché de perfiles diurnos en `DailyLifeSimulationEngine.profiles`. |
| **Grafo Social** | $\mathcal{O}(N^2)$ | Decaimiento e interacciones evaluadas entre todos los pares posibles. | Poda por vecindad espacial: solo los agentes presentes en el mismo `PlaceProfile` interactúan. |
| **Contención de Memoria** | $\mathcal{O}(T \cdot N)$ | Crecimiento no acotado del DAG causal tras miles de eventos. | Límite circular `max_nodes = 10,000` con descarte FIFO de nodos irrelevantes. |

---

## 5. CONCLUSIÓN

La arquitectura integrada de la Fase 1.8 demuestra una **escalabilidad robusta**:
- A escala de comunidad y barrio (20 a 100 agentes), la simulación corre en tiempo ultra-rápido ($>15$ TPS), ideal para exploración interactiva en tiempo real.
- A escala de distrito (500 a 1.000 agentes), la simulación se mantiene en tiempo real (1.0 a 2.2 TPS), permitiendo inspeccionar la vida urbana completa de San Salvador.
- A escala de ciudad (10.000 agentes), la combinación de perfiles diurnos ultralivianos (0.75 µs/agente) y LOD permite sostener el ritmo sin degradación del sistema anfitrión.
