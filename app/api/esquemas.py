"""Modelos Pydantic de request y response de la API (contracts/api.md)."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.dominio import Caso, CodigoMotivo, Emisor, Estado, Operacion, TipoEvento


class PedidoGeneracion(BaseModel):
    """Cuerpo de `POST /operaciones`. Un caso fuera de la tabla o ausente da 422."""

    caso: Caso


class EventoSalida(BaseModel):
    id: str
    momento: datetime
    tipo: TipoEvento
    emisor: Emisor
    codigo: CodigoMotivo | None = None  # solo en los rechazos; las rutas excluyen los None


class OperacionResumen(BaseModel):
    """Elemento de la lista (FR-013): solo ID y estado."""

    id: str
    estado: Estado


class OperacionDetalle(BaseModel):
    """Operación con su trace del más antiguo al más nuevo (FR-014). Sin caso ni hora de referencia."""

    id: str
    estado: Estado
    eventos: list[EventoSalida]


def detalle_de(op: Operacion) -> OperacionDetalle:
    """No copia `caso`, `hora_referencia` ni `origen`, que son internos."""
    return OperacionDetalle(
        id=op.id,
        estado=op.estado,
        eventos=[
            EventoSalida(id=e.id, momento=e.momento, tipo=e.tipo, emisor=e.emisor, codigo=e.codigo)
            for e in op.eventos
        ],
    )


class DiagnosticoSalida(BaseModel):
    tipo: Literal["diagnostico"] = "diagnostico"
    causa: str
    eventos_citados: list[str]
    recomendacion: str


class SinFalloSalida(BaseModel):
    tipo: Literal["sin_fallo"] = "sin_fallo"
    mensaje: str


class EnCursoSalida(BaseModel):
    tipo: Literal["en_curso"] = "en_curso"
    mensaje: str


# Unión discriminada por `tipo`: solo `diagnostico` lleva causa, citas y recomendación (FR-023, FR-024).
DiagnosticoRespuesta = Annotated[
    DiagnosticoSalida | SinFalloSalida | EnCursoSalida, Field(discriminator="tipo")
]


class ErrorSalida(BaseModel):
    detalle: str
