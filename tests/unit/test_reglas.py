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
        (),
    )


def test_ac01_es_cuenta_incorrecta_y_cita_el_rechazo():
    eventos = trace(ORDEN, DEBITO, AC01, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "cuenta incorrecta",
        ("OP-0100-E3",),
        "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó",
        ("OP-0100-E4",),
    )


def test_ab05_con_reversa_posterior_es_timeout_con_reintento():
    eventos = trace(ORDEN, DEBITO, ENVIO, AB05, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "timeout",
        ("OP-0100-E4",),
        "El débito ya se devolvió: se puede reintentar la transferencia",
        ("OP-0100-E5",),
    )


def test_ab05_sin_reversa_es_timeout_pidiendo_la_reversa():
    eventos = trace(ORDEN, DEBITO, ENVIO, AB05)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "timeout",
        ("OP-0100-E4",),
        "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
        "Si se reintenta antes, se cobra dos veces",
        (),
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
        (),
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


# --- Sin causa (historia 2): OK, en curso, no concluyente -------------------
# Imports propios de esta sección, para no tocar los de la parte de la historia 1.

import pytest  # noqa: E402

from app.diagnostico.resultados import EnCurso, SinFallo  # noqa: E402

ACEPTACION = (TipoEvento.ACEPTACION_PROVEEDOR, None)
ACREDITACION = (TipoEvento.ACREDITACION_DESTINO, None)

SIN_FALLO = SinFallo("La operación no tiene un fallo para investigar")
EN_CURSO = EnCurso("La operación sigue en curso")
NO_CONCLUYENTE_SIN_CLAVE = Diagnostico(
    "no concluyente", (), "Pedir los logs del proveedor desde el último evento conocido", ()
)
CONTRADICTORIA = "Evidencia contradictoria: revisar manualmente los eventos citados"


def test_operacion_ok_no_se_diagnostica():
    eventos = trace(ORDEN, DEBITO, ACEPTACION, ACREDITACION)

    assert diagnosticar(Estado.OK, eventos, despues_del_ultimo(eventos, minutes=5)) == SIN_FALLO


@pytest.mark.parametrize(
    "espera",
    [timedelta(minutes=2), timedelta(minutes=10), timedelta(minutes=-1)],
    ids=["2 min", "exactamente 10 min", "hora de referencia anterior al último evento"],
)
def test_pendiente_dentro_del_plazo_sigue_en_curso(espera):
    eventos = trace(ORDEN, DEBITO)

    assert diagnosticar(Estado.PENDIENTE, eventos, eventos[-1].momento + espera) == EN_CURSO


@pytest.mark.parametrize(
    "espera",
    [timedelta(minutes=10, seconds=1), timedelta(minutes=15)],
    ids=["10 min 1 s", "15 min"],
)
def test_pendiente_con_el_plazo_vencido_es_no_concluyente_sin_citas(espera):
    eventos = trace(ORDEN, DEBITO)

    assert (
        diagnosticar(Estado.PENDIENTE, eventos, eventos[-1].momento + espera)
        == NO_CONCLUYENTE_SIN_CLAVE
    )


def test_fallida_sin_evento_clave_es_no_concluyente_enseguida():
    """El plazo de espera aplica solo a pendientes (FR-021, FR-025)."""
    eventos = trace(ORDEN, DEBITO, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=1))

    assert resultado == NO_CONCLUYENTE_SIN_CLAVE


@pytest.mark.parametrize(
    "rechazo",
    [
        (TipoEvento.RECHAZO_ORIGEN, CodigoMotivo.AC01),
        (TipoEvento.RECHAZO_TIMEOUT, CodigoMotivo.AM04),
        (TipoEvento.RECHAZO_BANCO_DESTINO, CodigoMotivo.AB05),
    ],
    ids=["rechazo_origen+AC01", "rechazo_timeout+AM04", "rechazo_banco_destino+AB05"],
)
def test_rechazo_que_no_es_evento_clave_es_no_concluyente_sin_citas(rechazo):
    eventos = trace(ORDEN, DEBITO, rechazo)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == NO_CONCLUYENTE_SIN_CLAVE


def test_ac01_y_ab05_es_evidencia_contradictoria_citando_los_dos():
    eventos = trace(ORDEN, DEBITO, AC01, AB05, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico("no concluyente", ("OP-0100-E3", "OP-0100-E4"), CONTRADICTORIA, ())


def test_dos_ab05_es_evidencia_contradictoria_y_no_timeout():
    eventos = trace(ORDEN, DEBITO, ENVIO, AB05, AB05)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico("no concluyente", ("OP-0100-E4", "OP-0100-E5"), CONTRADICTORIA, ())


def test_tres_eventos_clave_cita_los_tres_en_orden_del_trace():
    eventos = trace(ORDEN, AM04, AC01, AB05)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "no concluyente", ("OP-0100-E2", "OP-0100-E3", "OP-0100-E4"), CONTRADICTORIA, ()
    )


@pytest.mark.parametrize(
    ("estado", "pasos", "espera"),
    [
        (Estado.OK, (ORDEN, DEBITO, ACEPTACION, ACREDITACION), timedelta(minutes=5)),
        (Estado.PENDIENTE, (ORDEN, DEBITO), timedelta(minutes=2)),
        (Estado.PENDIENTE, (ORDEN, DEBITO), timedelta(minutes=15)),
        (Estado.FALLIDA, (ORDEN, DEBITO, REVERSA), timedelta(minutes=1)),
        (Estado.FALLIDA, (ORDEN, DEBITO, AC01, AB05, REVERSA), timedelta(minutes=5)),
        (Estado.FALLIDA, (ORDEN, DEBITO, ENVIO, AB05, AB05), timedelta(minutes=5)),
    ],
    ids=["ok", "en curso", "pendiente vencida", "sin clave", "AC01+AB05", "AB05+AB05"],
)
def test_cinco_llamadas_iguales_dan_el_mismo_resultado_sin_causa(estado, pasos, espera):
    eventos = trace(*pasos)
    hora = eventos[-1].momento + espera

    resultados = [diagnosticar(estado, eventos, hora) for _ in range(5)]

    assert all(r == resultados[0] for r in resultados)


# --- Evidencia de la recomendación (feature 002) ----------------------------
# Spec specs/002-evidencia-recomendacion: el cuarto campo de Diagnostico.

CUENTA_INCORRECTA = "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó"


def test_002_ac01_sin_reversa_tiene_evidencia_vacia():
    """002, historia 1, escenario 4 (FR-003): sin reversa posterior, misma causa, cita y
    recomendación de 001, y la evidencia de la recomendación vacía."""
    eventos = trace(ORDEN, DEBITO, AC01)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico("cuenta incorrecta", ("OP-0100-E3",), CUENTA_INCORRECTA, ())


def test_002_ac01_con_reversa_anterior_tiene_evidencia_vacia():
    """002/FR-008: una reversa del débito anterior al evento clave no cuenta como evidencia."""
    eventos = trace(ORDEN, DEBITO, REVERSA, AC01)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico("cuenta incorrecta", ("OP-0100-E4",), CUENTA_INCORRECTA, ())


def test_002_pendiente_vencida_con_reversa_tiene_evidencia_vacia():
    """002/FR-006: en "no concluyente" la evidencia va vacía aunque el trace tenga una reversa."""
    eventos = trace(ORDEN, DEBITO, REVERSA)

    resultado = diagnosticar(Estado.PENDIENTE, eventos, despues_del_ultimo(eventos, minutes=15))

    assert resultado == Diagnostico(
        "no concluyente", (), "Pedir los logs del proveedor desde el último evento conocido", ()
    )


@pytest.mark.parametrize(
    "pasos",
    [(ORDEN, DEBITO, AC01), (ORDEN, DEBITO, REVERSA, AC01)],
    ids=["AC01 sin reversa", "AC01 con reversa anterior"],
)
def test_002_cinco_llamadas_dan_la_misma_evidencia(pasos):
    """002/FR-011: la misma entrada da siempre la misma evidencia de la recomendación."""
    eventos = trace(*pasos)
    hora = despues_del_ultimo(eventos, minutes=5)

    resultados = [diagnosticar(Estado.FALLIDA, eventos, hora) for _ in range(5)]

    assert all(r == resultados[0] for r in resultados)
    assert resultados[0] == Diagnostico(
        "cuenta incorrecta", (eventos[-1].id,), CUENTA_INCORRECTA, ()
    )


def test_002_ac01_con_dos_reversas_cita_las_dos_en_orden():
    """002, historia 1, escenario 5 (FR-002, FR-003, FR-012): las dos reversas posteriores, en el
    orden del trace. No es evidencia contradictoria."""
    eventos = trace(ORDEN, DEBITO, AC01, REVERSA, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "cuenta incorrecta", ("OP-0100-E3",), CUENTA_INCORRECTA, ("OP-0100-E4", "OP-0100-E5")
    )


def test_002_ab05_con_dos_reversas_cita_las_dos_en_orden():
    """002/FR-004, FR-012: timeout con dos reversas posteriores cita las dos, en orden."""
    eventos = trace(ORDEN, DEBITO, ENVIO, AB05, REVERSA, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "timeout",
        ("OP-0100-E4",),
        "El débito ya se devolvió: se puede reintentar la transferencia",
        ("OP-0100-E5", "OP-0100-E6"),
    )


def test_002_reversa_anterior_al_ac01_no_cuenta():
    """002/FR-008: de una reversa anterior y otra posterior al evento clave, solo cuenta la posterior."""
    eventos = trace(ORDEN, DEBITO, REVERSA, AC01, REVERSA)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado == Diagnostico(
        "cuenta incorrecta", ("OP-0100-E4",), CUENTA_INCORRECTA, ("OP-0100-E5",)
    )


@pytest.mark.parametrize(
    "pasos",
    [
        (ORDEN, DEBITO, AC01, REVERSA, REVERSA),
        (ORDEN, DEBITO, ENVIO, AB05, REVERSA, REVERSA),
        (ORDEN, DEBITO, REVERSA, AC01, REVERSA),
    ],
    ids=["AC01 con dos reversas", "AB05 con dos reversas", "AC01 con reversa anterior y posterior"],
)
def test_002_la_reversa_nunca_esta_en_los_eventos_citados(pasos):
    """002/FR-009: la reversa va en la evidencia de la recomendación, nunca en los eventos citados."""
    eventos = trace(*pasos)

    resultado = diagnosticar(Estado.FALLIDA, eventos, despues_del_ultimo(eventos, minutes=5))

    assert resultado.evidencia_recomendacion != ()
    assert set(resultado.eventos_citados) & set(resultado.evidencia_recomendacion) == set()
