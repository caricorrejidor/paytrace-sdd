# Contrato de la API HTTP

**Plan**: [../plan.md](../plan.md) | **Modelo**: [../data-model.md](../data-model.md)

API JSON en `http://localhost:8000`, sin autenticación (spec, Assumptions). FastAPI publica el
OpenAPI generado en `/openapi.json` y `/docs`; este documento es la referencia que esos esquemas
deben cumplir. Los textos entre comillas son literales del spec.

## Errores comunes de ID

Aplican a todo endpoint que recibe un ID de operación.

| Situación | Status | Cuerpo |
|---|---|---|
| ID vacío, ausente o que no cumple `^OP-[0-9]{4}$` (`op1`, `op-0001`, ` OP-0001`) | 400 | `{"detalle": "Ingresá un ID con formato OP-0000"}` |
| ID con formato válido que no existe (`OP-9999`) | 404 | `{"detalle": "Operación no encontrada"}` |

Un 400 nunca incluye una operación ni "Operación no encontrada" (FR-012).

## Esquemas

**EventoSalida**

```json
{"id": "OP-0006-E3", "momento": "2026-11-02T10:00:02Z", "tipo": "rechazo_banco_destino",
 "emisor": "banco_destino", "codigo": "AC01"}
```

`codigo` aparece solo en los rechazos.

**OperacionResumen**: `{"id": "OP-0001", "estado": "fallida"}`

**OperacionDetalle**: `{"id": "OP-0006", "estado": "fallida", "eventos": [EventoSalida, ...]}`,
con `eventos` del más antiguo al más nuevo (FR-014). No expone el caso ni la hora de referencia.

## Endpoints

### `POST /operaciones` — generar una operación (Historia 4, FR-001 a FR-004, FR-032)

Request: `{"caso": "timeout_sin_reversa"}`. `caso` ∈ `ok`, `fondos_insuficientes`,
`cuenta_incorrecta`, `timeout_con_reversa`, `timeout_sin_reversa`, `trace_incompleto`.

| Resultado | Status | Cuerpo |
|---|---|---|
| Creada | 201 | `OperacionDetalle` con el siguiente ID libre (con los datos fijos solos, `OP-0031`) |
| Caso desconocido o falta | 422 | error de validación de FastAPI |
| Se agotaron los IDs (el siguiente sería `OP-9000`) | 409 | `{"detalle": "No quedan IDs disponibles para generar operaciones"}`; no se crea ninguna operación (FR-032) |

### `GET /operaciones` — listar (Historia 5, FR-013)

200 → `[OperacionResumen, ...]`, todas las operaciones (fijas y generadas), por ID ascendente.

### `GET /busqueda?id={texto}` — buscar (Historia 3, FR-010 a FR-012)

200 → `OperacionDetalle`. `id` ausente o vacío → 400 (ver errores comunes). Inexistente → 404.

### `GET /operaciones/{id}` — abrir una operación con su trace (Historia 3, FR-014)

200 → `OperacionDetalle`. Errores comunes de ID.

### `GET /operaciones/{id}/diagnostico` — diagnosticar (Historias 1 y 2, FR-015 a FR-027)

Se calcula en cada pedido, nunca antes (FR-015). La hora de referencia es la de los datos (fijas)
o la del momento del pedido (generadas). Errores comunes de ID. 200 con una de estas tres formas,
discriminadas por `tipo`:

```json
{"tipo": "diagnostico", "causa": "cuenta incorrecta", "eventos_citados": ["OP-0006-E3"],
 "recomendacion": "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó"}
```

```json
{"tipo": "diagnostico", "causa": "no concluyente", "eventos_citados": [],
 "recomendacion": "Pedir los logs del proveedor desde el último evento conocido"}
```

```json
{"tipo": "diagnostico", "causa": "no concluyente", "eventos_citados": ["OP-0029-E3", "OP-0029-E4"],
 "recomendacion": "Evidencia contradictoria: revisar manualmente los eventos citados"}
```

```json
{"tipo": "sin_fallo", "mensaje": "La operación no tiene un fallo para investigar"}
```

```json
{"tipo": "en_curso", "mensaje": "La operación sigue en curso"}
```

Garantías del contrato:

- Si `causa` no es "no concluyente", `eventos_citados` tiene exactamente un ID, y es el de un
  evento clave del trace (FR-019, constitución I).
- `sin_fallo` y `en_curso` no incluyen las claves `causa`, `eventos_citados` ni `recomendacion`
  (FR-023, FR-024).
- Mismo pedido sobre una operación fija → mismo cuerpo, siempre (FR-027).
