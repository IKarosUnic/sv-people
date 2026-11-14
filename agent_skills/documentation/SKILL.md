---
name: saltbor-documentation
description: Technical report authoring, Mermaid architecture diagrams, KaTeX mathematical formulas, and ADR writing.
---

# SKILL: Technical Documentation, Mermaid Diagramming & Scientific Reporting

## 1. Objetivo
Elaborar documentación técnica, informes de auditoría, reportes de resultados experimentales y registros de decisiones arquitectónicas con el más alto rigor científico, claridad estructural, diagramas Mermaid legibles y fórmulas matemáticas en KaTeX.

## 2. Cuándo Utilizarla
- Al generar los reportes obligatorios de fin de fase (`*_AUDIT.md`, `*_REPORT.md`, `*_EXPERIMENT_RESULTS.md`).
- Al documentar nuevas decisiones de dependencia o cambios de arquitectura (ADRs).
- Al explicar flujos de trabajo, pipelines de eventos o ciclos de vida de entidades.
- Al responder a solicitudes complejas del usuario que requieran resúmenes estructurados.

## 3. Instrucciones de Trabajo
1. **Estructura Clara y Sin Repetición Innecesaria**:
   - Organizar los documentos con resúmenes ejecutivos, tablas maestras, diagramas explicativos y conclusiones cuantitativas.
   - No resumir redundante o extensamente artefactos en la respuesta directa si el usuario puede consultar el documento enlazado.
2. **Diagramas Mermaid Válidos**:
   - Utilizar únicamente tipos de diagramas soportados (`flowchart TD/LR`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `xychart-beta`).
   - Escapar etiquetas que contengan caracteres especiales (paréntesis, corchetes, comillas).
   - Evitar etiquetas HTML dentro de los nodos.
3. **Notación Matemática en KaTeX**:
   - Ecuaciones en bloque con `$$...$$` en su propia línea; fórmulas en línea con `$formula$`.
   - Escapar signos de dólar literales como `\$` en texto para evitar confusiones de renderizado.
4. **Enlaces a Archivos Clickables Obligatorios**:
   - Todo archivo referenciado debe presentarse como un enlace markdown con esquema `file:///` y barras inclinadas hacia adelante (forward slashes): `[basename](file:///absolute/path/to/file)`.

## 4. Procedimientos y Métodos
- **Plantilla Estándar para Reportes de Fase**:
  1. Título y Metadatos (Autor, Fecha, Entorno, Estado).
  2. Resumen Ejecutivo (*Executive Summary*).
  3. Matriz o Inventario de Componentes.
  4. Diagrama de Flujo / Secuencia de Integración.
  5. Tabla Cuantitativa de Métricas y Resultados.
  6. Evaluación de Causalidad y Límites.
  7. Certificación de Finalización.

## 5. Referencias y Repositorios Clave
- Guía oficial de GitHub Flavored Markdown (GFM).
- Especificación oficial de Mermaid.js.
- Documentación de KaTeX para expresiones matemáticas.

## 6. Herramientas Requeridas
- Formateadores Markdown y linters.
- Python standard library para generación automatizada de tablas de métricas.

## 7. Criterios de Validación
- Todos los diagramas Mermaid se renderizan sin errores de sintaxis.
- Todas las fórmulas matemáticas KaTeX compilan limpiamente.
- Todos los archivos referenciados tienen enlaces válidos `[basename](file:///...)`.

## 8. Limitaciones
- La documentación debe reflejar con estricta honestidad el código real implementado; prohibido documentar capacidades ficticias que no existan en el repositorio.
