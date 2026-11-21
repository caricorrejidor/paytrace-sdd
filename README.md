# PayTrace

Herramienta para analistas de pagos que diagnostica por qué falló o quedó pendiente una transferencia:
aplica reglas fijas al trace, cita el evento que prueba la causa y recomienda el próximo paso.
Los datos son 100 % simulados: no hay bancos, proveedores ni datos personales reales.

## Cómo correrlo

Requiere Python 3.12 y [uv](https://docs.astral.sh/uv/).

| Paso | Comando |
|---|---|
| Instalar | `uv sync` |
| Tests | `uv run pytest` |
| Backend | `uv run uvicorn app.main:app` |

La interfaz es la documentación interactiva de FastAPI en <http://localhost:8000/docs>.

## Endpoints

Detalle completo en [contracts/api.md](specs/001-diagnostico-transferencias/contracts/api.md).

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/operaciones` | Genera una operación simulada a partir de un `caso` |
| `GET` | `/operaciones` | Lista todas las operaciones por ID ascendente |
| `GET` | `/busqueda?id={texto}` | Busca una operación por ID |
| `GET` | `/operaciones/{id}` | Abre una operación con su trace |
| `GET` | `/operaciones/{id}/diagnostico` | Diagnostica la operación: causa (o "no concluyente"), eventos citados y recomendación |

## Cómo se construyó

Con Spec-Driven Development usando Spec Kit: primero los principios, después la especificación,
el plan y las tareas, y recién entonces el código.

| Artefacto | Archivo |
|---|---|
| Constitución | [.specify/memory/constitution.md](.specify/memory/constitution.md) |
| Especificación | [spec.md](specs/001-diagnostico-transferencias/spec.md) |
| Plan | [plan.md](specs/001-diagnostico-transferencias/plan.md) |
| Tareas | [tasks.md](specs/001-diagnostico-transferencias/tasks.md) |

## Números

| | |
|---|---|
| Tareas | 57 |
| Tests | 292 |
| Commits | Uno por tarea |
| Test-first | Verificable en el historial: los tests entran en un commit `test` en rojo, antes de la implementación que los pone en verde (excepto T054 y T055, verificaciones transversales; ver tasks.md) |

Para ver los commits de tests: `git log --oneline --grep='^test'`.
