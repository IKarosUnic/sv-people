---
name: saltbor-research
description: Repository discovery, literature review, framework benchmarking, and documentation analysis.
---

# SKILL: Technical Research, Repository Discovery & Literature Review

## 1. Objetivo
Guiar la investigación rigurosa de repositorios de código abierto, bibliotecas especializadas, artículos científicos y documentación técnica antes de implementar subsistemas complejos en SALTBOR. Proporcionar un método sistemático para descubrir, comparar y evaluar alternativas existentes.

## 2. Cuándo Utilizarla
- Antes de iniciar el diseño de un nuevo subsistema en SALTBOR.
- Cuando se enfrente un desafío técnico complejo (e.g. algoritmos de enrutamiento topográfico, clustering de confianza social, modelos de formación de precios).
- Al actualizar el catálogo de repositorios (`EXTERNAL_REPOSITORY_CATALOG.md`).
- Al buscar implementaciones de referencia en simulación social y vida artificial.

## 3. Instrucciones de Trabajo
1. **Búsqueda Sistemática de Alternativas**:
   - Identificar de 2 a 4 repositorios o bibliotecas que aborden el problema en cuestión.
   - Consultar fuentes como GitHub, GitLab, PapersWithCode, arXiv y documentación oficial.
2. **Criterios de Priorización**:
   - Mantenimiento activo (commits en los últimos 6 meses, issues respondidas).
   - Documentación completa con ejemplos ejecutables.
   - Pruebas automatizadas con alta cobertura.
   - Licencia compatible identificable (MIT, Apache 2.0, BSD).
   - Compatibilidad con Python 3.12–3.14.
   - Posibilidad de ejecución 100% local sin servicios en la nube.
3. **No Dejarse Guiar Únicamente por Popularidad**:
   - Un repositorio con 50,000 estrellas puede ser un framework monolítico inadecuado para SALTBOR; mientras que una biblioteca pequeña y enfocada con 300 estrellas puede contener el algoritmo exacto necesario.
4. **Clasificación Explícita de la Decisión**:
   - Clasificar cada repositorio evaluado como `ADOPTAR`, `EVALUAR`, `REFERENCIA` o `DESCARTAR`.

## 4. Procedimientos y Métodos
- **Estructura de la Ficha Técnica de Repositorio**:
  - Nombre y URL.
  - Funcionalidad esencial.
  - Subsistema de SALTBOR beneficiado.
  - Licencia y compatibilidad.
  - Árbol de dependencias y consumo de memoria/CPU.
  - Ventajas y limitaciones.
  - Justificación de la decisión arquitectónica.

## 5. Referencias y Repositorios Clave
- `EXTERNAL_REPOSITORY_CATALOG.md`
- Awesome Agent-Based Modeling lists.
- PapersWithCode (Multi-Agent Systems).

## 6. Herramientas Requeridas
- Herramientas de búsqueda web / terminal (`search_web`, inspección de código).
- Python AST / inspect para analizar estructuras de paquetes externos.

## 7. Criterios de Validación
- Cada nuevo subsistema complejo cuenta con al menos un repositorio o paper de referencia analizado en la documentación técnica.
- Ficha técnica completa incorporada a `EXTERNAL_REPOSITORY_CATALOG.md`.

## 8. Limitaciones
- La investigación debe converger en una decisión concreta; evitar el análisis parálisis.
