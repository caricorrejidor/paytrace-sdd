"""Modelos Pydantic de request y response de la API (contracts/api.md)."""

from typing import Literal

from pydantic import BaseModel


class DiagnosticoSalida(BaseModel):
    tipo: Literal["diagnostico"] = "diagnostico"
    causa: str
    eventos_citados: list[str]
    recomendacion: str


class ErrorSalida(BaseModel):
    detalle: str
