---
name: saltbor-multi-agent
description: Multi-agent coordination, emergent collective structures, spontaneous organizations, and group dynamics.
---

# SKILL: Multi-Agent Systems & Emergent Organization

## 1. Objetivo
Diseñar, simular y analizar fenómenos emergentes derivados de la interacción de agentes autónomos: formación espontánea de colectivos, escisiones organizacionales, alianzas comerciales, redes de apoyo mutuo y dinámicas de grupo sin control centralizado.

## 2. Cuándo Utilizarla
- Al implementar nuevas formas de organización social o económica en SALTBOR.
- Al modelar negociaciones, disputas o acuerdos entre grupos de agentes.
- Al calibrar umbrales de confianza, afinidad o necesidad para la acción colectiva.
- Al depurar escisiones (*fission*), fusiones (*merger*) o disoluciones organizacionales.

## 3. Instrucciones de Trabajo
1. **Evitar la Creación Top-Down Forzada**:
   - Las organizaciones no deben crearse automáticamente por decreto del código. Deben requerir condiciones locales: proximidad geográfica, necesidades compartidas, confianza bilateral suficiente y capital inicial aportado por los propios agentes.
2. **Ciclo de Vida Organizacional Completo**:
   - Toda organización debe soportar su ciclo completo: `EMERGENT_FORMING` $\rightarrow$ `ACTIVE_STABLE` $\rightarrow$ `EXPANDING` / `FAC_TENSION` $\rightarrow$ `FISSION` / `DISSOLVED`.
3. **Roles y Asimetría Interna**:
   - Los colectivos deben soportar roles diferenciados: `LEADER`, `TREASURER`, `VOCAL`, `ACTIVE_MEMBER`, `PASSIVE_MEMBER`. Los líderes tienen mayor peso en la agenda, pero su legitimidad depende de la satisfacción comunitaria.
4. **Conservación Estricta de Recursos**:
   - En una escisión, la tesorería debe dividirse proporcionalmente según los aportes históricos de los miembros. En una fusión, las tesorerías se combinan exactamente. Cero fondos creados o destruidos.

## 4. Procedimientos y Métodos
- **Escaneo Espacial de Candidatos**:
  - Agrupar agentes co-ubicados con intereses comunes mediante clustering rápido.
  - Verificar que el promedio de confianza bilateral entre candidatos supere el umbral mínimo (e.g. $\text{Trust} \ge 0.55$).
- **Métrica de Cohesión Grupal**:
  $$\text{Cohesión} = \frac{\sum_{i \ne j} \text{Afinidad}(i, j)}{N(N-1)} \times \left(1.0 - \text{Tensión Interna}\right)$$
- **Mecanismo de Fisión Faccional**:
  - Si la tensión interna supera $0.70$ y la cohesión cae por debajo de $0.30$, el grupo se escinde en dos facciones independientes con sus propios estatutos y tesorería repartida.

## 5. Referencias y Repositorios Clave
- *Micromotives and Macrobehavior* (Thomas Schelling).
- *An Introduction to MultiAgent Systems* (Michael Wooldridge).
- *Governing the Commons* (Elinor Ostrom).
- `saltbor/social/organization/emergent_engine.py`

## 6. Herramientas Requeridas
- `EmergentOrganizationEngine`
- `CollectiveGovernanceEngine`
- Experimentos: `EXP_19_A`, `EXP_19_B`, `EXP_19_C`, `EXP_19_R`.

## 7. Criterios de Validación
- Validación en `EXP_19_A` (formación espontánea de asociación comercial con tesorería aportada por socios).
- Validación en `EXP_19_C` (escisión limpia con conservación exacta de tesorería: $\$30 + \$20 = \$50$).
- Cero creación de dinero ficticio.

## 8. Limitaciones
- No asumir que todos los agentes tienen información perfecta sobre los demás.
- No modelar lealtad grupal como un valor estático inmutable.
