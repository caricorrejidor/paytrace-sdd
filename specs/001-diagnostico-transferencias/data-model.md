# Modelo de datos: PayTrace — diagnóstico de transferencias

**Fase**: 1 (diseño) | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

Todo vive en memoria. Los tipos de dominio (`app/dominio.py`) son dataclasses congeladas y enums de
la biblioteca estándar, sin dependencias externas, para que el módulo de reglas los use sin
acoplarse a la API. Los momentos son `datetime` con zona horaria (UTC).

## Enumeraciones

| Enum | Valores | Fuente |
|---|---|---|
| `Estado` | `ok`, `fallida`, `pendiente` | FR-005 |
| `Emisor` | `origen`, `proveedor`, `banco_destino` | FR-006 |
| `CodigoMotivo` | `AM04`, `AC01`, `AB05` | FR-006 |
| `TipoEvento` | ver tabla siguiente | Tabla de casos |
| `Caso` | `ok`, `fondos_insuficientes`, `cuenta_incorrecta`, `timeout_con_reversa`, `timeout_sin_reversa`, `trace_incompleto` | FR-001 |

### TipoEvento

| Valor | Texto en la tabla de casos | Emisor | ¿Rechazo (lleva código)? |
|---|---|---|---|
| `orden_enviada` | Orden enviada | origen | no |
| `debito_origen` | débito en origen | origen | no |
| `envio_proveedor` | envío al proveedor | origen | no |
| `aceptacion_proveedor` | aceptación del proveedor | proveedor | no |
| `acreditacion_destino` | acreditación en destino | banco_destino | no |
| `rechazo_origen` | rechazo en origen | origen | sí |
| `rechazo_banco_destino` | rechazo del banco destino | banco_destino | sí |
| `rechazo_timeout` | rechazo por timeout (lo informa el proveedor) | proveedor | sí |
| `reversa_debito` | reversa del débito | origen | no |

## Entidades

### Evento

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | `str` | Único en todo el sistema. Generadas: `{id_operacion}-E{n}`, n desde 1. |
| `momento` | `datetime` (UTC) | Estrictamente posterior al del evento anterior del trace (FR-031). |
| `tipo` | `TipoEvento` | — |
| `emisor` | `Emisor` | Debe coincidir con el de su `tipo` (tabla de arriba). |
| `codigo` | `CodigoMotivo \| None` | Obligatorio si el tipo es un rechazo; ausente si no (FR-006). |

**Evento clave** (no es una entidad aparte; es un predicado de las reglas, FR-016): un evento es
clave solo si es `rechazo_origen` + `AM04`, `rechazo_banco_destino` + `AC01` o `rechazo_timeout` +
`AB05`. Cualquier otra combinación de rechazo y código no es clave.

### Operación

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | `str` | Coincidencia completa (`re.fullmatch`) de `OP-[0-9]{4}`, único, nunca `OP-9xxx` (FR-002). |
| `estado` | `Estado` | Coincide con el trace (supuesto del spec). |
| `eventos` | `tuple[Evento, ...]` | El trace: al menos un evento, en orden cronológico estricto (FR-014, FR-031). |
| `caso` | `Caso \| None` | Caso de origen. Lo tienen las generadas y las del conjunto de evaluación. **No se pasa a las reglas ni se expone en la API.** |
| `hora_referencia` | `datetime \| None` | Obligatoria en los datos fijos (FR-026); `None` en las generadas (se usa la hora del pedido). |
| `origen` | `"fija" \| "generada"` | Interno; decide de dónde sale la hora de referencia. |

### Resultado del diagnóstico (`app/diagnostico/resultados.py`)

Unión de tres variantes; solo la primera tiene causa, eventos citados y recomendación (FR-017,
FR-023, FR-024).

| Variante | Campos | Cuándo |
|---|---|---|
| `Diagnostico` | `causa: str`, `eventos_citados: tuple[str, ...]`, `recomendacion: str` | Estado fallida, o pendiente con el plazo vencido. |
| `SinFallo` | `mensaje = "La operación no tiene un fallo para investigar"` | Estado OK. |
| `EnCurso` | `mensaje = "La operación sigue en curso"` | Pendiente con ≤ 10 min desde el último evento. |

Valores posibles de `Diagnostico` (textos literales en `app/diagnostico/textos.py`):

| Eventos clave en el trace | `causa` | `eventos_citados` | `recomendacion` |
|---|---|---|---|
| 1, AM04 | fondos insuficientes | [ese evento] | Avisar al cliente que no tenía saldo. No se debitó nada |
| 1, AC01 | cuenta incorrecta | [ese evento] | Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó |
| 1, AB05, con `reversa_debito` posterior | timeout | [ese evento] | El débito ya se devolvió: se puede reintentar la transferencia |
| 1, AB05, sin `reversa_debito` posterior | timeout | [ese evento] | El débito todavía no se devolvió: pedir la reversa antes de reintentar. Si se reintenta antes, se cobra dos veces |
| 0 | no concluyente | [] | Pedir los logs del proveedor desde el último evento conocido |
| > 1 | no concluyente | [todos los clave, en orden del trace] | Evidencia contradictoria: revisar manualmente los eventos citados |

### Hora de referencia

No es una entidad: es el tercer argumento de `diagnosticar(estado, eventos, hora_referencia)`.
Sale de `Operacion.hora_referencia` en las fijas y del reloj inyectado por la API en las generadas
(FR-026, [research.md R5](./research.md#r5-hora-de-referencia-por-tipo-de-operación)).

### Repositorio en memoria (`app/almacen/repositorio.py`)

- `dict[str, Operacion]`, cargado al iniciar con los tres archivos fijos (FR-030).
- `siguiente_id()`: devuelve `OP-{máximo+1:04d}`; si sería `OP-9000` (el mayor existente es
  `OP-8999`), lanza `IdsAgotados` (FR-003, FR-032).
- `crear(construir)`: bajo un `threading.Lock`, calcula `siguiente_id()`, llama `construir(id)` y
  agrega la operación, todo atómico. Si `siguiente_id()` lanza `IdsAgotados`, no llama `construir`
  y no crea nada ([research.md R9](./research.md#r9-asignación-de-ids-y-concurrencia)).
- `listar()`: todas, ordenadas por ID ascendente (FR-013).
- Sin persistencia: al reiniciar quedan solo los datos fijos (FR-009).

## Reglas de validación

La carga de los archivos fijos rechaza (y la app no arranca) si:

1. Un ID de operación no cumple, con coincidencia completa (`re.fullmatch`), `OP-[0-9]{4}`, o
   empieza con `OP-9`. No se usa `$`, que en Python acepta un `\n` final.
2. Hay IDs de operación o de evento repetidos, dentro de un archivo o entre archivos.
3. Una operación no tiene eventos, o sus momentos no son estrictamente crecientes.
4. Un momento o una hora de referencia no tiene zona horaria.
5. Un rechazo no tiene código, o un evento que no es rechazo tiene código.
6. El emisor no coincide con el del tipo de evento.
7. Falta `hora_referencia`.
8. Las cantidades no son las del spec: 25 en evaluación (5 por caso, sin OK), 2 en prueba de plazo,
   3 en casos borde (FR-007, FR-008, FR-029).

El generador produce operaciones que cumplen 1 a 6 por construcción; un test lo verifica para los
seis casos.

## Transiciones de estado

No hay. El estado de una operación queda fijo al cargarla o generarla; PayTrace solo diagnostica,
no corrige ni reintenta (spec, Assumptions). Lo único que depende del tiempo es el **resultado**
del diagnóstico de una pendiente: `EnCurso` mientras pasaron ≤ 10 min desde el último evento,
`Diagnostico` "no concluyente" cuando pasaron más.
