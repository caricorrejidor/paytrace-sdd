"""Tipos de dominio de PayTrace (data-model.md). Solo biblioteca estándar."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal


class Estado(StrEnum):
    OK = "ok"
    FALLIDA = "fallida"
    PENDIENTE = "pendiente"


class Emisor(StrEnum):
    ORIGEN = "origen"
    PROVEEDOR = "proveedor"
    BANCO_DESTINO = "banco_destino"


class CodigoMotivo(StrEnum):
    AM04 = "AM04"
    AC01 = "AC01"
    AB05 = "AB05"


class TipoEvento(StrEnum):
    ORDEN_ENVIADA = "orden_enviada"
    DEBITO_ORIGEN = "debito_origen"
    ENVIO_PROVEEDOR = "envio_proveedor"
    ACEPTACION_PROVEEDOR = "aceptacion_proveedor"
    ACREDITACION_DESTINO = "acreditacion_destino"
    RECHAZO_ORIGEN = "rechazo_origen"
    RECHAZO_BANCO_DESTINO = "rechazo_banco_destino"
    RECHAZO_TIMEOUT = "rechazo_timeout"
    REVERSA_DEBITO = "reversa_debito"


class Caso(StrEnum):
    OK = "ok"
    FONDOS_INSUFICIENTES = "fondos_insuficientes"
    CUENTA_INCORRECTA = "cuenta_incorrecta"
    TIMEOUT_CON_REVERSA = "timeout_con_reversa"
    TIMEOUT_SIN_REVERSA = "timeout_sin_reversa"
    TRACE_INCOMPLETO = "trace_incompleto"


EMISOR_POR_TIPO: dict[TipoEvento, Emisor] = {
    TipoEvento.ORDEN_ENVIADA: Emisor.ORIGEN,
    TipoEvento.DEBITO_ORIGEN: Emisor.ORIGEN,
    TipoEvento.ENVIO_PROVEEDOR: Emisor.ORIGEN,
    TipoEvento.ACEPTACION_PROVEEDOR: Emisor.PROVEEDOR,
    TipoEvento.ACREDITACION_DESTINO: Emisor.BANCO_DESTINO,
    TipoEvento.RECHAZO_ORIGEN: Emisor.ORIGEN,
    TipoEvento.RECHAZO_BANCO_DESTINO: Emisor.BANCO_DESTINO,
    TipoEvento.RECHAZO_TIMEOUT: Emisor.PROVEEDOR,
    TipoEvento.REVERSA_DEBITO: Emisor.ORIGEN,
}

TIPOS_RECHAZO: frozenset[TipoEvento] = frozenset(
    {
        TipoEvento.RECHAZO_ORIGEN,
        TipoEvento.RECHAZO_BANCO_DESTINO,
        TipoEvento.RECHAZO_TIMEOUT,
    }
)


@dataclass(frozen=True)
class Evento:
    id: str
    momento: datetime
    tipo: TipoEvento
    emisor: Emisor
    codigo: CodigoMotivo | None


@dataclass(frozen=True)
class Operacion:
    id: str
    estado: Estado
    eventos: tuple[Evento, ...]
    caso: Caso | None
    hora_referencia: datetime | None
    origen: Literal["fija", "generada"]


# [0-9] y fullmatch, no \d ni $: \d acepta dígitos Unicode y $ acepta un "\n" final (research R10).
_PATRON_ID = re.compile(r"OP-[0-9]{4}")


def es_id_valido(texto: str) -> bool:
    return _PATRON_ID.fullmatch(texto) is not None
