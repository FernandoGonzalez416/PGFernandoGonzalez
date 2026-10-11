# Guion de Demostración — Plataforma Inteligente de Inventarios

**Proyecto:** Plataforma inteligente basada en la nube con capacidad offline para la gestión de inventarios y reabastecimiento en tiendas cosméticas
**Caso de estudio:** Familia de la Cruz — Villa Nueva, Guatemala
**Versión:** F4 (Panel, Alertas, Reportes, Sugerencias, Notificaciones, **Predicción de demanda**)

---

## 1. Preparación previa

| Elemento | Detalle |
|----------|---------|
| **Backend** | `uvicorn app.main:app --reload --port 8000` (puerto 8000) |
| **Frontend** | `npm run dev` (puerto 5173 por defecto) |
| **Credenciales demo** | Ver sección 2 |
| **Datos de prueba** | 20 productos `SIM-0xx`, 168 ventas, 3 anuladas, 4 ajustes, 372 movimientos, 4 alertas stock bajo, 1 vencido (`SIM-005`), 2 por vencer (`SIM-006` +7d, `SIM-010` +9d) |

---

## 2. Cuentas de usuario

| Rol | Email | Password | Capacidades clave |
|-----|-------|----------|-------------------|
| **Propietario** | `propietario@prueba.com` | `123456` | Todo excepto `prediccion:ver` y `usuarios:gestionar` |
| **Padre** | `padre@prueba.com` | `123456` | Operación completa (ventas, alertas, sugerencias), anula **solo sus ventas** |
| **Admin** | `fer@gmail.com` | `123456` | Todas las capacidades incluyendo `prediccion:ver`, `usuarios:gestionar` |

> **Nota:** El padre ve la campana, alertas, sugerencias y puede atender/descartar, pero **no** ve "Generar sugerencias" (requiere `prediccion:ver`).

---

## 3. Recorrido guiado (≈ 12 min)

### 3.1 Login y Panel (2 min)

1. Abrir `http://localhost:5173`
2. Iniciar sesión como **Propietario** (`propietario@prueba.com` / `123456`)
3. **Panel** (`/`): observar los 5 bloques:
   - **Ventas de la semana**: total Q, nº ventas, gráfico SVG 7 días (hover en barras), enlace a Ventas
   - **Alertas**: contador stock bajo + vencimientos, lista con píldoras (Agotado/Bajo/Vencido/Próximo), enlace a Alertas
   - **Más vendidos (semana)**: top 5 con barras horizontales, enlace a Reportes
   - **Últimas ventas**: 5 últimas con folio y monto, enlace a Ventas
   - **Sugerencias de compra**: contador pendientes, lista con prioridad (alta/media/baja), enlace a Sugerencias
4. Cambiar a **Padre** (cerrar sesión → `padre@prueba.com`) → el bloque "Sugerencias" **no aparece** (sin `sugerencias:ver`)

### 3.2 Alertas de inventario (2 min)

1. Ir a **Alertas** (`/alertas`) como Propietario
2. Tabla con columnas: Producto, Código, Estado (píldora), Detalle, Ver
3. Píldoras semánticas:
   - 🔴 **Agotado** (existencia 0)
   - 🟠 **Bajo** (existencia > 0 pero < umbral)
   - 🔴 **Vencido** (días restantes ≤ 0)
   - 🟠 **Por vencer** (días restantes > 0)
4. Click en "Ver producto" → navega a Productos (pendiente filtro)

### 3.3 Reportes — Productos más vendidos (2 min)

1. Ir a **Reportes** (`/reportes`)
2. Filtros: Periodo (7/30/60 días) + fecha Desde/Hasta + botón Aplicar
3. Tabla: ranking, producto, código, cantidad vendida (barra horizontal), total Q
4. Probar error 422: poner fecha Desde > Hasta → mensaje "fecha_fin no puede ser menor que fecha_inicio"

### 3.4 Sugerencias de compra (2.5 min)

1. Ir a **Sugerencias** (`/sugerencias`) como **Admin** (`fer@gmail.com`)
2. Mensaje fijo visible: *"Generación: modelo seleccionado por validación temporal (Random Forest, Gradient Boosting, Ridge vs. promedio móvil); confianza según evidencia P13."*
3. Botón **"Generar sugerencias"** (requiere `prediccion:ver`) → toast "Sugerencias generadas: N (predicciones: M) por_metodo: {...}"
4. Filtro estado: Pendientes / Atendidas / Descartadas / Todas
5. Tabla: producto, código, **Método** (Random Forest, Gradient Boosting, Regresión Ridge, Promedio móvil), **Confianza** (píldora: Simulación/Baja/Alta), cantidad sugerida, prioridad, demanda/stock, fecha, acciones
6. **Atender** / **Descartar** (requiere `sugerencias:atender`) → toast confirmación
7. Intentar atender una ya atendida → error 409 toast *"Sugerencia no está pendiente"*
8. Cambiar a **Propietario** → botón "Generar" **no visible**, pero puede Atender/Descartar

### 3.5 Predicción de demanda (2 min)

1. Ir a **Predicción de demanda** (`/predicciones`) como **Admin** (`fer@gmail.com`)
   - *Solo visible en sidebar para rol con `prediccion:ver` (Admin)*
2. **Aviso fijo visible**: *"Datos de simulación: la precisión mostrada valida el funcionamiento del modelo, no su desempeño real en el negocio. Con historial real el modelo se recalibra (P13)."*
3. **Resumen superior**: tarjetas con "Productos con modelo ML", "Productos en línea base", "Mejora media vs. línea base"
4. **Tabla** con columnas: Producto, Código, Método, Demanda 7 días (con intervalo), MAE modelo/base, Mejora %, Confianza (píldora), Obs. usadas
5. **Click en fila** → panel lateral de detalle:
   - Gráfico SVG: historial 60 días (línea continua) + pronóstico 7 días (línea punteada) + banda de intervalo
   - Ejes rotulados, descripción para lector de pantalla, tabla alternativa accesible
   - Tarjetas: Modelo elegido, MAE modelo, MAE línea base, Mejora vs. base, Obs. usadas
   - Si cayó a línea base: motivo en lenguaje llano (ej. "el modelo no supera a la línea base")
6. Botón **"Actualizar predicciones"** → llama a `POST /api/sugerencias/generar`, muestra toast con conteo por método, recarga tabla
7. Cambiar a **Propietario** → opción "Predicción de demanda" **no aparece** en sidebar

### 3.6 Notificaciones y Campana (1.5 min)

1. Click en **campana** (🔔) en Topbar → panel con badge contador
2. Lista: tipo, mensaje, fecha; click en item → marca leída, badge decrementa
3. Ir a **Notificaciones** (`/notificaciones`)
3. Filtro: Todas / Sin leer / Leídas
4. Botón **"Marcar todas como leídas"** → toast + contador a 0
5. Click "Ver alertas" / "Ver sugerencias" → navegación contextual

### 3.6 Navegación y UX (1 min)

1. **Sidebar** (colapsable en móvil): 5 grupos — Inicio, Catálogo, Ventas, Inventario, Análisis (ahora incluye **Predicción de demanda** y Notificaciones)
2. **Títulos de página** en AppLayout: Panel, Productos, Ventas, Alertas, Reportes, Sugerencias, Notificaciones
3. **Responsive**: redimensionar <768px → tablas a tarjetas, sidebar off-canvas
4. **Toolbar Productos**: "Nuevo producto" no tapa el buscador en móvil (flex-wrap)
5. **ErrorBoundary**: forzar error (ej. romper import) → pantalla "Algo salió mal" + botón Recargar

---

## 4. Puntos clave a destacar

| Característica | Detalle técnico |
|----------------|-----------------|
| **Arquitectura** | Frontend/Backend separados, lazy loading + Suspense + ErrorBoundary |
| **RBAC** | `RequireCapacidad` en rutas + `useCan` en componentes |
| **Gráfico SVG** | Accesible (`role="img"`, `aria-label` con resumen textual), barras escaladas |
| **Píldoras semánticas** | Solo 3 colores de estado (ámbar/rojo/verde) + prioridad |
| **Mensaje IA** | Texto fijo en Sugerencias: "promedio móvil 7 días, confianza baja; IA no activa" |
| **Error 409** | Toast con mensaje exacto del backend ("Sugerencia no está pendiente") |
| **Campana** | Badge temps real, click marca leída, sin polling (refetch en mount + pathname) |
| **Responsive** | 390/768/960/1080px, `prefers-reduced-motion`, focus-visible |
| **Motion** | Entrada escalonada, hover/tap scale(0.97), curvas cubic-bezier custom |

---

## 5. Datos de prueba relevantes (para ver en demo)

| Código | Nombre | Stock | Umbral | Estado | Vence en |
|--------|--------|-------|--------|--------|----------|
| SIM-001 | Labial mate | 2 | 5 | Bajo | — |
| SIM-005 | Base líquida | 0 | 3 | **Agotado** | **Hoy (vencido)** |
| SIM-006 | Rubor crema | 8 | 5 | OK | +7 días |
| SIM-010 | Perfume 50ml | 12 | 10 | OK | +9 días |

> Ventas demo: 168 registradas, 3 anuladas, 4 ajustes de inventario, 372 movimientos.

---

## 6. Problemas conocidos / Limitaciones F3

| Item | Descripción |
|------|-------------|
| IA predicción | Implementada (Random Forest, Gradient Boosting, Ridge vs. promedio móvil, validación temporal, confianza por evidencia P13) |
| Offline/PWA | No implementado en F3 (arquitectura preparada) |
| App móvil | Fuera de alcance (React Native fase posterior) |
| VentaDetalle anulable | Botón "Anular" usa estado `'registrada'` vs real `'activa'` (discrepancia F2) |
| Test integración backend | Lento (~15 min) — no ejecutar en CI normal |

---

## 7. Checklist post-demo

- [ ] Verificar que todos los toasts aparecen y desaparecen
- [ ] Confirmar que la campana actualiza badge sin recargar
- [ ] Probar responsive en móvil real (Chrome DevTools device toolbar)
- [ ] Validar que el padre **no** ve "Generar sugerencias" pero sí atiende/descarta
- [ ] Comprobar que error 422 en Reportes muestra mensaje claro
- [ ] Verificar `prefers-reduced-motion` desactiva animaciones

---

*Documento generado para defensa de proyecto de graduación — Universidad Mariano Gálvez de Guatemala.*