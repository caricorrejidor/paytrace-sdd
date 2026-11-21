"""Historia 3: buscar una operación y ver su trace (spec, escenarios 1 a 4; AC-03, AC-04, AC-05, AC-11)."""

from datetime import datetime

import pytest

ID_INVALIDO = {"detalle": "Ingresá un ID con formato OP-0000"}
NO_ENCONTRADA = {"detalle": "Operación no encontrada"}
TIPOS_RECHAZO = {"rechazo_origen", "rechazo_banco_destino", "rechazo_timeout"}


def test_h3_e1_buscar_un_id_existente_muestra_la_operacion(cliente):
    """Dado que existe la operación "OP-0001", Cuando el analista busca "OP-0001", Entonces el sistema
    muestra la operación "OP-0001"."""
    respuesta = cliente.get("/busqueda", params={"id": "OP-0001"})

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == "OP-0001"


def test_h3_e2_buscar_un_id_inexistente_muestra_no_encontrada(cliente):
    """Dado que no existe ninguna operación "OP-9999", Cuando busca "OP-9999", Entonces el sistema
    muestra "Operación no encontrada"."""
    respuesta = cliente.get("/busqueda", params={"id": "OP-9999"})

    assert respuesta.status_code == 404
    assert respuesta.json() == NO_ENCONTRADA


@pytest.mark.parametrize(
    "url",
    ["/busqueda?id=op1", "/busqueda?id=op-0001", "/busqueda?id=", "/busqueda", "/busqueda?id=%20OP-0001"],
    ids=["op1", "op-0001", "vacío", "sin parámetro", "espacio adelante"],
)
def test_h3_e3_id_mal_escrito_o_vacio_pide_el_formato(cliente, url):
    """Dado que el analista escribe "op1", "op-0001" o deja la búsqueda vacía, Cuando busca, Entonces
    el sistema muestra "Ingresá un ID con formato OP-0000" y no muestra ninguna operación ni
    "Operación no encontrada"."""
    respuesta = cliente.get(url)

    assert respuesta.status_code == 400
    assert respuesta.json() == ID_INVALIDO


def test_h3_e4_abrir_la_operacion_muestra_sus_4_eventos_en_orden(cliente):
    """Dado una operación del caso "cuenta incorrecta", que tiene 4 eventos, Cuando el analista la
    abre, Entonces ve los 4 eventos, del más antiguo al más nuevo."""
    respuesta = cliente.get("/operaciones/OP-0006")

    assert respuesta.status_code == 200
    eventos = respuesta.json()["eventos"]
    assert [e["id"] for e in eventos] == ["OP-0006-E1", "OP-0006-E2", "OP-0006-E3", "OP-0006-E4"]
    momentos = [datetime.fromisoformat(e["momento"]) for e in eventos]
    assert all(a < b for a, b in zip(momentos, momentos[1:]))


def test_el_detalle_no_expone_caso_hora_de_referencia_ni_diagnostico(cliente):
    """El caso y la hora de referencia son internos; el diagnóstico solo se da cuando se pide (FR-015)."""
    cuerpo = cliente.get("/operaciones/OP-0006").json()

    assert set(cuerpo) == {"id", "estado", "eventos"}
    for clave in ["caso", "hora_referencia", "tipo", "causa", "eventos_citados", "recomendacion"]:
        assert clave not in cuerpo


def test_codigo_aparece_solo_en_los_rechazos(cliente):
    eventos = cliente.get("/operaciones/OP-0029").json()["eventos"]

    for evento in eventos:
        if evento["tipo"] in TIPOS_RECHAZO:
            assert evento["codigo"] in {"AM04", "AC01", "AB05"}
        else:
            assert "codigo" not in evento


def test_abrir_con_id_mal_formado_da_400(cliente):
    respuesta = cliente.get("/operaciones/op1")

    assert respuesta.status_code == 400
    assert respuesta.json() == ID_INVALIDO


def test_abrir_una_operacion_inexistente_da_404(cliente):
    respuesta = cliente.get("/operaciones/OP-9999")

    assert respuesta.status_code == 404
    assert respuesta.json() == NO_ENCONTRADA
