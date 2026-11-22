# Checklist de validación del spec: PayTrace — evidencia de la recomendación

**Purpose**: Validar la calidad de los requisitos del spec de la 002 ("unit tests del texto") en tres
ejes: completitud, verificabilidad de los criterios y coherencia con la constitución v1.0.0 y con el
spec de la 001. No valida ninguna implementación.
**Created**: 2026-11-22
**Feature**: [spec.md](../spec.md)

**Note**: Generado con `/speckit-checklist`. Los ítems marcados `[x]` pasan contra el spec tal como
quedó después de las clarificaciones de la sesión 2026-11-22. Los que no pasaron en la primera
corrida llevan debajo el hallazgo y cómo se resolvió.

## Completitud de requisitos

- [x] CHK001 - ¿Están completas las secciones obligatorias del template (User Scenarios, Requirements, Success Criteria) y sin marcadores [NEEDS CLARIFICATION] pendientes? [Completeness]
- [x] CHK002 - ¿Está definido el valor de la evidencia de la recomendación para cada resultado posible del diagnóstico de 001 (las cuatro causas con trace completo, los dos "no concluyente", OK y "en curso")? [Completeness, Spec §Evidencia de la recomendación por caso, §FR-003–FR-007]
- [x] CHK003 - ¿Está definida la diferencia entre campo "vacío" y campo que "no aparece"? [Completeness, Spec §Contexto, §FR-007]
- [x] CHK004 - ¿Está definido qué eventos pueden aparecer en la evidencia de la recomendación (solo eventos del trace de la misma operación)? [Completeness, Spec §FR-002]
- [x] CHK005 - ¿Está definido el orden de los IDs cuando la evidencia de la recomendación tiene más de una reversa? [Gap, Spec §FR-003, §FR-004, §FR-011]
  - Hallazgo: la clarificación Q2 dice que se citan todas las reversas posteriores, pero no en qué orden. Como el campo es una lista y FR-011 exige que el resultado sea siempre el mismo, el orden debería estar fijado (p. ej. el orden del trace, del más antiguo al más nuevo, como en 001/FR-014). Tampoco se fija el orden de los eventos en conflicto en 001/FR-022, así que conviene decidirlo para los dos campos.
  - Resuelto 2026-11-22: los IDs van en el orden del trace, del más antiguo al más nuevo (FR-002, Clarifications, tabla por caso). El orden de los eventos en conflicto de 001/FR-022 queda fuera de esta feature.
- [x] CHK006 - ¿Están definidos los atributos de la entidad Diagnóstico con el campo nuevo, y la relación entre evidencia de la recomendación y eventos citados? [Completeness, Spec §Key Entities]

## Claridad de requisitos

- [x] CHK007 - ¿Está definido con precisión qué reversa cuenta (solo la posterior al evento clave) y qué pasa con una reversa anterior? [Clarity, Spec §FR-008, §Edge Cases]
- [x] CHK008 - ¿Está claro que la reversa del débito nunca entra en los eventos citados? [Clarity, Spec §FR-009, §US1 escenario 3]
- [x] CHK009 - ¿Está claro que más de una reversa posterior no es evidencia contradictoria? [Clarity, Spec §FR-012, §Clarifications]
- [x] CHK010 - ¿Están numerados los requisitos en orden, de modo que se puedan referenciar sin confusión? [Traceability, Spec §Functional Requirements]
  - Hallazgo: FR-012 y FR-013 quedaron entre FR-004 y FR-005, porque se agregaron después de la clarificación. No cambia el contenido, pero conviene moverlos al final de la lista (sin renumerar, para no romper referencias).
  - Resuelto 2026-11-22: FR-012 y FR-013 se movieron al final de la lista, sin renumerar.
- [x] CHK011 - ¿Es FR-013 un requisito del sistema o una decisión sobre cómo se prueba? [Clarity, Spec §FR-013]
  - Hallazgo: FR-013 dice cómo se cubren dos casos ("pruebas de las reglas sobre traces armados") y prohíbe tocar los datos fijos. Lo segundo es un requisito sobre los datos; lo primero es una decisión de prueba que encaja mejor en Assumptions o en el plan. Propuesta: dejar en FR-013 solo "NO DEBEN agregarse operaciones a los datos fijos" y pasar el "cómo se prueba" a Assumptions.
  - Resuelto 2026-11-22: FR-013 quedó solo como "NO DEBE agregar operaciones a los datos fijos"; cómo se prueban los dos casos pasó a Assumptions.

## Coherencia entre requisitos

- [x] CHK012 - ¿Coinciden la tabla "Evidencia de la recomendación por caso", los FR-003 a FR-008 y los Edge Cases, incluidas las dos clarificaciones? [Consistency, Spec §Contexto, §FR-003–FR-008, §Edge Cases]
- [x] CHK013 - ¿Es coherente la descripción de la historia 2 con el caso "cuenta incorrecta" sin reversa? [Consistency, Spec §US2, §Clarifications Q1]
  - Hallazgo: la historia 2 dice que la evidencia va vacía "cuando la recomendación no se apoya en ningún evento del trace aparte del evento clave, o cuando el diagnóstico es 'no concluyente'". Después de Q1 también va vacía cuando la recomendación sí se apoya en una reversa, pero el trace no la tiene ("cuenta incorrecta" sin reversa). Propuesta: "cuando no hay ningún evento del trace, aparte del evento clave, que respalde la recomendación".
  - Resuelto 2026-11-22: la historia 2 dice "cuando no hay ningún evento del trace, aparte del evento clave, que respalde la recomendación".
- [x] CHK014 - ¿Coinciden los números de SC-001 y SC-002 (10 + 15 = 25 del conjunto de evaluación, más 3 de casos borde) con los datos fijos de 001 (001/FR-007, 001/FR-029)? [Consistency, Spec §SC-001, §SC-002]
- [x] CHK015 - ¿Es coherente el supuesto "exactamente una reversa posterior en los datos fijos y las generadas" con la tabla de casos y los casos borde de 001? [Consistency, Spec §Assumptions, 001 §Casos simulados, 001/FR-029]

## Coherencia con el spec de la 001

- [x] CHK016 - ¿Marca el spec cada requisito de 001 que modifica, amplía o mantiene (001/FR-016, FR-017, FR-018–FR-024, FR-027)? [Consistency, Spec §FR-001, §FR-007, §FR-009–FR-011]
- [x] CHK017 - ¿Deja intactos causa, eventos citados y recomendación de 001 para todos los traces, incluidos los casos borde? [Consistency, Spec §FR-009, §FR-010, §SC-004]
- [x] CHK018 - ¿Es coherente la condición "reversa posterior al evento clave" de FR-004 con la regla de 001 que distingue timeout con y sin reversa (001/FR-020, 001 §Assumptions)? [Consistency, Spec §FR-004, §Edge Cases]
- [x] CHK019 - ¿Está declarado que todo lo no mencionado sigue como en 001 (búsqueda, lista, generación, datos fijos, plazo, textos)? [Assumption, Spec §Fuente, §Assumptions]
- [x] CHK020 - ¿Está documentado que cubrir los casos borde nuevos sin datos fijos se aparta del criterio de 001 (que usó el archivo de casos borde), y que es una decisión explícita? [Consistency, Spec §Clarifications, §FR-013, 001 §Clarifications]
- [x] CHK021 - ¿Queda trazable el origen del cambio, como en 001 lo es el PRD? [Traceability, Spec §Fuente]
  - Hallazgo: la fuente es "devolución del profe a la v2", sin fecha ni texto. En 001 cada requisito remite a un RF/AC del PRD. Propuesta: anotar la fecha de la devolución y citar o resumir su pedido en Fuente, para que se pueda revisar si el spec responde a lo que se pidió.
  - Resuelto 2026-11-22: Fuente dice "devolución del profe a la entrega del M3 (v2), noviembre 2026: citar la reversa como evidencia de la recomendación".

## Calidad de criterios de aceptación (verificabilidad)

- [x] CHK022 - ¿Cada valor del campo (un ID, vacío, no aparece) tiene al menos un escenario Dado/Cuando/Entonces con resultado exacto? [Measurability, Spec §US1, §US2, §US3]
- [x] CHK023 - ¿Tienen escenario de aceptación los dos casos de las clarificaciones ("cuenta incorrecta" sin reversa y más de una reversa posterior)? [Coverage, Gap, Spec §Clarifications, §Edge Cases, §FR-013]
  - Hallazgo: están en Edge Cases y FR-013 dice que se cubren con pruebas de las reglas, pero no tienen escenario Dado/Cuando/Entonces ni criterio de éxito. En 001 el mismo hallazgo (001/CHK022) se resolvió con escenarios propios. Propuesta: sumar dos escenarios (p. ej. a la historia 1 o una historia nueva) con el trace exacto de cada uno y el resultado esperado, incluido el orden de los IDs (ver CHK005).
  - Resuelto 2026-11-22: historia 1, escenarios 4 ("cuenta incorrecta" sin reversa → evidencia vacía) y 5 (dos reversas → las dos, en el orden del trace), sobre traces armados para la prueba; Edge Cases remite a ellos.
- [x] CHK024 - ¿Son medibles SC-001 a SC-003, con cantidad de operaciones y porcentaje esperado? [Measurability, Spec §SC-001–SC-003]
- [x] CHK025 - ¿Está definida la operación OK que usa SC-003 y el Independent Test de la historia 3? [Measurability, Gap, Spec §SC-003, §US3]
  - Hallazgo: el conjunto de evaluación no tiene operaciones OK. En 001 esto se resolvió diciendo que la OK se carga directamente para la prueba y, con la historia 4, se prueba además con una generada (001/US2, 001 §Clarifications). Acá "una operación OK" no dice de dónde sale. Propuesta: remitir a la misma decisión de 001.
  - Resuelto 2026-11-22: la operación OK se carga directamente para la prueba, como en 001 (historia 3, SC-003, Clarifications).
- [x] CHK026 - ¿Es medible el determinismo del campo nuevo con un procedimiento concreto (5 pedidos por operación, 100 %)? [Measurability, Spec §SC-005]
- [x] CHK027 - ¿Es medible SC-006, reutilizando la definición de mediciones de 001 (125 mediciones, tiempo del servidor)? [Measurability, Spec §SC-006, 001 §SC-005, §SC-006]

## Coherencia con la constitución v1.0.0

- [x] CHK028 - Principio I: ¿sigue exigiendo el spec exactamente un evento clave citado por cada causa nombrada, sin sumar la reversa a los eventos citados? [Constitución §I, Spec §FR-009]
- [x] CHK029 - Principio I: ¿sigue el "no concluyente" sin causa, sin eventos citados o con los eventos en conflicto, y sin evidencia de la recomendación que sugiera una causa? [Constitución §I, Spec §FR-006, §FR-009]
- [x] CHK030 - Principio I: ¿sigue sin diagnosticar operaciones OK, tampoco a través del campo nuevo? [Constitución §I, Spec §FR-007]
- [x] CHK031 - Principio II: ¿exige el spec que el campo nuevo salga de reglas fijas, sin conocer el caso, con la hora de referencia como dato y con el mismo resultado para la misma entrada? [Constitución §II, Spec §FR-011]
  - Nota: el principio II enumera "misma causa, mismos eventos citados y misma recomendación"; FR-011 lo extiende al campo nuevo sin necesidad de enmendar la constitución (Spec §Assumptions).
- [x] CHK032 - Principio III: ¿están los requisitos del campo nuevo escritos como escenarios que se pueden traducir a tests antes de implementar? [Constitución §III, Spec §US1–US3]
- [x] CHK033 - Principio IV: ¿sigue el spec sin datos reales ni conexiones reales, y sin agregar datos fijos nuevos? [Constitución §IV, Spec §Assumptions, §FR-013]
- [x] CHK034 - ¿Está el spec libre de decisiones de stack (el nombre exacto del campo queda para el plan)? [Constitución §Flujo de desarrollo, Spec §Assumptions]

## Notes

- Primera corrida (2026-11-22): 27/34 ítems pasaban.
- Después de resolver los hallazgos (2026-11-22): 34/34. CHK005, CHK023 y CHK025 se resolvieron con
  decisiones de la autora del spec; CHK010, CHK011, CHK013 y CHK021, con las propuestas del checklist.
  El spec queda listo para `/speckit-plan`.
- Hallazgos de la primera corrida, por impacto (todos resueltos):
  - CHK005 (orden de los IDs) y CHK023 (escenarios para los casos de las clarificaciones): afectan la
    verificabilidad y el principio III; conviene resolverlos antes de `/speckit-plan`.
  - CHK025 (de dónde sale la operación OK) y CHK013 (texto de la historia 2): correcciones chicas.
  - CHK010 (orden de FR), CHK011 (FR-013 mezcla requisito y prueba) y CHK021 (fuente): forma y
    trazabilidad.
