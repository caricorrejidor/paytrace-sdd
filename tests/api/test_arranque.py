"""Arranque de la app: datos fijos cargados (FR-030) y generadas que no sobreviven al reinicio (FR-009)."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.dominio import Caso, Emisor, Estado, Evento, Operacion, TipoEvento

IDS_FIJOS = [f"OP-{n:04d}" for n in range(1, 31)]


def test_al_arrancar_estan_los_30_datos_fijos(repositorio):
    assert repositorio.cantidad() == 30
    assert all(repositorio.obtener(id_) is not None for id_ in IDS_FIJOS)


def test_las_generadas_se_pierden_al_reiniciar():
    from app.main import app

    generada = Operacion(
        id="OP-0031",
        estado=Estado.OK,
        eventos=(
            Evento(
                id="OP-0031-E1",
                momento=datetime(2026, 11, 19, 11, 0, tzinfo=UTC),
                tipo=TipoEvento.ORDEN_ENVIADA,
                emisor=Emisor.ORIGEN,
                codigo=None,
            ),
        ),
        caso=Caso.OK,
        hora_referencia=None,
        origen="generada",
    )
    # Cada `with TestClient(app)` corre el arranque y el apagado: el segundo es un reinicio.
    with TestClient(app) as primero:
        repositorio = primero.app.state.repositorio
        repositorio.agregar(generada)
        assert repositorio.cantidad() == 31

    with TestClient(app) as reiniciado:
        repositorio_nuevo = reiniciado.app.state.repositorio
        assert repositorio_nuevo.cantidad() == 30
        assert repositorio_nuevo.obtener("OP-0031") is None
