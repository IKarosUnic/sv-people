# SKILL: Cognitive Science & Social Epistemology
`agent_skills/cognitive_science/SKILL.md`

## 1. Purpose & Domain Scope
Guides the architecture of synthetic human memory, belief formation, cognitive appraisal, source trustworthiness, confirmation bias, and social epistemology.

## 2. When to Use
- Implementing agent belief updates upon receiving broadcast news or interpersonal rumors.
- Modeling cognitive dissonance, selective exposure, and memory decay.
- Evaluating how educational background, personality (Big Five), and emotional state modulate gullibility or skepticism.

## 3. Workflows & Procedures
1. **Belief Representation**: Represent beliefs as probabilistic propositions with confidence $c \in [0, 1]$ and emotional valence.
2. **Bayesian/Trust Modulation**: Update prior belief $P(B)$ when presented with report $R$ from source $S$ with perceived trustworthiness $T(S)$.
3. **Memory Attenuation**: Apply power-law or exponential forgetting curves to transient news items while consolidating emotionally salient events.

## 4. Technical References
- *OCC Model of Emotions* (Ortony, Clore, & Collins, 1988).
- *Social Epistemology* (Goldman, 1999).
- Ebbinghaus Forgetting Curve formulations.

## 5. Validation Criteria
- Heterogeneous response: identical reports produce diverse belief updates across different agents.
- Forgetting curve removes transient trivia while retaining critical life shocks.
