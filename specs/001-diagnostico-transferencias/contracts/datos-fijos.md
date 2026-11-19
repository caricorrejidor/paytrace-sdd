# Contrato de los archivos de datos fijos

**Plan**: [../plan.md](../plan.md) | **Modelo**: [../data-model.md](../data-model.md)

Tres archivos JSON en `app/datos/`, leídos al iniciar la app (FR-030). Todos los datos son
ficticios (FR-028): no hay nombres, cuentas, CBU/CVU ni documentos; solo IDs, momentos, tipos,
emisores y códigos.

## Estructura común

```json
{
  "operaciones": [
    {
      "id": "OP-0006",
      "estado": "fallida",
      "caso": "cuenta_incorrecta",
      "hora_referencia": "2026-11-02T10:05:00Z",
      "eventos": [
        {"id": "OP-0006-E1", "momento": "2026-11-02T10:00:00Z", "tipo": "orden_enviada",         "emisor": "origen"},
        {"id": "OP-0006-E2", "momento": "2026-11-02T10:00:01Z", "tipo": "debito_origen",         "emisor": "origen"},
        {"id": "OP-0006-E3", "momento": "2026-11-02T10:00:02Z", "tipo": "rechazo_banco_destino", "emisor": "banco_destino", "codigo": "AC01"},
        {"id": "OP-0006-E4", "momento": "2026-11-02T10:00:03Z", "tipo": "reversa_debito",        "emisor": "origen"}
      ]
    }
  ]
}
```

- Momentos y horas de referencia en ISO 8601 con zona (`Z`).
- `caso` es opcional en el formato; lo llevan las operaciones del conjunto de evaluación (los tests
  lo usan para saber el resultado esperado). Nunca llega a las reglas ni a la API.
- Las reglas de validación están en [data-model.md](../data-model.md#reglas-de-validación).

## Contenido de cada archivo

### `conjunto_evaluacion.json` (FR-007)

| IDs | Caso | Estado | Hora de referencia |
|---|---|---|---|
| OP-0001 a OP-0005 | fondos_insuficientes | fallida | posterior al último evento |
| OP-0006 a OP-0010 | cuenta_incorrecta | fallida | posterior al último evento |
| OP-0011 a OP-0015 | timeout_con_reversa | fallida | posterior al último evento |
| OP-0016 a OP-0020 | timeout_sin_reversa | fallida | posterior al último evento |
| OP-0021 a OP-0025 | trace_incompleto | pendiente | más de 10 min después del último evento (p. ej. 15 min) |

Cada trace sigue la secuencia de su caso en la tabla del spec. Los horarios varían entre
operaciones (distintos días u horas) para que no sean copias idénticas.

### `prueba_plazo.json` (FR-008)

| ID | Estado | Trace | Último evento vs. hora de referencia |
|---|---|---|---|
| OP-0026 | pendiente | orden enviada → débito en origen | 2 minutos antes |
| OP-0027 | pendiente | orden enviada → débito en origen | exactamente 10 minutos antes |

### `casos_borde.json` (FR-029)

| ID | Estado | Trace | Resultado esperado |
|---|---|---|---|
| OP-0028 | fallida | orden enviada → débito en origen → reversa del débito | no concluyente, sin eventos citados |
| OP-0029 | fallida | orden enviada → débito en origen → rechazo banco destino AC01 → rechazo timeout AB05 → reversa del débito | no concluyente, cita E3 y E4 |
| OP-0030 | fallida | orden enviada → débito en origen → envío al proveedor → rechazo timeout AB05 → rechazo timeout AB05 | no concluyente, cita E4 y E5 |
