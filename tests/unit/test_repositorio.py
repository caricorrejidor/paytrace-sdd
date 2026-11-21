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


# --- Historia 4: asignación de IDs (FR-002, FR-003, FR-032; research R9) ------

import threading  # noqa: E402

from app.almacen import repositorio as modulo_repositorio  # noqa: E402


def _con_ids(*ids: str) -> Repositorio:
    return Repositorio([_operacion(i) for i in ids])


def test_siguiente_id_con_los_30_fijos_es_op_0031():
    repo = _con_ids(*[f"OP-{n:04d}" for n in range(1, 31)])
    assert repo.siguiente_id() == "OP-0031"


def test_siguiente_id_no_reutiliza_huecos():
    assert _con_ids("OP-0001", "OP-0050").siguiente_id() == "OP-0051"


def test_crear_reserva_el_id_construye_y_agrega():
    repo = _con_ids("OP-0001")
    pedidos = []

    def construir(id_operacion):
        pedidos.append(id_operacion)
        return _operacion(id_operacion, origen="generada")

    creada = repo.crear(construir)

    assert pedidos == ["OP-0002"]
    assert creada.id == "OP-0002"
    assert repo.obtener("OP-0002") is creada
    assert repo.cantidad() == 2


def test_con_op_8999_siguiente_id_lanza_ids_agotados():
    with pytest.raises(modulo_repositorio.IdsAgotados):
        _con_ids("OP-0001", "OP-8999").siguiente_id()


def test_con_op_8999_crear_lanza_ids_agotados_sin_construir_ni_agregar():
    repo = _con_ids("OP-0001", "OP-8999")
    llamadas = []

    with pytest.raises(modulo_repositorio.IdsAgotados):
        repo.crear(lambda id_operacion: llamadas.append(id_operacion))

    assert llamadas == []
    assert repo.cantidad() == 2


def test_20_hilos_creando_a_la_vez_obtienen_ids_distintos_y_consecutivos():
    repo = _con_ids("OP-0001")
    largada = threading.Barrier(20)
    creados: list[str] = []
    candado = threading.Lock()

    def trabajar():
        largada.wait()
        op = repo.crear(lambda id_operacion: _operacion(id_operacion, origen="generada"))
        with candado:
            creados.append(op.id)

    hilos = [threading.Thread(target=trabajar) for _ in range(20)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert sorted(creados) == [f"OP-{n:04d}" for n in range(2, 22)]
    assert repo.cantidad() == 21
