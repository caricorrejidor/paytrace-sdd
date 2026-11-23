"""Reglas fijas de diagnóstico (research R3, spec FR-016 a FR-027).

Módulo puro: decide solo con el estado, el trace y la hora de referencia que recibe. No lee el
reloj, no usa azar y no conoce con qué escenario se generó la operación (constitución II).
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from app.diagnostico import textos
from app.diagnostico.resultados import Diagnostico, EnCurso, Resultado, SinFallo
from app.dominio import CodigoMotivo, Estado, Evento, TipoEvento

# Las únicas combinaciones de tipo y código que son evento clave (FR-016).
_COMBINACIONES_CLAVE = {
    (TipoEvento.RECHAZO_ORIGEN, CodigoMotivo.AM04),
    (TipoEvento.RECHAZO_BANCO_DESTINO, CodigoMotivo.AC01),
    (TipoEvento.RECHAZO_TIMEOUT, CodigoMotivo.AB05),
}


# Plazo de espera de las pendientes: vence solo con MÁS de 10 minutos (FR-025).
PLAZO_DE_ESPERA = timedelta(minutes=10)


def es_evento_clave(evento: Evento) -> bool:
    return (evento.tipo, evento.codigo) in _COMBINACIONES_CLAVE


def diagnosticar(
    estado: Estado, eventos: Sequence[Evento], hora_referencia: datetime
) -> Resultado:
    """Aplica las reglas en el orden de research R3; la primera que aplica decide."""
    # 1. Una operación OK no se diagnostica (FR-023).
    if estado is Estado.OK:
        return SinFallo(textos.MENSAJE_SIN_FALLO)

    # 2. Una pendiente dentro del plazo sigue en curso (FR-024, FR-025). Con exactamente 10 minutos
    #    también, y si la hora de referencia es anterior al último evento, la espera es negativa.
    if estado is Estado.PENDIENTE and hora_referencia - eventos[-1].momento <= PLAZO_DE_ESPERA:
        return EnCurso(textos.MENSAJE_EN_CURSO)

    # 3. Eventos clave del trace, en su orden.
    claves = [e for e in eventos if es_evento_clave(e)]

    # Más de uno: evidencia contradictoria, sin causa, citando todos (FR-022).
    if len(claves) > 1:
        return Diagnostico(
            textos.CAUSA_NO_CONCLUYENTE,
            tuple(e.id for e in claves),
            textos.RECOMENDACION_EVIDENCIA_CONTRADICTORIA,
            (),  # 002/FR-006: sin evidencia de la recomendación
        )

    # Ninguno: no concluyente, sin causa y sin citas (FR-021).
    if not claves:
        return Diagnostico(
            textos.CAUSA_NO_CONCLUYENTE,
            (),
            textos.RECOMENDACION_SIN_EVENTO_CLAVE,
            (),  # 002/FR-006: sin evidencia de la recomendación
        )

    # Exactamente uno: la única rama que nombra una causa (constitución I).
    return _con_un_evento_clave(claves[0], eventos)


def _con_un_evento_clave(clave: Evento, eventos: Sequence[Evento]) -> Diagnostico:
    """Exactamente un evento clave: nombra la causa y cita ese evento (FR-018 a FR-020)."""
    if clave.codigo is CodigoMotivo.AM04:
        return Diagnostico(
            textos.CAUSA_FONDOS_INSUFICIENTES,
            (clave.id,),
            textos.RECOMENDACION_FONDOS_INSUFICIENTES,
            (),  # 002/FR-005
        )
    if clave.codigo is CodigoMotivo.AC01:
        return Diagnostico(
            textos.CAUSA_CUENTA_INCORRECTA,
            (clave.id,),
            textos.RECOMENDACION_CUENTA_INCORRECTA,
            (),  # vacía por ahora: las reversas llegan con la historia 1 de la 002 (T010)
        )
    # AB05: la recomendación depende de si hay una reversa del débito después del rechazo.
    posicion = list(eventos).index(clave)
    hay_reversa_posterior = any(
        e.tipo is TipoEvento.REVERSA_DEBITO for e in eventos[posicion + 1 :]
    )
    return Diagnostico(
        textos.CAUSA_TIMEOUT,
        (clave.id,),
        textos.RECOMENDACION_TIMEOUT_CON_REVERSA
        if hay_reversa_posterior
        else textos.RECOMENDACION_TIMEOUT_SIN_REVERSA,
        (),  # vacía por ahora: las reversas llegan con la historia 1 de la 002 (T010)
    )
