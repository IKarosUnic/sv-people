---
name: saltbor-data-engineering
description: SQLite WAL persistence, relational schemas, migrations, transactions, and historical data modeling.
---

# SKILL: Data Engineering, Persistence & Database Architecture

## 1. Objetivo
Garantizar la persistencia eficiente, robusta y libre de corrupción del estado de la simulación SALTBOR mediante SQLite3 configurado con Write-Ahead Logging (WAL), diseño de esquemas relacionales limpios, serialización en blobs JSON estructurados y migraciones transparentes.

## 2. Cuándo Utilizarla
- Al modificar tablas de base de datos o esquemas de persistencia en `saltbor/data/`.
- Al agregar nuevas entidades al checkpointing del runner (`_checkpoint_body()`).
- Al depurar bloqueos de base de datos (`database is locked`) o escrituras WAL infladas.
- Al diseñar consultas analíticas sobre el historial de eventos o grafos de relaciones.

## 3. Instrucciones de Trabajo
1. **Configuración Obligatoria de SQLite**:
   - Activar siempre modo WAL y modo seguro:
     ```sql
     PRAGMA journal_mode = WAL;
     PRAGMA synchronous = NORMAL;
     PRAGMA foreign_keys = ON;
     PRAGMA busy_timeout = 5000;
     ```
2. **Atomicidad Transaccional**:
   - Agrupar escrituras masivas dentro de una sola transacción `BEGIN TRANSACTION ... COMMIT`. Nunca ejecutar `INSERT` o `UPDATE` individuales dentro de bucles de miles de agentes.
3. **Persistencia Híbrida (Relacional + Documental)**:
   - Utilizar columnas relacionales indexadas para campos de búsqueda frecuente (`agent_id`, `tick`, `event_type`, `location_id`).
   - Utilizar columnas JSON para estados complejos en evolución (perfil cognitivo, inventario, estado psicológico, estatutos institucionales).
4. **Respaldo y Reanudación**:
   - La simulación debe poder restaurarse íntegramente desde una base de datos SQLite guardada (`load_existing=True`), restaurando relojes, agentes y organizaciones al tick exacto.

## 4. Procedimientos y Métodos
- **Estructura del Checkpoint V4**:
  ```python
  def _checkpoint_body(self) -> dict[str, Any]:
      return {
          "version": 4,
          "tick": self.clock.current_tick,
          "clock": self.clock.to_dict(),
          "civilization_phase19_society": {
              "organizations": [org.to_dict() for org in self.emergent_organizations.get_all_organizations()],
              "institutions": [inst.to_dict() for inst in self.institutional_evolution.get_all_institutions()],
              "cpr_resources": [r.to_dict() for r in self.cpr_manager.get_all_resources()],
              "social_norms": [n.to_dict() for n in self.social_norms.get_all_norms()],
          }
      }
  ```
- **Limpieza de Archivos Temporales**:
  - Al cerrar runners en benchmarks o tests, invocar `runner.db.close()` y desvincular tanto el archivo `.db` como el archivo `.db-wal`.

## 5. Referencias y Repositorios Clave
- Documentación oficial de SQLite (WAL Mode & Pragma Directives).
- Repositorio de referencia: `duckdb/duckdb` (para consultas analíticas OLAP masivas post-simulación).
- `saltbor/data/database.py`.

## 6. Herramientas Requeridas
- `sqlite3` (Python Standard Library).
- `json` (Serialization).

## 7. Criterios de Validación
- Pruebas de roundtrip superadas: guardar estado, cerrar base de datos, reabrir y verificar que el estado es idéntico (`test_persistence_sqlite_roundtrip`).
- Cero errores de `OperationalError: database is locked` en pruebas concurrentes.
- Tamaño de archivo WAL contenido (<5 MB tras 100 ticks).

## 8. Limitaciones
- No utilizar ORMs pesados (SQLAlchemy / Django ORM) en el bucle principal de la simulación; la sobrecarga de instanciación de objetos degrada severamente los ms/tick.
