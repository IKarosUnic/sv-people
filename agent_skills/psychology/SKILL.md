---
name: saltbor-psychology
description: Computational appraisal (OCC), emotional dynamics, coping strategies, and Big Five personality plasticity.
---

# SKILL: Computational Psychology, Affective Dynamics & Trait Plasticity

## 1. Objetivo
Modelar la vida psicológica interna de los humanos sintéticos: evaluación cognitiva de acontecimientos según la teoría Ortony-Clore-Collins (OCC), dinámica de valencia emocional, estrategias de afrontamiento (*coping*), consolidación de memoria afectiva y deriva plástica selectiva de rasgos de personalidad (Big Five).

## 2. Cuándo Utilizarla
- Al procesar la reacción de un individuo ante eventos críticos (desastres naturales, pérdida económica, traición social, éxito comunitario).
- Al modelar la toma de decisiones sesgada por el estado afectivo o el estrés.
- Al calibrar la deriva de rasgos de personalidad tras experiencias vitales prolongadas.
- Al depurar mecanismos de afrontamiento activo o pasivo frente a la escasez.

## 3. Instrucciones de Trabajo
1. **Evaluación Subjetiva Basada en Acontecimientos (OCC)**:
   - Los acontecimientos no tienen impacto emocional objetivo universal. Se evalúan según:
     - Valencia intrínseca (placer / dolor).
     - Congruencia con las metas activas del individuo.
     - Responsabilidad causal (propia, de otro, o de la naturaleza).
     - Controlabilidad y potencial de afrontamiento.
     - Compatibilidad con normas internas y valores personales.
2. **Estabilidad de Rasgos vs Plasticidad Selectiva**:
   - Los rasgos del Big Five (*Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism*) son estables a corto plazo.
   - Eventos cotidianos triviales **NO** deben alterar los rasgos fundamentales.
   - Únicamente traumas severos reiterados (inundaciones, quiebra económica, violencia) o enriquecimientos sostenidos pueden inducir una deriva plástica gradual ($\Delta < 0.05$).
3. **Estrategias de Afrontamiento (*Coping Strategies*)**:
   - *Afrontamiento Enfocado en el Problema*: Búsqueda activa de empleo, reparación física de vivienda, convocatoria de asamblea.
   - *Afrontamiento Enfocado en la Emoción*: Búsqueda de consuelo en redes familiares, participación en fiestas patronales o resignación.

## 4. Procedimientos y Métodos
- **Vector de Evaluación OCC**:
  $$\text{VectorAppraisal} = [\text{Novedad}, \text{Valencia}, \text{MetaRelevancia}, \text{MetaCongruencia}, \text{Urgencia}, \text{Control}, \text{Potencia}, \text{Afrontamiento}, \text{NormaCompatibilidad}]$$
- **Actualización de Estrés**:
  $$\text{Estrés}_{t+1} = \text{Estrés}_t \cdot e^{-\lambda \Delta t} + \Delta \text{Estrés}(\text{Acontecimiento})$$

## 5. Referencias y Repositorios Clave
- *The Cognitive Structure of Emotions* (Ortony, Clore & Collins, OCC Model).
- *Stress, Appraisal, and Coping* (Richard Lazarus & Susan Folkman).
- `saltbor/psychology/engine.py`, `saltbor/psychology/appraisal.py`.

## 6. Herramientas Requeridas
- `PsychologicalEngine`
- `SyntheticHuman.psychological_state`
- `tests/test_experiments/test_phase17_experiments.py`

## 7. Criterios de Validación
- Validación en `EXP_17_A` (deriva plástica ante trauma vs estabilidad ante rutina).
- Ausencia de oscilaciones emocionales caóticas o desbordes numéricos (NaN o Inf).
- Rendimiento ultra-rápido ($<0.5$ ms para 100 agentes en la capa psicológica).

## 8. Limitaciones
- No tratar a los agentes como autómatas puramente racionales que maximizan utilidad matemática fría; el afecto modula las prioridades de elección.
