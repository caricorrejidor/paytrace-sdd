"""Carga y validación de los archivos de datos fijos (research R7, data-model.md Reglas de validación).

Si un archivo no cumple las reglas, se lanza ErrorDatosFijos con el archivo y la operación, y la app
no arranca.
"""

import json
from datetime import UTC
from pathlib import Path
from typing import Any, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from app.dominio import (
    EMISOR_POR_TIPO,
    TIPOS_RECHAZO,
    Caso,
    CodigoMotivo,
    Emisor,
    Estado,
    Evento,
    Operacion,
    TipoEvento,
    es_id_valido,
)


class ErrorDatosFijos(Exception):
    """Un archivo de datos fijos no cumple las reglas de validación."""


class EventoArchivo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    momento: AwareDatetime  # regla 4
    tipo: TipoEvento
    emisor: Emisor
    codigo: CodigoMotivo | None = None  # regla 5: fuera de AM04/AC01/AB05 no valida

    @model_validator(mode="after")
    def _codigo_y_emisor(self) -> Self:
        es_rechazo = self.tipo in TIPOS_RECHAZO
        if es_rechazo and self.codigo is None:  # regla 5
            raise ValueError(f"el evento {self.id} es un rechazo sin código")
        if not es_rechazo and self.codigo is not None:  # regla 5
            raise ValueError(f"el evento {self.id} no es un rechazo y tiene código")
        if EMISOR_POR_TIPO[self.tipo] is not self.emisor:  # regla 6
            raise ValueError(
                f"el evento {self.id} tiene emisor {self.emisor}, pero {self.tipo} lo emite "
                f"{EMISOR_POR_TIPO[self.tipo]}"
            )
        return self


class OperacionArchivo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    estado: Estado
    caso: Caso | None = None
    hora_referencia: AwareDatetime  # reglas 4 y 7
    eventos: list[EventoArchivo]

    @field_validator("id")
    @classmethod
    def _formato_de_id(cls, valor: str) -> str:  # regla 1
        if not es_id_valido(valor) or valor.startswith("OP-9"):
            raise ValueError("el ID no cumple OP-[0-9]{4} o es OP-9xxx")
        return valor

    @model_validator(mode="after")
    def _trace_ordenado(self) -> Self:  # regla 3
        if not self.eventos:
            raise ValueError("la operación no tiene eventos")
        for anterior, actual in zip(self.eventos, self.eventos[1:]):
            if actual.momento <= anterior.momento:
                raise ValueError(
                    f"el momento de {actual.id} no es estrictamente posterior al de {anterior.id}"
                )
        return self

    def a_dominio(self) -> Operacion:
        return Operacion(
            id=self.id,
            estado=self.estado,
            eventos=tuple(
                Evento(
                    id=e.id,
                    momento=e.momento.astimezone(UTC),
                    tipo=e.tipo,
                    emisor=e.emisor,
                    codigo=e.codigo,
                )
                for e in self.eventos
            ),
            caso=self.caso,
            hora_referencia=self.hora_referencia.astimezone(UTC),
            origen="fija",
        )


class ArchivoDatos(BaseModel):
    """Estructura externa del archivo. Cada operación se valida aparte para nombrarla en el error."""

    model_config = ConfigDict(extra="forbid")

    operaciones: list[dict[str, Any]]


def cargar_archivo(ruta: Path) -> list[Operacion]:
    nombre = Path(ruta).name
    try:
        contenido = json.loads(Path(ruta).read_text(encoding="utf-8"))
        archivo = ArchivoDatos.model_validate(contenido)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ErrorDatosFijos(f"{nombre}: no se pudo leer el archivo: {error}") from error

    operaciones = []
    for crudo in archivo.operaciones:
        try:
            operaciones.append(OperacionArchivo.model_validate(crudo).a_dominio())
        except ValidationError as error:
            raise ErrorDatosFijos(
                f"{nombre}: operación {crudo.get('id', '<sin id>')}: {error}"
            ) from error
    return operaciones


ARCHIVO_EVALUACION = "conjunto_evaluacion.json"
ARCHIVO_PLAZO = "prueba_plazo.json"
ARCHIVO_BORDE = "casos_borde.json"

# Regla 8: cantidades del spec (FR-007, FR-008, FR-029).
CANTIDADES = {ARCHIVO_EVALUACION: 25, ARCHIVO_PLAZO: 2, ARCHIVO_BORDE: 3}
POR_CASO_EN_EVALUACION = 5
CASOS_EN_EVALUACION = frozenset(Caso) - {Caso.OK}


def cargar_datos_fijos(directorio: Path) -> list[Operacion]:
    """Carga los tres archivos fijos y valida las reglas entre archivos (2 y 8)."""
    por_archivo = {nombre: cargar_archivo(Path(directorio) / nombre) for nombre in CANTIDADES}

    for nombre, operaciones in por_archivo.items():
        if len(operaciones) != CANTIDADES[nombre]:
            raise ErrorDatosFijos(
                f"{nombre}: tiene {len(operaciones)} operaciones y deben ser {CANTIDADES[nombre]}"
            )

    for caso in CASOS_EN_EVALUACION:
        cantidad = sum(op.caso is caso for op in por_archivo[ARCHIVO_EVALUACION])
        if cantidad != POR_CASO_EN_EVALUACION:
            raise ErrorDatosFijos(
                f"{ARCHIVO_EVALUACION}: tiene {cantidad} operaciones del caso {caso} y deben ser "
                f"{POR_CASO_EN_EVALUACION} (sin OK y todas con caso)"
            )

    ids_operacion: dict[str, str] = {}
    ids_evento: dict[str, str] = {}
    for nombre, operaciones in por_archivo.items():
        for op in operaciones:
            if op.id in ids_operacion:
                raise ErrorDatosFijos(
                    f"{nombre}: operación {op.id}: ID repetido (ya está en {ids_operacion[op.id]})"
                )
            ids_operacion[op.id] = nombre
            for evento in op.eventos:
                if evento.id in ids_evento:
                    raise ErrorDatosFijos(
                        f"{nombre}: operación {op.id}: ID de evento {evento.id} repetido "
                        f"(ya está en {ids_evento[evento.id]})"
                    )
                ids_evento[evento.id] = nombre

    return [op for operaciones in por_archivo.values() for op in operaciones]
