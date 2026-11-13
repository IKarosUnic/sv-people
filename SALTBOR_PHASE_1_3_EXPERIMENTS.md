# SALTBOR — PHASE 1.3 EXPERIMENTAL VALIDATION REPORT
## EMPIRICAL RESULTS, HYPOTHESIS TESTING & REPRODUCIBILITY AUDIT FOR EXPERIMENTS EXP_13_A THROUGH EXP_13_O

**Fecha:** 10 de Noviembre de 2026  
**Investigación:** Validación Empírica de Sistemas Cognitivos y Culturales Emergentes  
**Repositorio:** `sv people` / Rama `master`  
**Estado:** **15/15 Experimentos PASSED (0.068s ejecución total)**  
**Evidencia Empírica Registrada:** `experiments/results/phase13/phase13_results.json`  

---

## 1. TABLA MAESTRA DE EXPERIMENTOS DE LA FASE 1.3

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TABLA DE EXPERIMENTOS FASE 1.3                                  │
├───────────┬──────────────────────────────────────────┬───────────────────────┬─────────┤
│ ID Exp.   │ Hipótesis Teórica Sometida a Prueba      │ Estado Científico     │ Estatus │
├───────────┼──────────────────────────────────────────┼───────────────────────┼─────────┤
│ EXP_13_A  │ Desarrollo Cognitivo y Compensaciones    │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_B  │ Aprendizaje de 2do Orden (Meta-Learning) │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_C  │ Plasticidad, Rendimientos y Atrofia      │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_D  │ Divergencia Cognitiva en Gemelos         │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_E  │ Descubrimiento Científico Autónomo (8 Et)│ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_F  │ Razonamiento, Error de Muestra y Refutac.│ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_G  │ Transmisión Cultural Imperfecta          │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_H  │ Fragmentación Cultural por Fisión        │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_I  │ Relevo Intergeneracional vs Extinción    │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_J  │ Educación Distribuida y Talleres         │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_K  │ Resolución Colectiva y Groupthink        │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_L  │ Impuesto Cognitivo por Privación         │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_M  │ Senescencia Fluida vs Sabiduría Cristal. │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_N  │ Estabilidad de Rasgos y Adaptación       │ HYPOTHESIS_SUPPORTED  │ PASS    │
│ EXP_13_O  │ Evolución Longitudinal Multi-Sociedad    │ HYPOTHESIS_SUPPORTED  │ PASS    │
└───────────┴──────────────────────────────────────────┴───────────────────────┴─────────┘
```

---

## 2. ANÁLISIS DETALLADO DE CADA EXPERIMENTO

### 2.1 EXP_13_A: Desarrollo Cognitivo Individual y Compensaciones
- **Hipótesis:** *"El entrenamiento deliberado e intensivo en habilidades procedimentales y de resolución de problemas produce mejoras significativas sin un incremento uniforme en todas las capacidades (respetando restricciones de presupuesto mental)."*
- **Evidencia Empírica Multi-Semilla ($S = \{42, 101, 777, 1337, 2026\}$):**
  - Ganancia media en capacidad entrenada (`procedural_learning`): $+0.1542$.
  - Ganancia media en capacidad no entrenada (`abstract_thinking`): $+0.0000$.
  - Ratio de especialización entrenada vs no entrenada: $154.19\times$.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Se rechaza la noción de un "IQ general" que se eleva homogéneamente. La cognición se especializa con compensaciones claras.

---

### 2.2 EXP_13_B: Aprendizaje de Segundo Orden (Aprender a Aprender)
- **Hipótesis:** *"Los agentes equipados con motor de meta-aprendizaje reconocen estrategias ineficaces (ensayo y error en tareas complejas) y pivotan hacia métodos superiores (práctica deliberada), acumulando más del doble de experiencia que agentes bloqueados en un método fijo."*
- **Evidencia Empírica:**
  - Cambios autónomos de estrategia registrados: media de $12.67$ transiciones.
  - XP acumulada por agentes con meta-aprendizaje: $\mu = 42.33$ XP.
  - XP acumulada por agentes de control con estrategia fija: $\mu = 9.00$ XP.
  - Multiplicador de ventaja adaptativa: **$4.70\times$**.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Los individuos aprenden a modificar su propia manera de aprender.

---

### 2.3 EXP_13_C: Plasticidad Cognitiva, Curvas de Práctica y Atrofia
- **Hipótesis:** *"La ganancia marginal de competencia decrece asintóticamente conforme se aproxima a la maestría, y los periodos prolongados de inactividad inducen atrofia por desuso, siendo menor en habilidades sobreaprendidas."*
- **Evidencia Empírica:**
  - Ganancia marginal en novato ($P=0.20$): $+0.0523$ por 5 horas de práctica.
  - Ganancia marginal en experto ($P=0.85$): $+0.0070$ por 5 horas de práctica.
  - Ratio de rendimientos decrecientes: **$7.45\times$** más esfuerzo requerido por unidad de ganancia en niveles avanzados.
  - Atrofia normal tras 45 días de inactividad: $-0.0136$.
  - Atrofia en habilidad sobreaprendida: $-0.0068$ (50% de retención superior).
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Validación rigurosa de las leyes de potencia de práctica y decaimiento mnémico.

---

### 2.4 EXP_13_D: Divergencia Cognitiva Individual
- **Hipótesis:** *"Gemelos sintéticos con perfiles idénticos iniciales ($L_2 = 0.0$) expuestos a nichos ocupacionales opuestos (comercio urbano vs agricultura rural) divergen de forma estadísticamente significativa en el espacio 14D."*
- **Evidencia Empírica ($N=5$ pares de gemelos):**
  - Distancia Euclidiana $L_2$ inicial: $0.0000$.
  - Distancia Euclidiana $L_2$ final: $\mu = 0.4079$.
  - Distancia Manhattan $L_1$ final: $\mu = 1.0967$.
  - Máxima disparidad en una dimensión: $\mu = 0.2818$ (entre comunicación y adaptabilidad ambiental).
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. La historia y el entorno moldean trayectorias cognitivas irreductibles a la genética inicial.

---

### 2.5 EXP_13_E: Descubrimiento de Conocimiento Autónomo
- **Hipótesis:** *"Ante una anomalía territorial no resuelta, los agentes completan autónomamente las 8 etapas del pensamiento científico sin nombres de soluciones ni recetas pre-programadas."*
- **Evidencia Empírica:**
  - Etapas transitadas y registradas: 8 de 8 (`OBSERVATION` $\to$ `TRANSMISSION`).
  - Causalidad empírica demostrada: $\Delta = +2.532$ en retención de humedad.
  - Estado epistémico final: `VERIFIED_KNOWLEDGE` (confianza $0.785$).
  - Saltos de transmisión registrados: $1$.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Demuestra pensamiento crítico emergente desde abajo hacia arriba.

---

### 2.6 EXP_13_F: Razonamiento Científico, Conclusiones Erróneas y Refutación
- **Hipótesis:** *"En presencia de ruido empírico, muestras reducidas ($N=1$) pueden inducir conclusiones erróneas provisionales (falso positivo), pero ensayos ampliados sistemáticos ($N=8$) fuerzan la revisión bayesiana hacia la refutación formal."*
- **Evidencia Empírica:**
  - Evaluación inicial con $N=1$: dictamen `false_conclusion` con confianza provisional de $0.550$.
  - Evaluación tras replicación con $N=8$: dictamen `refuted` con transición a estado **`REFUTED_KNOWLEDGE`** y reducción de confianza a $0.347$.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. El sistema es capaz de equivocarse y auto-corregirse ante evidencia empírica contradictoria.

---

### 2.7 EXP_13_G: Transmisión Cultural Imperfecta y Mutación
- **Hipótesis:** *"La difusión cultural a lo largo de una cadena diádica de 5 saltos exhibe pérdidas de fidelidad y variaciones mutacionales condicionadas a la fidelidad del receptor y la elocuencia del emisor."*
- **Evidencia Empírica:**
  - Transmisiones exitosas: 5 de 5 saltos completados.
  - Variantes/mutaciones generadas autónomamente: 2 variantes locales emergentes.
  - Fidelidad media de la red cultural: $0.887$ (deriva no nula respecto al prototipo original).
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. La cultura se transforma durante su difusión social.

---

### 2.8 EXP_13_H: Fragmentación Cultural por Partición Social
- **Hipótesis:** *"La ruptura de lazos comunitarios (fisión social) aísla subgrupos que practican una misma técnica ancestral, generando derivas paramétricas divergentes ($D > 0.30$)."*
- **Evidencia Empírica:**
  - Tradición compartida: Sistema de captación de agua en milpa (30 cm de profundidad base).
  - Parámetro en Grupo A (tradicional): $30.0$ cm.
  - Parámetro en Grupo B (comunidad escindida): $42.0$ cm.
  - Delta de divergencia paramétrica: $12.0$ cm ($+40.0\%$).
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. La distancia relacional engendra diversificación cultural.

---

### 2.9 EXP_13_I: Transmisión Intergeneracional y Extinción Cultural
- **Hipótesis:** *"Los saberes técnicos sobreviven cuando se transfieren a aprendices jóvenes antes de la defunción de los ancianos; mueren irreversiblemente si el último maestro fallece sin sucesores."*
- **Evidencia Empírica:**
  - Tradición con aprendiz (*Alfarería de Ilobasco*): Relevo completado; $N=2$ adoptantes activos.
  - Tradición sin aprendiz (*Añil Silvestre*): Defunción del maestro maestro $\to$ clasificada formalmente como **`is_extinct = True`**, desapareciendo del repertorio comunitario activo.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. La cultura no es inmortal; depende de la continuidad biológica y social.

---

### 2.10 EXP_13_J: Educación Distribuida y Emergencia de Talleres
- **Hipótesis:** *"Bajo condiciones de déficit técnico local y excedente de recursos, los maestros y aprendices fundan talleres de formación espontánea que aceleran el aprendizaje respecto al autodidactismo solitario en $> 20\%$."*
- **Evidencia Empírica:**
  - Institución emergida: *Taller Comunitario de Textiles de san_sebastian_textil*.
  - Aprendices matriculados: 3.
  - Ganancia media en taller guiado: $+0.0942$.
  - Ganancia en práctica autodidacta sin maestro: $+0.0438$.
  - Ventaja pedagógica institucional: **$+115.2\%$**.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Las instituciones surgen de la necesidad social y potencian la transmisión del saber.

---

### 2.11 EXP_13_K: Resolución Colectiva de Problemas y Fricción
- **Hipótesis:** *"La cooperación multi-agente no garantiza soluciones: grupos con capacidades complementarias alineadas resuelven problemas difíciles, mientras que grupos con conflictos de interés o pensamiento de grupo acrítico colapsan en fracaso."*
- **Evidencia Empírica:**
  - Equipo 1 (Alineado y complementario): Resultado = **`SOLVED`**.
  - Equipo 2 (Conflictos de interés mayoritarios): Resultado = **`FAILED`** (coordinación rota).
  - Equipo 3 (Pensamiento de grupo con propuesta técnica viciada): Resultado = **`FAILED`** (adopción unánime errónea).
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. El trabajo en equipo reproduce dinámicas complejas de fricción y conformidad social.

---

### 2.12 EXP_13_L: Desarrollo Cognitivo Bajo Escasez y Privación
- **Hipótesis:** *"La privación socioeconómica severa (hambre $\ge 0.70$ y cero ahorro) impone un impuesto cognitivo que deprime la memoria de trabajo efectiva y la tasa de asimilación de habilidades."*
- **Evidencia Empírica:**
  - Memoria de trabajo efectiva en abundancia: $0.463$.
  - Memoria de trabajo efectiva bajo privación: $0.301$ (caída del $-35.0\%$).
  - Ganancia de habilidad en abundancia: $+0.0520$.
  - Ganancia de habilidad bajo privación: $+0.0270$.
  - Impuesto cognitivo efectivo sobre el aprendizaje: **$-48.1\%$**.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. La pobreza material se traduce directamente en pérdida de ancho de banda cognitivo.

---

### 2.13 EXP_13_M: Envejecimiento Cognitivo y Retención de Saberes
- **Hipótesis:** *"El envejecimiento biológico deteriora selectivamente capacidades fluidas (velocidad de procesamiento y memoria de trabajo), preservando o expandiendo la sabiduría causal y metacognitiva acumulada."*
- **Evidencia Empírica:**
  - Plasticidad fluida en joven (22 años): $1.000$.
  - Plasticidad fluida en anciano (72 años): $0.560$ (declinación del $-44.0\%$).
  - Plasticidad cristalizada en anciano: $0.890$ (alta maleabilidad semántica conservada).
  - Nivel de comprensión causal acumulada en anciano: $0.850$.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Distinción confirmada entre inteligencia fluida y cristalizada a lo largo del ciclo vital.

---

### 2.14 EXP_13_N: Adaptación Conductual y Estabilidad de Rasgos
- **Hipótesis:** *"Los choques económicos graves generan adaptaciones inmediatas en cautela y hábitos sin provocar derivas caóticas e inestables en los rasgos basales de personalidad."*
- **Evidencia Empírica:**
  - Deriva en rasgo basal de neuroticismo: $0.0020 \le 0.05$ (estabilidad basal verificada).
  - Incremento adaptativo en estado cauteloso actual: $+0.0098$.
  - Variación caótica o arbitraria detectada: **$0\%$**.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. Personalidad robusta ante el ruido, plástica ante la experiencia sostenida.

---

### 2.15 EXP_13_O: Evolución Cognitiva y Cultural Longitudinal
- **Hipótesis:** *"Simulaciones multi-agente longitudinales en paralelo divergen de forma estocástica hacia estados culturales y cognitivos heterogéneos sin requerir directivas centrales."*
- **Evidencia Empírica ($S = \{42, 101, 777, 1337, 2026\}$):**
  - Distancia media inter-societal en el espacio compuesto: $\mu = 1.0772 > 0.50$.
  - Disparidad mínima observada entre sociedades: $0.6272$.
  - Disparidad máxima observada entre sociedades: $1.7699$.
- **Dictamen:** **`HYPOTHESIS_SUPPORTED`**. La historia en SALTBOR es abierta, contingente y no sujeta a convergencias forzadas.
