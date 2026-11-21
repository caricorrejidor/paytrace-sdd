"""Dependencias de la API: validación de ID y reloj (contracts/api.md, Errores comunes de ID; research R5)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.api.dependencias import ErrorPayTrace, obtener_reloj, operacion_o_error
from app.dominio import Emisor, Estado, Evento, Operacion, TipoEvento


class _RepositorioFalso:
    def __init__(self, operaciones=()):
        self._operaciones = {op.id: op for op in operaciones}

    def obtener(self, id_operacion):
        return self._operaciones.get(id_operacion)


class _RepositorioQueNoDebeUsarse:
    def obtener(self, id_operacion):
        raise AssertionError("con un ID inválido no se consulta el repositorio")


def _operacion(id_operacion: str) -> Operacion:
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
        hora_referencia=datetime(2026, 11, 2, 10, 15, tzinfo=UTC),
        origen="fija",
    )


def test_devuelve_la_operacion_si_existe():
    op = _operacion("OP-0001")

    assert operacion_o_error("OP-0001", _RepositorioFalso([op])) is op


@pytest.mark.parametrize("texto", [None, "", "op1", "op-0001", " OP-0001"])
def test_id_invalido_da_400_sin_consultar_el_repositorio(texto):
    with pytest.raises(ErrorPayTrace) as error:
        operacion_o_error(texto, _RepositorioQueNoDebeUsarse())

    assert error.value.status == 400
    assert error.value.detalle == "Ingresá un ID con formato OP-0000"


def test_id_valido_inexistente_da_404():
    with pytest.raises(ErrorPayTrace) as error:
        operacion_o_error("OP-9999", _RepositorioFalso([_operacion("OP-0001")]))

    assert error.value.status == 404
    assert error.value.detalle == "Operación no encontrada"


def test_obtener_reloj_devuelve_un_callable_con_hora_utc():
    reloj = obtener_reloj()

    ahora = reloj()

    assert isinstance(ahora, datetime)
    assert ahora.utcoffset() == timedelta(0)
