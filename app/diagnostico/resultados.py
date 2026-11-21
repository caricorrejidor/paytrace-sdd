"""Resultados posibles de un pedido de diagnóstico (data-model.md, Resultado del diagnóstico)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostico:
    """Causa, eventos citados por ID y recomendación (FR-017)."""

    causa: str
    eventos_citados: tuple[str, ...]
    recomendacion: str


@dataclass(frozen=True)
class SinFallo:
    """Operación OK: no se diagnostica (FR-023)."""

    mensaje: str


@dataclass(frozen=True)
class EnCurso:
    """Pendiente dentro del plazo de espera (FR-024)."""

    mensaje: str


Resultado = Diagnostico | SinFallo | EnCurso
