"""Criterios de éxito sobre el conjunto de evaluación (spec SC-002, SC-003, SC-004, SC-007).

El caso esperado sale del repositorio (dato de prueba), nunca de la API, que no lo expone.
"""

import pytest

CAUSA_POR_CASO = {
    "fondos_insuficientes": "fondos insuficientes",
    "cuenta_incorrecta": "cuenta incorrecta",
    "timeout_con_reversa": "timeout",
    "timeout_sin_reversa": "timeout",
}

# Evento clave según el spec (FR-016): solo estas combinaciones de tipo y código.
COMBINACIONES_CLAVE = {
    ("rechazo_origen", "AM04"),
    ("rechazo_banco_destino", "AC01"),
    ("rechazo_timeout", "AB05"),
}

CON_TRACE_COMPLETO = [f"OP-{n:04d}" for n in range(1, 21)]


def _ids_de_eventos_clave(operacion) -> list[str]:
    return [
        e.id
        for e in operacion.eventos
        if (e.tipo.value, e.codigo.value if e.codigo else None) in COMBINACIONES_CLAVE
    ]


@pytest.mark.parametrize("id_operacion", CON_TRACE_COMPLETO)
def test_sc002_sc004_causa_del_caso_citando_su_unico_evento_clave(cliente, repositorio, id_operacion):
    operacion = repositorio.obtener(id_operacion)
    ids_clave = _ids_de_eventos_clave(operacion)
    assert len(ids_clave) == 1, "el dato de prueba debe tener un solo evento clave"

    cuerpo = cliente.get(f"/operaciones/{id_operacion}/diagnostico").json()

    assert cuerpo["causa"] == CAUSA_POR_CASO[operacion.caso.value]
    assert cuerpo["eventos_citados"] == ids_clave


@pytest.mark.parametrize("id_operacion", CON_TRACE_COMPLETO)
def test_sc007_cinco_pedidos_dan_el_mismo_cuerpo_trace_completo(cliente, id_operacion):
    respuestas = [cliente.get(f"/operaciones/{id_operacion}/diagnostico") for _ in range(5)]

    assert all(r.status_code == 200 for r in respuestas)
    cuerpos = [r.json() for r in respuestas]
    assert all(c == cuerpos[0] for c in cuerpos)
    assert cuerpos[0].get("tipo") == "diagnostico"


# --- Historia 2: las 5 con trace incompleto ----------------------------------

CON_TRACE_INCOMPLETO = [f"OP-{n:04d}" for n in range(21, 26)]


@pytest.mark.parametrize("id_operacion", CON_TRACE_INCOMPLETO)
def test_sc003_trace_incompleto_termina_como_no_concluyente(cliente, id_operacion):
    cuerpo = cliente.get(f"/operaciones/{id_operacion}/diagnostico").json()

    assert cuerpo["causa"] == "no concluyente"
    assert cuerpo["eventos_citados"] == []


@pytest.mark.parametrize("id_operacion", CON_TRACE_INCOMPLETO)
def test_sc007_cinco_pedidos_dan_el_mismo_cuerpo_trace_incompleto(cliente, id_operacion):
    respuestas = [cliente.get(f"/operaciones/{id_operacion}/diagnostico") for _ in range(5)]

    assert all(r.status_code == 200 for r in respuestas)
    cuerpos = [r.json() for r in respuestas]
    assert all(c == cuerpos[0] for c in cuerpos)
