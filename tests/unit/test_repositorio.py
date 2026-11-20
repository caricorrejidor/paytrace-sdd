"""Repositorio en memoria (data-model.md, Repositorio en memoria)."""

from datetime import UTC, datetime

import pytest

from app.almacen.repositorio import Repositorio
from app.dominio import Emisor, Estado, Evento, Operacion, TipoEvento


def _operacion(id_operacion: str, origen: str = "fija") -> Operacion:
    evento = Evento(
        id=f"{id_operacion}-E1",
        momento=datetime(2026, 11, 2, 10, 0, tzinfo=UTC),
        tipo=TipoEvento.ORDEN_ENVIADA,
        emisor=Emisor.ORIGEN,
        codigo=None,
    )
    return Operacion(
        id=id_operacion,
        estado=Estado.PENDIENTE,
        eventos=(evento,),
        caso=None,
        hora_referencia=datetime(2026, 11, 2, 10, 15, tzinfo=UTC) if origen == "fija" else None,
        origen=origen,
    )


def test_obtener_devuelve_la_operacion_existente():
    op = _operacion("OP-0001")
    repo = Repositorio([op, _operacion("OP-0002")])
    assert repo.obtener("OP-0001") is op


def test_obtener_devuelve_none_si_no_existe():
    repo = Repositorio([_operacion("OP-0001")])
    assert repo.obtener("OP-0002") is None


def test_cantidad_cuenta_las_operaciones():
    assert Repositorio([]).cantidad() == 0
    assert Repositorio([_operacion("OP-0001"), _operacion("OP-0002")]).cantidad() == 2


def test_agregar_suma_una_operacion():
    repo = Repositorio([_operacion("OP-0001")])
    nueva = _operacion("OP-0002", origen="generada")
    repo.agregar(nueva)
    assert repo.cantidad() == 2
    assert repo.obtener("OP-0002") is nueva


def test_agregar_con_id_existente_lanza_error_y_no_modifica_nada():
    original = _operacion("OP-0001")
    repo = Repositorio([original])
    with pytest.raises(ValueError):
        repo.agregar(_operacion("OP-0001", origen="generada"))
    assert repo.cantidad() == 1
    assert repo.obtener("OP-0001") is original


def test_constructor_con_ids_repetidos_lanza_error():
    with pytest.raises(ValueError):
        Repositorio([_operacion("OP-0001"), _operacion("OP-0001")])
