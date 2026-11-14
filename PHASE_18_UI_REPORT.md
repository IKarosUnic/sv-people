# SALTBOR FASE 1.8: INFORME DE INTEGRACIÓN DE LA INTERFAZ DE USUARIO
## Fidelidad Visual, Capa Cartográfica MapLibre GL 2.5D y Observabilidad en Tiempo Real

**Fecha:** 13 de Noviembre de 2026  
**Capa de Presentación:** Vanilla ES6 (`saltbor/visualization/web/app.js`), HTML5 semántico (`index.html`), CSS3 moderno (`style.css`), MapLibre GL JS (WebGL)  
**Canal de Telemetría:** Server-Sent Events (SSE) en `/api/events/stream` y REST Endpoints en `/api/*`  

---

## 1. PRINCIPIO FUNDAMENTAL: FIDELIDAD EXACTA AL BACKEND

Uno de los requerimientos primordiales de la Fase 1.8 fue la **eliminación de discrepancias entre frontend y backend**. En versiones anteriores, algunas vistas renderizaban valores sintéticos estáticos o contadores desconectados de la simulación real.

En la Fase 1.8:
- **Cero datos inventados:** Si el backend tiene 20 agentes en memoria, la capa SIG y el explorador individual muestran exactamente 20 agentes (validado empíricamente en `EXP_18_R`).
- **Estados reales de lugares:** Las viviendas, pupuserías, mercados y clínicas reflejan en tiempo real sus ocupantes actuales, sus horarios de apertura, sus aforos y sus inventarios reales.
- **Transmisión de eventos vivos:** Cada bloqueo de calle, compra de víveres o faena comunal viaja instantáneamente por SSE hacia la interfaz del usuario.

---

## 2. INTEGRACIÓN CARTOGRÁFICA EN MAPLIBRE GL JS

La vista territorial (`#view-world`) opera sobre un lienzo WebGL acelerado por hardware a 60 FPS con las siguientes capas integradas:

### 2.1. Separación Estricta de Capas Cartográficas
1. **`REAL_WORLD_LAYER` (Inmutable)**:
   - Malla vial y ejes de calles reales de OpenStreetMap (ODbL 1.0).
   - Huellas de edificios con extrusión 2.5D basada en alturas reales o inferidas por tipo de estructura.
   - Puntos de interés y monumentos clave de San Salvador (Plaza Barrios, Catedral Metropolitana, BINAES, Mercado Central).
   - Hidrografía real (Río Acelhuate, Quebrada El Zapote) y curvas de nivel topográficas.
2. **`SIMULATION_LAYER` (Dinámico)**:
   - **Agentes sintéticos (`gis-layer-sim-agents`)**: Círculos codificados por color según su actividad actual (naranja = trabajo, verde = comida, índigo = descanso, cian = socialización, púrpura = estudio).
   - **Trayectorias viales activas (`gis-layer-sim-trajectories`)**: Polilíneas discontinuas sobre los ejes de calles de OSM que representan los viajes en curso generados por `TransportationEngine`.
   - **Amenazas e infraestructura bloqueada (`sim_blockage_*`)**: Marcadores visuales de advertencia en coordenadas exactas de deslizamientos e inundaciones.

### 2.2. Blindaje de Viewport y Clampeo de Coordenadas
Se eliminaron por completo los errores HTTP `422 Unprocessable Entity` causados cuando el usuario alejaba el zoom o desplazaba el mapa fuera de los meridianos extremos. Los endpoints `/api/geography/geojson`, `/api/geography/features` y `/api/geography/ecological_profile` ahora aplican clampeo defensivo a los rangos $[-180.0, 180.0]$ de longitud y $[-90.0, 90.0]$ de latitud, asegurando navegación sin interrupciones.

---

## 3. PANELES DE INSPECCIÓN Y OBSERVABILIDAD

### 3.1. Inspector de Lugares y Establecimientos (`Place Inspector`)
Al seleccionar un comercio, vivienda o edificio público en el mapa o en las tablas de comercio, el usuario visualiza:
- **Nombre y categoría cultural** (e.g., Pupusería, Tienda de barrio, Comedor, Taller, Clínica).
- **Horario de atención** (e.g., 06:00 - 20:00) y estado actual (`ABIERTO` o `CERRADO`).
- **Aforo y ocupación actual**: Barra de progreso indicando ocupantes presentes frente a capacidad máxima.
- **Lista nominal de ocupantes**: Nombres y edades de las personas dentro del inmueble.
- **Inventario físico**: Existencias restantes de bienes (e.g., 149 pupusas, 500 lbs frijol).
- **Menú de servicios**: Servicios disponibles con costo y efecto biológico/psicológico asociado.

### 3.2. Inspector de Tránsito y Desplazamiento (`Transit Inspector`)
Muestra en tiempo real la lista de personas caminando o viajando en transporte colectivo:
- Origen y destino identificados.
- Porcentaje de avance de la polilínea ($0\% \rightarrow 100\%$).
- Velocidad cinemática modulada por clima (e.g., 2.9 km/h bajo tormenta).
- Demoras viales o bloqueos encontrados en ruta.

### 3.3. Explorador de Causalidad
En la pestaña de Línea de Tiempo (`#view-timeline`), al hacer clic en cualquier acontecimiento notable:
- Se despliega el subpanel de causalidad que consulta `/api/world/causality/{event_id}`.
- Muestra la cadena de causas que lo originaron (e.g. Tormenta tropical $\rightarrow$ Deslizamiento $\rightarrow$ Cierre de calle).
- Muestra el árbol de efectos desencadenados (e.g. Retraso laboral $\rightarrow$ Pérdida de jornal $\rightarrow$ Faena ADESCO).

### 3.4. Modo Zen / Pantalla Completa Limpia (`Tecla H`)
Para demostraciones visuales o inspección inmersiva de la vida urbana, el usuario puede presionar la tecla `H` o el botón de Interfaz para ocultar instantáneamente la barra superior, el sidebar lateral y los paneles flotantes, dejando únicamente el gemelo digital 2.5D en pantalla completa, con un botón sutil flotante para restaurar la interfaz en cualquier momento.

---

## 4. CONCLUSIÓN

La interfaz de usuario de SALTBOR en la Fase 1.8 trasciende el rol de un simple "tablero de mandos": es una ventana transparente, fidedigna y científicamente rigurosa hacia el interior de la vida humana y social simulada en El Salvador.
