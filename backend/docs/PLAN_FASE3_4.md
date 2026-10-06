# Plan de implementación — Backend Fase 3/4

**Fecha:** 2026-10-05
**Alcance:** terminar el backend (FastAPI) para los 7 requerimientos funcionales del Cap. IV de la tesis.
**Estado:** documento de plan. **No implementa código.** Nada de lo aquí descrito está commiteado.

---

## 1. Punto de partida verificado

Comprobado contra el proyecto Supabase real (`spozipecnvhmchxvmsqt`) y contra el código del repo el 2026-10-05.

### Ya existe y funciona

| Pieza | Ubicación | Estado |
|---|---|---|
| Esquema de 13 tablas | `supabase/migrations/00..14` | Aplicado en Supabase |
| RLS habilitado, denegación por defecto | `supabase/migrations/14_enable_rls.sql` | Aplicado |
| Sesión async SQLAlchemy | `backend/app/core/db.py` | Commiteado |
| Configuración por entorno | `backend/app/core/config.py` | Commiteado |
| Autenticación JWT (JWKS ES256/RS256) | `backend/app/core/security.py` | Commiteado, validado E2E |
| Matriz de capacidades P14 (18 capacidades) | `backend/app/core/capacidades.py` | Commiteado |
| Dependencia `requiere(capacidad)` | `backend/app/core/permissions.py` | Commiteado |
| Endpoint de verificación | `backend/app/api/me.py` + `main.py` | Commiteado, `HTTP 200` |
| Pruebas | `backend/tests/` (42) | 42 passed |

### Restricciones reales de la base de datos (mueven el diseño)

Estas NO son suposiciones: se leyeron de los CHECK/UNIQUE del esquema vivo.

| Tabla | Restricción | Consecuencia en el backend |
|---|---|---|
| `venta` | `CHECK (folio ~ '^F-\d{4}-\d{4,}$')` | El folio es `F-AAAA-NNNN` con **mínimo 4 dígitos**, no `F-AÑO-SECUENCIAL` libre |
| `venta` | `UNIQUE (folio)` | La generación de folio debe ser segura ante concurrencia |
| `venta` | `CHECK (total = subtotal - descuento)`, `0 <= descuento <= subtotal` | El backend **no** puede redondear total por su cuenta: debe cuadrar exacto |
| `venta` | `CHECK (estado <> 'anulada' OR motivo_anulacion IS NOT NULL)` | El motivo de anulación es obligatorio a nivel de BD |
| `detalle_venta` | `CHECK (subtotal = cantidad * precio_unitario)` | El subtotal de la línea es exacto, sin redondeo independiente |
| `detalle_venta` | `UNIQUE (venta_id, producto_id)` | **Un producto no puede repetirse en la misma venta**: hay que fusionar líneas duplicadas |
| `movimiento_inventario` | `CHECK (cantidad > 0)` | No existen cantidades negativas: una reversión es `tipo='entrada'`, no un `-5` |
| `movimiento_inventario` | `tipo IN ('entrada','salida','ajuste')`, `referencia_tipo IN ('venta','compra','ajuste','vencimiento','devolucion','inicial')` | Enumeraciones fijas a respetar |
| `existencia` | `UNIQUE (producto_id, almacen_id)`, `CHECK (cantidad >= 0)` | El stock es por producto+almacén y nunca negativo |
| `producto` | `CHECK (umbral_minimo >= 0)`, `CHECK (dias_vencimiento_aviso >= 0)` | Base de las 2 alertas del Cap. IV |
| `sugerencia` | `prediccion_id` **NOT NULL** + `UNIQUE (prediccion_id, producto_id)` | **No se puede crear una sugerencia sin una predicción previa** |
| `notificacion` | `tipo IN ('bajo_stock','vencimiento_proximo','sugerencia_compra','sistema')` | Enumeración fija |
| `prediccion` | `nivel_confianza IN ('alta','baja','simulacion')`, `datos_ficticios NOT NULL` | La distinción simulación/real es de esquema |

### Datos actuales (bloqueante)

```
almacen 0 · categoria 0 · proveedor 0 · producto 0 · existencia 0
cliente 0 · venta 0 · movimiento_inventario 0 · notificacion 0
prediccion 0 · sugerencia 0 · usuario 1
```

**`almacen` tiene 0 filas y `existencia.almacen_id` es NOT NULL con FK a `almacen`.** Sin un almacén no se puede registrar ni una existencia ni una venta. Esto obliga a sembrar datos base antes de la Fase B, y es la razón de la **Fase 0**.

### RLS y autorización (realidad, no suposición)

`14_enable_rls.sql` deja las 13 tablas en denegación total para `anon`/`authenticated`. El backend **no** usa `service_role`: `DATABASE_URL` conecta directo como `postgres`, que es propietario de las tablas y por tanto **no** pasa por RLS.

Consecuencias que el plan asume y hay que documentar:

1. La **autorización P14 vive únicamente en FastAPI** (`requiere()`). RLS es la segunda barrera, para acceso directo del cliente, y hoy está en "denegado".
2. El **frontend no puede leer datos de Supabase directamente** con la publishable key: todo pasa por la API. Esto es coherente con `arquitectura.md`.
3. Hay una **discrepancia documental**: el comentario de `14_enable_rls.sql` dice "service_role (usado por FastAPI)", pero FastAPI conecta como `postgres`. Corregir el comentario (o la intención) es una decisión, ver §3.

---

## 2. Reglas transversales (aplican a todas las fases)

1. **Nada de lógica de negocio en los routers.** Cada router valida con Pydantic, llama a un servicio y devuelve. La lógica vive en `backend/app/services/`.
2. **Excepciones de dominio tipadas** en `backend/app/core/errores.py`, mapeadas a HTTP **una sola vez** en un handler global. El envelope se mantiene `{"detail": "..."}` porque es el contrato que ya usa `/api/me` y el que espera el frontend; **no se cambia**.
3. **Excepciones previstas**: `ProductoNoEncontradoError` (404), `CodigoProductoDuplicadoError` (409), `StockInsuficienteError` (409), `FolioDuplicadoError` (409), `VentaNoAnulableError` (409), `AnulacionNoPermitidaError` (403), `VencimientoInvalidoError` (422), `CapacidadInsuficienteError` (403, la produce `requiere()`).
4. **Convención de routers (a estandarizar en Fase 0).** Hoy `/api/me` lleva el prefijo dentro del decorador, lo que hace muy fácil duplicarlo. Se adopta:
   ```python
   # backend/app/api/productos.py
   router = APIRouter()
   @router.get("/")                       # ruta sin prefijo
   # backend/app/main.py
   app.include_router(productos_router, prefix="/api/productos", tags=["productos"])
   ```
   En Fase 0 se corrige `me.py` a esta convención sin cambiar la URL pública (`/api/me`).
5. **Paginación y búsqueda** desde el inicio en los listados (`limit`/`offset`), para no reescribir después.
6. **Soft delete**: catálogo se desactiva con `activo = false`. Prohibido `DELETE` en `venta`/`detalle_venta` y `DELETE`/actualización destructiva en `movimiento_inventario`.
7. **Datos ficticios siempre etiquetados** (P4). La semilla se ejecuta en un entorno explícito y toda salida se marca como simulación.
8. **Cero `any` implícito, Pydantic en el borde y reglas de negocio en el servicio** (`backend.md`).
9. **Nada de comitear sin autorización del usuario.**

---

## 3. Decisiones pendientes que BLOQUEAN la implementación

Regla "no inventar" (`AGENTS.md`). Se identifican como **B1–B7** ("bloqueante") para no chocar con los criterios estables **D1–D6** de `DECISIONES.md`.

### Resueltas (2026-10-05)

| # | Decisión | Resolución | Registrada en |
|---|---|---|---|
| B1 | **Almacén por defecto.** | Un único almacén "Principal" sembrado por `scripts/semilla.py`, resuelto con la config `ALMACEN_PREDETERMINADO`. Multi-almacén fuera de esta fase. | **P19** |
| B2 | **Base de datos de pruebas.** | Esquema `test` en el mismo Supabase con el DDL de las migraciones; cada prueba de integración dentro de una transacción que revierte. Marcadas con `pytest.mark.integracion`, se omiten sin `DATABASE_URL_TEST`. | **P20** |
| B3 | **Folio concurrente.** | `pg_advisory_xact_lock` + `MAX(folio)` del año actual, calculado dentro de la misma transacción de la venta, antes del `INSERT`. **No requiere cambios al esquema P15**: el `CHECK` de formato y el `UNIQUE` de folio ya existen. | **P22** |
| B4 | **Redondeo de dinero.** | 2 decimales `ROUND_HALF_UP` en `app/core/dinero.py`. Precios cuantizados al guardar; subtotal de línea **exacto**; el redondeo ocurre una sola vez, en los totales de la venta. | **P21** |

**Consecuencia:** la Fase 0 ya puede escribirse y la Fase B ya tiene resuelto el mecanismo de folio. B2 añade un entregable que el plan no tenía: crear el esquema `test` y su fixture transaccional en `conftest.py`.

### Pendientes

| # | Decisión | Bloquea | Opciones |
|---|---|---|---|
| B5 | **Comprobante en PDF** (P8 exige imprimible y descargable). Hoy no hay ninguna librería PDF instalada y agregar una es decisión de arquitectura. | Fase E | (a) vista HTML de recibo + impresión del navegador, **sin dependencia nueva** (recomendado); (b) agregar `reportlab` |
| B6 | **Sugerencia sin motor de IA.** `sugerencia.prediccion_id` es NOT NULL y la estrategia de IA está aprobada pero **no autorizada a implementar** (P3/P13). | Fase D | (a) crear la predicción **base** (`metodo='promedio_movil'`, `nivel_confianza='baja'`, `datos_ficticios=true`), que es la regla de la tesis, **sin ML**; (b) dejar `Sugerencia` sin CRUD hasta autorizar el motor |
| B7 | **RESUELTA — P23 (2026-10-05).** Opción (a): se corrigió el comentario a "conexión directa como propietario (`postgres`), que tampoco pasa por RLS; no se usa `service_role` vía PostgREST". No cambió ninguna política ni código. | — | — |

Además, sin definir y **no bloqueante**: destinatario de las notificaciones (¿solo al dueño? ¿a todos los activos?) y si `Cliente` entra en esta fase o queda para después (afecta el tamaño de la Fase E).

---

## 4. Fase 0 — Cimientos, convención y datos base

**Objetivo:** dejar el backend listo para que las fases siguientes solo agreguen dominio. Sin esto, la Fase B no puede funcionar (`almacen` vacío). Depende de **B1 (P19)**, **B2 (P20)** y **B4 (P21)**, ya resueltas.

**Entidades:** `almacen`, `usuario` (solo lectura), `categoria` (mínimo).

**Endpoints:** ninguno nuevo. Se normaliza `/api/me`.

**Archivos:**

| Archivo | Acción |
|---|---|
| `backend/app/core/errores.py` | **crear** — jerarquía de excepciones de dominio |
| `backend/app/main.py` | **modificar** — handler global de errores + `include_router` de cada router |
| `backend/app/core/config.py` | **modificar** — `ALMACEN_PREDETERMINADO` (P19) |
| `backend/app/api/me.py` | **modificar** — quitar `/api` del decorador, usar `prefix="/api"` |
| `backend/app/schemas/errores.py` | **crear** — modelo Pydantic del envelope |
| `backend/app/core/dinero.py` | **crear** — `CUANTIA` = `Decimal('0.01')`, `redondear()`, `a_decimal()` (P21) |
| `backend/scripts/semilla.py` | **crear** — siembra almacén por defecto + catálogo mínimo **ficticio etiquetado** |
| `backend/scripts/README.md` | **crear** — cómo ejecutar la semilla |
| `backend/tests/conftest.py` | **crear** — fixtures compartidos + fixture transaccional del esquema `test` (P20) |
| `backend/pytest.ini` | **modificar** — registrar el marcador `integracion` (P20) |
| `backend/tests/sql/00_test_schema.sql` | **crear** — DDL del esquema `test` replicando `supabase/migrations/` (P20). Va en `backend/tests/sql/`, **no** en `supabase/migrations/`, para que el flujo de migraciones no lo aplique a la base de la aplicación. |
| `backend/tests/test_integracion_esquema.py` | **crear** — verifica aislamiento `test` vs `public` y que las 13 tablas existen (P20) |
| `backend/tests/test_dinero.py` | **crear** |
| `backend/tests/test_errores.py` | **crear** |
| `supabase/migrations/15_*.sql` | **no se necesita**: B7 se resolvió documentalmente (P23), sin cambios de esquema |

**Reglas de negocio a resolver:**

1. `ALMACEN_PREDETERMINADO` (P19): la venta necesita un almacén y `existencia.almacen_id` es NOT NULL. El servicio lo resuelve desde la configuración; el cliente nunca manda `almacen_id`.
2. El manejo de `numeric` de PostgreSQL con SQLAlchemy async devuelve `Decimal` (P21); las sumas de `subtotal` deben **cuantizarse una vez** al final, nunca por línea, para no violar `chk_detalle_venta_calculo`.
3. La semilla debe ser **idempotente** (`ON CONFLICT DO NOTHING` / `INSERT ... WHERE NOT EXISTS`): ejecutarla dos veces no debe duplicar ni fallar. Debe sembrar el almacén "Principal" y un catálogo ficticio con `umbral_minimo > 0`.
4. La semilla **solo** crea el almacén y lo mínimo para poder probar. El catálogo ficticio completo va en Fase A.
5. **Esquema `test` (P20):** el DDL debe replicar el de `supabase/migrations/`. Cada prueba de integración corre en una transacción con rollback, marcada con `pytest.mark.integracion`, y se **omite** si falta `DATABASE_URL_TEST`. Nunca debe apuntar a la base de desarrollo.
6. **Alcance de los archivos:** `scripts/semilla.py` es una herramienta local, no un endpoint; no se expone por HTTP.

**Tests mínimos:** `redondear()` redondea_half_up en casos límite (0.005, 1.005, 2.675); `a_decimal()` acepta `str` y `Decimal` y rechaza `float` con decimales ambiguos; el handler global traduce cada excepción de dominio al código HTTP correcto y con envelope `{"detail": ...}`; la semilla es idempotente.

**Criterio de aceptación:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
Esperado: `0 failed` y los tests nuevos de `test_dinero.py` y `test_errores.py` en Passed.

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\semilla.py
.\.venv\Scripts\python.exe scripts\semilla.py   # segunda vez: no debe duplicar
```
Esperado: la primera imprime el almacén creado y `SIMULACION: datos ficticios`; la segunda imprime `0 creados` y termina sin error.

```powershell
cd backend
.\.venv\Scripts\python.exe -c "import app.main; print(sorted(app.main.app.openapi()['paths']))"
```
Esperado: `['/api/me', '/docs', '/docs/oauth2-redirect', '/health', '/openapi.json', '/redoc']` — confirmar que `/api/me` **no** se volvió `/api/api/me`.

---

## 5. Fase A — Producto, Categoría y Proveedor

**Cubre:** requerimientos 1 (registrar productos con nombre, categoría, cantidad, proveedor, fecha de ingreso, precio), 2 (consultar cantidad disponible por nombre, código o categoría) y 5 (proveedores con precios y condiciones de entrega).

**Entidades:** `producto`, `categoria`, `proveedor`, y la fila inicial de `existencia` + `movimiento_inventario` de tipo `inicial`.

**Endpoints:**

| Método | Ruta | Capacidad |
|---|---|---|
| GET/POST | `/api/productos` | `PRODUCTOS_CONSULTAR` / `PRODUCTOS_EDITAR` |
| GET/PATCH | `/api/productos/{id}` | `PRODUCTOS_CONSULTAR` / `PRODUCTOS_EDITAR` |
| GET | `/api/productos/{id}/existencia` | `STOCK_CONSULTAR` |
| GET/POST | `/api/categorias` | `PRODUCTOS_CONSULTAR` / `CATEGORIAS_GESTIONAR` |
| GET/PATCH | `/api/proveedores`, `/api/proveedores/{id}` | `STOCK_CONSULTAR` / `PROVEEDORES_GESTIONAR` |

`categoria` y `proveedor`: consulta abierta a los tres roles, escritura solo administrador y propietario (P14).

**Archivos:**

```
backend/app/api/productos.py        crear   (router delgado)
backend/app/api/categorias.py       crear
backend/app/api/proveedores.py      crear
backend/app/schemas/producto.py     crear   (ProductoCreate, ProductoUpdate, ProductoRead)
backend/app/schemas/categoria.py    crear
backend/app/schemas/proveedor.py    crear
backend/app/schemas/existencia.py   crear   (ExistenciaRead, ExistenciaAjuste)
backend/app/services/productos.py   crear   (CRUD + búsqueda + alta con existencia inicial)
backend/app/services/categorias.py  crear
backend/app/services/proveedores.py crear
backend/app/main.py                 modificar (include_router)
backend/tests/test_productos.py     crear
backend/tests/test_categorias.py    crear
backend/tests/test_proveedores.py   crear
backend/tests/test_busqueda.py     crear   (req. 2: nombre, código, categoría)
```

**Reglas de negocio a resolver:**

1. **`codigo` es UNIQUE.** El alta debe convertir la violación de unicidad en `CodigoProductoDuplicadoError` (409), nunca un 500.
2. **Alta de producto con cantidad inicial.** El requerimiento 1 pide registrar cantidad. Eso escribe **dos** tablas: `existencia` (cantidad) y `movimiento_inventario` (`tipo='entrada'`, `referencia_tipo='inicial'`, `usuario_id` = quien creó, `nota` con "Alta de producto"). **Debe ser una sola transacción** o la existencia queda sin traza.
3. **`fecha_vencimiento` es la fecha del lote activo**; `NULL` = no perecedero (P15, sin entidad `Lote`). Si se envía vencimiento, no puede estar en el pasado → `VencimientoInvalidoError`.
4. **`precio_venta` y `precio_costo` son `>= 0`** (CHECK). El precio de venta es el que usa la venta; el de costo, el margen en reportes. Validar en Pydantic **y** dejar el CHECK como última barrera.
5. **Búsqueda del requerimiento 2**: `GET /api/productos?q=…` debe buscar por `lower(nombre)` (usa `idx_producto_nombre`), por `codigo` exacto y por `categoria_id`. Los tres filtros son combinables y `limit` es obligatorio (piso 50).
6. **Desactivar, no borrar**: `PATCH /api/productos/{id} {"activo": false}`. Un producto **no** se puede desactivar si tiene existencias con cantidad mayor a 0 o ventas asociadas: se rechaza con 409, para no perder trazabilidad de los movimientos.
7. `activo = false` **excluye** el producto de la búsqueda de venta, pero **no** de los reportes históricos.

**Tests mínimos:** código duplicado → 409; alta con cantidad deja `existencia` **y** `movimiento_inventario` de tipo `inicial` (afirmar ambos); **no se crea movimiento si la cantidad inicial es 0**; `fecha_vencimiento` en pasado → 422; búsqueda por nombre (case-insensitive), por código y por categoría devuelven lo esperado; desactivar con existencias → 409; el padre (rol `padre`) recibe 403 en `POST /api/productos` y 200 en `GET /api/productos` (contraste directo de P14).

**Criterio de aceptación:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
Esperado: `0 failed`, y specifically `test_productos.py::...::test_codigo_duplicado_409`, `...::test_alta_deja_movimiento_inicial`, `...::test_padre_no_puede_crear`, `...::test_padre_si_puede_consultar` en Passed.

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```
```powershell
$h = @{ "Authorization" = "Bearer <JWT>"; apikey = "<SUPABASE_ANON_KEY>" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/productos?q=shampoo" -Headers $h | ConvertTo-Json
```
Esperado: JSON con `{"id":...,"codigo":...,"nombre":...,"precio_venta":...,"existencia":...}`; con un token de rol `padre` responde 200, y con el mismo token un `POST /api/productos` responde **403**.

---

## 6. Fase B — Existencias y pipeline de venta

**Cubre:** requerimientos 2 (cantidad disponible) y 4 (registrar ventas con descuento de inventario, folio único, comprobante y validación de disponibilidad). Es la fase más compleja: 4 escrituras y 1 transacción.

**Entidades:** `existencia`, `movimiento_inventario`, `venta`, `detalle_venta`, `producto`, `cliente` (opcional).

**Endpoints:**

| Método | Ruta | Capacidad |
|---|---|---|
| GET | `/api/inventario/existencia` | `STOCK_CONSULTAR` |
| GET | `/api/inventario/movimientos` | `INVENTARIO_VER_MOVIMIENTOS` |
| POST | `/api/inventario/ajustes` | `INVENTARIO_AJUSTAR` |
| GET | `/api/ventas`, `/api/ventas/{id}` | `STOCK_CONSULTAR` |
| POST | `/api/ventas` | `VENTAS_REGISTRAR` |
| POST | `/api/ventas/{id}/anular` | `VENTAS_ANULAR` |

**Archivos:**

```
backend/app/api/inventario.py      crear
backend/app/api/ventas.py          crear
backend/app/schemas/venta.py       crear   (VentaCreate, VentaDetalle, VentaRead, AnulacionCreate)
backend/app/schemas/inventario.py  crear
backend/app/services/existencia.py crear   (reservar/ajustar stock con movements)
backend/app/services/folio.py      crear   (generación segura del folio — P22)
backend/app/services/ventas.py     crear   (transacción atómica + anulación)
backend/app/core/errores.py        modificar (añadir errores de stock/folio/anulación)
backend/app/main.py                modificar
backend/tests/test_inventario.py   crear
backend/tests/test_ventas.py       crear
backend/tests/test_anulacion.py    crear
backend/tests/test_folio.py        crear
backend/tests/conftest.py          modificar (fixture transaccional del esquema `test` — P20)
```

**Reglas de negocio a resolver:**

1. **Atomicidad.** `venta` + N `detalle_venta` + N `movimiento_inventario` + N `existencia` en **una sola transacción** (`async with session.begin()`). Si un solo producto falla la validación de stock, **no** queda venta ni movimiento parcial. Es el criterio central de la fase.
2. **Validación de disponibilidad antes de cobrar.** Por cada línea: `SELECT ... FOR UPDATE` sobre `existencia` del producto en el almacén, y exigir `cantidad >= pedida`. Si alguna falla → `StockInsuficienteError` (409) con el detalle de **qué producto** y cuánto hay. El `FOR UPDATE` es lo que evita el doble gasto concurrente sobre el mismo producto.
3. **Folio único `F-AAAA-NNNN` (P22 — resuelto).** El `CHECK` exige 4 dígitos mínimo y hay `UNIQUE`. Generación aprobada: dentro de **la misma transacción de la venta**, antes del `INSERT`, `pg_advisory_xact_lock` sobre una clave fija del año, luego `SELECT max(folio) WHERE folio LIKE 'F-AAAA-%'` y `+1` con `lpad` a 4 dígitos. Con el bloqueo, dos ventas simultáneas no colisionan; el `UNIQUE` sigue siendo la red de seguridad. **No requiere cambios al esquema P15.**
4. **Totales que cuadran con los CHECK.** `subtotal_linea = cantidad * precio_unitario` **exacto** (sin redondeo propio). `subtotal_venta = sum(subtotal_linea)` cuantizado a 2 decimales. `descuento` entre 0 y `subtotal` (validado en servicio). `total = subtotal - descuento`. Si el total queda negativo → 422, nunca ajustar a mano.
5. **El precio lo toma el backend.** El request manda `producto_id` y `cantidad`; el `precio_unitario` se lee de `producto.precio_venta` en la transacción. **Aceptar precio del cliente es un agujero de precio** y no debe permitirse.
6. **Líneas duplicadas.** `UNIQUE (venta_id, producto_id)` impide repetir producto: el servicio **fusiona** las líneas repetidas sumando cantidades (y valida el stock sobre la cantidad ya fusionada). Si no se fusiona, la venta falla con 500 por violación de unicidad.
7. **Movimiento por venta.** Una `movimiento_inventario` por línea con `tipo='salida'`, `referencia_tipo='venta'`, `referencia_id = venta.id`, `usuario_id` = quien cobra, `cantidad = cantidad vendida`. La `existencia.cantidad` se descuenta con `UPDATE ... SET cantidad = cantidad - :n WHERE id = :id`.
8. **Ajuste de inventario** (`POST /api/inventario/ajustes`, capacidad `INVENTARIO_AJUSTAR`, solo admin y propietario): escribe `movimiento_inventario` con `tipo='ajuste'` y `referencia_tipo='ajuste'`, con `nota` **obligatoria**. Nunca se sobrescribe la existencia sin movimiento.
9. **Anulación.** `estado='anulada'` + `motivo_anulacion` obligatorio (CHECK). Genera **un movimiento compensatorio por línea** con `tipo='entrada'`, `referencia_tipo='venta'`, `referencia_id = venta.id`, `nota` con el motivo, y devuelve el stock a `existencia`. Como `cantidad > 0` en el CHECK, la reversión es una `entrada`, **nunca** un `-5`.
10. **Regla P14 de anulación.** `verificar_anulacion_venta(venta_usuario_id, usuario_id, rol)` ya existe en `capacidades.py`: el `padre` solo anula ventas de su propia sesión. El servicio debe llamarla y traducir el `PermissionError` a `AnulacionNoPermitidaError` (403). Administrador y dueño anulan cualquier venta.
11. **Anular dos veces** → `VentaNoAnulableError` (409): si `estado='anulada'` ya no hay segundo movimiento compensatorio.
12. **No hay `DELETE` en ventas.** El historial se conserva siempre; `detalle_venta` se mantiene para auditoría.
13. **`cliente_id` es opcional** (venta de mostrador). Si viene, debe existir y estar `activo`.

**Tests mínimos** (con BD real si se aprueba D2a; si no, con dobles y se marca laatomicidad como no verificada):

- **Totales:** venta de 3 líneas con descuento → `subtotal`, `descuento`, `total` exactos, incluido el caso de redondeo (P21).
- **Stock insuficiente:** pedir más de lo que hay → `StockInsuficienteError` **y** ninguna fila creada en `venta`, `detalle_venta`, `movimiento_inventario` ni cambio en `existencia` (afirmar el conteo antes y después: la prueba atómica).
- **Descuento correcto:** `existencia.cantidad` baja exactamente lo vendido y queda un `movimiento_inventario` trazable por línea.
- **Líneas duplicadas se fusionan** en una sola `detalle_venta`.
- **Folio:** la primera venta del año da `F-AAAA-0001`; dos ventas seguidas dan `0001` y `0002`; el formato cumple el regex del CHECK.
- **Anulación:** devuelvo stock, creo un movimiento `entrada` por línea, `estado='anulada'`, `motivo_anulacion` persistido; anular de nuevo → 409; anular **sin motivo** → 422.
- **P14:** el padre anula su propia venta (200) y la de otro usuario (403); el administrador anula cualquiera (200).
- **Ajuste:** con nota vacía → 422; con nota → movimiento `ajuste` y existencia actualizada.

**Criterio de aceptación:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
Esperado: `0 failed`, con `test_ventas.py::...::test_stock_insuficiente_no_deja_rastro` y `...::test_folio_incremental_en_el_anio` en Passed.

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```
```powershell
# Venta válida -> 201 con folio F-AAAA-0001
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/ventas" -Headers $h -Body $v | ConvertTo-Json
# Misma venta otra vez con el mismo producto -> 409
# Venta de más stock -> 409 con el detalle de qué producto falta
```
Esperado: la primera devuelve `{"id":…,"folio":"F-2026-0001","subtotal":…,"descuento":0,"total":…,"estado":"activa"}`; la repetida responde `409`; el exceso de stock responde `409` con `detail` nombrando el producto y la cantidad disponible. Luego, en Supabase, `existencia.cantidad` debe haber bajado y existir un `movimiento_inventario` `tipo='salida'` por línea.

---

## 7. Fase C — Alertas y reportes

**Cubre:** requerimientos 3 (alertas de nivel bajo y vencimiento próximo) y 6 (reportes de productos más vendidos en un periodo).

**Entidades:** `producto`, `existencia`, `movimiento_inventario`, `venta`, `detalle_venta`.

**Endpoints:**

| Método | Ruta | Capacidad |
|---|---|---|
| GET | `/api/alertas/bajo-stock` | `ALERTAS_VER` |
| GET | `/api/alertas/vencimiento` | `ALERTAS_VER` |
| GET | `/api/reportes/mas-vendidos` | `REPORTES_VER` |

`ALERTAS_VER` la tienen los tres roles; `REPORTES_VER` **no** la tiene el `padre` (P14) — la asimetría es intencional y debe estar probada.

**Archivos:**

```
backend/app/api/alertas.py         crear
backend/app/api/reportes.py        crear
backend/app/schemas/alertas.py     crear   (AlertaStock, AlertaVencimiento)
backend/app/schemas/reportes.py    crear   (MasVendido, VentasPorPeriodo)
backend/app/services/alertas.py    crear
backend/app/services/reportes.py   crear
backend/app/main.py                modificar
backend/tests/test_alertas.py      crear
backend/tests/test_reportes.py     crear
```

**Reglas de negocio a resolver:**

1. **Bajo stock.** Un producto está en nivel bajo cuando la `existencia.cantidad` **total** (suma de todos los almacenes) es `<= producto.umbral_minimo`. El umbral es **por producto** (CHECK `>= 0`). Decisión de lectura: `<=` (alcanzar el umbral ya avisa) o `<` (solo al pasarse). Recomiendo `<=` y que quede escrito y probado, porque es la diferencia entre avisar tarde y a tiempo.
2. **Vencimiento próximo.** `producto.fecha_vencimiento IS NOT NULL AND fecha_vencimiento <= hoy() + dias_vencimiento_aviso`. `dias_vencimiento_aviso` es **por producto** (default 30, CHECK `>= 0`). Un producto ya vencido entra en la misma alerta con severidad máxima.
3. **Ambas alertas se calculan, no se almacenan.** Se derivan del estado actual; no se crea tabla de alertas. La persistencia de avisos es la Fase D (notificaciones). Esto evita duplicar la verdad.
4. **Las alertas son de lectura**: no mutan nada y no generan notificación por sí solas (eso es Fase D, para no acoplar).
5. **Umbral 0.** Con `umbral_minimo = 0` (default del esquema) **todo** producto sale como bajo stock, porque `cantidad >= 0` siempre. Hay que decidir: o la Fase 0 siembra umbrales > 0, o el servicio trata `umbral_minimo = 0` como "sin alerta". Recomiendo lo segundo y dejarlo explícito.
6. **Más vendidos por periodo.** `SUM(detalle_venta.cantidad)` por producto entre `inicio` y `fin`, **excluyendo** `venta.estado = 'anulada'` (obligatorio: una venta anulada no es una venta). Ambos límites son obligatorios y `fin >= inicio` (422 si no).
7. **Zonas horarias.** `venta.fecha` es `timestamptz` y el negocio opera en `America/Guatemala`. Comparar por rango `[inicio, fin)` con esos límites en hora local, no en UTC. Debe quedar explícito en el servicio y en el test.
8. **Ranking**: orden por cantidad descendente, con `limit` (piso 50) y el total facturado como dato secundario del reporte.

**Tests mínimos:**

- Bajo stock: producto con `cantidad = umbral_minimo` → aparece; con `cantidad = umbral_minimo + 1` → no aparece; `umbral_minimo = 0` → no genera alerta masiva.
- La suma de existencias de **varios almacenes** se compara con un único umbral.
- Vencimiento: dentro de `dias_vencimiento_aviso` → aparece; fuera → no; `fecha_vencimiento IS NULL` → nunca aparece; ya vencido → aparece.
- Los tres roles ven `/api/alertas/*` (200) y el padre recibe **403** en `/api/reportes/mas-vendidos`.
- Más vendidos: excluye ventas anuladas; respeta el rango de fechas; ordena por cantidad descendente; `fin < inicio` → 422.

**Criterio de aceptación:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
Esperado: `0 failed`, con `test_alertas.py::...::test_padre_no_puede_ver_reportes` y `...::test_venta_anulada_no_cuenta_en_mas_vendidos` en Passed.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/alertas/bajo-stock" -Headers $h | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/reportes/mas-vendidos?inicio=2026-10-01&fin=2026-10-31" -Headers $h | ConvertTo-Json
```
Esperado: la primera devuelve el JSON de alertas con `producto_id`, `nombre`, `cantidad`, `umbral_minimo`; la segunda devuelve el ranking con `producto_id`, `nombre`, `cantidades_vendidas`, `total_facturado`. Con el token del `padre` la segunda responde **403**.

---

## 8. Fase D — Notificaciones y sugerencias (sin motor de IA)

**Entidades:** `notificacion`, `sugerencia`, `prediccion` (**solo** la fila base, ver B6).

**Endpoints:**

| Método | Ruta | Capacidad |
|---|---|---|
| GET | `/api/notificaciones` | `SUGERENCIAS_VER` |
| POST | `/api/notificaciones/{id}/leer` | `SUGERENCIAS_VER` |
| GET | `/api/sugerencias` | `SUGERENCIAS_VER` |
| POST | `/api/sugerencias/{id}/atender`, `/descartar` | `SUGERENCIAS_ATENDER` |

**Archivos:**

```
backend/app/api/notificaciones.py  crear
backend/app/api/sugerencias.py     crear
backend/app/schemas/notificacion.py crear
backend/app/schemas/sugerencia.py  crear
backend/app/services/notificaciones.py crear
backend/app/services/sugerencias.py crear
backend/app/main.py                modificar
backend/tests/test_notificaciones.py crear
backend/tests/test_sugerencias.py  crear
```

**Reglas de negocio a resolver:**

1. **Solo estado, sin inteligencia.** Esta fase **no** implementa el modelo de predicción: P3/P3a/P13 está aprobado pero `AGENTS.md` prohíbe escribir el modelo hasta autorización explícita. Se implementa únicamente CRUD/lectura y transición de estados.
2. **Bloqueo de esquema.** `sugerencia.prediccion_id` es NOT NULL. Sin una predicción previa **no se puede crear una sugerencia**. Esto obliga a B6. Si se aprueba B6a, la fila base se crea con `metodo='promedio_movil'`, `nivel_confianza='baja'` y `datos_ficticios=true`, que es exactamente la regla de respaldo de la tesis (últimos 7 días) y **no** es el modelo de ML.
3. **Estados de sugerencia:** `pendiente` → `atendida` | `descartada`. Solo se permite la transición desde `pendiente` (rechazar una ya atendida → 409).
4. **`prioridad`** ∈ `alta` | `media` | `baja` (CHECK).
5. **Notificación:** `tipo` ∈ `bajo_stock` | `vencimiento_proximo` | `sugerencia_compra` | `sistema` (CHECK). Marcar como leída es idempotente: volver a marcar una leída responde 200 sin error.
6. **No duplicar avisos.** Antes de crear una notificación `bajo_stock` para un producto, comprobar si ya existe una del mismo `tipo` sin resolver para ese producto. Sin columna de "resuelta", la deduplicación tiene que apoyarse en `leida = false` — hay que decidirlo explícitamente porque es una limitación del esquema actual.
7. **Destinatario.** `notificacion.usuario_id` es nullable. Falta definir a quién se le avisa (¿solo al propietario? ¿a los tres?). No se puede escribir el servicio sin eso.
8. **Nada de `DELETE`**: `notificacion` se lee por estado (`leida`), no se borra.

**Tests mínimos:** crear notificación de cada `tipo` válido; `tipo` inválido → 422; marcar leída dos veces → 200 ambas; listar solo devuelve las del usuario (o las que le correspondan según D-pendiente); sugerencia `pendiente` → `atendida` OK; `atendida` → `descartada` → 409; sugerencia sin `prediccion_id` → 422; el padre puede ver sugerencias pero no administrar usuarios.

**Criterio de aceptación:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
Esperado: `0 failed`, con `test_sugerencias.py::...::test_transicion_invalida_409` y `...::test_sugerencia_exige_prediccion` en Passed.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/notificaciones" -Headers $h | ConvertTo-Json
```
Esperado: JSON con `id`, `tipo`, `mensaje`, `leida`, `fecha`. Con `POST /api/sugerencias` sin `prediccion_id` → **422**.

---

## 9. Fase E — Clientes, usuarios y comprobante

**Cubre:** el cierre del CRUD de `cliente`, la gestión de los tres usuarios del sistema (P14: solo el administrador) y el comprobante de venta (P8: recibo interno con folio, imprimible y descargable; **no** es factura tributaria ni SAT/FEL).

**Entidades:** `cliente`, `usuario`, `venta`, `detalle_venta`, `producto`.

**Endpoints:**

| Método | Ruta | Capacidad |
|---|---|---|
| GET/POST | `/api/clientes`, `/api/clientes/{id}` | `STOCK_CONSULTAR` / `CONFIGURACION_GESTIONAR` |
| GET/POST | `/api/usuarios`, `/api/usuarios/{id}/activo` | `USUARIOS_GESTIONAR` |
| GET | `/api/ventas/{id}/comprobante` | `STOCK_CONSULTAR` |

**Archivos:**

```
backend/app/api/clientes.py        crear
backend/app/api/usuarios.py        crear
backend/app/api/comprobantes.py    crear
backend/app/schemas/cliente.py     crear
backend/app/schemas/usuario.py     crear
backend/app/schemas/comprobante.py crear
backend/app/services/clientes.py   crear
backend/app/services/usuarios.py   crear
backend/app/services/comprobantes.py crear
backend/app/main.py                modificar
backend/tests/test_clientes.py     crear
backend/tests/test_usuarios.py     crear
backend/tests/test_comprobante.py  crear
```

**Reglas de negocio a resolver:**

1. **Gestión de usuarios.** El alta de un usuario real requiere **dos** pasos coordinados: crearlo en Supabase Auth (Admin API, `email_confirm`) y luego insertar la fila en `usuario` con el `auth_id` recibido. Si se hace solo uno de los dos, el login da 403 "Usuario sin perfil registrado" — **ya verificado** en la validación E2E. La Fase E debe decidir si el backend hace ambos (necesita `SUPABASE_SERVICE_ROLE_KEY` en el servidor) o si el alta de usuarios se sigue haciendo por script. **No se puede ampliar el alcance de la clave de servicio sin decisión explícita.**
2. **Solo administrador** puede crear, desactivar o cambiar roles de usuarios. `uq_usuario_email` y `uq_usuario_auth_id` → violación de unicidad = 409.
3. **Nunca crear el primer administrador por endpoint**: el proceso de arranque (bootstrap) queda como script documentado, no como endpoint abierto.
4. **Comprobante.** Renderiza los datos de la venta (folio, fecha, cliente, líneas, subtotal, descuento, total) desde los datos guardados, **nunca** recalculados. Si `estado = 'anulada'`, el comprobante debe mostrarse como anulado con su motivo.
5. **Comprobante no tributario.** El texto "recibo interno" y la ausencia de ISBN/autorización SAT deben ser explícitos en la vista (P8).
6. **PDF (B5).** Recomendación sin dependencia nueva: endpoint HTML con estilos de impresión + `window.print()` en el frontend, que es lo que permite "descargar PDF" desde el navegador. Si se quiere PDF nativo en servidor, es una dependencia nueva y requiere aprobación aparte.
7. **`cliente` con `activo`**: desactivar, no borrar. `idx_cliente_nombre` cubre la búsqueda.

**Tests mínimos:** alta de usuario con `email` duplicado → 409; solo el administrador entra a `/api/usuarios` (el `padre` y el `propietario` reciben 403); desactivar un usuario → su JWT deja de servir (el endpoint protegido responde 403 "Usuario inactivo"); el comprobante de una venta anulada muestra el motivo; el total del comprobante coincide **exactamente** con `venta.total` almacenado (sin recalcular).

**Criterio de aceptación:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```
Esperado: `0 failed`, con `test_usuarios.py::...::test_padre_no_gestiona_usuarios` y `test_comprobante.py::...::test_comprobante_coincide_con_venta` en Passed.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/ventas/<id>/comprobante" -Headers $h | ConvertTo-Json
```
Esperado: JSON con `folio`, `fecha`, `lineas[]`, `subtotal`, `descuento`, `total`, `estado`. Con token de `padre` en `/api/usuarios` → **403**.

---

## 10. Fuera de alcance (y por qué)

| Tema | Estado | Razón |
|---|---|---|
| Modelo de predicción (RF/HistGB/Ridge), job diario | **No implementar** | P3/P3a/P13 aprobado pero `AGENTS.md` prohíbe implementarlo sin autorización. La Fase D solo deja CRUD/estado. |
| Offline / sincronización | **No implementar** | P2 y R4: estrategia sin definir. La arquitectura queda abierta (contratos claros, idempotencia donde aplica). |
| App móvil / React Native | **Prohibido** | D1 de `DECISIONES.md`: fuera de alcance en esta fase. |
| Hosting / despliegue | **Pospuesto** | P12 / R5. |
| Nodo.js serverless | **Sin justificar todavía** | P1: no hay una tarea liviana que no pertenezca a FastAPI. No crear funciones Node solo porque la tecnología existe. |
| Facturación electrónica (SAT/FEL) | **Fuera** | P8: el comprobante es un recibo interno. |

---

## 11. Trazabilidad con los requerimientos del Cap. IV

| # | Requerimiento (Cap. IV) | Fase | Estado |
|---|---|---|---|
| 1 | Registrar productos (nombre, categoría, cantidad, proveedor, fecha de ingreso, precio) | A | Pendiente |
| 2 | Consultar cantidad disponible (nombre, código, categoría) | A (consulta) + B (existencia) | Pendiente |
| 3 | Alertas: nivel bajo y vencimiento próximo | C | Pendiente |
| 4 | Ventas: descuento de inventario, folio único, comprobante, validación de disponibilidad | B (núcleo) + E (comprobante) | Pendiente |
| 5 | Gestión de proveedores (precios, condiciones de entrega) | A | Pendiente |
| 6 | Reportes de productos más vendidos por periodo | C | Pendiente |
| 7 | Predicción de demanda con job diario | **Fuera de alcance** (autorización pendiente) | Pos-puesto |

---

## 12. Orden de ejecución y por qué difiere del agrupamiento inicial

El agrupamiento propuesto (A catálogo, B ventas, C alertas/reportes, D notificaciones) se conserva, con dos ajustes:

1. **Se antepone una Fase 0 (cimientos) que no estaba en el listado original.** No es opcional: `almacen` tiene 0 filas y `existencia.almacen_id` es NOT NULL con FK a `almacen`, de modo que la Fase B **no puede ni probarse** sin un almacén sembrado. Además centraliza la convención de routers, el envelope de errores y el manejo de dinero, que si no se fijan en la Fase 0 se replican inconsistentes en las cinco fases siguientes.
2. **Se añade una Fase E (clientes, usuarios, comprobante)** al final, que no cabía en A–D. El requerimiento 4 exige comprobante (P8) y sin clientes ni gestión de usuarios la plataforma queda sin cerrar: el padre y el propietario **no existen todavía** en la base (solo hay 1 usuario, el de pruebas), así que la matriz P14 no se puede validar de extremo a extremo hasta que existan los tres.

El orden final es: **0 → A → B → C → D → E**. B va después de A porque una venta necesita productos y existencias reales. C va después de B porque "productos más vendidos" necesita ventas, y las alertas necesitan umbrales ya sembrados en A.

---

## 13. Pendientes de este plan

- [x] **Resueltas (2026-10-05)**: **B1** (P19, almacén por defecto), **B2** (P20, esquema `test`), **B3** (P22, folio concurrente con `pg_advisory_xact_lock`), **B4** (P21, redondeo). Con esto la Fase 0 ya puede escribirse y el folio de la Fase B ya está resuelto.
- [ ] Resolver **B5 y B6** de §3. **B5** bloquea el comprobante (Fase E); **B6** bloquea la Fase D. **B7** ya no está pendiente: se resolvió en P23.
- [x] Aplicar `backend/tests/sql/00_test_schema.sql` en Supabase y definir `DATABASE_URL_TEST` en `backend/.env` (vacía en `.env.example`) para habilitar las pruebas de integración.
- [x] Corregir el comentario de `supabase/migrations/14_enable_rls.sql`: FastAPI conecta como propietario (`postgres`), que tampoco pasa por RLS; no se usa `service_role` vía PostgREST (resuelve **B7**).
- [ ] Revisar y autorizar el resto de la Fase 0 antes de escribirla (`errores.py`, `dinero.py`, `config.py`, `scripts/semilla.py`, `api/me.py`).
- [ ] Nada se commitea sin autorización explícita del usuario.
