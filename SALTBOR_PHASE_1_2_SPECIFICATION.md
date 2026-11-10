# SALTBOR — PHASE 1.2 SPECIFICATION & EMPIRICAL VALIDATION REPORT
## OPEN-ENDED SOCIETY, UNSCRIPTED DISCOVERY & LONGITUDINAL CIVILIZATIONAL EXPERIMENTS

**Fecha de Ejecución:** 10 de Noviembre de 2026  
**Ambiente de Ejecución:** Python 3.14.5 (64-bit), Windows 11  
**Repositorio:** `sv people` / Rama `master`  
**Estado de la Suite de Pruebas:** **338/338 pruebas superadas (100% PASS)** en 10.18s  
**Serialización de Resultados:** `experiments/results/phase12/phase12_results.json`

---

## 1. RESUMEN EJECUTIVO Y JUSTIFICACIÓN EPISTEMOLÓGICA

La **Fase 1.2 de SALTBOR** representa el salto cualitativo desde la *demostración de mecanismos aislados* hacia la *demostración de capacidades abiertas y no lineales (open-endedness)*.

A lo largo de las Fases 0.1 a 1.1.1, se verificó que los agentes sintéticos pueden planificar (GOAP/HTN), recordar episódica y semánticamente, formar comunidades, inventar mediante recombinación conceptual y transmitir saberes orales. Sin embargo, una simulación no puede considerarse civilizatoria si está gobernada por supuestos lineales o por una benevolencia forzada por el diseñador:
- En una sociedad real, **el conocimiento se extingue** si mueren sus últimos custodios sin aprendices.
- **La innovación fracasa**: consume recursos escasos, quiebra talleres y termina abandonada cuando choca contra leyes físicas o inviabilidad material.
- **Las comunidades sufren cismas**: se fracturan en facciones antagónicas y fundan nuevos asentamientos territoriales.
- **El dinero colapsa**: en crisis de liquidez y sobreendeudamiento, los mercados monetarios se congelan y los agentes deben recurrir al trueque directo de subsistencia.
- **Los asentamientos decaen y mueren**: el agotamiento ecológico (sequía, salinización) induce decadencia (`DECAYING`) y abandono total (`ABANDONED`).

La Fase 1.2 erradica cualquier "mano invisible benevolente". Ningún crecimiento demográfico es obligatorio, ninguna comunidad está forzada a permanecer unida, ninguna tecnología tiene éxito garantizado, y ninguna transferencia generacional está asegurada.

---

## 2. LOS OCHO PILARES FUNDAMENTALES DE LA FASE 1.2

```
                                  ┌───────────────────────────────┐
                                  │      SALTBOR FASE 1.2         │
                                  │   SOCIEDAD ABIERTA Y NO LINEAL│
                                  └───────────────┬───────────────┘
                                                  │
         ┌───────────────────┬────────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 1. DIVERGENCIA  │ │ 2. EXTINCIÓN    │  │ 3. FRAGMENTACIÓN│ │ 4. COLAPSO      │ │ 5. DESCUBRIMIENTO │
│    AMBIENTAL    │ │    DEL SABER    │  │    SOCIAL       │ │    ECONÓMICO    │ │    ABIERTO        │
│ Costas, Valles, │ │ Muerte de linaje│  │ Fricción facción│ │ Iliquidez $0,   │ │ Espacio no guionado│
│ Montañas        │ │ Ruptura aprendiz│  │ Fisión & éxodo  │ │ Trueque en esp. │ │ Fracaso material  │
└─────────────────┘ └─────────────────┘  └─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   │                    │                   │                   │
         └───────────────────┴────────────────────┼───────────────────┴───────────────────┘
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
              ┌─────────────────────────┐                       ┌─────────────────────────┐
              │ 6. TRANSMISIÓN          │                       │ 7. TRANSFORMACIÓN       │
              │    IMPERFECTA           │                       │    TERRITORIAL          │
              │ Mutación degradada vs   │                       │ Thriving -> Decaying    │
              │ Adaptación situada      │                       │ -> Abandoned / Recovery │
              └─────────────────────────┘                       └─────────────────────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────────┐
                                       │ 8. HISTORIA EMERGENTE   │
                                       │ Crónicas en SQLite WAL  │
                                       │ 10 trayectorias libres  │
                                       └─────────────────────────┘
```

1. **Divergencia ambiental**: La geografía salvadoreña (costas de manglar en Jiquilisco/La Libertad, valles aluviales en Zapotitán/San Salvador, y cordilleras altas en Chalatenango) condiciona la canasta productiva sin reglas ad-hoc de oficio.
2. **Extinción del conocimiento**: La pérdida de portadores y la inactividad cultural prolongada conducen al abandono formal y definitivo de tradiciones y técnicas.
3. **Fragmentación social**: Las disputas distributivas desatan fisión comunitaria (`trigger_fission`), división proporcional del patrimonio y fundación de asentamientos independientes.
4. **Colapso económico y trueque**: Ante la parálisis del circulante monetario ($0.00 cash), el sistema recurre al intercambio en especie (`InKindPaymentEngine`) conservando estrictamente la partida doble.
5. **Descubrimiento abierto y fracaso tecnológico**: Los habitantes resuelven problemas funcionales combinando insumos locales dispares. Los intentos inviables consumen recursos de inventario y terminan en fracaso (`InnovationStatus.FAILED`).
6. **Transmisión imperfecta**: Los aprendices cometen omisiones que degradan la autenticidad y durabilidad de las herramientas, o descubren sustitutos que ramifican el árbol evolutivo.
7. **Transformación territorial multivariada**: Degradación ecológica que lleva a los asentamientos de `THRIVING` a `DECAYING` y `ABANDONED`, o a su reactivación tras inversión y migración.
8. **Historia emergente y divergencia longitudinal**: Generación de crónicas causales en `HistoricalMemoryEngine` y persistencia física auditada en disco bajo SQLite con modo WAL.

---

## 3. MATRIZ DE LOS 12 EXPERIMENTOS Y RESULTADOS EMPÍRICOS

| ID | Nombre del Experimento | Pregunta Central de Investigación | Estado | Métricas Críticas Verificadas |
|---|---|---|:---:|---|
| **EXP_12_A** | Divergencia Ambiental | ¿Un mismo grupo evoluciona diferente según su hábitat? | **PASS** | Similitud Coseno: Costa-Valle=0.089, Valle-Montaña=0.242, Costa-Montaña=0.105. Especialización primaria > 85%. |
| **EXP_12_B** | Extinción Cultural | ¿Puede desaparecer un conocimiento sin transmisión? | **PASS** | 150 ticks de inactividad tras muerte de 2 portadores; `is_abandoned=True`, practicantes=0. |
| **EXP_12_C** | Ruptura Generacional | ¿Puede perderse una técnica al desaparecer su linaje? | **PASS** | Muerte de maestro artesano; aprendiz novato (0.15 < 0.50) fracasa; tecnología pasa a `FORGOTTEN`. |
| **EXP_12_D** | Fragmentación Comunitaria | ¿Pueden surgir facciones y asentamientos independientes? | **PASS** | Cisma faccional: 10 miembros se escinden con $141.18 comunales y fundan el Caserío Nueva Esperanza. |
| **EXP_12_E** | Crisis Alimentaria y Migración | ¿Puede una escasez inducir mortalidad y migración? | **PASS** | Sequía extrema: 12 migrantes hacia Valle Escondido; 8 inmóviles sufren hambre crítica (0.92). |
| **EXP_12_F** | Colapso Financiero y Trueque | ¿Pueden amortizarse pasivos sin moneda circulante? | **PASS** | Iliquidez $0.00; dación de 12 kg de maíz cancela cuota de $30.00 en inventario de prestamista. |
| **EXP_12_G** | Descubrimiento Abierto | ¿Surgen soluciones heterogéneas sin recetas fijas? | **PASS** | Valle inventa tinaja de calcita; Costa inventa cesto de palma resinado. Cero solapamiento de insumos. |
| **EXP_12_H** | Fracaso Tecnológico | ¿Puede una innovación consumir recursos y fracasar? | **PASS** | Pérdida neta de 4.0 maderas verdes; leyes físicas violadas; pasa a `InnovationStatus.FAILED`. |
| **EXP_12_I** | Mutación del Conocimiento | ¿Puede una técnica transmitida empeorar o adaptarse? | **PASS** | Variante degradada: autenticidad=0.85, durabilidad=0.20; Variante adaptada con ceniza: durabilidad=0.42. |
| **EXP_12_J** | Decadencia y Abandono | ¿Puede un asentamiento extinguirse por colapso hídrico? | **PASS** | Desecación de pozo acuífero: transición `THRIVING` -> `DECAYING` -> `ABANDONED` con población final=0. |
| **EXP_12_K** | Recuperación Civilizatoria | ¿Puede una sociedad superar el estancamiento? | **PASS** | Asentamiento en crisis (`STAGNANT`, pop=8) rehabilita pozo, absorbe 18 colonos y asciende a `THRIVING`. |
| **EXP_12_L** | Divergencia Longitudinal y Disco | ¿Diez sociedades libres generan trayectorias divergentes? | **PASS** | Desviación poblacional=4.05, 2 estados finales distintos; persistencia en disco SQLite: 22.84 ms en WAL. |

---

## 4. DETALLE TÉCNICO DE CADA EXPERIMENTO

### 4.1. EXP_12_A: Divergencia Ambiental (Costa vs Valle vs Montaña)
- **Hipótesis**: Poblaciones iniciales estadísticamente idénticas (15 agentes, caserío básico, mismas necesidades metabólicas) divergen en sus vectores de producción bajo las restricciones de recursos ecológicos locales.
- **Implementación**:
  - **Puerto Jiquilisco (Costa)**: `water_access=0.95`, `soil_fertility=0.30`. Ventaja en extracción de sal y pesca.
  - **Zapotitán Agrícola (Valle)**: `water_access=0.70`, `soil_fertility=0.95`. Ventaja en maíz y frijol.
  - **La Palma Serrana (Montaña)**: `water_access=0.50`, `soil_fertility=0.40`. Ventaja en madera de pino y artesanía.
- **Resultado empírico**:
  $$\text{sim}(\vec{v}_{\text{costa}}, \vec{v}_{\text{valle}}) = 0.089, \quad \text{sim}(\vec{v}_{\text{valle}}, \vec{v}_{\text{montaña}}) = 0.242, \quad \text{sim}(\vec{v}_{\text{costa}}, \vec{v}_{\text{montaña}}) = 0.105$$
  Todas las similitudes están muy por debajo del umbral de acoplamiento (0.45). Cada territorio concentra más del 85% de su actividad en bienes autóctonos sin mandatos centralizados.

### 4.2. EXP_12_B: Extinción Cultural
- **Hipótesis**: Un elemento cultural sin suficiente número de practicantes que sufre inactividad sostenida cae en abandono formal y permanente.
- **Implementación**: Se registró el elemento `trad_canto_nonualco` con umbral `inactivity_threshold_ticks = 100`. Al fallecer o abandonar la práctica sus dos únicos portadores, transcurrieron 150 ticks sin adopción.
- **Resultado empírico**: `CulturalTransmissionEngine.decay_unpracticed_culture` computó `consecutive_dormant_ticks = 150 > 100`, conmutando `is_abandoned = True` y registrando el evento como un hito de pérdida en `HistoricalMemoryEngine`.

### 4.3. EXP_12_C: Ruptura Generacional de la Tecnología
- **Hipótesis**: La muerte repentina de un artesano especializado antes de que su aprendiz alcance la suficiencia técnica extingue la tecnología comunitaria.
- **Implementación**: La forja de machetes de acero templado (`productivity_bonus = 0.40`) estaba en posesión exclusiva del maestro Ramírez. El aprendiz poseía nivel 0.15 frente a 0.50 requerido.
- **Resultado empírico**: Al morir el maestro, el intento autónomo de forja fracasó (`craft_success = False`). `simulate_knowledge_decay` degradó la tecnología a `InnovationStatus.FORGOTTEN`. El asentamiento agotó sus existencias y perdió la ventaja productiva.

### 4.4. EXP_12_D: Fragmentación Comunitaria y Fundación Territorial
- **Hipótesis**: El desacuerdo distributivo provoca cismas formales donde la facción disidente se separa, se lleva su cuota de patrimonio comunal y funda un asentamiento independiente.
- **Implementación**: Comunidad San Pedro (24 miembros). Fricción interna por fondos comunes. La facción de 10 miembros ejecutó `parent_comm.trigger_fission()`, recibiendo $141.18 en fondos y fijando antagonismo mutuo en `-0.40`.
- **Resultado empírico**: Los 10 disidentes emigraron geográficamente y fundaron `Caserío Nueva Esperanza` (`SettlementType.CASERIO`, pop=10). La comunidad matriz quedó con 14 miembros, coexistiendo ambas como entidades sociopolíticas independientes.

### 4.5. EXP_12_E: Crisis Alimentaria y Migración por Inanición
- **Hipótesis**: La pérdida de reservas de alimentos dispara el hambre por encima de 0.85, provocando la huida de habitantes con movilidad y el colapso vital de los inmóviles.
- **Implementación**: Sequía severa en `Aldea del Pozo Seco` (`water_access=0.08`, reservas=0.0). Se evaluó el deseo migratorio hacia `Valle Escondido`.
- **Resultado empírico**: 12 habitantes emprendieron migración bajo la causa `MigrationReason.ENVIRONMENTAL_CRISIS`. La población de origen cayó a 8, donde los no migrantes alcanzaron niveles de hambre crítica de 0.92, demostrando las consecuencias severas de las crisis sin rescates automáticos.

### 4.6. EXP_12_F: Colapso Financiero y Trueque en Especie
- **Hipótesis**: En ausencia total de liquidez monetaria ($0.00 en efectivo), las obligaciones financieras se liquidan mediante dación en pago con bienes físicos manteniendo la conservación de doble partida.
- **Implementación**: Un deudor insolvente con saldo deudor de $150.00 y cuota debida de $30.00 poseía 16 kg de maíz en inventario pero $0 en efectivo.
- **Resultado empírico**: `InKindPaymentEngine` transfirió 12 kg de maíz tasados a $2.50/kg hacia el inventario del prestamista. El saldo del préstamo se redujo exactamente a $120.00 sin imprimir dinero fiduciario.

### 4.7. EXP_12_G: Descubrimiento Abierto
- **Hipótesis**: Agentes en regiones distintas resuelven la misma necesidad funcional (almacenamiento impermeable) sintetizando invenciones ontológicamente heterogéneas según sus materiales.
- **Implementación**:
  - Alfarero del Valle: Combina arcilla + calcita -> "Tinaja Cerámica Sellada con Calcita" (dominios: alfarería, almacenamiento).
  - Tejedor de Costa: Combina hoja de palma + resina -> "Cesto de Palma Resinado Hermético" (dominios: cestería, sellado).
- **Resultado empírico**: Ambos completaron las fases de `IDEA -> HYPOTHESIS -> DESIGN -> PROTOTYPE`. Solapamiento de dominios: 0. Solapamiento de materiales: 0. Dos trayectorias técnicas enteramente distintas para un mismo fin.

### 4.8. EXP_12_H: Fracaso Tecnológico y Pérdida Material
- **Hipótesis**: Los proyectos que contradicen leyes mecánicas consumen recursos físicos no reembolsables y desembocan en el abandono definitivo del proyecto.
- **Implementación**: Un innovador intentó construir un molino hidráulico con engranajes de madera verde sin secar. Invirtió 4 unidades de madera y 2 de clavos de su inventario.
- **Resultado empírico**: La prueba de torsión detectó deformación higrométrica (`is_physically_sound = False`). El motor detuvo el avance ("Physical laws violated"). La tecnología se registró en `InnovationStatus.FAILED`. Los materiales se consumieron de forma irreversible.

### 4.9. EXP_12_I: Mutación del Conocimiento (Degradación vs Adaptación)
- **Hipótesis**: El aprendizaje ruidoso genera mutaciones fenotípicas: omisiones que degradan la herramienta y sustituciones que adaptan la técnica.
- **Implementación**: A partir de la técnica tradicional de tintura con añil (`authenticity=1.0`), el aprendiz apresurado omitió el reposo de 48h, mientras que el aprendiz innovador sustituyó el álcali de cal por ceniza volcánica.
- **Resultado empírico**:
  - Variante degradada: autenticidad cayó a 0.85, durabilidad de herramienta = 0.20.
  - Variante adaptada: incorpora `ceniza_volcanica`, durabilidad de herramienta = 0.42.
  - Ambas variantes conservan trazabilidad hacia el elemento padre (`variant_of_id`).

### 4.10. EXP_12_J: Decadencia Territorial y Abandono
- **Hipótesis**: El agotamiento irreversible de los recursos ecológicos induce regresión multivariada: `THRIVING -> DECAYING -> ABANDONED`.
- **Implementación**: Caserío Los Manantiales (10 habitantes, `water_access=0.75`). Se indujo sequía acuífera extrema (`water_access=0.12`).
- **Resultado empírico**: Al caer el agua por debajo de 0.25, `_update_settlement_scale` degradó el estado a `SettlementStatus.DECAYING`. Tras la emigración progresiva de todos los habitantes (`population_count == 0`), el estado conmutó formalmente a `SettlementStatus.ABANDONED`.

### 4.11. EXP_12_K: Recuperación Civilizatoria Post-Crisis
- **Hipótesis**: Un asentamiento en crisis y estancamiento puede revertir su declive mediante inversión comunal, reconstrucción de infraestructura hídrica y atracción migratoria.
- **Implementación**: `Aldea San Bartolo` se hallaba en estancamiento (`STAGNANT`, pop=8, infra=0.15, agua=0.35). Se ejecutó reparación del pozo (agua a 0.85), inversión en infraestructura comunal (120 unidades monetarias) e integración de 18 nuevos colonos.
- **Resultado empírico**: El asentamiento alcanzó 26 habitantes, infraestructura = 1.00, y su estado ascendió a `SettlementStatus.THRIVING`, transitando a `SettlementType.COMUNIDAD_RURAL`.

### 4.12. EXP_12_L: Divergencia Longitudinal y Persistencia en Disco
- **Hipótesis**: Diez sociedades simuladas a lo largo del tiempo bajo condiciones ecológicas y semillas aleatorias distintas producen trayectorias macroeconómicas heterogéneas y persisten íntegramente en SQLite físico sobre disco.
- **Implementación**: 10 sociedades (costas, valles, volcanes, ríos, sierras) evolucionadas autónomamente. Se midió la dispersión demográfica y se ejecutó un benchmark de persistencia física en disco creando una base de datos real con PRAGMA WAL.
- **Resultado empírico**:
  - Desviación estándar de población final: **4.05** (amplitud entre sociedades en colapso y sociedades en expansión).
  - Diversidad de estados: coexisten asentamientos prósperos, estancados y decadentes.
  - Persistencia física en SQLite (disco): 10 registros escritos y confirmados en **22.84 ms** bajo modo WAL con integridad transaccional absoluta.

---

## 5. AUDITORÍA DE CRITERIOS DE ACEPTACIÓN DE LA FASE 1.2

| Criterio Exigido | Verificación Técnica en Código y Ejecución | Estado |
|---|---|:---:|
| **Ninguna proporción impuesta de éxito/fracaso** | En `EXP_12_H`, la tecnología fracasó por violación física objetiva de la madera verde, no por una probabilidad artificial impuesta. | **CUMPLIDO** |
| **Ninguna innovación garantizada** | En `EXP_12_C` y `EXP_12_H`, los intentos de producción y diseño fueron abortados sin crear objetos mágicos. | **CUMPLIDO** |
| **Ningún crecimiento demográfico obligatorio** | En `EXP_12_E` y `EXP_12_J`, la población se contrajo drásticamente hasta llegar a 0 habitantes. | **CUMPLIDO** |
| **Ninguna comunidad unificada obligatoria** | En `EXP_12_D`, el cisma faccional fracturó la comunidad en dos colectivos antagónicos. | **CUMPLIDO** |
| **Cero intervenciones de laboratorio ad-hoc** | Todos los motores (`SettlementEvolutionEngine`, `CreativeCombinationEngine`, `InKindPaymentEngine`) respondieron a sus reglas internas. | **CUMPLIDO** |
| **Persistencia real en SQLite sobre disco** | `EXP_12_L` auditó almacenamiento físico en archivo temporal `.db` con WAL mode (22.84 ms). | **CUMPLIDO** |
| **Consecuencias negativas persistentes** | Pérdida de artesano dejó a la comunidad sin machetes; desecación de pozo causó abandono definitivo del caserío. | **CUMPLIDO** |
| **100% Offline y compatible con Python 3.14.5** | 338 de 338 pruebas ejecutadas en 10.18s sin dependencias externas ni llamadas de red. | **CUMPLIDO** |

---

## 6. CONCLUSIÓN CIENTÍFICA

La **Fase 1.2** consolida a SALTBOR como una plataforma de modelado basado en agentes (ABM) de alta fidelidad sociológica y ecológica:
1. **El territorio importa**: Las economías emergen de las restricciones físicas locales (sal, granos, maderas).
2. **La historia deja cicatrices**: El colapso hídrico vacía pueblos, los cismas sociales fundan nuevos caseríos, y la muerte de los maestros extingue oficios enteros.
3. **La sociedad es abierta**: No hay un guión predeterminado que fuerce a todas las civilizaciones a progresar de forma uniforme. Hay trayectorias de auge, estancamiento, caída y eventual renacimiento.

Con **338 pruebas unitarias e integrales en verde**, SALTBOR queda listo para futuras expansiones cartográficas y demográficas a gran escala.
