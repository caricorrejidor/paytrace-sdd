"""Dependencias de la capa API: errores de ID, repositorio y reloj (research R5, contracts/api.md)."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from fastapi import Request

from app.almacen.repositorio import Repositorio
from app.dominio import Operacion, es_id_valido

MENSAJE_ID_INVALIDO = "Ingresá un ID con formato OP-0000"
MENSAJE_NO_ENCONTRADA = "Operación no encontrada"


class ErrorPayTrace(Exception):
    """Error que la API responde como {"detalle": ...} con su status."""

    def __init__(self, status: int, detalle: str) -> None:
        super().__init__(detalle)
        self.status = status
        self.detalle = detalle


class _ConObtener(Protocol):
    def obtener(self, id_operacion: str) -> Operacion | None: ...


def operacion_o_error(texto: str | None, repositorio: _ConObtener) -> Operacion:
    """Valida el formato antes de buscar: un ID inválido nunca llega al repositorio (FR-012)."""
    if texto is None or not es_id_valido(texto):
        raise ErrorPayTrace(400, MENSAJE_ID_INVALIDO)
    operacion = repositorio.obtener(texto)
    if operacion is None:
        raise ErrorPayTrace(404, MENSAJE_NO_ENCONTRADA)
    return operacion


def obtener_repositorio(request: Request) -> Repositorio:
    return request.app.state.repositorio


def obtener_reloj() -> Callable[[], datetime]:
    """Único lugar de la app que lee el reloj. Los tests lo reemplazan con dependency_overrides."""
    return lambda: datetime.now(UTC)
