---
name: saltbor-code-review
description: Static code analysis, dead code elimination, technical debt mitigation, and conservation law audit.
---

# SKILL: Code Review, Quality Assurance & Technical Debt Control

## 1. Objetivo
Evaluar y auditar la calidad, mantenibilidad, seguridad y rendimiento del código desarrollado para SALTBOR. Identificar regresiones potenciales, violaciones de leyes de conservación, código duplicado, variables no utilizadas y deuda técnica acumulada.

## 2. Cuándo Utilizarla
- Antes de dar por finalizada la implementación de un subsistema o fase.
- Al revisar contribuciones o refactorizaciones complejas.
- Cuando una prueba falle inesperadamente o se detecten incoherencias en las métricas.
- Periódicamente para eliminar código muerto (*dead code pruning*).

## 3. Instrucciones de Trabajo
1. **Auditoría de Leyes de Conservación**:
   - Comprobar que ninguna función aumente el saldo monetario de un agente sin debitar de otra cuenta o de una tesorería registrada.
   - Comprobar que las transferencias de inventario respeten la masa física.
2. **Eliminación de Código Muerto**:
   - Eliminar importaciones no utilizadas, variables huérfanas y funciones de depuración temporales.
3. **Manejo Defensivo de Atributos**:
   - Usar `getattr(obj, "field", default)` al interactuar con modelos de fases anteriores que puedan tener variantes de nombres (e.g. `human_a_id` vs `human_a_uid`).
4. **Verificación de Coherencia de Nombres y Estilo**:
   - Respetar PEP 8: nombres de clases en `PascalCase`, funciones y variables en `snake_case`, constantes en `UPPER_CASE`.
   - Mantener documentación de docstrings en funciones públicas principales.

## 4. Procedimientos y Métodos
- **Lista de Verificación de Revisión de Código**:
  1. ¿El código respeta las capas de arquitectura definidas en `AGENT_ECOSYSTEM.md`?
  2. ¿Existen operaciones $O(N^2)$ dentro de bucles frecuentes que deban optimizarse?
  3. ¿Se cierran adecuadamente todos los descriptores de archivos y conexiones de base de datos?
  4. ¿Se mantienen los enlaces a archivos con formato markdown clickable `[basename](file:///path/to/file)`?
  5. ¿Pasa la suite de tests completa sin regresiones?

## 5. Referencias y Repositorios Clave
- *Clean Code: A Handbook of Agile Software Craftsmanship* (Robert C. Martin).
- `AGENT_ECOSYSTEM.md`, `DEPENDENCY_DECISIONS.md`.

## 6. Herramientas Requeridas
- `pytest`
- Git diff / status para inspección de cambios.

## 7. Criterios de Validación
- `git status` muestra únicamente archivos necesarios y relevantes para la tarea.
- Cero advertencias críticas o errores no capturados en el log de ejecución.
- Toda la suite de pruebas del proyecto pasa limpiamente.

## 8. Limitaciones
- La revisión de código debe centrarse en la corrección, rendimiento y arquitectura; evitar debates estéticos triviales que no aporten valor al simulador.
