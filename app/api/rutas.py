"""Endpoints de contracts/api.md. Se agregan historia por historia."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.almacen.repositorio import Repositorio
from app.api.dependencias import obtener_repositorio, operacion_o_error
from app.api.esquemas import DiagnosticoSalida, ErrorSalida
from app.diagnostico import diagnosticar

router = APIRouter()

RepositorioDep = Annotated[Repositorio, Depends(obtener_repositorio)]

ERRORES_DE_ID = {
    400: {"model": ErrorSalida, "description": "ID con formato inválido"},
    404: {"model": ErrorSalida, "description": "Operación no encontrada"},
}


@router.get(
    "/operaciones/{id}/diagnostico",
    response_model=DiagnosticoSalida,
    responses=ERRORES_DE_ID,
    summary="Diagnosticar una operación",
)
def diagnosticar_operacion(id: str, repositorio: RepositorioDep) -> DiagnosticoSalida:
    """Se calcula en cada pedido, nunca antes (FR-015). Las reglas no reciben el caso (FR-016)."""
    op = operacion_o_error(id, repositorio)
    resultado = diagnosticar(op.estado, op.eventos, op.hora_referencia)
    return DiagnosticoSalida(
        causa=resultado.causa,
        eventos_citados=list(resultado.eventos_citados),
        recomendacion=resultado.recomendacion,
    )
