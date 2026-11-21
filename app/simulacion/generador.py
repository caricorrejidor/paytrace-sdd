"""Generador de operaciones simuladas por caso (spec Historia 4, FR-001 a FR-004; research R8).

Función pura: no lee el reloj ni usa azar. La misma entrada da siempre la misma operación.
"""

from datetime import datetime, timedelta

from app.dominio import (
    EMISOR_POR_TIPO,
    Caso,
    CodigoMotivo,
    Estado,
    Evento,
    Operacion,
    TipoEvento,
)

T = TipoEvento
C = CodigoMotivo

# Tabla de casos del spec: estado y secuencia de (tipo, código) del trace.
_SECUENCIAS: dict[Caso, tuple[Estado, tuple[tuple[TipoEvento, CodigoMotivo | None], ...]]] = {
    Caso.OK: (
        Estado.OK,
        (
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.ACEPTACION_PROVEEDOR, None),
            (T.ACREDITACION_DESTINO, None),
        ),
    ),
    Caso.FONDOS_INSUFICIENTES: (
        Estado.FALLIDA,
        ((T.ORDEN_ENVIADA, None), (T.RECHAZO_ORIGEN, C.AM04)),
    ),
    Caso.CUENTA_INCORRECTA: (
        Estado.FALLIDA,
        (
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.RECHAZO_BANCO_DESTINO, C.AC01),
            (T.REVERSA_DEBITO, None),
        ),
    ),
    Caso.TIMEOUT_CON_REVERSA: (
        Estado.FALLIDA,
        (
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.ENVIO_PROVEEDOR, None),
            (T.RECHAZO_TIMEOUT, C.AB05),
            (T.REVERSA_DEBITO, None),
        ),
    ),
    Caso.TIMEOUT_SIN_REVERSA: (
        Estado.FALLIDA,
        (
            (T.ORDEN_ENVIADA, None),
            (T.DEBITO_ORIGEN, None),
            (T.ENVIO_PROVEEDOR, None),
            (T.RECHAZO_TIMEOUT, C.AB05),
        ),
    ),
    Caso.TRACE_INCOMPLETO: (
        Estado.PENDIENTE,
        ((T.ORDEN_ENVIADA, None), (T.DEBITO_ORIGEN, None)),
    ),
}

_SEPARACION = timedelta(seconds=1)

# FR-004: el trace incompleto termina MÁS de 10 minutos antes de la generación (con 10 justos
# quedaría "en curso").
_ATRASO_TRACE_INCOMPLETO = timedelta(minutes=11)


def generar(caso: Caso, id_operacion: str, ahora: datetime) -> Operacion:
    estado, secuencia = _SECUENCIAS[caso]
    ultimo = ahora.replace(microsecond=0)
    if caso is Caso.TRACE_INCOMPLETO:
        ultimo -= _ATRASO_TRACE_INCOMPLETO
    primero = ultimo - _SEPARACION * (len(secuencia) - 1)

    eventos = tuple(
        Evento(
            id=f"{id_operacion}-E{n}",
            momento=primero + _SEPARACION * (n - 1),
            tipo=tipo,
            emisor=EMISOR_POR_TIPO[tipo],
            codigo=codigo,
        )
        for n, (tipo, codigo) in enumerate(secuencia, start=1)
    )
    return Operacion(
        id=id_operacion,
        estado=estado,
        eventos=eventos,
        caso=caso,
        hora_referencia=None,
        origen="generada",
    )
