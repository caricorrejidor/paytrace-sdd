"""Contenido de los archivos reales de app/datos/ (contracts/datos-fijos.md, spec FR-007, FR-008, FR-029).

Los tests están separados por archivo y por caso para que cada archivo (y cada tramo del conjunto
de evaluación) pueda verse en verde por su cuenta.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.almacen.carga import cargar_archivo, cargar_datos_fijos

DATOS = Path(__file__).resolve().parents[2] / "app" / "datos"
EVALUACION = DATOS / "conjunto_evaluacion.json"
PLAZO = DATOS / "prueba_plazo.json"
BORDE = DATOS / "casos_borde.json"

# Secuencia exacta (tipo, código) de cada caso, según la tabla de casos del spec.
ORDEN = ("orden_enviada", None)
DEBITO = ("debito_origen", None)
ENVIO = ("envio_proveedor", None)
REVERSA = ("reversa_debito", None)
AM04 = ("rechazo_origen", "AM04")
AC01 = ("rechazo_banco_destino", "AC01")
AB05 = ("rechazo_timeout", "AB05")

SECUENCIAS = {
    "fondos_insuficientes": [ORDEN, AM04],
    "cuenta_incorrecta": [ORDEN, DEBITO, AC01, REVERSA],
    "timeout_con_reversa": [ORDEN, DEBITO, ENVIO, AB05, REVERSA],
    "timeout_sin_reversa": [ORDEN, DEBITO, ENVIO, AB05],
    "trace_incompleto": [ORDEN, DEBITO],
}

# Rangos de IDs del contrato de datos fijos.
RANGOS_EVALUACION = {
    "fondos_insuficientes": range(1, 6),
    "cuenta_incorrecta": range(6, 11),
    "timeout_con_reversa": range(11, 16),
    "timeout_sin_reversa": range(16, 21),
    "trace_incompleto": range(21, 26),
}


def _secuencia(op) -> list[tuple[str, str | None]]:
    return [(e.tipo.value, e.codigo.value if e.codigo else None) for e in op.eventos]


def _ids_de_evento_correlativos(op) -> bool:
    return [e.id for e in op.eventos] == [f"{op.id}-E{n}" for n in range(1, len(op.eventos) + 1)]


def _por_id(ruta: Path) -> dict:
    return {op.id: op for op in cargar_archivo(ruta)}


# --- (a) Conjunto de evaluación, por caso -------------------------------------


@pytest.mark.parametrize("caso", list(RANGOS_EVALUACION))
def test_evaluacion_tramo_del_caso(caso):
    operaciones = _por_id(EVALUACION)
    ids = [f"OP-{n:04d}" for n in RANGOS_EVALUACION[caso]]

    assert all(id_ in operaciones for id_ in ids), f"faltan operaciones de {caso}"
    estado_esperado = "pendiente" if caso == "trace_incompleto" else "fallida"
    primeros_momentos = set()
    for id_ in ids:
        op = operaciones[id_]
        assert op.caso.value == caso, id_
        assert op.estado.value == estado_esperado, id_
        assert _secuencia(op) == SECUENCIAS[caso], id_
        assert _ids_de_evento_correlativos(op), id_
        espera = op.hora_referencia - op.eventos[-1].momento
        if caso == "trace_incompleto":
            assert espera > timedelta(minutes=10), id_
        else:
            assert espera > timedelta(0), id_
        primeros_momentos.add(op.eventos[0].momento)
    assert len(primeros_momentos) == len(ids), f"hay operaciones de {caso} con los mismos horarios"


def test_evaluacion_tiene_25_operaciones_con_horarios_distintos():
    operaciones = cargar_archivo(EVALUACION)

    assert sorted(op.id for op in operaciones) == [f"OP-{n:04d}" for n in range(1, 26)]
    assert len({op.eventos[0].momento for op in operaciones}) == 25


# --- (b) Prueba de plazo ------------------------------------------------------


@pytest.mark.parametrize(("id_", "minutos"), [("OP-0026", 2), ("OP-0027", 10)])
def test_plazo(id_, minutos):
    operaciones = _por_id(PLAZO)

    assert sorted(operaciones) == ["OP-0026", "OP-0027"]
    op = operaciones[id_]
    assert op.estado.value == "pendiente"
    assert op.caso is None
    assert _ids_de_evento_correlativos(op)
    assert _secuencia(op) == [ORDEN, DEBITO]
    assert op.hora_referencia - op.eventos[-1].momento == timedelta(minutes=minutos)


# --- (c) Casos borde (FR-029) -------------------------------------------------

SECUENCIAS_BORDE = {
    "OP-0028": [ORDEN, DEBITO, REVERSA],
    "OP-0029": [ORDEN, DEBITO, AC01, AB05, REVERSA],
    "OP-0030": [ORDEN, DEBITO, ENVIO, AB05, AB05],
}


@pytest.mark.parametrize("id_", list(SECUENCIAS_BORDE))
def test_casos_borde(id_):
    operaciones = _por_id(BORDE)

    assert sorted(operaciones) == list(SECUENCIAS_BORDE)
    op = operaciones[id_]
    assert op.estado.value == "fallida"
    assert op.caso is None
    assert _ids_de_evento_correlativos(op)
    assert _secuencia(op) == SECUENCIAS_BORDE[id_]


# --- (d) Solo claves del contrato y sin datos personales (FR-028, SC-008) ----

CLAVES_DEL_CONTRATO = {
    "operaciones", "id", "estado", "caso", "hora_referencia", "eventos",
    "momento", "tipo", "emisor", "codigo",
}
VALORES_DE_ENUM = {
    "ok", "fallida", "pendiente",
    "origen", "proveedor", "banco_destino",
    "AM04", "AC01", "AB05",
    *SECUENCIAS,  # nombres de los casos con fallo o pendiente; "ok" ya está arriba
    *(tipo for tipo, _ in [ORDEN, DEBITO, ENVIO, REVERSA, AM04, AC01, AB05]),
    "aceptacion_proveedor", "acreditacion_destino",
}
PATRON_ID = re.compile(r"OP-[0-9]{4}(-E[0-9]+)?")


def _recorrer(valor, claves: set, textos: list):
    if isinstance(valor, dict):
        claves.update(valor)
        for v in valor.values():
            _recorrer(v, claves, textos)
    elif isinstance(valor, list):
        for v in valor:
            _recorrer(v, claves, textos)
    else:
        textos.append(valor)


def _es_texto_permitido(texto) -> bool:
    if not isinstance(texto, str):
        return False
    if texto in VALORES_DE_ENUM or PATRON_ID.fullmatch(texto):
        return True
    try:
        datetime.fromisoformat(texto)
        return True
    except ValueError:
        return False


@pytest.mark.parametrize("ruta", [EVALUACION, PLAZO, BORDE], ids=lambda r: r.name)
def test_json_solo_usa_claves_del_contrato_y_valores_simulados(ruta):
    claves: set = set()
    textos: list = []
    _recorrer(json.loads(ruta.read_text(encoding="utf-8")), claves, textos)

    assert claves <= CLAVES_DEL_CONTRATO
    no_permitidos = [t for t in textos if not _es_texto_permitido(t)]
    assert no_permitidos == []


# --- (e) Los tres archivos juntos ---------------------------------------------


def test_cargar_datos_fijos_devuelve_las_30_operaciones():
    operaciones = cargar_datos_fijos(DATOS)

    assert sorted(op.id for op in operaciones) == [f"OP-{n:04d}" for n in range(1, 31)]
