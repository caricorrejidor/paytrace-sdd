---

description: "Lista de tareas de la feature 002-evidencia-recomendacion"
---

# Tareas: PayTrace — evidencia de la recomendación

**Entrada**: documentos de diseño en `specs/002-evidencia-recomendacion/`

**Prerrequisitos**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md), [quickstart.md](./quickstart.md)

**Tests**: obligatorios (constitución, principio III). Cada tarea de test va antes que la
implementación que cubre y termina cuando el test corre y **se ve fallar** por la razón esperada.
Un test nunca se modifica para que pase. Esta lista **no tiene excepciones** al rojo→verde: todo test
nuevo se ve fallar antes de la implementación que lo pone en verde.

**Cambio explícito de tests de 001 (T001)**: FR-001 modifica 001/FR-017 (el diagnóstico pasa de tres a
cuatro campos), así que tres archivos de test de 001 quedan desactualizados respecto del spec. T001 los
actualiza en una tarea y un commit propios, **antes de tocar `app/`**, justificado contra FR-001
([research R6](./research.md#r6-tests-existentes-que-cambian)). No es editar un test para que pase:
después de T001 esos tests fallan, y pasan recién con la implementación.

**Criterios cubiertos por tests de 001 que no cambian** (por eso no hay tareas nuevas para ellos):

- **SC-003 / FR-007 / historia 3**: `test_h2_e2_operacion_ok_no_tiene_fallo`,
  `test_h2_e3_pendiente_a_2_minutos_sigue_en_curso` y
  `test_h2_e4_pendiente_a_exactamente_10_minutos_sigue_en_curso` (en
  `tests/api/test_h2_sin_respaldo.py`), y `test_ok_generada_da_sin_fallo` (en
  `tests/api/test_h4_generacion.py`). Comparan el cuerpo **exacto** de `sin_fallo` y `en_curso`: si
  apareciera `evidencia_recomendacion`, fallarían. T001 no los toca.
- **SC-005 / FR-011 (determinismo en la API)**: `test_sc007_cinco_pedidos_dan_el_mismo_cuerpo_trace_completo`
  y `test_sc007_cinco_pedidos_dan_el_mismo_cuerpo_trace_incompleto` (en
  `tests/api/test_conjunto_evaluacion.py`). Comparan el cuerpo completo 5 veces para `OP-0001` a
  `OP-0025`, así que con el cambio también comparan `evidencia_recomendacion`.
- **SC-006**: `tests/api/test_tiempos.py`, sin cambios.

T011 verifica que esos archivos no cambien en la rama, salvo lo que hace T001.

**Organización**: por historia de usuario del spec, con un orden que no es el de prioridad (ver
Dependencias): la historia 2 va antes que la 1, porque el campo es obligatorio (research R3) y, al
agregarlo, todas las ramas de las reglas tienen que devolver algo. Escribir primero los tests de
"vacía" (historia 2) hace que se vean fallar antes de que exista el campo. Después, la historia 1 suma
las reversas. La historia 3 no tiene tareas: la cubren los tests de 001 de arriba.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias de tareas pendientes).
- **[USn]**: historia de usuario del spec de la 002 a la que pertenece la tarea.
- Cada tarea nombra el archivo que toca y cierra con **Terminada cuando**.

## Convenciones

- Mismas convenciones que [001/tasks.md](../001-diagnostico-transferencias/tasks.md#convenciones),
  con estas precisiones:
- "Ve fallar" = `uv run pytest <archivo>` termina con fallos o errores causados por la pieza que
  falta (`TypeError` por el cuarto argumento de `Diagnostico`, assert por la clave
  `evidencia_recomendacion` o por una evidencia vacía), no por un error del propio test.
- Los tests nuevos de la 002 llevan el prefijo `test_002_`, para no confundirse con los de 001 que
  tienen el mismo número de historia y escenario: en `tests/api/test_evidencia_recomendacion.py`, los
  de escenarios se llaman `test_002_h<historia>_e<escenario>_<descripción>`, donde la historia y el
  escenario son **los del spec de la 002**, y llevan como docstring el Dado/Cuando/Entonces del spec;
  los de criterios, `test_002_sc<nnn>_<descripción>`. En `tests/unit/test_reglas.py`, los nuevos se
  llaman `test_002_<descripción>`.
- Los tests nuevos de reglas van en `tests/unit/test_reglas.py`, en una sección propia
  `# --- Evidencia de la recomendación (feature 002) ---`, y reutilizan el helper `trace()` y las
  constantes del archivo (research R7).
- Los tests comparan contra **textos e IDs literales** escritos en el propio test, nunca contra
  constantes de `app/diagnostico/textos.py`.
- Las operaciones con traces raros que no están en los datos fijos se arman dentro del test (FR-013):
  en reglas, con `trace()`; en API, generándolas con `POST /operaciones`.
- Durante `/speckit-implement`, cada tarea se commitea al terminar con el skill `conventional-commit`,
  **sin esperar OK** por commit. Las tareas de test se commitean cuando el test **se ve fallar**
  (commit en rojo, tipo `test`), antes de la implementación que lo pone en verde. T001 va en su propio
  commit de tipo `test`, que cita FR-001 en el cuerpo. Ese commit en rojo es la referencia contra la
  que T011 verifica que el test no cambió.
- Los commits de implementación (`feat`, `fix`, `refactor`) **no tocan** `tests/`.
- Dentro de una fase puede haber commits intermedios con la suite rota (por ejemplo, entre T004 y T005
  las reglas dan `TypeError`; entre T006 y T007 el endpoint de diagnóstico falla al validar la
  respuesta). Se acepta porque la revisión es por fase.
- Al terminar cada fase, la implementación **se frena**, hace `git push` de la rama y muestra el
  `git log` de los commits de la fase y el resultado de `uv run pytest` para revisión. Si un archivo
  da error de colección (Fase 1), se agrega `--continue-on-collection-errors` para ver el resto. La
  fase siguiente empieza recién con el OK.

---

## Fase 1: Fundacional — ajuste de los tests de 001 al spec nuevo

**Propósito**: que los tests de 001 que comparan el diagnóstico completo digan lo que dice el spec de
la 002 (cuatro campos), antes de tocar `app/`.

**⚠️ CRÍTICO**: ninguna historia empieza hasta terminar esta fase. Línea base antes de empezar:
`uv run pytest` da 292 passed.

- [X] T001 Actualizar, justificado por FR-001 (modifica 001/FR-017) y sin cambiar ninguna otra cosa, tres archivos de test de 001. En `tests/unit/test_reglas.py`, sumar el cuarto argumento a cada `Diagnostico(...)` esperado, con el valor de la tabla de data-model.md: `test_am04_…` → `()`; `test_ac01_es_cuenta_incorrecta_y_cita_el_rechazo` → `("OP-0100-E4",)`; `test_ab05_con_reversa_posterior_es_timeout_con_reintento` → `("OP-0100-E5",)`; `test_ab05_sin_reversa_…` y `test_ab05_con_reversa_anterior_…` → `()`; la constante `NO_CONCLUYENTE_SIN_CLAVE` → `()`; los tres `Diagnostico("no concluyente", …, CONTRADICTORIA)` → `()`. En `tests/api/test_h1_diagnostico_con_evidencia.py`, sumar `"evidencia_recomendacion"` a `CLAVES_DIAGNOSTICO`. En `tests/api/test_h2_sin_respaldo.py`, sumar `"evidencia_recomendacion": []` a los cinco cuerpos completos de `"tipo": "diagnostico"` (`test_h2_e1`, `test_h2_e5`, `test_h2_e6`, `test_h2_e7` y la segunda aserción de `test_generada_usa_la_hora_del_pedido_como_hora_de_referencia`). Los cuerpos `sin_fallo` y `en_curso` **no** se tocan (FR-007). **Terminada cuando**: `git diff` muestra solo esos cambios, y `uv run pytest --continue-on-collection-errors` muestra exactamente este rojo (sin el flag, pytest corta toda la corrida en el error de colección y no muestra el resto): (a) `tests/unit/test_reglas.py` da **error de colección** con `TypeError` en `NO_CONCLUYENTE_SIN_CLAVE`, porque la constante arma un `Diagnostico` de cuatro argumentos al importar el módulo, así que no corre ningún test de ese archivo (tampoco los que T001 no toca); (b) en `test_h1_diagnostico_con_evidencia.py` fallan por assert de claves `test_h1_e1` a `test_h1_e4`; (c) en `test_h2_sin_respaldo.py` fallan por assert de cuerpo los cinco tests tocados; (d) todo lo demás, incluidos `test_h2_e2`, `test_h2_e3` y `test_h2_e4`, sigue en verde. Resumen esperado: 9 failed, 257 passed, 1 error. El commit `test` cita FR-001 en el cuerpo.

**Checkpoint**: suite en rojo solo por lo que dice T001. Es el rojo esperado: el spec cambió y la app
todavía no. En la revisión de esta fase, mostrar `uv run pytest --continue-on-collection-errors`.

---

## Fase 2: Historia 2 — Evidencia de la recomendación vacía cuando no hay evento que la respalde (P1)

**Objetivo**: el diagnóstico tiene el cuarto campo, `evidencia_recomendacion`, siempre presente y vacío
en fondos insuficientes, timeout sin reversa y "no concluyente", aunque el trace tenga reversas.

**Prueba independiente**: pedir el diagnóstico de `OP-0001` a `OP-0005`, `OP-0016` a `OP-0025` y
`OP-0028` a `OP-0030`, y verificar que todas traen `"evidencia_recomendacion": []` y que causa, citas y
recomendación son las de 001.

### Tests de la Historia 2 (primero; deben verse fallar) ⚠️

- [ ] T002 [US2] Agregar en `tests/unit/test_reglas.py`, en la sección nueva `# --- Evidencia de la recomendación (feature 002) ---`, los tests de evidencia vacía que T001 no cubre: (a) `test_002_ac01_sin_reversa_tiene_evidencia_vacia` (escenario 4 de la historia 1, que afirma evidencia vacía): `trace(ORDEN, DEBITO, AC01)` → `Diagnostico("cuenta incorrecta", ("OP-0100-E3",), "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó", ())` (FR-003); (b) `test_002_ac01_con_reversa_anterior_tiene_evidencia_vacia` (FR-008): `trace(ORDEN, DEBITO, REVERSA, AC01)` → misma causa y recomendación, cita `("OP-0100-E4",)`, evidencia `()`; (c) `test_002_pendiente_vencida_con_reversa_tiene_evidencia_vacia` (FR-006): `trace(ORDEN, DEBITO, REVERSA)` en estado `pendiente` a 15 min → `Diagnostico("no concluyente", (), "Pedir los logs del proveedor desde el último evento conocido", ())`; (d) `test_002_cinco_llamadas_dan_la_misma_evidencia` (FR-011): 5 llamadas iguales para (a) y (b) dan el mismo resultado. Depende de T001 (mismo archivo). **Terminada cuando**: los cuatro tests existen y `uv run pytest tests/unit/test_reglas.py` sigue dando el error de colección de T001 (`TypeError` en `NO_CONCLUYENTE_SIN_CLAVE`). Es el mismo rojo, porque mientras `Diagnostico` tenga tres campos no corre ningún test del archivo. Además, cada test nuevo arma un `Diagnostico` de cuatro argumentos, así que por sí solo también fallaría con `TypeError`.
- [ ] T003 [P] [US2] Crear `tests/api/test_evidencia_recomendacion.py` con un helper `_diagnostico(cliente, id)` (status 200, `tipo == "diagnostico"`, claves exactamente `{tipo, causa, eventos_citados, recomendacion, evidencia_recomendacion}`). Agregar: (a) los escenarios de la historia 2 de la 002: `test_002_h2_e1` (`OP-0001`), `test_002_h2_e2` (`OP-0016`), `test_002_h2_e3` (`OP-0021`), `test_002_h2_e4` (`OP-0028`), `test_002_h2_e5` (`OP-0029`) y `test_002_h2_e6` (`OP-0030`). Cada uno verifica `evidencia_recomendacion == []` y causa, `eventos_citados` y recomendación literales de 001 (`["OP-0001-E2"]`, `["OP-0016-E4"]`, `[]`, `[]`, `["OP-0029-E3", "OP-0029-E4"]`, `["OP-0030-E4", "OP-0030-E5"]`). (b) `test_002_sc002_evidencia_vacia`: parametrizado sobre `OP-0001`–`OP-0005`, `OP-0016`–`OP-0025` y `OP-0028`–`OP-0030` (18 operaciones), verifica `evidencia_recomendacion == []`. (c) `test_002_sc004_recomendacion_de_001` (FR-010, SC-004): parametrizado sobre `OP-0001`–`OP-0025`, toma el `caso` de la operación desde la fixture `repositorio` (nunca de la API) y verifica, con `_diagnostico`, que la recomendación es la literal de 001 para ese caso. Los textos son los de la tabla de data-model.md de 001; en `trace_incompleto`, "Pedir los logs del proveedor desde el último evento conocido". **Terminada cuando**: todos los tests del archivo se ven fallar por el assert de claves de `_diagnostico` (la respuesta no tiene `evidencia_recomendacion`).

### Implementación de la Historia 2

- [ ] T004 [US2] Agregar en `app/diagnostico/resultados.py` el campo `evidencia_recomendacion: tuple[str, ...]` al final de `Diagnostico`, **sin valor por defecto** (research R3), con docstring que cite FR-001. `SinFallo` y `EnCurso` no cambian. Depende de T002 y T003. **Terminada cuando**: `uv run python -c "from app.diagnostico.resultados import Diagnostico; Diagnostico('c', (), 'r', ())"` no da error y `Diagnostico('c', (), 'r')` da `TypeError`.
- [ ] T005 [US2] Actualizar `app/diagnostico/reglas.py` para que **cada** `Diagnostico(...)` pase su cuarto argumento: `()` en las ramas "no concluyente" (0 y > 1 eventos clave; FR-006), en AM04 (FR-005) y, por ahora, también en AC01 y AB05 (mínimo para el verde; las reversas llegan en T010). No cambia ninguna causa, cita ni recomendación (FR-010). Sigue importando solo stdlib, `app.dominio` y `app/diagnostico/`. Depende de T004. **Terminada cuando**: `uv run pytest tests/unit/test_reglas.py tests/unit/test_reglas_aislamiento.py` pasa, salvo exactamente `test_ac01_es_cuenta_incorrecta_y_cita_el_rechazo` y `test_ab05_con_reversa_posterior_es_timeout_con_reintento`, que esperan la reversa (historia 1).
- [ ] T006 [US2] Agregar en `app/api/esquemas.py` el campo `evidencia_recomendacion: list[str]`, obligatorio, a `DiagnosticoSalida` (research R5). `SinFalloSalida`, `EnCursoSalida` y `DiagnosticoRespuesta` no cambian. **Terminada cuando**: `uv run python -c "from app.api.esquemas import DiagnosticoSalida; DiagnosticoSalida(causa='c', eventos_citados=[], recomendacion='r', evidencia_recomendacion=[])"` no da error.
- [ ] T007 [US2] Actualizar `_a_salida()` en `app/api/rutas.py` para que el `case Diagnostico(...)` también tome `evidencia_recomendacion` y lo copie como lista a `DiagnosticoSalida`. Depende de T005 y T006. **Terminada cuando**: `uv run pytest tests/api/` pasa completo, y `uv run pytest` falla solo en los dos tests de `test_reglas.py` nombrados en T005.

**Checkpoint**: el campo existe y es correcto en todos los casos vacíos. Quedan en rojo solo los dos
tests de T001 que esperan la reversa: es el rojo que pone en verde la historia 1.

---

## Fase 3: Historia 1 — Ver el evento que respalda la recomendación (P1) 🎯 MVP

**Objetivo**: en "cuenta incorrecta" y "timeout", `evidencia_recomendacion` lleva los IDs de todas las
reversas del débito posteriores al evento clave, en el orden del trace, sin tocar causa, citas ni
recomendación.

**Prueba independiente**: pedir el diagnóstico de `OP-0006` a `OP-0015` y verificar que la evidencia
es exactamente la reversa del débito de cada trace (`OP-0006-E4` … `OP-0010-E4` y `OP-0011-E5` …
`OP-0015-E5`) y que no está en `eventos_citados`.

### Tests de la Historia 1 (primero; deben verse fallar) ⚠️

- [ ] T008 [US1] Agregar en `tests/unit/test_reglas.py`, en la sección de la feature 002: (a) `test_002_ac01_con_dos_reversas_cita_las_dos_en_orden` (escenario 5): `trace(ORDEN, DEBITO, AC01, REVERSA, REVERSA)` → `Diagnostico("cuenta incorrecta", ("OP-0100-E3",), "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó", ("OP-0100-E4", "OP-0100-E5"))`. No es "no concluyente" (FR-012). (b) `test_002_ab05_con_dos_reversas_cita_las_dos_en_orden`: `trace(ORDEN, DEBITO, ENVIO, AB05, REVERSA, REVERSA)` → "timeout", cita `("OP-0100-E4",)`, "El débito ya se devolvió: se puede reintentar la transferencia", evidencia `("OP-0100-E5", "OP-0100-E6")`. (c) `test_002_reversa_anterior_al_ac01_no_cuenta` (FR-008 mixto): `trace(ORDEN, DEBITO, REVERSA, AC01, REVERSA)` → evidencia `("OP-0100-E5",)` (la reversa anterior no cuenta). (d) `test_002_la_reversa_nunca_esta_en_los_eventos_citados` (FR-009): parametrizado sobre los traces de (a), (b) y (c); **primero** afirma `r.evidencia_recomendacion != ()` y **después** `set(r.eventos_citados) & set(r.evidencia_recomendacion) == set()`. Depende de T002 (mismo archivo) y del cierre de la Fase 2. **Terminada cuando**: (a), (b), (c) y (d) se ven fallar por assert: la evidencia es `()` en todos, y en (d) falla la primera aserción.
- [ ] T009 [P] [US1] Agregar en `tests/api/test_evidencia_recomendacion.py`: `test_002_h1_e1` (`OP-0006`: causa "cuenta incorrecta", `eventos_citados == ["OP-0006-E3"]`, `evidencia_recomendacion == ["OP-0006-E4"]`); `test_002_h1_e2` (`OP-0011`: "timeout", `["OP-0011-E4"]`, "El débito ya se devolvió: se puede reintentar la transferencia", evidencia `["OP-0011-E5"]`); `test_002_h1_e3` parametrizado sobre `OP-0006`–`OP-0015`, que **primero** afirma `evidencia_recomendacion != []` y **después** que ninguno de sus IDs está en `eventos_citados`. `test_002_sc001_evidencia_es_la_reversa_posterior`: parametrizado sobre `OP-0006`–`OP-0015`, toma el trace con `GET /operaciones/{id}` y verifica que la evidencia es exactamente `[ID del único evento reversa_debito]` y que ese evento está después del evento citado. `test_002_generadas_citan_su_reversa` (FR-011 con generadas): `POST /operaciones` con `cuenta_incorrecta` y con `timeout_con_reversa`, y para cada una la evidencia es el ID de la `reversa_debito` de su trace. Depende de T003 (mismo archivo). **Terminada cuando**: todos los tests nuevos se ven fallar por assert (`[]` en lugar del ID; en `test_002_h1_e3`, la primera aserción).

### Implementación de la Historia 1

- [ ] T010 [US1] Implementar en `app/diagnostico/reglas.py` la función privada `_reversas_posteriores(clave, eventos) -> tuple[str, ...]` (IDs de los `reversa_debito` que están después de la posición de `clave` en el trace, en el orden del trace; research R4) y usarla en `_con_un_evento_clave()`: AC01 → evidencia = reversas; AB05 → evidencia = reversas, y la recomendación "con reversa" si `reversas` no está vacía (reemplaza el `any(...)` actual por el mismo cálculo). AM04 y las ramas "no concluyente" siguen en `()`. Depende de T008 y T009. **Terminada cuando**: `uv run pytest` pasa completo, incluidos los dos tests de T001 que quedaban en rojo, `test_reglas_aislamiento.py`, `test_conjunto_evaluacion.py` (SC-004 y SC-005) y `test_002_sc004_recomendacion_de_001`.

**Checkpoint**: historias 1 y 2 completas; suite completa en verde. Es el MVP de la feature.

---

## Fase 4: Historia 3 — Sin campo de evidencia cuando no hay diagnóstico (P2)

**Objetivo**: confirmar que las respuestas `sin_fallo` y `en_curso` no tienen la clave
`evidencia_recomendacion` (FR-007, SC-003).

**Sin tareas**: la cubren tests de 001 que comparan el cuerpo exacto y que T001 no toca (ver
"Criterios cubiertos por tests de 001" al principio). Agregar tests nuevos solo los duplicaría, y además
pasarían sin verse fallar, porque la clave falta por construcción (research R3, R5). Que esos tests
sigan sin cambios lo verifica T011.

**Checkpoint**: con el verde de la Fase 3, la historia 3 queda verificada.

---

## Fase 5: Pulido y verificaciones transversales

- [ ] T011 Correr `uv run pytest` completo y revisar la rama contra `main`: (a) para cada archivo de test tocado en la feature, compararlo con `git diff <commit en rojo> HEAD -- <archivo>` contra el commit de la tarea de test que lo dejó fallando: `test_reglas.py` contra T008 (el último commit en rojo del archivo), `test_h1_diagnostico_con_evidencia.py` y `test_h2_sin_respaldo.py` contra T001, y `test_evidencia_recomendacion.py` contra T009. Los cuatro diffs tienen que dar vacío. (b) Verificar que lo que dejaron T001 y T002 en `test_reglas.py` no cambió después: `git log --stat <commit de T001>..HEAD -- tests/` tiene que mostrar solo los commits `test` de T002, T003, T008 y T009, y `git diff <commit de T001> <commit de T008> -- tests/unit/test_reglas.py` tiene que contener solo líneas agregadas en la sección de la feature 002. (c) Ningún commit `feat`, `fix` o `refactor` de la rama toca `tests/` (`git log --stat main..HEAD`). (d) `git diff main -- tests/unit/test_reglas_aislamiento.py tests/api/test_conjunto_evaluacion.py tests/api/test_tiempos.py tests/api/test_h4_generacion.py app/datos/` da vacío. Esto cubre SC-003 a SC-006 con los tests de 001 sin cambios, y FR-013 sin datos fijos nuevos. **Terminada cuando**: la suite está en verde y (a) a (d) se cumplen.
- [ ] T012 Recorrer a mano los pasos 1 a 9 de `specs/002-evidencia-recomendacion/quickstart.md` con `uv run uvicorn app.main:app` y `curl`, y revisar en `http://localhost:8000/docs` que el esquema de la respuesta de diagnóstico muestra `evidencia_recomendacion`. **Terminada cuando**: los 9 pasos dan lo esperado y `/docs` muestra el campo.

---

## Dependencias y orden de ejecución

### Entre fases

- **Fundacional (Fase 1, T001)**: sin dependencias; **bloquea** todas las historias.
- **US2 (Fase 2)**: depende de la Fase 1. Va antes que US1 aunque las dos son P1. El campo es
  obligatorio, así que al agregarlo todas las ramas tienen que devolver un valor; si US1 fuera primero,
  los tests de "vacía" ya pasarían al escribirse y no se verían fallar.
- **US1 (Fase 3)**: depende de US2: usa el campo, el esquema y la ruta que deja US2, y completa las
  ramas AC01 y AB05 de `reglas.py`.
- **US3 (Fase 4)**: sin tareas; queda verificada con el verde de la Fase 3.
- **Pulido (Fase 5)**: después de todas las historias.

### Dentro de cada historia

- Tests → se ven fallar → `resultados.py` → `reglas.py` → `esquemas.py` → `rutas.py`.
- Archivos compartidos entre tareas, que se tocan en orden y nunca en paralelo:
  - `tests/unit/test_reglas.py`: T001 → T002 → T008.
  - `tests/api/test_evidencia_recomendacion.py`: T003 → T009.
  - `app/diagnostico/reglas.py`: T005 → T010.

## Oportunidades de paralelismo

- US2: T003 junto con T002 (archivos distintos). T006 puede hacerse junto con T004/T005 (archivo
  distinto, sin dependencia), pero T007 espera a T005 y T006.
- US1: T009 junto con T008.
- El resto es secuencial: el cambio es chico y casi todo pasa por `test_reglas.py`, `reglas.py` y
  `test_evidencia_recomendacion.py`.

### Ejemplo: Historia 2

```text
# Tests (en paralelo, los dos deben verse fallar):
Tarea: "T002 Evidencia vacía en tests/unit/test_reglas.py"
Tarea: "T003 Escenarios H2, SC-002 y recomendación de las 25 en tests/api/test_evidencia_recomendacion.py"

# Implementación:
Tarea: "T004 Campo en app/diagnostico/resultados.py"
Tarea: "T006 Campo en app/api/esquemas.py"        # en paralelo con T004/T005
Tarea: "T005 Ramas en app/diagnostico/reglas.py"  # después de T004
Tarea: "T007 Conversión en app/api/rutas.py"      # después de T005 y T006
```

### Ejemplo: Historia 1

```text
Tarea: "T008 Reversas en tests/unit/test_reglas.py"
Tarea: "T009 Escenarios H1, SC-001 y generadas en tests/api/test_evidencia_recomendacion.py"
```

---

## Estrategia de implementación

### MVP (Fases 1 a 3)

1. Fase 1: ajuste de los tests de 001 (rojo esperado).
2. Fase 2 (US2): el campo existe y está vacío donde corresponde.
3. Fase 3 (US1): la reversa como evidencia en "cuenta incorrecta" y "timeout".
4. **Parar y validar**: `uv run pytest` en verde y
   `curl localhost:8000/operaciones/OP-0006/diagnostico` con `"evidencia_recomendacion": ["OP-0006-E4"]`.

US2 sola no es entregable: no responde a la devolución (citar la reversa). US1 sin US2 no se puede
construir con el campo obligatorio (ver Dependencias).

### Entrega incremental

1. Fundacional → los tests de 001 dicen lo que dice el spec nuevo.
2. US2 → el campo, vacío y correcto en 18 operaciones de los datos fijos.
3. US1 → la reversa citada en las 10 restantes con diagnóstico de causa.
4. US3 → ya cubierta por los tests de 001 sin cambios.
5. Pulido → revisión contra los commits en rojo y contra `main`, quickstart.

## Notas

- Commits: ver Convenciones (un commit por tarea sin OK individual; T001 en su propio commit; push y
  revisión con `git log` y `uv run pytest` al final de cada fase).
- Revisión de cada cambio (constitución): rechazar causas sin evento citado, la reversa dentro de
  `eventos_citados`, lectura del reloj o del caso dentro de `app/diagnostico/`, azar o LLM en el
  diagnóstico, tests editados para que pasen, y datos fijos nuevos (FR-013).
