# Decisiones del proyecto

Este archivo contiene **únicamente** decisiones reales: confirmadas por el usuario o pendientes de confirmación. No se rellena con información inventada.

Estado de las entradas: `APROBADO` (confirmado explícitamente), `PENDIENTE DE APROBACIÓN` (propuesto, en revisión, NO se implementa), `NO APLICA / POSPUESTO` (fuera de alcance actual).

Actualización principal: 2026-09-21 (confirmación P1–P12 y aprobación de **P3/P3a/P13, P14, P15 y P16**). Mismo día, **P17 fue CONFIGURADO**: servidor Supabase MCP añadido a `opencode.json` (`read_only=true`, `features=database,docs,development`) y **autenticado** vía OAuth. Pendiente: aportar el **Project Ref** para limitar el alcance a un solo proyecto y reiniciar OpenCode para que la sesión cargue las herramientas MCP. Mismo día, **P18 fue APROBADO**: `httpx2` como cliente HTTP de testing del backend (ver sección P18).

Actualización: 2026-09-26 — **P7 reaprobada (identidad visual)**. Se **descartan** la paleta morado/blanco con acentos dorados y la marca de prueba "Belleza Clara". Identidad oficial: **Familia de la Cruz**, paleta crema/nude/terracota/café/gloss y tipografías **Playfair Display** (títulos) + **Montserrat** (cuerpo). El stack tecnológico no cambia. Ver sección P7, incluida la discrepancia con la tesis §5.2.

### Tabla de estado general

| # | Tema | Estado |
|---|---|---|
| P1 | Node.js serverless | APROBADO |
| P2 | Offline / sincronización | APROBADO (enfoque); implementación POSPUESTA a fase posterior |
| P3 | Modelo de predicción | APROBADO (2026-09-21) |
| P4 | Datos de predicción y desarrollo | APROBADO |
| P5 | Usuarios y roles | APROBADO; permisos APROBADOS (P14) |
| P6 | Modelo de datos | APROBADO (13 entidades; esquema P15 APROBADO) |
| P7 | Diseño web | APROBADO; identidad visual **REAPROBADA el 2026-09-26** (nude/terracota/café en lugar de morado/dorado; marca "Familia de la Cruz") |
| P8 | Comprobante de venta | APROBADO (detalle del recibo se define al implementar) |
| P9 | Supabase | APROBADO; conexión MCP CONFIGURADA y AUTENTICADA (P17); falta scoping por Project Ref |
| P10 | Git | APROBADO (commit/push pendientes de orden explícita) |
| P11 | Versiones | APROBADO (proceso + propuesta P16) |
| P12 | Hosting / despliegue | NO APLICA / POSPUESTO |
| P13 | Criterio de suficiencia de datos | APROBADO (2026-09-21) |
| P14 | Matriz de permisos | APROBADO (2026-09-21, con modificación) |
| P15 | Esquema de datos detallado | APROBADO (2026-09-21, esquema inicial) |
| P16 | Versiones detalladas | APROBADO (2026-09-21; no instalar aún) |
| P17 | Supabase MCP | CONFIGURADO y AUTENTICADO (2026-09-21): solo lectura en `opencode.json`; **Project Ref aportado y aplicado** (2026-09-21); pendiente reiniciar OpenCode |
| P18 | Cliente HTTP para tests del backend | APROBADO (2026-09-21): `httpx2` (fork "next generation" de Pydantic) en vez de `httpx` |
| P19 | Patrón de acceso frontend↔Supabase | APROBADO |

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

### P7. Diseño de la aplicación Web — DECIDIDO (identidad visual REAPROBADA el 2026-09-26)

> **Reaprobación 2026-09-26 (sustituye la identidad anterior).** El usuario **descartó oficialmente** la identidad previa (morado/blanco con acentos dorados) y la marca de prueba **"Belleza Clara"**. La identidad vigente es la propuesta de cosmética moderna aprobada abajo, con la marca real **Familia de la Cruz**. **No se reintroducen el morado ni el dorado.**

#### Alcance de la interfaz (sin cambios)
- La aplicación actual será principalmente una **aplicación web de escritorio**, pero **responsive** y accesible desde teléfonos mediante navegador (no es una app móvil).
- Prioridad de experiencia:
  1. Computadora / escritorio.
  2. Teléfono mediante navegador como vista secundaria/responsive.
- Debe funcionar correctamente en ambas situaciones.
- **NO copiar literalmente** la navegación móvil de la tesis; la interfaz usa una estructura apropiada para aplicación web.
- **El cambio es solo de identidad visual**: variables de estilo, clases, tipografías y nombre de la tienda. **No se modifica el stack tecnológico** (React + Vite + TypeScript, FastAPI, Supabase, Motion); la lógica de las vistas (selector de tonos, carrito, modales) se adapta con las tecnologías ya definidas en el repositorio.

#### Nombre oficial del establecimiento
- **"Familia de la Cruz"** es el nombre real de la marca y debe mantenerse **en todo momento**: interfaz, comprobante de venta, reportes y documentación.
- **Prohibido** usar marcas genéricas o de prueba ("Belleza Clara", "Cosméticos De la Cruz", "Gloss & Nude" o cualquier otra) en cualquier vista o artefacto del proyecto.

#### Paleta de colores oficial

| Rol | Token | Hex | Uso |
|---|---|---|---|
| Blanco crema | `crema` | `#FAF6F0` | Fondo principal y áreas de lectura limpia |
| Rosa nude suave | `nude` | `#E0C9BB` | Fondos secundarios, tarjetas de productos y secciones destacadas |
| Terracota | `terracota` | `#C87D71` | Acento primario: botones de acción (CTA), precios y etiquetas destacadas, bordes y estados activos |
| Café oscuro profundo | `cafe` | `#2D2424` | Tipografía principal, títulos, iconos y encabezados (reemplaza al negro puro) |
| Gloss soft | `gloss` | `#D8B4A0` | Estados *hover*, bordes activos e interacciones secundarias |

Reglas de aplicación (confirmadas por el usuario):
- **Contraste**: el terracota se usa como **relleno, borde o estado activo**, nunca como color de texto sobre crema (2.9:1, no cumple AA). Sobre relleno terracota el texto es **café `#2D2424`** (4.8:1, cumple AA).
- **Precios y etiquetas**: se destacan con terracota como fondo, borde o subrayado, manteniendo el texto en café.
- **Hover**: se resuelve con `gloss` o con un tinte de `gloss`; no se incorporan colores nuevos.
- **Estados de alerta**: se **conservan** los colores semánticos (ámbar = bajo stock, rojo = vencimiento/agotado, verde = disponible) porque transmiten información, no marca. La paleta nude/terracota es la identidad; los colores semánticos no la reemplazan.
- **Sombras**: siempre teñidas (`rgba` de café o terracota), nunca negro puro.
- Contraste mínimo **WCAG AA** en todo el texto (≥ 4.5:1) y en bordes y elementos gráficos con significado (≥ 3:1).

#### Tipografía oficial

| Uso | Familia | Pesos |
|---|---|---|
| Títulos y encabezados (H1, H2, H3, nombres de líneas, nombre del establecimiento) | **Playfair Display** (serif) | 500 / 600 / 700 |
| Cuerpo de texto, precios, filtros, navegación, botones y etiquetas | **Montserrat** (sans-serif) | 400 / 500 / 600 / 700 / 800 |

- Números y montos: `font-variant-numeric: tabular-nums`.
- Ambas familias son de uso libre; en el prototipo se cargan desde Google Fonts y en producción se servirían como archivos locales (self-hosted).

#### Discrepancia con la tesis (señalada, NO se corrige en el documento)
> **Corrección 2026-09-26.** Una nota anterior de P7 afirmaba que §5.2 no tenía sub-puntos numerados. Es **incorrecto**: el documento contiene §5.2.1 a §5.2.10 numerados. La referencia se corrige abajo.

La tesis §5.2 "Maquetización" **sí** existe y está numerada (§5.2.1–§5.2.10). Se adoptó su **estructura** (encabezado + menú lateral con cuatro accesos, contenido central, formularios guiados, colores semánticos de estado) y se resolvió así cada conflicto con la identidad aprobada:

| §tesis | Qué pide | Conflicto | Resolución en esta fase |
|---|---|---|---|
| §5.2.2 | Logotipo **genérico**, no vinculado a un negocio | Contradice la marca real obligatoria | Se usa el logotipo de **"Familia de la Cruz"**; la estructura (logotipo en el encabezado) sí se respeta |
| §5.2.4 | Paleta **morado / blanco / dorado**, acento dorado en botones y alertas positivas | Contradice la paleta oficial | Se usa crema / nude / terracota / café / gloss; el **terracota** es el acento de los botones de acción. "Alertas positivas" en **verde** (`--ok`), no en dorado |
| §5.2.5 | Tipografía **sans-serif** genérica, en su mayoría semibold | Contradice la tipografía oficial | **Playfair Display** en títulos y **Montserrat** en cuerpo |
| §5.2.3 | Cuatro accesos: Panel general, Productos, Ventas, Alertas | — | **Se aplica tal cual** |
| §5.2.6 – §5.2.10 | Login, panel, productos, ventas y alertas con la estructura descrita | — | **Se aplican tal cual** |

- **No se modifica el documento académico** para que coincida con el código (regla del proyecto). Las diferencias quedan registradas aquí y deben explicarse en la defensa del proyecto como decisiones de diseño posteriores, tomadas con el usuario.
- Nota sobre §5.2.7: la tesis pide que la **predicción de demanda** sea una vista exclusiva del administrador. Por eso **no es uno de los cuatro accesos del menú lateral** (que §5.2.3 fija en cuatro); se abre desde el Panel general mediante una tarjeta que indica que es una vista de administración.
- Nota sobre §5.2.8: la tesis enumera seis campos para registrar un producto (nombre, categoría, cantidad, proveedor, fecha de ingreso y precio). Los seis se respetan y se muestran en ese orden, en formulario vertical. Se **agregan dos campos opcionales** —**cantidad mínima** y **fecha de vencimiento**— porque las reglas de alerta del proyecto (`umbralMinimo`, `diasVencimientoAviso`) no pueden calcularse sin ellos y ambos existen en el modelo de datos aprobado (P15). Quedan marcados como "Opcional" en la interfaz para no atribuir a la tesis un requisito que no enuncia.

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

> P3a, P13, P14, P15 y P16 fueron **APROBADAS el 2026-09-21**; **P17 fue CONFIGURADO y AUTENTICADO** el mismo día (MCP de Supabase en `opencode.json`, solo lectura). Aunque aprobadas/configuradas, **ninguna de estas propuestas se implementa** (código, dependencias, tablas) hasta que el usuario autorice el inicio del desarrollo.

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

## P17. Conexión de Supabase vía MCP (CONFIGURADO Y AUTENTICADO — 2026-09-21; solo lectura)

> **Estado 2026-09-21**: se aprobó el **enfoque solo lectura** y **quedó configurado y autenticado**: el servidor remoto `supabase` está en `opencode.json` (`read_only=true`, `features=database,docs,development`) y la sesión OAuth fue completada por el usuario en el navegador (`opencode mcp auth supabase`). El **Project Ref `spozipecnvhmchxvmsqt` fue aportado y aplicado** a la URL (`project_ref=spozipecnvhmchxvmsqt`, scoping a un solo proyecto; deshabilita las herramientas de cuenta) — **no es un secreto** (ni API key ni token), por lo que se commitea normal, sin variables de entorno. **Solo falta reiniciar OpenCode** para que la sesión cargue las herramientas MCP scoped al proyecto (reinicio manual del usuario, no posible desde dentro de la sesión actual).

### Qué configuración se necesita

Estado actual en `opencode.json` del proyecto (sin credenciales; solo la URL y opciones):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [".opencode/rules/*.md"],
  "mcp": {
    "supabase": {
      "type": "remote",
      "enabled": true,
      "url": "https://mcp.supabase.com/mcp?read_only=true&features=database,docs,development"
    }
  }
}
```

Pendiente de aplicar en la URL (una vez se tenga el Project Ref): `project_ref=<REF>` para limitar el servidor a **un solo proyecto** (desactiva herramientas de gestión de cuentas) → `https://mcp.supabase.com/mcp?project_ref=<REF>&read_only=true&features=database,docs,development`.

- **Project Ref APORTADO y APLICADO (2026-09-21)**: `spozipecnvhmchxvmsqt` — la URL activa es `https://mcp.supabase.com/mcp?project_ref=spozipecnvhmchxvmsqt&read_only=true&features=database,docs,development`. No es un secreto (no es API key ni token), se commitea normal, sin variables de entorno.

- `read_only=true`: se trabaja en **modo solo lectura** (inspección del esquema actual). Al autorizar migraciones se cambia de forma explícita e informada.
- `features=database,docs,development`: expone solo consultas/tablas/migraciones/lógica de desarrollo y búsqueda de docs; sin Storage ni Branching.
- El **token de autenticación NO se guarda en el repositorio**: opencode lo almacena en su propio store de credenciales (OAuth dinámico; no se requirió PAT).

### Estado manual (ejecutado el 2026-09-21)

1. ✅ Añadido el servidor `supabase` a `opencode.json` del proyecto (solo lectura).
2. ✅ Autenticado: `opencode mcp auth supabase` — el usuario completó el flujo OAuth en el navegador. Verificado con `opencode mcp auth list` → `supabase ✓ authenticated`.
3. ⏳ Pendiente (manual del usuario): **reiniciar OpenCode** para que la sesión cargue las herramientas MCP (los cambios de `opencode.json` no se recargan en caliente).
4. ✅ **Project Ref aportado y aplicado (2026-09-21)**: `spozipecnvhmchxvmsqt` en la URL (`project_ref=spozipecnvhmchxvmsqt`), deshabilita herramientas de cuenta. No es un secreto; se commitea normal.
5. ⏳ Pendiente: verificar la conexión pidiendo "listar las tablas actuales del schema".
6. Para carga de credenciales de la aplicación usamos **variables de entorno** (nunca archivos del repo). No se requieren PAT en este flujo (OAuth dinámico); si en el futuro se necesita CI, se usará `SUPABASE_ACCESS_TOKEN` en variable de entorno, nunca commitearla.

---

## P18. Cliente HTTP para las pruebas del backend: `httpx2` (APROBADO — 2026-09-21)

> **Aprobado directamente por Fernando el 2026-09-21**: se usa **`httpx2`** (fork "next generation" de Pydantic, `github.com/pydantic/httpx2`) como dependencia de testing del backend, **en lugar del `httpx` clásico**.

### Contexto

- Para probar la API con `fastapi.testclient` (TestClient de Starlette) se requiere un cliente HTTP de pruebas.
- El `httpx` estándar quedó **desactualizado/deprecado para este uso** con las versiones vigentes de Starlette (**1.6.0+**): el TestClient dejó de recomendarlo e insta a migrar, emitiendo además un warning de deprecación si se usa.
- Starlette 1.6.0 (incluido en FastAPI 0.141.1, según P16) importa `httpx2` como cliente preferido del TestClient (`import httpx2 as httpx`).

### Decisión

- Instalar **`httpx2==2.13.0`** como dependencia de **desarrollo** del backend (`backend/requirements-dev.txt`, pines exactos igual que P16), junto con `pytest` y `pytest-asyncio`.
- **No** instalar `httpx` clásico en esta fase para testing: queda fuera del stack de pruebas.
- Configuración verificada: `TestClient(app)` funciona con `httpx2` sin warnings (respuesta `/health` OK).

### Consideraciones

- `httpx2` es el reemplazo moderno recomendado por Starlette para `TestClient` (mismo criterio aplicado cuando se decidió el stack en `testing.md`).
- `requirements-dev.txt` referencia `requirements.txt` (dependencias de runtime) y añade los pines de testing.

---

## P19. Almacén por defecto para el inventario (APROBADO — 2026-10-05)

> **Aprobado directamente por Fernando el 2026-10-05**, junto con P20 y P21, para desbloquear la Fase 0 del backend.

### Contexto

- El proyecto Supabase (`spozipecnvhmchxvmsqt`) tiene la tabla `almacen` con **0 filas**.
- `existencia.almacen_id` es **NOT NULL** con FK a `almacen` (esquema P15), y `existencia.cantidad` está en `CHECK (cantidad >= 0)`.
- Sin al menos un almacén no se puede registrar ni una existencia ni una venta: **la venta del requerimiento 4 es imposible en el estado actual**.
- El piloto es un negocio familiar con un único punto de stock.

### Decisión

- **Un único almacén "Principal"**, sembrado de forma idempotente por `backend/scripts/semilla.py`.
- El backend lo resuelve con la variable de configuración `ALMACEN_PREDETERMINADO` (en `backend/app/core/config.py`), de modo que **ningún endpoint exige que el cliente mande `almacen_id`**.
- **Multi-almacén queda fuera de esta fase**: no se expone `almacen_id` en la venta ni en los ajustes.

### Consideraciones

- No se cierra la puerta a multi-almacén: la columna y la unicidad `UNIQUE (producto_id, almacen_id)` ya lo permiten. Si más adelante se requiere, se añade `almacen_id` al request y un selector en la UI.
- La Fase 0 siembra umbrales `umbral_minimo > 0` en el catálogo ficticio, porque con `umbral_minimo = 0` **todo** producto aparecería como bajo stock.

---

## P20. Base de datos para las pruebas de integración (APROBADO — 2026-10-05)

### Contexto

- `backend/tests/` corre **42 pruebas con dobles (mocks)**, sin base de datos.
- Los dobles **no pueden verificar** la atomicidad de la venta, los `CHECK` de folios y totales, ni los `UNIQUE` (`folio`, `detalle_venta (venta_id, producto_id)`, `producto.codigo`), que son precisamente el núcleo del requerimiento 4.
- `pytest-mock` no está instalado: se usa `unittest.mock` de la stdlib.

### Decisión

- **Esquema `test` dentro del mismo proyecto Supabase**, con el mismo DDL que las migraciones de `supabase/migrations/`.
- Cada prueba de integración se ejecuta **dentro de una transacción que se revierte al final** (rollback), de modo que el esquema `test` no acumula datos.
- Las pruebas unitarias (capacidades, dinero, errores) **siguen sin base de datos**.
- Las pruebas de integración se marcan con `pytest.mark.integracion` y exigen `DATABASE_URL_TEST`; sin esa variable se **omiten** (`skip`), nunca se apuntan por error a la base de desarrollo.

### Consideraciones

- No requiere Docker ni un Postgres local, y usa el mismo proyecto ya configurado (P9/P17).
- Al conectar como propietario, **RLS no aplica** en el esquema `test`: la autorización se sigue probando en la capa de FastAPI (`requiere()`).
- Si el proyecto Supabase se usara para producción, convendría mover el esquema `test` a una base separada; hoy el piloto es un único entorno.

---

## P21. Redondeo y precisión del dinero (APROBADO — 2026-10-05)

### Contexto

- Los montos son `numeric` **sin escala fija** en PostgreSQL.
- Hay restricciones que exigen cuadrar **exacto**: `venta.total = subtotal - descuento`, `0 <= descuento <= subtotal`, `detalle_venta.subtotal = cantidad * precio_unitario`.
- Sin una regla explícita, el redondeo por línea puede hacer que el total no cuadre y la venta sea rechazada por el `CHECK`.

### Decisión

- **2 decimales con `ROUND_HALF_UP`**, implementados en `backend/app/core/dinero.py` (helper único, sin lógica duplicada).
- **Los precios se cuantizan al guardar** (`precio_venta`, `precio_costo`) en Pydantic y en el servicio.
- Con `cantidad` entera y precio ya cuantizado a 2 decimales, el **subtotal de línea es exacto** (`cantidad * precio_unitario`), lo que satisface el `CHECK` sin redondear la línea.
- El **redondeo ocurre una sola vez**, al cuantizar los totales de la venta (`subtotal`, `descuento`, `total`), nunca por línea.

### Consideraciones

- Si algún día una cantidad admitiera fracciones, la regla debe revisarse: el `CHECK` de `detalle_venta` seguiría exigiendo aritmética exacta.
- `Decimal` en Python y `numeric` en PostgreSQL se complementan sin pérdida, siempre que no se convierta a `float` en el camino.

---

## P22. Generación concurrente del folio de venta (APROBADO — 2026-10-05)

> **Aprobado directamente por Fernando el 2026-10-05**. Resuelve la decisión bloqueante **B3** del plan `backend/docs/PLAN_FASE3_4.md`.

### Contexto

- `venta.folio` tiene `CONSTRAINT chk_venta_folio_formato CHECK (folio ~ '^F-\d{4}-\d{4,}$')` y `CONSTRAINT uq_venta_folio UNIQUE (folio)`.
- No existe tabla de contador de folios, y el esquema P15 está **aprobado**: agregar una tabla sería una decisión de esquema.
- Sin serialización, dos ventas simultáneas pueden leer el mismo `MAX(folio)` y colisionar en el `UNIQUE`.

### Decisión

- **`pg_advisory_xact_lock` + `MAX(folio)` del año actual**, calculados **dentro de la misma transacción de la venta y antes del `INSERT`**.
- El bloqueo se toma sobre una clave fija del año en curso; el `UNIQUE` permanece como red de seguridad.
- **No requiere cambios al esquema P15**: el `CHECK` de formato y el `UNIQUE` de folio ya existen.

### Consideraciones

- `pg_advisory_xact_lock` se libera automáticamente al confirmar o revertir la transacción, incluso ante error: no hay estado que limpiar.
- **El `pg_advisory_xact_lock` se libera al terminar la transacción completa del request (commit en `get_db_session`), no al cerrar el SAVEPOINT del servicio** — esto es intencional: serializa la generación de folio entre requests concurrentes durante toda la duración del request, no solo durante el cálculo del folio.
- El folio queda con el formato `F-AAAA-NNNN` (4 dígitos mínimos, `lpad`), que es lo que el `CHECK` exige.
- Si más adelante se necesita un folio por sucursal o por serie, la clave del bloqueo y la consulta cambiarían; el `CHECK` de formato habría que revisarlo (afecta P15).

---

## P23. Acceso de FastAPI y RLS: el propietario tampoco pasa por RLS (APROBADO — 2026-10-05)

> **Resuelve la decisión bloqueante B7** del plan `backend/docs/PLAN_FASE3_4.md`. La corrección es **documental**: no cambió ninguna política ni una línea de código de la aplicación.

### Contexto

- El comentario de `supabase/migrations/14_enable_rls.sql` afirmaba que "`service_role` (usado por FastAPI) NO se ve afectado por RLS bajo ninguna circunstancia".
- Esa frase era **incorrecta para este proyecto**: FastAPI **no** consume `service_role` ni pasa por PostgREST. Abre conexión directa a PostgreSQL con el rol `postgres` (`app/core/db.py`, `DATABASE_URL`).
- El frontend tampoco habla con Supabase directamente: toda la aplicación web consume la API.

### Decisión

- FastAPI conecta como **propietario (owner) de las tablas**, y PostgreSQL **no aplica RLS al owner** salvo que se use `FORCE ROW LEVEL SECURITY`, que el proyecto no usa.
  Por lo tanto **FastAPI tampoco pasa por RLS**: el propietario los ignora.
- El texto corregido dice exactamente eso y aclara que `service_role` vía PostgREST **no se usa** en este proyecto.
- **Consecuencia de seguridad**: la autorización **no** descansa en RLS, sino en `requiere()` y las capacidades por rol (P14) aplicadas en cada endpoint. RLS queda como red de seguridad para el resto de superficies.

### Consideraciones

- **RLS se mantiene habilitada** en las tablas de `public`: sigue siendo útil frente al acceso del cliente con la `anon` key y frente a Realtime, que sí pasan por RLS.
- Si en el futuro FastAPI conectara con un rol **no propietario**, las políticas de `14_enable_rls.sql` **sí** se aplicarían y habría que revisar el rendimiento de las consultas.
- El esquema `test` de las pruebas de integración (P20) tampoco habilita RLS, por la misma razón: las pruebas conectan como propietario y la autorización se verifica en la capa de FastAPI.

---

## P24. Límite transaccional: SAVEPOINT en el servicio y `commit` en el request (APROBADO — 2026-10-05)

### Contexto

- El plan `backend/docs/PLAN_FASE3_4.md` exige atomicidad en el alta de producto: producto + existencia + movimiento inicial, o nada.
- Había dos lecturas posibles: `commit`/`rollback` dentro de cada servicio, o una transacción abierta durante todo el request.
- La segunda era **incorrecta** en este proyecto: `get_db_session` es una dependencia de FastAPI compartida por todos los endpoints, y un `commit` por endpoint es frágil de mantener.

### Decisión (elegida por el usuario)

- **Los servicios usan SAVEPOINT** (`session.begin_nested()`), no transacción completa. Así una operación atómica de negocio se revierte sola sin tocar el resto de la transacción abierta.
- **`get_db_session` es la unidad de trabajo**: hace `commit()` al salir del request y `rollback()` si el handler lanza una excepción. Es el único lugar que decide confirmar.
- Beneficio directo: los tests de integración pueden **envolver cada prueba en una transacción y hacer `rollback` al final**, conservando el `commit` del código de producción sin ensuciar la base.

### Consideraciones

- Un fallo dentro de un SAVEPOINT no invalida la transacción exterior, pero **deja los locks tomados hasta el commit/rollback final**: por eso los servicios no capturan errores de BD sin loguear ni re-lanzar.
- Cualquier servicio que se cierre a sí mismo con `commit()` violaría esta decisión y rompería las pruebas por rollback.

---

## P25. Ajuste de inventario: dirección, forma del request y contrato de los GET (APROBADO — 2026-10-06)

### Contexto

- La Fase B (`backend/docs/PLAN_FASE3_4.md`) define `POST /api/inventario/ajustes` y su regla 8 pide `movimiento_inventario` con `tipo='ajuste'` y `referencia_tipo='ajuste'`, pero **no dice cómo se expresa si el stock sube o baja**.
- El DDL real impone dos restricciones: `chk_movimiento_cantidad CHECK (cantidad > 0)` y **ninguna columna de signo**. Con `tipo='ajuste'` fijo, la dirección del cambio quedaría solo en el texto de la nota y la bitácora dejaría de ser reconstruible.
- Tampoco estaban definidos los campos de `ExistenciaAjuste` (el plan la lista pero no la especifica) ni los filtros/respuesta de `GET /api/inventario/existencia` y `GET /api/inventario/movimientos`.

### Decisión (elegida por Fernando el 2026-10-06)

1. **El request manda un delta con signo y `tipo` codifica la dirección.** `ExistenciaAjuste.cantidad` es un delta firmado (positivo suma, negativa resta). El servicio escribe `tipo='entrada'` si sube y `tipo='salida'` si baja, siempre con `referencia_tipo='ajuste'` y `movimiento.cantidad = |delta|`. **Esto desvía la letra de la regla 8 del plan** (que pedía `tipo='ajuste'`): se eligió porque es la única lectura que deja la bitácora reconstruible sin ambigüedad. `tipo='ajuste'` sigue siendo un valor válido del CHECK y queda disponible si más adelante se necesita marcarlo de otra forma.
2. **`ExistenciaAjuste` vive en `app/schemas/existencia.py`** (donde el plan la lista) con `producto_id`, `cantidad` y `nota`. `extra="forbid"`; `nota` no puede quedar vacía tras `strip()`; `cantidad` no puede ser 0. **Si el producto no tiene fila en `existencia`** (alta con cantidad inicial 0), el ajuste **la crea** con `INSERT ... ON CONFLICT`, en vez de responder 404.
3. **Los dos GET**: `GET /api/inventario/existencia` devuelve la lista **global** de existencias (todas las filas, todas las sucursales) con filtro opcional `producto_id`; `GET /api/inventario/movimientos` devuelve la lista paginada (`limite` default 50 `ge=1 le=100`, `desplazamiento` `ge=0`, igual que productos) con filtro opcional `producto_id`, orden `fecha DESC`. El schema `MovimientoRead` replica las columnas de la tabla, sin campos derivados.

### Consideraciones

- **P19 sigue intacta**: ningún request expone `almacen_id`; todo ajuste va al almacén `ALMACEN_PREDETERMINADO`.
- Un ajuste que dejaría `existencia.cantidad < 0` se rechaza con **409** (`StockInsuficienteError`) **antes** de escribir, dentro del SAVEPOINT: no queda ni fila de existencia tocada ni movimiento. El mensaje nombra el producto y las unidades disponibles.
- Si el producto no existe → **404** (se valida antes de tocar existencias).
- `POST /api/inventario/ajustes` responde **201**, por consistencia con los otros POST que crean una fila (`movimiento_inventario`).
- Los listados solo devuelven **filas de `existencia`**: un producto alta con cantidad 0 no aparece, porque no tiene fila. La cantidad 0 de esos productos ya es visible en `GET /api/productos` (`existencia` con `COALESCE`).

---

## B6. Sugerencias con promedio móvil de 7 días, sin motor de IA (APROBADO — 2026-10-07)

> **Resuelve la decisión bloqueante B6** del plan `backend/docs/PLAN_FASE3_4.md` (§3) y habilita la Fase D. Opción (a) del plan.

### Contexto

- El DDL real impone `sugerencia.prediccion_id NOT NULL` + `UNIQUE (prediccion_id, producto_id)`: **no se puede crear una sugerencia sin una predicción previa**.
- La estrategia de IA está **aprobada** (P3/P3a/P13) pero `AGENTS.md` **prohíbe implementar el modelo** (código, dependencias, job) hasta autorización explícita.
- La Fase D necesita sugerencias de reabastecimiento funcionando **ya**, sin esperar esa autorización.

### Decisión

1. **Fila base de predicción** por cada producto activo al ejecutar `POST /api/sugerencias/generar`, usando la **línea base de la tesis**: `metodo='promedio_movil'`, `nivel_confianza='baja'`, `inicio_horizonte = hoy + 1`, `fin_horizonte = hoy + 7`, `observaciones_usadas = 7`, `intervalo_inf`/`intervalo_sup` en `NULL`.
2. **Promedio diario** = unidades vendidas por producto en los **últimos 7 días** (ventana calendario de 7 días terminando hoy, ventas `estado='activa'` sobre `detalle_venta`; los días sin venta cuentan como 0) → `demanda_pronosticada = promedio × 7`.
3. **`datos_ficticios` refleja la configuración** `DATOS_FICTICIOS` (nueva variable de entorno, default `false`) en lugar del `true` fijo que planteaba el plan. Con `DATOS_FICTICIOS=true` la predicción se marca `nivel_confianza='simulacion'`; sin él, `'baja'`. Coherente con P4: los ficticios jamás se presentan como reales.
4. **El motor de Scikit-learn (Random Forest / HistGB / Ridge) queda para una fase posterior**, hasta autorización explícita del usuario. Esta decisión **no** instala dependencias ni escribe el job.

### Consideraciones

- La generación corre en un **SAVEPOINT** (P24): si algo falla, no queda media corrida escrita.
- `cantidad_sugerida = max(0, demanda_pronosticada − stock_proyectado + umbral_minimo)`, a 2 decimales; solo se crea la sugerencia si es `> 0`.
- **No se duplica**: si el producto ya tiene una sugerencia `pendiente`, no se crea otra (la predicción de la corrida sí se registra, como traza del pronóstico del día).
- La notificación generada es **una sola por corrida**, tipo `sugerencia_compra` y `usuario_id NULL` (general). Las alertas de stock/vencimiento **no** escriben en `notificacion` en esta fase: siguen bajo demanda desde `GET /api/alertas/*`.
- **Desviaciones respecto del plan §8** (aplicada la especificación de la Fase D): el plan declara `GET /api/notificaciones` con `SUGERENCIAS_VER`, `POST /api/notificaciones/{id}/leer` y `POST /api/sugerencias/{id}/atender|/descartar`; se implementa `ALERTAS_VER` para notificaciones, `PATCH /api/notificaciones/{id}/leida`, `PATCH /api/sugerencias/{id}` con `{"estado": ...}` y el alta `POST /api/sugerencias/generar` con `PREDICCION_VER`. Las pruebas van en un único `tests/test_fase_d.py`.

---

## B5. Comprobante de venta en HTML imprimible, sin dependencias nuevas (APROBADO — 2026-10-07)

> **Resuelve la decisión bloqueante B5** del plan `backend/docs/PLAN_FASE3_4.md` (§3) y habilita el comprobante de la Fase E. Opción (a) del plan.

### Contexto

- P8 exige un comprobante **imprimible y descargable en PDF**, pero el proyecto **no tiene ninguna librería PDF instalada** y agregar una es una decisión de arquitectura (dependencia nueva).
- El comprobante es un **recibo interno** con folio único: **no** es factura tributaria ni está sujeto a SAT/FEL (P8).

### Decisión

- **Vista HTML del recibo con estilos de impresión** (`@media print`), y la descarga a PDF se logra con **imprimir del navegador** (`window.print()` → "Guardar como PDF"), que es el camino nativo del navegador.
- **Sin dependencias nuevas**: no se agrega `reportlab`, `weasyprint` ni ninguna otra librería de PDF.

### Consideraciones

- El HTML se renderiza **desde los datos ya guardados de la venta** (folio, fecha, líneas, subtotal, descuento, total), nunca recalculados.
- Si más adelante se necesita un PDF generado en servidor (numeración, marca de agua, envío automático), eso será una **dependencia nueva y requerirá aprobación aparte**; esta decisión no la bloquea.
- La vista debe mostrar explícitamente que es un **recibo interno no tributario**, sin autorización SAT.

---


Registradas aquí, **sin corregir silenciosamente** ni el plan ni el código. Las ya resueltas se marcan con **RESUELTO + fecha** (queda el texto original bajo cada una para no perder el origen de la discrepancia):

- **`limite` en la paginación — RESUELTA el 2026-10-06**: el "piso 50" del plan se interpreta como el **valor por defecto** (ya implementado: `default=50, ge=1, le=100`), no como un mínimo obligatorio. **No se cambió el código.** Texto original de la discrepancia: §2.4 dice "`limit` obligatorio con piso 50", pero el criterio de aceptación invoca `GET /api/productos?q=shampoo` **sin** `limit`. Sigue admitiendo `limit=1`.
- **`codigo` del producto — RESUELTO el 2026-10-06**: el plan declara `UNIQUE` pero no dice si `codigo` es inmutable. Se resolvió aplicando `model_config = ConfigDict(extra="forbid")` (Pydantic v2.13.5) a los **3 schemas `Update`** — `ProductoUpdate`, `CategoriaUpdate` y `ProveedorUpdate` —, de modo que cualquier campo no declarado (`codigo`, `id`, `created_at`, …) devuelve **422** en vez de descartarse en silencio. Cubierto por `TestCamposNoEditables` en `test_productos.py`, `test_categorias.py` y `test_proveedores.py`. El plan sigue sin definir la inmutabilidad de `codigo` como regla de negocio: ahora el intento es explícito (422), pero queda pendiente si la API debe aceptar y actualizar ese campo en el futuro.
- **Alta con `cantidad_inicial=0` no creaba la fila `existencia` — RESUELTA el 2026-10-06**: el servicio guardaba la fila tras `if cantidad_inicial > 0`, de modo que un producto nuevo sin entradas no tenía fila en `existencia` y desaparecía de `GET /api/inventario/existencia` —invisible para las alertas de bajo stock (requerimiento funcional 3). Se corrigió `app/services/productos.py`: **la fila se crea siempre** (con `cantidad=0` si no hay entrada) y **solo el `movimiento_inventario` sigue siendo condicional**, porque su `CHECK (cantidad > 0)` lo impide. Verificado en la base: no hay ningún trigger de `producto` que cree `existencia`, y `chk_existencia_cantidad` acepta `0`. Cubierto por `test_cantidad_cero_no_crea_movimiento` (reforzado) y `test_producto_con_cantidad_cero_sigue_apareciendo_en_el_listado`.
- **`ExistenciaAjuste` — RESUELTA el 2026-10-06 (P25)**: se creó en `app/schemas/existencia.py` junto al endpoint de ajuste de stock, con `producto_id`, `cantidad` y `nota`. Texto original de la discrepancia: el plan la lista en `app/schemas/existencia.py`, pero ningún endpoint ni servicio de la Fase A la consume (solo hay lectura de existencias); no se creó entonces para no dejar código muerto.
- **Barra final en las rutas**: los decoradores del ejemplo del plan (`@router.get("/")` con `prefix="/api/productos"`) publicaban `/api/productos/` y obligaban a un **307** desde la URL del criterio de aceptación. Se registraron con `@router.get("")` para que la ruta canónica sea `/api/productos`, tal como documenta la tabla de endpoints del plan.
- **`a_decimal()` docstring vs código — RESUELTA el 2026-10-06**: **el código es correcto**: acepta `float` a propósito solo cuando su valor es exactamente representable (`1.5`, `2.0`), comportamiento verificado por tests (`test_dinero.py`). Se corrigió el **docstring** en `app/core/dinero.py` para describir el comportamiento real en vez de negarlo. Texto original de la discrepancia: acepta un `float` si su valor exacto es representable (`1.5`, `2.0`), aunque su docstring afirmaba que un `float` nunca es entrada válida.

---

## Decisiones aún pendientes (requieren confirmación)

**Resueltas el 2026-09-21 (APROBADAS)**: R1 (P3/P3a, selección de modelo + plan de 18 puntos), R2/R9 (P14, matriz de 18 capacidades con la modificación de anulación propia del padre), R3/R10 (P15, esquema inicial + 10 respuestas), R6/R11 (P16, versiones/pin-range), R8 (P13, suficiencia + confianza por evidencia).

**Resueltas el 2026-10-05 (APROBADAS)**: P19 (almacén por defecto), P20 (esquema `test` para pruebas de integración), P21 (redondeo del dinero), P22 (folio concurrente), P23 (acceso de FastAPI y RLS), P24 (límite transaccional: SAVEPOINT + `commit` en el request). Las cuatro primeras corresponden a las decisiones bloqueantes B1–B4 del plan `backend/docs/PLAN_FASE3_4.md` y P23 a B7; **P24 no corresponde a B1–B7**: surgir de una pregunta de arquitectura sobre el límite transaccional, que el plan no cubría.

**Resueltas el 2026-10-07 (APROBADAS)**: **B6** (sugerencias con promedio móvil de 7 días como línea base, `nivel_confianza='baja'` o `'simulacion'` con `DATOS_FICTICIOS`, motor Scikit-learn para fase posterior) y **B5** (comprobante en HTML con estilos de impresión, descarga a PDF vía imprimir del navegador, sin dependencias nuevas). Secciones **B6** y **B5** de más arriba.

Siguen pendientes:
- **R4. Estrategia offline definitiva** y su tecnología (P2): se documentará cuando llegue el momento; no bloquea la primera versión.
- **R5. Detalles de despliegue/hosting** (P12): cuando la aplicación esté avanzada.
- **R7/R12. Supabase MCP (P17)**: CONFIGURADO y AUTENTICADO (2026-09-21). **Project Ref `spozipecnvhmchxvmsqt` aportado y aplicado** (2026-09-21). Pendiente únicamente: **reiniciar OpenCode** (manual, hecho por el usuario) para cargar las herramientas MCP scoped al proyecto en la sesión. No crear ni modificar objetos en Supabase sin informar antes.
- **Inicio del desarrollo**: crear código (React/FastAPI/Node/Supabase/IA), instalar dependencias o crear tablas queda **prohibido hasta orden explícita** del usuario.

---

## Criterios estables del proyecto (no son pendientes)

- **D1. Alcance de esta fase**: solo aplicación Web. React Native queda para fase posterior; prohibido código/carpetas/servicios móviles. La arquitectura se mantiene compatible con una futura app móvil.
- **D2. Stack confirmado**: React.js (web) · FastAPI (API principal) · Node.js (tareas livianas/serverless ocasional) · Supabase (PostgreSQL, Auth, Storage) · Scikit-learn (predicción).
- **D3. Jerarquía de autoridad**: 1) instrucciones explícitas del usuario · 2) requisitos confirmados del proyecto · 3) código y arquitectura existente · 4) AGENTS.md · 5) reglas de `.opencode/rules/` · 6) este documento · 7) convenciones generales de frameworks/lenguajes.
- **D4. Regla "no inventar"**: si algo no está definido, detectar la ambigüedad, explicar qué falta, proponer alternativas y pedir confirmación antes de decisiones importantes.
- **D5. Entidades y requerimientos de referencia**: ver `AGENTS.md` (entidades de la tesis + 6 requerimientos funcionales del Cap. IV + predicción con job diario).
- **D6. Fuentes de verdad**: tesis `Fernando Gonzalez PG 2 UNIVERSIDAD MARIANO GALVEZ DE GUATEMALA.docx` (raíz) + decisiones documentadas aquí.