"""Carga y validación de los archivos de datos fijos (data-model.md, Reglas de validación)."""

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.almacen.carga import ErrorDatosFijos, cargar_archivo
from app.dominio import CodigoMotivo, Emisor, Estado, Operacion, TipoEvento


def _operacion_valida(id_operacion: str = "OP-0006") -> dict:
    return {
        "id": id_operacion,
        "estado": "fallida",
        "caso": "cuenta_incorrecta",
        "hora_referencia": "2026-11-02T10:05:00Z",
        "eventos": [
            {"id": f"{id_operacion}-E1", "momento": "2026-11-02T10:00:00Z", "tipo": "orden_enviada", "emisor": "origen"},
            {"id": f"{id_operacion}-E2", "momento": "2026-11-02T10:00:01Z", "tipo": "debito_origen", "emisor": "origen"},
            {
                "id": f"{id_operacion}-E3",
                "momento": "2026-11-02T10:00:02Z",
                "tipo": "rechazo_banco_destino",
                "emisor": "banco_destino",
                "codigo": "AC01",
            },
            {"id": f"{id_operacion}-E4", "momento": "2026-11-02T10:00:03Z", "tipo": "reversa_debito", "emisor": "origen"},
        ],
    }


def _escribir(tmp_path: Path, operaciones: list[dict], nombre: str = "datos.json") -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps({"operaciones": operaciones}), encoding="utf-8")
    return ruta


# --- Archivo válido -----------------------------------------------------------


def test_archivo_valido_se_convierte_a_tipos_de_dominio(tmp_path):
    ruta = _escribir(tmp_path, [_operacion_valida()])

    operaciones = cargar_archivo(ruta)

    assert len(operaciones) == 1
    op = operaciones[0]
    assert isinstance(op, Operacion)
    assert op.id == "OP-0006"
    assert op.estado is Estado.FALLIDA
    assert op.origen == "fija"
    assert op.hora_referencia == datetime(2026, 11, 2, 10, 5, tzinfo=UTC)
    assert op.hora_referencia.tzinfo is not None
    assert [e.id for e in op.eventos] == ["OP-0006-E1", "OP-0006-E2", "OP-0006-E3", "OP-0006-E4"]
    assert all(e.momento.tzinfo is not None for e in op.eventos)
    rechazo = op.eventos[2]
    assert rechazo.tipo is TipoEvento.RECHAZO_BANCO_DESTINO
    assert rechazo.emisor is Emisor.BANCO_DESTINO
    assert rechazo.codigo is CodigoMotivo.AC01
    assert op.eventos[0].codigo is None


def test_caso_es_opcional(tmp_path):
    datos = _operacion_valida()
    del datos["caso"]
    ruta = _escribir(tmp_path, [datos])

    assert cargar_archivo(ruta)[0].caso is None


# --- Rechazos por regla -------------------------------------------------------


def _modificada(cambio) -> dict:
    datos = copy.deepcopy(_operacion_valida())
    cambio(datos)
    return datos


def _sin_eventos(d):
    d["eventos"] = []


def _momentos_iguales(d):
    d["eventos"][1]["momento"] = d["eventos"][0]["momento"]


def _momentos_decrecientes(d):
    d["eventos"][1]["momento"] = "2026-11-02T09:59:00Z"


def _momento_sin_zona(d):
    d["eventos"][0]["momento"] = "2026-11-02T10:00:00"


def _hora_referencia_sin_zona(d):
    d["hora_referencia"] = "2026-11-02T10:05:00"


def _rechazo_sin_codigo(d):
    del d["eventos"][2]["codigo"]


def _no_rechazo_con_codigo(d):
    d["eventos"][1]["codigo"] = "AM04"


def _codigo_desconocido(d):
    d["eventos"][2]["codigo"] = "AM02"


def _emisor_que_no_coincide(d):
    d["eventos"][2]["emisor"] = "proveedor"


def _sin_hora_referencia(d):
    del d["hora_referencia"]


REGLAS_POR_OPERACION = {
    "regla 3: sin eventos": _sin_eventos,
    "regla 3: momentos iguales": _momentos_iguales,
    "regla 3: momentos decrecientes": _momentos_decrecientes,
    "regla 4: momento sin zona": _momento_sin_zona,
    "regla 4: hora de referencia sin zona": _hora_referencia_sin_zona,
    "regla 5: rechazo sin código": _rechazo_sin_codigo,
    "regla 5: evento no rechazo con código": _no_rechazo_con_codigo,
    "regla 5: código fuera de AM04/AC01/AB05": _codigo_desconocido,
    "regla 6: emisor que no coincide con el tipo": _emisor_que_no_coincide,
    "regla 7: falta hora_referencia": _sin_hora_referencia,
}


@pytest.mark.parametrize("cambio", REGLAS_POR_OPERACION.values(), ids=REGLAS_POR_OPERACION.keys())
def test_rechaza_operacion_invalida_nombrando_archivo_y_operacion(tmp_path, cambio):
    ruta = _escribir(tmp_path, [_operacion_valida("OP-0001"), _modificada(cambio)], nombre="roto.json")

    with pytest.raises(ErrorDatosFijos) as error:
        cargar_archivo(ruta)

    mensaje = str(error.value)
    assert "roto.json" in mensaje
    assert "OP-0006" in mensaje


@pytest.mark.parametrize("id_invalido", ["OP-06", "op-0006", "OP-0006\n", "OP-9000", "OP-9999"])
def test_regla_1_rechaza_id_de_operacion_invalido(tmp_path, id_invalido):
    datos = _operacion_valida()
    datos["id"] = id_invalido
    ruta = _escribir(tmp_path, [datos], nombre="roto.json")

    with pytest.raises(ErrorDatosFijos) as error:
        cargar_archivo(ruta)

    mensaje = str(error.value)
    assert "roto.json" in mensaje
    assert id_invalido.strip() in mensaje
