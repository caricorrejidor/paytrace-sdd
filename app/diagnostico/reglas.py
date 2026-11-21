"""Reglas fijas de diagnóstico (research R3, spec FR-016 a FR-027).

Módulo puro: decide solo con el estado, el trace y la hora de referencia que recibe. No lee el
reloj, no usa azar y no conoce con qué escenario se generó la operación (constitución II).
"""

from collections.abc import Sequence
from datetime import datetime

from app.diagnostico import textos
from app.diagnostico.resultados import Diagnostico, Resultado
from app.dominio import CodigoMotivo, Estado, Evento, TipoEvento

# Las únicas combinaciones de tipo y código que son evento clave (FR-016).
_COMBINACIONES_CLAVE = {
    (TipoEvento.RECHAZO_ORIGEN, CodigoMotivo.AM04),
    (TipoEvento.RECHAZO_BANCO_DESTINO, CodigoMotivo.AC01),
    (TipoEvento.RECHAZO_TIMEOUT, CodigoMotivo.AB05),
}


def es_evento_clave(evento: Evento) -> bool:
    return (evento.tipo, evento.codigo) in _COMBINACIONES_CLAVE


def diagnosticar(
    estado: Estado, eventos: Sequence[Evento], hora_referencia: datetime
) -> Resultado:
    if estado is Estado.OK:
        raise NotImplementedError("operación OK: llega con la historia 2")
    if estado is Estado.PENDIENTE:
        raise NotImplementedError("plazo de espera de pendientes: llega con la historia 2")

    claves = [e for e in eventos if es_evento_clave(e)]
    if len(claves) != 1:
        raise NotImplementedError("ninguno o más de un evento clave: llega con la historia 2")

    return _con_un_evento_clave(claves[0], eventos)


def _con_un_evento_clave(clave: Evento, eventos: Sequence[Evento]) -> Diagnostico:
    """Exactamente un evento clave: nombra la causa y cita ese evento (FR-018 a FR-020)."""
    if clave.codigo is CodigoMotivo.AM04:
        return Diagnostico(
            textos.CAUSA_FONDOS_INSUFICIENTES,
            (clave.id,),
            textos.RECOMENDACION_FONDOS_INSUFICIENTES,
        )
    if clave.codigo is CodigoMotivo.AC01:
        return Diagnostico(
            textos.CAUSA_CUENTA_INCORRECTA,
            (clave.id,),
            textos.RECOMENDACION_CUENTA_INCORRECTA,
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
    )
