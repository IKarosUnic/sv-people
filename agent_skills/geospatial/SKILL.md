---
name: saltbor-geospatial
description: OpenStreetMap topology, spatial routing, coordinates, terrain slope, bridges, and obstacle navigation.
---

# SKILL: Geospatial Modeling, OpenStreetMap & Territorial Navigation

## 1. Objetivo
Modelar el territorio geográfico real de El Salvador con fidelidad cartográfica: coordenadas geodésicas (WGS84), red vial de OpenStreetMap, topografía accidentada, ríos, pendientes pronunciadas, puentes estratégicos y obstáculos climáticos/desastres.

## 2. Cuándo Utilizarla
- Al integrar nuevas ubicaciones, cantones, caseríos o distritos en el registro espacial.
- Al calcular distancias, rutas de navegación o tiempos de viaje realistas.
- Al modelar obstáculos viales (derrumbes en Los Chorros, crecidas de ríos, caminos rurales deslavados).
- Al proyectar la movilidad peatonal o vehicular con penalizaciones por pendiente y carga.

## 3. Instrucciones de Trabajo
1. **Utilizar Fuentes Cartográficas Verificables**:
   - Basarse en nodos, vías y relaciones reales de OpenStreetMap (OSM) y demarcaciones del Centro Nacional de Registros (CNR).
2. **Cálculo de Distancias Sin Dependencias Pesadas**:
   - Usar la fórmula de Haversine para distancias esféricas entre coordenadas $(\text{lat}_1, \text{lon}_1)$ y $(\text{lat}_2, \text{lon}_2)$ con radio terrestre $R = 6,371,000$ m.
   - Usar `shapely` para pruebas de contención geométrica plana (punto en polígono).
3. **Penalización por Pendiente Topográfica**:
   - Los caminos con pendiente $>8\%$ deben aumentar el coste de energía y reducir la velocidad de caminata de los agentes según la función de Tobler o equivalente.
4. **Respeto a Puntos de Paso Obligados (Bridges & Chokepoints)**:
   - Los ríos no pueden cruzarse libremente salvo en vados o puentes formales. El cierre de un chokepoint (e.g. Carretera a Los Chorros) debe forzar desvíos reales o detener el tránsito.

## 4. Procedimientos y Métodos
- **Fórmula de Haversine**:
  $$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
  $$d = 2R \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
- **Penalización por Terreno y Carga**:
  $$\text{Velocidad} = \text{VelocidadBase} \times (1.0 - 0.5 \cdot \text{Pendiente}) \times (1.0 - 0.3 \cdot \text{CargaCuerpo})$$
- **Ruteo Dijkstra Nativo**:
  - Implementar búsqueda de caminos sobre el grafo de navegación en memoria (`NavigationGraph`), evitando dependencias pesadas como GDAL o OSMnx en tiempo de ejecución.

## 5. Referencias y Repositorios Clave
- OpenStreetMap El Salvador extract (Geofabrik).
- Repositorio de referencia: `gboeing/osmnx` (referencia algorítmica para simplificación de redes).
- `saltbor/world/gis/`, `saltbor/world/transportation/`.

## 6. Herramientas Requeridas
- `shapely` (Core geometry).
- `numpy` (Vectorized coordinates).
- `LocationRegistry`, `NavigationGraph`.

## 7. Criterios de Validación
- Tiempos de viaje realistas (e.g., San Esteban Catarina a San Salvador: 45–60 km, tiempos consistentes con topografía y modo de transporte).
- Los Chorros bloqueado redirige a rutas alternas o suspende viajes.
- Cero coordenadas invertidas (latitud en torno a $+13.6^{\circ}$ a $+14.0^{\circ}$, longitud en torno a $-88.8^{\circ}$ a $-89.3^{\circ}$).

## 8. Limitaciones
- No renderizar mallas 3D complejas en el backend; el cálculo de elevación se maneja vía pendientes tabuladas o perfiles de elevación simplificados.
