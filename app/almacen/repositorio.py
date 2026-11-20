"""Repositorio de operaciones en memoria (data-model.md). Se pierde al reiniciar (FR-009)."""

from collections.abc import Iterable

from app.dominio import Operacion


class Repositorio:
    def __init__(self, operaciones: Iterable[Operacion]) -> None:
        self._operaciones: dict[str, Operacion] = {}
        for op in operaciones:
            if op.id in self._operaciones:
                raise ValueError(f"ID de operación repetido: {op.id}")
            self._operaciones[op.id] = op

    def obtener(self, id_operacion: str) -> Operacion | None:
        return self._operaciones.get(id_operacion)

    def cantidad(self) -> int:
        return len(self._operaciones)

    def agregar(self, operacion: Operacion) -> None:
        if operacion.id in self._operaciones:
            raise ValueError(f"Ya existe la operación {operacion.id}")
        self._operaciones[operacion.id] = operacion
