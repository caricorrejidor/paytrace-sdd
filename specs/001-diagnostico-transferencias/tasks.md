---

description: "Lista de tareas de la feature 001-diagnostico-transferencias"
---

# Tareas: PayTrace — diagnóstico de transferencias fallidas o pendientes

**Entrada**: documentos de diseño en `specs/001-diagnostico-transferencias/`

**Prerrequisitos**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md),
[contracts/datos-fijos.md](./contracts/datos-fijos.md), [quickstart.md](./quickstart.md)

**Tests**: obligatorios. La constitución (principio III, test-first) exige que los tests de la
lógica de diagnóstico se escriban y **se vean fallar** antes de implementarla; por pedido explícito,
esta lista aplica el mismo orden a **todas** las piezas: cada tarea de test va antes que la
implementación que cubre, y termina cuando el test corre y falla por la razón esperada (import
inexistente, assert, 404 de una ruta que todavía no existe). Un test nunca se modifica para que
pase (principio III).

**Excepción explícita**: T054 (tiempos) y T055 (sin conexiones externas, azar ni LLM) no siguen el
orden rojo→verde. Son verificaciones transversales sobre la app ya construida, no lógica de
diagnóstico: se escriben al final y terminan cuando pasan.

**Organización**: por historia de usuario del spec, para que cada una se implemente y se pruebe
por separado.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias de tareas pendientes).
- **[USn]**: historia de usuario del spec a la que pertenece la tarea.
- Cada tarea nombra el archivo que toca y cierra con **Terminada cuando**.

## Convenciones

- Proyecto único en la raíz: `app/` y `tests/` (ver plan, Project Structure).
- "Ve fallar" = `uv run pytest <archivo>` termina con fallos o errores de colección causados por
  la pieza que falta, no por un error del propio test.
- Los tests de escenarios se llaman `test_h<historia>_e<escenario>_<descripción>` y llevan como
  docstring el Dado/Cuando/Entonces del spec (research R11).
- Los tests comparan contra los **textos literales** del spec escritos en el propio test, nunca
  contra las constantes de `app/diagnostico/textos.py` (si no, el test sería tautológico).
- Las fixtures de API van en `tests/api/conftest.py` (no en `tests/conftest.py`) para que los tests
  unitarios no importen `app.main` antes de que exista.
- Durante `/speckit-implement`, cada tarea se commitea al terminar con el skill `conventional-commit`,
  **sin esperar OK** por commit. Las tareas de test se commitean cuando el test **se ve fallar**
  (commit en rojo, tipo `test`), antes de la implementación que lo pone en verde. Ese commit es la
  referencia contra la que T056 verifica que el test no cambió.
- Al terminar cada fase, la implementación **se frena** y muestra el `git log` de los commits de la
  fase y el resultado de `uv run pytest` para revisión; la fase siguiente empieza recién con el OK.

---

## Fase 1: Setup (infraestructura compartida)

**Propósito**: proyecto uv instalable y estructura de paquetes vacía.

- [X] T001 Crear `pyproject.toml` (nombre `paytrace`, `requires-python = ">=3.12,<3.13"`, sección `[tool.pytest.ini_options]` con `pythonpath = ["."]` y `testpaths = ["tests"]`) y `.python-version` con `3.12`. **Terminada cuando**: `uv sync` termina sin error y `uv run python --version` muestra 3.12.
- [X] T002 Agregar dependencias con uv en `pyproject.toml` y `uv.lock`: `uv add fastapi==0.165.0 uvicorn==0.54.0` y `uv add --dev pytest==9.2.0 httpx==0.28.1` (research R1). Depende de T001. **Terminada cuando**: `uv.lock` existe, fija esas versiones y `uv run python -c "import fastapi, uvicorn, pytest, httpx"` no da error.
- [X] T003 [P] Crear los paquetes vacíos `app/__init__.py`, `app/diagnostico/__init__.py`, `app/simulacion/__init__.py`, `app/almacen/__init__.py`, `app/api/__init__.py` y los directorios `app/datos/`, `tests/unit/`, `tests/api/`. **Terminada cuando**: `uv run python -c "import app.diagnostico, app.simulacion, app.almacen, app.api"` no da error y `uv run pytest` termina con "no tests ran" (código 5).
- [X] T004 [P] Crear `.gitignore` con `.venv/`, `__pycache__/`, `.pytest_cache/`. **Terminada cuando**: después de `uv run pytest`, `git status` no muestra ninguno de esos directorios.

---

## Fase 2: Fundacional (prerrequisitos de todas las historias)

**Propósito**: tipos de dominio, repositorio básico, carga y validación de los 30 datos fijos, y
la app FastAPI arrancando con ellos.

**⚠️ CRÍTICO**: ninguna historia empieza hasta terminar esta fase.

### Dominio

- [X] T005 [P] Escribir `tests/unit/test_dominio.py`: (a) los enums `Estado`, `Emisor`, `CodigoMotivo`, `TipoEvento`, `Caso` tienen exactamente los valores de data-model.md; (b) `EMISOR_POR_TIPO` asigna a cada uno de los 9 `TipoEvento` el emisor de la tabla TipoEvento; (c) `TIPOS_RECHAZO` es exactamente `{rechazo_origen, rechazo_banco_destino, rechazo_timeout}`; (d) `Evento` y `Operacion` son inmutables (asignar un campo lanza `FrozenInstanceError`); (e) `es_id_valido` acepta `"OP-0001"` y `"OP-9999"` y rechaza `"op1"`, `"op-0001"`, `""`, `" OP-0001"`, `"OP-0001 "`, `"OP-0001\n"`, `"OP-001"`, `"OP-00001"` y `"OP-٠٠٠١"` (dígitos arábigo-índicos). **Terminada cuando**: el archivo existe y se ve fallar por `ImportError` de `app.dominio`.
- [X] T006 Implementar `app/dominio.py` (solo stdlib): los 5 enums (`StrEnum`), `EMISOR_POR_TIPO`, `TIPOS_RECHAZO`, dataclasses `frozen=True` `Evento(id, momento, tipo, emisor, codigo)` y `Operacion(id, estado, eventos: tuple[Evento, ...], caso, hora_referencia, origen: Literal["fija", "generada"])`, y `es_id_valido(texto)` con `re.fullmatch(r"OP-[0-9]{4}", texto)` (no `\d` ni `$`, que aceptan dígitos Unicode y un `\n` final; research R10). **Terminada cuando**: `uv run pytest tests/unit/test_dominio.py` pasa completo.

### Repositorio básico

- [X] T007 [P] Escribir `tests/unit/test_repositorio.py` (parte básica): `Repositorio(operaciones)` permite `obtener(id)` (devuelve la operación o `None`) y `cantidad()`; `agregar(op)` suma una operación y lanza `ValueError` si el ID ya existe, sin modificar el contenido; el constructor lanza `ValueError` con IDs repetidos. **Terminada cuando**: se ve fallar por `ImportError` de `app.almacen.repositorio`.
- [X] T008 Implementar en `app/almacen/repositorio.py` la clase `Repositorio` con un `dict[str, Operacion]` y los métodos `obtener`, `cantidad` y `agregar` (sin `siguiente_id` ni `listar`, que llegan en US4 y US5). Depende de T006. **Terminada cuando**: `uv run pytest tests/unit/test_repositorio.py` pasa.

### Carga y validación de datos fijos

- [X] T009 [P] Escribir en `tests/unit/test_carga_datos.py` los tests de `cargar_archivo(ruta)` con archivos JSON armados en `tmp_path`: un archivo válido (formato de contracts/datos-fijos.md) se convierte en `Operacion`/`Evento` de dominio con momentos UTC con zona y `origen="fija"`; y se rechaza con `ErrorDatosFijos` (mensaje que nombra el archivo y el ID de la operación) cada regla por operación de data-model.md: 1 (ID mal formado y ID `OP-9xxx`), 3 (sin eventos; momentos iguales; momentos decrecientes), 4 (momento sin zona; hora de referencia sin zona), 5 (rechazo sin código; evento no rechazo con código; código fuera de AM04/AC01/AB05), 6 (emisor que no coincide con el tipo) y 7 (falta `hora_referencia`). **Terminada cuando**: se ve fallar por `ImportError` de `app.almacen.carga`.
- [X] T010 Agregar en `tests/unit/test_carga_datos.py` los tests de `cargar_datos_fijos(directorio)` con tres archivos armados en `tmp_path`: devuelve las operaciones de los tres archivos; rechaza con `ErrorDatosFijos` la regla 2 (ID de operación repetido dentro de un archivo y entre archivos; ID de evento repetido dentro de un archivo y entre archivos) y la regla 8 (cantidades distintas de 25/2/3; evaluación sin 5 operaciones por cada caso salvo OK, con una operación `caso: "ok"` o sin `caso`); y rechaza si falta alguno de los tres archivos. Depende de T009 (mismo archivo). **Terminada cuando**: los tests nuevos se ven fallar.
- [ ] T011 Implementar en `app/almacen/carga.py` los modelos Pydantic del archivo (`EventoArchivo`, `OperacionArchivo`, `ArchivoDatos`) con las validaciones de las reglas 1 y 3 a 7, la excepción `ErrorDatosFijos` y `cargar_archivo(ruta) -> list[Operacion]` que convierte a los tipos de `app.dominio`. Depende de T006 y T009. **Terminada cuando**: pasan los tests de T009.
- [ ] T012 Implementar en `app/almacen/carga.py` `cargar_datos_fijos(directorio) -> list[Operacion]`: lee `conjunto_evaluacion.json`, `prueba_plazo.json` y `casos_borde.json`, y valida las reglas 2 y 8 entre archivos. Depende de T010 y T011. **Terminada cuando**: `uv run pytest tests/unit/test_carga_datos.py` pasa completo.

### Archivos de datos fijos (30 operaciones)

- [ ] T013 Escribir `tests/unit/test_datos_fijos.py` sobre los archivos reales de `app/datos/`, con tests **separados por archivo y por caso** (usan `cargar_archivo`, para que cada tarea de datos pueda verse en verde por su cuenta): (a) evaluación: IDs `OP-0001` a `OP-0025` en los rangos de contracts/datos-fijos.md, cada operación con el estado y la secuencia exacta de tipos y códigos de su caso en la tabla del spec, IDs de evento `{op}-E{n}` desde 1, hora de referencia posterior al último evento en las fallidas y **más de 10 min** posterior en las 5 de trace incompleto, y momentos distintos entre operaciones (no son copias); (b) plazo: `OP-0026` y `OP-0027` pendientes, sin `caso`, IDs de evento `{op}-E{n}` desde 1, orden enviada → débito en origen, último evento exactamente 2 min y exactamente 10 min antes de su hora de referencia; (c) casos borde: `OP-0028` a `OP-0030` fallidas, sin `caso`, IDs de evento `{op}-E{n}` desde 1, con las secuencias de FR-029; (d) los JSON solo usan las claves del contrato (`operaciones`, `id`, `estado`, `caso`, `hora_referencia`, `eventos`, `momento`, `tipo`, `emisor`, `codigo`), sin datos personales (FR-028, SC-008); (e) `cargar_datos_fijos(Path("app/datos"))` devuelve 30 operaciones `OP-0001` a `OP-0030`. Depende de T012 (usa `cargar_archivo` y `cargar_datos_fijos`). **Terminada cuando**: se ve fallar porque los archivos no existen.
- [ ] T014 Escribir en `app/datos/conjunto_evaluacion.json` las operaciones `OP-0001` a `OP-0010`: 5 `fondos_insuficientes` (orden enviada → rechazo en origen AM04, clave en `E2`) y 5 `cuenta_incorrecta` (orden enviada → débito en origen → rechazo banco destino AC01 → reversa del débito, clave en `E3`), estado `fallida`, horarios distintos entre operaciones. Depende de T013. **Terminada cuando**: pasan los tests de T013 para esos dos casos.
- [ ] T015 Agregar en `app/datos/conjunto_evaluacion.json` las operaciones `OP-0011` a `OP-0020`: 5 `timeout_con_reversa` (orden → débito → envío al proveedor → rechazo timeout AB05 → reversa) y 5 `timeout_sin_reversa` (orden → débito → envío al proveedor → rechazo timeout AB05), clave en `E4`, estado `fallida`. Depende de T014 (mismo archivo). **Terminada cuando**: pasan los tests de T013 para esos dos casos.
- [ ] T016 Agregar en `app/datos/conjunto_evaluacion.json` las operaciones `OP-0021` a `OP-0025`: `trace_incompleto`, estado `pendiente`, orden enviada → débito en origen, hora de referencia 15 min después del último evento. Depende de T015 (mismo archivo). **Terminada cuando**: pasan todos los tests de T013 sobre el conjunto de evaluación (25 operaciones).
- [ ] T017 [P] Escribir `app/datos/prueba_plazo.json` con `OP-0026` (último evento 2 min antes de su hora de referencia) y `OP-0027` (exactamente 10 min antes), ambas `pendiente` y sin `caso`, según contracts/datos-fijos.md. Depende de T013. **Terminada cuando**: pasan los tests de T013 sobre prueba de plazo.
- [ ] T018 [P] Escribir `app/datos/casos_borde.json` con `OP-0028` (orden → débito → reversa), `OP-0029` (orden → débito → rechazo banco destino AC01 en `E3` → rechazo timeout AB05 en `E4` → reversa) y `OP-0030` (orden → débito → envío al proveedor → rechazo timeout AB05 en `E4` → rechazo timeout AB05 en `E5`), todas `fallida`, sin `caso`. Depende de T013. **Terminada cuando**: pasan los tests de T013 sobre casos borde y, con T016 y T017 hechas, `uv run pytest tests/unit/test_datos_fijos.py` pasa completo.

### Dependencias de la API y arranque

- [ ] T019 [P] Escribir `tests/unit/test_dependencias.py`: `operacion_o_error(texto, repositorio)` devuelve la operación si existe; lanza `ErrorPayTrace(400, "Ingresá un ID con formato OP-0000")` con `None`, `""`, `"op1"`, `"op-0001"` y `" OP-0001"`, sin consultar el repositorio (un repositorio falso que falla si se lo llama); lanza `ErrorPayTrace(404, "Operación no encontrada")` con `"OP-9999"`. `obtener_reloj()` devuelve un callable que da un `datetime` con zona UTC. **Terminada cuando**: se ve fallar por `ImportError` de `app.api.dependencias`.
- [ ] T020 Implementar `app/api/dependencias.py`: excepción `ErrorPayTrace(status, detalle)`, `operacion_o_error(texto, repositorio)` (usa `es_id_valido`), `obtener_repositorio(request)` (devuelve `request.app.state.repositorio`) y `obtener_reloj()` (devuelve `lambda: datetime.now(UTC)`; es el **único** lugar de la app que lee el reloj). Depende de T006, T008 y T019. **Terminada cuando**: `uv run pytest tests/unit/test_dependencias.py` pasa.
- [ ] T021 [P] Escribir `tests/api/conftest.py`: constante `HORA_FIJA = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)`; fixture `reloj` (objeto con atributo `ahora`, inicializado en `HORA_FIJA`, que cada test puede cambiar); fixture `cliente` que importa `app.main` dentro de la fixture, sobrescribe `obtener_reloj` con `app.dependency_overrides` para que devuelva una función que da la hora del reloj falso (`lambda: reloj.ahora`, leída en cada llamada; así `reloj()` en las rutas funciona igual que con el reloj real), abre `TestClient(app)` como context manager (corre el lifespan: repositorio fresco por test) y limpia los overrides al salir; fixture `repositorio` que devuelve `cliente.app.state.repositorio`. **Terminada cuando**: el archivo existe y `uv run pytest tests/api` no da errores propios del conftest (sin tests todavía).
- [ ] T022 Escribir `tests/api/test_arranque.py`: al arrancar, `repositorio.cantidad() == 30` y existen `OP-0001` a `OP-0030`; FR-009: agregar una operación `origen="generada"` con `repositorio.agregar`, cerrar el cliente, abrir uno nuevo y verificar que vuelven a ser 30 y que la agregada no está. Depende de T021. **Terminada cuando**: se ve fallar por `ImportError` de `app.main`.
- [ ] T023 Implementar `app/main.py` y `app/api/rutas.py` (este último solo con un `APIRouter` vacío): `FastAPI` con `lifespan` que crea `Repositorio(cargar_datos_fijos(<ruta de app/datos>))` en `app.state.repositorio` (si la carga falla, la app no arranca), handler de `ErrorPayTrace` que responde `{"detalle": ...}` con su status, e `include_router` del router. Depende de T012, T016–T018, T020 y T022. **Terminada cuando**: `uv run pytest tests/api/test_arranque.py` pasa y `uv run uvicorn app.main:app` arranca sin error.

**Checkpoint**: base lista; `uv run pytest` en verde. Las historias pueden empezar.

---

## Fase 3: Historia 1 — Diagnosticar una operación fallida con evidencia (P1) 🎯 MVP

**Objetivo**: `GET /operaciones/{id}/diagnostico` nombra la causa de una fallida con exactamente un
evento clave, cita ese evento y da la recomendación de la tabla.

**Prueba independiente**: con el conjunto de evaluación cargado, pedir el diagnóstico de las 20
operaciones con trace completo (`OP-0001` a `OP-0020`) y verificar causa, evento citado y
recomendación contra la tabla de casos.

### Tests de la Historia 1 (primero; deben verse fallar) ⚠️

- [ ] T024 [P] [US1] Escribir `tests/unit/test_reglas_aislamiento.py` (research R2): (a) en `app/diagnostico/` existen `__init__.py`, `reglas.py`, `resultados.py` y `textos.py` (así el test no pasa vacío antes de implementar); (b) recorriendo el AST de cada archivo, falla si hay imports de `fastapi`, `pydantic`, `random`, `secrets`, `time`, `app.api`, `app.almacen` o `app.simulacion`; llamadas a `now`, `utcnow` o `today`; o identificadores (nombres, atributos, argumentos, alias de import) `Caso` o `caso`. No mira docstrings ni comentarios. **Terminada cuando**: se ve fallar porque faltan `reglas.py`, `resultados.py` y `textos.py`.
- [ ] T025 [P] [US1] Escribir en `tests/unit/test_reglas.py` (con un helper local para armar eventos) los tests de causa nombrada de `diagnosticar(estado, eventos, hora_referencia)`, todos con estado `fallida`: AM04 en `rechazo_origen` → `Diagnostico("fondos insuficientes", (id del rechazo,), "Avisar al cliente que no tenía saldo. No se debitó nada")`; AC01 en `rechazo_banco_destino` → "cuenta incorrecta" con su recomendación; AB05 en `rechazo_timeout` con `reversa_debito` **posterior** → "timeout", "El débito ya se devolvió: se puede reintentar la transferencia"; AB05 sin reversa → "timeout", "El débito todavía no se devolvió: pedir la reversa antes de reintentar. Si se reintenta antes, se cobra dos veces"; AB05 con `reversa_debito` **anterior** al rechazo → recomendación "sin reversa" (FR-020); el resultado de una fallida no cambia con dos horas de referencia distintas; 5 llamadas con la misma entrada dan resultados iguales (FR-027). **Terminada cuando**: se ve fallar por `ImportError` de `app.diagnostico`.
- [ ] T026 [P] [US1] Escribir `tests/api/test_h1_diagnostico_con_evidencia.py`: `test_h1_e1` a `test_h1_e4` con `OP-0001` (cita `["OP-0001-E2"]`), `OP-0006` (`["OP-0006-E3"]`), `OP-0011` y `OP-0016` (`["OP-00xx-E4"]`): status 200, cuerpo con claves exactamente `{tipo, causa, eventos_citados, recomendacion}`, `tipo == "diagnostico"`, causa y recomendación literales del spec; errores comunes: `/operaciones/op1/diagnostico` → 400 `{"detalle": "Ingresá un ID con formato OP-0000"}` y `/operaciones/OP-9999/diagnostico` → 404 `{"detalle": "Operación no encontrada"}`. **Terminada cuando**: se ve fallar (404 de ruta inexistente).
- [ ] T027 [P] [US1] Escribir `tests/api/test_conjunto_evaluacion.py` (parte SC-002/SC-004): parametrizado sobre `OP-0001` a `OP-0020`, toma el `caso` de la operación desde la fixture `repositorio` (nunca de la API), pide el diagnóstico y verifica que la causa es la de su caso y que `eventos_citados` tiene exactamente un ID, que es el del único evento clave del trace de esa operación; y SC-007 sobre las mismas 20: 5 pedidos de diagnóstico de cada una dan el mismo cuerpo las 5 veces. **Terminada cuando**: se ve fallar (ruta inexistente).

### Implementación de la Historia 1

- [ ] T028 [P] [US1] Escribir `app/diagnostico/textos.py` (sin imports): constantes con los textos literales del spec para las 4 causas (`fondos insuficientes`, `cuenta incorrecta`, `timeout`, `no concluyente`), las 6 recomendaciones de la tabla de data-model.md y los mensajes "La operación no tiene un fallo para investigar" y "La operación sigue en curso". **Terminada cuando**: el archivo existe con esas constantes y `uv run python -c "import app.diagnostico.textos"` no da error.
- [ ] T029 [P] [US1] Escribir `app/diagnostico/resultados.py` (solo stdlib): dataclasses `frozen=True` `Diagnostico(causa: str, eventos_citados: tuple[str, ...], recomendacion: str)`, `SinFallo(mensaje)` y `EnCurso(mensaje)`, y el alias `Resultado = Diagnostico | SinFallo | EnCurso`. **Terminada cuando**: `uv run python -c "from app.diagnostico.resultados import Diagnostico, SinFallo, EnCurso, Resultado"` no da error.
- [ ] T030 [US1] Implementar `app/diagnostico/reglas.py` y exportar `diagnosticar` en `app/diagnostico/__init__.py`: `es_evento_clave(evento)` (solo `rechazo_origen`+AM04, `rechazo_banco_destino`+AC01, `rechazo_timeout`+AB05) y la rama "exactamente un evento clave" de `diagnosticar` (causa por código, cita ese evento, recomendación; para AB05 busca `reversa_debito` posterior). Las demás ramas lanzan `NotImplementedError` hasta US2 (rojo → verde mínimo). Solo importa stdlib, `app.dominio` y los módulos de `app/diagnostico/`. Depende de T024, T025, T028 y T029. **Terminada cuando**: `uv run pytest tests/unit/test_reglas.py tests/unit/test_reglas_aislamiento.py` pasa.
- [ ] T031 [US1] Agregar en `app/api/esquemas.py` los modelos Pydantic `DiagnosticoSalida` (`tipo: Literal["diagnostico"]`, `causa`, `eventos_citados: list[str]`, `recomendacion`) y `ErrorSalida` (`detalle`). **Terminada cuando**: `uv run python -c "from app.api.esquemas import DiagnosticoSalida, ErrorSalida"` no da error.
- [ ] T032 [US1] Agregar en `app/api/rutas.py` `GET /operaciones/{id}/diagnostico`: `operacion_o_error`, hora de referencia `op.hora_referencia`, llamada `diagnosticar(op.estado, op.eventos, hora)` (sin pasar `op.caso`) y conversión a `DiagnosticoSalida`; documenta 400/404 con `ErrorSalida`. Depende de T023, T030 y T031. **Terminada cuando**: `uv run pytest tests/api/test_h1_diagnostico_con_evidencia.py tests/api/test_conjunto_evaluacion.py` pasa.

**Checkpoint**: diagnóstico con evidencia de las 20 fallidas con trace completo. Todavía no es entregable: las OK, las pendientes y los casos borde dan `NotImplementedError` hasta US2.

---

## Fase 4: Historia 2 — No diagnosticar sin respaldo (P1)

**Objetivo**: responder "no concluyente" (sin citas o citando los eventos en conflicto), "La
operación sigue en curso" y "La operación no tiene un fallo para investigar", sin nombrar causa.

**Prueba independiente**: pedir el diagnóstico de `OP-0021` a `OP-0025`, de una operación OK
insertada directamente en el repositorio (con `origen="generada"`; con US4 se agrega la prueba de
punta a punta con una OK generada), de `OP-0026`/`OP-0027` y de `OP-0028` a `OP-0030`, y verificar las respuestas sin causa.

### Tests de la Historia 2 (primero; deben verse fallar) ⚠️

- [ ] T033 [US2] Agregar en `tests/unit/test_reglas.py` los tests sin causa: estado `ok` → `SinFallo("La operación no tiene un fallo para investigar")`; pendiente con último evento 2 min antes, exactamente 10 min antes y **después** de la hora de referencia → `EnCurso("La operación sigue en curso")`; pendiente con 10 min 1 s y con 15 min → `Diagnostico("no concluyente", (), "Pedir los logs del proveedor desde el último evento conocido")`; fallida sin evento clave con la hora de referencia a 1 min del último evento → "no concluyente" sin citas **enseguida** (el plazo es solo para pendientes); fallida con rechazos que no son clave (`rechazo_origen`+AC01, `rechazo_timeout`+AM04, `rechazo_banco_destino`+AB05) → "no concluyente" sin citas; AC01 + AB05 → "no concluyente", cita los dos en orden del trace, "Evidencia contradictoria: revisar manualmente los eventos citados"; AB05 + AB05 → "no concluyente" (no "timeout"), cita los dos; tres eventos clave → cita los tres; determinismo (5 llamadas iguales) para cada variante. Depende de T030 (mismo archivo). **Terminada cuando**: los tests nuevos se ven fallar (`NotImplementedError` o assert).
- [ ] T034 [P] [US2] Escribir `tests/api/test_h2_sin_respaldo.py`: `test_h2_e1` (`OP-0021`), `test_h2_e2` (operación OK con `origen="generada"` y `hora_referencia=None` insertada con `repositorio.agregar`) → `{"tipo": "sin_fallo", "mensaje": ...}` con claves exactamente `{tipo, mensaje}`, `test_h2_e3` (`OP-0026`) y `test_h2_e4` (`OP-0027`) → `en_curso` con claves exactamente `{tipo, mensaje}`, `test_h2_e5` (`OP-0028`, sin citas), `test_h2_e6` (`OP-0029`, cita `["OP-0029-E3", "OP-0029-E4"]`), `test_h2_e7` (`OP-0030`, cita `["OP-0030-E4", "OP-0030-E5"]`), con textos literales; y hora de referencia de las generadas (FR-026): una pendiente generada insertada con su último evento 5 min antes de `reloj.ahora` → `en_curso`, y tras mover `reloj.ahora` a 11 min → "no concluyente". **Terminada cuando**: se ve fallar (respuestas sin las variantes `sin_fallo`/`en_curso` o error con `hora_referencia=None`).
- [ ] T035 [P] [US2] Agregar en `tests/api/test_conjunto_evaluacion.py` SC-003 (`OP-0021` a `OP-0025` → "no concluyente", `eventos_citados == []`) y SC-007 para `OP-0021` a `OP-0025` (5 pedidos de diagnóstico de cada una dan el mismo cuerpo las 5 veces; `OP-0001` a `OP-0020` ya están en T027). Depende de T027 (mismo archivo). **Terminada cuando**: los tests nuevos de SC-003 y SC-007 se ven fallar.

### Implementación de la Historia 2

- [ ] T036 [US2] Completar `diagnosticar` en `app/diagnostico/reglas.py` con el orden de research R3: OK → `SinFallo`; pendiente con `hora_referencia − último.momento <= timedelta(minutes=10)` → `EnCurso`; más de un evento clave → "no concluyente" citando todos en orden del trace; ninguno → "no concluyente" sin citas; exactamente uno → rama de US1. Sin `NotImplementedError`. Depende de T033. **Terminada cuando**: `uv run pytest tests/unit/test_reglas.py tests/unit/test_reglas_aislamiento.py` pasa completo.
- [ ] T037 [US2] Agregar en `app/api/esquemas.py` `SinFalloSalida` (`tipo: Literal["sin_fallo"]`, `mensaje`), `EnCursoSalida` (`tipo: Literal["en_curso"]`, `mensaje`) y `DiagnosticoRespuesta = Annotated[DiagnosticoSalida | SinFalloSalida | EnCursoSalida, Field(discriminator="tipo")]`. **Terminada cuando**: `uv run python -c "from app.api.esquemas import DiagnosticoRespuesta"` no da error.
- [ ] T038 [US2] Actualizar en `app/api/rutas.py` el endpoint de diagnóstico: `response_model=DiagnosticoRespuesta`, conversión de las tres variantes de `Resultado`, y hora de referencia `op.hora_referencia` si `op.origen == "fija"` o `reloj()` (dependencia `obtener_reloj`) si es generada. Depende de T036 y T037. **Terminada cuando**: `uv run pytest tests/api/test_h2_sin_respaldo.py tests/api/test_conjunto_evaluacion.py tests/api/test_h1_diagnostico_con_evidencia.py` pasa.

**Checkpoint**: Historias 1 y 2 completas; todo el módulo de reglas en verde.

---

## Fase 5: Historia 3 — Buscar una operación y ver su trace (P1)

**Objetivo**: `GET /busqueda?id=` y `GET /operaciones/{id}` devuelven la operación con su trace en
orden cronológico, con los errores literales de ID.

**Prueba independiente**: buscar IDs existentes, inexistentes y mal escritos, y abrir `OP-0006`
para verificar el orden de sus 4 eventos.

### Tests de la Historia 3 (primero; deben verse fallar) ⚠️

- [ ] T039 [P] [US3] Escribir `tests/api/test_h3_busqueda_y_trace.py`: `test_h3_e1` (`/busqueda?id=OP-0001` → 200, `id == "OP-0001"`); `test_h3_e2` (`OP-9999` → 404, cuerpo exactamente `{"detalle": "Operación no encontrada"}`); `test_h3_e3` parametrizado con `op1`, `op-0001`, `?id=`, sin parámetro y `%20OP-0001` → 400, cuerpo exactamente `{"detalle": "Ingresá un ID con formato OP-0000"}` (sin operación ni "Operación no encontrada"); `test_h3_e4` (`/operaciones/OP-0006` → 4 eventos, momentos estrictamente crecientes, IDs `E1` a `E4`); además: el detalle no tiene las claves `caso` ni `hora_referencia`, ni ninguna clave de diagnóstico (`tipo`, `causa`, `eventos_citados`, `recomendacion`), porque el diagnóstico se da solo cuando se pide (FR-015), `codigo` aparece solo en los rechazos, y `/operaciones/op1` → 400, `/operaciones/OP-9999` → 404. **Terminada cuando**: se ve fallar (rutas inexistentes).

### Implementación de la Historia 3

- [ ] T040 [US3] Agregar en `app/api/esquemas.py` `EventoSalida` (`id`, `momento`, `tipo`, `emisor`, `codigo` que no aparece en el JSON si es `None`), `OperacionDetalle` (`id`, `estado`, `eventos`) y la función `detalle_de(op) -> OperacionDetalle` (no copia `caso`, `hora_referencia` ni `origen`). **Terminada cuando**: `uv run python -c "from app.api.esquemas import OperacionDetalle, detalle_de"` no da error.
- [ ] T041 [US3] Agregar en `app/api/rutas.py` `GET /busqueda` (parámetro `id: str | None = None`, pasa por `operacion_o_error`) y `GET /operaciones/{id}`, ambos con `response_model=OperacionDetalle` y `response_model_exclude_none=True` (o equivalente). Depende de T023 y T040. **Terminada cuando**: `uv run pytest tests/api/test_h3_busqueda_y_trace.py` pasa.

**Checkpoint**: Historias 1, 2 y 3 funcionan cada una por su cuenta.

---

## Fase 6: Historia 4 — Generar operaciones simuladas por caso (P1)

**Objetivo**: `POST /operaciones` genera una operación de cualquiera de los 6 casos con el
siguiente ID libre, nunca `OP-9xxx`, y responde 409 si se agotaron los IDs.

**Prueba independiente**: generar una operación de cada caso y verificar estado, eventos, último
evento e ID asignado.

### Tests de la Historia 4 (primero; deben verse fallar) ⚠️

- [ ] T042 [P] [US4] Escribir `tests/unit/test_generador.py`: parametrizado sobre los 6 casos, `generar(caso, "OP-0031", ahora)` da el estado y la secuencia exacta de tipos y códigos de la tabla de casos, el evento y el último evento de la tabla de la historia 4, emisor según `EMISOR_POR_TIPO`, IDs `OP-0031-E1…En`, momentos separados por 1 s y truncados al segundo, último evento `== ahora` truncado en los casos con resultado final y `== ahora − 11 min` en `trace_incompleto` (FR-004), `caso` igual al pedido, `origen == "generada"`, `hora_referencia is None`; misma entrada → operación igual; y `diagnosticar` sobre la operación generada (con `ahora` como hora de referencia) da la causa de su caso para los 5 casos con fallo o pendiente. **Terminada cuando**: se ve fallar por `ImportError` de `app.simulacion.generador`.
- [ ] T043 [P] [US4] Agregar en `tests/unit/test_repositorio.py` los tests de generación de IDs: con los 30 fijos `siguiente_id() == "OP-0031"`; con `OP-0001` y `OP-0050` → `"OP-0051"` (no reutiliza huecos); `crear(construir)` reserva el ID, llama `construir(id)` y agrega la operación de forma atómica; con `OP-8999` presente, `siguiente_id()` lanza `IdsAgotados`, y `crear` también lo lanza, no llama `construir` y la cantidad no cambia; 20 hilos llamando `crear` a la vez obtienen 20 IDs distintos y consecutivos. Depende de T008. **Terminada cuando**: los tests nuevos se ven fallar.
- [ ] T044 [P] [US4] Escribir `tests/api/test_h4_generacion.py`: `test_h4_e1` parametrizado con los 6 casos (`POST /operaciones {"caso": ...}` → 201, estado y eventos de la tabla); `test_h4_e2` (`trace_incompleto`: último evento más de 10 min antes de `reloj.ahora`); `test_h4_e3` (primer ID `OP-0031`, segundo `OP-0032`, ninguno coincide con existentes ni empieza con `OP-9`); caso desconocido y cuerpo sin `caso` → 422; agotamiento (FR-032): con `OP-8999` agregado vía `repositorio.agregar` → 409, cuerpo exactamente `{"detalle": "No quedan IDs disponibles para generar operaciones"}` y `repositorio.cantidad()` igual que antes; punta a punta con US2: generar `ok` y pedir su diagnóstico → `sin_fallo`; generar `trace_incompleto` y diagnosticarla enseguida con el mismo `reloj.ahora` → "no concluyente" sin citas. **Terminada cuando**: se ve fallar (405/404 en `POST /operaciones`).

### Implementación de la Historia 4

- [ ] T045 [US4] Implementar `app/simulacion/generador.py` (solo stdlib y `app.dominio`, sin reloj ni azar): secuencia de `(tipo, codigo)` por `Caso` y `generar(caso, id_operacion, ahora) -> Operacion` según research R8; exportar `generar` en `app/simulacion/__init__.py`. Depende de T042 y de T036 (el test cruza con `diagnosticar`). **Terminada cuando**: `uv run pytest tests/unit/test_generador.py` pasa.
- [ ] T046 [US4] Implementar en `app/almacen/repositorio.py` `siguiente_id()` (lanza `IdsAgotados` si el siguiente sería `OP-9000`), `crear(construir)` y la excepción `IdsAgotados`, con un `threading.Lock` que cubre la reserva del ID y la inserción (research R9). Depende de T043. **Terminada cuando**: `uv run pytest tests/unit/test_repositorio.py` pasa completo.
- [ ] T047 [US4] Agregar en `app/api/esquemas.py` `PedidoGeneracion` (`caso: Caso`). Depende de T040 (la respuesta usa `OperacionDetalle`). **Terminada cuando**: `uv run python -c "from app.api.esquemas import PedidoGeneracion"` no da error.
- [ ] T048 [US4] Agregar en `app/api/rutas.py` `POST /operaciones` (status 201, `response_model=OperacionDetalle`): toma `ahora = reloj()`, llama `repositorio.crear(lambda id: generar(pedido.caso, id, ahora))` y convierte `IdsAgotados` en `ErrorPayTrace(409, "No quedan IDs disponibles para generar operaciones")`. Depende de T045, T046 y T047. **Terminada cuando**: `uv run pytest tests/api/test_h4_generacion.py` pasa.

**Checkpoint**: flujo de demo completo: generar, buscar, ver trace y diagnosticar.

---

## Fase 7: Historia 5 — Ver la lista de operaciones con su estado (P2)

**Objetivo**: `GET /operaciones` lista todas las operaciones (fijas y generadas) con su estado,
por ID ascendente.

**Prueba independiente**: generar operaciones de tres casos distintos y abrir la lista.

### Tests de la Historia 5 (primero; deben verse fallar) ⚠️

- [ ] T049 [P] [US5] Agregar en `tests/unit/test_repositorio.py` los tests de `listar()`: devuelve todas las operaciones ordenadas por ID ascendente aunque se hayan agregado desordenadas, incluidas las agregadas después del arranque. Depende de T043 (mismo archivo). **Terminada cuando**: los tests nuevos se ven fallar.
- [ ] T050 [P] [US5] Escribir `tests/api/test_h5_lista.py`: con solo los datos fijos, `GET /operaciones` → 30 elementos `OP-0001` a `OP-0030` en orden, cada uno con claves exactamente `{id, estado}`; `test_h5_e1`: tras generar `ok`, `fondos_insuficientes` y `trace_incompleto`, la lista tiene 33 elementos y los 3 nuevos con estados `ok`, `fallida` y `pendiente`. **Terminada cuando**: se ve fallar (405 en `GET /operaciones`).

### Implementación de la Historia 5

- [ ] T051 [US5] Implementar `listar()` en `app/almacen/repositorio.py`. Depende de T049. **Terminada cuando**: `uv run pytest tests/unit/test_repositorio.py` pasa completo.
- [ ] T052 [US5] Agregar en `app/api/esquemas.py` `OperacionResumen` (`id`, `estado`). **Terminada cuando**: `uv run python -c "from app.api.esquemas import OperacionResumen"` no da error.
- [ ] T053 [US5] Agregar en `app/api/rutas.py` `GET /operaciones` con `response_model=list[OperacionResumen]`. Depende de T051 y T052. **Terminada cuando**: `uv run pytest tests/api/test_h5_lista.py` pasa.

**Checkpoint**: las 5 historias funcionan.

---

## Fase 8: Pulido y verificaciones transversales

- [ ] T054 [P] Escribir `tests/api/test_tiempos.py` (SC-005, SC-006; excepción al rojo→verde, ver Tests): 5 pedidos de diagnóstico y 5 de `GET /operaciones/{id}` por cada una de las 25 operaciones del conjunto de evaluación (125 de cada tipo), medidos con `time.perf_counter`; al menos el 95 % de cada grupo en ≤ 2 s. **Terminada cuando**: `uv run pytest tests/api/test_tiempos.py` pasa.
- [ ] T055 [P] Escribir `tests/unit/test_sin_conexiones_externas.py` (principios II y IV, FR-028; excepción al rojo→verde, ver Tests): recorre el AST de todos los `.py` de `app/` y falla si hay imports de `httpx`, `requests`, `urllib.request`, `urllib3`, `http.client`, `socket`, `aiohttp`, `random`, `secrets`, `openai` o `anthropic`. **Terminada cuando**: `uv run pytest tests/unit/test_sin_conexiones_externas.py` pasa.
- [ ] T056 Correr la suite completa con `uv run pytest` y, para cada archivo de test, compararlo con `git diff <commit en rojo> HEAD -- <archivo>` contra el commit de la tarea de test que lo dejó fallando (ver Convenciones). Si un archivo recibió tests en varias tareas (p. ej. `test_reglas.py`: T025 y T033), cada parte se compara contra su propio commit en rojo. Todo cambio posterior tiene que estar justificado contra el spec, nunca hecho para que el test pase (principio III). T054 y T055 no tienen commit en rojo (ver Tests). **Terminada cuando**: toda la suite está en verde, cada archivo de test se comparó contra su commit en rojo y no hay tests editados para que pasen.
- [ ] T057 Recorrer a mano los pasos 1 a 14 de `specs/001-diagnostico-transferencias/quickstart.md` con `uv run uvicorn app.main:app` y `curl`. **Terminada cuando**: los 14 pasos dan lo esperado (SC-001 queda para la medición con una persona, fuera de esta lista).

---

## Dependencias y orden de ejecución

### Entre fases

- **Setup (Fase 1)**: sin dependencias.
- **Fundacional (Fase 2)**: depende de Setup; **bloquea** todas las historias.
- **US1 (Fase 3)**: depende de la Fase 2.
- **US2 (Fase 4)**: depende de US1 (completa `app/diagnostico/reglas.py` y el endpoint de diagnóstico que crea US1).
- **US3 (Fase 5)**: depende solo de la Fase 2; puede hacerse en paralelo con US1/US2 (choca solo en `esquemas.py` y `rutas.py`: coordinar o hacerla después).
- **US4 (Fase 6)**: depende de la Fase 2, de US3 (`OperacionDetalle`, T040) y de US2 (T036 para el cruce generador ↔ reglas y el endpoint de diagnóstico para los tests de punta a punta).
- **US5 (Fase 7)**: depende de la Fase 2; su test de API usa `POST /operaciones`, así que va después de US4.
- **Pulido (Fase 8)**: después de todas las historias.

### Dentro de cada historia

- Tests → se ven fallar → modelos/funciones puras → esquemas → rutas.
- Archivos compartidos entre tareas (se tocan en orden, nunca en paralelo): `tests/unit/test_reglas.py` (T025 → T033), `tests/unit/test_repositorio.py` (T007 → T043 → T049), `tests/unit/test_carga_datos.py` (T009 → T010), `tests/api/test_conjunto_evaluacion.py` (T027 → T035), `app/datos/conjunto_evaluacion.json` (T014 → T015 → T016), `app/almacen/carga.py` (T011 → T012), `app/almacen/repositorio.py` (T008 → T046 → T051), `app/diagnostico/reglas.py` (T030 → T036), `app/api/esquemas.py` (T031 → T037 → T040 → T047 → T052), `app/api/rutas.py` (T023 → T032 → T038 → T041 → T048 → T053).

## Oportunidades de paralelismo

- Fase 1: T003 y T004.
- Fase 2: T005, T007, T009, T019 y T021 (tests de piezas distintas); T013 después de T012; luego T017 y T018 junto con la serie T014–T016.
- US1: T024, T025, T026 y T027 (cuatro archivos de test); después T028 y T029.
- US2: T034 y T035 junto con T033.
- US3: T039 puede escribirse mientras se hace US1/US2.
- US4: T042, T043 y T044.
- US5: T049 y T050.
- Pulido: T054 y T055.

### Ejemplo: Historia 1

```text
# Tests (en paralelo, todos deben verse fallar):
Tarea: "T024 Aislamiento de reglas en tests/unit/test_reglas_aislamiento.py"
Tarea: "T025 Causas nombradas en tests/unit/test_reglas.py"
Tarea: "T026 Escenarios H1 en tests/api/test_h1_diagnostico_con_evidencia.py"
Tarea: "T027 SC-002/SC-004 en tests/api/test_conjunto_evaluacion.py"

# Piezas sin dependencias entre sí:
Tarea: "T028 Textos literales en app/diagnostico/textos.py"
Tarea: "T029 Resultados en app/diagnostico/resultados.py"
```

### Ejemplo: Historia 4

```text
Tarea: "T042 Tests del generador en tests/unit/test_generador.py"
Tarea: "T043 Tests de IDs en tests/unit/test_repositorio.py"
Tarea: "T044 Escenarios H4 en tests/api/test_h4_generacion.py"
```

---

## Estrategia de implementación

### MVP (Historias 1 y 2)

1. Fase 1 (Setup) y Fase 2 (Fundacional).
2. Fase 3 (US1): diagnóstico con evidencia de las 20 fallidas con trace completo.
3. Fase 4 (US2): "no concluyente", "en curso" y "sin fallo"; el módulo de reglas queda completo.
4. **Parar y validar**: `uv run pytest` en verde y `curl localhost:8000/operaciones/OP-0001/diagnostico`.

US1 sola no es un MVP: deja el principio I a medias (las pendientes, las OK y los casos borde dan
`NotImplementedError`).

### Entrega incremental

1. Setup + Fundacional → la app arranca con los 30 datos fijos.
2. US1 → causas con evidencia.
3. US2 → "evidencia o nada" completo.
4. US3 → búsqueda y trace (puede adelantarse; es independiente).
5. US4 → generación para la demo.
6. US5 → lista.
7. Pulido → tiempos, guardas de conexiones externas, quickstart.

## Notas

- Commits: ver Convenciones (un commit por tarea sin OK individual; revisión con `git log` y
  `uv run pytest` al final de cada fase).
- Revisión de cada cambio (constitución): rechazar causas sin evento citado, lectura del reloj
  dentro de `app/diagnostico/`, azar o LLM en el diagnóstico, tests editados para que pasen, y
  conexiones o datos reales.
