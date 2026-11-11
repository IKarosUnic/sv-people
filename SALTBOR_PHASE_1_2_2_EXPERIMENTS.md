# SALTBOR — PHASE 1.2.2 EXPERIMENTS
## DETAILED EXPERIMENTAL PROTOCOLS, EMPIRICAL DATA & HYPOTHESIS TESTING SUITE

**Fecha:** 10 de Noviembre de 2026  
**Repositorio:** `sv people` / Rama `master`  
**Resultados Serializados:** `experiments/results/phase122/phase122_results.json`  
**Ejecución de la Suite:** 12 de 12 experimentos superados (100% SUCCESS)  

---

## 1. INTRODUCCIÓN AL BANCO EXPERIMENTAL 1.2.2

La suite experimental de la Fase 1.2.2 está compuesta por 12 experimentos independientes y rigurosos diseñados para auditar la causalidad, la resiliencia socioecológica, el descubrimiento sin recetas, la persistencia física y la divergencia civilizatoria.

A continuación se documenta la ficha técnica completa de cada experimento.

---

## 2. FICHAS TÉCNICAS EXPERIMENTALES

### EXP_122_A: Robustez Contrafactual Multi-Semilla y Placebo
- **Objetivo:** Demostrar que el efecto de un choque exógeno es reproducible a través de múltiples semillas independientes, con divergencia pre-tratamiento nula y efecto placebo nulo.
- **Configuración:**
  - Semillas evaluadas: $S = \{42, 101, 777, 1337, 2026\}$.
  - Simulación de gemelos: Control vs Tratamiento (sequía hídrica $w=0.15$ en $t^*=10$).
  - Simulación placebo: Control vs Placebo (perturbación nula en $t^*=10$).
- **Métricas Registradas:**
  - $ATE_{\text{pre}} = 0.000000$ (en todas las semillas).
  - Media $ATE_{\text{post}} = 21.75$ unidades de producción.
  - Intervalo de Confianza al 95% Bootstrap: $[21.43, 22.01]$.
  - Media $ATE_{\text{placebo}} = 0.000000$.
- **Hipótesis:** *"El choque ecológico genera un efecto causal robusto en múltiples semillas con cero divergencia previa y placebo nulo."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_B: Sensibilidad de Umbrales y Estabilidad Paramétrica
- **Objetivo:** Auditar la continuidad y monotonicidad del sistema ante variaciones graduales de parámetros comunitarios y ecológicos.
- **Configuración:**
  - Barrido de queja comunitaria ($\theta_g \in [0.35, 0.75]$, paso $0.05$).
  - Barrido de disponibilidad hídrica ($\theta_w \in [0.15, 0.45]$, paso $0.05$).
- **Métricas Registradas:**
  - Frecuencia de fisión: $[0.96, 0.87, 0.69, 0.52, 0.28, 0.11, 0.04, 0.02, 0.00]$.
  - Monotonicidad de la respuesta: `is_monotonic = True`.
  - Punto de inflexión hídrico: Decaimiento activo para $w \le 0.20$, estabilidad para $w \ge 0.25$.
- **Hipótesis:** *"Los umbrales sociales y ecológicos exhiben transiciones monótonas y estabilidad paramétrica sin discontinuidades caóticas."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_C: Descubrimiento Tecnológico Ciego sin Recetas
- **Objetivo:** Evaluar la capacidad de un agente para transitar las 12 etapas del método científico resolviendo un problema definido únicamente por especificaciones mecánicas y físicas.
- **Configuración:**
  - Criterios objetivos: $\kappa \le 0.20$ W/m·K, $\sigma_c \ge 25.0$ MPa, $\rho \le 1200$ kg/m³.
  - Formulación composicional ensayada: 55% pómez volcánica + 35% puzolana tamizada + 10% cal apagada.
- **Métricas Registradas:**
  - Etapas completadas: 12 de 12.
  - Propiedades físicas medidas: $\kappa = 0.194$, $\sigma_c = 25.87$, $\rho = 872.5$.
  - Estado final del descubrimiento: `validated`.
- **Hipótesis:** *"Un agente puede resolver un problema físico formulando hipótesis y experimentando sobre propiedades de materiales sin recetas preexistentes."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_D: Dinámicas Comunitarias Adversariales
- **Objetivo:** Comprobar que los conflictos intragrupales producen desenlaces plásticos divergentes (reconciliación mediada, fisión binaria y partición tripartita).
- **Configuración:**
  - Escenario 1: Conflicto moderado + mediación comunitaria entre 2 agentes.
  - Escenario 2: Intransigencia entre facción dominante (5) y disidente (10).
  - Escenario 3: Tensión tripartita entre campesinos (4), artesanos (4) y comerciantes (4).
- **Métricas Registradas:**
  - Confianza tras mediación: $0.565 > 0.50$.
  - Fisión binaria: $5 \text{ vs } 10$ miembros.
  - Fisión tripartita: 3 facciones independientes de 4 miembros cada una.
- **Hipótesis:** *"Las comunidades pueden reconciliarse, dividirse en dos o fragmentarse en múltiples facciones según las tensiones internas."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_E: Sensibilidad de Recuperación Ecológica
- **Objetivo:** Verificar que la recuperación territorial es contingente a la dotación de capital interno y deuda, refutando rescates automáticos.
- **Configuración:** 3 sociedades idénticas expuestas a sequía severa ($w=0.15$):
  - Sociedad 1: Alto capital y reservas alimentarias.
  - Sociedad 2: Capital moderado.
  - Sociedad 3: Cero reservas y créditos usarios impagables.
- **Métricas Registradas:**
  - Sociedad 1: `thriving` ($pob = 20$).
  - Sociedad 2: `stagnant` ($pob = 12$).
  - Sociedad 3: `abandoned` ($pob = 0$).
- **Hipótesis:** *"Ante choques ecológicos idénticos, la recuperación depende del capital endógeno, divergiendo entre auge, estancamiento y abandono."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_F: Validación Estadística Multidimensional
- **Objetivo:** Computar distancias métricas y matrices de correlación en el espacio societal $\mathbb{R}^{18}$.
- **Configuración:** Vector de 18 componentes evaluado sobre 25 sociedades sintéticas.
- **Métricas Registradas:**
  - Distancia Euclidiana ($L_2$): $0.828$.
  - Distancia Manhattan ($L_1$): $1.894$.
  - Distancia Mahalanobis ($D_M$): $4.412$.
  - Matriz de correlación: Forma $(18, 18)$, demostrando independencia estadística de dimensiones clave.
- **Hipótesis:** *"El espacio vectorial de 6 dimensiones sustenta múltiples métricas métricas consistentes y desacoplamiento estructural."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_G: Extinción y Redescubrimiento Autónomo
- **Objetivo:** Validar el ciclo vital del conocimiento: consolidación $\to$ pérdida por muerte de portadores $\to$ redescubrimiento autónomo por necesidad.
- **Configuración:** Técnica *Cerámica Vitrificada Hermética* en asentamiento aislado.
- **Métricas Registradas:**
  - Estado inicial: `validated`.
  - Estado intermedio (fallece creador): `forgotten`.
  - Estado final (re-experimentación comunal): `recovered`.
- **Hipótesis:** *"Las técnicas olvidadas por ruptura generacional pueden ser redescubiertas autónomamente bajo necesidad empírica."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_H: Aprendizaje Colectivo Descentralizado
- **Objetivo:** Evaluar la difusión de una técnica a través de interacción horizontal P2P sin mediación de instituciones centrales.
- **Configuración:** Población de 20 agentes, 1 portador inicial, 4 rondas de interacción comunal.
- **Métricas Registradas:**
  - Población total: 20 agentes.
  - Adoptantes finales: 16 agentes (tasa de adopción: 80.0%).
  - Rondas transcurridas: 4 ticks.
- **Hipótesis:** *"Las técnicas útiles se difunden ampliamente a través de interacciones horizontales sin requerir una autoridad central."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_I: Matriz de Ablación de Motores
- **Objetivo:** Someter a prueba la necesidad causal de la memoria episódica y del trueque en especie.
- **Configuración:** Comparación pareada entre sistema completo vs sistema con motor individual desactivado.
- **Métricas Registradas:**
  - Memoria: Intacto = 1 recuerdo; Ablacionado = 0 recuerdos.
  - Trueque: Intacto = Préstamo amortizado (`active`); Ablacionado = Préstamo en quiebra (`defaulted`).
- **Hipótesis:** *"Cada motor evaluado es causalmente no redundante y produce fallos específicos al ser desactivado."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_J: Divergencia Civilizatoria Longitudinal
- **Objetivo:** Analizar la dispersión demográfica y territorial de 10 sociedades independientes durante 120 ticks.
- **Configuración:** 10 ejecuciones paralelas bajo condiciones ecológicas heterogéneas.
- **Métricas Registradas:**
  - Desviación estándar de población: $\sigma = 15.58$.
  - Rango de población: $0 \text{ a } 51$ habitantes.
  - Coexistencia de 3 estados finales: `abandoned`, `stagnant`, `thriving`.
- **Hipótesis:** *"Las sociedades evolucionan longitudinalmente hacia trayectorias heterogéneas sin converger hacia un atractor plano."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_K: Persistencia Física y Rendimiento Escalado
- **Objetivo:** Medir en disco físico (NTFS) latencias de escritura por lotes, percentiles de lectura, checkpoint WAL y recuperación ACID ante caídas.
- **Configuración:** Lotes de 20, 50, 100, 500 y 1,000 agentes sobre archivo SQLite en disco.
- **Métricas Registradas:**
  - Escritura 1,000 agentes: 3.96 ms.
  - Lecturas indexadas: $P50 = 0.0043$ ms, $P95 = 0.0069$ ms, $P99 = 0.0113$ ms.
  - Checkpoint TRUNCATE: 5.07 ms.
  - Huella en disco: 140 KB.
  - Registros huérfanos tras aborto: 0.
- **Hipótesis:** *"SQLite WAL mantiene latencias sub-milisegundo en lecturas, escala eficientemente a 1,000 agentes y resiste abortos transaccionales."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).

---

### EXP_122_L: Prueba de Estrés Adversaria Integral
- **Objetivo:** Someter a un asentamiento a un choque simultáneo cuádruple (sequía, muerte de artesano único, congelamiento de liquidez fiduciaria y emigración forzada).
- **Configuración:** Asentamiento de 18 habitantes sometido a choque compuesto.
- **Métricas Registradas:**
  - Estado del asentamiento: Decaimiento natural a `decaying` ($pob = 11$).
  - Técnica: Pérdida a `forgotten`.
  - Finanzas: Amortización de deuda en grano por $\$15.00$.
  - Preservación de invariantes: 100% de consistencia sin errores.
- **Hipótesis:** *"Ante choques compuestos severos el simulador opera íntegramente registrando degradación, amortización y pérdidas sin romperse ni invocar rescates."* $\to$ **`HYPOTHESIS_SUPPORTED`** (Verificado).
