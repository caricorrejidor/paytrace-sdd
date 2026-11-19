# Feature Specification: PayTrace — diagnóstico de transferencias fallidas o pendientes

**Feature Branch**: `001-diagnostico-transferencias`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Generá el spec a partir del PRD en PRD.md. Escribilo en español. No incluyas stack, frameworks ni decisiones técnicas. No inventes: donde el PRD no decida algo, dejá un marcador [NEEDS CLARIFICATION]. No commitees."

**Fuente**: PRD-001 (`PRD.md`, 04/11/2026). Las referencias RF-xx, RNF-xx, OBJ-x y AC-xx remiten a ese documento.

## Contexto

Cuando una transferencia falla o queda pendiente, el analista de operaciones o soporte de pagos la
rastrea a mano por los logs de varios sistemas, cada uno con su propio ID. Un analista senior tarda
~20 min por caso y uno nuevo ~40 min (estimación de referencia, no medición); a veces no tiene
permisos para ver todos los logs, y dos analistas pueden llegar a causas distintas porque el
diagnóstico no siempre cita qué evento lo prueba.

PayTrace permite investigar la operación desde un solo lugar: un historial (trace) unificado y
**simulado** de la operación. Aplica reglas fijas al trace, nombra la causa citando el evento que la
prueba y recomienda el próximo paso. Si la evidencia no alcanza, responde "no concluyente". No
diagnostica operaciones sin fallo.

**Personas**:

- **Laura**, analista senior: quiere dejar de seguir el ID log por log y tener la causa con la
  evidencia a mano.
- **Nico**, analista nuevo, sin permisos para todos los logs: quiere llegar a la misma causa que
  Laura sin depender de su experiencia ni de pedir accesos.

### Casos simulados

Cada operación se genera a partir de uno de estos casos. Las reglas de diagnóstico **no** conocen el
caso: solo ven el trace, el estado y la hora de referencia. El **evento clave** es el que prueba la
causa. Para las reglas, un evento clave es únicamente un rechazo en origen con código AM04, un rechazo
del banco destino con código AC01 o un rechazo por timeout con código AB05; la acreditación en
destino del caso OK no cuenta como evento clave para las reglas.

| Caso | Estado | Trace simulado (evento clave en negrita) | Causa | Recomendación |
|---|---|---|---|---|
| OK | OK | Orden enviada → débito en origen → aceptación del proveedor → **acreditación en destino** | — (no se investiga) | — |
| Fondos insuficientes | Fallida | Orden enviada → **rechazo en origen, código AM04** | fondos insuficientes | Avisar al cliente que no tenía saldo. No se debitó nada |
| Cuenta incorrecta | Fallida | Orden enviada → débito en origen → **rechazo del banco destino, código AC01** → reversa del débito | cuenta incorrecta | Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó |
| Timeout con reversa | Fallida | Orden enviada → débito en origen → envío al proveedor → **rechazo por timeout, código AB05** (el proveedor informa que el banco destino no respondió a tiempo) → reversa del débito | timeout | El débito ya se devolvió: se puede reintentar la transferencia |
| Timeout sin reversa | Fallida | Orden enviada → débito en origen → envío al proveedor → **rechazo por timeout, código AB05** (el proveedor informa que el banco destino no respondió a tiempo) | timeout | El débito todavía no se devolvió: pedir la reversa antes de reintentar. Si se reintenta antes, se cobra dos veces |
| Trace incompleto | Pendiente | Orden enviada → débito en origen → (pasaron más de 10 minutos sin ningún evento más) | no concluyente | Pedir los logs del proveedor desde el último evento conocido |

Los códigos de motivo siguen ISO 20022 y el MVP usa solo tres: AM04 (fondos insuficientes), AC01
(la cuenta no existe en el banco destino) y AB05 (timeout del banco destino).

## Clarifications

### Session 2026-11-18

- Q: Con evidencia contradictoria (más de un evento clave), ¿se citan los eventos en conflicto? → A: Sí: cita por su ID todos los eventos clave en conflicto, sin nombrar causa, con la recomendación "Evidencia contradictoria: revisar manualmente los eventos citados".
- Q: ¿Qué recomendación lleva un "no concluyente" sin ningún evento clave que no viene del caso trace incompleto (p. ej. una fallida cuyo trace no encaja en ninguna regla)? → A: La misma para todo "no concluyente" sin evento clave: "Pedir los logs del proveedor desde el último evento conocido".
- Q: ¿Las operaciones generadas se conservan cuando la aplicación se reinicia? → A: No: existen solo mientras la aplicación está en uso; al reiniciar se pierden y quedan solo el conjunto de evaluación y el archivo de prueba de plazo.
- Q: ¿Qué hora de referencia usa cada grupo de operaciones? → A: Cada operación fija (conjunto de evaluación y archivo de prueba de plazo) trae su propia hora de referencia fija en los datos; para las operaciones generadas, la hora de referencia es el momento en que el analista pide el diagnóstico, tomado fuera de las reglas y pasado como dato.
- Q: ¿Qué responde una operación fallida sin ningún evento clave cuyo último evento está dentro de los 10 minutos? → A: "No concluyente" enseguida; el plazo de espera aplica solo a pendientes.
- Q: ¿Las reglas usan el estado de la operación o solo el trace? → A: Deciden con el trace, el estado y la hora de referencia, sin conocer el caso. Que el estado no coincida con el trace no ocurre con datos simulados (supuesto).
- Q: ¿Qué cuenta como evento clave para las reglas? → A: Solo el rechazo en origen con AM04, el rechazo del banco destino con AC01 y el rechazo por timeout con AB05. Más de un evento clave, aunque tengan el mismo código, es evidencia contradictoria.
- Q: ¿Cómo se verifican FR-021 (fallida sin evento clave) y FR-022 (evidencia contradictoria)? → A: Con escenarios de aceptación propios y un archivo fijo de casos borde, aparte del conjunto de evaluación, con una fallida sin evento clave y una fallida con dos eventos clave.
- Q: ¿Se cubre con datos fijos la evidencia contradictoria con el mismo código repetido? → A: Sí: el archivo de casos borde suma una tercera fallida con dos rechazos por timeout AB05 (orden enviada → débito en origen → envío al proveedor → rechazo AB05 → rechazo AB05), con su escenario en la historia 2.
- Q: ¿Los datos fijos aparte del conjunto de evaluación se buscan, se listan y ocupan IDs? → A: Sí: todos los datos fijos se cargan al iniciar, se pueden buscar y listar, y sus IDs cuentan como ocupados.
- Q: ¿Qué IDs están prohibidos? → A: Ninguna operación, fija o generada, usa un ID `OP-9xxx`.
- Q: ¿Cómo se ordenan dos eventos con el mismo momento? → A: No pueden existir: dentro de un trace, cada evento tiene un momento estrictamente posterior al anterior.
- Q: ¿Qué es "siguiente ID libre"? → A: El número siguiente al mayor ID existente.
- Q: ¿De dónde sale la operación OK de la prueba independiente de la historia 2? → A: Se genera con la historia 4, porque el conjunto de evaluación no tiene operaciones OK.
- Q: ¿Cuántas mediciones cuentan para SC-005 y SC-006? → A: 5 por cada una de las 25 operaciones del conjunto de evaluación (125 en total), desde el pedido del analista hasta que ve el resultado completo.

## User Scenarios & Testing *(mandatory)*

### Historia de usuario 1 - Diagnosticar una operación fallida con evidencia (Priority: P1)

El analista toma una operación fallida, pide el diagnóstico y recibe la causa, el único evento del
trace que la prueba (por su ID de evento) y la recomendación del próximo paso.

**Why this priority**: es el valor central del producto (OBJ-1, OBJ-2, OBJ-4). Sin esto PayTrace no
reemplaza la investigación manual.

**Independent Test**: con el conjunto de evaluación cargado, pedir el diagnóstico de cada una de las
20 operaciones con trace completo y verificar causa, evento citado y recomendación contra la tabla
de casos.

**Acceptance Scenarios** (AC-06, AC-07, AC-08):

1. **Dado** una operación del caso "fondos insuficientes", **Cuando** el analista pide el
   diagnóstico, **Entonces** la causa es exactamente "fondos insuficientes", cita un solo evento
   (el "rechazo en origen, código AM04" de ese trace) y la recomendación es la de la tabla para ese caso.
2. **Dado** una operación del caso "cuenta incorrecta", **Cuando** pide el diagnóstico, **Entonces**
   la causa es exactamente "cuenta incorrecta", cita un solo evento (el "rechazo del banco destino,
   código AC01") y la recomendación es la de la tabla para ese caso.
3. **Dado** una operación del caso "timeout con reversa", **Cuando** pide el diagnóstico,
   **Entonces** la causa es exactamente "timeout", cita un solo evento (el "rechazo por timeout,
   código AB05") y la recomendación es "El débito ya se devolvió: se puede reintentar la transferencia".
4. **Dado** una operación del caso "timeout sin reversa", **Cuando** pide el diagnóstico,
   **Entonces** la causa es exactamente "timeout", cita un solo evento (el "rechazo por timeout,
   código AB05") y la recomendación es "El débito todavía no se devolvió: pedir la reversa antes de
   reintentar. Si se reintenta antes, se cobra dos veces".

---

### Historia de usuario 2 - No diagnosticar sin respaldo (Priority: P1)

Cuando no hay nada que diagnosticar o la evidencia no alcanza, PayTrace lo dice y no nombra una
causa: "no concluyente" si el trace no tiene ningún evento clave (en una pendiente, recién cuando ya
pasó el plazo de espera) o si tiene más de uno; "La operación sigue en curso" si está pendiente
dentro del plazo; "La operación no tiene un fallo para investigar" si la operación es OK.

**Why this priority**: es el principio de producto ("evidencia o nada") y de la constitución
(principio I). Un diagnóstico inventado es peor que ninguno (OBJ-3).

**Independent Test**: pedir el diagnóstico de las 5 operaciones con trace incompleto del conjunto de
evaluación, de una operación OK generada con la historia 4 (el conjunto de evaluación no tiene
operaciones OK), de las 2 operaciones del archivo de prueba de plazo y de las 3 del archivo de casos
borde, y verificar las respuestas sin causa.

**Acceptance Scenarios** (AC-08, AC-09, AC-10, AC-12, AC-15; los escenarios 5 a 7 no tienen AC en
el PRD):

1. **Dado** una operación del caso "trace incompleto", **Cuando** el analista pide el diagnóstico,
   **Entonces** la causa es "no concluyente", no aparece ninguna otra causa de la tabla, no cita
   ningún evento y la recomendación es "Pedir los logs del proveedor desde el último evento conocido".
2. **Dado** una operación del caso "OK", **Cuando** pide el diagnóstico, **Entonces** el sistema
   muestra "La operación no tiene un fallo para investigar" y no muestra causa, eventos citados ni
   recomendación.
3. **Dado** la operación pendiente del archivo de prueba de plazo cuyo último evento es 2 minutos
   anterior a su hora de referencia, **Cuando** pide el diagnóstico, **Entonces** el sistema muestra
   "La operación sigue en curso" y no muestra causa, eventos citados ni recomendación.
4. **Dado** la operación pendiente del archivo de prueba de plazo cuyo último evento es exactamente
   10 minutos anterior a su hora de referencia, **Cuando** pide el diagnóstico, **Entonces** el
   sistema muestra "La operación sigue en curso" y no muestra causa, eventos citados ni recomendación.
5. **Dado** la operación fallida del archivo de casos borde que no tiene ningún evento clave,
   **Cuando** el analista pide el diagnóstico, **Entonces** la causa es "no concluyente", no aparece
   ninguna otra causa de la tabla, no cita ningún evento y la recomendación es "Pedir los logs del
   proveedor desde el último evento conocido".
6. **Dado** la operación fallida del archivo de casos borde que tiene dos eventos clave con códigos
   distintos (AC01 y AB05), **Cuando** el analista pide el diagnóstico, **Entonces** la causa es "no
   concluyente", no aparece ninguna otra causa de la tabla, cita exactamente esos dos eventos por su
   ID y la recomendación es "Evidencia contradictoria: revisar manualmente los eventos citados".
7. **Dado** la operación fallida del archivo de casos borde que tiene dos rechazos por timeout con
   código AB05, **Cuando** el analista pide el diagnóstico, **Entonces** la causa es "no concluyente"
   (no "timeout"), no aparece ninguna otra causa de la tabla, cita exactamente esos dos eventos por
   su ID y la recomendación es "Evidencia contradictoria: revisar manualmente los eventos citados".

---

### Historia de usuario 3 - Buscar una operación y ver su trace (Priority: P1)

El analista escribe el ID de la operación, la encuentra y ve su trace en orden cronológico, del
evento más antiguo al más nuevo.

**Why this priority**: es el punto de entrada de toda investigación (OBJ-1); reemplaza seguir el ID
log por log.

**Independent Test**: con el conjunto de evaluación cargado, buscar IDs existentes, inexistentes y
mal escritos, y abrir una operación para verificar el orden de su trace.

**Acceptance Scenarios** (AC-03, AC-04, AC-05, AC-11):

1. **Dado** que existe la operación "OP-0001", **Cuando** el analista busca "OP-0001", **Entonces**
   el sistema muestra la operación "OP-0001".
2. **Dado** que no existe ninguna operación "OP-9999", **Cuando** busca "OP-9999", **Entonces** el
   sistema muestra "Operación no encontrada".
3. **Dado** que el analista escribe "op1", "op-0001" o deja la búsqueda vacía, **Cuando** busca,
   **Entonces** el sistema muestra "Ingresá un ID con formato OP-0000" y no muestra ninguna operación
   ni "Operación no encontrada".
4. **Dado** una operación del caso "cuenta incorrecta", que tiene 4 eventos, **Cuando** el analista
   la abre, **Entonces** ve los 4 eventos, del más antiguo al más nuevo.

---

### Historia de usuario 4 - Generar operaciones simuladas por caso (Priority: P1)

El analista elige uno de los casos de la tabla y genera una operación simulada nueva de ese caso,
con su estado y su trace, para investigarla en la demo.

**Why this priority**: el PRD lo marca imprescindible y es la base del flujo de demo. Se ubica
después de las historias 1–3 porque esas pueden probarse solo con el conjunto de evaluación.

**Independent Test**: generar una operación de cada caso y verificar estado, eventos, último evento
e ID asignado.

**Acceptance Scenarios** (AC-01, AC-13, AC-14):

1. **Dado** que el analista elige un caso, **Cuando** genera la operación, **Entonces** la operación
   queda con el estado y el trace de la tabla:

   | Caso | Estado | Tiene el evento | Último evento |
   |---|---|---|---|
   | OK | OK | acreditación en destino | acreditación en destino |
   | fondos insuficientes | fallida | rechazo en origen, código AM04 | rechazo en origen, código AM04 |
   | cuenta incorrecta | fallida | rechazo del banco destino, código AC01 | reversa del débito |
   | timeout con reversa | fallida | rechazo por timeout, código AB05 | reversa del débito |
   | timeout sin reversa | fallida | rechazo por timeout, código AB05 | rechazo por timeout, código AB05 |
   | trace incompleto | pendiente | débito en origen | débito en origen |

2. **Dado** que el analista elige el caso "trace incompleto", **Cuando** genera la operación,
   **Entonces** el último evento del trace es más de 10 minutos anterior al momento de la generación.
3. **Dado** que están cargadas las operaciones del conjunto de evaluación, **Cuando** el analista
   genera una operación, **Entonces** su ID no coincide con el de ninguna operación existente y no
   empieza con "OP-9".

---

### Historia de usuario 5 - Ver la lista de operaciones con su estado (Priority: P2)

El analista ve todas las operaciones (las del conjunto de evaluación y las que generó) con su estado
y puede elegir una para investigarla, sin tener que tipear el ID.

**Why this priority**: el PRD lo marca como deseable (RF-02); la búsqueda por ID ya cubre el acceso.

**Independent Test**: generar operaciones de tres casos distintos y abrir la lista.

**Acceptance Scenarios** (AC-02):

1. **Dado** que se generaron operaciones de los casos "OK", "fondos insuficientes" y "trace
   incompleto", **Cuando** el analista abre la lista, **Entonces** ve esas 3 operaciones con los
   estados OK, fallida y pendiente.

---

### Edge Cases

- **ID con formato inválido**: cualquier ID que no sea `OP-` seguido de 4 dígitos en mayúscula
  (p. ej. `op1`, `op-0001`, vacío) responde "Ingresá un ID con formato OP-0000", sin buscar.
- **ID con formato válido que no existe** (p. ej. `OP-9999`): responde "Operación no encontrada".
- **Pendiente con exactamente 10 minutos sin eventos**: sigue en curso; el plazo vence recién con
  más de 10 minutos.
- **Pedir el diagnóstico varias veces**: la misma operación da siempre el mismo resultado (misma
  causa, mismos eventos citados, misma recomendación).
- **Operación fallida sin ningún evento clave** (su trace no encaja en ninguna regla): la respuesta es
  "no concluyente" enseguida, sin esperar el plazo (que aplica solo a pendientes), sin causa y sin
  eventos citados (constitución, principio I). La recomendación es la misma que la del caso trace
  incompleto: "Pedir los logs del proveedor desde el último evento conocido". El generador no crea
  operaciones así; se cubren con el archivo de casos borde.
- **Evidencia contradictoria (más de un evento clave en el trace, aunque tengan el mismo código)**:
  la respuesta es "no concluyente", no nombra causa, cita por su ID todos los eventos clave en
  conflicto y recomienda "Evidencia contradictoria: revisar manualmente los eventos citados"
  (constitución, principio I; AGENTS.md). El "sin eventos citados" del PRD (RF-08) aplica solo cuando
  no hay ningún evento clave. Se cubre con el archivo de casos borde.
- **Se agotan los IDs disponibles para operaciones generadas** (todos los menores a `OP-9000` están
  ocupados; no se pueden usar `OP-9xxx`): la generación se rechaza con el mensaje "No quedan IDs
  disponibles para generar operaciones" y no se crea ninguna operación (FR-032).

## Requirements *(mandatory)*

### Functional Requirements

**Operaciones y generación**

- **FR-001** (RF-01): El sistema DEBE permitir al analista generar una operación simulada de
  cualquiera de los seis casos de la tabla de casos, con el estado y la secuencia de eventos que la
  tabla define para ese caso.
- **FR-002**: Cada operación DEBE tener un ID único con formato `OP-` seguido de 4 dígitos, en
  mayúscula (ej.: `OP-0001`). Ninguna operación, fija o generada, usa un ID `OP-9xxx`.
- **FR-003**: Una operación generada DEBE tomar el siguiente ID libre: el número siguiente al mayor ID
  existente (contando todos los datos fijos y las generadas), sin repetir ningún ID y NUNCA un ID
  `OP-9xxx`.
- **FR-004**: Una operación del caso "trace incompleto" DEBE generarse con su último evento más de
  10 minutos anterior al momento de la generación.
- **FR-005**: Cada operación DEBE tener uno de tres estados: **OK** (se acreditó en destino),
  **fallida** (se rechazó; no se acredita en destino) o **pendiente** (todavía no hay resultado final).
- **FR-006**: Cada evento DEBE tener ID de evento, momento, tipo, emisor (origen, proveedor o banco
  destino) y, si es un rechazo, su código de motivo ISO 20022 (solo AM04, AC01 o AB05).
- **FR-007**: El sistema DEBE tener disponible el conjunto de evaluación: 25 operaciones fijas, 5 de
  cada caso salvo el caso OK, con IDs y horarios que no cambian entre usos, que conviven con las
  operaciones generadas.
- **FR-008**: El sistema DEBE tener disponible el archivo de prueba de plazo: 2 operaciones
  pendientes fijas, una con su último evento 2 minutos anterior a su hora de referencia y otra con su
  último evento exactamente 10 minutos anterior a su hora de referencia.
- **FR-009**: Las operaciones generadas DEBEN existir mientras la aplicación está en uso y NO se
  conservan al reiniciarla: después de un reinicio solo quedan los datos fijos (conjunto de
  evaluación, archivo de prueba de plazo y archivo de casos borde), iguales que antes.
- **FR-029**: El sistema DEBE tener disponible el archivo de casos borde: 3 operaciones fallidas
  fijas, aparte del conjunto de evaluación, con IDs y horarios que no cambian entre usos:
  - una sin ningún evento clave: orden enviada → débito en origen → reversa del débito;
  - una con dos eventos clave de códigos distintos: orden enviada → débito en origen → rechazo del
    banco destino, código AC01 → rechazo por timeout, código AB05 → reversa del débito;
  - una con dos eventos clave del mismo código: orden enviada → débito en origen → envío al
    proveedor → rechazo por timeout, código AB05 → rechazo por timeout, código AB05.
- **FR-030**: Todos los datos fijos (conjunto de evaluación, archivo de prueba de plazo y archivo de
  casos borde) DEBEN estar cargados desde el inicio, poder buscarse y listarse como cualquier otra
  operación, y sus IDs DEBEN contar como ocupados para FR-003.
- **FR-031**: Dentro de un trace, cada evento DEBE tener un momento estrictamente posterior al del
  evento anterior; no hay dos eventos con el mismo momento.
- **FR-032**: Si no quedan IDs disponibles para generar (todos los menores a `OP-9000` están
  ocupados), la generación DEBE rechazarse con el mensaje "No quedan IDs disponibles para generar
  operaciones" y NO DEBE crearse ninguna operación.

**Búsqueda, lista y trace**

- **FR-010** (RF-03): El sistema DEBE permitir buscar una operación por su ID y mostrarla si existe.
- **FR-011** (RF-03): Si el ID buscado tiene formato válido pero no existe, el sistema DEBE mostrar
  "Operación no encontrada".
- **FR-012** (RF-03): Si el ID buscado está vacío o no respeta el formato, el sistema DEBE mostrar
  "Ingresá un ID con formato OP-0000" y NO DEBE mostrar ninguna operación ni "Operación no encontrada".
- **FR-013** (RF-02): El sistema DEBERÍA listar todas las operaciones (datos fijos y generadas) con
  su estado.
- **FR-014** (RF-04): El sistema DEBE mostrar el trace de una operación con todos sus eventos en
  orden cronológico, del más antiguo al más nuevo.

**Diagnóstico**

- **FR-015**: El diagnóstico DEBE darse solo cuando el analista lo pide; no es automático.
- **FR-016**: Las reglas de diagnóstico DEBEN decidir solo a partir del trace, el estado de la
  operación y la hora de referencia, sin conocer el caso con el que se generó la operación. Para las
  reglas, un evento clave es únicamente un rechazo en origen con código AM04, un rechazo del banco
  destino con código AC01 o un rechazo por timeout con código AB05.
- **FR-017**: El diagnóstico DEBE tener tres campos: causa, eventos citados (por ID de evento) y
  recomendación.
- **FR-018** (RF-05): Para una operación fallida, la causa DEBE ser exactamente uno de los valores de
  la columna "Causa" de la tabla de casos ("fondos insuficientes", "cuenta incorrecta", "timeout"),
  determinada por el evento clave del trace, o "no concluyente".
- **FR-019** (RF-06): Cuando nombra una causa, el diagnóstico DEBE citar, por su ID, exactamente un
  evento: el evento clave del trace que la prueba. NUNCA se nombra una causa sin ese evento citado.
- **FR-020** (RF-07): El diagnóstico DEBE mostrar la recomendación de la tabla de casos que
  corresponde al trace. Para el timeout, la recomendación DEBE distinguir si el trace tiene o no la
  reversa del débito después del rechazo.
- **FR-021** (RF-08): Si el trace no tiene ningún evento clave, el diagnóstico DEBE tener la causa
  "no concluyente", sin ninguna otra causa y sin eventos citados, y DEBE recomendar "Pedir los logs
  del proveedor desde el último evento conocido". En una operación fallida esto aplica enseguida; en
  una pendiente, solo cuando ya pasó el plazo de espera (si no, aplica FR-024).
- **FR-022**: Si la evidencia es contradictoria (más de un evento clave, aunque tengan el mismo
  código), el diagnóstico DEBE ser "no concluyente", NO DEBE nombrar ninguna causa, DEBE citar por su
  ID todos los eventos clave en
  conflicto y DEBE recomendar "Evidencia contradictoria: revisar manualmente los eventos citados".
- **FR-023** (RF-09): Si la operación es OK, el sistema DEBE mostrar "La operación no tiene un fallo
  para investigar" y NO DEBE mostrar causa, eventos citados ni recomendación.
- **FR-024** (RF-10): Si la operación está pendiente y todavía no pasó el plazo de espera, el sistema
  DEBE mostrar "La operación sigue en curso" y NO DEBE mostrar causa, eventos citados ni recomendación.
- **FR-025**: El plazo de espera aplica solo a operaciones pendientes. DEBE considerarse vencido solo
  cuando pasaron **más** de 10 minutos entre el último evento del trace y la hora de referencia. Con
  exactamente 10 minutos, la operación sigue en curso.
- **FR-026**: La hora de referencia ("ahora") DEBE ser un dato de entrada del diagnóstico; las reglas
  no dependen de nada más que el trace, el estado y esa hora. Cada operación de los datos fijos
  (conjunto de evaluación, archivo de prueba de plazo y archivo de casos borde) DEBE traer su propia hora de referencia fija en los datos, de modo que
  las 5 operaciones con trace incompleto del conjunto de evaluación tengan su último evento más de 10
  minutos anterior a ella. Para las operaciones generadas, la hora de referencia es el momento en que
  el analista pide el diagnóstico; ese momento se toma fuera de las reglas y se les pasa como dato.
- **FR-027** (RNF-04): El diagnóstico DEBE ser determinista: pedir el diagnóstico de la misma
  operación varias veces DEBE dar siempre la misma causa, los mismos eventos citados y la misma
  recomendación. No se usa ninguna fuente aleatoria ni modelo de IA para diagnosticar.

**Datos simulados**

- **FR-028** (RNF-03): Todos los datos DEBEN ser simulados: 0 datos personales reales y ninguna
  conexión con bancos, proveedores ni sistemas reales.

### Key Entities *(include if feature involves data)*

- **Operación**: transferencia simulada. Tiene ID único (`OP-` + 4 dígitos), estado (OK, fallida,
  pendiente) y un trace. Proviene de los datos fijos (conjunto de evaluación, archivo de prueba de
  plazo o archivo de casos borde) o de una generación del analista.
- **Evento**: hecho del trace. Tiene ID de evento, momento, tipo, emisor (origen, proveedor o banco
  destino) y, si es un rechazo, un código de motivo ISO 20022.
- **Evento clave**: para las reglas, un rechazo en origen con AM04, un rechazo del banco destino con
  AC01 o un rechazo por timeout con AB05. Un trace con exactamente uno permite nombrar la causa; con
  ninguno o con más de uno, la respuesta es "no concluyente".
- **Trace**: lista de eventos de una operación, unificada y en orden cronológico, con momentos
  estrictamente crecientes.
- **Caso**: escenario con el que se generó la operación (fila de la tabla de casos). Define estado,
  secuencia de eventos, evento clave, causa y recomendación. Las reglas no lo ven.
- **Diagnóstico**: respuesta a un pedido del analista: causa, eventos citados y recomendación. En
  lugar de un diagnóstico, el sistema puede responder "La operación no tiene un fallo para
  investigar" (operación OK) o "La operación sigue en curso" (pendiente dentro del plazo).
- **Conjunto de evaluación**: 25 operaciones fijas (5 por cada caso con fallo o pendiente), con IDs
  y horarios estables.
- **Archivo de prueba de plazo**: 2 operaciones pendientes fijas, aparte del conjunto de evaluación,
  usadas solo para verificar el límite del plazo de espera.
- **Archivo de casos borde**: 3 operaciones fallidas fijas, aparte del conjunto de evaluación, para
  verificar el "no concluyente" sin evento clave y con evidencia contradictoria (FR-029).
- **Hora de referencia**: el "ahora" contra el que se mide el plazo de espera. Fija y propia de cada
  operación en los datos fijos; para las operaciones generadas, el momento del pedido de diagnóstico.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (OBJ-1): La mediana del tiempo de investigación es **≤ 5 minutos** por caso, medida
  sobre 10 operaciones del conjunto de evaluación cronometradas por una persona que no las generó,
  desde que busca el ID hasta que tiene el diagnóstico (hoy ~20 min, estimación de referencia).
- **SC-002** (OBJ-2): El **100 %** de los diagnósticos con causa de las 20 operaciones con trace
  completo del conjunto de evaluación cita exactamente un evento: el evento clave de su caso.
- **SC-003** (OBJ-3): El **100 %** de las 5 operaciones con trace incompleto del conjunto de
  evaluación termina como "no concluyente".
- **SC-004** (OBJ-4): El **100 %** de las 20 operaciones con trace completo del conjunto de
  evaluación recibe la causa que corresponde a su caso.
- **SC-005** (RNF-01): El diagnóstico se muestra en **≤ 2 segundos** en al menos el 95 % de 125
  mediciones (5 por cada operación del conjunto de evaluación), cada una desde que el analista pide
  el diagnóstico hasta que ve el resultado completo.
- **SC-006** (RNF-02): El trace de una operación se muestra en **≤ 2 segundos** en al menos el 95 %
  de 125 mediciones (5 por cada operación del conjunto de evaluación), cada una desde que el analista
  abre la operación hasta que ve todos sus eventos.
- **SC-007** (RNF-04): Pedir **5 veces** el diagnóstico de cada operación del conjunto de evaluación
  da el mismo resultado las 5 veces en el **100 %** de las operaciones.
- **SC-008** (RNF-03): **0** datos personales reales en todo el sistema.
- **SC-009**: Todos los criterios de aceptación AC-01 a AC-15 del PRD se cumplen.

## Assumptions

- Hay un solo tipo de usuario (el analista); no hay login, roles ni permisos, y todos los analistas
  ven todas las operaciones (PRD §6).
- El trace ya llega unido: el MVP no une logs reales de varios sistemas (PRD §6).
- PayTrace solo diagnostica: no corrige ni reintenta operaciones (PRD §6).
- Solo transferencias; quedan afuera tarjetas, otros medios de pago y otros casos de fallo (AM02,
  duplicados, antifraude, etc.) y los mensajes ISO 20022 completos (PRD §6).
- La lista de operaciones no tiene paginación; el volumen esperado es el de la demo: las 25 del
  conjunto de evaluación más las que genere el analista (PRD §6).
- Los textos que ve el analista ("Operación no encontrada", "Ingresá un ID con formato OP-0000", "La
  operación sigue en curso", "La operación no tiene un fallo para investigar", "no concluyente" y las
  recomendaciones) son los del PRD, literales, salvo los que se definen en Clarifications y en
  FR-032.
- Para los casos de timeout, "con reversa" y "sin reversa" se distinguen solo por la presencia de la
  reversa del débito en el trace, porque las reglas no conocen el caso (PRD §1, término "Caso").
- El estado de una operación siempre coincide con su trace (p. ej. una OK siempre tiene la
  acreditación en destino), porque todos los datos son simulados. No se define qué pasa si no
  coinciden.
- Un agente de IA para traces que no encajen en ninguna regla queda para después del MVP (PRD §6–§7).
- Dependencia: la lista oficial de códigos de motivo ISO 20022 (External Code Sets), para mantener
  alineados AM04, AC01 y AB05 (PRD §7).
