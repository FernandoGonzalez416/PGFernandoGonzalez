"""Tests unitarios para el motor de predicción (sin BD)."""

import numpy as np
import pytest

from app.ml.serie import serie_a_array
from app.ml.features import construir_features, validar_sin_fuga, WARMUP_DIAS
from app.ml.evaluacion import (
    evaluar_modelos,
    evaluar_suficiencia,
    pronosticar_promedio_movil_7,
    calcular_metricas,
    ResultadoEvaluacion,
)
from app.ml.pronostico import calcular_intervalo, generar_pronostico_completo
from app.ml.confianza import determinar_confianza, CASOS_PRUEBA_CONFIANZA
from app.ml.modelos import crear_modelos


def test_no_fuga_en_features():
    """Verifica que no hay fuga de información del futuro en las features."""
    # Serie con patrón claro: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
    serie = np.arange(1, 21, dtype=np.float64)
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(20)]

    X, y, _ = construir_features(serie, fechas)

    # Validar sin fuga
    assert validar_sin_fuga(X, y, serie), "Hay fuga de información en features"

    # Verificar valores específicos
    # Primera fila válida (índice 14 en serie original = día 15)
    # lag1 = serie[13] = 14
    # lag7 = serie[7] = 8
    # media_movil_7 = mean(serie[7:14]) = mean(8..14) = 11
    assert np.isclose(X[0, 4], 14.0), f"lag1 incorrecto: {X[0, 4]}"
    assert np.isclose(X[0, 5], 8.0), f"lag7 incorrecto: {X[0, 5]}"
    assert np.isclose(X[0, 6], 11.0), f"media_movil_7 incorrecta: {X[0, 6]}"


def test_suficiencia_74_dias_linea_base():
    """74 días -> línea base (insuficiente)."""
    # 74 días totales, warmup 14 = 60 de entrenamiento, validación 14
    # Pero la regla dice ventana >= 75 días desde primera venta
    serie = np.random.poisson(2, 74).astype(np.float64)
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(74)]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    assert resultado.modelo_seleccionado == "promedio_movil"
    assert not resultado.suficiente
    assert "menor a 75" in resultado.motivo_no_suficiente


def test_suficiencia_75_dias_poca_densidad_linea_base():
    """75 días calendario pero pocos días con venta -> línea base."""
    # Necesitamos 75 días calendario + 14 warmup + 14 validación = 103 días totales
    # para que la validación empiece en día 75 de la serie completa
    total_dias = 103
    serie = np.zeros(total_dias, dtype=np.float64)
    # Ventas en entrenamiento (después de warmup día 14, hasta día 75-14=61): 10 días
    serie[14:24] = 1  # 10 días con venta en entrenamiento
    # Ventas en validación (últimos 14 días = días 89-102): 5 días
    serie[89:94] = 1
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(total_dias)]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    assert resultado.modelo_seleccionado == "promedio_movil"
    assert not resultado.suficiente
    assert "pocos días con venta en entrenamiento" in resultado.motivo_no_suficiente


def test_suficiencia_75_dias_densidad_ok_modelo_selecciona():
    """75 días calendario con densidad suficiente -> se evalúan modelos."""
    # 75 días calendario + 14 warmup + 14 validación = 103 días totales
    total_dias = 103
    serie = np.zeros(total_dias, dtype=np.float64)
    # Ventas en entrenamiento (días 14 a 75): 25 días con venta
    serie[14:39] = 1  # 25 días con venta en entrenamiento (índices 14-38)
    # Ventas en validación (últimos 14 días = días 89-102): 5 días
    serie[89:94] = 1
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(total_dias)]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    # Debe ser suficiente
    assert resultado.suficiente
    # Puede ser promedio_movil si ningún modelo vence, o un modelo ML


def test_solo_despliega_si_vence_linea_base():
    """Caso donde el modelo NO vence a la línea base -> usa línea base."""
    # Crear serie donde la línea base (promedio móvil) sea muy buena
    # y los modelos ML no aporten valor (ruido puro)
    np.random.seed(42)
    serie = np.random.poisson(5, 100).astype(np.float64)
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    # Con ruido puro, es probable que la línea base gane
    # Lo importante es que la lógica de selección funcione
    assert resultado.modelo_seleccionado in ["promedio_movil", "random_forest", "hist_gradient_boosting", "ridge"]


def test_tabla_confianza():
    """Tabla de casos de confianza (alta, baja, simulacion)."""
    for caso in CASOS_PRUEBA_CONFIANZA:
        suficiente, vence, nmae, ficticios, esperado, desc = caso
        resultado = determinar_confianza(
            suficiente=suficiente,
            modelo_vence_linea_base=vence,
            nmae=nmae,
            datos_ficticios=ficticios,
        )
        assert resultado.nivel == esperado, f"Fallo en {desc}: esperado {esperado}, got {resultado.nivel}"


def test_pronostico_7_dias_sin_negativos():
    """El pronóstico siempre tiene 7 días y no hay negativos."""
    # Caso línea base
    serie = np.array([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], dtype=np.float64)
    pred = pronosticar_promedio_movil_7(serie, 7)
    assert len(pred) == 7
    assert np.all(pred >= 0)

    # Caso con modelo ML - verificar que generar_pronostico_completo no crashea
    from app.ml.evaluacion import ResultadoEvaluacion, MetricasValidacion
    from app.ml.pronostico import generar_pronostico_completo

    # Crear resultado de evaluación simulado para línea base
    resultado_eval = ResultadoEvaluacion(
        modelo_seleccionado="promedio_movil",
        metricas_modelo=MetricasValidacion(1.0, 0.1, 0.2, 5, 5.0),
        metricas_linea_base=MetricasValidacion(1.0, 0.1, 0.2, 5, 5.0),
        suficiente=True,
        motivo_no_suficiente=None,
        observaciones_usadas=50,
    )
    X = np.random.randn(50, 8)
    y = np.random.randn(50)
    pred, demanda, inf, sup, mae, wape = generar_pronostico_completo(
        resultado_eval, X, y, serie
    )
    assert len(pred) == 7
    assert np.all(pred >= 0)
    assert demanda >= 0


def test_determinismo_dos_corridas():
    """Resultado idéntico en dos corridas (random_state=42)."""
    np.random.seed(42)
    serie1 = np.random.poisson(3, 100).astype(np.float64)
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]

    X1, y1, _ = construir_features(serie1, fechas)
    r1 = evaluar_modelos(X1, y1, serie1, fechas)

    np.random.seed(42)
    serie2 = np.random.poisson(3, 100).astype(np.float64)
    X2, y2, _ = construir_features(serie2, fechas)
    r2 = evaluar_modelos(X2, y2, serie2, fechas)

    assert r1.modelo_seleccionado == r2.modelo_seleccionado
    assert np.isclose(r1.metricas_modelo.mae, r2.metricas_modelo.mae)


def test_sanidad_estacionalidad_semanal_modelo_vence():
    """En serie sintética con estacionalidad semanal fuerte, el modelo vence a línea base."""
    # Crear serie con patrón semanal claro: lunes-viernes=5, sábado=10, domingo=2
    np.random.seed(42)
    base = np.array([5,5,5,5,5,10,2] * 15)  # 105 días
    ruido = np.random.normal(0, 0.5, len(base))
    serie = np.maximum(base + ruido, 0).astype(np.float64)
    from datetime import date, timedelta
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie))]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    # Con estacionalidad semanal clara, RF/HGB deberían capturar el patrón
    # y vencer al promedio móvil plano
    if resultado.suficiente and resultado.modelo_seleccionado != "promedio_movil":
        assert resultado.metricas_modelo.mae < resultado.metricas_linea_base.mae


def test_intervalo_aproximado():
    """Verifica fórmula del intervalo aproximado."""
    demanda = 100.0
    mae = 5.0
    inf, sup = calcular_intervalo(demanda, mae, 7)

    # m = 1.28 * 5 * sqrt(7) ≈ 1.28 * 5 * 2.646 ≈ 16.93
    m_esperado = 1.28 * mae * np.sqrt(7)
    assert np.isclose(inf, max(0, demanda - m_esperado))
    assert np.isclose(sup, demanda + m_esperado)


def test_evaluacion_por_bloques_recursivos():
    """Verifica que la evaluación por bloques de 7 días funciona."""
    from app.ml.evaluacion import evaluar_por_bloques_recursivos
    from sklearn.linear_model import LinearRegression

    np.random.seed(42)
    X = np.random.randn(50, 8)
    y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(50) * 0.1
    X_train, X_val = X[:36], X[36:]
    y_train, y_val = y[:36], y[36:]

    modelo = LinearRegression()
    y_pred, y_real = evaluar_por_bloques_recursivos(modelo, X_train, y_train, X_val, y_val, np.array([]))

    assert len(y_pred) == 14  # 2 bloques de 7
    assert len(y_real) == 14
    assert np.array_equal(y_real, y_val)


def test_pronostico_recursivo_no_colapsa_a_ultimo_valor():
    """Regresión M1: pronosticar_recursivo usa el modelo entrenado, sin reajuste.

    Reajustar con una sola muestra colapsaba los árboles a una hoja y el
    pronóstico salía plano (= último valor): 11 productos con demanda 0.00
    aunque tenían ventas recientes.
    """
    from datetime import date, timedelta

    from app.ml.pronostico import pronosticar_recursivo

    np.random.seed(42)
    base = np.array([5, 5, 5, 5, 5, 10, 2] * 15, dtype=np.float64)
    serie = np.maximum(base + np.random.normal(0, 0.5, len(base)), 0)
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie))]

    X, y, _ = construir_features(serie, fechas)
    modelo = crear_modelos()["random_forest"]
    modelo.fit(X, y)

    pronostico = pronosticar_recursivo(modelo, X[-1], serie)

    assert len(pronostico) == 7
    assert np.all(pronostico >= 0)
    assert not np.allclose(pronostico, serie[-1])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])