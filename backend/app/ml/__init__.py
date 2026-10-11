"""Módulo ML: Motor de predicción de demanda (P3/P3a/P13)."""

from .serie import obtener_serie_diaria, serie_a_array
from .features import construir_features, validar_sin_fuga, WARMUP_DIAS
from .modelos import crear_modelos, nombre_metodo_clave_a_bd
from .evaluacion import (
    evaluar_modelos,
    ResultadoEvaluacion,
    MetricasValidacion,
    VENTANA_MINIMA_DIAS,
    DIAS_CON_VENTA_ENTRENAMIENTO_MIN,
    DIAS_CON_VENTA_VALIDACION_MIN,
    VALIDACION_DIAS,
)
from .pronostico import generar_pronostico_completo, calcular_intervalo, HORIZONTE
from .confianza import determinar_confianza, ResultadoConfianza, NivelConfianza

__all__ = [
    "obtener_serie_diaria",
    "serie_a_array",
    "construir_features",
    "validar_sin_fuga",
    "WARMUP_DIAS",
    "crear_modelos",
    "nombre_metodo_clave_a_bd",
    "evaluar_modelos",
    "ResultadoEvaluacion",
    "MetricasValidacion",
    "VENTANA_MINIMA_DIAS",
    "DIAS_CON_VENTA_ENTRENAMIENTO_MIN",
    "DIAS_CON_VENTA_VALIDACION_MIN",
    "VALIDACION_DIAS",
    "generar_pronostico_completo",
    "calcular_intervalo",
    "HORIZONTE",
    "determinar_confianza",
    "ResultadoConfianza",
    "NivelConfianza",
]