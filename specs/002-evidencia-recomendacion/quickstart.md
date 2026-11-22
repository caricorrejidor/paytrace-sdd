# Quickstart: validar la evidencia de la recomendación

**Plan**: [plan.md](./plan.md) | **Contrato**: [contracts/api.md](./contracts/api.md) |
**Base**: [001/quickstart.md](../001-diagnostico-transferencias/quickstart.md)

Guía para comprobar el cambio de punta a punta. Requisitos, instalación y el recorrido de 001 siguen
iguales; acá solo están los pasos que verifican el campo nuevo. Los cuerpos completos están en el
[contrato](./contracts/api.md) y los valores esperados por operación, en el
[modelo de datos](./data-model.md#valores-esperados-en-los-datos-fijos).

## Correr

```bash
uv sync
uv run pytest                             # toda la suite, 001 + 002
uv run uvicorn app.main:app --reload      # API en http://localhost:8000
```

Resultado esperado de `uv run pytest`: todo en verde, incluidos
`tests/api/test_evidencia_recomendacion.py`, los tests nuevos de `tests/unit/test_reglas.py` y, sin
cambios, `test_reglas_aislamiento.py`, `test_conjunto_evaluacion.py` y `test_tiempos.py`.

## Recorrido manual

Con la API corriendo (o desde `http://localhost:8000/docs`):

| # | Pedido | Esperado | Verifica |
|---|---|---|---|
| 1 | `curl -s localhost:8000/operaciones/OP-0006/diagnostico` | "cuenta incorrecta", `eventos_citados` `["OP-0006-E3"]`, `evidencia_recomendacion` `["OP-0006-E4"]` | H1-E1, H1-E3 |
| 2 | `curl -s localhost:8000/operaciones/OP-0006` | E4 es `reversa_debito` y es posterior a E3 | FR-002, FR-003 |
| 3 | `curl -s localhost:8000/operaciones/OP-0011/diagnostico` | "timeout", "El débito ya se devolvió…", evidencia `["OP-0011-E5"]` | H1-E2 |
| 4 | Diagnóstico de OP-0001 y OP-0016 | `evidencia_recomendacion: []` | H2, FR-005 |
| 5 | Diagnóstico de OP-0021, OP-0028, OP-0029 y OP-0030 | "no concluyente", `evidencia_recomendacion: []` (OP-0028 y OP-0029 tienen reversa) | H2, FR-006 |
| 6 | Diagnóstico de OP-0026 y OP-0027 | "La operación sigue en curso", sin la clave `evidencia_recomendacion` | H3, FR-007 |
| 7 | `curl -s -X POST localhost:8000/operaciones -H 'content-type: application/json' -d '{"caso":"ok"}'` y diagnosticar la nueva | "La operación no tiene un fallo para investigar", sin la clave | H3, FR-007 |
| 8 | Generar `cuenta_incorrecta` y diagnosticarla | evidencia = el ID de su reversa del débito | FR-011 (sin conocer el caso) |
| 9 | Repetir el pedido 1 cinco veces | mismo cuerpo las 5 veces | SC-005 |

Los escenarios 4 y 5 de la historia 1 ("cuenta incorrecta" sin reversa y con dos reversas) no se
pueden recorrer a mano: no hay datos fijos así (FR-013). Los cubren los tests de reglas.

## Mediciones

- **SC-004**: `tests/api/test_conjunto_evaluacion.py`, sin cambios, sigue en verde.
- **SC-006**: `tests/api/test_tiempos.py`, sin cambios, sigue en verde.
