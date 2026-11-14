---
name: saltbor-economics
description: Economic conservation, fiado credit, business solvency, inequality metrics (Gini, Palma), and cuchubales.
---

# SKILL: Computational Economics, Accounting Conservation & Inequality Metrics

## 1. Objetivo
Modelar la economía comunitaria y de mercado de SALTBOR bajo estricta conservación contable, instituciones crediticias informales salvadoreñas (*fiado*, *cuchubales*), ciclo de vida de micronegocios y medición multidimensional de la estratificación y movilidad social.

## 2. Cuándo Utilizarla
- Al implementar transacciones monetarias, cuotas asociativas o pagos de salarios.
- Al modelar negocios familiares (tiendas, pupuserías, talleres, puestos de mercado).
- Al calcular coeficientes de desigualdad (Gini de ingresos, Gini de patrimonio, ratio de Palma).
- Al implementar círculos de ahorro y crédito rotativo (*cuchubales*).

## 3. Instrucciones de Trabajo
1. **Conservación Contable Absoluta (Zero Money from Air)**:
   - Todo ingreso debe tener una contrapartida exacta de gasto en otra entidad.
   - En compraventas: $\Delta \text{Dinero}_{\text{comprador}} = -P$, $\Delta \text{Dinero}_{\text{vendedor}} = +P$.
   - En cuotas de membresía: debitar de la billetera del socio y acreditar a la tesorería de la organización. Si el socio no tiene liquidez, la transacción falla; no generar saldo ficticio.
2. **Crédito Informal de Confianza (*El Fiado*)**:
   - En las tiendas y mercados rurales salvadoreños, el crédito cotidiano se otorga por confianza interpersonal, no por colateral bancario formal.
   - El límite de crédito fiado depende del historial de pago previo y del nivel de confianza bilateral (`trust`).
3. **Círculos de Ahorro Rotativo (*Cuchubales*)**:
   - Grupos de ayuda mutua donde $N$ miembros aportan una cuota fija semanal/mensual $C$. En cada turno, un miembro recibe el pozo acumulado $N \times C$, sustituyendo seguros y créditos bancarios inaccesibles.
4. **Métricas de Desigualdad Multidimensional**:
   - Calcular el coeficiente de Gini sobre ingresos y patrimonio ordenados en $O(N \log N)$.
   - Calcular la razón de Palma: proporción del ingreso total del decil superior (Top 10%) dividida entre la del 40% inferior (Bottom 40%).

## 4. Procedimientos y Métodos
- **Cálculo Vectorizado del Coeficiente de Gini**:
  Dado un vector ordenado de ingresos $y_1 \le y_2 \le \dots \le y_N$:
  $$G = \frac{2 \sum_{i=1}^N i \cdot y_i}{N \sum_{i=1}^N y_i} - \frac{N+1}{N}$$
- **Razón de Palma**:
  $$\text{Palma} = \frac{\sum_{i \in \text{D10}} y_i}{\sum_{i \in \text{Q1–Q4}} y_i}$$
- **Insolvencia Empresarial**:
  - Si un negocio acumula deudas superiores al valor de liquidación de su inventario durante más de 30 días, se declara en quiebra (`BANKRUPT`), liquida sus activos a precio de remate para saldar deudas y cierra ordenadamente.

## 5. Referencias y Repositorios Clave
- *Capital in the Twenty-First Century* (Thomas Piketty, sobre concentración patrimonial).
- *The Palma Proposition* (José Gabriel Palma, sobre dinámicas del decil superior vs base piramidal).
- `saltbor/social/stratification/mobility_engine.py`, `saltbor/social/salvadoran/community.py`.

## 6. Herramientas Requeridas
- `SocialStratificationEngine`
- `ADESCOEngine` (Cuchubales)
- `BusinessRegistry`
- Experimentos: `EXP_19_K`, `EXP_19_L`, `EXP_19_U`.

## 7. Criterios de Validación
- Validación en `EXP_19_K` (quiebra de pupusería sin deuda impaga ni dinero desaparecido).
- Validación en `EXP_19_L` (Gini y Palma computados con transiciones de movilidad ascendente y descendente).
- Validación en `EXP_19_U` (ejecución exacta de cuchubal: 5 socios $\times$ \$15 = pozo de \$75 entregado).

## 8. Limitaciones
- No asumir tasas de interés constantes en economías informales.
- No reducir la posición socioeconómica de un individuo a una sola cifra salarial.
