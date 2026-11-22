# Feature Specification: PayTrace — evidencia de la recomendación

**Feature Branch**: `002-evidencia-recomendacion`

**Created**: 2026-11-22

**Status**: Draft

**Input**: User description: "Feature 002 sobre la feature 001 (specs/001-diagnostico-transferencias/spec.md). Escribila en español, sin stack ni decisiones técnicas. Origen: devolución del profe a la v2. Cambio: el diagnóstico suma un campo "evidencia de la recomendación" con los IDs de los eventos que respaldan la recomendación. En "cuenta incorrecta" y en "timeout con reversa" es la reversa del débito posterior al evento clave; en fondos insuficientes, timeout sin reversa y "no concluyente" (sin evento clave o con evidencia contradictoria) va vacío. En las respuestas sin diagnóstico ("en curso" y operación OK) no aparece. Lo que NO cambia: "eventos citados" sigue citando exactamente un evento, el que prueba la causa (constitución, principio I). Donde algo no esté decidido, dejá [NEEDS CLARIFICATION]. No commitees."

**Fuente**: devolución del profe a la v2. Esta feature extiende la feature 001
(`specs/001-diagnostico-transferencias/spec.md`); todo lo que esta spec no cambia sigue como está ahí.
Las referencias "001/FR-xx" remiten a los requisitos de esa spec.

## Contexto

En la feature 001 el diagnóstico tiene tres campos: causa, eventos citados y recomendación. Los
eventos citados prueban la **causa**, pero la **recomendación** a veces se apoya en otro evento del
trace que el analista tiene que ir a buscar por su cuenta. Por ejemplo, en "timeout con reversa" la
recomendación "El débito ya se devolvió: se puede reintentar la transferencia" depende de que el trace
tenga la reversa del débito después del rechazo, y en "cuenta incorrecta" la recomendación pide
confirmar que la reversa se acreditó. Hoy el diagnóstico no dice cuál es ese evento.

Esta feature suma un cuarto campo, **evidencia de la recomendación**: los IDs de los eventos del trace
que respaldan la recomendación. Así el analista puede verificar no solo por qué falló la operación,
sino también por qué se le recomienda ese próximo paso.

**Lo que no cambia**: "eventos citados" sigue citando exactamente un evento, el evento clave que prueba
la causa (constitución, principio I; 001/FR-019), y en "no concluyente" sigue sin eventos citados o con
los eventos en conflicto (001/FR-021, 001/FR-022). La evidencia de la recomendación es un campo aparte:
nunca reemplaza ni se suma a los eventos citados.

### Evidencia de la recomendación por caso

| Caso (según lo que ven las reglas) | Causa | Eventos citados | Evidencia de la recomendación |
|---|---|---|---|
| Fondos insuficientes | fondos insuficientes | rechazo en origen, código AM04 | vacía |
| Cuenta incorrecta | cuenta incorrecta | rechazo del banco destino, código AC01 | la reversa del débito posterior al evento clave (todas, si hay más de una; vacía si no hay ninguna) |
| Timeout con reversa | timeout | rechazo por timeout, código AB05 | la reversa del débito posterior al evento clave (todas, si hay más de una) |
| Timeout sin reversa | timeout | rechazo por timeout, código AB05 | vacía |
| No concluyente, sin evento clave (trace incompleto vencido o fallida sin evento clave) | no concluyente | ninguno | vacía |
| No concluyente, evidencia contradictoria | no concluyente | los eventos clave en conflicto | vacía |
| OK | — (no hay diagnóstico) | — | no aparece |
| Pendiente dentro del plazo ("en curso") | — (no hay diagnóstico) | — | no aparece |

"Vacía" quiere decir que el campo está en el diagnóstico pero no tiene ningún ID. "No aparece" quiere
decir que la respuesta no tiene el campo, igual que no tiene causa, eventos citados ni recomendación.

## Clarifications

### Session 2026-11-22

- Q: Si un trace tiene un único rechazo AC01 y ninguna reversa del débito posterior, ¿qué responde el diagnóstico? → A: Sigue siendo "cuenta incorrecta", con el mismo evento citado y la misma recomendación de 001, y la evidencia de la recomendación va vacía. No se agregan operaciones a los datos fijos: este caso se cubre con una prueba de las reglas sobre un trace armado para esa prueba.
- Q: Si el trace tiene dos o más reversas del débito después del evento clave, ¿qué va en la evidencia de la recomendación? → A: Se citan por su ID todas las reversas del débito posteriores al evento clave. No es evidencia contradictoria: la causa, los eventos citados y la recomendación no cambian. Tampoco se agregan operaciones a los datos fijos; se cubre con una prueba de las reglas.

## User Scenarios & Testing *(mandatory)*

### Historia de usuario 1 - Ver el evento que respalda la recomendación (Priority: P1)

El analista pide el diagnóstico de una operación fallida cuya recomendación depende de la reversa del
débito ("cuenta incorrecta" o "timeout con reversa") y, además de la causa y el evento que la prueba,
recibe el ID de la reversa del débito que respalda la recomendación.

**Why this priority**: es el cambio pedido en la devolución. Sin esto, el analista tiene que buscar a
mano en el trace el evento que justifica el próximo paso.

**Independent Test**: con el conjunto de evaluación cargado, pedir el diagnóstico de las 5 operaciones
de "cuenta incorrecta" y las 5 de "timeout con reversa", y verificar que la evidencia de la
recomendación es exactamente la reversa del débito de cada trace y que los eventos citados no cambian.

**Acceptance Scenarios**:

1. **Dado** una operación del caso "cuenta incorrecta", **Cuando** el analista pide el diagnóstico,
   **Entonces** la causa es "cuenta incorrecta", los eventos citados son exactamente un evento (el
   "rechazo del banco destino, código AC01"), la recomendación es la de la tabla de casos de 001 y la
   evidencia de la recomendación es exactamente un ID: el de la "reversa del débito" posterior a ese
   rechazo.
2. **Dado** una operación del caso "timeout con reversa", **Cuando** el analista pide el diagnóstico,
   **Entonces** la causa es "timeout", los eventos citados son exactamente un evento (el "rechazo por
   timeout, código AB05"), la recomendación es "El débito ya se devolvió: se puede reintentar la
   transferencia" y la evidencia de la recomendación es exactamente un ID: el de la "reversa del
   débito" posterior a ese rechazo.
3. **Dado** una operación de "cuenta incorrecta" o de "timeout con reversa", **Cuando** el analista
   pide el diagnóstico, **Entonces** el ID de la reversa del débito aparece solo en la evidencia de la
   recomendación y no en los eventos citados.

---

### Historia de usuario 2 - Evidencia de la recomendación vacía cuando no hay evento que la respalde (Priority: P1)

Cuando la recomendación no se apoya en ningún evento del trace aparte del evento clave, o cuando el
diagnóstico es "no concluyente", el diagnóstico trae el campo de evidencia de la recomendación vacío,
sin inventar un evento.

**Why this priority**: mantiene el principio "evidencia o nada" también para la recomendación: el
sistema no cita eventos que no respaldan lo que recomienda.

**Independent Test**: pedir el diagnóstico de las 5 operaciones de "fondos insuficientes", las 5 de
"timeout sin reversa" y las 5 de "trace incompleto" del conjunto de evaluación, y de las 3 operaciones
del archivo de casos borde, y verificar que todas traen la evidencia de la recomendación vacía y que el
resto del diagnóstico no cambia respecto de 001.

**Acceptance Scenarios**:

1. **Dado** una operación del caso "fondos insuficientes", **Cuando** el analista pide el diagnóstico,
   **Entonces** el diagnóstico tiene la causa, el evento citado y la recomendación de 001, y la
   evidencia de la recomendación está vacía.
2. **Dado** una operación del caso "timeout sin reversa", **Cuando** pide el diagnóstico, **Entonces**
   el diagnóstico tiene la causa "timeout", el evento citado y la recomendación de 001, y la evidencia
   de la recomendación está vacía.
3. **Dado** una operación del caso "trace incompleto" con el plazo de espera vencido, **Cuando** pide
   el diagnóstico, **Entonces** la causa es "no concluyente", no cita ningún evento, la recomendación es
   "Pedir los logs del proveedor desde el último evento conocido" y la evidencia de la recomendación
   está vacía.
4. **Dado** la operación fallida del archivo de casos borde sin ningún evento clave (orden enviada →
   débito en origen → reversa del débito), **Cuando** pide el diagnóstico, **Entonces** la causa es "no
   concluyente", no cita ningún evento y la evidencia de la recomendación está vacía, aunque el trace
   tenga una reversa del débito.
5. **Dado** la operación fallida del archivo de casos borde con dos eventos clave de códigos distintos
   (AC01 y AB05, seguidos de una reversa del débito), **Cuando** pide el diagnóstico, **Entonces** la
   causa es "no concluyente", cita exactamente esos dos eventos, la recomendación es "Evidencia
   contradictoria: revisar manualmente los eventos citados" y la evidencia de la recomendación está
   vacía, aunque el trace tenga una reversa del débito.
6. **Dado** la operación fallida del archivo de casos borde con dos rechazos por timeout AB05,
   **Cuando** pide el diagnóstico, **Entonces** la causa es "no concluyente", cita exactamente esos dos
   eventos y la evidencia de la recomendación está vacía.

---

### Historia de usuario 3 - Sin campo de evidencia cuando no hay diagnóstico (Priority: P2)

Cuando la operación es OK o está pendiente dentro del plazo, la respuesta sigue siendo un mensaje sin
diagnóstico, y tampoco incluye la evidencia de la recomendación.

**Why this priority**: confirma que el cambio no altera las respuestas sin diagnóstico de 001; ya están
cubiertas por 001 y solo hay que verificar que el nuevo campo no aparece.

**Independent Test**: pedir el diagnóstico de una operación OK y de las 2 operaciones del archivo de
prueba de plazo, y verificar que ninguna respuesta tiene el campo de evidencia de la recomendación.

**Acceptance Scenarios**:

1. **Dado** una operación del caso "OK", **Cuando** el analista pide el diagnóstico, **Entonces** el
   sistema muestra "La operación no tiene un fallo para investigar" y no muestra causa, eventos citados,
   recomendación ni evidencia de la recomendación.
2. **Dado** las operaciones pendientes del archivo de prueba de plazo (último evento 2 minutos y
   exactamente 10 minutos anterior a su hora de referencia), **Cuando** pide el diagnóstico,
   **Entonces** el sistema muestra "La operación sigue en curso" y no muestra causa, eventos citados,
   recomendación ni evidencia de la recomendación.

---

### Edge Cases

- **Reversa del débito anterior al evento clave**: no cuenta como evidencia de la recomendación; solo
  cuenta una reversa del débito posterior al evento clave. En "timeout" esto coincide con la regla de
  001 que distingue "con reversa" de "sin reversa".
- **Reversa del débito en un "no concluyente"** (casos borde sin evento clave y con evidencia
  contradictoria): la evidencia de la recomendación va vacía igual, porque no hay un evento clave
  único después del cual buscarla y la recomendación no depende de la reversa.
- **"Cuenta incorrecta" sin reversa del débito posterior al evento clave**: el generador no crea
  operaciones así y los datos fijos no las tienen, pero las reglas solo ven el trace. El diagnóstico
  sigue siendo "cuenta incorrecta", con el mismo evento citado y la misma recomendación, y la evidencia
  de la recomendación va vacía. Se cubre con una prueba de las reglas, sin agregar datos fijos.
- **Más de una reversa del débito posterior al evento clave** (en "cuenta incorrecta" o en "timeout"):
  el generador no crea operaciones así y los datos fijos no las tienen. La evidencia de la
  recomendación cita todas esas reversas por su ID; la causa, los eventos citados y la recomendación no
  cambian. Se cubre con una prueba de las reglas, sin agregar datos fijos.
- **Pedir el diagnóstico varias veces**: la misma operación, con la misma hora de referencia, da
  siempre la misma evidencia de la recomendación, igual que los demás campos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (modifica 001/FR-017): El diagnóstico DEBE tener cuatro campos: causa, eventos citados
  (por ID de evento), recomendación y evidencia de la recomendación (por ID de evento).
- **FR-002**: La evidencia de la recomendación DEBE ser una lista de IDs de eventos del trace de la
  operación, que puede estar vacía. Nunca incluye IDs de eventos de otra operación ni IDs que no estén
  en el trace.
- **FR-003**: Si la causa es "cuenta incorrecta", la evidencia de la recomendación DEBE contener los
  IDs de todas las reversas del débito posteriores al evento clave, y solo esos. Si no hay ninguna, DEBE
  estar vacía, y la causa, el evento citado y la recomendación siguen siendo los de 001.
- **FR-004**: Si la causa es "timeout" y el trace tiene al menos una reversa del débito posterior al
  evento clave (recomendación "El débito ya se devolvió: se puede reintentar la transferencia"), la
  evidencia de la recomendación DEBE contener los IDs de todas esas reversas, y solo esos.
- **FR-012**: Tener más de una reversa del débito posterior al evento clave NO DEBE tratarse como
  evidencia contradictoria: no cambia la causa, los eventos citados ni la recomendación.
- **FR-013**: Los traces de "cuenta incorrecta" sin reversa posterior y con más de una reversa
  posterior DEBEN cubrirse con pruebas de las reglas sobre traces armados para esas pruebas; NO DEBEN
  agregarse operaciones a los datos fijos (conjunto de evaluación, archivo de prueba de plazo ni
  archivo de casos borde).
- **FR-005**: Si la causa es "fondos insuficientes", o es "timeout" sin reversa del débito posterior al
  evento clave, la evidencia de la recomendación DEBE estar vacía.
- **FR-006**: Si la causa es "no concluyente", tanto sin ningún evento clave (001/FR-021) como con
  evidencia contradictoria (001/FR-022), la evidencia de la recomendación DEBE estar vacía, aunque el
  trace tenga una reversa del débito.
- **FR-007** (amplía 001/FR-023 y 001/FR-024): Si la operación es OK o está pendiente dentro del plazo
  de espera, la respuesta NO DEBE incluir el campo de evidencia de la recomendación, igual que no
  incluye causa, eventos citados ni recomendación.
- **FR-008**: Una reversa del débito anterior al evento clave NO DEBE contarse como evidencia de la
  recomendación.
- **FR-009** (no cambia 001/FR-019, 001/FR-021, 001/FR-022): Los eventos citados DEBEN seguir siendo
  exactamente los de 001: un solo evento, el evento clave, cuando se nombra una causa; ninguno en "no
  concluyente" sin evento clave; los eventos clave en conflicto en "no concluyente" con evidencia
  contradictoria. El ID de la reversa del débito NUNCA aparece en los eventos citados.
- **FR-010** (no cambia 001/FR-018, 001/FR-020): La causa y la recomendación DEBEN seguir siendo
  exactamente las de 001 para cada trace; esta feature solo agrega el campo de evidencia de la
  recomendación.
- **FR-011** (amplía 001/FR-016 y 001/FR-027): La evidencia de la recomendación DEBE decidirse con las
  mismas reglas fijas que el resto del diagnóstico, solo a partir del trace, el estado y la hora de
  referencia, sin conocer el caso, y DEBE ser determinista: la misma operación con la misma hora de
  referencia da siempre la misma evidencia de la recomendación.

### Key Entities *(include if feature involves data)*

- **Diagnóstico** (modifica la entidad de 001): respuesta a un pedido del analista con cuatro campos:
  causa, eventos citados, recomendación y evidencia de la recomendación. Las respuestas sin diagnóstico
  ("La operación no tiene un fallo para investigar" y "La operación sigue en curso") no tienen ninguno
  de los cuatro.
- **Evidencia de la recomendación**: lista, posiblemente vacía, de IDs de eventos del trace que
  respaldan la recomendación. Es distinta de los eventos citados: estos prueban la causa; aquella
  respalda el próximo paso recomendado.
- **Reversa del débito**: evento del trace que devuelve el débito en origen. Respalda la recomendación
  solo cuando es posterior al evento clave y la causa es "cuenta incorrecta" o "timeout".

Las demás entidades (operación, evento, evento clave, trace, caso, conjunto de evaluación, archivo de
prueba de plazo, archivo de casos borde, hora de referencia) siguen como en 001.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El **100 %** de las 10 operaciones de "cuenta incorrecta" y "timeout con reversa" del
  conjunto de evaluación recibe una evidencia de la recomendación con exactamente un ID: el de la
  reversa del débito posterior al evento clave de su trace.
- **SC-002**: El **100 %** de las 15 operaciones de "fondos insuficientes", "timeout sin reversa" y
  "trace incompleto" del conjunto de evaluación, y de las 3 del archivo de casos borde, recibe la
  evidencia de la recomendación vacía.
- **SC-003**: El **0 %** de las respuestas sin diagnóstico (operación OK y las 2 operaciones del
  archivo de prueba de plazo) incluye el campo de evidencia de la recomendación.
- **SC-004**: Los criterios SC-002, SC-003 y SC-004 de 001 se siguen cumpliendo al **100 %**: mismos
  eventos citados, mismas causas y mismos "no concluyente" que antes del cambio, en las 25 operaciones
  del conjunto de evaluación.
- **SC-005**: Pedir **5 veces** el diagnóstico de cada operación del conjunto de evaluación da la misma
  evidencia de la recomendación las 5 veces en el **100 %** de las operaciones.
- **SC-006**: Los tiempos de respuesta de 001 (SC-005 y SC-006 de 001, ≤ 2 segundos en al menos el
  95 % de 125 mediciones) se siguen cumpliendo con el campo nuevo.

## Assumptions

- Todo lo que esta spec no menciona (búsqueda, lista, trace, generación, datos fijos, plazo de espera,
  textos) sigue igual que en la feature 001.
- La evidencia de la recomendación se muestra donde ya se muestra el diagnóstico (la misma respuesta de
  la API); no hay pantallas nuevas.
- En "cuenta incorrecta" y "timeout con reversa", los datos fijos y las operaciones generadas tienen
  exactamente una reversa del débito, y es posterior al evento clave (tabla de casos de 001). Los
  traces que no cumplen esto quedan en los Edge Cases.
- No hay datos fijos nuevos: el conjunto de evaluación y el archivo de casos borde de 001 ya cubren
  los valores del campo con un ID y vacío, y los traces de los Edge Cases se cubren con pruebas de las
  reglas (FR-013).
- El campo se llama "evidencia de la recomendación" en el lenguaje del analista; su nombre exacto en la
  respuesta se decide en el plan.
- La constitución no cambia: el principio I habla de la evidencia de la causa, que sigue igual; la
  evidencia de la recomendación aplica el mismo criterio ("evidencia o nada") a la recomendación.
