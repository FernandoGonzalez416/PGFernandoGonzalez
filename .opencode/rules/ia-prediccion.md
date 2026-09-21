# Reglas de inteligencia artificial / predicción de demanda

La predicción de demanda forma parte del proyecto y usa **Scikit-learn** según la tesis. La **estrategia está aprobada** en `DECISIONES.md` (P3/P3a/P13). **No implementar el modelo** (código, dependencias, job) **hasta que se autorice el desarrollo**.

## Lo que está confirmado por la tesis

- **Job programado** diario (el disparador puede ser diario o al cierre de ventas del día).
- **Datos de entrada mínimos**: historial de ventas por producto, inventario actual y estacionalidad conocida.
- **Regla de negocio**: si no hay suficiente historial, se aplica un método simple (promedio móvil) y el pronóstico se marca como **baja confianza**.
- **Salidas**: pronóstico con intervalo/confianza, sugerencia de compra (demanda pronosticada vs stock proyectado) y notificación al responsable.
- La presentación al usuario debe ser en lenguaje llano (sin terminología estadística), con gráfico de tendencia simple por producto.

## Estrategia aprobada (P3/P3a/P13 — APROBADO)

- **Línea base/respaldo**: promedio móvil simple (últimas 7 observaciones) con etiqueta "baja confianza".
- **Modelo principal**: Random Forest Regressor con características (día de semana, mes, fin de semana, tendencia, rezagos t-1 y t-7, media/desviación móvil de 7 días). Horizonte: próxima semana.
- **Candidatos de contraste** (mismo harness de validación): HistGradientBoostingRegressor (regularización y pérdida quantile para intervalo de confianza) y Ridge.
- **Selección**: en validación temporal se usa el candidato de menor MAE, y solo se despliega si supera al promedio móvil de 7 días; si no, línea base.
- **Criterio de suficiencia de datos** (P13, ver `DECISIONES.md`): ventana ≥ 75 días desde la primera venta Y densidad ≥ 20 días con venta > 0 en entrenamiento y ≥ 3 en validación (ambos umbrales configurables; se calibrarán con el piloto).
- **Validación**: división temporal secuencial (últimos 14 días); walk-forward cuando haya ≥ 12 meses de historial.
- **Métricas**: MAE (principal), MAPE/WAPE solo con ventas > 0 ("precisión ≈ 100 − MAPE").
- **Confianza alta** por **evidencia** (P13, se eliminó el umbral «MAE ≤ 30 %» que era arbitrario): solo si pasó el criterio, venció a la línea base en validación, `nMAE < 100 %` (error medio ≤ demanda media diaria; cota de cordura) y se entrenó con datos reales del piloto (los ficticios siempre se marcan "simulación"). El pronóstico siempre reporta su error esperado (MAE/WAPE/nMAE).
- No implementar el modelo ni instalar dependencias hasta que se autorice el desarrollo.

## Reglas fundamentales

- **No inventar** modelos de machine learning, variables, métricas ni datos de entrenamiento.
- **No afirmar que un modelo funciona correctamente sin pruebas** reales.
- **No presentar resultados ficticios como resultados reales**.
- Cualquier resultado producido con **datos ficticios** debe identificarse claramente como simulación/prueba.

## Trabajo con datos (P4)

- Durante desarrollo inicial se usan **datos ficticios identificados como datos de prueba** (para construir, probar y validar).
- En el piloto se registran **ventas reales desde el inicio**; no asumir historial digital previo ni inventar historial real del negocio.
- La predicción se adapta progresivamente a la cantidad de datos disponibles.
- Documentar variables, supuestos, métricas de error y confianza de cada pronóstico.
- Si faltan datos o decisiones para la predicción, **marcarlo como pendiente** en lugar de inventar.

## Integración

- Orquestar la ejecución del job desde el backend y persistir predicciones, sugerencias y notificaciones (entidades Predicción, Sugerencia, Notificación de la tesis).
- Mantener la lógica de IA desacoplada de la UI web.