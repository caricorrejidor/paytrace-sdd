# Research: PayTrace — evidencia de la recomendación

**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

No quedan NEEDS CLARIFICATION: el stack, la estructura y los patrones son los de la feature 001
([001/research.md](../001-diagnostico-transferencias/research.md)). Esta investigación solo fija las
decisiones propias del campo nuevo. Las referencias "001/R-x" remiten a esa investigación.

## R1. Stack y dependencias

- **Decisión**: sin cambios. Python 3.12 + FastAPI + uv, en memoria, pytest + httpx (`TestClient`),
  solo API. No se agregan dependencias ni se actualizan versiones.
- **Razón**: el cambio es un campo más en una respuesta existente; nada del stack lo limita.
- **Alternativas**: ninguna evaluada; actualizar versiones mezclaría cambios ajenos a la feature.

## R2. Nombre del campo

- **Decisión**: `evidencia_recomendacion`, en el resultado de las reglas y en la respuesta de la API.
- **Razón**: sigue el estilo de `eventos_citados` (snake_case, sin artículos) y nombra lo que el spec
  llama "evidencia de la recomendación" (Assumptions del spec dejan el nombre para el plan).
- **Alternativas**: `evidencia_de_la_recomendacion` (más largo, sin ganar claridad);
  `eventos_recomendacion` (se confunde con `eventos_citados` y no dice que es evidencia).

## R3. Dónde vive el campo

- **Decisión**: cuarto campo del dataclass `Diagnostico` en `app/diagnostico/resultados.py`,
  `evidencia_recomendacion: tuple[str, ...]`, **obligatorio y sin valor por defecto**. `SinFallo` y
  `EnCurso` no cambian.
- **Razón**: el spec dice que es parte del diagnóstico (FR-001) y que se decide con las mismas reglas
  (FR-011). Sin valor por defecto, cada rama de `diagnosticar()` tiene que decir explícitamente qué
  evidencia devuelve: una rama que se olvide no compila en silencio con una evidencia vacía.
  `SinFallo` y `EnCurso` siguen sin campos de diagnóstico, así que FR-007 se cumple por construcción.
- **Alternativas**:
  - Valor por defecto `()`: menos cambios en los tests existentes, pero esconde ramas que se
    olvidan del campo (un "vacía" que nadie decidió) y deja de ser cierto que el diagnóstico tiene
    siempre cuatro campos decididos por las reglas.
  - Función o módulo aparte (`evidencia_de(...)`): el pedido es no crear módulos nuevos, y obligaría
    a recalcular el evento clave fuera de `diagnosticar()`, con el riesgo de que la recomendación y su
    evidencia se decidan con condiciones distintas.

## R4. Regla de la evidencia

- **Decisión**: en `app/diagnostico/reglas.py`, una función privada
  `_reversas_posteriores(clave, eventos) -> tuple[str, ...]` devuelve los IDs de los eventos
  `reversa_debito` que están **después de la posición del evento clave en el trace**, en el orden del
  trace. `_con_un_evento_clave()` la usa así:

  | Evento clave | `evidencia_recomendacion` | Cambio en la recomendación |
  |---|---|---|
  | AM04 | `()` (FR-005) | ninguno |
  | AC01 | `_reversas_posteriores(...)`; vacía si no hay (FR-003) | ninguno |
  | AB05 | `_reversas_posteriores(...)` (FR-004, FR-005) | la condición "con reversa" pasa a ser `bool(reversas)`: es la misma condición de 001 escrita con el mismo cálculo |

  Las dos ramas "no concluyente" (0 claves y > 1 claves) devuelven `()` aunque el trace tenga reversas
  (FR-006). Más de una reversa posterior no entra en el conteo de eventos clave, porque
  `reversa_debito` no es evento clave (001/FR-016), así que no es contradictoria (FR-012).
- **Razón**: "posterior" se decide por posición en el trace, igual que 001 decide hoy "timeout con
  reversa" (001/R3); el trace ya está ordenado del más antiguo al más nuevo (001/FR-014), así que el
  orden de la tupla es el que pide FR-002. Que la recomendación de timeout y su evidencia salgan del
  mismo cálculo garantiza que nunca se contradicen ("ya se devolvió" sin reversa citada, o al revés).
  La función sigue pura: solo mira `eventos` y no conoce el caso (FR-011, constitución II).
- **Alternativas**:
  - Comparar por `momento` en lugar de por posición: da lo mismo con traces bien formados, pero
    agregaría una segunda forma de decidir "posterior" distinta de la de 001.
  - Citar solo la primera reversa: contradice la clarificación ("todas").

## R5. Esquema de la respuesta

- **Decisión**: `DiagnosticoSalida` en `app/api/esquemas.py` suma
  `evidencia_recomendacion: list[str]`, obligatorio. Se serializa siempre que `tipo` es
  `"diagnostico"`, también como `[]`. `_a_salida()` en `app/api/rutas.py` copia el campo. `SinFalloSalida`
  y `EnCursoSalida` no cambian.
- **Razón**: "vacía" (`[]`) y "no aparece" (sin clave) son cosas distintas en el spec (Contexto). La
  unión discriminada por `tipo` de 001 (001/R10) ya garantiza que las respuestas sin diagnóstico no
  tienen la clave. El endpoint de diagnóstico no usa `response_model_exclude_none`, y una lista vacía
  no es `None`, así que `[]` nunca desaparece. La documentación `/docs` se actualiza sola.
- **Alternativas**: omitir la clave cuando está vacía (confundiría "vacía" con "no aparece");
  `None` en lugar de `[]` (el spec dice lista, posiblemente vacía, FR-002).

## R6. Tests existentes que cambian

- **Decisión**: FR-001 modifica 001/FR-017 (el diagnóstico pasa de tres a cuatro campos), así que
  algunos tests de 001 que comparan el diagnóstico completo quedan desactualizados respecto del spec.
  Se actualizan en una **tarea propia, antes de tocar `app/`**, que cita FR-001 y se ve fallar (rojo):
  - `tests/unit/test_reglas.py`: cada `Diagnostico(...)` esperado suma su cuarto valor (`()` o el ID
    de la reversa).
  - `tests/api/test_h1_diagnostico_con_evidencia.py`: `CLAVES_DIAGNOSTICO` suma
    `"evidencia_recomendacion"`.
  - `tests/api/test_h2_sin_respaldo.py`: los cuerpos completos de "no concluyente" suman
    `"evidencia_recomendacion": []`. Los de `sin_fallo` y `en_curso` no cambian, y siguen probando
    FR-007.
- **Razón**: la constitución (principio III) prohíbe modificar un test para que pase, pero permite
  cambiarlo cuando la spec cambia, si se justifica contra ella y va separado de la implementación. Acá
  el test no se ajusta al código: se ajusta al spec nuevo y falla hasta que se implementa.
- **Alternativas**: valor por defecto en el dataclass para no tocar los tests (rechazada en R3); dejar
  los tests viejos y sumar otros (quedarían tests que afirman que el diagnóstico tiene tres campos, en
  contra de FR-001).

## R7. Estrategia de tests nuevos

- **Decisión**:
  - `tests/unit/test_reglas.py` (mismo archivo, con su helper `trace()`): un test por fila de la tabla
    del spec y por caso borde, con IDs esperados escritos literalmente:
    - AC01 con una reversa posterior → `("OP-0100-E4",)`; AB05 con reversa → el ID de la reversa.
    - AM04 y AB05 sin reversa → `()`.
    - Escenario 4: AC01 sin reversa → `()`, misma causa, cita y recomendación.
    - Escenario 5: AC01 → reversa → reversa → los dos IDs, en orden; no es contradictoria (FR-012).
    - FR-008: reversa **antes** del AC01, y reversa antes del AB05 → `()`; en el AB05 la
      recomendación es la de "sin reversa", como en 001.
    - FR-006: 0 claves con reversa (como OP-0028) y > 1 claves con reversa (como OP-0029) → `()`.
    - FR-011: mismo resultado en llamadas repetidas.
  - `tests/api/test_evidencia_recomendacion.py` (archivo de tests nuevo; `app/` no suma módulos):
    historias 1 a 3 de punta a punta sobre los datos fijos. SC-001 (las 10 con un ID: `OP-0006-E4`…
    `OP-0010-E4`, `OP-0011-E5`…`OP-0015-E5`), SC-002 (las 15 + OP-0028 a OP-0030 con `[]`), SC-003
    (una OK cargada en el repositorio del test, OP-0026 y OP-0027 sin la clave), SC-005 (5 pedidos por
    operación). También el escenario 3 de la historia 1: el ID de la reversa no está en
    `eventos_citados`.
  - Sin cambios: `test_reglas_aislamiento.py` (sigue verificando que `app/diagnostico` es puro),
    `test_conjunto_evaluacion.py` (SC-004: causas y citas de 001 iguales) y `test_tiempos.py` (SC-006).
- **Razón**: igual que en 001 (001/R11), las reglas se prueban con traces armados y la API con los
  datos fijos. Los escenarios 4 y 5 solo existen como traces armados (FR-013).
- **Alternativas**: un archivo `test_reglas_evidencia.py` aparte; se descarta porque reutiliza el
  helper `trace()` y las constantes de `test_reglas.py`, y separar duplicaría código de test.
