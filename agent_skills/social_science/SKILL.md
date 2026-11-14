---
name: saltbor-social-science
description: Social norms, graduated sanctions, Ostrom CPR governance, conflict escalation, traditions, and desuetudo.
---

# SKILL: Computational Social Science, Norm Evolution & Institutional Dynamics

## 1. Objetivo
Modelar con fidelidad sociológica la emergencia, formalización, aplicación y decadencia de normas sociales, la gestión colectiva de bienes comunes según los principios de Elinor Ostrom, y la dinámica de conflictos intergrupales sin imponer juicios morales o armonías predeterminadas.

## 2. Cuándo Utilizarla
- Al programar reglas de convivencia comunitaria, turnos de riego, faenas o prácticas de mercado.
- Al implementar sanciones graduales frente al oportunismo (*free-riding*).
- Al modelar recursos de uso común (pozos, trojas, caminos, bosques).
- Al analizar la decadencia de costumbres por falta de uso (*desuetudo*).

## 3. Instrucciones de Trabajo
1. **Los 8 Principios de Ostrom para Bienes Comunes (CPR)**:
   - 1: Límites claramente definidos (quién tiene derecho a extraer agua o leña).
   - 2: Coherencia entre reglas de extracción y condiciones locales.
   - 3: Arreglos de elección colectiva (los afectados participan en las modificaciones de reglas).
   - 4: Monitoreo activo de usuarios y del recurso.
   - 5: Sanciones graduadas frente a infracciones (amonestación $\rightarrow$ pérdida de turno $\rightarrow$ exclusión temporal $\rightarrow$ expulsión).
   - 6: Mecanismos rápidos y de bajo coste para la resolución de conflictos.
   - 7: Reconocimiento mínimo de derechos de organización por autoridades externas.
   - 8: Empresas anidadas para recursos interconectados.
2. **Dinámica de Sanciones Graduadas**:
   - Una primera infracción nunca debe castigarse con la máxima severidad. Iniciar con advertencia verbal (`VERBAL_ADMONITION`), escalar a ostracismo social (`SOCIAL_OSTRACISM`), multa económica (`ECONOMIC_FINE`), y finalmente exclusión comunitaria (`EXPULSION`).
3. **Decaimiento por Desuso (*Desuetudo*)**:
   - Las tradiciones culturales no son eternas. Si una norma o costumbre acumula ciclos prolongados sin ser practicada ni sancionada, su vitalidad decae paulatinamente hasta quedar inactiva o extinguida.
4. **Escalada de Conflictos No Forzada**:
   - Los conflictos pueden resolverse mediante mediación y pactos, estancarse o escalar hacia huelgas o confrontaciones según los recursos, intereses y relaciones de los involucrados.

## 4. Procedimientos y Métodos
- **Función de Adherencia a la Norma**:
  $$\text{Adherencia} = 0.40 \cdot \text{Legitimidad} + 0.35 \cdot \text{RigorSanción} + 0.25 \cdot \text{PresiónPares}$$
- **Decaimiento de Vitalidad de la Norma**:
  - Incrementar `dormant_ticks`.
  - Si `dormant_ticks > 192` (2 días sin práctica): $\text{Legitimidad} \leftarrow \max(0.05, \text{Legitimidad} - 0.03)$.
  - Si $\text{Legitimidad} \le 0.15$ y $\text{dormant_ticks} \ge 384$: La norma se marca `is_active = False` y se archiva por desuetudo.

## 5. Referencias y Repositorios Clave
- *Governing the Commons: The Evolution of Institutions for Collective Action* (Elinor Ostrom, 1990).
- *Institutions, Institutional Change and Economic Performance* (Douglass C. North).
- `saltbor/social/norms/norm_evolution.py`, `saltbor/social/resources/cpr_manager.py`.

## 6. Herramientas Requeridas
- `SocialNormEvolutionEngine`
- `CollectiveResourceManager`
- `IntergroupConflictEngine`
- Experimentos: `EXP_19_I`, `EXP_19_J`, `EXP_19_N`, `EXP_19_O`, `EXP_19_H`.

## 7. Criterios de Validación
- Validación en `EXP_19_I` (gestión sostenible de pozo de agua bajo monitoreo Ostrom).
- Validación en `EXP_19_J` (sobreexplotación y caída de stock por falta de monitoreo).
- Validación en `EXP_19_O` (extinción formal de costumbre patronal por desuetudo).

## 8. Limitaciones
- No confundir frecuencia estadística con norma formal: una conducta frecuente no es una norma a menos que exista expectativa compartida de cumplimiento y disposición a sancionar su infracción.
