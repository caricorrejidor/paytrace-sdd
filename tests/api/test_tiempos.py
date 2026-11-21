"""Tiempos de respuesta (spec SC-005, SC-006). Excepción al rojo→verde: verificación transversal.

Se mide con time.perf_counter alrededor de cada pedido al TestClient, que corre la app en el mismo
proceso: no hay red, así que el tiempo medido es el del servidor más el del transporte en memoria,
una cota superior del tiempo del servidor que piden SC-005 y SC-006.
"""

import time

import pytest

CONJUNTO_EVALUACION = [f"OP-{n:04d}" for n in range(1, 26)]
PEDIDOS_POR_OPERACION = 5
LIMITE_SEGUNDOS = 2.0
PROPORCION_MINIMA = 0.95


def _medir(cliente, url: str) -> float:
    inicio = time.perf_counter()
    respuesta = cliente.get(url)
    duracion = time.perf_counter() - inicio
    assert respuesta.status_code == 200, url
    return duracion


@pytest.mark.parametrize(
    "plantilla",
    ["/operaciones/{id}/diagnostico", "/operaciones/{id}"],
    ids=["SC-005 diagnóstico", "SC-006 trace"],
)
def test_al_menos_el_95_por_ciento_responde_en_2_segundos(cliente, plantilla):
    duraciones = [
        _medir(cliente, plantilla.format(id=id_operacion))
        for id_operacion in CONJUNTO_EVALUACION
        for _ in range(PEDIDOS_POR_OPERACION)
    ]

    assert len(duraciones) == 125
    dentro = sum(d <= LIMITE_SEGUNDOS for d in duraciones)
    assert dentro / len(duraciones) >= PROPORCION_MINIMA, f"{dentro}/125 en ≤ 2 s"
