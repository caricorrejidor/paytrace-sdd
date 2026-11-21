# Research: PayTrace — diagnóstico de transferencias fallidas o pendientes

**Fase**: 0 (investigación) | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

El Technical Context no quedó con ningún "NEEDS CLARIFICATION": el stack lo fijan AGENTS.md y el
pedido del plan, y el comportamiento lo fija el spec (con sus clarificaciones del 2026-11-18). Esta
fase registra las decisiones de diseño que el spec deja abiertas a la implementación, con su
justificación y las alternativas descartadas.

---

## R1. Versiones del stack

- **Decisión**: Python 3.12 (`requires-python = ">=3.12,<3.13"` y `.python-version` = `3.12`),
  gestionado con uv. Dependencias de ejecución: `fastapi` y `uvicorn`. Dependencias de desarrollo
  (grupo `dev`): `pytest` y `httpx` (lo necesita `fastapi.testclient.TestClient`). Versiones
  estables en PyPI al 2026-11-18: fastapi 0.165.0, uvicorn 0.54.0, pydantic 2.14.4 (llega con
  FastAPI; es la versión que resolvió uv), pytest 9.2.0, httpx 0.28.1. Se agregan con `uv add` y
  quedan fijadas en `uv.lock`.
- **Nota**: con Starlette 1.10, `TestClient` avisa que `httpx` está deprecado
  (`StarletteDeprecationWarning`, recomienda `httpx2`). Se deja así a propósito: funciona y
  cambiarlo es un cambio de stack.
- **Justificación**: es el stack de AGENTS.md. La máquina tiene Python 3.14 en el sistema; uv
  descarga y usa 3.12 por el `.python-version`, así que no hace falta instalar nada a mano.
- **Alternativas descartadas**: `fastapi[standard]` (trae CLI, plantillas y extras que una API en
  memoria no usa); pip + venv (AGENTS.md exige uv).

## R2. Aislamiento del módulo de reglas

- **Decisión**: las reglas viven en `app/diagnostico/`, un módulo puro que solo importa la
  biblioteca estándar y los tipos de dominio de `app/dominio.py` (también stdlib pura). La función
  pública es `diagnosticar(estado, eventos, hora_referencia) -> Resultado`. No recibe la operación
  entera ni el caso: recibe exactamente lo que FR-016 permite usar.
- **Justificación**: FR-016, FR-026 y la constitución (principio II) exigen que las reglas decidan
  solo con trace, estado y hora de referencia, sin leer el reloj. Con esta firma el caso ni siquiera
  está disponible dentro de las reglas, y la hora entra siempre como argumento.
- **Cómo se verifica**: un test de aislamiento (`tests/unit/test_reglas_aislamiento.py`) recorre el
  AST de los archivos de `app/diagnostico/` y falla si encuentra imports de `fastapi`, `pydantic`,
  `random`, `time`, `app.api`, `app.almacen`, `app.simulacion`, llamadas a `now`, `utcnow` o
  `today`, o cualquier referencia a `Caso`/`caso`.
- **Alternativas descartadas**: modelos Pydantic dentro de las reglas (acopla el núcleo a la capa
  de validación de la API); pasar la operación completa (expone el caso a las reglas y viola
  FR-016 en potencia).

## R3. Orden de evaluación de las reglas

- **Decisión**: las reglas se evalúan en este orden, y la primera que aplica decide:
  1. Estado **OK** → "La operación no tiene un fallo para investigar" (FR-023).
  2. Estado **pendiente** y `hora_referencia − momento del último evento ≤ 10 min` → "La operación
     sigue en curso" (FR-024, FR-025).
  3. Se buscan los eventos clave del trace (FR-016): `rechazo_origen`+AM04,
     `rechazo_banco_destino`+AC01, `rechazo_timeout`+AB05.
     - **Más de uno** → "no concluyente", cita todos los eventos clave en el orden del trace,
       recomendación "Evidencia contradictoria: revisar manualmente los eventos citados" (FR-022).
     - **Ninguno** → "no concluyente", sin eventos citados, recomendación "Pedir los logs del
       proveedor desde el último evento conocido" (FR-021).
     - **Exactamente uno** → causa según el código (AM04 → "fondos insuficientes", AC01 → "cuenta
       incorrecta", AB05 → "timeout"), cita ese evento y da la recomendación de la tabla (FR-018 a
       FR-020). Para AB05 la recomendación depende de si hay un `reversa_debito` **después** del
       rechazo en el trace.
- **Justificación**: es la lectura directa del spec: el plazo aplica solo a pendientes y, en una
  pendiente, "no concluyente" recién cuando venció (FR-021, FR-024). Las reglas se aplican igual
  para cualquier estado distinto de OK; el spec asume que el estado siempre coincide con el trace,
  así que una pendiente vencida con un evento clave no se da con datos simulados.
- **Alternativas descartadas**: decidir por estado primero y "fallida" exigida para nombrar causa
  (agrega una rama para un caso que el spec declara inexistente, sin requisito que la respalde).

## R4. Comparación del plazo de espera

- **Decisión**: vencido si `hora_referencia − último_evento.momento > timedelta(minutes=10)`, con
  `datetime` con zona horaria (UTC). Exactamente 10 minutos no vence (FR-025). Si la hora de
  referencia es anterior al último evento, la diferencia es negativa y la operación sigue en curso.
- **Justificación**: comparación estricta tal como la pide FR-025; con datetimes con zona no hay
  ambigüedad de horario de verano ni de zona local.
- **Alternativas descartadas**: comparar minutos enteros (redondeo: 10 min 30 s contaría como 10);
  datetimes sin zona (la carga los rechaza; ver R7).

## R5. Hora de referencia por tipo de operación

- **Decisión**: cada operación de los datos fijos trae `hora_referencia` en su archivo. Para las
  generadas, la capa API toma la hora del reloj en el momento del pedido, mediante una dependencia
  inyectable (`obtener_reloj`), y se la pasa a `diagnosticar`. Los tests reemplazan esa dependencia
  con `app.dependency_overrides` para fijar la hora.
- **Justificación**: FR-026 y la clarificación del 2026-11-18. El reloj se lee fuera de las reglas
  (constitución, principio II) y se puede fijar en los tests.
- **Alternativas descartadas**: aceptar la hora de referencia como parámetro del endpoint (permitiría
  que el analista cambie el resultado de una operación fija, y FR-026 dice que la de las fijas es
  propia de los datos).

## R6. Formato de los datos fijos

- **Decisión**: tres archivos JSON en `app/datos/`: `conjunto_evaluacion.json` (25 operaciones,
  OP-0001 a OP-0025), `prueba_plazo.json` (2, OP-0026 y OP-0027) y `casos_borde.json` (3, OP-0028 a
  OP-0030). El formato está en [contracts/datos-fijos.md](./contracts/datos-fijos.md). Cada
  operación del conjunto de evaluación lleva el campo `caso` para que los tests sepan qué resultado
  esperar; ese campo no llega nunca a las reglas ni sale por la API.
- **Justificación**: JSON se lee con la biblioteca estándar; el spec pide que los datos fijos se
  carguen desde archivos con IDs y horarios estables (FR-007, FR-008, FR-029). Los IDs consecutivos
  dejan el primer ID generado en OP-0031.
- **Alternativas descartadas**: YAML (dependencia extra sin beneficio); datos en código Python (el
  pedido exige archivos); exponer `caso` en la API (le mostraría la respuesta al analista y no lo
  pide ningún requisito).

## R7. Validación de los datos al cargar

- **Decisión**: la carga (`app/almacen/carga.py`) valida con modelos Pydantic y convierte a los
  tipos de dominio. Si algún archivo no cumple las reglas de
  [data-model.md](./data-model.md#reglas-de-validación), la aplicación no arranca (falla en el
  `lifespan` con un mensaje que nombra el archivo y la operación).
- **Justificación**: los datos fijos son la base de la evaluación (SC-002 a SC-004 y SC-007); un
  dato roto tiene que detectarse al iniciar, no en medio de una demo.
- **Alternativas descartadas**: cargar sin validar y confiar en los tests (un archivo editado a mano
  pasaría desapercibido hasta el diagnóstico).

## R8. Generación de operaciones

- **Decisión**: `app/simulacion/generador.py` es una función pura `generar(caso, id_operacion,
  ahora) -> Operacion`. La API le pasa el reloj inyectado. Los eventos quedan separados por 1 segundo
  y con momentos truncados al segundo:
  - en los casos con resultado final, el último evento es `ahora`;
  - en "trace incompleto", el último evento (débito en origen) es `ahora − 11 min` y la orden
    enviada `ahora − 11 min − 1 s` (FR-004: más de 10 minutos antes de la generación).
  - Los IDs de evento son `{id_operacion}-E{n}` (n desde 1), únicos en todo el sistema.
- **Justificación**: dada la misma entrada siempre produce la misma operación, se testea sin reloj
  real y respeta FR-001, FR-004 y FR-031.
- **Alternativas descartadas**: IDs de evento con UUID (no deterministas, ilegibles al citarlos);
  margen exacto de 10 min para el trace incompleto (quedaría "en curso").

## R9. Asignación de IDs y concurrencia

- **Decisión**: el repositorio en memoria (`app/almacen/repositorio.py`) guarda las operaciones en
  un `dict` por ID. El siguiente ID es `máximo número existente + 1` (FR-003), calculado y reservado
  dentro de `crear(construir)` bajo un `threading.Lock`, porque FastAPI ejecuta los endpoints síncronos en un pool de hilos. Si el
  siguiente número fuera ≥ 9000, `siguiente_id()` lanza `IdsAgotados` y la generación responde 409 "No quedan IDs disponibles para generar
  operaciones" y no crea ninguna operación (FR-032).
- **Justificación**: FR-002/FR-003 prohíben `OP-9xxx` siempre y FR-032 define el rechazo y su
  mensaje literal. La reserva del ID y la inserción ocurren bajo el mismo lock, así que un rechazo no
  deja ninguna operación a medio crear. Se usa 409 porque el pedido es válido pero choca con el
  estado actual del repositorio.
- **Alternativas descartadas**: reutilizar huecos (contradice "número siguiente al mayor ID");
  base de datos o archivo (el spec pide que las generadas se pierdan al reiniciar, FR-009).

## R10. Diseño de la API

- **Decisión**: API REST JSON, sin front. Endpoints (detalle en
  [contracts/api.md](./contracts/api.md)):
  - `POST /operaciones` (generar), `GET /operaciones` (listar), `GET /busqueda?id=` (buscar),
    `GET /operaciones/{id}` (abrir, con trace), `GET /operaciones/{id}/diagnostico` (diagnosticar).
  - El formato de ID se valida con `re.fullmatch(r"OP-[0-9]{4}", texto)` (no `\d`, que en Python
    acepta dígitos Unicode, ni `$`, que acepta un `\n` final),
    sin recortar espacios: inválido → 400 con "Ingresá un ID con formato OP-0000"; válido e
    inexistente → 404 con "Operación no encontrada".
  - El diagnóstico es una unión discriminada por `tipo`: `diagnostico` (causa, eventos citados,
    recomendación), `sin_fallo` y `en_curso` (solo mensaje). En las dos últimas los campos de causa,
    eventos citados y recomendación **no aparecen** en el JSON (FR-023, FR-024).
- **Justificación**: la búsqueda tiene su propio endpoint porque debe responder al texto vacío o
  ausente (FR-012), algo que una ruta con el ID en el path no puede recibir. El diagnóstico es `GET`
  porque no cambia nada y es idempotente; se calcula solo cuando se pide (FR-015).
- **Alternativas descartadas**: 422 de FastAPI para IDs inválidos (el mensaje tiene que ser el
  literal del spec); `POST` para el diagnóstico (no tiene efectos); campos `null` en vez de ausentes
  (el spec dice que no se muestran).

## R11. Estrategia de tests

- **Decisión**: pytest, sin behave ni pytest-bdd. Cada escenario de aceptación del spec es una
  función de test nombrada por historia y escenario (p. ej. `test_h2_e4_pendiente_exactamente_10_minutos_sigue_en_curso`)
  con un docstring que copia el Dado/Cuando/Entonces. Capas:
  - `tests/unit/`: reglas (tabla de casos, límites del plazo, contradicciones, determinismo),
    aislamiento de las reglas, generador, carga de datos, repositorio.
  - `tests/api/`: los escenarios de las historias 1 a 5 contra la app con `TestClient`, más las
    verificaciones de SC-002, SC-003, SC-004 y SC-007 sobre las 25 operaciones del conjunto de
    evaluación, y una verificación automática de tiempos (SC-005, SC-006: 125 pedidos de cada tipo,
    ≥ 95 % en ≤ 2 s).
  - Test-first (constitución, principio III): los tests de reglas se escriben y se ven fallar antes
    de implementar `app/diagnostico/`.
- **Justificación**: es lo que piden AGENTS.md y la constitución. SC-001 (mediana ≤ 5 min con una
  persona) no se automatiza: se mide a mano siguiendo [quickstart.md](./quickstart.md).
- **Alternativas descartadas**: pytest-bdd/behave (excluidos explícitamente); medir SC-005/SC-006
  solo a mano (el tiempo del servidor es automatizable; la parte humana queda en el quickstart).
