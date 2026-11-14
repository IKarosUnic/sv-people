---
name: saltbor-testing
description: Automated testing, pytest methodologies, regression prevention, seed determinism, and property testing.
---

# SKILL: Automated Testing, Regression Prevention & Deterministic Validation

## 1. Objetivo
Diseñar, estructurar y ejecutar baterías de pruebas automatizadas exhaustivas para SALTBOR. Prevenir regresiones en fases previas, garantizar determinismo mediante control estricto de semillas pseudoaleatorias, y verificar el cumplimiento de contratos e invariantes.

## 2. Cuándo Utilizarla
- Al implementar cualquier cambio de código, nuevo motor o corrección de bugs.
- Al refactorizar componentes o actualizar esquemas de base de datos.
- Antes de cerrar un hito evolutivo o generar reportes de fase.
- Al investigar fallos intermitentes (*flaky tests*).

## 3. Instrucciones de Trabajo
1. **Ejecutar Pruebas Siempre con `python -m pytest`**:
   - En entornos Windows y entornos virtuales, invocar siempre `python -m pytest` para asegurar que se utiliza el intérprete correcto y sus dependencias.
2. **Determinismo y Semillas Fijas**:
   - Todo test que involucre estocasticidad debe configurar una semilla aleatoria explícita (`random_seed=42`).
   - El test no debe depender del orden de ejecución de la suite.
3. **Aislamiento de Persistencia**:
   - Utilizar bases de datos en memoria (`:memory:`) o archivos temporales creados con `tempfile.NamedTemporaryFile` que se limpian rigurosamente al finalizar (`unlink`).
4. **Pruebas Basadas en Propiedades (Property-Based Testing)**:
   - Para invariantes universales (e.g. conservación de masa monetaria, límites del Gini entre 0.0 y 1.0), utilizar o diseñar pruebas con entradas aleatorias acotadas inspiradas en `hypothesis`.

## 4. Procedimientos y Métodos
- **Estructura de la Suite de Pruebas**:
  - `tests/test_acceptance/`: Pruebas de aceptación de alto nivel por fase.
  - `tests/test_experiments/`: Baterías de experimentos reproducibles (`EXP_10_*` a `EXP_19_*`).
  - `tests/test_civilization/`: Dinámicas intergeneracionales, historia y territorio.
  - `tests/test_visualization/`: Endpoints REST y contratos de activos web.
  - `tests/test_world/`: Navegación, topografía, clima y eventos espaciales.
- **Patrón AAA (Arrange - Act - Assert)**:
  ```python
  def test_organization_dues_conservation():
      # Arrange
      runner = make_test_runner(seed=42)
      org = runner.emergent_organizations.register_organization(...)
      initial_total = get_total_monetary_mass(runner)
      
      # Act
      runner.emergent_organizations.collect_all_dues(runner.population, tick=96)
      
      # Assert
      final_total = get_total_monetary_mass(runner)
      assert abs(final_total - initial_total) < 1e-6, "Money created or leaked during dues collection!"
  ```

## 5. Referencias y Repositorios Clave
- Documentación oficial de Pytest (Fixtures, Parametrization, Hooks).
- Repositorio de referencia: `HypothesisWorks/hypothesis` (Property-based testing).
- `tests/test_experiments/test_phase19_experiments.py`.

## 6. Herramientas Requeridas
- `pytest`
- `httpx` (para pruebas de FastAPI TestClient)
- Python 3.12+

## 7. Criterios de Validación
- 100% de tests pasando (más de 619 tests verdes).
- Cero advertencias de aserciones omitidas.
- Tiempo de ejecución acotado (<90 segundos para la suite completa en hardware de referencia).

## 8. Limitaciones
- Evitar tests que dependan de timers reales (`time.sleep()`); usar siempre ticks simulados.
