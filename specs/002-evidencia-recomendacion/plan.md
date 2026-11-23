# Implementation Plan: PayTrace — evidencia de la recomendación

**Branch**: `002-evidencia-recomendacion` | **Date**: 2026-11-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-evidencia-recomendacion/spec.md`

**Base**: [plan de la feature 001](../001-diagnostico-transferencias/plan.md). Todo lo que este plan no
menciona sigue como está ahí.

## Summary

El diagnóstico suma un cuarto campo, `evidencia_recomendacion`: los IDs de los eventos del trace que
respaldan la recomendación. Es un cambio chico sobre la 001 que no crea capas ni módulos:

- `app/diagnostico/resultados.py`: `Diagnostico` suma el campo, obligatorio.
- `app/diagnostico/reglas.py`: en "cuenta incorrecta" y "timeout" el campo lleva las reversas del
  débito posteriores al evento clave, en el orden del trace; en los demás casos, vacío. La
  recomendación de timeout y su evidencia salen del mismo cálculo.
- `app/api/esquemas.py` y `app/api/rutas.py`: la respuesta `diagnostico` suma la clave, siempre
  presente; `sin_fallo` y `en_curso` no la tienen.

Las reglas siguen siendo puras. Causa, eventos citados y recomendación no cambian. Decisiones en
[research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12, gestionado con uv (sin cambios)

**Primary Dependencies**: FastAPI 0.165.0, Pydantic 2.14.4, uvicorn 0.54.0 (sin cambios, sin dependencias nuevas)

**Storage**: N/A. En memoria; datos fijos JSON de 001 sin cambios (FR-013)

**Testing**: pytest 9.2.0 + httpx 0.28.1 (`TestClient`), sin cambios

**Target Platform**: servidor local (Linux/WSL2), `uv run uvicorn app.main:app`

**Project Type**: web service (solo API REST JSON)

**Performance Goals**: 002/SC-006, que remite a 001/SC-005 (diagnóstico) y 001/SC-006 (trace): ≤ 2 s
en el 95 % de 125 mediciones cada uno. El campo nuevo agrega
un recorrido del trace (≤ 5 eventos)

**Constraints**: reglas puras y deterministas, sin reloj, azar, LLM ni caso (FR-011); no se agregan
datos fijos (FR-013); no se crean módulos ni capas en `app/` (pedido del usuario)

**Scale/Scope**: 4 archivos de `app/` modificados; 1 archivo de tests nuevo y 3 actualizados

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Antes de Fase 0 | Después de Fase 1 |
|---|---|---|---|
| **I. Evidencia o nada** | `eventos_citados` no cambia: un solo evento clave cuando hay causa; ninguno o los en conflicto en "no concluyente" (FR-009). La reversa va solo en `evidencia_recomendacion`, que en "no concluyente" está vacía (FR-006) y en OK no existe (FR-007). La evidencia nunca inventa: es una lista de IDs del trace, o vacía ([research R4](./research.md#r4-regla-de-la-evidencia)). | ✅ | ✅ |
| **II. Determinismo** | `_reversas_posteriores()` es pura: solo mira el trace, sin reloj, azar, LLM ni caso. La firma de `diagnosticar(estado, eventos, hora_referencia)` no cambia y `test_reglas_aislamiento.py` sigue vigilándola. El principio enumera causa, citas y recomendación; FR-011 extiende el determinismo al campo nuevo sin enmendar la constitución. | ✅ | ✅ |
| **III. Test-first** | Primero se actualizan los tests de 001 que comparan el diagnóstico completo, justificado por FR-001 (modifica 001/FR-017), en una tarea propia y separada de la implementación ([research R6](./research.md#r6-tests-existentes-que-cambian)). Después, por historia, los tests nuevos de reglas y de API, que se ven fallar antes de la implementación que los pone en verde ([research R7](./research.md#r7-estrategia-de-tests-nuevos)). Sin excepciones al rojo→verde: lo que ya se cumple sin implementación nueva (SC-003, SC-005) lo cubren tests de 001 que no cambian, en lugar de tests nuevos que pasarían sin verse fallar. | ✅ | ✅ |
| **IV. Solo datos simulados** | Sin datos fijos nuevos (FR-013), sin conexiones; los traces de los escenarios 4 y 5 se arman dentro de los tests. | ✅ | ✅ |

**Resultado**: sin violaciones. Complexity Tracking queda vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-evidencia-recomendacion/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones del campo nuevo
├── data-model.md        # Fase 1: Diagnostico con el cuarto campo
├── quickstart.md        # Fase 1: guía de validación
├── contracts/
│   └── api.md           # Fase 1: cambio en GET /operaciones/{id}/diagnostico
├── checklists/          # Checklists del spec (ya existentes)
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea /speckit-plan)
```

### Source Code (repository root)

Solo se listan los archivos que cambian; el resto del árbol es el de 001.

```text
app/
├── diagnostico/
│   ├── resultados.py        # MODIFICA: Diagnostico.evidencia_recomendacion: tuple[str, ...] (sin default)
│   └── reglas.py            # MODIFICA: _reversas_posteriores(); cada rama devuelve su evidencia
└── api/
    ├── esquemas.py          # MODIFICA: DiagnosticoSalida.evidencia_recomendacion: list[str]
    └── rutas.py             # MODIFICA: _a_salida() copia el campo

tests/
├── unit/
│   └── test_reglas.py                       # ACTUALIZA expectativas (FR-001) + SUMA tests del campo
└── api/
    ├── test_h1_diagnostico_con_evidencia.py # ACTUALIZA: CLAVES_DIAGNOSTICO con la clave nueva
    ├── test_h2_sin_respaldo.py              # ACTUALIZA: cuerpos de "no concluyente" con []
    └── test_evidencia_recomendacion.py      # NUEVO: historias 1 y 2, SC-001, SC-002, recomendación de las 25 (SC-004)
```

Sin cambios: `app/diagnostico/textos.py`, `app/diagnostico/__init__.py`, `app/dominio.py`,
`app/almacen/`, `app/simulacion/`, `app/datos/`, `app/main.py`, `app/api/dependencias.py`, y los tests
`test_reglas_aislamiento.py`, `test_conjunto_evaluacion.py` (causas y citas de SC-004; SC-005 con
`test_sc007_*`), `test_h4_generacion.py` y `test_tiempos.py` (SC-006). La historia 3 y SC-003 los
cubren `test_h2_e2`, `test_h2_e3` y `test_h2_e4` de `test_h2_sin_respaldo.py` y
`test_ok_generada_da_sin_fallo` de `test_h4_generacion.py`, que comparan el cuerpo exacto de
`sin_fallo` y `en_curso` y no cambian.

**Structure Decision**: la de 001, sin módulos ni capas nuevos. Las dependencias siguen en un solo
sentido (`api` → `diagnostico` → `dominio`), y `diagnostico` sigue sin conocer la API, el reloj ni el
caso.

## Flujo de un diagnóstico (cambios sobre 001)

1. a 3. Sin cambios: validación del ID, hora de referencia y `diagnosticar(op.estado, op.eventos, hora)`.
4. Si hay exactamente un evento clave, `_con_un_evento_clave()` calcula una sola vez las reversas
   posteriores. En AC01 y AB05 van a `evidencia_recomendacion`; en AB05 también deciden la
   recomendación, igual que en 001. AM04 y las ramas "no concluyente" devuelven `()`.
5. `_a_salida()` convierte `Diagnostico` a `DiagnosticoSalida` con la lista; `SinFallo` y `EnCurso` se
   convierten igual que antes.

## Riesgos y notas para tareas

- **Orden test-first** (constitución III), para `/speckit-tasks`:
  1. Una tarea que actualiza los tests de 001 a cuatro campos (research R6), justificada por FR-001.
     Va antes de tocar `app/` y se ve fallar.
  2. Por historia (primero la 2, después la 1; ver tasks.md), los tests nuevos de reglas (escenarios
     4 y 5, FR-006, FR-008, FR-012) y de API, que se ven fallar.
  3. La implementación de esa historia: `resultados.py` y `reglas.py`, después `esquemas.py` y
     `rutas.py`.
- **Commits separados**: el cambio de tests de 001 va en su propio commit, distinto de los tests
  nuevos y de la implementación, para que la revisión vea que se justificó contra el spec y no contra
  el código.
- **Regresión de 001**: `test_conjunto_evaluacion.py` verifica que causas y citas no cambian en las 25
  operaciones (SC-004), pero no mira la recomendación. Por eso `test_evidencia_recomendacion.py` suma
  un test de recomendación sobre las 25 (FR-010, SC-004). La recomendación de timeout pasa a usar
  `bool(reversas)`, que es la misma condición que en 001. Lo confirman ese test y los tests de reglas
  de "timeout con reversa", "sin reversa" y "reversa anterior".
- **Datos fijos**: no se tocan. Si una tarea necesita un trace raro (sin reversa, dos reversas,
  reversa anterior), se arma en el test con el helper `trace()` de `test_reglas.py`.
- **Estado actual**: `uv run pytest` da 292 passed antes del cambio.

## Complexity Tracking

Sin violaciones de la constitución; no hay nada que justificar.
