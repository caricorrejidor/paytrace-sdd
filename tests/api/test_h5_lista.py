"""Historia 5: ver la lista de operaciones con su estado (spec, escenario 1; AC-02, FR-013)."""


def test_con_los_datos_fijos_lista_las_30_por_id_ascendente(cliente):
    respuesta = cliente.get("/operaciones")

    assert respuesta.status_code == 200
    lista = respuesta.json()
    assert [op["id"] for op in lista] == [f"OP-{n:04d}" for n in range(1, 31)]
    for op in lista:
        assert set(op) == {"id", "estado"}
        assert op["estado"] in {"ok", "fallida", "pendiente"}


def test_h5_e1_las_generadas_aparecen_con_su_estado(cliente):
    """Dado que se generaron operaciones de los casos "OK", "fondos insuficientes" y "trace
    incompleto", Cuando el analista abre la lista, Entonces ve esas 3 operaciones con los estados OK,
    fallida y pendiente."""
    generadas = [
        cliente.post("/operaciones", json={"caso": caso}).json()["id"]
        for caso in ["ok", "fondos_insuficientes", "trace_incompleto"]
    ]

    lista = cliente.get("/operaciones").json()

    assert len(lista) == 33
    estados = {op["id"]: op["estado"] for op in lista}
    assert [estados[i] for i in generadas] == ["ok", "fallida", "pendiente"]
    assert [op["id"] for op in lista] == sorted(op["id"] for op in lista)
