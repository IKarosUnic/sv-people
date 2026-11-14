# SALTBOR FASE 1.8: INFORME DE CAUSALIDAD Y TRAZABILIDAD DE EVENTOS
## Grafo Causal Acíclico Dirigido (DAG), Propagación Ecosistémica y Explicabilidad

**Fecha:** 13 de Noviembre de 2026  
**Subsistema:** `CausalEventGraph` (`saltbor/events/causal_graph.py`)  
**Integración:** `IntegratedWorldSimulationEngine` y `SimulationRunner`  

---

## 1. ARQUITECTURA DEL GRAFO CAUSAL

En la Fase 1.8 se consolidó la conexión entre el motor de eventos de la simulación y el **Grafo Causal Acíclico Dirigido (`CausalEventGraph`)**. Anteriormente, los eventos emitidos por el `EventBus` se archivaban como registros cronológicos planos en memoria o SQLite, lo que respondía a la pregunta *"¿Cuándo ocurrió X?"*, pero impedía responder con rigor científico a las preguntas fundamentales:
- *"¿Por qué ocurrió este evento?"* (Trazabilidad retrospectiva de causas raíz).
- *"¿Qué consecuencias desencadenó este acontecimiento?"* (Trazabilidad prospectiva de impacto).

### Estructura del Nodo Causal (`CausalNode`)
Cada evento registrado en el sistema se convierte en un nodo inmutable:
- `event_id`: Identificador UUID único.
- `event_type`: Tipo tipado de evento (e.g. `ROAD_BLOCKED`, `FAENA_COMPLETED`, `COMMERCE_TRANSACTION`).
- `tick`: Momento temporal exacto.
- `description`: Resumen narrativo y técnico.
- `location_id` / `coordinates`: Anclaje espacial preciso en El Salvador.
- `affected_uids`: Individuos sintéticos impactados directamente.
- `cause_event_ids`: Lista de enlaces a nodos ancestros causales.
- `consequence_event_ids`: Lista de enlaces a nodos descendientes provocados por este evento.
- `importance`: Peso escalar entre 0.0 y 1.0.

---

## 2. PREVENCIÓN DE BUCLES Y CONTROL DE CASCADAS

Para evitar que una retroalimentación sistémica (e.g. caída de ingresos $\rightarrow$ desnutrición $\rightarrow$ enfermedad $\rightarrow$ pérdida de empleo $\rightarrow$ caída de ingresos) genere bucles cerrados que destruyan la propiedad acíclica del grafo o provoquen desbordamiento de pila por recursión infinita:

1. **Detección Previa de Ciclos (`_would_create_cycle`)**:
   Antes de aceptar un enlace causal $A \rightarrow B$, el motor ejecuta un recorrido DFS en profundidad desde el nodo $B$. Si el nodo $A$ es alcanzable desde $B$, el enlace causal se rechaza y se emite una advertencia en el log.
2. **Monotonía Temporal**:
   Un evento del tick $T_2$ no puede figurar como causa directa de un evento ocurrido en $T_1$ si $T_1 < T_2$.
3. **Poda y Capacidad Acotada (`max_nodes = 10,000`)**:
   El grafo causal mantiene en memoria una ventana deslizante de 10.000 eventos prioritarios, descartando en orden FIFO los eventos cotidianos de baja importancia ($<0.30$) al superar el umbral.

---

## 3. PROPAGACIÓN MULTIDOMINIO: CADENA CAUSAL VERIFICADA

Durante la ejecución integrada de la Fase 1.8, se comprobó experimentalmente la propagación de consecuencias a través de los cinco dominios de la simulación:

```
[DOMINIO AMBIENTAL]
Tormenta tropical: Precipitación > 20 mm/h en la cuenca del Río Acelhuate
       │
       ▼
[DOMINIO DE INFRAESTRUCTURA & TRANSPORTE]
Crecida de Quebrada El Zapote anega Calle Rubén Darío (ROAD_BLOCKED)
El agente en tránsito a pie detecta el bloqueo y queda detenido (JOURNEY_BLOCKED)
       │
       ▼
[DOMINIO LABORAL & ECONÓMICO]
Llegada tardía al taller artesanal (WORK_DELAYED)
Pérdida de salario diario y disminución del saldo disponible en billetera
       │
       ▼
[DOMINIO FAMILIAR & BIOLÓGICO]
Contracción del presupuesto familiar en el hogar
Ajuste de consumo alimentario a canasta básica
       │
       ▼
[DOMINIO SOCIAL & COMUNITARIO]
Convocatoria de la directiva comunal ADESCO (COMMUNITY_PROJECT_PROPOSED)
Vecinos realizan faena colectiva de limpieza y remoción de escombros (FAENA_COMPLETED)
       │
       ▼
[DOMINIO HISTÓRICO COLECTIVO]
Consolidación del acontecimiento en SalvadoranHistoricalMemoryEngine
Preservación como hito de resiliencia comunitaria en la historia del pueblo
```

---

## 4. CONSULTA Y EXPLICABILIDAD VÍA API REST

Los siguientes endpoints permiten a los investigadores y usuarios examinar la causalidad en tiempo real:

- **`GET /api/world/causality/{event_id}`**:
  Retorna la ficha del evento, la cadena cronológica de causas ancestras (`ancestor_causes`), el árbol de efectos desencadenados (`descendant_consequences`) y la explicación estructurada (`explanation`).
- **Función `explain_event(event_id)`**:
  Genera una síntesis comprensible que describe la génesis del evento (quién, dónde, qué causa inmediata lo activó y cuáles han sido sus repercusiones en la comunidad).

---

## 5. CONCLUSIÓN

El `CausalEventGraph` convierte a SALTBOR en una plataforma completamente **explicable y auditable**. Las acciones no surgen de "cajas negras" opacas ni de distribuciones aleatorias desvinculadas: cada decisión, cada compra rechazada, cada cambio de ruta y cada hito comunitario posee un linaje causal verificable, fundamentando científicamente los estudios de vida artificial y dinámica social.
