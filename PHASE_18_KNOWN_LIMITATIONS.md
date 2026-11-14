# SALTBOR FASE 1.8: LIMITACIONES CONOCIDAS Y ALCANCE CIENTÍFICO
## Fronteras Computacionales, Simplificaciones del Modelo y Advertencias Metodológicas

**Fecha:** 13 de Noviembre de 2026  
**Documento de Honestidad Científica y Transparencia Metodológica**  

---

## 1. LIMITACIONES COMPUTACIONALES Y DE ESCALA

1. **Crecimiento Superlineal en Simulación Total ($\ge 1.000$ Agentes)**:
   - Cuando la población simulada con resolución completa supera los 1.000 agentes simultáneos en un único hilo, la latencia por tick se aproxima a $\sim 1.000$ ms (1 tick por segundo).
   - **Solución arquitectónica:** Para poblaciones de $10.000$ o más habitantes, la plataforma requiere la activación del sistema de Nivel de Detalle (LOD) de la Fase 1.4, donde los agentes lejanos o fuera del campo visual del observador ejecutan biorritmos estadísticos agregados (0.75 µs por agente) en lugar de ruteo cinemático continuo.
2. **Capacidad de Almacenamiento del Grafo Causal**:
   - El DAG causal almacena un histórico de eventos con causas y efectos. En simulaciones longitudinales extensas ($>50.000$ ticks), el grafo sin podar acumularía millones de nodos.
   - **Mitigación:** Se ha establecido un límite de ventana deslizante de 10.000 nodos prioritarios en memoria, archivando eventos antiguos en SQLite.
3. **Caché de Ruteo A\***:
   - Si se introducen cientos de bloqueos dinámicos simultáneos, las subredes en caché deben invalidarse, lo que temporalmente eleva la latencia de cálculo de rutas hasta en un 25%.

---

## 2. SIMPLIFICACIONES ESPACIALES Y URBANAS

1. **Navegación Interior en Inmuebles**:
   - Dentro de un `PlaceProfile` (e.g., Centro Comercial Metrocentro o Mercado Central), la presencia de los individuos se modela como pertenencia al aforo del lugar (`current_occupants`), con coordenadas ancladas al centroide del polígono del edificio.
   - **No se simula malla 3D de pasillos interiores ni habitaciones individuales.** La arquitectura jerárquica de 8 niveles modela la capacidad, inventario y horarios, pero no la cinemática de caminar entre pasillos o estantes.
2. **Tráfico Vehicular Agregado vs. Microsimulación**:
   - Los vehículos y autobuses se modelan como agentes cinemáticos que siguen la polilínea vial de OpenStreetMap con velocidades adecuadas a su modo (20 km/h para autobús urbano).
   - **No es un microsimulador de tráfico estilo SUMO:** No se modelan fases de semáforos en cada intersección, cambios de carril ni distancias de frenado entre parachoques.
3. **Completitud de Datos OSM en Zonas Rurales**:
   - Mientras que el Centro Histórico de San Salvador y Santa Tecla cuentan con un mapeo detallado de huellas de edificios y comercios, las zonas rurales y asentamientos precarios periféricos poseen menor densidad de información en OpenStreetMap, recurriendo a extrapolación topológica.

---

## 3. LÍMITES ECONÓMICOS Y FINANCIEROS

1. **Economía de Escala Local vs. Macroeconomía Compleja**:
   - El motor económico modela con rigor la microeconomía cotidiana salvadoreña: jornales, salarios, fiado en tiendas de barrio, remesas familiares y círculos solidarios de ahorro (*cuchubales*).
   - **No incluye instrumentos financieros macroeconómicos complejos:** No se modelan derivados financieros, curvas de rendimiento de bonos soberanos ni políticas de encaje legal bancario.
2. **Conservación Contable Rigurosa**:
   - Todo dinero debe provenir de saldos iniciales, salarios o remesas registradas. El sistema no permite "crear dinero" de la nada para resolver déficit de los agentes, lo que en situaciones extremas de desempleo prolongado puede inducir pobreza crítica emergente que requiere intervención comunitaria (ADESCO) o gubernamental.

---

## 4. ADVERTENCIAS DE SALUD Y EPIDEMIOLOGÍA

1. **Modelo Conductual y Fisiológico, NO Diagnóstico Clínico**:
   - Las enfermedades modeladas en `HealthEngine` (infecciones respiratorias, enfermedades diarreicas agudas, dengue, fatiga por calor) son **abstracciones operativas para la toma de decisiones y alteración de movilidad cotidiana**.
   - **Bajo ninguna circunstancia deben interpretarse como diagnósticos médicos reales, pronósticos clínicos ni proyecciones epidemiológicas validadas para salud pública.**
   - Las tasas de recuperación dependen de descanso, nutrición y visitas a la clínica comunal simulada, pero no modelan farmacocinética ni interacciones moleculares.

---

## 5. CONCLUSIÓN

Hacer explícitas estas limitaciones forma parte del compromiso de SALTBOR con la **honestidad y la excelencia científica**. La plataforma no pretende simular cada molécula del universo físico, sino construir un modelo matemáticamente consistente, causalmente trazable y culturalmente verídico de la vida humana y comunitaria en El Salvador.
