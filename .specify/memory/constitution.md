<!--
Sync Impact Report
- Cambio de versión: plantilla sin completar → 1.0.0 (ratificación inicial)
- Principios definidos:
  - [PRINCIPLE_1_NAME] → I. Evidencia o nada
  - [PRINCIPLE_2_NAME] → II. Determinismo
  - [PRINCIPLE_3_NAME] → III. Test-first (NO NEGOCIABLE)
  - [PRINCIPLE_4_NAME] → IV. Solo datos simulados
  - [PRINCIPLE_5_NAME] → eliminado (el proyecto define 4 principios)
- Secciones agregadas: Flujo de desarrollo y puertas de calidad
- Secciones eliminadas: [SECTION_2_NAME] (restricciones adicionales / stack): el stack vive en
  AGENTS.md y en el plan de cada feature, no en la constitución
- Templates:
  - ✅ .specify/templates/plan-template.md: "Constitution Check" se deriva de este archivo; sin cambios
  - ✅ .specify/templates/spec-template.md: sin cambios necesarios
  - ✅ .specify/templates/tasks-template.md: nota de tests actualizada (obligatorios y primero para
    la lógica de diagnóstico)
  - ✅ .specify/templates/checklist-template.md: sin cambios necesarios
  - ✅ AGENTS.md, CLAUDE.md, PRD.md: no modificados por pedido explícito; ya son consistentes
- Ajuste previo al primer commit (se mantiene 1.0.0): principio I precisa que una causa exige
  exactamente un evento clave citado; evidencia insuficiente o contradictoria (p. ej. más de un
  evento clave) → "no concluyente" sin causa; en el caso contradictorio puede citar los eventos
  en conflicto; sin evento clave, sin eventos citados.
- TODOs diferidos: ninguno
-->

# Constitución de PayTrace

## Core Principles

### I. Evidencia o nada

- El sistema NUNCA nombra una causa sin citar exactamente un evento clave del trace que la
  prueba, identificado por su ID de evento.
- Si la evidencia no alcanza o es contradictoria (por ejemplo, hay más de un evento clave), la
  respuesta DEBE ser "no concluyente" y NUNCA se nombra una causa. El sistema NO DEBE inventar,
  suponer ni "adivinar la más probable" de las causas.
  - Evidencia contradictoria: la respuesta PUEDE citar los eventos en conflicto, por su ID, para
    que el analista los revise.
  - Sin ningún evento clave: la respuesta va sin eventos citados.
- Una operación sin fallo (OK) no se diagnostica.

**Razón**: el valor de PayTrace para el analista es un diagnóstico verificable. Una causa sin
evidencia es peor que no tener causa, porque lleva a acciones equivocadas y a que dos analistas
lleguen a conclusiones distintas.

### II. Determinismo

- El diagnóstico usa solo reglas fijas. NO DEBE usar LLM, modelos estadísticos ni ninguna fuente
  de aleatoriedad.
- La misma operación con los mismos datos de entrada DEBE dar siempre el mismo resultado: misma
  causa, mismos eventos citados y misma recomendación.
- La hora actual se recibe como dato de entrada (hora de referencia). Las reglas NUNCA leen el
  reloj del sistema ni ningún otro estado externo implícito.

**Razón**: un diagnóstico que cambia entre corridas no es auditable ni se puede testear. Recibir
la hora como dato hace reproducibles los casos que dependen del plazo de espera.

### III. Test-first (NO NEGOCIABLE)

- La lógica de diagnóstico se desarrolla con tests escritos ANTES que la implementación.
- Cada test DEBE verse fallar primero, y recién después se implementa lo mínimo para que pase
  (rojo → verde → refactor).
- Un test NUNCA se modifica para que pase. Si un test es incorrecto, el cambio se justifica
  contra la especificación (PRD/spec) y se hace como un cambio explícito, separado de la
  implementación.

**Razón**: las reglas de diagnóstico son el núcleo del producto; escribir el test primero
garantiza que cada regla responde a un comportamiento especificado y no a lo que el código
terminó haciendo.

### IV. Solo datos simulados

- El sistema NO DEBE conectarse con bancos, proveedores de pago ni ningún sistema real.
- NO DEBEN usarse datos personales reales: nombres, cuentas, documentos y demás datos son
  ficticios.
- Toda operación, evento y trace es simulado y generado o cargado por el propio sistema.

**Razón**: PayTrace es un MVP de demostración; operar con sistemas o datos reales agregaría
riesgos de seguridad, privacidad y cumplimiento que están fuera de su alcance.

## Flujo de desarrollo y puertas de calidad

- Cada plan de feature DEBE pasar el "Constitution Check" verificando los cuatro principios antes
  de la investigación (Fase 0) y de nuevo después del diseño (Fase 1).
- Las tareas de una feature que toque lógica de diagnóstico DEBEN incluir tareas de test que
  precedan a las de implementación.
- Una revisión de cambios DEBE rechazar: causas sin evento citado, lectura del reloj dentro de las
  reglas, cualquier fuente aleatoria o LLM en el diagnóstico, tests editados para hacerlos pasar,
  y conexiones o datos reales.
- Las decisiones de stack, tecnologías y estructura del proyecto no se fijan acá: corresponden a
  AGENTS.md y al plan de cada feature.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica del proyecto. Ante un conflicto entre
  un plan, una spec o una tarea y esta constitución, gana la constitución.
- Enmiendas: se proponen como un cambio a este archivo con su justificación, se actualiza el
  Sync Impact Report y se propagan los cambios a los templates de `.specify/templates/`.
- Versionado semántico:
  - MAJOR: se elimina o redefine un principio de forma incompatible.
  - MINOR: se agrega un principio o sección, o se amplía materialmente una guía.
  - PATCH: aclaraciones, redacción o correcciones sin cambio de significado.
- Cumplimiento: cada plan, spec, lista de tareas y revisión de código DEBE verificar el
  cumplimiento de los principios. Toda excepción se documenta y justifica en la sección
  "Complexity Tracking" del plan.

**Version**: 1.0.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15
