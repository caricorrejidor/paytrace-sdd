"""Feature 002: evidencia de la recomendación (specs/002-evidencia-recomendacion/spec.md).

Los números de historia y escenario de los nombres (test_002_h<historia>_e<escenario>) son los del
spec de la 002, no los de la 001. Los textos esperados son los literales del spec, escritos acá.
"""

import pytest

CLAVES_DIAGNOSTICO = {"tipo", "causa", "eventos_citados", "recomendacion", "evidencia_recomendacion"}

SIN_CLAVE = "Pedir los logs del proveedor desde el último evento conocido"
CONTRADICTORIA = "Evidencia contradictoria: revisar manualmente los eventos citados"

RECOMENDACION_POR_CASO = {
    "fondos_insuficientes": "Avisar al cliente que no tenía saldo. No se debitó nada",
    "cuenta_incorrecta": (
        "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó"
    ),
    "timeout_con_reversa": "El débito ya se devolvió: se puede reintentar la transferencia",
    "timeout_sin_reversa": (
        "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
        "Si se reintenta antes, se cobra dos veces"
    ),
    "trace_incompleto": SIN_CLAVE,
}

CONJUNTO_DE_EVALUACION = [f"OP-{n:04d}" for n in range(1, 26)]

# SC-002: fondos insuficientes, timeout sin reversa, trace incompleto y los 3 casos borde.
CON_EVIDENCIA_VACIA = (
    [f"OP-{n:04d}" for n in range(1, 6)]
    + [f"OP-{n:04d}" for n in range(16, 26)]
    + ["OP-0028", "OP-0029", "OP-0030"]
)


def _diagnostico(cliente, id_operacion):
    respuesta = cliente.get(f"/operaciones/{id_operacion}/diagnostico")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == CLAVES_DIAGNOSTICO
    assert cuerpo["tipo"] == "diagnostico"
    return cuerpo


# --- Historia 2: evidencia vacía cuando no hay evento que respalde la recomendación ----------


def test_002_h2_e1_fondos_insuficientes_tiene_evidencia_vacia(cliente):
    """Dado una operación del caso "fondos insuficientes", Cuando el analista pide el diagnóstico,
    Entonces el diagnóstico tiene la causa, el evento citado y la recomendación de 001, y la evidencia
    de la recomendación está vacía."""
    cuerpo = _diagnostico(cliente, "OP-0001")

    assert cuerpo["causa"] == "fondos insuficientes"
    assert cuerpo["eventos_citados"] == ["OP-0001-E2"]
    assert cuerpo["recomendacion"] == RECOMENDACION_POR_CASO["fondos_insuficientes"]
    assert cuerpo["evidencia_recomendacion"] == []


def test_002_h2_e2_timeout_sin_reversa_tiene_evidencia_vacia(cliente):
    """Dado una operación del caso "timeout sin reversa", Cuando pide el diagnóstico, Entonces el
    diagnóstico tiene la causa "timeout", el evento citado y la recomendación de 001, y la evidencia
    de la recomendación está vacía."""
    cuerpo = _diagnostico(cliente, "OP-0016")

    assert cuerpo["causa"] == "timeout"
    assert cuerpo["eventos_citados"] == ["OP-0016-E4"]
    assert cuerpo["recomendacion"] == RECOMENDACION_POR_CASO["timeout_sin_reversa"]
    assert cuerpo["evidencia_recomendacion"] == []


def test_002_h2_e3_trace_incompleto_tiene_evidencia_vacia(cliente):
    """Dado una operación del caso "trace incompleto" con el plazo de espera vencido, Cuando pide el
    diagnóstico, Entonces la causa es "no concluyente", no cita ningún evento, la recomendación es
    "Pedir los logs del proveedor desde el último evento conocido" y la evidencia de la recomendación
    está vacía."""
    cuerpo = _diagnostico(cliente, "OP-0021")

    assert cuerpo["causa"] == "no concluyente"
    assert cuerpo["eventos_citados"] == []
    assert cuerpo["recomendacion"] == SIN_CLAVE
    assert cuerpo["evidencia_recomendacion"] == []


def test_002_h2_e4_sin_evento_clave_con_reversa_tiene_evidencia_vacia(cliente):
    """Dado la operación fallida del archivo de casos borde sin ningún evento clave (orden enviada →
    débito en origen → reversa del débito), Cuando pide el diagnóstico, Entonces la causa es "no
    concluyente", no cita ningún evento y la evidencia de la recomendación está vacía, aunque el
    trace tenga una reversa del débito."""
    cuerpo = _diagnostico(cliente, "OP-0028")

    assert cuerpo["causa"] == "no concluyente"
    assert cuerpo["eventos_citados"] == []
    assert cuerpo["recomendacion"] == SIN_CLAVE
    assert cuerpo["evidencia_recomendacion"] == []


def test_002_h2_e5_contradictoria_con_reversa_tiene_evidencia_vacia(cliente):
    """Dado la operación fallida del archivo de casos borde con dos eventos clave de códigos distintos
    (AC01 y AB05, seguidos de una reversa del débito), Cuando pide el diagnóstico, Entonces la causa
    es "no concluyente", cita exactamente esos dos eventos, la recomendación es "Evidencia
    contradictoria: revisar manualmente los eventos citados" y la evidencia de la recomendación está
    vacía, aunque el trace tenga una reversa del débito."""
    cuerpo = _diagnostico(cliente, "OP-0029")

    assert cuerpo["causa"] == "no concluyente"
    assert cuerpo["eventos_citados"] == ["OP-0029-E3", "OP-0029-E4"]
    assert cuerpo["recomendacion"] == CONTRADICTORIA
    assert cuerpo["evidencia_recomendacion"] == []


def test_002_h2_e6_dos_ab05_tiene_evidencia_vacia(cliente):
    """Dado la operación fallida del archivo de casos borde con dos rechazos por timeout AB05, Cuando
    pide el diagnóstico, Entonces la causa es "no concluyente", cita exactamente esos dos eventos y
    la evidencia de la recomendación está vacía."""
    cuerpo = _diagnostico(cliente, "OP-0030")

    assert cuerpo["causa"] == "no concluyente"
    assert cuerpo["eventos_citados"] == ["OP-0030-E4", "OP-0030-E5"]
    assert cuerpo["recomendacion"] == CONTRADICTORIA
    assert cuerpo["evidencia_recomendacion"] == []


@pytest.mark.parametrize("id_operacion", CON_EVIDENCIA_VACIA)
def test_002_sc002_evidencia_vacia(cliente, id_operacion):
    """SC-002: las 15 operaciones sin reversa que respalde la recomendación y las 3 de casos borde."""
    assert _diagnostico(cliente, id_operacion)["evidencia_recomendacion"] == []


@pytest.mark.parametrize("id_operacion", CONJUNTO_DE_EVALUACION)
def test_002_sc004_recomendacion_de_001(cliente, repositorio, id_operacion):
    """FR-010, SC-004: la recomendación es la de 001 para el caso de la operación. El caso sale del
    repositorio (dato de prueba), nunca de la API."""
    caso = repositorio.obtener(id_operacion).caso.value

    assert _diagnostico(cliente, id_operacion)["recomendacion"] == RECOMENDACION_POR_CASO[caso]
