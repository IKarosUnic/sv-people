# SALTBOR — ARQUITECTURA DE SIMULACIÓN GEOESPACIAL A GRAN ESCALA
## ESPECIFICACIÓN TÉCNICA: MOTOR PARA 1 MILLÓN DE AGENTES, LOD MULTINIVEL & RENDERING GPU

**Versión:** 1.0.0 — SALTBOR Extreme Scale Architecture  
**Hardware Objetivo:** AMD Ryzen 7 8700G (16 hilos), Radeon 780M (RDNA 3), 32 GB RAM DDR5, Windows 11  
**Escalas Evaluadas:** 1,000 · 10,000 · 50,000 · 100,000 · 500,000 · 1,000,000 individuos persistentes

---

## 1. PRINCIPIO FUNDAMENTAL

SALTBOR es un simulador de civilización a escala real, no un simulador pequeño sobre un mapa grande.
Millones de habitantes deben ser arquitecturalmente representables y persistentes, mientras que el cómputo detallado y el renderizado gráfico se asignan dinámicamente según la necesidad causal y el contexto espacial.

Bajo ninguna circunstancia se sacrificará la continuidad individual, la consistencia causal o la integridad científica para inflar artificialmente números de benchmark.

---

## 2. TAXONOMÍA DE LAS CUATRO POBLACIONES

Para desacoplar el almacenamiento, el cómputo y la visualización, la población total se divide estrictamente en cuatro subconjuntos no equivalentes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. POBLACIÓN PERSISTENTE                        │
│   Todos los individuos registrados en la civilización (hasta 1,000,000+)│
│   Almacenados en SQLite (WAL) en estructuras compactas indexadas.      │
│   Identidad única, genealogía, relaciones y saberes garantizados.      │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         │                                                     │
┌────────┴──────────────────────────┐       ┌──────────────────┴─────────┐
│     2. ACTIVAMENTE SIMULADA       │       │       3. AGREGADA          │
│   LOD 0: Deliberación Completa    │       │   LOD 2: Grupos y Hogares  │
│   LOD 1: Rutina Simplificada      │       │   LOD 3: Comunidades       │
│   (20 a 5,000 individuos en RAM)  │       │   LOD 4: Regiones y Macro  │
└────────────────┬──────────────────┘       └──────────────────┬─────────┘
                 │                                             │
                 └──────────────────┬──────────────────────────┘
                                    │ Proyección Espacial Frustum
┌───────────────────────────────────┴────────────────────────────────────┐
│                        4. POBLACIÓN RENDERIZADA                        │
│   Entidades visibles en el viewport actual de la cámara (GPU Instanced)│
│   Zoom < 13: Mapa de Densidad / Coropletas Regionales (LOD 4)          │
│   Zoom 13-15: Clústeres de Cohorte con Conteo Dinámico (LOD 2/3)       │
│   Zoom > 15: Tokens 2.5D Individuales (LOD 0/1, máx. 2,000 por cuadro)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ARQUITECTURA LOD MULTINIVEL (5 NIVELES)

### 3.1 Definición de Niveles
- **LOD 0 — Detalle Individual Completo:**
  - Modelo cognitivo completo: Deliberación MAUT, 6 subsistemas cerebrales, codificación episódica, grafo de conocimiento individual, navegación continua paso a paso.
  - Tasa de actualización: Cada 1 tick (15 min simulados).
- **LOD 1 — Individuos Simplificados:**
  - Ejecución heurística de rutinas diarias (trabajo, comida, sueño), cinemática lineal interpolada, decaimiento de necesidades por reglas fijas.
  - Tasa de actualización: Cada 2–4 ticks.
- **LOD 2 — Grupos Poblacionales (Cohortes / Hogares):**
  - Modelado de nivel de hogar o cuadrilla laboral. Movimiento grupal, consumo consolidado, preservación explícita de miembros excepcionales.
  - Tasa de actualización: Cada 8–16 ticks.
- **LOD 3 — Simulación Comunitaria:**
  - Ecuaciones diferenciales / en diferencias para dinámica demográfica, balances de mercado local, transmisión cultural y eventos comunitarios.
  - Tasa de actualización: Cada 32 ticks (8 horas simuladas).
- **LOD 4 — Simulación Regional:**
  - Densidad macro, modelo gravitacional de migración entre distritos de El Salvador, producción agregada e impacto ambiental/climático.
  - Tasa de actualización: Cada 96–128 ticks (24 a 32 horas simuladas).

### 3.2 Reglas de Transición, Promoción e Hidratación
1. **Regla de Causalidad:** Un individuo nunca se congela indefinidamente. Si un evento exógeno (accidente, desastre, crisis económica, citación judicial) afecta a su cohorte o ubicación, el individuo es promovido inmediatamente a LOD 0/1.
2. **Preservación de Excepciones:** Individuos con roles de liderazgo (alcalde, juez, presidente ADESCO), riqueza anómala (percentil 99/1) o estrés crítico (hambre > 0.85, salud < 0.20) se mantienen en simulación detallada sin importar si la cámara los enfoca.
3. **Contrato de Rehidratación:** Al promover un individuo desde el estado comprimido en base de datos al estado `SyntheticHuman` en RAM, se reconstruyen exactamente su personalidad, historial de memoria, inventario y relaciones sin pérdida de fidelidad.

---

## 4. PARTICIONAMIENTO ESPACIAL HÍBRIDO

Se implementan y evalúan tres estructuras espaciales:
1. **Uniform Spatial Grid:** Celdas regulares de 50 m para indexación $O(1)$ de movimiento continuo en zonas urbanas densas.
2. **Adaptive Spatial Quadtree:** Subdivisión adaptativa que desciende hasta 8 niveles de profundidad en centros densos (San Salvador Centro) y se mantiene en niveles superiores en zonas rurales montañosas (Chalatenango, Morazán).
3. **R-Tree (STRtree):** Indexación de polígonos estáticos (huellas de edificios, parcelas agrícolas, límites distritales).

---

## 5. AGREGACIÓN POBLACIONAL MATEMÁTICAMENTE EXPLÍCITA

### 5.1 Demografía de Cohortes
La población agregada se clasifica en matrices de cohortes por grupo etario $a \in [0..17]$ (quincenios) y género $g \in \{M, F\}$:
$$P_{a+1, g}(t + \Delta t) = P_{a, g}(t) \cdot (1 - \mu_{a, g}(t)) + M_{a, g}(t)$$
Donde $\mu_{a, g}(t)$ es la tasa de mortalidad modulada por salud y disponibilidad de alimentos, y $M_{a, g}(t)$ es el flujo migratorio neto.

### 5.2 Función de Producción Agregada
Para comunidades en LOD 3:
$$Y = A \cdot K^\alpha \cdot (L \cdot h)^\beta$$
Donde $K$ es el capital de infraestructura comunitaria, $L$ es la mano de obra disponible, $h$ es el índice promedio de salud/educación, y $\alpha + \beta \le 1$.

---

## 6. RENDERING GPU & VIEWPORT STREAMING

1. **Protocolo de Streaming por Viewport:**
   - El cliente web MapLibre envía periódicamente su bounding box actual:
     `GET /api/gis/viewport_population?min_lon=...&min_lat=...&max_lon=...&max_lat=...&zoom=...&max_entities=2000`
   - El backend consulta el Quadtree espacial y devuelve únicamente las entidades que intersecan el frustum.
2. **Agrupamiento GPU (Clustering):**
   - Para niveles de zoom intermedios (zoom 12 a 15), los datos se entregan agrupados en puntos de cohorte con propiedades `point_count`, `avg_wealth`, `dominant_activity`.
   - Para zoom > 15, se entregan tokens individuales instanciados con radio, color y vector de desplazamiento.
3. **Presupuesto de Memoria y Cuadros:**
   - Máximo de 2,000 entidades renderizadas simultáneamente en DOM/WebGL para mantener 60 FPS estables en la GPU integrada Radeon 780M.
