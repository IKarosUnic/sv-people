---
name: saltbor-frontend
description: Lightweight vanilla HTML5/CSS3/ES6 dashboards, real-time KPI rendering, and FastAPI REST endpoints.
---

# SKILL: Lightweight Frontend Design, Interactive UI & REST APIs

## 1. Objetivo
Diseñar, implementar y mantener la interfaz de usuario web interactiva de SALTBOR: un panel de control rápido, responsivo y completamente fuera de línea que visualice el estado de los agentes, la geografía salvadoreña, los indicadores macroeconómicos y la dinámica institucional sin dependencias pesadas de Node.js o frameworks externos.

## 2. Cuándo Utilizarla
- Al crear nuevas pestañas, subpaneles o componentes visuales en la interfaz web de SALTBOR.
- Al añadir nuevos endpoints a la API REST de FastAPI (`saltbor/visualization/api.py`).
- Al diseñar tarjetas de KPI, barras de progreso, mapas o tablas interactivas.
- Al depurar problemas de sincronización en tiempo real entre el simulador y la UI.

## 3. Instrucciones de Trabajo
1. **Adherirse Estrictamente a Vanilla Web**:
   - Todo el frontend debe construirse exclusivamente con **HTML5 semántico, CSS3 moderno (Flexbox/Grid/Variables) y JavaScript ES6 estándar**.
   - Prohibido instalar Node.js, Webpack, Vite, React, Vue, Tailwind o dependencias en `node_modules`.
2. **Operación 100% Fuera de Línea**:
   - No cargar hojas de estilo ni fuentes desde CDNs externos (Google Fonts, cdnjs, unpkg).
   - Todos los activos (estilos, iconos SVG, scripts) deben servirse localmente desde `saltbor/visualization/web/`.
3. **Desacoplamiento Vía API REST**:
   - La interfaz consume datos a través de llamadas asíncronas `fetch('/api/...')` hacia los endpoints servidos por FastAPI.
   - Cada subsistema nuevo debe exponer su propio endpoint limpio documentado en Pydantic.
4. **Respuesta Rápida y Ligereza**:
   - El bundle completo de la UI no debe superar los 250 KB.
   - El renderizado de tablas y métricas debe ejecutarse en menos de 50 milisegundos tras recibir la respuesta JSON.

## 4. Procedimientos y Métodos
- **Patrón de Subpaneles y Subnavegación**:
  - Ubicar los botones de navegación secundaria dentro de la vista correspondiente (e.g. subnavegación de Civilización para la Fase 1.9).
  - Manejar el cambio de vista mediante clases CSS activas (`.active`, `display: none` / `display: block`).
- **Renderizado Dinámico en `app.js`**:
  ```javascript
  async function fetchPhase19Data() {
      try {
          const res = await fetch('/api/social/stratification/overview');
          const data = await res.json();
          document.getElementById('gini-income-val').textContent = data.gini_income.toFixed(3);
          document.getElementById('palma-val').textContent = data.palma_ratio.toFixed(2);
      } catch (err) {
          console.error("Failed to load Phase 1.9 data:", err);
      }
  }
  ```

## 5. Referencias y Repositorios Clave
- Documentación oficial de FastAPI (StaticFiles, APIRouter).
- MDN Web Docs (Vanilla JavaScript ES6, Fetch API, CSS Grid).
- `saltbor/visualization/api.py`, `saltbor/visualization/web/index.html`, `saltbor/visualization/web/app.js`.

## 6. Herramientas Requeridas
- `FastAPI`, `Uvicorn`
- Navegador web moderno (Chrome, Firefox, Edge)
- Pruebas con `tests/test_visualization/`

## 7. Criterios de Validación
- Pruebas en `tests/test_visualization/test_web_assets.py` pasan al 100%.
- Cero errores en la consola del navegador al navegar por todos los paneles.
- Cero peticiones de red salientes hacia internet.

## 8. Limitaciones
- La interfaz es una herramienta de inspección científica y depuración; no es un videojuego 3D intensivo en WebGL.
