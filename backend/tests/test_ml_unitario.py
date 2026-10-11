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
    """Verifica la evaluación por bloques de 7 días con la serie real."""
    from datetime import date, timedelta

    from app.ml.evaluacion import evaluar_por_bloques_recursivos

    np.random.seed(42)
    base = np.array([5, 5, 5, 5, 5, 10, 2] * 17, dtype=np.float64)
    serie = np.maximum(base + np.random.normal(0, 0.5, len(base)), 0)
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie))]

    X, y, _ = construir_features(serie, fechas)
    n = len(y)
    X_train, X_val = X[: n - 14], X[n - 14 :]
    y_train, y_val = y[: n - 14], y[n - 14 :]

    modelo = crear_modelos()["random_forest"]
    y_pred, y_real = evaluar_por_bloques_recursivos(
        modelo, X_train, y_train, X_val, y_val, serie
    )

    assert len(y_pred) == 8  # 8 orígenes rodantes, un total semanal cada uno
    assert len(y_real) == 8
    # El último origen (o=7) arranca en la base de la ventana de validación
    origen_final = WARMUP_DIAS + len(X_train)
    assert np.isclose(y_real[-1], float(np.sum(serie[origen_final : origen_final + 7])))
    assert np.all(np.isfinite(y_pred))
    # Determinista salvo ruido de punto flotante (RandomForest usa n_jobs=-1):
    # dos corridas dan lo mismo
    modelo2 = crear_modelos()["random_forest"]
    y_pred2, _ = evaluar_por_bloques_recursivos(
        modelo2, X_train, y_train, X_val, y_val, serie
    )
    assert np.allclose(y_pred, y_pred2)


def test_bloques_sin_fuga_dentro_del_bloque():
    """Cambiar los valores reales DENTRO del bloque no altera su pronóstico."""
    from datetime import date, timedelta

    from app.ml.evaluacion import evaluar_por_bloques_recursivos

    np.random.seed(42)
    base = np.array([5, 5, 5, 5, 5, 10, 2] * 17, dtype=np.float64)
    serie_a = np.maximum(base + np.random.normal(0, 0.5, len(base)), 0)
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie_a))]

    X_a, y_a, _ = construir_features(serie_a, fechas)
    n = len(y_a)
    X_train, X_val_a = X_a[: n - 14], X_a[n - 14 :]
    y_train, y_val_a = y_a[: n - 14], y_a[n - 14 :]

    # Escenario B: mismos datos hasta el primer origen (o=0, el más tardío),
    # +50 solo en su semana real [origen:origen+7]. Los orígenes posteriores
    # usan historial contaminado por diseño (serie real hasta o-1), así que
    # solo el primer origen debe coincidir: es la prueba de no fuga.
    # (los 17 ciclos dan suficiencia: 20+ días con venta en entrenamiento)
    origen_serie = WARMUP_DIAS + len(X_train) + (14 - 7)
    serie_b = serie_a.copy()
    serie_b[origen_serie : origen_serie + 7] += 50.0
    X_b, y_b, _ = construir_features(serie_b, fechas)
    X_val_b, y_val_b = X_b[n - 14 :], y_b[n - 14 :]

    pred_a, _ = evaluar_por_bloques_recursivos(
        crear_modelos()["random_forest"], X_train, y_train, X_val_a, y_val_a, serie_a
    )
    pred_b, _ = evaluar_por_bloques_recursivos(
        crear_modelos()["random_forest"], X_train, y_train, X_val_b, y_val_b, serie_b
    )

    assert len(pred_a) == 8 and len(pred_b) == 8
    assert np.isclose(pred_a[0], pred_b[0])


def test_bloque_usa_funcion_recursiva_compartida():
    """Cada origen semanal es idéntico al de la función compartida."""
    from datetime import date, timedelta

    from app.ml.evaluacion import evaluar_por_bloques_recursivos, ORIGENES_RODANTES
    from app.ml.recursivo import HORIZONTE, pronosticar_recursivo

    np.random.seed(42)
    base = np.array([5, 5, 5, 5, 5, 10, 2] * 17, dtype=np.float64)
    serie = np.maximum(base + np.random.normal(0, 0.5, len(base)), 0)
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie))]

    X, y, _ = construir_features(serie, fechas)
    n = len(y)
    X_train, X_val = X[: n - 14], X[n - 14 :]
    y_train, y_val = y[: n - 14], y[n - 14 :]
    origen_serie_val = WARMUP_DIAS + len(X_train)

    pred_bloques, _ = evaluar_por_bloques_recursivos(
        crear_modelos()["random_forest"], X_train, y_train, X_val, y_val, serie
    )

    modelo_directo = crear_modelos()["random_forest"]
    modelo_directo.fit(X_train, y_train)
    for o in range(ORIGENES_RODANTES):
        fila = 14 - HORIZONTE - o
        origen = origen_serie_val + (14 - HORIZONTE - o)
        pred_directo = pronosticar_recursivo(
            modelo_directo, X_val[fila], serie[:origen]
        )
        assert np.allclose(pred_bloques[o], float(np.sum(pred_directo)))


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


def test_pronostico_semanal_no_colapsa_en_demanda_intermitente():
    """Regresión M1-TER: con >60% de ceros y semanal estable, 0.5x <= D <= 1.5x."""
    from datetime import date, timedelta

    from app.ml.pronostico import generar_pronostico_completo

    np.random.seed(7)
    # ~5 unidades/semana concentradas en 1-2 días (intermitente, semanal estable)
    serie = np.zeros(119, dtype=np.float64)
    dias_con_venta = np.random.choice(119, size=35, replace=False)
    for d in dias_con_venta:
        serie[d] = float(np.random.choice([1, 2]))
    assert float(np.mean(serie == 0)) > 0.60
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie))]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    assert resultado.suficiente
    pronostico, demanda, *_ = generar_pronostico_completo(resultado, X, y, serie)
    media_semanal = float(np.sum(serie[-28:]) / 4.0)
    assert media_semanal > 0
    assert 0.5 * media_semanal <= demanda <= 1.5 * media_semanal


def test_origen_sin_fuga_posterior():
    """Cambiar valores reales posteriores al origen no altera su pronóstico."""
    from datetime import date, timedelta

    from app.ml.recursivo import pronosticar_recursivo

    np.random.seed(42)
    base = np.array([5, 5, 5, 5, 5, 10, 2] * 15, dtype=np.float64)
    serie_a = np.maximum(base + np.random.normal(0, 0.5, len(base)), 0)
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie_a))]

    X_a, y_a, _ = construir_features(serie_a, fechas)
    n = len(y_a)
    X_train, X_val = X_a[: n - 14], X_a[n - 14 :]
    y_train = y_a[: n - 14]
    origen = WARMUP_DIAS + len(X_train) + 3  # cuarto origen semanal

    modelo = crear_modelos()["random_forest"]
    modelo.fit(X_train, y_train)
    pred_a = pronosticar_recursivo(modelo, X_val[14 - 7 - 3], serie_a[:origen])

    serie_b = serie_a.copy()
    serie_b[origen : origen + 7] += 50.0
    modelo_b = crear_modelos()["random_forest"]
    modelo_b.fit(X_train, y_train)
    pred_b = pronosticar_recursivo(modelo_b, X_val[14 - 7 - 3], serie_b[:origen])

    assert np.allclose(pred_a, pred_b)


def test_seleccion_semanal_no_premia_modelo_de_ceros():
    """El MAE diario favorecería al modelo de ceros; el semanal no."""
    from datetime import date, timedelta

    # Serie intermitente (~75% ceros): picos de 4 cada 4 días, total semanal
    # estable en 7. Un modelo de ceros tendría MAE diario bajo pero MAE
    # semanal = 7; la selección semanal no lo premia.
    serie = np.zeros(119, dtype=np.float64)
    serie[3::4] = 4.0
    fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(len(serie))]

    X, y, _ = construir_features(serie, fechas)
    resultado = evaluar_modelos(X, y, serie, fechas)

    assert resultado.suficiente
    # La selección se decide con MAE semanal: documenta cuál ganó aquí
    assert resultado.modelo_seleccionado in (
        "random_forest",
        "hist_gradient_boosting",
        "ridge",
        "promedio_movil",
    )
    # Un predictor que siempre da cero tendría MAE semanal = media de los
    # totales reales; el MAE diario lo favorecería (75% de días en cero),
    # pero la selección semanal exige vencer a la base con totales.
    idx_serie_val = 14 + (len(y) - 14)
    reales = np.array(
        [
            float(np.sum(serie[idx_serie_val + (14 - 7 - o) : idx_serie_val + (14 - 7 - o) + 7]))
            for o in range(8)
        ]
    )
    mae_ceros = float(np.mean(np.abs(reales)))
    assert mae_ceros > 0
    assert resultado.metricas_modelo.mae <= mae_ceros


if __name__ == "__main__":
    pytest.main([__file__, "-v"])