"""Endpoints de contracts/api.md. Se agregan historia por historia."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.almacen.repositorio import Repositorio
from app.api.dependencias import obtener_reloj, obtener_repositorio, operacion_o_error
from app.api.esquemas import (
    DiagnosticoRespuesta,
    DiagnosticoSalida,
    EnCursoSalida,
    ErrorSalida,
    SinFalloSalida,
)
from app.diagnostico import diagnosticar
from app.diagnostico.resultados import Diagnostico, EnCurso, Resultado, SinFallo

router = APIRouter()

RepositorioDep = Annotated[Repositorio, Depends(obtener_repositorio)]
RelojDep = Annotated[Callable[[], datetime], Depends(obtener_reloj)]

ERRORES_DE_ID = {
    400: {"model": ErrorSalida, "description": "ID con formato inválido"},
    404: {"model": ErrorSalida, "description": "Operación no encontrada"},
}


def _a_salida(resultado: Resultado) -> DiagnosticoSalida | SinFalloSalida | EnCursoSalida:
    match resultado:
        case Diagnostico(causa=causa, eventos_citados=citados, recomendacion=recomendacion):
            return DiagnosticoSalida(
                causa=causa, eventos_citados=list(citados), recomendacion=recomendacion
            )
        case SinFallo(mensaje=mensaje):
            return SinFalloSalida(mensaje=mensaje)
        case EnCurso(mensaje=mensaje):
            return EnCursoSalida(mensaje=mensaje)


@router.get(
    "/operaciones/{id}/diagnostico",
    response_model=DiagnosticoRespuesta,
    responses=ERRORES_DE_ID,
    summary="Diagnosticar una operación",
)
def diagnosticar_operacion(id: str, repositorio: RepositorioDep, reloj: RelojDep):
    """Se calcula en cada pedido, nunca antes (FR-015). Las reglas no reciben el caso (FR-016).

    Hora de referencia (FR-026): la de los datos en las fijas; el momento del pedido en las generadas.
    """
    op = operacion_o_error(id, repositorio)
    hora_referencia = op.hora_referencia if op.origen == "fija" else reloj()
    return _a_salida(diagnosticar(op.estado, op.eventos, hora_referencia))
