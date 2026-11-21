"""Sin conexiones externas ni azar en la app (constitución II y IV, FR-028).

Excepción al rojo→verde: verificación transversal. Recorre el AST de todos los .py de app/.
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"
ARCHIVOS = sorted(APP.rglob("*.py"))

MODULOS_PROHIBIDOS = {
    "httpx",
    "requests",
    "urllib.request",
    "urllib3",
    "http.client",
    "socket",
    "aiohttp",
    "random",
    "secrets",
    "openai",
    "anthropic",
}


def _prohibido(nombre: str | None) -> bool:
    if not nombre:
        return False
    return any(nombre == m or nombre.startswith(m + ".") for m in MODULOS_PROHIBIDOS)


def _imports_prohibidos(arbol: ast.AST) -> list[str]:
    encontrados = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            encontrados += [f"línea {nodo.lineno}: import {a.name}" for a in nodo.names if _prohibido(a.name)]
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
            if _prohibido(nodo.module):
                encontrados.append(f"línea {nodo.lineno}: from {nodo.module} import ...")
            # `from urllib import request` o `from http import client`
            encontrados += [
                f"línea {nodo.lineno}: from {nodo.module} import {a.name}"
                for a in nodo.names
                if nodo.module and _prohibido(f"{nodo.module}.{a.name}")
            ]
    return encontrados


def test_hay_archivos_para_revisar():
    assert len(ARCHIVOS) >= 10


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda r: str(r.relative_to(APP)))
def test_la_app_no_importa_red_azar_ni_llm(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))

    assert _imports_prohibidos(arbol) == []


def test_el_detector_encuentra_cada_forma_de_import():
    """Control del propio test: si el detector no ve nada, el test de arriba pasaría vacío."""
    codigo = (
        "import httpx\n"
        "import urllib.request\n"
        "from urllib import request\n"
        "from http import client\n"
        "from random import choice\n"
        "import anthropic.types\n"
        "import urllib.parse\n"
        "from http import HTTPStatus\n"
    )

    encontrados = " | ".join(_imports_prohibidos(ast.parse(codigo)))

    for esperado in [
        "import httpx",
        "import urllib.request",
        "from urllib import request",
        "from http import client",
        "from random",
        "import anthropic.types",
    ]:
        assert esperado in encontrados
    assert "urllib.parse" not in encontrados
    assert "HTTPStatus" not in encontrados
