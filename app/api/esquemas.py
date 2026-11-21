"""Modelos Pydantic de request y response de la API (contracts/api.md)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


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
