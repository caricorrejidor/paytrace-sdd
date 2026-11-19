# Checklist de validación del spec: PayTrace — diagnóstico de transferencias fallidas o pendientes

**Purpose**: Validar la calidad de los requisitos del spec ("unit tests del texto") en tres ejes:
completitud, verificabilidad de los criterios y coherencia con la constitución v1.0.0. No valida
ninguna implementación.
**Created**: 2026-11-18
**Feature**: [spec.md](../spec.md)

**Note**: Generado con `/speckit-checklist`. Los ítems marcados `[x]` pasan contra el spec tal
como quedó después de `/speckit-clarify` (sesión 2026-11-18). Los que quedan `[ ]` llevan el
hallazgo debajo.

## Completitud de requisitos

- [x] CHK001 - ¿Están completas todas las secciones obligatorias del template (User Scenarios, Requirements, Success Criteria) y sin marcadores [NEEDS CLARIFICATION]? [Completeness]
- [x] CHK002 - ¿Está definido el resultado del diagnóstico para cada uno de los seis casos de la tabla (causa, evento clave, recomendación o mensaje sin diagnóstico)? [Completeness, Spec §Casos simulados, §FR-018–FR-024]
- [x] CHK003 - ¿Están definidos los atributos de Operación y Evento (ID, estado, momento, tipo, emisor, código de motivo) necesarios para que las reglas decidan? [Completeness, Spec §FR-005, §FR-006, §Key Entities]
- [x] CHK004 - ¿Está definido qué pasa con las operaciones generadas al reiniciar la aplicación? [Completeness, Spec §FR-009]
- [x] CHK005 - ¿Está definida la hora de referencia para cada grupo de operaciones (conjunto de evaluación, archivo de prueba de plazo, generadas)? [Completeness, Spec §FR-026]
- [x] CHK006 - ¿Está definido el resultado para una operación **fallida** sin ningún evento clave cuyo último evento está dentro de los 10 minutos de la hora de referencia? [Gap, Spec §FR-021, §FR-024]
  - Hallazgo: FR-021 condiciona el "no concluyente" a que "ya pasó el plazo de espera", y FR-024 ("sigue en curso") aplica solo a pendientes. Para una fallida sin evento clave dentro del plazo no hay respuesta definida. El plazo debería aplicar solo a pendientes, o hay que decir qué pasa en este caso.
  - Resuelto 2026-11-18: una fallida sin evento clave es "no concluyente" enseguida; el plazo aplica solo a pendientes (FR-021, FR-025).
- [x] CHK007 - ¿Está definido si las operaciones del archivo de prueba de plazo se pueden buscar, aparecen en la lista y ocupan IDs, y cuáles son esos IDs? [Gap, Spec §FR-008, §FR-013, §Key Entities]
  - Hallazgo: Key Entities dice que una Operación puede venir del archivo de prueba de plazo, pero FR-013 lista solo el conjunto de evaluación y las generadas. Tampoco se dice si sus IDs cuentan para el "siguiente ID libre" (FR-003).
  - Resuelto 2026-11-18: todos los datos fijos se cargan al inicio, se buscan, se listan y ocupan IDs (FR-030, FR-013).
- [x] CHK008 - ¿Está definido que **ninguna** operación (tampoco las fijas) usa IDs `OP-9xxx`, como dice el PRD? [Gap, Spec §FR-002, §FR-003]
  - Hallazgo: el PRD (glosario, "Operación") lo dice para todas las operaciones. El spec lo exige solo para las generadas (FR-003), y AC-04 depende de que `OP-9999` no exista nunca.
  - Resuelto 2026-11-18: ninguna operación, fija o generada, usa `OP-9xxx` (FR-002).

## Claridad de requisitos

- [x] CHK009 - ¿Está claro si el estado de la operación es un dato de entrada de las reglas o se deduce del trace? [Ambiguity, Spec §FR-016, §FR-023, §FR-024]
  - Hallazgo: FR-016 dice que las reglas deciden "solo a partir del trace (y de la hora de referencia)", pero FR-023/FR-024 se disparan por el estado ("si la operación es OK", "si está pendiente"). Tampoco se dice qué pasa si estado y trace no coinciden (p. ej. estado OK sin acreditación en destino).
  - Resuelto 2026-11-18: las reglas usan trace, estado y hora de referencia (FR-016, FR-026); la coincidencia estado-trace queda como supuesto (Assumptions).
- [x] CHK010 - ¿Está definido con precisión qué eventos cuentan como "evento clave" para las reglas, y si dos eventos clave del mismo código (p. ej. dos AB05) son evidencia contradictoria? [Ambiguity, Spec §Casos simulados, §FR-022]
  - Hallazgo: el evento clave se define por caso ("el que prueba la causa"), pero las reglas no conocen el caso. Falta decir que, para las reglas, evento clave = rechazo con código AM04, AC01 o AB05, y si "más de un evento clave" incluye repetidos del mismo código. Tampoco queda claro si la "acreditación en destino" (en negrita en el caso OK) cuenta para la contradicción.
  - Resuelto 2026-11-18: evento clave = rechazo AM04 en origen, AC01 del banco destino o AB05 por timeout; más de uno, aunque repitan código, es contradictorio (FR-016, FR-022, Key Entities).
- [x] CHK011 - ¿Está definido el orden del trace cuando dos eventos tienen el mismo momento? [Ambiguity, Spec §FR-014]
  - Hallazgo: "orden cronológico" no decide los empates. Esto afecta FR-014 y la regla del timeout, que pide la reversa "después del rechazo" (FR-020).
  - Resuelto 2026-11-18: dentro de un trace los momentos son estrictamente crecientes (FR-031).
- [x] CHK012 - ¿Está claro qué significa "siguiente ID libre" (el menor libre o el siguiente al mayor existente)? [Ambiguity, Spec §FR-003]
  - Hallazgo: las dos lecturas cumplen AC-14, pero dan IDs distintos. Puede quedar como decisión del plan si se acepta que cualquiera de las dos es válida.
  - Resuelto 2026-11-18: siguiente ID libre = número siguiente al mayor ID existente (FR-003).
- [x] CHK013 - ¿Está cuantificado el límite del plazo de espera, incluido el caso borde de exactamente 10 minutos? [Clarity, Spec §FR-025, §Edge Cases]
- [x] CHK014 - ¿Están fijados de forma literal todos los textos que ve el analista, incluidas las dos recomendaciones nuevas de Clarifications? [Clarity, Spec §Assumptions, §FR-021, §FR-022]

## Coherencia entre requisitos

- [x] CHK015 - ¿Son coherentes FR-021 ("sin eventos citados") y FR-022 (cita los eventos en conflicto), separando claramente "sin evento clave" de "más de un evento clave"? [Consistency, Spec §FR-021, §FR-022, §Edge Cases]
- [x] CHK016 - ¿Coincide la tabla de US4 (estado, evento, último evento) con la tabla de casos simulados? [Consistency, Spec §US4, §Casos simulados]
- [x] CHK017 - ¿Coinciden los números del conjunto de evaluación (25 = 5 × 5 casos, 20 completos + 5 incompletos) entre FR-007, Key Entities y SC-002–SC-004? [Consistency]
- [x] CHK018 - ¿Es coherente el Independent Test de US2, que usa "una operación OK", con un conjunto de evaluación que no tiene operaciones OK? [Consistency, Spec §US2, §FR-007]
  - Hallazgo: la operación OK tiene que salir de una generación (US4). Conviene decirlo para que el test no dependa de un dato que no existe.
  - Resuelto 2026-11-18: la operación OK se genera con la historia 4 (US2, Independent Test).
- [x] CHK019 - ¿Está documentada la diferencia con el PRD (glosario: "eventos citados vacío si la causa es no concluyente") y justificada por la constitución? [Consistency, Spec §Edge Cases, §Clarifications]

## Calidad de criterios de aceptación (verificabilidad)

- [x] CHK020 - ¿Cada causa nombrada (AM04, AC01, AB05 con y sin reversa) tiene un escenario con causa, evento citado y recomendación exactos? [Measurability, Spec §US1]
- [x] CHK021 - ¿Los mensajes sin diagnóstico (OK, sigue en curso, no concluyente del trace incompleto) tienen escenarios que dicen qué se muestra y qué no? [Measurability, Spec §US2]
- [x] CHK022 - ¿Tienen escenario de aceptación y datos de prueba definidos la evidencia contradictoria (FR-022) y la fallida sin evento clave (FR-021)? [Coverage, Gap, Spec §FR-021, §FR-022]
  - Hallazgo: solo están en Edge Cases. El MVP no genera esas operaciones y no están en el conjunto de evaluación, así que no hay forma de verificarlas con los datos definidos. El principio III (test-first) necesita un escenario para escribir el test antes.
  - Resuelto 2026-11-18: escenarios 5 a 7 de US2 y archivo de casos borde (FR-029), que incluye una contradictoria con el mismo código repetido (dos AB05).
- [x] CHK023 - ¿Están completamente especificadas SC-005 y SC-006 (cuántas mediciones, desde qué acción hasta qué momento)? [Measurability, Spec §SC-005, §SC-006]
  - Hallazgo: "al menos el 95 % de las mediciones sobre el conjunto de evaluación" no dice cuántas mediciones son ni dónde empieza y termina cada una.
  - Resuelto 2026-11-18: 125 mediciones (5 por operación del conjunto de evaluación) con inicio y fin definidos (SC-005, SC-006).
- [x] CHK024 - ¿Es medible el determinismo con un procedimiento concreto (5 pedidos por operación, 100 %)? [Measurability, Spec §SC-007]
- [x] CHK025 - ¿Es medible SC-001, con el tamaño de la muestra, quién mide y los puntos de inicio y fin definidos? [Measurability, Spec §SC-001]

## Coherencia con la constitución v1.0.0

- [x] CHK026 - Principio I: ¿exige el spec citar exactamente un evento clave por ID para cada causa nombrada, y prohíbe nombrar causa sin él? [Constitución §I, Spec §FR-019]
- [x] CHK027 - Principio I: ¿responde el spec "no concluyente" sin causa cuando la evidencia no alcanza o es contradictoria, sin eventos citados si no hay ningún evento clave, y citando los eventos en conflicto si hay más de uno? [Constitución §I, Spec §FR-021, §FR-022]
- [x] CHK028 - Principio I: ¿prohíbe el spec diagnosticar operaciones OK? [Constitución §I, Spec §FR-023]
- [x] CHK029 - Principio II: ¿prohíbe el spec LLM y aleatoriedad, y exige el mismo resultado para la misma entrada? [Constitución §II, Spec §FR-027]
- [x] CHK030 - Principio II: ¿recibe la hora de referencia como dato y deja la lectura del reloj (para las generadas) fuera de las reglas? [Constitución §II, Spec §FR-026]
- [x] CHK031 - Principio III: ¿están escritos los requisitos de diagnóstico como escenarios Dado/Cuando/Entonces que se pueden traducir a tests antes de implementar? [Constitución §III, Spec §US1, §US2] (incluidos FR-021 y FR-022, ver CHK022)
- [x] CHK032 - Principio IV: ¿exige el spec datos 100 % simulados, sin conexiones reales y sin datos personales reales? [Constitución §IV, Spec §FR-028, §SC-008]
- [x] CHK033 - ¿Está el spec libre de decisiones de stack, que según la constitución corresponden a AGENTS.md y al plan? [Constitución §Flujo de desarrollo, Spec completo]

## Casos borde, alcance y supuestos

- [x] CHK034 - ¿Están definidos los casos borde de búsqueda (vacío, formato inválido, válido inexistente)? [Edge Case, Spec §FR-011, §FR-012]
- [x] CHK035 - ¿Están declarados de forma explícita los límites de alcance (sin login, sin unión de logs reales, sin reintentos, solo transferencias, sin paginación)? [Assumption, Spec §Assumptions]
- [x] CHK036 - ¿Está definido qué pasa cuando se agotan los IDs generables (rechazo de la generación con su mensaje literal y sin crear ninguna operación)? [Edge Case, Spec §Edge Cases, §FR-032]

## Notes

- Primera corrida (2026-11-18): 26/36 ítems pasaban.
- Después de resolver los hallazgos (2026-11-18): 36/36. CHK006, CHK009, CHK010 y CHK022 se
  resolvieron con decisiones de la autora del spec; CHK007, CHK008, CHK011, CHK012, CHK018 y CHK023,
  con propuestas aceptadas para revisión (ver spec §Clarifications).
