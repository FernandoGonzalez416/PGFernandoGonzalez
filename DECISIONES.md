# Decisiones del proyecto

Este archivo contiene **únicamente** decisiones reales: confirmadas por el usuario o pendientes de confirmación. No se rellena con información inventada.

Estado de las entradas: `APROBADO` (confirmado explícitamente), `PENDIENTE DE APROBACIÓN` (propuesto, en revisión, NO se implementa), `NO APLICA / POSPUESTO` (fuera de alcance actual).

Actualización principal: 2026-09-21 (confirmación P1–P12 y aprobación de **P3/P3a/P13, P14, P15 y P16**; P17 queda **PENDIENTE DE CONFIGURACIÓN**).

### Tabla de estado general

| # | Tema | Estado |
|---|---|---|
| P1 | Node.js serverless | APROBADO |
| P2 | Offline / sincronización | APROBADO (enfoque); implementación POSPUESTA a fase posterior |
| P3 | Modelo de predicción | APROBADO (2026-09-21) |
| P4 | Datos de predicción y desarrollo | APROBADO |
| P5 | Usuarios y roles | APROBADO; permisos APROBADOS (P14) |
| P6 | Modelo de datos | APROBADO (13 entidades; esquema P15 APROBADO) |
| P7 | Diseño web | APROBADO |
| P8 | Comprobante de venta | APROBADO (detalle del recibo se define al implementar) |
| P9 | Supabase | APROBADO; conexión MCP PENDIENTE DE CONFIGURACIÓN (P17) |
| P10 | Git | APROBADO (commit/push pendientes de orden explícita) |
| P11 | Versiones | APROBADO (proceso + propuesta P16) |
| P12 | Hosting / despliegue | NO APLICA / POSPUESTO |
| P13 | Criterio de suficiencia de datos | APROBADO (2026-09-21) |
| P14 | Matriz de permisos | APROBADO (2026-09-21, con modificación) |
| P15 | Esquema de datos detallado | APROBADO (2026-09-21, esquema inicial) |
| P16 | Versiones detalladas | APROBADO (2026-09-21; no instalar aún) |
| P17 | Supabase MCP | PENDIENTE DE CONFIGURACIÓN (solo lectura; sin conexión ni modificaciones) |

> Regla: **no se cambia una decisión a APROBADO por haberla propuesto**. Solo el usuario lo aprueba.

---

## Decisiones confirmadas

### P1. Node.js serverless — DECIDIDO: SE ADOPTA
- El proyecto utiliza **FastAPI** y **Node.js**.
- **FastAPI** sigue siendo el backend/API principal y concentra la lógica de negocio.
- **Node.js** se usa para tareas livianas/serverless **cuando corresponda**, especialmente las que tengan sentido como funciones independientes: actualizaciones o procesos puntuales, notificaciones, tareas auxiliares y otros procesos que posteriormente se determine que se benefician de serverless.
- **No trasladar lógica arbitrariamente** de FastAPI a Node.js.
- La necesidad concreta de cada función Node.js debe justificarse según el caso; **no crear funciones Node.js solo porque la tecnología está disponible**.

### P2. Offline / sincronización — DECIDIDO (enfoque iterativo)
- Para las primeras versiones **no es obligatorio** implementar toda la funcionalidad offline desde el primer momento.
- Prioridad inicial: construcción de una primera versión funcional de la plataforma web y posterior iteración.
- La arquitectura debe **evitar cerrar** la posibilidad de implementar offline/sincronización posteriormente.
- Por ahora: no implementar arquitectura offline compleja sin necesidad; no asumir IndexedDB, PWA, Service Workers u otra tecnología específica; documentar la estrategia concreta cuando llegue el momento.
- La funcionalidad offline **sigue siendo un requisito importante** de la solución final, pero **no debe bloquear** la construcción de la primera versión funcional.

### P3. Modelo de predicción — APROBADO (2026-09-21)

> Propuesta técnica **aprobada por el usuario el 2026-09-21** (selección de modelo + plan completo P3a + criterio P13). **No implementar el modelo hasta que se autorice el desarrollo** (quedan pendientes el proyecto de código, la instalación de dependencias y el job).
>
> **Revisión 2026-09-21:** el criterio anterior de confianza «MAE ≤ 30 %» era un **umbral arbitrario** y fue **eliminado**; fue sustituido en P13 por un criterio basado en evidencia (vencer a la línea base, errores reportados y error no mayor que la demanda promedio). La estrategia completa consta de este apartado (selección de modelo) + la sección **P3a** (plan completo).

#### Contexto y restricciones
- Objetivo: predecir demanda por producto para reabastecimiento.
- No existe historial digital de ventas inicial; los datos de desarrollo serán ficticios; los datos reales comenzarán a acumularse en el piloto.
- Debe ser técnicamente defendible como trabajo de graduación, razonablemente implementable y evaluable con Scikit-learn, sin complejidad innecesaria.

#### Confirma la línea base (tesis)
- **Promedio móvil simple** (media de las últimas observaciones) como línea base y respaldo para el escenario de pocos datos, con pronóstico marcado como **baja confianza**.

#### Modelo seleccionado (principal, con historial suficiente)
Regresión basada en características (*feature-based regression*) con **Random Forest Regressor** de Scikit-learn (dentro de un `Pipeline`):

- **Variable objetivo**: unidades vendidas del producto en el día `t`.
- **Características (features)**:
  - día de la semana (0–6);
  - mes;
  - fin de semana (0/1);
  - día desde el inicio del historial (tendencia);
  - rezagos: ventas de `t-1` y `t-7`;
  - media móvil de 7 días;
  - desviación estándar móvil de 7 días.
- **Horizonte de pronóstico**: próximos 7 días; la suma del periodo alimenta la sugerencia de compra.

**Razón de la elección:** con historial corto y ruidoso por producto, un árbol de regresión robusto a datos pequeños y no lineales (Random Forest) suele superar a la regresión lineal simple, no exige escalado de variables, y su implementación está totalmente dentro de Scikit-learn. La literatura reciente sobre demanda en micro y pequeñas empresas (MSE/PYME) documenta además que Random Forest funciona bien con datos escasos y con parámetros por defecto, sin tuning pesado. Se compara siempre contra la línea base; **si el modelo no supera a la línea base en validación, se usa la línea base**. Esto evita afirmar que un modelo "funciona" sin evidencia.

#### Alternativas evaluadas (mismo harness de validación)

Para que la elección sea defendible en la tesis y no dependa de una sola técnica, el motor entrena y evalúa los siguientes candidatos con las mismas features, datos y validación temporal (ver sección "P13. Criterio de suficiencia de datos"):

- **RandomForestRegressor** (propuesto como método principal): robusto a ruido y no-linealidades, sin escalado, bueno con datos pequeños; suitable para series con muchos ceros.
- **HistGradientBoostingRegressor**: cálculo más eficiente, regularización explícita y soporte de función de pérdida `quantile`, que permite generar un **intervalo de confianza** (P10-P90) sin dependencias extra — clave para el "intervalo de confianza" que pide la tesis (CU-03).
- **Ridge** (regresión lineal regularizada con features de calendario codificadas y rezagos): menor varianza en muestras muy pequeñas y más interpretable; buen contraste técnico.

Regla de selección: en validación temporal se elige el candidato con menor MAE; **solo se despliega si vence a la línea base** (promedio móvil 7 días). Random Forest se documenta como método principal; HistGB y Ridge quedan como alternativas de contraste en el mismo pipeline.

#### Cantidad mínima de historial considerada "suficiente"

Criterio revisado y detallado en la sección **"P13. Criterio de suficiencia de datos"** (propuestas nuevas). El umbral anterior de "60 observaciones" era arbitrario y se descarta. Resumen del nuevo criterio:

- **Ventana mínima**: 75 días desde la primera venta del producto (≈ 10-11 semanas).
- **Densidad mínima**: 20 días con venta > 0 en el bloque de entrenamiento y 3 días con venta > 0 en la ventana de validación.
- Ambas condiciones deben cumplirse; si no, se usa **promedio móvil de 7 días + "baja confianza"**.
- Los umbrales serán **configurables** y calibrados con los datos reales del piloto; los datos ficticios de desarrollo marcan rutina pero no confianza real.
- Con **12 meses o más** de historial se habilita la estacionalidad anual/mensual y la validación walk-forward (ver P13).

#### Métricas
- **MAE** (error absoluto medio) en unidades de producto — métrica principal, interpretable.
- **MAPE** (error porcentual absoluto medio) solo cuando las ventas reales > 0; se traduce a la "precisión" del indicador de la tesis (100 − MAPE).
- Comparación contra la **línea base (promedio móvil)** en el mismo periodo de validación: se usa el modelo solo si su error es menor.
- Registro de métricas por producto y periodo (en la entidad Predicción) para trazabilidad y defensa académica.

#### Validación
- División **temporal** (no aleatoria): últimos 14 días como ventana de validación (mínimo para cubrir un ciclo semanal) y el resto como entrenamiento; cuando el historial lo permite (~20 % del total).
- Con **12 meses o más** de historial se pasa a **walk-forward** (origen rodante, p. ej. reentrenar y evaluar cada 7 días sobre el pasado reciente) para reflejar cómo operará el job en producción.
- Criterio de activación: `MAE(candidato) < MAE(promedio móvil 7 días)` en la ventana de validación.
- Toda evaluación se registra junto al pronóstico (fecha de entrenamiento, observaciones usadas, MAE/MAPE y método seleccionado).

#### Actualización / reentrenamiento
- Elasticidad: el job diario detecta observaciones nuevas; si un producto cumple el umbral, se reentrena (reentrenamiento completo por el volumen pequeño) cuando haya datos nuevos (p. ej. semanal o con N observaciones nuevas).
- Se persisten: fecha de entrenamiento, observaciones usadas, métricas de validación y nivel de confianza del pronóstico.

#### Estrategia para historial insuficiente
- Promedio móvil + pronóstico de **baja confianza** (tesis).
- La sugerencia de compra se genera igualmente, con margen de precaución documentado, sin inventar datos.

#### Estrategia de datos de desarrollo
- Datos ficticios claramente identificados como simulación; nunca presentados como reales.

#### Limitaciones
- Los datos ficticios iniciales **no validan** el modelo en el negocio real.
- El modelo solo se considera válido al acumular historial real en el piloto.
- No es un modelo de series temporales dedicado (no ARIMA/Prophet/Holt-Winters en esta fase); puede evolucionar si el volumen y la evidencia lo justifican.
- Pronóstico presentado en lenguaje llano, con nivel de confianza y gráfico de tendencia simple por producto (tesis, Cap. V).

---

### P4. Datos de predicción y desarrollo — DECIDIDO
- Durante el desarrollo inicial se usarán **datos ficticios** para construir, probar y validar funcionalidades.
- Estos datos deben estar **claramente identificados como datos de prueba**; no presentarse como datos reales del negocio.
- Cuando el sistema se use en el negocio piloto: se registran **ventas reales desde ese momento**, se acumula historial real, y **no se asume historial digital previo**.
- La predicción se adapta progresivamente a la cantidad de datos disponibles.
- **No inventar historial real del negocio.**

### P5. Usuarios y roles — DECIDIDO (modelo simple)
- Grupo reducido de usuarios:
  1. El administrador del sistema (el usuario/desarrollador).
  2. El dueño del negocio.
  3. El padre del dueño.
- **No se necesitan** roles empresariales complejos (supervisor, encargado de compras, encargado de inventario, etc.) salvo decisión posterior.
- El sistema debe soportar **autenticación y autorización**.
- La diferencia exacta de permisos entre los tres usuarios queda **PENDIENTE** (no inventar permisos sin confirmación).

### P6. Modelo de datos — DECIDIDO (entidades base); detalle PENDIENTE
- Se mantienen las entidades de la tesis: Producto, Categoría, Proveedor, Cliente, Usuario, Venta, DetalleVenta, Almacén, Existencia, MovimientoInventario, Predicción, Sugerencia, Notificación.
- El diseño detallado de atributos, tipos, claves y relaciones debe realizarse **antes de crear las tablas**.
- El modelo debe ser coherente con los requerimientos funcionales reales; **no crear entidades innecesarias** solo porque podrían ser útiles en el futuro.

### P7. Diseño de la aplicación Web — DECIDIDO
- La aplicación actual será principalmente una **aplicación web de escritorio**, pero **responsive** y accesible desde teléfonos mediante navegador (no es una app móvil).
- Prioridad de experiencia:
  1. Computadora / escritorio.
  2. Teléfono mediante navegador como vista secundaria/responsive.
- Debe funcionar correctamente en ambas situaciones.
- Se conserva la identidad visual de la tesis (paleta morado/blanco, acentos dorados suaves, estados de alerta, estructura relacionada con inventario y ventas).
- **NO copiar literalmente** la navegación móvil de la tesis; la interfaz usa una estructura apropiada para aplicación web.

### P8. Comprobante de venta — DECIDIDO
- El comprobante es un **recibo interno**, no una factura tributaria.
- La aplicación debe: generar un **folio único** por venta; mostrar el comprobante tras registrar la venta; permitir **imprimirlo**; permitir **descargarlo como PDF**; almacenar la venta y su comprobante en la base de datos.
- **No implementar** facturación electrónica SAT/FEL en esta fase.
- El comprobante **no debe presentarse** como documento tributario.
- El diseño visual exacto del recibo se define durante la implementación.

### P9. Supabase — DECIDIDO
- **Ya existe un proyecto de Supabase gratuito** creado para este proyecto. **No crear otro proyecto** sin autorización.
- La intención es que OpenCode gestione la interacción con Supabase mediante **MCP**.
- Antes de operaciones destructivas o cambios importantes en la BD: **revisar el estado actual**, confirmar qué se modificará, evitar eliminar información innecesariamente, usar **migraciones o mecanismos reproducibles** cuando corresponda, y mantener las **credenciales fuera del código**.
- **PENDIENTE de config**: acceso MCP de Supabase (no hay servidor MCP configurado en este entorno) y confirmación de credenciales/manejo de variables de entorno. Indicar lo que deba hacerse manualmente antes de asumir acceso.

### P10. Git — DECIDIDO
- El proyecto utiliza **Git desde el inicio**.
- Existe repositorio remoto: **https://github.com/FernandoGonzalez416/PGFernandoGonzalez** — no crear otro.
- Si el directorio local no está inicializado/vinculado correctamente, preparar la inicialización y la vinculación con el repositorio existente (cuando se autorice).
- Crear un **`.gitignore`** apropiado para Node.js, Python, React, FastAPI, archivos `.env`, credenciales, temporales, builds y dependencias.
- **Nunca subir secretos** al repositorio.

### P11. Versiones — DECIDIDO (proceso)
- Las versiones concretas (React, Node.js, FastAPI, Python, Supabase, Scikit-learn y demás dependencias) deben ser **investigadas y propuestas** por el agente cuando corresponda.
- **No usar automáticamente la última versión** sin comprobar compatibilidad.
- Atención especial a la compatibilidad entre **Python, FastAPI, Pydantic** y sus dependencias.
- Al inicializar cada componente: revisar versiones estables y compatibles, proponerlas, explicar incompatibilidades relevantes y usar versiones coherentes entre sí.

### P12. Hosting / despliegue — DECIDIDO (se difiere)
- Hosting/despliegue **fuera de las prioridades actuales**.
- No invertir tiempo en decidir el proveedor todavía; se definirá cuando la aplicación esté suficientemente avanzada.

---

## Regla de iteración (DECIDIDO)

- El proyecto se desarrolla de forma **incremental**.
- La primera versión no necesita resolver todos los requisitos avanzados desde el primer día.
- Prioridad: 1) base correcta, 2) primera versión funcional, 3) probarla, 4) detectar problemas, 5) mejorarla progresivamente.
- No sacrificar la arquitectura por velocidad, pero **no introducir complejidad innecesaria** para problemas que todavía no existen.
- Cuando una funcionalidad pueda implementarse de forma sencilla inicialmente y evolucionar después, se puede comenzar con una solución simple **siempre que no cierre** innecesariamente las posibilidades futuras.

---

## Decisiones aún pendientes (requieren confirmación)

> Lista consolidada y actualizada de pendientes R1–R12, al final del documento, junto a las propuestas nuevas P13–P17.

---

## Propuestas revisadas y aprobadas

> P3a, P13, P14, P15 y P16 fueron **APROBADAS el 2026-09-21**; P17 queda **PENDIENTE DE CONFIGURACIÓN**. Aunque aprobadas, **ninguna de estas propuestas se implementa** (código, dependencias, tablas) hasta que el usuario autorice el inicio del desarrollo.

## P3a. Estrategia de predicción: plan completo (APROBADO — 2026-09-21)

> Plan que define cómo se implementa, valida y evalúa la predicción (requisito 7, tesis CU-03). Complementa a P3 (selección de modelo) y P13 (suficiencia de datos). **Aprobado por el usuario el 2026-09-21; no se implementa ninguna pieza hasta que se autorice el desarrollo.**

1. **Problema exacto**: pronosticar la demanda por producto para decidir el reabastecimiento, con alerta/sugerencia diaria (job programado) y reporte de incertidumbre.
2. **Variable objetivo**: unidades vendidas del producto en el día `t` (agregación diaria de `DetalleVenta` por producto).
3. **Horizonte**: próximos **7 días** (`t+1 … t+7`). La suma del periodo alimenta la sugerencia de compra; se evalúa día a día y acumulado.
4. **Unidad de agregación**: filas **día × producto**; un modelo por producto (catálogo pequeño).
5. **Frecuencia**: el job diario evalúa cada producto; reentrena solo si hay observaciones nuevas (volumen pequeño → reentrenamiento completo sencillo) y persiste métricas.
6. **Features de calendario**: día de la semana (0–6), mes, fin de semana (0/1), tendencia (días desde el inicio del historial).
7. **Features de rezagos**: ventas en `t-1` y `t-7` (último mismo día de la semana).
8. **Features móviles (sin fuga)**: media móvil y desviación móvil de 7 días calculadas **solo con datos hasta `t-1`** (nunca con el valor de `t` ni futuros). Warm-up de 14 días: se descartan las primeras filas sin features completas.
9. **Modelos candidatos** (mismo harness de validación): `RandomForestRegressor` (principal), `HistGradientBoostingRegressor` (pérdida `quantile` → intervalo P10–P90), `Ridge` (contraste, features de calendario codificadas). Todos dentro de un `Pipeline` de Scikit-learn, sin tuning pesado inicial.
10. **Línea base**: promedio móvil simple de 7 días (la "media de las últimas observaciones" de la tesis). **Todo** modelo ML se compara contra esta línea base.
11. **Split temporal**: división **secuencial sin barajar** → últimos 14 días como validación, resto entrenamiento (≈ 80/20). Nunca aleatoria (evita *look-ahead bias*).
12. **Walk-forward**: con ≥ 12 meses de historial se usa origen rodante (evaluar/reentrenar en pasos de 7 días sobre el pasado), reflejando el comportamiento real del job.
13. **Métricas**: **MAE** (unidades) como criterio de selección; **WAPE/MAPE** solo sobre días con ventas > 0 (evita dividir por cero); la tesis enlaza "precisión ≈ 100 − MAPE".
14. **nMAE y reporte de incertidumbre**: el pronóstico siempre reporta su error esperado (`nMAE = MAE / demanda media diaria`) junto con MAE/WAPE. El «30 %» queda **eliminado** (arbitrario); la confianza se decide por evidencia (P13).
15. **Selección y despliegue**: se elige el candidato de menor MAE en validación **y solo se despliega si vence a la línea base**; si no, se usa la línea base con "baja confianza".
16. **Historial insuficiente** (no pasa P13): promedio móvil de 7 días + **"baja confianza — historial en construcción"**; la sugerencia se genera igual con margen de precaución.
17. **Sin historial** (producto nuevo, sin ventas): **no se pronostica**; la sugerencia usa el stock mínimo (`umbralMinimo`) y datos básicos, marcada como "sin historial".
18. **Evaluación en el piloto (4 semanas)**: al vencer el horizonte se registra `demandaReal` contra el pronóstico (campo en `Prediccion`), se acumula error real por producto y se recalibran umbrales (P13) y modelo (P3) con datos reales. Los indicadores del piloto (precisión de pronóstico, disponibilidad de stock, tiempo de respuesta) se evalúan en esa ventana.

---

## P13. Criterio de suficiencia de datos (APROBADO — 2026-09-21)

> **Confirmado por el usuario (2026-09-21)**: horizonte de 7 días; datos agregados por día y producto; 75 días como umbral para intentar ML; warm-up de 14 días; validación inicial de 14 días; densidad mínima de ventas; Random Forest, HistGradientBoosting y Ridge como candidatos; comparación contra el promedio móvil de 7 días; selección únicamente mediante evidencia de validación; MAE, WAPE y nMAE como métricas; `nMAE < 100 %` solo como cota de cordura (no como criterio de "buena precisión"); sin historial suficiente → promedio móvil/con baja confianza; sin historial → no pronosticar; walk-forward cuando exista suficiente historial; evaluación específica durante el piloto de 4 semanas.
>
> Las limitaciones siguen documentadas en este apartado, y los **datos ficticios sirven para desarrollo/pruebas, no para demostrar precisión real** del modelo (P4). **No implementar hasta que se autorice el desarrollo.**

Objetivo: definir cuándo un producto tiene "historial suficiente" para entrenar modelos de aprendizaje automático, de forma **defendible académica y técnicamente**, no por una cifra arbitraria.

### De dónde salen los números

El criterio se deriva del propio pipeline del motor:

1. **Warm-up de features (14 días)**: los rezagos `t-1` y `t-7` y las medias/desviaciones móviles de 7 días exigen al menos 7 días previos completos; se descartan los primeros 14 días del historial para que toda fila de entrenamiento tenga features válidas al 100 %.
2. **Ventana de validación (14 días)**: la validación temporal debe cubrir al menos un ciclo semanal completo para evaluar la estacionalidad de día de la semana; 14 días = dos ciclos.
3. **Tamaño de entrenamiento (≈ 47 días)**: con warm-up de 14 y validación de 14, un total de 75 días deja ≈ 47 días de entrenamiento. Con 47 días, **cada día de la semana está representado ≥ 6 veces** en entrenamiento, lo que da base aprovechable para estimar el efecto del día de la semana (7 categorías) sin que el modelo quede sin ejemplos de un día en particular.
4. **Densidad de demanda (20 días con venta > 0)**: en una tienda pequeña de cosméticos hay productos con demanda esporádica (muchos días con venta 0). El conteo calendario solo no basta: si un producto tiene 75 días pero solo 4 días con ventas, un árbol de regresión no tiene forma de estimar nivel ni variabilidad. Se exige un mínimo de ejemplos positivos: **20 días con venta > 0 en entrenamiento** y **3 días con venta > 0 en validación** (para poder medir el error en días donde hubo demanda real).

### Regla de suficiencia (dos umbrales, ambos obligatorios)

Un producto pasa a "historial suficiente" SOLO si, contando desde su primera venta:

| Condición | Umbral | Justificación |
|---|---|---|
| Ventana calendario | **≥ 75 días** | warm-up 14 + validación 14 + entrenamiento ≈ 47 días (≥ 6 ejemplos por día de semana) |
| Densidad de demanda | **≥ 20 días con venta > 0** en entrenamiento **y ≥ 3** en validación | el árbol necesita ejemplos positivos suficientes para nivel y dispersión |

Umbrales **configurables** por constante y calibrables con los datos reales del piloto.

### Qué ocurre mientras no se cumple

- Pronóstico = **promedio móvil simple de 7 días** (tesis, CU-03) de las ventas diarias, etiquetado **"baja confianza — historial en construcción"**.
- La sugerencia de compra se genera igual, con margen de precaución y sin inventar datos.

### Cómo se construye el conjunto de entrenamiento

- Filas = **día × producto** (una fila por día con demanda del día y las features del mismo día).
- Features: día de la semana (0-6), mes, fin de semana (0/1), día desde el inicio del historial (tendencia), rezago `t-1`, rezago `t-7`, media móvil 7 días, desviación móvil 7 días.
- Objetivo: demanda del día `t` (unidades vendidas).
- Se descartan los primeros 14 días (warm-up). No se rellenan días cerrados ni se imputan ventas; se usa la serie tal cual con sus ceros reales.
- Un **modelo por producto** (el catálogo es pequeño); opcional a futuro: pooling por categoría para productos con muy pocas ventas (documentado como evolución).

### Baseline de comparación

- **Línea base**: promedio móvil simple de 7 días (equivale a la "media de las últimas observaciones" de la tesis).
- El modelo ML solo se despliega si su MAE en validación es **menor** que el de la línea base en la misma ventana; si no, se usa la línea base.

### Validación temporal

- División **secuencial, sin barajar**: últimos 14 días = validación; resto = entrenamiento.
- Con ≥ 12 meses: **walk-forward** (origen rodante cada 7 días) para simular el comportamiento del job diario en producción.
- Advertencia académica importante: dividir al azar validaría con datos "del futuro"; la división temporal evita ese sesgo (look-ahead bias).

### Métricas

- **MAE** (unidades de producto): métrica principal; interpretable y comparable entre días con demanda real.
- MAE validación vs MAE promedio móvil: decide entre desplegar ML o usar línea base.
- **MAPE/WAPE**: solo sobre días/semanas con ventas > 0; evita divisiones por cero. La tesis enlaza "precisión ≈ 100 − MAPE" (indicador 2.2).
- Se persisten métricas por producto y por ejecución en la entidad `Predicción`.

### Cuándo el modelo se considera confiable (criterio por evidencia; se eliminó el umbral de 30 %)

El umbral «MAE ≤ 30 %» **no se usa** (era arbitrario: imponía una meta porcentual sin justificación por volumen). La confianza se decide por **evidencia observada**, no por un porcentaje fijo:

- Se marca **"confianza alta"** SOLO si se cumplen todas las condiciones:
  1. pasó el criterio de suficiencia (P13, ambos umbrales);
  2. venció a la línea base en validación temporal (`MAE(candidato) < MAE(promedio móvil 7 días)`);
  3. el error es **comparable al volumen real**: `nMAE < 100 %` — el error medio por día no es mayor que la demanda media que se pronostica. Es una **cota de cordura** (máximo tolerable para llamarlo "alta"), no una meta de precisión;
  4. fue entrenado con **datos reales** del piloto (no ficticios, P4).
- El pronóstico **siempre reporta su error esperado** (MAE/WAPE/nMAE en unidades y %), sin ocultarlo; quien lee la sugerencia conoce la incertidumbre.
- Con datos ficticios de desarrollo el etiquetado siempre será "simulación" (P4), aunque el harness funcione.
- **"Confianza baja"** = no cumple 1–4: historial insuficiente, no vence a la línea base, o error ≥ demanda promedio. Es la regla de la tesis (promedio móvil + baja confianza), no un fallo.
- La escala (alta/baja) se recalibra con los datos reales del piloto; aquí queda definida la **lógica**, no un número mágico.

### Limitaciones que documentar en la tesis

- Los datos de desarrollo son ficticios; el modelo **no se considera válido** hasta acumular historial real.
- La estacionalidad mensual/anual exigirá ≥ 12 meses de datos; antes solo se captura la semanal.
- No se incluyen variables externas (promociones, precios temporales, clima, días feriados) en la primera versión.
- Muchos ceros (productos de baja rotación) limitan cualquier modelo; por eso la regla de densidad.
- Random Forest/etc. cubre bien el promedio condicionado, pero no extrapola tendencias fuertes ni eventos atípicos.
- El intervalo de confianza es aproximado (pérdida quantile de HistGB o ± factor de MAE), no estadístico exacto.
- Los umbrales se calibrarán con el piloto real; los límites aquí son iniciales.

---

## P14. Matriz de permisos completa para los 3 usuarios (APROBADO — 2026-09-21, con modificación)

> **Aprobado por el usuario el 2026-09-21 con una modificación**: el padre del propietario **SÍ puede anular las ventas registradas desde su propia sesión**. El resto de la matriz se mantiene.

Base: 6 requerimientos funcionales confirmados + CU-03 de la tesis (vista de predicción **exclusiva del administrador**; notificaciones a "administrador o encargado"). No se inventan permisos: se agrupan funcionalidades existentes y se distribuyen de forma conservadora. `admin` = administrador (yo), `dueño` = propietario, `padre` = padre del dueño.

| # | Capacidad | admin | dueño | padre |
|---|---|---|---|---|
| 1 | Ingresar (login) y cerrar sesión | ✅ | ✅ | ✅ |
| 2 | Cambiar su propia contraseña | ✅ | ✅ | ✅ |
| 3 | Registrar y consultar productos | ✅ | ✅ | ✅ |
| 4 | Editar/desactivar productos y umbrales de alerta (bajo stock y vencimiento) | ✅ | ✅ | ❌ (solo consulta) |
| 5 | Gestionar categorías | ✅ | ✅ | ❌ (solo consulta) |
| 6 | Gestionar proveedores (precios y condiciones de entrega) | ✅ | ✅ | ❌ (solo consulta) |
| 7 | Consultar stock disponible (por nombre, código o categoría) | ✅ | ✅ | ✅ |
| 8 | Registrar ventas (descuento de inventario, folio, recibo) | ✅ | ✅ | ✅ |
| 9 | Anular una venta | ✅ | ✅ | ✅ (solo ventas de su propia sesión) |
| 10 | Ajustes de inventario (entradas, salidas, mermas) | ✅ | ✅ | ❌ (solo consulta) |
| 11 | Ver movimientos de inventario | ✅ | ✅ | ✅ |
| 12 | Ver alertas (bajo stock / vencimiento próximo) | ✅ | ✅ | ✅ |
| 13 | Reportes (más vendidos, periodo) | ✅ | ✅ | ❌ |
| 14 | Ver predicción de demanda (CU-03: exclusiva del administrador) | ✅ | ❌ | ❌ |
| 15 | Ver sugerencias de compra | ✅ | ✅ | ✅ |
| 16 | Atender / marcar / descartar sugerencias | ✅ | ✅ | ✅ |
| 17 | Gestión de usuarios y roles | ✅ | ❌ | ❌ |
| 18 | Configuración del sistema (umbrales globales, datos ficticios, etc.) | ✅ | ❌ | ❌ |

Notas y justificación:
- **CU-03 (tesis)**: la vista de predicción es **exclusiva del administrador** → solo admin (fila 14). Las **notificaciones** van a "administrador o encargado"; en nuestros 3 usuarios, admin y dueño reciben notificaciones; el padre ve alertas y sugerencias en operación diaria.
- El **padre** tiene perfil de **operación diaria**: ventas (incluida la **anulación de sus propias ventas**), consulta de stock/productos y alertas y sugerencias; sin ajustes de inventario, borrados, usuarios ni configuración.
- El **dueño** gestiona catálogo e inventario, pero **no** usuarios, roles ni configuración del sistema; ve reportes.
- **Anulación (fila 9)**: aprobado 2026-09-21 — el **padre SÍ puede anular** las ventas registradas desde **su propia sesión** (el usuario logueado que hizo la venta). No puede anular ventas de admin/dueño ni de otras sesiones; esas requieren admin/dueño.
- Autenticación y autorización obligatorias para todos (requisito no funcional).
- **Discrepancia tesis (señalada, no corregida)**: la tesis menciona roles administrador/encargado/supervisor/vendedor; la implementación usa 3 usuarios (P5). Los permisos se traducen a estos 3 roles.

---

## P15. Esquema de datos detallado: las 13 entidades (APROBADO — 2026-09-21, esquema inicial)

> **Aprobado por el usuario el 2026-09-21 como esquema inicial**: un solo almacén, proveedor habitual por producto, folio `F-2026-0001`, método de pago según propuesta, 13 entidades, UUID, `numeric(12,2)`, CHECK e índices. **Aún NO se crean tablas** (se hará al iniciar el desarrollo, tras la verificación de relaciones indicada abajo).
>
> **Lotes (decisión 2026-09-21)**: **no se agrega una entidad `Lote`** en esta versión; el vencimiento se maneja con `Producto.fechaVencimiento` (lote activo; NULL = no perecedero). El diseño de `Producto`/`Existencia` **no debe cerrar** la posibilidad de incorporar lotes posteriormente (los productos podrían eventualmente tener distintas fechas de vencimiento). **Antes de crear las tablas** se verificará que las relaciones y restricciones (PK/FK, unicidades, CHECK) sean compatibles con esa evolución (p. ej. no fijar `fechaVencimiento` como `NOT NULL` ni hacerla parte de unicidades de inventario).

Base: las 13 entidades de la tesis. Convenciones: `id` = `uuid` PK con `gen_random_uuid()`; dinero = `numeric(12,2)` con `CHECK (x >= 0)`; fechas = `timestamptz`; valores cerrados = `text` + `CHECK` (portable a Supabase/PostgreSQL); `created_at` = `timestamptz NOT NULL DEFAULT now()`. Marcas: PK, FK, U (única), NN (no nulo).

### Catálogo y proveedores

**`Categoria`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| nombre | text | U, NN |
| descripcion | text | NULL |
| estado | text | NN, DEFAULT 'activo', CHECK in ('activo','inactivo') |
| created_at | timestamptz | NN, DEFAULT now() |

**`Proveedor`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| nombre | text | NN |
| contacto | text | NULL |
| telefono | text | NULL |
| email | text | NULL |
| condicionesEntrega | text | NULL |
| precioHabitual | numeric(12,2) | NULL, CHECK >= 0 (al enterar nuevas compras se actualiza) |
| estado | text | NN, DEFAULT 'activo', CHECK in ('activo','inactivo') |
| created_at | timestamptz | NN |

**`Producto`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| codigo | text | U, NN (código interno o de barra) |
| nombre | text | NN |
| descripcion | text | NULL |
| categoria_id | uuid | FK → Categoria, NN |
| proveedor_id | uuid | FK → Proveedor, **NULL** (proveedor habitual) |
| precioVenta | numeric(12,2) | NN, CHECK >= 0 |
| precioCosto | numeric(12,2) | NN, CHECK >= 0 |
| unidadMedida | text | NN, DEFAULT 'unidad' |
| umbralMinimo | numeric(12,2) | NN, DEFAULT 0, CHECK >= 0 (alerta bajo stock) |
| diasVencimientoAviso | integer | NN, DEFAULT 30, CHECK >= 0 (días antes de vencer para alerta) |
| fechaVencimiento | date | **NULL** (lote activo; NULL = no perecedero) — ver pregunta 8 |
| fechaIngreso | date | NULL |
| estado | text | NN, DEFAULT 'activo', CHECK in ('activo','inactivo') |
| created_at | timestamptz | NN |

### Ventas

**`Cliente`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| nombre | text | NN |
| telefono | text | NULL |
| activo | bool | NN, DEFAULT true |
| created_at | timestamptz | NN |

Sin DPI/NIT por privacidad (pregunta 5).

**`Venta`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| folio | text | **U, NN** (formato `F-<AÑO>-<sec>` global por año; el secuencial reinicia cada año) |
| fecha | timestamptz | NN, DEFAULT now() |
| cliente_id | uuid | FK → Cliente, **NULL** |
| usuario_id | uuid | FK → Usuario (vendedor), NN |
| metodoPago | text | NN, CHECK in ('efectivo','tarjeta','transferencia','otro') |
| subtotal | numeric(12,2) | NN, CHECK >= 0 |
| descuento | numeric(12,2) | NN, DEFAULT 0, CHECK >= 0 |
| total | numeric(12,2) | NN, CHECK >= 0 |
| estado | text | NN, DEFAULT 'activa', CHECK in ('activa','anulada') |
| motivoAnulacion | text | NULL |
| created_at | timestamptz | NN |

**`DetalleVenta`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| venta_id | uuid | FK → Venta, NN |
| producto_id | uuid | FK → Producto, NN |
| cantidad | integer | NN, CHECK > 0 |
| precioUnitario | numeric(12,2) | NN, CHECK >= 0 |
| subtotal | numeric(12,2) | NN, CHECK >= 0 |
| — | — | **U (venta_id, producto_id)** (un producto por línea) |

### Inventario

**`Almacen`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| nombre | text | U, NN (piloto: "Principal") |
| ubicacion | text | NULL |
| activo | bool | NN, DEFAULT true |

**`Existencia`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| producto_id | uuid | FK → Producto, NN |
| almacen_id | uuid | FK → Almacen, NN |
| cantidad | numeric(12,2) | NN, DEFAULT 0, CHECK >= 0 |
| — | — | **U (producto_id, almacen_id)** |

**`MovimientoInventario`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| producto_id | uuid | FK → Producto, NN |
| almacen_id | uuid | FK → Almacen, **NULL** |
| tipo | text | NN, CHECK in ('entrada','salida','ajuste') |
| referenciaTipo | text | NN, CHECK in ('venta','compra','ajuste','vencimiento','devolucion','inicial') |
| referenciaId | uuid | **NULL** (id de Venta/Compra según tipo; sin FK rígido por simplicidad — trazabilidad) |
| cantidad | numeric(12,2) | NN, CHECK > 0 (positiva; la dirección la da `tipo`) |
| usuario_id | uuid | FK → Usuario, **NULL** (NULL en procesos automáticos/job) |
| nota | text | NULL |
| fecha | timestamptz | NN, DEFAULT now() |

Índice recomendado: `(producto_id, fecha)`.

### Usuarios y autenticación

**`Usuario`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| auth_id | uuid | U, NN (UUID de Supabase Auth) |
| nombre | text | NN |
| email | text | U, NN |
| rol | text | NN, CHECK in ('administrador','propietario','padre') |
| activo | bool | NN, DEFAULT true |

### Predicción, sugerencia y notificaciones

**`Prediccion`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| producto_id | uuid | FK → Producto, NN |
| fechaGeneracion | timestamptz | NN, DEFAULT now() |
| inicioHorizonte | date | NN |
| finHorizonte | date | NN |
| demandaPronosticada | numeric(12,2) | NN, CHECK >= 0 |
| demandaReal | numeric(12,2) | **NULL** (se completa al vencer el horizonte; alimenta la evaluación del piloto) |
| intervaloInf | numeric(12,2) | NULL (P10/P90 de HistGB o ± factor de MAE) |
| intervaloSup | numeric(12,2) | NULL |
| metodo | text | NN, CHECK in ('promedioMovil','randomForest','histGradientBoosting','ridge') |
| nivelConfianza | text | NN, CHECK in ('alta','baja','simulacion') |
| maeValidacion | numeric(12,2) | NULL |
| wapeValidacion | numeric(12,2) | NULL |
| nmae | numeric(12,2) | NULL (MAE / demanda media diaria) |
| observacionesUsadas | integer | NULL |
| datosFicticios | bool | NN, DEFAULT false |
| created_at | timestamptz | NN |

**`Sugerencia`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| prediccion_id | uuid | FK → Prediccion, NN |
| producto_id | uuid | FK → Producto, NN |
| fecha | timestamptz | NN, DEFAULT now() |
| demandaPronosticada | numeric(12,2) | NN, CHECK >= 0 |
| stockProyectado | numeric(12,2) | NN, CHECK >= 0 |
| cantidadSugerida | numeric(12,2) | NN, CHECK >= 0 |
| prioridad | text | NN, CHECK in ('alta','media','baja') |
| estado | text | NN, DEFAULT 'pendiente', CHECK in ('pendiente','atendida','descartada') |
| — | — | U (prediccion_id, producto_id) |

**`Notificacion`**
| campo | tipo | restricción |
|---|---|---|
| id | uuid | PK |
| usuario_id | uuid | FK → Usuario, **NULL** (NULL = notificación general/visible a todos) |
| tipo | text | NN, CHECK in ('bajoStock','vencimientoProximo','sugerenciaCompra','sistema') |
| mensaje | text | NN |
| leida | bool | NN, DEFAULT false |
| fecha | timestamptz | NN, DEFAULT now() |

### Relaciones

Proveedor 1:N Producto · Categoria 1:N Producto · Producto 1:N DetalleVenta · Venta 1:N DetalleVenta · Venta N:1 Usuario (vendedor) · Cliente 0..1:N Venta · Producto 1:N Existencia (por almacén) · Almacen 1:N Existencia · Producto 1:N MovimientoInventario · Producto 1:N Prediccion · Prediccion 1:N Sugerencia · Usuario 1:N Notificacion.

### Respuestas a las preguntas de diseño

1. **¿Cuántos almacenes?** → Uno en el piloto ("Principal", `Almacen` con lote "Principal"). `Existencia` y `MovimientoInventario` quedan modeladas con `almacen_id` para no cerrar el multi-almacén futuro.
2. **¿Varios proveedores por producto?** → Hoy: **un proveedor habitual** (`Producto.proveedor_id`). Una tabla puente `proveedor_producto` se difiere hasta que exista necesidad real en el negocio.
3. **Formato del folio de venta** → `F-<AÑO>-<SECUENCIAL>` (p. ej. `F-2026-0001`), **único global**, reinicia por año. El diseño visual del recibo se define al implementar (P8).
4. **¿Método de pago?** → Sí, mínimo con `CHECK` cerrado: efectivo / tarjeta / transferencia / otro. Sin caja/arqueo en esta fase.
5. **¿Se registran clientes?** → `Cliente` opcional en la venta (`Venta.cliente_id` nullable). **Sin DPI/NIT** por privacidad.
6. **¿Anulación de ventas?** → `Venta.estado='anulada'`, **los detalles se conservan** (auditoría), se genera un `MovimientoInventario` compensatorio que restaura el stock y **el folio no se reutiliza**. Solo admin/dueño (P14). Motivo obligatorio (`motivoAnulacion`).
7. **¿Movimientos de inventario?** → Un solo tipo de entidad con `tipo` (entrada/salida/ajuste) + `referenciaTipo` + `referenciaId` genérico; así toda variación de stock queda trazada (venta, compra, merma, vencimiento, devolución, inicial).
8. **¿Vencimientos? (decisión 2026-09-21)** → **NO se crea entidad `Lote` en esta fase.** El vencimiento se maneja con `Producto.fechaVencimiento` (lote activo; NULL = no perecedero) + `diasVencimientoAviso`. El diseño **no cierra** la posibilidad de incorporar lotes después: `fechaVencimiento` en `Producto` es compatible con una futura entidad `Lote`. **Antes de crear las tablas** se verificarán relaciones y restricciones para que esa evolución no genere problemas (no `NOT NULL` en `fechaVencimiento`, no unicidades de inventario que impidan lotes por lote).
9. **¿Soft o hard delete?** → **Soft**: `estado`/`activo` en catálogo; las ventas nunca se borran (auditoría). No hay `UPDATE`/`DELETE` destructivo en `Venta`/`DetalleVenta`.
10. **¿Quién genera notificaciones?** → El job diario evalúa bajo stock y vencimientos; las sugerencias de compra generan notificaciones; destinatarios por rol (P14). No hay sistema de colas en esta fase.

---

## P16. Propuesta de versiones (APROBADO — 2026-09-21)

Versiones consultadas el 2026-09-21 en registros oficiales (npm, PyPI, nodejs.org, endoflife.date). **APROBADO por el usuario el 2026-09-21: versiones exactas fijadas para el backend, rangos compatibles + lockfile para el frontend, y Node.js 24 LTS sin pin exacto. No se instala/actualiza nada hasta que se autorice el desarrollo.**

| Componente | Versión propuesta | Por qué | Compatibilidad | Riesgos | Recomendación |
|---|---|---|---|---|---|
| Python | **3.14.x** (local 3.14.4; hay 3.14.7) | estable actual, soportada por todo el stack | — | ninguno relevante | entorno local: se puede actualizar a 3.14.7; documentar en `README`/`.python-version` |
| FastAPI | **0.141.1** | estable, usa Pydantic v2 | requiere Python ≥ 3.10 ✓ | bajo | backend: **pin exacto** |
| Pydantic | **2.13.5** | v2 actual; intercambio directo con FastAPI | requiere Python ≥ 3.9 ✓ | bajo | backend: **pin exacto** |
| Uvicorn | **0.53.0** | servidor ASGI dev/despliegue | requiere Python ≥ 3.10 ✓ | bajo | backend: **pin exacto** |
| scikit-learn | **1.9.1** | publica ruedas oficiales para Python 3.14 (cp314, win_amd64) | requiere Python ≥ 3.11 ✓; instalable en 3.14 | bajo | backend: **pin exacto** (las métricas de la tesis deben ser reproducibles) |
| Node.js | **v24 LTS (Krypton)**, actual 24.21.0; local 24.15.0 | línea LTS activa, soporte LTS completo | toda la toolchain frontend actual ✓ | muy bajo (estamos dentro de la misma LTS) | **no pin**: quedarse en la línea LTS v24 |
| React (web) | **19.3.0** | estable actual | funciona con Node 24 ✓ | bajo | frontend: rango major `^19` (+ lockfile) |
| supabase-js | **2.116.0** | cliente oficial Supabase browser/Node | versión 2.x estable; WebSocket Real-time ✓ | bajo | frontend: rango major `^2` (+ lockfile) |
| Vite (bundler) | **8.3.0** | build estándar de React | requiere Node moderno (ok v24) ✓ | bajo | frontend: rango major `^8`; **revalidar al momento del scaffold** |
| react-router | **8.4.0** | enrutado web | compatible React 19 ✓ | bajo | frontend: rango major `^8`; confirmar al hacer el scaffold |

Notas:
- Compatibilidad verificada (registros oficiales 2026-09-21): `FastAPI 0.141 + Pydantic 2.13 + Uvicorn 0.53` todos aceptan Python 3.14; `scikit-learn 1.9.1` publica ruedas `cp314` para Windows (`win_amd64`). `React 19 + Vite 8` funcionan con Node 24 LTS.
- **Estrategia de versionado**: backend con **pines exactos** (requirements.txt/pyproject congelado; reproducibilidad de resultados y de la tesis); frontend con **rangos de major** (`^`) y `package-lock.json` fijado (parches automáticos seguros); Node en **línea LTS sin pin menor**.
- Versiones de build (Vite/router) **se revalidan al inicializar el scaffold** antes de instalar.

---

## P17. Conexión de Supabase vía MCP (PENDIENTE DE CONFIGURACIÓN — solo lectura; sin conexión aún)

> **Estado 2026-09-21**: se aprueba el **enfoque solo lectura**, pero **no se configura ni conecta MCP ni se modifica Supabase** hasta que se indique. Cuando corresponda, se pedirá al usuario el **Project Ref** (`xxxx` de `supabase.com/dashboard/project/xxxxxxxx`) y se le indicará el comando exacto (`opencode mcp auth supabase`). No hay nada más por decidir; los pasos están listos abajo.

### Qué configuración se necesita

En `opencode.json` del proyecto (sin credenciales; solo la URL y opciones):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [".opencode/rules/*.md"],
  "mcp": {
    "supabase": {
      "type": "remote",
      "url": "https://mcp.supabase.com/mcp?project_ref=<REF>&read_only=true&features=database,docs,development",
      "enabled": true
    }
  }
}
```

- `project_ref=<REF>`: limita el servidor a **un solo proyecto** (desactiva herramientas de gestión de cuentas).
- `read_only=true`: al inicio se trabaja en **modo solo lectura** (inspección del esquema actual); al autorizar migraciones se cambia a escritura.
- `features=database,docs,development`: expone solo consultas/tablas/migraciones/lógica de desarrollo y búsqueda de docs; sin Storage ni Branching.
- El **token de autenticación NO se guarda en el repositorio**: opencode lo almacena en su propio store de credenciales tras el flujo OAuth.

### Qué debe hacer el usuario manualmente

1. Proporcionar el **Project Ref** del proyecto Supabase existente (segmento `xxxx` de la URL del dashboard: `supabase.com/dashboard/project/xxxxxxxx`). Es lo único que falta para completar la URL.
2. Etapa 1 (inspección): ejecutar en terminal `opencode mcp auth supabase`. Se abre el navegador; iniciar sesión en Supabase y **conceder acceso a la organización** que contiene el proyecto.
3. Reiniciar OpenCode (los cambios de `opencode.json` no se recargan en caliente).
4. Verificar: pedir "listar las tablas actuales del schema" para confirmar la conexión.
5. Para carga de credenciales usamos **variables de entorno** (nunca archivos del repo). No se requieren PAT en este flujo (OAuth dinámico); si en el futuro se necesita CI, se usará `SUPABASE_ACCESS_TOKEN` en variable de entorno, nunca commitearla.

---

## Decisiones aún pendientes (requieren confirmación)

**Resueltas el 2026-09-21 (APROBADAS)**: R1 (P3/P3a, selección de modelo + plan de 18 puntos), R2/R9 (P14, matriz de 18 capacidades con la modificación de anulación propia del padre), R3/R10 (P15, esquema inicial + 10 respuestas), R6/R11 (P16, versiones/pin-range), R8 (P13, suficiencia + confianza por evidencia).

Siguen pendientes:
- **R4. Estrategia offline definitiva** y su tecnología (P2): se documentará cuando llegue el momento; no bloquea la primera versión.
- **R5. Detalles de despliegue/hosting** (P12): cuando la aplicación esté avanzada.
- **R7/R12. Supabase MCP (P17)**: PENDIENTE DE CONFIGURACIÓN — falta aportar el **Project Ref** y ejecutar `opencode mcp auth supabase`. No conectar ni modificar Supabase hasta que se indique.
- **Inicio del desarrollo**: crear código (React/FastAPI/Node/Supabase/IA), instalar dependencias o crear tablas queda **prohibido hasta orden explícita** del usuario.

---

## Criterios estables del proyecto (no son pendientes)

- **D1. Alcance de esta fase**: solo aplicación Web. React Native queda para fase posterior; prohibido código/carpetas/servicios móviles. La arquitectura se mantiene compatible con una futura app móvil.
- **D2. Stack confirmado**: React.js (web) · FastAPI (API principal) · Node.js (tareas livianas/serverless ocasional) · Supabase (PostgreSQL, Auth, Storage) · Scikit-learn (predicción).
- **D3. Jerarquía de autoridad**: 1) instrucciones explícitas del usuario · 2) requisitos confirmados del proyecto · 3) código y arquitectura existente · 4) AGENTS.md · 5) reglas de `.opencode/rules/` · 6) este documento · 7) convenciones generales de frameworks/lenguajes.
- **D4. Regla "no inventar"**: si algo no está definido, detectar la ambigüedad, explicar qué falta, proponer alternativas y pedir confirmación antes de decisiones importantes.
- **D5. Entidades y requerimientos de referencia**: ver `AGENTS.md` (entidades de la tesis + 6 requerimientos funcionales del Cap. IV + predicción con job diario).
- **D6. Fuentes de verdad**: tesis `Fernando Gonzalez PG 2 UNIVERSIDAD MARIANO GALVEZ DE GUATEMALA.docx` (raíz) + decisiones documentadas aquí.