# Quickstart: validar PayTrace de punta a punta

**Plan**: [plan.md](./plan.md) | **Contrato**: [contracts/api.md](./contracts/api.md)

Guía para comprobar que la feature funciona. No contiene implementación: los cuerpos de las
respuestas y los textos esperados están en el [contrato de la API](./contracts/api.md) y en el
[modelo de datos](./data-model.md).

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado. Python 3.12 lo descarga uv si hace falta.
- `curl` (o el navegador en `http://localhost:8000/docs`).

## Instalar y correr

```bash
uv sync                                   # instala dependencias según uv.lock
uv run pytest                             # toda la suite: unit + escenarios del spec
uv run uvicorn app.main:app --reload      # API en http://localhost:8000
```

Resultado esperado de `uv run pytest`: todos los tests en verde, incluidos los de las historias 1 a
5 (`tests/api/test_h*.py`) y el de aislamiento de reglas (`tests/unit/test_reglas_aislamiento.py`).

## Recorrido manual (flujo de demo)

Con la API corriendo:

| # | Pedido | Esperado | Verifica |
|---|---|---|---|
| 1 | `curl -s localhost:8000/operaciones` | 30 operaciones (OP-0001 a OP-0030) con su estado | FR-030, FR-013 |
| 2 | `curl -s "localhost:8000/busqueda?id=OP-0001"` | 200, operación OP-0001 | H3-E1 |
| 3 | `curl -s "localhost:8000/busqueda?id=OP-9999"` | 404, "Operación no encontrada" | H3-E2 |
| 4 | `curl -s "localhost:8000/busqueda?id=op-0001"` y `?id=` | 400, "Ingresá un ID con formato OP-0000" | H3-E3 |
| 5 | `curl -s localhost:8000/operaciones/OP-0006` | 4 eventos, del más antiguo al más nuevo | H3-E4 |
| 6 | `curl -s localhost:8000/operaciones/OP-0001/diagnostico` | "fondos insuficientes", cita el evento AM04 | H1-E1 |
| 7 | Repetir el pedido 6 cinco veces | mismo cuerpo las 5 veces | FR-027, SC-007 |
| 8 | `curl -s localhost:8000/operaciones/OP-0021/diagnostico` | "no concluyente", sin eventos citados | H2-E1 |
| 9 | Diagnóstico de OP-0026 y OP-0027 | "La operación sigue en curso" en las dos | H2-E3, H2-E4 |
| 10 | Diagnóstico de OP-0028, OP-0029 y OP-0030 | "no concluyente": sin citas / cita 2 / cita 2 | H2-E5 a E7 |
| 11 | `curl -s -X POST localhost:8000/operaciones -H 'content-type: application/json' -d '{"caso":"ok"}'` | 201, `OP-0031`, estado `ok` | H4-E1, H4-E3 |
| 12 | Diagnóstico de `OP-0031` | "La operación no tiene un fallo para investigar" | H2-E2 |
| 13 | Generar `trace_incompleto` y diagnosticarla enseguida | último evento > 10 min antes; "no concluyente" | H4-E2, FR-021 |
| 14 | Reiniciar la API y listar | vuelven a ser 30; las generadas se perdieron | FR-009 |

## Medición humana (SC-001, SC-005, SC-006)

- **SC-001**: una persona que no generó los datos elige 10 operaciones del conjunto de evaluación y
  cronometra, para cada una, desde que busca el ID hasta que tiene el diagnóstico. Aprobado si la
  mediana es ≤ 5 minutos.
- **SC-005 / SC-006**: la suite incluye una verificación automática del tiempo del servidor (125
  pedidos de diagnóstico y 125 de trace, ≥ 95 % en ≤ 2 s). La medición de punta a punta con la
  persona que mira el resultado se hace en la demo con el mismo criterio.
