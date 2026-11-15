# AUDITORÍA DE INTEGRACIÓN — FASE 1.15
## SALTBOR: De Demostrador Aislado a Capacidad Territorial Generalizada

**Fecha de Ejecución**: Noviembre 2026  
**Sistema**: SALTBOR Multi-Scale Territorial Simulation  
**Objetivo**: Auditoría técnica exhaustiva de `ConnectedTerritorialScenariosDemonstrator` (Fase 1.14), componentes de simulación territorial, modelos causales, motores reales y consistencia contable antes de la implementación de la Fase 1.15.

---

### 1. Clasificación Arquitectónica de Componentes Existentes

#### 1.1 Motores Reales (Real Engines)
Los siguientes módulos implementan dinámica computacional real basada en ecuaciones, teoría de colas, grafos y balances contables:
1. **`CrossDomainInteractionEngine` (`saltbor/territory/cross_domain.py`)**: Implementa fórmulas analíticas de acoplamiento macro/meso:
   - Transporte $\rightarrow$ Comercio: Multiplicador de fricción vial, recargo logístico de flete ($c_{delivery} = d \times c_{km} \times \mu_{friction}$), contracción del tráfico de clientes (*footfall*).
   - Educación $\rightarrow$ Economía: Transmisión de pobreza de hogares a tasa de deserción escolar y oferta de mano de obra no calificada.
   - Salud $\rightarrow$ Economía del Hogar: Modelo de colas $M/M/c$ para tiempo de espera en clínicas, cálculo de salarios perdidos por enfermedad y días cama, gasto de bolsillo en fármacos.
   - Agricultura $\rightarrow$ Comercio de Alimentos: Transmisión de pérdidas de cosecha a precios mayoristas y minoristas de granos básicos (maíz, frijol).
2. **`MultiScaleTerritorialSimulationEngine` (`saltbor/territory/multi_scale.py`)**: Registra la jerarquía estricta de 6 niveles (Individuo, Hogar, Empresa/Institución, Comunidad, Municipio [44 D.L. 762], Departamento [14 IGN/CNR]). Permite agregación espacial (*roll-up*) y desagregación (*drill-down*).
3. **`RegionalEconomicNetworkEngine` (`saltbor/territory/regional_economics.py`)**: Red de nodos de suministro (productores, mayoristas, minoristas, consumidores), transmisión de precios por escalones (*echelon pricing*) y compraventas con conservación contable en balances de nodos comerciales.
4. **`PublicServiceCapacityEngine` (`saltbor/territory/public_services.py`)**: Monitoreo de demanda diaria vs capacidad instalada en escuelas, clínicas y puestos de agua; cálculo de factor de sobrecarga $\rho = \lambda / c\mu$ y tiempos de espera.
5. **`CollaborativeGovernanceEngine` (`saltbor/territory/governance.py`)**: Asambleas deliberativas, ponderación de votos (ADESCOs, autoridades municipales, sociedad civil), umbrales de aprobación y registro de auditoría (*governance audit trail*).
6. **`HumanNeedsAssessmentEngine` (`saltbor/territory/needs_assessment.py`)**: Matriz de Necesidades Fundamentales de Max-Neef (Subsistencia, Protección, Entendimiento, Participación, Identidad) con ponderación empírica territorial.
7. **`TerritorialProjectEngine` (`saltbor/territory/projects.py`)**: Diseñador de proyectos multisectoriales, presupuestos, fases de ejecución y mitigación de cuellos de botella.
8. **`UniversalDomainEngine` (`saltbor/domain/engine.py`)**: Orquestador central de dominios de actividad (agricultura, comercio, educación, salud, transporte, alimentos), conectado con la cartografía editable (`EditableWorldEngine`) y permisos de dominio.
9. **`CausalInferenceEngine` & `CausalEventTraceabilityEngine` (`saltbor/scientific/`)**: Modelos causales estructurales (SCM), intervenciones de Pearl $do(X=x)$, cálculo de ATE/CATE y grafo DAG retrospectivo de 9 niveles.

#### 1.2 Adaptadores (Adapters)
1. **`TerritorialEcosystemEngine` (`saltbor/territory/ecosystem.py`)**: Orquestador de alto nivel que sincroniza el avance por tick de los sub-motores territoriales y consolida métricas para el Observatorio Territorial.
2. **`saltbor/visualization/api.py`**: Adaptador REST (FastAPI) que expone los métodos internos hacia el cliente web mediante serialización JSON.

#### 1.3 Componentes Exclusivos de la Demostración (Demo-Only)
1. **`ConnectedTerritorialScenariosDemonstrator` (`saltbor/territory/connected_scenarios.py`)**: Clase rígida diseñada exclusivamente para reproducir una narrativa fija de 5 etapas con dos familias específicas (Familia Henríquez: José y Mateo; Familia Vásquez: Carmen, Rosa y Lucía).
2. **`scripts/demo_connected_scenarios.py`**: Script de terminal que invoca las 5 etapas secuenciales e imprime un reporte formateado en consola.
3. **`tests/test_territory/test_connected_scenarios.py`**: Pruebas unitarias que validan exclusivamente los valores numéricos fijos arrojados por el script demostrador.
4. **Endpoint `/territory/connected_scenarios/run` en `api.py`**: Invoca directamente el demostrador con semilla fija 42 sin permitir parámetros de entrada, cohortes alternativas ni intervenciones configurables.
5. **Función `runConnectedScenariosDemonstration` en `app.js`**: Renderiza tarjetas estáticas de las 5 etapas precalculadas.

---

### 2. Resultados Calculados Mediante Reglas Específicas (Ad-Hoc Scripting)

La auditoría de `connected_scenarios.py` evidencia que las etapas no son simulaciones dinámicas emergentes, sino asignaciones predefinidas:
1. **Inflación Minorista de Alimentos**: En `trigger_commercial_transport_shock()`, el precio minorista se calcula fijando arbitrariamente un margen del 32%:
   $$\text{inflated\_retail} = \text{round}(\text{inflated\_wholesale} \times 1.32, 2) = \$0.98/\text{lb}$$
2. **Agotamiento de Liquidez de José**:
   $$\text{cash} = \text{round}(\max(0.0, 48.00 - ((8.90 - 5.50) \times 5.0) - 8.00), 2) = \$8.50$$
   Esta fórmula resta \$8.00 de imprevisto y asume 5 días de gasto sin simular los 5 días de trabajo o transacciones diarias.
3. **Asistencia y Deserción Escolar de Mateo**:
   En `propagate_to_education()`, la asistencia escolar de Mateo se sobrescribe directamente:
   $$\text{mateo\_attendance\_pct} = 48.0\%$$
   $$\text{mateo\_is\_working\_informal} = \text{True}$$
   $$\text{mateo\_dropout\_risk} = \text{edu\_shock["dropout\_rate"]} \approx 0.44$$
   No hay evaluación cognitiva, ponderación del valor del estudio ni estrategia de resiliencia del hogar.
4. **Jornales Perdidos y Gastos Médicos de Bolsillo**:
   En `propagate_to_healthcare_and_feedback()`, se fijan valores directos:
   $$\text{jose\_lost\_days} = 4 \quad (\text{1 día en cola de clínica} + \text{3 días postrado})$$
   $$\text{out\_of\_pocket\_med\_usd} = \$25.00$$
   $$\text{informal\_fiado\_balance\_usd} = \$18.00$$
5. **Aparición Mágica de Dinero en la Recuperación (Fase 5)**:
   En `apply_integrated_territorial_solution()`:
   - El saldo de José pasa de \$0.00 a \$42.00 ("tras pagar los \$18 de fiado"), lo que implica que obtuvo \$60.00 de la nada.
   - La caja de la Tiendita salta de \$32.00 a \$215.00 (un incremento de \$183.00), de los cuales solo \$18.00 provienen del repago del fiado. Los restantes \$165.00 son dinero creado sin contrapartida.

---

### 3. Relaciones Causales Existentes vs Faltantes

#### 3.1 Relaciones Causales Existentes
- **Fricción Vial $\rightarrow$ Sobrecosto Logístico $\rightarrow$ Inflación Minorista**: Conectada en `cross_domain.py` mediante función explícita.
- **Sobrecarga de Clínica $\rightarrow$ Cola $M/M/c$ $\rightarrow$ Tiempos de Espera**: Implementada matemáticamente en `public_services.py` y `cross_domain.py`.
- **Precios de Insumos $\rightarrow$ Precios al Consumidor en Nodos**: Implementada en `regional_economics.py` (`compute_echelon_price_transmission`).

#### 3.2 Relaciones Causales Faltantes o Desconectadas
- **Microeconomía del Hogar $\rightarrow$ Decisiones Escolares**: Falta el mecanismo de toma de decisiones del hogar donde el trabajo informal de un menor sea una respuesta adaptativa de último recurso, no un resultado inevitable e impuesto.
- **Crédito Informal (*Fiado*) $\rightarrow$ Liquidez del Negocio**: En 1.14, el fiado debitó erróneamente el efectivo de la tienda en vez de transferir inventario y registrar una cuenta por cobrar.
- **Inversión Pública en Vía $\rightarrow$ Contratación Local de Mano de Obra**: La reparación vial en la etapa 5 ocurrió sin gasto fiscal, sin adjudicación de obra y sin pagar salarios a trabajadores locales.

---

### 4. Discrepancias Contables y Duplicación de Datos Detectadas

1. **Discrepancia en Liquidez Inicial de José**:
   - Inicialización en `_setup_shared_territory_and_cohort()`: `jose_worker.cash_usd = 45.00`, `hh_henriquez.shared_cash_usd = 45.00`.
   - Snapshot en `run_baseline()`: `jose_cash_balance_usd = 48.00`. (Discrepancia de \$3.00 sin justificación).
2. **Discrepancia en Caja Inicial de Carmen / Tiendita**:
   - Inicialización: `carmen_trader.cash_usd = 180.00`, `tiendita.cash_balance_usd = 180.00`.
   - Snapshot en `run_baseline()`: `tiendita_cash_usd = 195.00`. (Discrepancia de \$15.00 sin transacción).
3. **Tratamiento Contable Incorrecto del Fiado**:
   - Cuando Carmen fía \$18.00 de comida a José, el código ejecutó: `self.tiendita.cash_balance_usd -= 18.00`.
   - En contabilidad estricta:
     - El efectivo de Carmen no cambia ($\Delta \text{Caja} = \$0.00$).
     - El inventario físico de la tienda disminuye al costo ($\Delta \text{Inventario} = -\$13.50$).
     - Se registra una cuenta por cobrar (*Fiado Receivable*) por \$18.00.
     - José recibe \$18.00 en alimentos para la despensa familiar y registra una cuenta por pagar (*Fiado Payable*) por \$18.00.
4. **Ausencia de Libro Diario Verificable (*Ledger*)**:
   Las transacciones entre individuos, hogares y comercios no se registraban en una estructura inmutable de doble partida, imposibilitando la auditoría de conservación.

---

### 5. Determinismo vs Emergencia Individual

| Dimensión | Enfoque Fase 1.14 (Demostrador) | Enfoque Fase 1.15 (Sistemas Complejos) |
| :--- | :--- | :--- |
| **Población** | Exactamente 2 hogares fijos (Henríquez y Vásquez). | Muestreo dinámico de cohortes sintéticas en cualquier cantón, distrito o municipio de El Salvador. |
| **Trayectoria** | Secuencia lineal e invariable de 5 etapas. | Simulación basada en ticks, donde los acontecimientos interactúan con umbrales heterogéneos. |
| **Decisión de Deserción Escolar** | Mateo es obligado a desertar al subir el precio del maíz. | Modelo de decisión multi-factor: ahorros previos, severidad del shock, edad del menor, valor familiar de la educación, alternativas de apoyo comunitario (*cuchubal*, remesas, ayuda vecinal). |
| **Resiliencia de Negocio** | Tiendita quiebra/descapitaliza a \$32 por valores fijos. | Solvencia real en función de margen de venta, cobro de cartera fiada, rotación de inventario y gastos operativos. |
| **Recuperación** | Inyección instantánea de fondos no contabilizados. | Políticas territoriales con costo explícito, subsidios canalizados y transferencias registradas en libro contable. |

---

### 6. Mapa de Integración entre Demostración y Motores Reales

```
[ GeneralizedTerritorialScenarioEngine ]
       │
       ├──► [ VerifiableEconomicLedger ] ◄── (Asegura Conservación Doble Partida)
       │        ├── Transacciones Individuo <-> Hogar
       │        ├── Compras Hogar <-> Tiendita (Efectivo & Fiado)
       │        ├── Abastecimiento Tiendita <-> Mayorista
       │        └── Pago de Salarios / Vouchers / Obras Públicas
       │
       ├──► [ CausalTraceEngine ] ◄── (Grafo DAG Acíclico de Propagación)
       │        ├── Antecedente (Shock Vial, Infección, Sequía)
       │        ├── Mecanismo Intermedio (Fricción, Inflación, Tiempos de Espera)
       │        ├── Entidad Afectada & Magnitud Delta
       │        └── Clasificación Epistémica (Mecanismo Explícito vs Asociación vs Hipótesis)
       │
       ├──► [ SharedEntityConsistencyValidator ] ◄── (Sincronización Transaccional)
       │        ├── MultiScaleIndividualRecord (Billetera, Salud, Empleo, Educación)
       │        ├── MultiScaleHouseholdRecord (Despensa, Deudas, Presupuesto Compartido)
       │        ├── RegionalTradeNode (Caja, Inventario, Cuentas por Cobrar)
       │        └── PublicServiceFacility (Capacidad, Personal, Colas M/M/c)
       │
       ├──► [ HumanBehaviorHeterogeneityEngine ] ◄── (Decisiones Basadas en Contexto)
       │        ├── Jerarquía de Estrategias de Afrontamiento (Coping Strategies)
       │        ├── Factores Psicológicos y Rasgos de Personalidad (Big Five, Resiliencia)
       │        └── Emergencia de Deserción, Continuidad, Búsqueda de Crédito o Trabajo
       │
       └──► [ InterventionCounterfactualEngine ] ◄── (Comparativa de Políticas Públicas)
                ├── Caso Base (Sin shock)
                ├── Shock No Mitigado
                ├── Alternativa A: Reparación Vial Inmediata
                ├── Alternativa B: Transporte Escolar de Emergencia
                ├── Alternativa C: Transferencia Monetaria Focalizada
                └── Alternativa D: Paquete Territorial Integrado
```

---

### 7. Conclusión de la Auditoría

El demostrador de la Fase 1.14 cumplió con evidenciar la interdependencia conceptual entre transporte, comercio, educación y salud en una misma comunidad salvadoreña. Sin embargo, su implementación se basó en variables fijadas manualmente, ecuaciones ad-hoc y creación de dinero sin respaldo contable.

La **Fase 1.15** sustituye esta lógica ad-hoc por motores generalizados:
1. Definiciones declarativas de escenarios reutilizables (`GeneralizedTerritorialScenarioEngine`).
2. Trazabilidad causal completa (`CausalTraceEngine`) con diferenciación rigurosa de niveles epistémicos.
3. Libro contable verificable (`VerifiableEconomicLedger`) con estricta conservación contable de doble partida.
4. Validación transaccional de consistencia de entidades compartidas (`ConsistencyValidator`).
5. Heterogeneidad en respuestas individuales (`HumanBehaviorHeterogeneityEngine`).
6. Banco de experimentos reproducibles multi-hogar y multi-semilla (`EXP_115_A` a `EXP_115_T`).
7. Actualización del Observatorio Territorial y su interfaz web conectada a endpoints reales del backend.
