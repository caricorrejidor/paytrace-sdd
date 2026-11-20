"""Fixtures de los tests de API: reloj fijo y repositorio fresco por test (research R5, R11).

app.main se importa dentro de la fixture para que los tests unitarios no dependan de que exista.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

HORA_FIJA = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


@dataclass
class RelojFalso:
    """Cada test puede mover `ahora`; las rutas lo leen en cada llamada a reloj()."""

    ahora: datetime = HORA_FIJA


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


@pytest.fixture
def cliente(reloj):
    from app.api.dependencias import obtener_reloj
    from app.main import app

    # obtener_reloj devuelve una función que da la hora; el reemplazo también, y la lee en cada
    # llamada para que mover reloj.ahora dentro del test tenga efecto.
    app.dependency_overrides[obtener_reloj] = lambda: (lambda: reloj.ahora)
    try:
        with TestClient(app) as cliente_http:  # corre el lifespan: repositorio fresco por test
            yield cliente_http
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def repositorio(cliente):
    return cliente.app.state.repositorio
