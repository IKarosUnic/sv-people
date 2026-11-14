# SKILL: Cartographic & Telemetry Visualization
`agent_skills/visualization/SKILL.md`

## 1. Purpose & Domain Scope
Guides the architecture and rendering of interactive cartography, population heatmaps, media diffusion flows, and real-time simulation dashboards using modern web standards (MapLibre, WebGL, Canvas, FastAPI SSE).

## 2. When to Use
- Implementing or enhancing browser visualization of real Salvadoran geography.
- Visualizing agent movements, road congestion, and broadcast coverage areas.
- Designing charts for economic Gini, sentiment, and transmission trees.

## 3. Workflows & Procedures
1. **Spatial Aggregation**: Avoid rendering individual DOM elements for $N > 1000$; cluster points using grid bins or WebGL point clouds.
2. **Offline Tile Serving**: Serve offline Vector/GeoJSON layers through local FastAPI static endpoints (`/static/tiles`).
3. **Reactive State Sync**: Push simulation tick diffs over WebSockets or Server-Sent Events (SSE) with decoupled frontend frame rates.

## 4. Technical References
- MapLibre GL JS Documentation & GeoJSON Specifications (RFC 7946).
- deck.gl Spatial Data Visualisation Layering.

## 5. Validation Criteria
- Offline accessibility: Zero reliance on Google Maps or Mapbox proprietary tokens.
- Fluid 60 FPS rendering on modern browsers for 5,000+ visible agents.
