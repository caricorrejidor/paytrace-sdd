"""Repositorio de operaciones en memoria (data-model.md). Se pierde al reiniciar (FR-009)."""

import threading
from collections.abc import Callable, Iterable

from app.dominio import Operacion

# OP-9xxx nunca se usa (FR-002): el último número asignable es 8999.
_ULTIMO_NUMERO = 8999


class IdsAgotados(Exception):
    """El siguiente ID según FR-003 sería OP-9000 (FR-032)."""


class Repositorio:
    def __init__(self, operaciones: Iterable[Operacion]) -> None:
        self._operaciones: dict[str, Operacion] = {}
        # FastAPI corre los endpoints síncronos en un pool de hilos: la reserva del ID y la
        # inserción van bajo el mismo lock (research R9).
        self._lock = threading.Lock()
        for op in operaciones:
            if op.id in self._operaciones:
                raise ValueError(f"ID de operación repetido: {op.id}")
            self._operaciones[op.id] = op

    def obtener(self, id_operacion: str) -> Operacion | None:
        return self._operaciones.get(id_operacion)

    def cantidad(self) -> int:
        return len(self._operaciones)

    def agregar(self, operacion: Operacion) -> None:
        with self._lock:
            self._agregar(operacion)

    def siguiente_id(self) -> str:
        """El número siguiente al mayor existente, sin reutilizar huecos (FR-003)."""
        with self._lock:
            return self._siguiente_id()

    def crear(self, construir: Callable[[str], Operacion]) -> Operacion:
        """Reserva el siguiente ID, construye la operación con él y la agrega, todo de forma atómica.

        Si no quedan IDs lanza `IdsAgotados` sin llamar a `construir` ni agregar nada (FR-032).
        """
        with self._lock:
            operacion = construir(self._siguiente_id())
            self._agregar(operacion)
            return operacion

    def _siguiente_id(self) -> str:
        mayor = max((int(i.removeprefix("OP-")) for i in self._operaciones), default=0)
        if mayor >= _ULTIMO_NUMERO:
            raise IdsAgotados
        return f"OP-{mayor + 1:04d}"

    def _agregar(self, operacion: Operacion) -> None:
        if operacion.id in self._operaciones:
            raise ValueError(f"Ya existe la operación {operacion.id}")
        self._operaciones[operacion.id] = operacion
