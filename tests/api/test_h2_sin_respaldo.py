"""Historia 2: no diagnosticar sin respaldo (spec, escenarios 1 a 7; AC-08, AC-09, AC-10, AC-12, AC-15).

La operación OK y las pendientes generadas se insertan directamente en el repositorio con
origen="generada"; la prueba de punta a punta con POST /operaciones llega con la historia 4.
"""

from datetime import timedelta

from app.dominio import EMISOR_POR_TIPO, Caso, Estado, Evento, Operacion, TipoEvento

SIN_CLAVE = "Pedir los logs del proveedor desde el último evento conocido"
CONTRADICTORIA = "Evidencia contradictoria: revisar manualmente los eventos citados"


def _get(cliente, id_operacion):
    respuesta = cliente.get(f"/operaciones/{id_operacion}/diagnostico")
    assert respuesta.status_code == 200
    return respuesta.json()


def _generada(id_operacion, estado, caso, tipos, ultimo_momento) -> Operacion:
    """Operación como la dejaría el generador: sin hora de referencia propia."""
    eventos = tuple(
        Evento(
            id=f"{id_operacion}-E{n}",
            momento=ultimo_momento - timedelta(seconds=len(tipos) - n),
            tipo=tipo,
            emisor=EMISOR_POR_TIPO[tipo],
            codigo=None,
        )
        for n, tipo in enumerate(tipos, start=1)
    )
    return Operacion(
        id=id_operacion, estado=estado, eventos=eventos, caso=caso, hora_referencia=None, origen="generada"
    )


def test_h2_e1_trace_incompleto_es_no_concluyente(cliente):
    """Dado una operación del caso "trace incompleto", Cuando el analista pide el diagnóstico,
    Entonces la causa es "no concluyente", no aparece ninguna otra causa de la tabla, no cita ningún
    evento y la recomendación es "Pedir los logs del proveedor desde el último evento conocido"."""
    assert _get(cliente, "OP-0021") == {
        "tipo": "diagnostico",
        "causa": "no concluyente",
        "eventos_citados": [],
        "recomendacion": SIN_CLAVE,
    }


def test_h2_e2_operacion_ok_no_tiene_fallo(cliente, repositorio, reloj):
    """Dado una operación del caso "OK", Cuando pide el diagnóstico, Entonces el sistema muestra "La
    operación no tiene un fallo para investigar" y no muestra causa, eventos citados ni recomendación."""
    tipos = [
        TipoEvento.ORDEN_ENVIADA,
        TipoEvento.DEBITO_ORIGEN,
        TipoEvento.ACEPTACION_PROVEEDOR,
        TipoEvento.ACREDITACION_DESTINO,
    ]
    repositorio.agregar(_generada("OP-0031", Estado.OK, Caso.OK, tipos, reloj.ahora))

    cuerpo = _get(cliente, "OP-0031")

    assert cuerpo == {"tipo": "sin_fallo", "mensaje": "La operación no tiene un fallo para investigar"}


def test_h2_e3_pendiente_a_2_minutos_sigue_en_curso(cliente):
    """Dado la operación pendiente del archivo de prueba de plazo cuyo último evento es 2 minutos
    anterior a su hora de referencia, Cuando pide el diagnóstico, Entonces el sistema muestra "La
    operación sigue en curso" y no muestra causa, eventos citados ni recomendación."""
    assert _get(cliente, "OP-0026") == {"tipo": "en_curso", "mensaje": "La operación sigue en curso"}


def test_h2_e4_pendiente_a_exactamente_10_minutos_sigue_en_curso(cliente):
    """Dado la operación pendiente del archivo de prueba de plazo cuyo último evento es exactamente 10
    minutos anterior a su hora de referencia, Cuando pide el diagnóstico, Entonces el sistema muestra
    "La operación sigue en curso" y no muestra causa, eventos citados ni recomendación."""
    assert _get(cliente, "OP-0027") == {"tipo": "en_curso", "mensaje": "La operación sigue en curso"}


def test_h2_e5_fallida_sin_evento_clave_es_no_concluyente(cliente):
    """Dado la operación fallida del archivo de casos borde que no tiene ningún evento clave, Cuando el
    analista pide el diagnóstico, Entonces la causa es "no concluyente", no aparece ninguna otra causa
    de la tabla, no cita ningún evento y la recomendación es "Pedir los logs del proveedor desde el
    último evento conocido"."""
    assert _get(cliente, "OP-0028") == {
        "tipo": "diagnostico",
        "causa": "no concluyente",
        "eventos_citados": [],
        "recomendacion": SIN_CLAVE,
    }


def test_h2_e6_dos_eventos_clave_distintos_es_evidencia_contradictoria(cliente):
    """Dado la operación fallida del archivo de casos borde que tiene dos eventos clave con códigos
    distintos (AC01 y AB05), Cuando el analista pide el diagnóstico, Entonces la causa es "no
    concluyente", no aparece ninguna otra causa de la tabla, cita exactamente esos dos eventos por su
    ID y la recomendación es "Evidencia contradictoria: revisar manualmente los eventos citados"."""
    assert _get(cliente, "OP-0029") == {
        "tipo": "diagnostico",
        "causa": "no concluyente",
        "eventos_citados": ["OP-0029-E3", "OP-0029-E4"],
        "recomendacion": CONTRADICTORIA,
    }


def test_h2_e7_dos_ab05_es_evidencia_contradictoria(cliente):
    """Dado la operación fallida del archivo de casos borde que tiene dos rechazos por timeout con
    código AB05, Cuando el analista pide el diagnóstico, Entonces la causa es "no concluyente" (no
    "timeout"), no aparece ninguna otra causa de la tabla, cita exactamente esos dos eventos por su ID
    y la recomendación es "Evidencia contradictoria: revisar manualmente los eventos citados"."""
    assert _get(cliente, "OP-0030") == {
        "tipo": "diagnostico",
        "causa": "no concluyente",
        "eventos_citados": ["OP-0030-E4", "OP-0030-E5"],
        "recomendacion": CONTRADICTORIA,
    }


def test_generada_usa_la_hora_del_pedido_como_hora_de_referencia(cliente, repositorio, reloj):
    """FR-026: para las generadas, la hora de referencia es el momento en que se pide el diagnóstico."""
    tipos = [TipoEvento.ORDEN_ENVIADA, TipoEvento.DEBITO_ORIGEN]
    ultimo = reloj.ahora - timedelta(minutes=5)
    repositorio.agregar(_generada("OP-0031", Estado.PENDIENTE, Caso.TRACE_INCOMPLETO, tipos, ultimo))

    assert _get(cliente, "OP-0031") == {"tipo": "en_curso", "mensaje": "La operación sigue en curso"}

    reloj.ahora = ultimo + timedelta(minutes=11)

    assert _get(cliente, "OP-0031") == {
        "tipo": "diagnostico",
        "causa": "no concluyente",
        "eventos_citados": [],
        "recomendacion": SIN_CLAVE,
    }
