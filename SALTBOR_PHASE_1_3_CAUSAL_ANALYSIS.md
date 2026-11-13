# SALTBOR — PHASE 1.3 CAUSAL ANALYSIS
## COUNTERFACTUAL CAUSALITY, COGNITIVE DIVERGENCE, EPISTEMIC FALSIFICATION & RIGIDITY AUDIT

**Fecha:** 10 de Noviembre de 2026  
**Investigación:** Causal Inference & Computational Cognitive Science Group  
**Repositorio:** `sv people` / Rama `master`  
**Evidencia Empírica:** `experiments/results/phase13/phase13_results.json` (EXP_13_A a EXP_13_O)  

---

## 1. MARCO METODOLÓGICO Y CONTRAFACTUAL

El núcleo de la Fase 1.3 rechaza la falacia del "progreso garantizado" en agentes sintéticos. En muchos modelos multi-agente tradicionales, el aprendizaje se reduce a un contador incremental monótono donde los agentes acumulan puntos de experiencia linealmente.

En SALTBOR Phase 1.3, el desarrollo individual y la inteligencia cultural se modelan como **procesos causales dinámicos, contingentes y reversibles**:
1. El aprendizaje tiene costos de oportunidad y fatiga.
2. Las capacidades no practicadas sufren atrofia por desuso (*Ebbinghaus decay*).
3. El estrés biológico y la pobreza imponen un "impuesto cognitivo" (*cognitive tax*) que reduce el ancho de banda efectivo.
4. La ciencia empírica puede llevar a conclusiones erróneas por sesgos de muestra pequeña antes de ser corregida por replicación.
5. Las tradiciones culturales se distorsionan o extinguen irremediablemente ante el aislamiento o la muerte de los sabios ancianos.

Para aislar formalmente el impacto de cada mecanismo, empleamos el marco contrafactual de Rubin acoplado a simulaciones multi-semilla sincronizadas.

---

## 2. DIVERGENCIA COGNITIVA CONTRAFACTUAL (GEMELOS SINTÉTICOS)

### 2.1 Planteamiento del Experimento
Sea un par de agentes "gemelos" $A_1$ y $A_2$ con perfiles cognitivos iniciales idénticos en $\mathbb{R}^{14}$:
$$\mathbf{c}_1(t=0) = \mathbf{c}_2(t=0) = [0.60, 0.60, \dots, 0.60], \quad \|\mathbf{c}\|_1 = 8.40$$

- **Sujeto $A_1$ (Condición Vulnerable):** Expuesto a estrés nutricional crónico (hambre $= 0.85$, fatiga continua, sin acceso a educación).
- **Sujeto $A_2$ (Condición Nutriente):** Expuesto a práctica deliberada en razonamiento lógico y memoria de trabajo, con nutrición óptima y descanso diario.

### 2.2 Resultados Empíricos (`EXP_13_D` & `EXP_13_E`)
Tras 30 ticks de simulación:

| Dimensión Cognitiva | Sujeto $A_1$ (Privación) | Sujeto $A_2$ (Práctica + Soporte) | Efecto Causal ($\tau = A_2 - A_1$) |
|---|---|---|---|
| **Razonamiento Lógico** | $0.468$ | $0.782$ | **$+0.314$** ($p < 0.001$) |
| **Memoria de Trabajo** | $0.441$ | $0.745$ | **$+0.304$** ($p < 0.001$) |
| **Creatividad Combinatoria** | $0.512$ | $0.589$ | **$+0.077$** |
| **Adaptación Ambiental** | $0.672$ | $0.531$ | **$-0.141$** ($A_1$ especializa en supervivencia) |
| **Distancia Euclidiana 14D ($L_2$)** | — | — | **$D = 0.528$** |

### 2.3 Hallazgos Causales:
1. **Divergencia Real sin Sesgo Inicial:** Dos agentes idénticos se bifurcan fenotípicamente como consecuencia exclusiva de su trayectoria vital.
2. **Especialización Inversa:** El agente en privación no se vuelve "tonto en todo"; su capacidad de *Adaptación Ambiental* aumenta en relación a sus otras capacidades para maximizar supervivencia inmediata, mientras que sus funciones ejecutivas abstractas se sacrifican por el impuesto cognitivo.

---

## 3. CAUSALIDAD EN EL META-APRENDIZAJE (*LEARNING TO LEARN*)

### 3.1 Transición Dinámica de Estrategias (`EXP_13_B`)
Se evaluó si los agentes cambian su estrategia de aprendizaje en respuesta causal a la acumulación de fracasos o si lo hacen por ruido estocástico:

- **Fase Inicial:** El agente inicia con `OBSERVATION` (observar a otros artesanos).
- **Perturbación Causal:** Se inyecta una tasa de fallo forzada en la tarea ($r < 0$ durante 4 ticks consecutivos).
- **Mecanismo Evaluado:**
  $$\text{Streak}_{\text{fail}} \ge 3 \implies \text{trigger\_strategy\_switch}()$$
- **Resultado:**
  - El agente detecta la meseta/ineficacia y conmuta inmediatamente a `TRIAL_ERROR` o `DELIBERATE_PRACTICE`.
  - La recompensa promedio tras la conmutación se incrementa de $-0.25$ a $+0.58$.
  - En el contrafactual con el motor de meta-aprendizaje desactivado (agente atado rígidamente a `OBSERVATION`), la tasa de fallo persiste indefinidamente, produciendo un colapso en la habilidad.

---

## 4. EPISTEMOLOGÍA EXPERIMENTAL Y REFUTACIÓN CIENTÍFICA

### 4.1 La Trampa del Tamaño Muestral Pequeño (`EXP_13_F`)
Uno de los principios de diseño más estrictos de la Fase 1.3 es que los agentes **no reciben la verdad universal revelada**.

En `EXP_13_F`, un agente investiga si "añadir ceniza volcánica a la milpa duplica la cosecha":
1. **Ensayo Inicial ($N=1$, muestra ruidosa):**
   - Una fluctuación meteorológica favorable coincide con la aplicación de ceniza.
   - El agente calcula $\Delta y = +0.45$.
   - **Estado Epistémico:** `HYPOTHESIS` con alta confianza subjetiva inicial ($0.80$). Conclusión prematura y espuria.
2. **Replicación Sistemática ($N \ge 8$):**
   - El agente ejecuta experimentos controlados repetidos. La media empírica de diferencia converge a $\Delta \bar{y} = 0.00$.
   - **Transición Causal de Creencia:** El motor de pensamiento científico detecta contradicción con la predicción ($E_{\text{observed}} \ll E_{\text{predicted}}$).
   - **Estado Epistémico Final:** `REFUTED_KNOWLEDGE` (confianza $0.90$ en la falsedad de la hipótesis).

```
Evolución de la Confianza Epistémica en una Hipótesis Falsa
Confianza
1.0 ┤      ● (N=1, Falso Positivo)
0.8 ┤     / \
0.6 ┤    /   \
0.4 ┤   /     \  ● (N=4, Duda Metódica)
0.2 ┤  /       \───● (N=8, REFUTED_KNOWLEDGE)
0.0 └──┴───────────┴───────────►
      t=0        t=5          t=15
```

---

## 5. TRANSMISIÓN IMPERFECTA Y EXTINCIÓN CULTURAL

### 5.1 Pérdida de Información Intergeneracional (`EXP_13_G`)
En una cadena de transmisión de 5 agentes sucesivos ($A_1 \to A_2 \to A_3 \to A_4 \to A_5$):
- **Complejidad Inicial:** Técnica agrícola ancestral con fidelidad $1.00$ y parámetros $[0.85, 0.40, 0.90]$.
- **Mecanismo:** La probabilidad de transmisión está modulada por la capacidad comunicativa del maestro y la capacidad social del aprendiz:
  $$P(\text{adopción}) = 1 - (1 - P_{\text{base}})^K$$
- **Resultado:**
  - A lo largo de la cadena, los parámetros mutan estocásticamente ($\mu \in [-0.05, +0.05]$ por paso).
  - La fidelidad final cae a $0.77$.
  - Si los encuentros son infrecuentes ($K=1$), la tradición se pierde en el paso 3. Con $K=6$, sobrevive pero transformada.

### 5.2 Extinción Irreversible (`EXP_13_H`)
- Cuando el único portador anciano de una tradición fallece sin que ningún aprendiz haya completado el proceso de internalización, la tradición se marca como `is_extinct = True`.
- **Efecto Contrafactual:** La sociedad pierde la capacidad de ejecutar la técnica; futuros agentes deben redescubrirla mediante pensamiento científico o experimentación desde cero, incurriendo en elevados costos temporales.

---

## 6. AUDITORÍA DE RIGIDEZ Y PRESERVACIÓN DE COMPLEJIDAD

Se realizó una auditoría de código para verificar la ausencia de trampas algorítmicas comunes:

1. **¿Existe un factor general "IQ" escondido?**
   - **No.** Se auditaron las 14 capacidades. Operan con tasas de fatiga independientes, elasticidades de práctica diferenciadas y costos de oportunidad sobre el presupuesto mental $B=8.40$.
2. **¿Aparecen instituciones automáticamente por umbrales de población?**
   - **No.** En `EXP_13_J`, una aldea de 50 habitantes sin maestros calificados no genera escuelas. Un taller surge espontáneamente en una aldea de 5 habitantes cuando un artesano de alto nivel ($>0.70$) coincide con aprendices necesitados y relaciones de confianza activa.
3. **¿La cooperación garantiza el éxito?**
   - **No.** En `EXP_13_K`, grupos con alta homogeneidad y obediencia a una figura autoritaria cayeron en *pensamiento de grupo* (*groupthink*), aprobando unánimemente una propuesta catastrófica. La diversidad cognitiva y el desacuerdo fueron necesarios para evitar el sesgo de confirmación grupal.

---

## 7. CONCLUSIÓN

El análisis causal confirma que la Fase 1.3 de SALTBOR genera **inteligencia adaptativa real y contingente**:
- Los individuos pueden fracasar, olvidar, estancarse o especializarse.
- El conocimiento científico avanza por ensayo y refutación empírica.
- Las culturas están sujetas a deriva memética, mutación y extinción.
- Todo fenómeno observado responde a interacciones causales trazables bit a bit entre agentes y su entorno histórico.
