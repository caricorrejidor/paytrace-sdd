"""Endpoints de contracts/api.md. Se agregan historia por historia."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.almacen.repositorio import IdsAgotados, Repositorio
from app.api.dependencias import (
    ErrorPayTrace,
    obtener_reloj,
    obtener_repositorio,
    operacion_o_error,
)
from app.api.esquemas import (
    DiagnosticoRespuesta,
    DiagnosticoSalida,
    EnCursoSalida,
    ErrorSalida,
    OperacionDetalle,
    OperacionResumen,
    PedidoGeneracion,
    SinFalloSalida,
    detalle_de,
)
from app.diagnostico import diagnosticar
from app.diagnostico.resultados import Diagnostico, EnCurso, Resultado, SinFallo
from app.simulacion import generar

router = APIRouter()

RepositorioDep = Annotated[Repositorio, Depends(obtener_repositorio)]
RelojDep = Annotated[Callable[[], datetime], Depends(obtener_reloj)]

ERRORES_DE_ID = {
    400: {"model": ErrorSalida, "description": "ID con formato inválido"},
    404: {"model": ErrorSalida, "description": "Operación no encontrada"},
}


@router.post(
    "/operaciones",
    status_code=201,
    response_model=OperacionDetalle,
    response_model_exclude_none=True,
    responses={409: {"model": ErrorSalida, "description": "No quedan IDs disponibles"}},
    summary="Generar una operación simulada de un caso",
)
def generar_operacion(
    pedido: PedidoGeneracion, repositorio: RepositorioDep, reloj: RelojDep
) -> OperacionDetalle:
    """Toma el siguiente ID libre (FR-003). Si sería OP-9000 responde 409 y no crea nada (FR-032)."""
    ahora = reloj()
    try:
        op = repositorio.crear(lambda id_operacion: generar(pedido.caso, id_operacion, ahora))
    except IdsAgotados:
        raise ErrorPayTrace(409, "No quedan IDs disponibles para generar operaciones") from None
    return detalle_de(op)


@router.get(
    "/operaciones",
    response_model=list[OperacionResumen],
    summary="Listar las operaciones con su estado",
)
def listar_operaciones(repositorio: RepositorioDep) -> list[OperacionResumen]:
    """Fijas y generadas, por ID ascendente (FR-013)."""
    return [OperacionResumen(id=op.id, estado=op.estado) for op in repositorio.listar()]


@router.get(
    "/busqueda",
    response_model=OperacionDetalle,
    response_model_exclude_none=True,
    responses=ERRORES_DE_ID,
    summary="Buscar una operación por ID",
)
def buscar_operacion(repositorio: RepositorioDep, id: str | None = None) -> OperacionDetalle:
    """Sin `id` o con `id` vacío responde 400, igual que con un formato inválido (FR-012)."""
    return detalle_de(operacion_o_error(id, repositorio))


@router.get(
    "/operaciones/{id}",
    response_model=OperacionDetalle,
    response_model_exclude_none=True,
    responses=ERRORES_DE_ID,
    summary="Abrir una operación con su trace",
)
def abrir_operacion(id: str, repositorio: RepositorioDep) -> OperacionDetalle:
    return detalle_de(operacion_o_error(id, repositorio))


def _a_salida(resultado: Resultado) -> DiagnosticoSalida | SinFalloSalida | EnCursoSalida:
    match resultado:
        case Diagnostico(
            causa=causa,
            eventos_citados=citados,
            recomendacion=recomendacion,
            evidencia_recomendacion=evidencia,
        ):
            return DiagnosticoSalida(
                causa=causa,
                eventos_citados=list(citados),
                recomendacion=recomendacion,
                evidencia_recomendacion=list(evidencia),
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
