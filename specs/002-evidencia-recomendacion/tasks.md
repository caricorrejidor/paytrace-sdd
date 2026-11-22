---

description: "Lista de tareas de la feature 002-evidencia-recomendacion"
---

# Tareas: PayTrace — evidencia de la recomendación

**Entrada**: documentos de diseño en `specs/002-evidencia-recomendacion/`

**Prerrequisitos**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md), [quickstart.md](./quickstart.md)

**Tests**: obligatorios (constitución, principio III). Cada tarea de test va antes que la
implementación que cubre y termina cuando el test corre y **se ve fallar** por la razón esperada.
Un test nunca se modifica para que pase.

**Cambio explícito de tests de 001 (T001)**: FR-001 modifica 001/FR-017 (el diagnóstico pasa de tres a
cuatro campos), así que tres archivos de test de 001 quedan desactualizados respecto del spec. T001 los
actualiza en una tarea y un commit propios, **antes de tocar `app/`**, justificado contra FR-001
([research R6](./research.md#r6-tests-existentes-que-cambian)). No es editar un test para que pase:
después de T001 esos tests fallan, y pasan recién con la implementación.

**Excepciones explícitas al rojo→verde**: T011 (historia 3) y T012 (SC-005) verifican comportamiento
que ya se cumple sin implementación nueva: las respuestas sin diagnóstico no tienen la clave por
construcción (research R3, R5) y las reglas ya son deterministas. Son guardas de regresión: se
escriben, terminan cuando pasan y se commitean en verde.

**Organización**: por historia de usuario del spec, con un orden que no es el de prioridad (ver
Dependencias): la historia 2 va antes que la 1, porque el campo es obligatorio (research R3) y, al
agregarlo, todas las ramas de las reglas tienen que devolver algo. Escribir primero los tests de
"vacía" (historia 2) hace que se vean fallar antes de que exista el campo. Después, la historia 1 suma
las reversas.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias de tareas pendientes).
- **[USn]**: historia de usuario del spec de la 002 a la que pertenece la tarea.
- Cada tarea nombra el archivo que toca y cierra con **Terminada cuando**.

## Convenciones

- Mismas convenciones que [001/tasks.md](../001-diagnostico-transferencias/tasks.md#convenciones),
  con estas precisiones:
- "Ve fallar" = `uv run pytest <archivo>` termina con fallos o errores causados por la pieza que
  falta (`TypeError` por el cuarto argumento de `Diagnostico`, `KeyError` o assert por la clave
  `evidencia_recomendacion`), no por un error del propio test.
- En `tests/api/test_evidencia_recomendacion.py`, los tests de escenarios se llaman
  `test_h<historia>_e<escenario>_<descripción>`, donde la historia y el escenario son **los del spec de
  la 002**, y llevan como docstring el Dado/Cuando/Entonces del spec.
- Los tests nuevos de reglas van en `tests/unit/test_reglas.py`, en una sección propia
  `# --- Evidencia de la recomendación (feature 002) ---`, y reutilizan el helper `trace()` y las
  constantes del archivo (research R7).
- Los tests comparan contra **textos e IDs literales** escritos en el propio test, nunca contra
  constantes de `app/diagnostico/textos.py`.
- Las operaciones OK o con traces raros que no están en los datos fijos se arman dentro del test
  (FR-013): en reglas, con `trace()`; en API, insertándolas con `repositorio.agregar` como en
  `tests/api/test_h2_sin_respaldo.py`, o generándolas con `POST /operaciones`.
- Durante `/speckit-implement`, cada tarea se commitea al terminar con el skill `conventional-commit`,
  **sin esperar OK** por commit. Las tareas de test se commitean cuando el test **se ve fallar**
  (commit en rojo, tipo `test`), antes de la implementación que lo pone en verde. T001 va en su propio
  commit de tipo `test`, que cita FR-001 en el cuerpo. Ese commit en rojo es la referencia contra la
  que T013 verifica que el test no cambió.
- Al terminar cada fase, la implementación **se frena** y muestra el `git log` de los commits de la
  fase y el resultado de `uv run pytest` para revisión. La fase siguiente empieza recién con el OK.

---

## Fase 1: Fundacional — ajuste de los tests de 001 al spec nuevo

**Propósito**: que los tests de 001 que comparan el diagnóstico completo digan lo que dice el spec de
la 002 (cuatro campos), antes de tocar `app/`.

**⚠️ CRÍTICO**: ninguna historia empieza hasta terminar esta fase. Línea base antes de empezar:
`uv run pytest` da 292 passed.

- [ ] T001 Actualizar, justificado por FR-001 (modifica 001/FR-017) y sin cambiar ninguna otra cosa, tres archivos de test de 001. En `tests/unit/test_reglas.py`, sumar el cuarto argumento a cada `Diagnostico(...)` esperado, con el valor de la tabla de data-model.md: `test_am04_…` → `()`; `test_ac01_es_cuenta_incorrecta_y_cita_el_rechazo` → `("OP-0100-E4",)`; `test_ab05_con_reversa_posterior_es_timeout_con_reintento` → `("OP-0100-E5",)`; `test_ab05_sin_reversa_…` y `test_ab05_con_reversa_anterior_…` → `()`; la constante `NO_CONCLUYENTE_SIN_CLAVE` → `()`; los tres `Diagnostico("no concluyente", …, CONTRADICTORIA)` → `()`. En `tests/api/test_h1_diagnostico_con_evidencia.py`, sumar `"evidencia_recomendacion"` a `CLAVES_DIAGNOSTICO`. En `tests/api/test_h2_sin_respaldo.py`, sumar `"evidencia_recomendacion": []` a los cinco cuerpos completos de `"tipo": "diagnostico"` (`test_h2_e1`, `test_h2_e5`, `test_h2_e6`, `test_h2_e7` y la segunda aserción de `test_generada_usa_la_hora_del_pedido_como_hora_de_referencia`). Los cuerpos `sin_fallo` y `en_curso` **no** se tocan (FR-007). **Terminada cuando**: `git diff` muestra solo esos cambios; `uv run pytest` muestra en rojo exactamente los tests tocados que comparan un diagnóstico (`TypeError` en `test_reglas.py`; assert de claves o de cuerpo en `test_h1` y `test_h2`), y el resto sigue en verde. El commit `test` cita FR-001 en el cuerpo.

**Checkpoint**: suite en rojo solo en los tests ajustados por T001. Es el rojo esperado: el spec
cambió y la app todavía no.

---

## Fase 2: Historia 2 — Evidencia de la recomendación vacía cuando no hay evento que la respalde (P1)

**Objetivo**: el diagnóstico tiene el cuarto campo, `evidencia_recomendacion`, siempre presente y vacío
en fondos insuficientes, timeout sin reversa y "no concluyente", aunque el trace tenga reversas.

**Prueba independiente**: pedir el diagnóstico de `OP-0001` a `OP-0005`, `OP-0016` a `OP-0025` y
`OP-0028` a `OP-0030`, y verificar que todas traen `"evidencia_recomendacion": []` y que causa, citas y
recomendación son las de 001.

### Tests de la Historia 2 (primero; deben verse fallar) ⚠️

- [ ] T002 [US2] Agregar en `tests/unit/test_reglas.py`, en la sección nueva `# --- Evidencia de la recomendación (feature 002) ---`, los tests de evidencia vacía que T001 no cubre: (a) escenario 4 de la historia 1, que afirma evidencia vacía: `trace(ORDEN, DEBITO, AC01)` → `Diagnostico("cuenta incorrecta", ("OP-0100-E3",), "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó", ())` (FR-003); (b) FR-008 en AC01: `trace(ORDEN, DEBITO, REVERSA, AC01)` → misma causa y recomendación, cita `("OP-0100-E4",)`, evidencia `()`; (c) FR-006 con pendiente vencida y reversa: `trace(ORDEN, DEBITO, REVERSA)` en estado `pendiente` a 15 min → `Diagnostico("no concluyente", (), "Pedir los logs del proveedor desde el último evento conocido", ())`; (d) FR-011: 5 llamadas iguales para (a) y (b) dan el mismo resultado. Depende de T001 (mismo archivo). **Terminada cuando**: los tests nuevos se ven fallar con `TypeError` (Diagnostico no acepta un cuarto argumento).
- [ ] T003 [P] [US2] Crear `tests/api/test_evidencia_recomendacion.py` con un helper `_diagnostico(cliente, id)` (status 200, `tipo == "diagnostico"`, claves exactamente `{tipo, causa, eventos_citados, recomendacion, evidencia_recomendacion}`) y los escenarios de la historia 2: `test_h2_e1` (`OP-0001`), `test_h2_e2` (`OP-0016`), `test_h2_e3` (`OP-0021`), `test_h2_e4` (`OP-0028`), `test_h2_e5` (`OP-0029`) y `test_h2_e6` (`OP-0030`). Cada uno verifica `evidencia_recomendacion == []` y causa, `eventos_citados` y recomendación literales de 001 (`["OP-0001-E2"]`, `["OP-0016-E4"]`, `[]`, `[]`, `["OP-0029-E3", "OP-0029-E4"]`, `["OP-0030-E4", "OP-0030-E5"]`). Agregar SC-002: test parametrizado sobre `OP-0001`–`OP-0005`, `OP-0016`–`OP-0025` y `OP-0028`–`OP-0030` (18 operaciones) que verifica `evidencia_recomendacion == []`. **Terminada cuando**: se ve fallar (assert de claves: la respuesta no tiene `evidencia_recomendacion`).

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
es exactamente la reversa del débito de cada trace (`OP-000n-E4` / `OP-00nn-E5`) y que no está en
`eventos_citados`.

### Tests de la Historia 1 (primero; deben verse fallar) ⚠️

- [ ] T008 [US1] Agregar en `tests/unit/test_reglas.py`, en la sección de la feature 002: (a) escenario 5: `trace(ORDEN, DEBITO, AC01, REVERSA, REVERSA)` → `Diagnostico("cuenta incorrecta", ("OP-0100-E3",), "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó", ("OP-0100-E4", "OP-0100-E5"))`. No es "no concluyente" (FR-012). (b) AB05 con dos reversas: `trace(ORDEN, DEBITO, ENVIO, AB05, REVERSA, REVERSA)` → "timeout", cita `("OP-0100-E4",)`, "El débito ya se devolvió: se puede reintentar la transferencia", evidencia `("OP-0100-E5", "OP-0100-E6")`. (c) FR-008 mixto: `trace(ORDEN, DEBITO, REVERSA, AC01, REVERSA)` → evidencia `("OP-0100-E5",)` (la reversa anterior no cuenta). (d) La reversa nunca está en las citas: para (a), (b) y (c), `set(r.eventos_citados) & set(r.evidencia_recomendacion) == set()` (FR-009). Depende de T005 (mismo archivo). **Terminada cuando**: (a), (b) y (c) se ven fallar por assert (la evidencia es `()`).
- [ ] T009 [P] [US1] Agregar en `tests/api/test_evidencia_recomendacion.py`: `test_h1_e1` (`OP-0006`: causa "cuenta incorrecta", `eventos_citados == ["OP-0006-E3"]`, `evidencia_recomendacion == ["OP-0006-E4"]`); `test_h1_e2` (`OP-0011`: "timeout", `["OP-0011-E4"]`, "El débito ya se devolvió: se puede reintentar la transferencia", evidencia `["OP-0011-E5"]`); `test_h1_e3` parametrizado sobre `OP-0006`–`OP-0015` (el ID de la evidencia no está en `eventos_citados`). SC-001: parametrizado sobre `OP-0006`–`OP-0015`, toma el trace con `GET /operaciones/{id}` y verifica que la evidencia es exactamente `[ID del único evento reversa_debito]` y que ese evento está después del evento citado. FR-011 con generadas: `POST /operaciones` con `cuenta_incorrecta` y con `timeout_con_reversa`, y para cada una la evidencia es el ID de la `reversa_debito` de su trace. Depende de T003 (mismo archivo). **Terminada cuando**: los tests nuevos se ven fallar por assert (`[]` en lugar del ID).

### Implementación de la Historia 1

- [ ] T010 [US1] Implementar en `app/diagnostico/reglas.py` la función privada `_reversas_posteriores(clave, eventos) -> tuple[str, ...]` (IDs de los `reversa_debito` que están después de la posición de `clave` en el trace, en el orden del trace; research R4) y usarla en `_con_un_evento_clave()`: AC01 → evidencia = reversas; AB05 → evidencia = reversas, y la recomendación "con reversa" si `reversas` no está vacía (reemplaza el `any(...)` actual por el mismo cálculo). AM04 y las ramas "no concluyente" siguen en `()`. Depende de T008 y T009. **Terminada cuando**: `uv run pytest` pasa completo, incluidos los dos tests de T001 que quedaban en rojo, `test_reglas_aislamiento.py` y `test_conjunto_evaluacion.py` (SC-004).

**Checkpoint**: historias 1 y 2 completas; suite completa en verde. Es el MVP de la feature.

---

## Fase 4: Historia 3 — Sin campo de evidencia cuando no hay diagnóstico (P2)

**Objetivo**: confirmar que las respuestas `sin_fallo` y `en_curso` no tienen la clave
`evidencia_recomendacion` (FR-007).

**Prueba independiente**: pedir el diagnóstico de una OK insertada para la prueba, de una OK generada,
de `OP-0026` y de `OP-0027`, y verificar que ninguna respuesta tiene la clave.

- [ ] T011 [US3] Agregar en `tests/api/test_evidencia_recomendacion.py` (excepción al rojo→verde, ver Tests): `test_h3_e1`, una operación OK con `origen="generada"` y `hora_referencia=None` insertada con `repositorio.agregar` (como en `test_h2_sin_respaldo.py`) → cuerpo exactamente `{"tipo": "sin_fallo", "mensaje": "La operación no tiene un fallo para investigar"}` y `"evidencia_recomendacion" not in cuerpo`; la misma verificación con una OK generada con `POST /operaciones` (`{"caso": "ok"}`); `test_h3_e2` parametrizado sobre `OP-0026` y `OP-0027` → exactamente `{"tipo": "en_curso", "mensaje": "La operación sigue en curso"}`, sin la clave (SC-003). Depende de T009 (mismo archivo). **Terminada cuando**: `uv run pytest tests/api/test_evidencia_recomendacion.py` pasa; se commitea en verde, tipo `test`.

**Checkpoint**: las 3 historias verificadas.

---

## Fase 5: Pulido y verificaciones transversales

- [ ] T012 Agregar en `tests/api/test_evidencia_recomendacion.py` SC-005 (excepción al rojo→verde, ver Tests): parametrizado sobre `OP-0001`–`OP-0025`, 5 pedidos de diagnóstico de cada operación dan la misma `evidencia_recomendacion` (y el mismo cuerpo) las 5 veces. Depende de T011 (mismo archivo). **Terminada cuando**: `uv run pytest tests/api/test_evidencia_recomendacion.py` pasa.
- [ ] T013 Correr `uv run pytest` completo y, para cada archivo de test tocado en la feature, compararlo con `git diff <commit en rojo> HEAD -- <archivo>` contra el commit de la tarea de test que lo dejó fallando: `test_reglas.py` contra T001, T002 y T008 (cada parte contra su commit); `test_h1_diagnostico_con_evidencia.py` y `test_h2_sin_respaldo.py` contra T001; `test_evidencia_recomendacion.py` contra T003 y T009. T011 y T012 no tienen commit en rojo. Verificar además que `test_reglas_aislamiento.py`, `test_conjunto_evaluacion.py` y `test_tiempos.py` (SC-004, SC-006) no cambiaron en la rama (`git diff main -- <archivo>` vacío). **Terminada cuando**: toda la suite está en verde, ningún test se editó después de su commit en rojo sin justificación contra el spec, y esos tres archivos no cambiaron.
- [ ] T014 Recorrer a mano los pasos 1 a 9 de `specs/002-evidencia-recomendacion/quickstart.md` con `uv run uvicorn app.main:app` y `curl`, y revisar en `http://localhost:8000/docs` que el esquema de la respuesta de diagnóstico muestra `evidencia_recomendacion`. **Terminada cuando**: los 9 pasos dan lo esperado y `/docs` muestra el campo.

---

## Dependencias y orden de ejecución

### Entre fases

- **Fundacional (Fase 1, T001)**: sin dependencias; **bloquea** todas las historias.
- **US2 (Fase 2)**: depende de la Fase 1. Va antes que US1 aunque las dos son P1. El campo es
  obligatorio, así que al agregarlo todas las ramas tienen que devolver un valor; si US1 fuera primero,
  los tests de "vacía" ya pasarían al escribirse y no se verían fallar.
- **US1 (Fase 3)**: depende de US2: usa el campo, el esquema y la ruta que deja US2, y completa las
  ramas AC01 y AB05 de `reglas.py`.
- **US3 (Fase 4)**: depende de US1 solo porque comparte archivo de test. No toca `app/`.
- **Pulido (Fase 5)**: después de todas las historias.

### Dentro de cada historia

- Tests → se ven fallar → `resultados.py` → `reglas.py` → `esquemas.py` → `rutas.py`.
- Archivos compartidos entre tareas, que se tocan en orden y nunca en paralelo:
  - `tests/unit/test_reglas.py`: T001 → T002 → T008.
  - `tests/api/test_evidencia_recomendacion.py`: T003 → T009 → T011 → T012.
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
Tarea: "T003 Escenarios H2 y SC-002 en tests/api/test_evidencia_recomendacion.py"

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
4. US3 → guarda de que las respuestas sin diagnóstico no cambian.
5. Pulido → determinismo, revisión contra los commits en rojo, quickstart.

## Notas

- Commits: ver Convenciones (un commit por tarea sin OK individual; T001 en su propio commit; revisión
  con `git log` y `uv run pytest` al final de cada fase).
- Revisión de cada cambio (constitución): rechazar causas sin evento citado, la reversa dentro de
  `eventos_citados`, lectura del reloj o del caso dentro de `app/diagnostico/`, azar o LLM en el
  diagnóstico, tests editados para que pasen, y datos fijos nuevos (FR-013).
