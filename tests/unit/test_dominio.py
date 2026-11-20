"""Tipos de dominio: enums, emisor por tipo, inmutabilidad y formato de ID (data-model.md)."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.dominio import (
    EMISOR_POR_TIPO,
    TIPOS_RECHAZO,
    Caso,
    CodigoMotivo,
    Emisor,
    Estado,
    Evento,
    Operacion,
    TipoEvento,
    es_id_valido,
)


def test_estado_tiene_los_valores_del_modelo():
    assert {e.value for e in Estado} == {"ok", "fallida", "pendiente"}


def test_emisor_tiene_los_valores_del_modelo():
    assert {e.value for e in Emisor} == {"origen", "proveedor", "banco_destino"}


def test_codigo_motivo_tiene_los_valores_del_modelo():
    assert {c.value for c in CodigoMotivo} == {"AM04", "AC01", "AB05"}


def test_tipo_evento_tiene_los_valores_del_modelo():
    assert {t.value for t in TipoEvento} == {
        "orden_enviada",
        "debito_origen",
        "envio_proveedor",
        "aceptacion_proveedor",
        "acreditacion_destino",
        "rechazo_origen",
        "rechazo_banco_destino",
        "rechazo_timeout",
        "reversa_debito",
    }


def test_caso_tiene_los_valores_del_modelo():
    assert {c.value for c in Caso} == {
        "ok",
        "fondos_insuficientes",
        "cuenta_incorrecta",
        "timeout_con_reversa",
        "timeout_sin_reversa",
        "trace_incompleto",
    }


def test_emisor_por_tipo_sigue_la_tabla_tipo_evento():
    assert {t.value: e.value for t, e in EMISOR_POR_TIPO.items()} == {
        "orden_enviada": "origen",
        "debito_origen": "origen",
        "envio_proveedor": "origen",
        "aceptacion_proveedor": "proveedor",
        "acreditacion_destino": "banco_destino",
        "rechazo_origen": "origen",
        "rechazo_banco_destino": "banco_destino",
        "rechazo_timeout": "proveedor",
        "reversa_debito": "origen",
    }


def test_tipos_rechazo_son_exactamente_los_tres_rechazos():
    assert {t.value for t in TIPOS_RECHAZO} == {
        "rechazo_origen",
        "rechazo_banco_destino",
        "rechazo_timeout",
    }


def _evento() -> Evento:
    return Evento(
        id="OP-0001-E1",
        momento=datetime(2026, 11, 2, 10, 0, tzinfo=UTC),
        tipo=TipoEvento.ORDEN_ENVIADA,
        emisor=Emisor.ORIGEN,
        codigo=None,
    )


def test_evento_es_inmutable():
    evento = _evento()
    with pytest.raises(FrozenInstanceError):
        evento.id = "OP-0001-E2"


def test_operacion_es_inmutable():
    operacion = Operacion(
        id="OP-0001",
        estado=Estado.PENDIENTE,
        eventos=(_evento(),),
        caso=None,
        hora_referencia=datetime(2026, 11, 2, 10, 15, tzinfo=UTC),
        origen="fija",
    )
    with pytest.raises(FrozenInstanceError):
        operacion.estado = Estado.OK


@pytest.mark.parametrize("texto", ["OP-0001", "OP-9999"])
def test_es_id_valido_acepta_el_formato(texto):
    assert es_id_valido(texto) is True


@pytest.mark.parametrize(
    "texto",
    [
        "op1",
        "op-0001",
        "",
        " OP-0001",
        "OP-0001 ",
        "OP-0001\n",
        "OP-001",
        "OP-00001",
        "OP-٠٠٠١",  # dígitos arábigo-índicos
    ],
)
def test_es_id_valido_rechaza_formatos_invalidos(texto):
    assert es_id_valido(texto) is False
