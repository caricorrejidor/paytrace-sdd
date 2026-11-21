"""Generador de operaciones simuladas (spec Historia 4, FR-001 a FR-004, FR-031; research R8)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.diagnostico import diagnosticar
from app.diagnostico.resultados import Diagnostico, SinFallo
from app.dominio import (
    EMISOR_POR_TIPO,
    TIPOS_RECHAZO,
    Caso,
    CodigoMotivo,
    Estado,
    TipoEvento,
    es_id_valido,
)
from app.simulacion.generador import generar

T = TipoEvento
C = CodigoMotivo

# Con microsegundos, para verificar que los momentos se truncan al segundo.
AHORA = datetime(2026, 11, 20, 15, 30, 45, 678901, tzinfo=UTC)
AHORA_TRUNCADO = datetime(2026, 11, 20, 15, 30, 45, tzinfo=UTC)

# Tabla de casos del spec: estado y secuencia exacta de (tipo, código).
TABLA = {
    Caso.OK: (
        Estado.OK,
        [
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.ACEPTACION_PROVEEDOR, None),
            (T.ACREDITACION_DESTINO, None),
        ],
    ),
    Caso.FONDOS_INSUFICIENTES: (
        Estado.FALLIDA,
        [(T.ORDEN_ENVIADA, None), (T.RECHAZO_ORIGEN, C.AM04)],
    ),
    Caso.CUENTA_INCORRECTA: (
        Estado.FALLIDA,
        [
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.RECHAZO_BANCO_DESTINO, C.AC01),
            (T.REVERSA_DEBITO, None),
        ],
    ),
    Caso.TIMEOUT_CON_REVERSA: (
        Estado.FALLIDA,
        [
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.ENVIO_PROVEEDOR, None),
            (T.RECHAZO_TIMEOUT, C.AB05),
            (T.REVERSA_DEBITO, None),
        ],
    ),
    Caso.TIMEOUT_SIN_REVERSA: (
        Estado.FALLIDA,
        [
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.ENVIO_PROVEEDOR, None),
            (T.RECHAZO_TIMEOUT, C.AB05),
        ],
    ),
    Caso.TRACE_INCOMPLETO: (
        Estado.PENDIENTE,
        [(T.ORDEN_ENVIADA, None), (T.DEBITO_ORIGEN, None)],
    ),
}

# Tabla de la Historia 4: el evento que tiene que estar y el último evento.
TIENE_Y_ULTIMO = {
    Caso.OK: ((T.ACREDITACION_DESTINO, None), (T.ACREDITACION_DESTINO, None)),
    Caso.FONDOS_INSUFICIENTES: ((T.RECHAZO_ORIGEN, C.AM04), (T.RECHAZO_ORIGEN, C.AM04)),
    Caso.CUENTA_INCORRECTA: ((T.RECHAZO_BANCO_DESTINO, C.AC01), (T.REVERSA_DEBITO, None)),
    Caso.TIMEOUT_CON_REVERSA: ((T.RECHAZO_TIMEOUT, C.AB05), (T.REVERSA_DEBITO, None)),
    Caso.TIMEOUT_SIN_REVERSA: ((T.RECHAZO_TIMEOUT, C.AB05), (T.RECHAZO_TIMEOUT, C.AB05)),
    Caso.TRACE_INCOMPLETO: ((T.DEBITO_ORIGEN, None), (T.DEBITO_ORIGEN, None)),
}

CAUSA_ESPERADA = {
    Caso.FONDOS_INSUFICIENTES: "fondos insuficientes",
    Caso.CUENTA_INCORRECTA: "cuenta incorrecta",
    Caso.TIMEOUT_CON_REVERSA: "timeout",
    Caso.TIMEOUT_SIN_REVERSA: "timeout",
    Caso.TRACE_INCOMPLETO: "no concluyente",
}

TODOS_LOS_CASOS = list(Caso)


def _tipos_y_codigos(op):
    return [(e.tipo, e.codigo) for e in op.eventos]


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_estado_y_secuencia_de_la_tabla_de_casos(caso):
    op = generar(caso, "OP-0031", AHORA)
    estado, secuencia = TABLA[caso]

    assert op.estado is estado
    assert _tipos_y_codigos(op) == secuencia


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_evento_y_ultimo_evento_de_la_historia_4(caso):
    op = generar(caso, "OP-0031", AHORA)
    tiene, ultimo = TIENE_Y_ULTIMO[caso]

    assert tiene in _tipos_y_codigos(op)
    assert _tipos_y_codigos(op)[-1] == ultimo


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_emisor_segun_el_tipo_y_codigo_solo_en_rechazos(caso):
    op = generar(caso, "OP-0031", AHORA)

    for e in op.eventos:
        assert e.emisor is EMISOR_POR_TIPO[e.tipo]
        assert (e.codigo is not None) == (e.tipo in TIPOS_RECHAZO)


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_ids_de_evento_con_el_id_de_la_operacion(caso):
    op = generar(caso, "OP-0031", AHORA)

    assert op.id == "OP-0031"
    assert es_id_valido(op.id)
    assert [e.id for e in op.eventos] == [f"OP-0031-E{n}" for n in range(1, len(op.eventos) + 1)]


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_momentos_separados_por_un_segundo_y_truncados(caso):
    op = generar(caso, "OP-0031", AHORA)
    momentos = [e.momento for e in op.eventos]

    for m in momentos:
        assert m.tzinfo is not None
        assert m.microsecond == 0
    assert all(b - a == timedelta(seconds=1) for a, b in zip(momentos, momentos[1:]))


@pytest.mark.parametrize("caso", [c for c in TODOS_LOS_CASOS if c is not Caso.TRACE_INCOMPLETO])
def test_con_resultado_final_el_ultimo_evento_es_ahora(caso):
    op = generar(caso, "OP-0031", AHORA)

    assert op.eventos[-1].momento == AHORA_TRUNCADO


def test_trace_incompleto_termina_11_minutos_antes_de_ahora():
    """FR-004: más de 10 minutos antes de la generación (research R8)."""
    op = generar(Caso.TRACE_INCOMPLETO, "OP-0031", AHORA)

    assert op.eventos[-1].momento == AHORA_TRUNCADO - timedelta(minutes=11)
    assert op.eventos[0].momento == AHORA_TRUNCADO - timedelta(minutes=11, seconds=1)


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_caso_origen_y_hora_de_referencia(caso):
    op = generar(caso, "OP-0031", AHORA)

    assert op.caso is caso
    assert op.origen == "generada"
    assert op.hora_referencia is None


@pytest.mark.parametrize("caso", TODOS_LOS_CASOS)
def test_misma_entrada_da_la_misma_operacion(caso):
    assert generar(caso, "OP-0031", AHORA) == generar(caso, "OP-0031", AHORA)


@pytest.mark.parametrize("caso", list(CAUSA_ESPERADA))
def test_diagnosticar_la_generada_da_la_causa_de_su_caso(caso):
    op = generar(caso, "OP-0031", AHORA)

    resultado = diagnosticar(op.estado, op.eventos, AHORA)

    assert isinstance(resultado, Diagnostico)
    assert resultado.causa == CAUSA_ESPERADA[caso]


def test_diagnosticar_la_ok_generada_no_da_diagnostico():
    op = generar(Caso.OK, "OP-0031", AHORA)

    resultado = diagnosticar(op.estado, op.eventos, AHORA)

    assert isinstance(resultado, SinFallo)
