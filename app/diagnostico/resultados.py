"""Resultados posibles de un pedido de diagnóstico (data-model.md, Resultado del diagnóstico)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostico:
    """Causa, eventos citados por ID, recomendación (001/FR-017) y evidencia de la recomendación
    por ID (002/FR-001). La evidencia no tiene valor por defecto: cada regla la decide."""

    causa: str
    eventos_citados: tuple[str, ...]
    recomendacion: str
    evidencia_recomendacion: tuple[str, ...]


@dataclass(frozen=True)
class SinFallo:
    """Operación OK: no se diagnostica (FR-023)."""

    mensaje: str


@dataclass(frozen=True)
class EnCurso:
    """Pendiente dentro del plazo de espera (FR-024)."""

    mensaje: str


Resultado = Diagnostico | SinFallo | EnCurso
