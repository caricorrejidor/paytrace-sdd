# Implementation Plan: PayTrace — diagnóstico de transferencias fallidas o pendientes

**Branch**: `001-diagnostico-transferencias` | **Date**: 2026-11-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-diagnostico-transferencias/spec.md`

## Summary

PayTrace es una API (sin front: el analista la usa desde la documentación interactiva `/docs`) que permite al analista generar transferencias simuladas por caso,
buscarlas y listarlas, ver su trace en orden y pedir un diagnóstico. El diagnóstico lo calcula un
módulo puro de reglas fijas (`app/diagnostico/`), aislado de la API, que recibe solo el estado, el
trace y la hora de referencia: nombra la causa citando exactamente un evento clave, o responde "no
concluyente", "La operación sigue en curso" o "La operación no tiene un fallo para investigar". Todo
vive en memoria; los datos fijos (conjunto de evaluación, prueba de plazo y casos borde) se cargan
al iniciar desde archivos JSON. Decisiones de diseño en [research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12, gestionado con uv

**Primary Dependencies**: FastAPI 0.165.0 (última estable; trae Pydantic 2.14.3), uvicorn 0.54.0

**Storage**: N/A. Operaciones en memoria (se pierden al reiniciar, FR-009); datos fijos en archivos
JSON de solo lectura en `app/datos/`

**Testing**: pytest 9.2.0 + httpx 0.28.1 (`TestClient`). Escenarios del spec como tests comunes,
sin behave ni pytest-bdd

**Target Platform**: servidor local (Linux/WSL2), `uv run uvicorn app.main:app`

**Project Type**: web service (solo API REST JSON)

**Performance Goals**: diagnóstico y trace en ≤ 2 s en el 95 % de 125 mediciones cada uno (SC-005,
SC-006); con ~30 operaciones en memoria el cálculo es de microsegundos

**Constraints**: reglas deterministas sin reloj, azar ni LLM (FR-026, FR-027); nunca `OP-9xxx`
(FR-002); generación rechazada con 409 al agotarse los IDs (FR-032); datos 100 % simulados, sin conexiones externas (FR-028)

**Scale/Scope**: demo para un analista: 30 operaciones fijas más las que genere; 5 endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Antes de Fase 0 | Después de Fase 1 |
|---|---|---|---|
| **I. Evidencia o nada** | La única rama que nombra causa es "exactamente un evento clave", y cita ese ID. 0 claves → "no concluyente" sin citas; > 1 → "no concluyente" citando los en conflicto. OK → `sin_fallo`, sin diagnóstico ([research R3](./research.md#r3-orden-de-evaluación-de-las-reglas), [contrato](./contracts/api.md)). | ✅ | ✅ |
| **II. Determinismo** | `diagnosticar(estado, eventos, hora_referencia)` es pura: sin reloj, sin azar, sin LLM. El reloj se lee en la capa API (dependencia inyectable) y entra como dato. Un test AST verifica el aislamiento ([research R2, R5](./research.md#r2-aislamiento-del-módulo-de-reglas)). | ✅ | ✅ |
| **III. Test-first** | Los tests de reglas (tabla de casos, límites del plazo, contradicciones, determinismo) se escriben y se ven fallar antes de implementar `app/diagnostico/`; `/speckit-tasks` debe ordenarlos primero ([research R11](./research.md#r11-estrategia-de-tests)). | ✅ | ✅ |
| **IV. Solo datos simulados** | Datos fijos sin nombres, cuentas ni documentos ([contrato de datos](./contracts/datos-fijos.md)); el generador es local; ningún cliente HTTP saliente en el código de la app. | ✅ | ✅ |

**Resultado**: sin violaciones. Complexity Tracking queda vacío.

## Project Structure

### Documentation (this feature)

```text
specs/001-diagnostico-transferencias/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones de diseño
├── data-model.md        # Fase 1: entidades, validaciones
├── quickstart.md        # Fase 1: guía de validación
├── contracts/
│   ├── api.md           # Fase 1: endpoints HTTP
│   └── datos-fijos.md   # Fase 1: formato y contenido de los JSON fijos
├── checklists/          # Checklists del spec (ya existentes)
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml               # uv; requires-python >=3.12,<3.13; pytest pythonpath = ["."]
.python-version              # 3.12
uv.lock

app/
├── __init__.py
├── main.py                  # crea la app FastAPI; lifespan carga los datos fijos
├── dominio.py               # enums y dataclasses: Estado, Emisor, CodigoMotivo, TipoEvento, Caso, Evento, Operacion (stdlib pura)
├── diagnostico/             # MÓDULO PURO de reglas: solo stdlib + app.dominio
│   ├── __init__.py          # expone diagnosticar()
│   ├── reglas.py            # diagnosticar(estado, eventos, hora_referencia) -> Resultado
│   ├── resultados.py        # Diagnostico | SinFallo | EnCurso
│   └── textos.py            # causas, recomendaciones y mensajes literales del spec
├── simulacion/
│   ├── __init__.py
│   └── generador.py         # generar(caso, id_operacion, ahora) -> Operacion (puro)
├── almacen/
│   ├── __init__.py
│   ├── carga.py             # lee y valida los JSON fijos (Pydantic) → Operacion
│   └── repositorio.py       # dict en memoria; crear(construir) bajo lock, siguiente_id(), IdsAgotados, listar()
├── api/
│   ├── __init__.py
│   ├── rutas.py             # los 5 endpoints de contracts/api.md
│   ├── esquemas.py          # modelos Pydantic de request/response
│   └── dependencias.py      # ErrorPayTrace, operacion_o_error(), obtener_repositorio(), obtener_reloj() (sobrescribibles en tests)
└── datos/
    ├── conjunto_evaluacion.json   # OP-0001..OP-0025
    ├── prueba_plazo.json          # OP-0026..OP-0027
    └── casos_borde.json           # OP-0028..OP-0030

tests/
├── unit/
│   ├── test_dominio.py              # enums, EMISOR_POR_TIPO, inmutabilidad, es_id_valido()
│   ├── test_datos_fijos.py          # los 30 JSON reales: IDs, secuencias por caso, horas de referencia
│   ├── test_dependencias.py         # operacion_o_error() (400/404), obtener_reloj()
│   ├── test_sin_conexiones_externas.py  # AST: sin clientes HTTP, sockets, azar ni LLM en app/
│   ├── test_reglas.py               # todas las ramas de diagnosticar(), límite 10 min, determinismo
│   ├── test_reglas_aislamiento.py   # AST: sin fastapi/pydantic/random/time/now()/caso en app/diagnostico
│   ├── test_generador.py            # los 6 casos: estado, eventos, último evento, momentos crecientes
│   ├── test_carga_datos.py          # archivos válidos, cantidades, IDs, rechazo de datos inválidos
│   └── test_repositorio.py          # siguiente ID, nunca OP-9xxx, listado ordenado
└── api/
    ├── conftest.py                  # TestClient con reloj fijo y repositorio fresco por test
    ├── test_arranque.py             # 30 datos fijos al iniciar; generadas se pierden al reiniciar (FR-009)
    ├── test_h1_diagnostico_con_evidencia.py
    ├── test_h2_sin_respaldo.py
    ├── test_h3_busqueda_y_trace.py
    ├── test_h4_generacion.py
    ├── test_h5_lista.py
    ├── test_conjunto_evaluacion.py  # SC-002, SC-003, SC-004, SC-007 sobre las 25
    └── test_tiempos.py              # SC-005, SC-006 (tiempo del servidor)
```

**Structure Decision**: proyecto único (solo backend), paquete `app/` en la raíz para que
`uv run uvicorn app.main:app` funcione tal como dice AGENTS.md. Las dependencias van en un solo
sentido: `api` → `almacen`, `simulacion`, `diagnostico` → `dominio`. `diagnostico` y `simulacion`
no conocen la API ni el reloj; `diagnostico` tampoco conoce el caso.

## Flujo de un diagnóstico

1. `GET /operaciones/{id}/diagnostico` valida el formato del ID (400) y lo busca (404).
2. La capa API elige la hora de referencia: la de la operación si es fija; si es generada,
   `obtener_reloj()()` en ese momento.
3. Llama `diagnosticar(op.estado, op.eventos, hora)`; no le pasa `op.caso`.
4. Convierte el `Resultado` al esquema de respuesta (unión discriminada por `tipo`).

## Riesgos y notas para tareas

- **Orden test-first**: en `tasks.md`, los tests de `tests/unit/test_reglas.py` y
  `test_reglas_aislamiento.py` van antes que `app/diagnostico/`; los tests de cada historia antes
  de su endpoint.
- **Datos fijos**: las 30 operaciones se escriben a mano según
  [contracts/datos-fijos.md](./contracts/datos-fijos.md). `test_carga_datos.py` prueba las reglas de
  validación de la carga (incluidas las cantidades) y `test_datos_fijos.py` verifica, sobre los
  archivos reales, la secuencia de cada caso. La carga no valida secuencias: un JSON con una secuencia
  rota arranca, y lo detecta `test_datos_fijos.py`.
- **Agotamiento de IDs**: el 409 de `POST /operaciones` implementa FR-032
  ([research R9](./research.md#r9-asignación-de-ids-y-concurrencia)). Lleva un test unitario del
  repositorio y un test de API que verifica el mensaje y que la cantidad de operaciones no cambia.
- **SC-001** se mide a mano (ver [quickstart.md](./quickstart.md)).

## Complexity Tracking

Sin violaciones de la constitución; no hay nada que justificar.
