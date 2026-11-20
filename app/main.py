"""App FastAPI de PayTrace. Al arrancar carga los datos fijos; si fallan, la app no arranca (research R7)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.almacen.carga import cargar_datos_fijos
from app.almacen.repositorio import Repositorio
from app.api.dependencias import ErrorPayTrace
from app.api.rutas import router

DIRECTORIO_DATOS = Path(__file__).resolve().parent / "datos"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Repositorio nuevo en cada arranque: las generadas no sobreviven a un reinicio (FR-009).
    app.state.repositorio = Repositorio(cargar_datos_fijos(DIRECTORIO_DATOS))
    yield


app = FastAPI(
    title="PayTrace",
    description="Diagnóstico de transferencias simuladas fallidas o pendientes.",
    lifespan=lifespan,
)


@app.exception_handler(ErrorPayTrace)
async def _error_paytrace(request: Request, error: ErrorPayTrace) -> JSONResponse:
    return JSONResponse(status_code=error.status, content={"detalle": error.detalle})


app.include_router(router)
