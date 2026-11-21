"""Historia 1: diagnosticar una operación fallida con evidencia (spec, escenarios 1 a 4; AC-06, AC-07, AC-08)."""

CLAVES_DIAGNOSTICO = {"tipo", "causa", "eventos_citados", "recomendacion"}


def _diagnostico(cliente, id_operacion):
    respuesta = cliente.get(f"/operaciones/{id_operacion}/diagnostico")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == CLAVES_DIAGNOSTICO
    assert cuerpo["tipo"] == "diagnostico"
    return cuerpo


def test_h1_e1_fondos_insuficientes(cliente):
    """Dado una operación del caso "fondos insuficientes", Cuando el analista pide el diagnóstico,
    Entonces la causa es exactamente "fondos insuficientes", cita un solo evento (el "rechazo en
    origen, código AM04" de ese trace) y la recomendación es la de la tabla para ese caso."""
    cuerpo = _diagnostico(cliente, "OP-0001")

    assert cuerpo["causa"] == "fondos insuficientes"
    assert cuerpo["eventos_citados"] == ["OP-0001-E2"]
    assert cuerpo["recomendacion"] == "Avisar al cliente que no tenía saldo. No se debitó nada"


def test_h1_e2_cuenta_incorrecta(cliente):
    """Dado una operación del caso "cuenta incorrecta", Cuando pide el diagnóstico, Entonces la causa
    es exactamente "cuenta incorrecta", cita un solo evento (el "rechazo del banco destino, código
    AC01") y la recomendación es la de la tabla para ese caso."""
    cuerpo = _diagnostico(cliente, "OP-0006")

    assert cuerpo["causa"] == "cuenta incorrecta"
    assert cuerpo["eventos_citados"] == ["OP-0006-E3"]
    assert cuerpo["recomendacion"] == (
        "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó"
    )


def test_h1_e3_timeout_con_reversa(cliente):
    """Dado una operación del caso "timeout con reversa", Cuando pide el diagnóstico, Entonces la causa
    es exactamente "timeout", cita un solo evento (el "rechazo por timeout, código AB05") y la
    recomendación es "El débito ya se devolvió: se puede reintentar la transferencia"."""
    cuerpo = _diagnostico(cliente, "OP-0011")

    assert cuerpo["causa"] == "timeout"
    assert cuerpo["eventos_citados"] == ["OP-0011-E4"]
    assert cuerpo["recomendacion"] == "El débito ya se devolvió: se puede reintentar la transferencia"


def test_h1_e4_timeout_sin_reversa(cliente):
    """Dado una operación del caso "timeout sin reversa", Cuando pide el diagnóstico, Entonces la causa
    es exactamente "timeout", cita un solo evento (el "rechazo por timeout, código AB05") y la
    recomendación es "El débito todavía no se devolvió: pedir la reversa antes de reintentar. Si se
    reintenta antes, se cobra dos veces"."""
    cuerpo = _diagnostico(cliente, "OP-0016")

    assert cuerpo["causa"] == "timeout"
    assert cuerpo["eventos_citados"] == ["OP-0016-E4"]
    assert cuerpo["recomendacion"] == (
        "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
        "Si se reintenta antes, se cobra dos veces"
    )


def test_diagnostico_con_id_mal_formado_da_400(cliente):
    respuesta = cliente.get("/operaciones/op1/diagnostico")

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detalle": "Ingresá un ID con formato OP-0000"}


def test_diagnostico_de_operacion_inexistente_da_404(cliente):
    respuesta = cliente.get("/operaciones/OP-9999/diagnostico")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "Operación no encontrada"}
