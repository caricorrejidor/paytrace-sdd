# Contrato de la API: cambios de la feature 002

**Plan**: [plan.md](./plan.md) | **Base**: [001/contracts/api.md](../../001-diagnostico-transferencias/contracts/api.md)

Solo cambia `GET /operaciones/{id}/diagnostico`. Los demás endpoints, los errores de ID (400, 404),
la hora de referencia y los textos siguen como en el contrato de 001. Los datos fijos no cambian
([001/contracts/datos-fijos.md](../../001-diagnostico-transferencias/contracts/datos-fijos.md)).

## `GET /operaciones/{id}/diagnostico` — modificado (FR-001 a FR-012)

Las respuestas con `"tipo": "diagnostico"` suman la clave `evidencia_recomendacion`: una lista de IDs
de eventos del trace, posiblemente vacía, que **siempre está presente**. Las respuestas `sin_fallo` y
`en_curso` no cambian y **no tienen** la clave.

Cuenta incorrecta (OP-0006): la reversa del débito posterior al rechazo AC01.

```json
{"tipo": "diagnostico", "causa": "cuenta incorrecta", "eventos_citados": ["OP-0006-E3"],
 "recomendacion": "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó",
 "evidencia_recomendacion": ["OP-0006-E4"]}
```

Timeout con reversa (OP-0011):

```json
{"tipo": "diagnostico", "causa": "timeout", "eventos_citados": ["OP-0011-E4"],
 "recomendacion": "El débito ya se devolvió: se puede reintentar la transferencia",
 "evidencia_recomendacion": ["OP-0011-E5"]}
```

Fondos insuficientes, timeout sin reversa y "no concluyente": la clave está y va vacía.

```json
{"tipo": "diagnostico", "causa": "no concluyente", "eventos_citados": ["OP-0029-E3", "OP-0029-E4"],
 "recomendacion": "Evidencia contradictoria: revisar manualmente los eventos citados",
 "evidencia_recomendacion": []}
```

Sin diagnóstico: sin cambios.

```json
{"tipo": "sin_fallo", "mensaje": "La operación no tiene un fallo para investigar"}
```

```json
{"tipo": "en_curso", "mensaje": "La operación sigue en curso"}
```

### Garantías del contrato (se suman a las de 001)

- Si `tipo` es `"diagnostico"`, el cuerpo tiene exactamente las claves `tipo`, `causa`,
  `eventos_citados`, `recomendacion` y `evidencia_recomendacion` (FR-001).
- `evidencia_recomendacion` solo tiene IDs de eventos `reversa_debito` del trace de esa operación,
  posteriores al evento clave, en el orden del trace (FR-002, FR-003, FR-004, FR-008).
- Ningún ID aparece a la vez en `eventos_citados` y en `evidencia_recomendacion` (FR-009).
- Si `causa` es `"no concluyente"` o `"fondos insuficientes"`, `evidencia_recomendacion` es `[]`
  (FR-005, FR-006).
- `sin_fallo` y `en_curso` no incluyen `evidencia_recomendacion` (FR-007).
- `causa`, `eventos_citados` y `recomendacion` son los mismos que en 001 para cualquier trace (FR-009,
  FR-010).
- Mismo pedido sobre una operación fija → mismo cuerpo, incluida la evidencia (FR-011).

### Esquema (`app/api/esquemas.py`)

`DiagnosticoSalida` suma `evidencia_recomendacion: list[str]` (obligatorio). La unión discriminada
`DiagnosticoRespuesta` y los esquemas `SinFalloSalida` y `EnCursoSalida` no cambian. El OpenAPI de
`/docs` refleja el campo sin cambios manuales.
