"""Textos literales del spec que ve el analista (tabla de casos, FR-021 a FR-024, Clarifications)."""

# Causas (FR-018)
CAUSA_FONDOS_INSUFICIENTES = "fondos insuficientes"
CAUSA_CUENTA_INCORRECTA = "cuenta incorrecta"
CAUSA_TIMEOUT = "timeout"
CAUSA_NO_CONCLUYENTE = "no concluyente"

# Recomendaciones (tabla de casos y Clarifications)
RECOMENDACION_FONDOS_INSUFICIENTES = "Avisar al cliente que no tenía saldo. No se debitó nada"
RECOMENDACION_CUENTA_INCORRECTA = (
    "Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó"
)
RECOMENDACION_TIMEOUT_CON_REVERSA = "El débito ya se devolvió: se puede reintentar la transferencia"
RECOMENDACION_TIMEOUT_SIN_REVERSA = (
    "El débito todavía no se devolvió: pedir la reversa antes de reintentar. "
    "Si se reintenta antes, se cobra dos veces"
)
RECOMENDACION_SIN_EVENTO_CLAVE = "Pedir los logs del proveedor desde el último evento conocido"
RECOMENDACION_EVIDENCIA_CONTRADICTORIA = (
    "Evidencia contradictoria: revisar manualmente los eventos citados"
)

# Mensajes en lugar de un diagnóstico (FR-023, FR-024)
MENSAJE_SIN_FALLO = "La operación no tiene un fallo para investigar"
MENSAJE_EN_CURSO = "La operación sigue en curso"
