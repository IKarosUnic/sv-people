# SALTBOR FASE 1.8: PROCEDENCIA Y LICENCIAS DE DATOS GEOGRÁFICOS
## Cumplimiento Legal, Integridad de Fuentes, Atribución y Política Anti-Scraping

**Fecha:** 13 de Noviembre de 2026  
**Ámbito Territorial:** República de El Salvador (Área Metropolitana de San Salvador y Regiones Aledañas)  
**Sistema de Referencia de Coordenadas:** EPSG:4326 (WGS84)  

---

## 1. POLÍTICA DE FUENTES Y CUMPLIMIENTO LEGAL

SALTBOR se adhiere a una política estricta de **integridad de datos, legalidad y reproducibilidad científica**:

1. **Prohibición Total de Scraping Comercial**:
   No se utiliza scraping de Google Maps, Google Places, Waze ni ningún servicio cartográfico propietario cuyos términos de servicio o acuerdos de licencia de usuario final (EULA) prohíban la extracción, almacenamiento local o redistribución de datos espaciales.
2. **Uso de Fuentes Abiertas y Verificables**:
   Toda la cartografía vectorial (vías, edificios, paradas, hidrografía, límites distritales) proviene de fuentes de datos abiertos con licencias documentadas.
3. **Operación Offline Autónoma**:
   La plataforma opera de manera completamente autónoma sin depender de APIs de pago externas ni conectividad en vivo a servidores comerciales. Los datos se ingieren, normalizan y empaquetan localmente en `saltbor/datasets/gis/`.

---

## 2. FUENTES CARTOGRÁFICAS UTILIZADAS

### 2.1. OpenStreetMap (Fuente Principal)
- **Proveedor:** Fundación OpenStreetMap (OSMF) y colaboradores globales.
- **Formato de Origen:** Protocolbuffer Binary Format (OSM PBF) y Overpass API.
- **Licencia:** **Open Database License (ODbL) 1.0** (Open Data Commons).
- **Atribución Obligatoria:** *"© OpenStreetMap contributors"*. Esta atribución se incluye de forma permanente en todas las respuestas GeoJSON (`/api/geography/geojson`) y en el visor WebGL de MapLibre GL JS.
- **Capas Ingeridas:**
  - `roads`: Vías primarias, secundarias, terciarias, residenciales y senderos peatonales.
  - `buildings`: Huellas de edificios públicos, comerciales y residenciales.
  - `waterways`: Río Acelhuate, quebradas y canales urbanos.
  - `amenities`: Mercados, iglesias, clínicas, escuelas, parques y pupuserías.

### 2.2. Centro Nacional de Registros (CNR) de El Salvador (Fuente Complementaria Oficial)
- **Portal de Referencia:** [https://mapa.elsalvadormaps.sv/cnr/map/4](https://mapa.elsalvadormaps.sv/cnr/map/4)
- **Uso:** Referencia topográfica y toponímica para la validación de nombres de colonias, barrios, límites distritales oficiales conforme al Decreto Legislativo D.L. 762 de reestructuración municipal, y validación de coordenadas de monumentos históricos.
- **Condiciones:** Los datos del CNR se utilizan exclusivamente dentro de los términos de consulta pública oficial y delimitación catastral legal, sin vulnerar derechos de propiedad intelectual del Estado salvadoreño.

---

## 3. ESQUEMA DE METADATOS Y PROCEDENCIA DE CADA OBJETO

Cada entidad geográfica procesada por el pipeline de ingestión (`saltbor/datasets/gis/pipeline.py`) conserva un registro de procedencia inmutable:

```json
{
  "feature_id": "osm_way_12345678",
  "layer_system": "REAL_WORLD_LAYER",
  "source": "OpenStreetMap",
  "license": "ODbL 1.0",
  "ingested_at": "2026-11-13T18:00:00Z",
  "last_updated": "2026-11-13T18:00:00Z",
  "geometry_type": "LineString",
  "feature_class": "highway_residential",
  "name": "Calle Rubén Darío",
  "validation_state": "VERIFIED_REAL",
  "known_accuracy": "sub-meter"
}
```

---

## 4. INTEGRIDAD Y PARTICIÓN POR REGIONES

Para evitar sobrecargar la memoria RAM cargando innecesariamente la cartografía completa del país:
- La base de datos espacial utiliza un índice R-Tree espacial en SQLite (`saltbor/datasets/gis/spatial_index.db`).
- Las consultas se filtran estrictamente por la caja delimitadora (bounding box) de la zona activa (e.g. San Salvador Centro: `[-89.2100, 13.6900, -89.1800, 13.7100]`).
- Los datos de elevación y curvas de nivel se derivan de modelos digitales de elevación (DEM) de libre acceso (SRTM / Copernicus 30m).

---

## 5. CONCLUSIÓN

La plataforma SALTBOR garantiza que cada metro cuadrado de su territorio simulado cuenta con trazabilidad legal y cartográfica transparente, cumpliendo rigurosamente con los estándares éticos y legales internacionales en materia de datos geoespaciales.
