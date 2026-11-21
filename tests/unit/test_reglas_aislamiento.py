"""Aislamiento del módulo de reglas (research R2, FR-016, FR-026, constitución II).

Recorre el AST de app/diagnostico/: no mira docstrings ni comentarios, solo código.
"""

import ast
from pathlib import Path

import pytest

DIAGNOSTICO = Path(__file__).resolve().parents[2] / "app" / "diagnostico"
ARCHIVOS = ["__init__.py", "reglas.py", "resultados.py", "textos.py"]

MODULOS_PROHIBIDOS = {
    "fastapi",
    "pydantic",
    "random",
    "secrets",
    "time",
    "app.api",
    "app.almacen",
    "app.simulacion",
}
LLAMADAS_PROHIBIDAS = {"now", "utcnow", "today"}
IDENTIFICADORES_PROHIBIDOS = {"Caso", "caso"}


def _modulo_prohibido(nombre: str | None) -> bool:
    if not nombre:
        return False
    return any(nombre == m or nombre.startswith(m + ".") for m in MODULOS_PROHIBIDOS)


def _violaciones(arbol: ast.AST) -> list[str]:
    encontradas = []
    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", "?")
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if _modulo_prohibido(alias.name):
                    encontradas.append(f"línea {linea}: import {alias.name}")
        elif isinstance(nodo, ast.ImportFrom):
            if _modulo_prohibido(nodo.module):
                encontradas.append(f"línea {linea}: from {nodo.module} import ...")
        if isinstance(nodo, ast.Call):
            funcion = nodo.func
            nombre = funcion.attr if isinstance(funcion, ast.Attribute) else getattr(funcion, "id", None)
            if nombre in LLAMADAS_PROHIBIDAS:
                encontradas.append(f"línea {linea}: llamada a {nombre}()")

        identificadores = []
        if isinstance(nodo, ast.Name):
            identificadores.append(nodo.id)
        elif isinstance(nodo, ast.Attribute):
            identificadores.append(nodo.attr)
        elif isinstance(nodo, ast.arg):
            identificadores.append(nodo.arg)
        elif isinstance(nodo, ast.keyword) and nodo.arg:
            identificadores.append(nodo.arg)
        elif isinstance(nodo, ast.alias):
            identificadores.extend(n for n in (nodo.name, nodo.asname) if n)
        for identificador in identificadores:
            if identificador.split(".")[-1] in IDENTIFICADORES_PROHIBIDOS:
                encontradas.append(f"línea {linea}: referencia a {identificador}")
    return encontradas


@pytest.mark.parametrize("archivo", ARCHIVOS)
def test_el_archivo_del_modulo_de_reglas_existe(archivo):
    assert (DIAGNOSTICO / archivo).is_file()


@pytest.mark.parametrize("archivo", ARCHIVOS)
def test_el_modulo_de_reglas_no_usa_dependencias_reloj_azar_ni_caso(archivo):
    ruta = DIAGNOSTICO / archivo
    assert ruta.is_file(), f"falta {ruta}"

    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))

    assert _violaciones(arbol) == []


def test_el_detector_encuentra_cada_tipo_de_violacion():
    """Control del propio test: si el detector no ve nada, el test de arriba pasaría vacío."""
    codigo = (
        "import random\n"
        "from fastapi import APIRouter\n"
        "from app.almacen.repositorio import Repositorio\n"
        "from datetime import datetime\n"
        "x = datetime.now()\n"
        "def f(caso): return caso\n"
        "from app.dominio import Caso\n"
        "y = op.caso\n"
        "g(caso=1)\n"
    )

    violaciones = " | ".join(_violaciones(ast.parse(codigo)))

    for esperado in ["import random", "from fastapi", "from app.almacen.repositorio", "now()", "Caso", "caso"]:
        assert esperado in violaciones
