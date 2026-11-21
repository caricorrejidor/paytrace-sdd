"""Historia 4: generar operaciones simuladas por caso (spec, escenarios 1 a 3; FR-001 a FR-004, FR-032)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.dominio import Emisor, Estado, Evento, Operacion, TipoEvento

AGOTADOS = {"detalle": "No quedan IDs disponibles para generar operaciones"}

# Tabla de casos del spec: estado y secuencia de (tipo, código) del trace.
TABLA = {
    "ok": (
        "ok",
        [
            ("orden_enviada", None),
            ("debito_origen", None),
            ("aceptacion_proveedor", None),
            ("acreditacion_destino", None),
        ],
    ),
    "fondos_insuficientes": ("fallida", [("orden_enviada", None), ("rechazo_origen", "AM04")]),
    "cuenta_incorrecta": (
        "fallida",
        [
            ("orden_enviada", None),
            ("debito_origen", None),
            ("rechazo_banco_destino", "AC01"),
            ("reversa_debito", None),
        ],
    ),
    "timeout_con_reversa": (
        "fallida",
        [
            ("orden_enviada", None),
            ("debito_origen", None),
            ("envio_proveedor", None),
            ("rechazo_timeout", "AB05"),
            ("reversa_debito", None),
        ],
    ),
    "timeout_sin_reversa": (
        "fallida",
        [
            ("orden_enviada", None),
            ("debito_origen", None),
            ("envio_proveedor", None),
            ("rechazo_timeout", "AB05"),
        ],
    ),
    "trace_incompleto": ("pendiente", [("orden_enviada", None), ("debito_origen", None)]),
}


def _generar(cliente, caso):
    return cliente.post("/operaciones", json={"caso": caso})


@pytest.mark.parametrize("caso", list(TABLA))
def test_h4_e1_la_operacion_queda_con_el_estado_y_el_trace_de_la_tabla(cliente, caso):
    """Dado que el analista elige un caso, Cuando genera la operación, Entonces la operación queda
    con el estado y el trace de la tabla."""
    respuesta = _generar(cliente, caso)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    estado, secuencia = TABLA[caso]
    assert cuerpo["estado"] == estado
    assert [(e["tipo"], e.get("codigo")) for e in cuerpo["eventos"]] == secuencia
    assert set(cuerpo) == {"id", "estado", "eventos"}


def test_h4_e2_trace_incompleto_termina_mas_de_10_minutos_antes(cliente, reloj):
    """Dado que el analista elige "trace incompleto", Cuando genera la operación, Entonces el último
    evento del trace es más de 10 minutos anterior al momento de la generación."""
    cuerpo = _generar(cliente, "trace_incompleto").json()

    ultimo = datetime.fromisoformat(cuerpo["eventos"][-1]["momento"])
    assert reloj.ahora - ultimo > timedelta(minutes=10)


def test_h4_e3_el_id_es_el_siguiente_libre_y_no_empieza_con_op_9(cliente, repositorio):
    """Dado que están cargadas las operaciones del conjunto de evaluación, Cuando el analista genera
    una operación, Entonces su ID no coincide con ninguna existente y no empieza con "OP-9"."""
    existentes = {f"OP-{n:04d}" for n in range(1, 31)}
    assert all(repositorio.obtener(i) is not None for i in existentes)

    primero = _generar(cliente, "ok").json()["id"]
    segundo = _generar(cliente, "fondos_insuficientes").json()["id"]

    assert (primero, segundo) == ("OP-0031", "OP-0032")
    for id_generado in (primero, segundo):
        assert id_generado not in existentes
        assert not id_generado.startswith("OP-9")


def test_la_generada_queda_disponible_para_abrirla(cliente):
    id_generado = _generar(cliente, "cuenta_incorrecta").json()["id"]

    respuesta = cliente.get(f"/operaciones/{id_generado}")

    assert respuesta.status_code == 200
    assert respuesta.json()["eventos"][0]["id"] == f"{id_generado}-E1"


@pytest.mark.parametrize(
    "cuerpo", [{"caso": "desconocido"}, {}, {"caso": "OK"}], ids=["desconocido", "sin caso", "mayúscula"]
)
def test_caso_desconocido_o_ausente_da_422_y_no_crea_nada(cliente, repositorio, cuerpo):
    antes = repositorio.cantidad()

    respuesta = cliente.post("/operaciones", json=cuerpo)

    assert respuesta.status_code == 422
    assert repositorio.cantidad() == antes


def test_ids_agotados_da_409_y_no_crea_nada(cliente, repositorio):
    """FR-032: con OP-8999 presente el siguiente sería OP-9000, que no se puede usar."""
    repositorio.agregar(
        Operacion(
            id="OP-8999",
            estado=Estado.PENDIENTE,
            eventos=(
                Evento(
                    "OP-8999-E1",
                    datetime(2026, 11, 19, 11, 0, tzinfo=UTC),
                    TipoEvento.ORDEN_ENVIADA,
                    Emisor.ORIGEN,
                    None,
                ),
            ),
            caso=None,
            hora_referencia=None,
            origen="generada",
        )
    )
    antes = repositorio.cantidad()

    respuesta = _generar(cliente, "timeout_sin_reversa")

    assert respuesta.status_code == 409
    assert respuesta.json() == AGOTADOS
    assert repositorio.cantidad() == antes
    assert repositorio.obtener("OP-9000") is None


# --- Punta a punta con la Historia 2 ------------------------------------------


def test_ok_generada_da_sin_fallo(cliente):
    id_generado = _generar(cliente, "ok").json()["id"]

    cuerpo = cliente.get(f"/operaciones/{id_generado}/diagnostico").json()

    assert cuerpo == {"tipo": "sin_fallo", "mensaje": "La operación no tiene un fallo para investigar"}


def test_trace_incompleto_generado_diagnosticado_enseguida_es_no_concluyente(cliente):
    """Mismo reloj.ahora en la generación y en el diagnóstico: ya pasaron 11 minutos del último evento."""
    id_generado = _generar(cliente, "trace_incompleto").json()["id"]

    cuerpo = cliente.get(f"/operaciones/{id_generado}/diagnostico").json()

    assert cuerpo["tipo"] == "diagnostico"
    assert cuerpo["causa"] == "no concluyente"
    assert cuerpo["eventos_citados"] == []
