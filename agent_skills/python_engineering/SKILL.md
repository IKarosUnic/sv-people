---
name: saltbor-python-engineering
description: Python 3.14 idioms, Pydantic v2 schemas, strict type annotations, and memory-efficient data structures.
---

# SKILL: Modern Python Engineering, Type Safety & Performance Idioms

## 1. Objetivo
Aplicar las mejores prácticas de ingeniería de software en Python 3.12–3.14 para SALTBOR: tipado estricto con `typing`, validación declarativa con Pydantic v2, diseño de dataclasses eficientes, gestión limpia de recursos con context managers y código idiomático mantenible.

## 2. Cuándo Utilizarla
- Al escribir nuevas clases, funciones o modelos de datos en `saltbor/`.
- Al refactorizar código heredado hacia esquemas Pydantic v2.
- Al definir contratos de datos para la API REST o la persistencia SQLite.
- Al depurar errores de tipos (`TypeError`, `AttributeError`) o problemas de serialización JSON.

## 3. Instrucciones de Trabajo
1. **Tipado Estricto Obligatorio**:
   - Todo módulo debe incluir `from __future__ import annotations`.
   - Todas las funciones y métodos públicos deben declarar anotaciones de tipo completas en parámetros y valor de retorno (`-> ReturnType`).
2. **Pydantic v2 para Validación de Dominio**:
   - Utilizar `pydantic.BaseModel` con `Field(...)` para entidades con validación compleja, límites numéricos (`ge=0.0, le=1.0`) o deserialización JSON.
   - En modelos de datos puramente internos de rendimiento crítico que se instancian decenas de miles de veces por tick, preferir dataclasses estándar (`@dataclass`) para evitar sobrecarga de validación repetitiva.
3. **Gestión de Recursos con `with`**:
   - Toda conexión a base de datos, archivo temporal o lock concurrente debe administrarse con context managers (`with`) para garantizar el cierre seguro de descriptores incluso ante excepciones.
4. **Inmutabilidad y Copias Defensivas**:
   - Utilizar listas o tuplas inmutables cuando los datos deban protegerse de mutaciones accidentales entre subsistemas.

## 4. Procedimientos y Métodos
- **Patrón de Modelo de Dominio en SALTBOR**:
  ```python
  from __future__ import annotations
  from typing import Any, Optional
  from pydantic import BaseModel, Field
  from saltbor.core.types import Tick, HumanID

  class DomainRecord(BaseModel):
      record_id: str
      created_tick: Tick
      initiator_id: HumanID
      intensity: float = Field(default=0.5, ge=0.0, le=1.0)
      metadata: dict[str, Any] = Field(default_factory=dict)
  ```
- **Uso de Enums Fuertemente Tipados**:
  - Toda categoría finita (dominios institucionales, estados de salud CPR, roles) debe expresarse como `str, enum.Enum` para facilitar la serialización JSON directa.

## 5. Referencias y Repositorios Clave
- Documentación oficial de Python 3.14 (`typing`, `dataclasses`).
- Documentación oficial de Pydantic v2.
- PEP 563 (Postponed Evaluation of Annotations) & PEP 604 (Union types `A | B`).

## 6. Herramientas Requeridas
- Python 3.12+ (CPython 3.14.5 en entorno activo).
- `pydantic>=2.0`

## 7. Criterios de Validación
- Validación sintáctica y de importación sin advertencias.
- Serialización y deserialización JSON bidireccional exitosa (`model.model_dump()` / `model.model_validate()`).
- Cobertura de tipos verificable sin violaciones estáticas obvias.

## 8. Limitaciones
- Evitar metaprogramación oscura o decoradores anidados complejos que dificulten la depuración y el perfilado.
