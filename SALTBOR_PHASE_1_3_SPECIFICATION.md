# SALTBOR — PHASE 1.3 SPECIFICATION
## OPEN-ENDED COGNITIVE EVOLUTION, INDIVIDUAL DEVELOPMENT & EMERGENT CULTURAL INTELLIGENCE

**Fecha:** 10 de Noviembre de 2026  
**Fase:** Phase 1.3  
**Estado:** Implementado, Integrado, Probado (380/380 tests PASSED)  
**Compatibilidad:** Python 3.14.5 (64-bit), SQLite WAL Mode, Pydantic v2  

---

## 1. OBJETIVO Y VISIÓN ARQUITECTÓNICA

La Fase 1.3 de SALTBOR trasciende la simulación de agentes que meramente ejecutan algoritmos fijos o consumen recetas predeterminadas. Establece una arquitectura donde los individuos sintéticos modifican progresivamente sus capacidades cognitivas, sus métodos de aprendizaje (meta-aprendizaje), sus saberes y sus interpretaciones del mundo a partir de su historia de vida e interacción social.

Asimismo, la sociedad artificial desarrolla, transforma, fragmenta y pierde prácticas culturales, técnicas artesanales, gastronomía, normas sociales e instituciones educativas sin guiones predefinidos ni garantías de progreso ascendente universal.

---

## 2. ARQUITECTURA DE DOMINIO Y NUEVOS SUBSISTEMAS

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        MAPA DE LA ARQUITECTURA COGNITIVA FASE 1.3                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Perfil Cognitivo Individual Dinámico (14 Capacidades Diferenciadas)                 │
│    - logical_reasoning, working_memory_capacity, episodic_semantic_retention          │
│    - causal_understanding, problem_solving_ability, abstract_thinking                  │
│    - procedural_learning, pattern_recognition, combinatorial_creativity               │
│    - planning_depth, communication_efficacy, social_learning_fidelity                  │
│    - environmental_adaptability, metacognitive_accuracy                               │
│    - Invariantes: Presupuesto mental acotado (8.40), compensaciones y fatiga           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Motor de Aprendizaje de Segundo Orden (Meta-Learning Engine)                        │
│    - 6 Estrategias: Observación, Práctica Deliberada, Instrucción Formal,              │
│      Ensayo y Error, Colaboración de Pares, Inferencia Analógica                       │
│    - Selección autónoma según rendimiento empírico previo (XP/tick) y compatibilidad   │
│    - Detección de mesetas, errores recurrentes y solicitud autónoma de mentoría        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Plasticidad Cognitiva, Costos y Divergencia                                         │
│    - Curvas de práctica de ley de potencia asintótica con rendimientos decrecientes    │
│    - Atrofia por desuso (degradación logarítmica inspirada en Ebbinghaus)              │
│    - Sinergias de transferencia de dominio y penalizaciones por interferencia         │
│    - Impuesto cognitivo por privación socioeconómica y estrés crónico                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. Pensamiento Científico y Descubrimiento Epistémico (8 Estados)                      │
│    - Ciclo: OBSERVACIÓN -> PREGUNTA -> HIPÓTESIS -> EXPERIMENTACIÓN ->                 │
│             RESULTADO -> EVALUACIÓN -> REVISIÓN DE CREENCIA -> POSIBLE TRANSMISIÓN     │
│    - 8 Estados: VERIFIED_KNOWLEDGE, PROVISIONAL_KNOWLEDGE, HYPOTHESIS,                │
│      PERSONAL_BELIEF, RUMOR, CONTRADICTORY_INFO, FORGOTTEN_KNOWLEDGE, REFUTED_KNOWLEDGE│
│    - Posibilidad de conclusiones falsas por muestras pequeñas (N<=2) y ruido empírico  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. Evolución Cultural y Educación Distribuida                                          │
│    - Transmisión imperfecta dependiente de comunicación docente y fidelidad aprendiz   │
│    - Mutación y deriva estocástica; fragmentación cultural por partición social        │
│    - Extinción cultural irreversible ante mortalidad de maestros sin sucesores         │
│    - Emergencia espontánea de Talleres y Espacios de Aprendizaje sin umbrales censales │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 6. Resolución Colectiva de Problemas                                                  │
│    - Agrupación de capacidades complementarias frente a fricciones de coordinación     │
│    - Riesgo de fracaso colectivo por pensamiento de grupo (groupthink) o conflicto     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FORMULACIONES MATEMÁTICAS FORMALES

### 3.1 Presupuesto Cognitivo y Compensaciones
Sea $\mathbf{C} = (c_1, c_2, \dots, c_{14}) \in [0.05, 1.0]^{14}$ el vector de capacidades del individuo. La restricción de presupuesto mental sostenible es:
$$\sum_{i=1}^{14} c_i \le B_{\text{max}} = 8.40$$
Cuando el entrenamiento intensivo de una capacidad $c_k$ incrementa su nivel por $\Delta c_k$, si $\sum c_i > B_{\text{max}}$, las capacidades no ejercitadas $c_{j \neq k}$ experimentan una compensación distributiva:
$$c_j \leftarrow \max(c_j^{\text{base}} \cdot 0.60, \; c_j - \delta), \quad \text{donde } \delta = \frac{\text{exceso}}{13} \cdot 0.60$$

### 3.2 Curva de Práctica No Lineal con Rendimientos Decrecientes
La ganancia de competencia $\Delta P$ tras $H$ horas de práctica se rige por:
$$\Delta P = 0.04 \cdot H^{0.65} \cdot \Phi_{\text{eff}} \cdot (1 - P)^{1.2}$$
donde el ancho de banda cognitivo efectivo $\Phi_{\text{eff}}$ es:
$$\Phi_{\text{eff}} = \left(0.50 c_{\text{proc}} + 0.30 c_{\text{wm}} + 0.20 c_{\text{rel}}\right) \cdot (1 - 0.40 f) \cdot (1 - \tau_{\text{depriv}})$$
con fatiga mental $f \in [0, 0.40]$ y penalización por privación $\tau_{\text{depriv}} \in [0, 0.35]$.

### 3.3 Atrofia por Desuso (Ebbinghaus Asintótico)
Tras $\Delta t$ días de inactividad ($\Delta t > 3.0$):
$$\Delta P_{\text{atrophy}} = P \cdot (1 - \sigma_{\text{ret}}) \cdot 0.02 \cdot \ln(1 + \Delta t - 2.0)$$
donde el escudo de retención es $\sigma_{\text{ret}} = \min(0.95, 0.40 + 0.60 c_{\text{ret}})$. Para habilidades sobreaprendidas ($P > 0.85$), $\sigma_{\text{ret}} \leftarrow \min(0.99, \sigma_{\text{ret}} + 0.15)$.

### 3.4 Probabilidad de Adopción y Mutación Cultural
La probabilidad base de adopción en un contacto interpersonal diádico es:
$$P_{\text{base}} = \left(0.25 \, \text{trust} + 0.20 \, \text{prestige} + 0.20 \, \text{closeness} + 0.15 \, c_{\text{comm}}^{\text{mentor}} + 0.20 \, c_{\text{soc\_fid}}^{\text{learner}}\right) \cdot U_{\text{trad}}$$
Bajo una frecuencia de interacción $K$ (reiteración cotidiana):
$$P_{\text{adopt}} = 1 - (1 - P_{\text{base}})^K$$
La tasa de mutación o refracción cultural $\mu$ es inversamente proporcional a la fidelidad:
$$\mu = \max\left(0.12, \; 0.35 \cdot \left(1 - \frac{c_{\text{comm}}^{\text{mentor}} + c_{\text{soc\_fid}}^{\text{learner}}}{2}\right)\right)$$

---

## 4. INTEGRACIÓN TERRITORIAL Y SOCIOCULTURAL SALVADOREÑA

La arquitectura implementa dinámicas directas con el contexto salvadoreño:
1. **Corredor Seco y Sequía Agrícola:**
   - La milpa con cobertura de rastrojo y zanjas de ladera se somete a prueba empírica mediante el motor de pensamiento científico, descubriendo de forma autónoma su retención hídrica (+2.5 unidades de humedad).
2. **Gastronomía Tradicional y Nixtamalización:**
   - Las técnicas de cocción de maíz con cal y molienda circulan como tradiciones con fidelidad paramétrica, generando variantes regionales.
3. **Oficios y Talleres Comunitarios:**
   - Alfarería tradicional en Ilobasco y telares artesanales en San Sebastián emergen espontáneamente como talleres cuando existen artesanos mayores con prestigio y jóvenes aprendices locales.
4. **Resiliencia ante Crisis y Remesas:**
   - El choque económico por pérdidas de cosecha no altera caóticamente la personalidad basal de los agentes, pero incrementa de forma adaptativa su cautela y recurrencia al fiado o diversificación.
