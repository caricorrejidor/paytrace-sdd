# Data Model: PayTrace — evidencia de la recomendación

**Plan**: [plan.md](./plan.md) | **Base**: [001/data-model.md](../001-diagnostico-transferencias/data-model.md)

Solo se documenta lo que cambia. Enumeraciones, `Evento`, `Operacion`, hora de referencia, repositorio,
reglas de validación de la carga y transiciones de estado siguen como en 001. No hay datos fijos
nuevos (FR-013).

## Resultado del diagnóstico (`app/diagnostico/resultados.py`) — modificado

| Variante | Campos | Cambio |
|---|---|---|
| `Diagnostico` | `causa: str`, `eventos_citados: tuple[str, ...]`, `recomendacion: str`, **`evidencia_recomendacion: tuple[str, ...]`** | campo nuevo, obligatorio, sin valor por defecto ([research R3](./research.md#r3-dónde-vive-el-campo)) |
| `SinFallo` | `mensaje` | sin cambios: no tiene ninguno de los cuatro campos (FR-007) |
| `EnCurso` | `mensaje` | sin cambios: no tiene ninguno de los cuatro campos (FR-007) |

### Valores posibles de `Diagnostico`

Las columnas `causa`, `eventos_citados` y `recomendacion` son exactamente las de 001 (FR-009, FR-010).
"Reversas posteriores" = IDs de los eventos `reversa_debito` que están después del evento clave en el
trace, en el orden del trace ([research R4](./research.md#r4-regla-de-la-evidencia)).

| Eventos clave en el trace | `causa` | `eventos_citados` | `recomendacion` | `evidencia_recomendacion` |
|---|---|---|---|---|
| 1, AM04 | fondos insuficientes | [ese evento] | Avisar al cliente… | `()` |
| 1, AC01 | cuenta incorrecta | [ese evento] | Pedir al cliente que verifique el CBU/CVU… | reversas posteriores (`()` si no hay) |
| 1, AB05, con `reversa_debito` posterior | timeout | [ese evento] | El débito ya se devolvió… | reversas posteriores (≥ 1) |
| 1, AB05, sin `reversa_debito` posterior | timeout | [ese evento] | El débito todavía no se devolvió… | `()` |
| 0 | no concluyente | [] | Pedir los logs del proveedor… | `()`, aunque haya reversas |
| > 1 | no concluyente | [todos los clave] | Evidencia contradictoria… | `()`, aunque haya reversas |

## Reglas que cumple `evidencia_recomendacion`

- Solo contiene IDs de eventos del trace que recibió `diagnosticar()`; nunca de otra operación (FR-002).
- Solo contiene IDs de eventos `reversa_debito`, y nunca uno anterior al evento clave (FR-008).
- No comparte IDs con `eventos_citados`: la reversa no es evento clave (FR-009).
- Si tiene más de un ID, van del más antiguo al más nuevo (FR-002).
- Se decide solo con estado, trace y hora de referencia, sin el caso; la misma entrada da la misma
  tupla (FR-011).
- En timeout, `evidencia_recomendacion` no vacía ⇔ recomendación "El débito ya se devolvió…".

## Valores esperados en los datos fijos

| Operaciones | `evidencia_recomendacion` |
|---|---|
| OP-0006 a OP-0010 (cuenta incorrecta) | `["OP-0006-E4"]` … `["OP-0010-E4"]` (la reversa, 4.º evento) |
| OP-0011 a OP-0015 (timeout con reversa) | `["OP-0011-E5"]` … `["OP-0015-E5"]` (la reversa, 5.º evento) |
| OP-0001 a OP-0005, OP-0016 a OP-0025 | `[]` |
| OP-0028 a OP-0030 (casos borde) | `[]` (OP-0028 y OP-0029 tienen reversa, pero son "no concluyente") |
| OP-0026, OP-0027 (en curso) y una OK | la respuesta no tiene la clave |
