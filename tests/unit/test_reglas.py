"""Reglas de diagnóstico: diagnosticar(estado, eventos, hora_referencia) (spec FR-016 a FR-027, research R3).

Los textos esperados son los literales del spec, escritos acá (nunca importados de textos.py).
"""

from datetime import UTC, datetime, timedelta

from app.diagnostico import diagnosticar
from app.diagnostico.resultados import Diagnostico
from app.dominio import EMISOR_POR_TIPO, CodigoMotivo, Estado, Evento, TipoEvento

INICIO = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)

ORDEN = (TipoEvento.ORDEN_ENVIADA, None)
DEBITO = (TipoEvento.DEBITO_ORIGEN, None)
ENVIO = (TipoEvento.ENVIO_PROVEEDOR, None)
REVERSA = (TipoEvento.REVERSA_DEBITO, None)
AM04 = (TipoEvento.RECHAZO_ORIGEN, CodigoMotivo.AM04)
AC01 = (TipoEvento.RECHAZO_BANCO_DESTINO, CodigoMotivo.AC01)
AB05 = (TipoEvento.RECHAZO_TIMEOUT, CodigoMotivo.AB05)


def trace(*pasos, id_operacion: str = "OP-0100", separacion=timedelta(seconds=2)) -> tuple[Evento, ...]:
    """Arma un trace con IDs {op}-E{n} y momentos estrictamente crecientes."""
    return tuple(
        Evento(
            id=f"{id_operacion}-E{n}",
            momento=INICIO + separacion * (n - 1),
            tipo=tipo,
            emisor=EMISOR_POR_TIPO[tipo],
            codigo=codigo,
        )
        for n, (tipo, codigo) in enumerate(pasos, start=1)
    )


def despues_del_ultimo(eventos, **delta) -> datetime:
    return eventos[-1].momento + timedelta(**delta)


# --- Causa nombrada: exactamente un evento clave (historia 1) ----------------


def test_am04_es_fondos_insuficientes_y_cita_el_rechazo():
    eventos = trace(ORDEN, AM04)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "fondos insuficientes",
        ("OP-0100-E2",),
        "Avisar al cliente que no tenía saldo. No se debitó nada",
    )


def test_ac01_es_cuenta_incorrecta_y_cita_el_rechazo():
    eventos = trace(ORDEN, DEBITO, AC01, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "cuenta incorrecta",
        ("OP-0100-E3",),
        "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó",
    )


def test_ab05_con_reversa_posterior_es_timeout_con_reintento():
    eventos = trace(ORDEN, DEBITO, ENVIO, AB05, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "timeout",
        ("OP-0100-E4",),
        "El débito ya se devolvió: se puede reintentar la transferencia",
    )


def test_ab05_sin_reversa_es_timeout_pidiendo_la_reversa():
    eventos = trace(ORDEN, DEBITO, ENVIO, AB05)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "timeout",
        ("OP-0100-E4",),
        "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
        "Si se reintenta antes, se cobra dos veces",
    )


def test_ab05_con_reversa_anterior_al_rechazo_cuenta_como_sin_reversa():
    """FR-020: solo cuenta la reversa del débito posterior al rechazo."""
    eventos = trace(ORDEN, DEBITO, REVERSA, ENVIO, AB05)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "timeout",
        ("OP-0100-E5",),
        "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
        "Si se reintenta antes, se cobra dos veces",
    )


def test_el_resultado_de_una_fallida_no_depende_de_la_hora_de_referencia():
    eventos = trace(ORDEN, DEBITO, AC01, REVERSA)

    a_un_minuto = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=1))
    a_un_dia = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, days=1))

    assert a_un_minuto == a_un_dia


def test_cinco_llamadas_con_la_misma_entrada_dan_el_mismo_resultado():
    """FR-027: determinismo."""
    for pasos in [(ORDEN, AM04), (ORDEN, DEBITO, AC01, REVERSA), (ORDEN, DEBITO, ENVIO, AB05, REVERSA), (ORDEN, DEBITO, ENVIO, AB05)]:
        eventos = trace(*pasos)
        hora = despues_del_ultimo(eventos, minutes=5)

        resultados = [diagnosticar(Estado.FALLIDA, eventos, hora) for _ in range(5)]

        assert all(r == resultados[0] for r in resultados)
