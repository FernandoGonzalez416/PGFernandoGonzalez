F5 — MODO SIN CONEXIÓN MÍNIMO + IDEMPOTENCIA DE VENTAS
======================================================

Cierre de F5 (2026-10-12). Decisión documentada: **P27** en `DECISIONES.md`.
Alcance: versión **mínima** de POS sin conexión (no es la estrategia offline
definitiva: P2/R4 siguen vigentes). Sin Service Worker, sin PWA, sin IndexedDB.

--- PUNTO 0: DIAGNÓSTICO DEL MOTOR (solo lectura) ---

Series evaluadas (datos de demostración SIM):
- SIM-007: 120 días, perfil media (1.5/día), última venta = 4. Últimos 21 días:
  [0,1,0,1,0,1,0,2,5,7,4,0,2,0,0,0,2,1,0,0,4]. Caída al final de la serie.
- SIM-001: 117 días, perfil media-alta (1-2/día), última venta = 0. Últimos 21 días:
  [1,0,0,6,4,0,0,7,15,0,4,11,12,6,0,0,0,0,2,0,0]. Patrón intermitente.

Diagnóstico en una frase: el error de la línea base **sí** lo explican los datos
(ambas series caen al final), por lo que el promedio móvil queda rezagado; es un
patrón de ventas, no un defecto del motor.

--- PUNTO 1: BACKEND — idempotencia y fecha del cliente ---

a) Migración `supabase/migrations/16_add_client_request_id_venta.sql`:
   `ALTER TABLE venta ADD COLUMN client_request_id uuid NULL` + UNIQUE parcial
   (`WHERE client_request_id IS NOT NULL`). Espejo en `backend/tests/sql/00_test_schema.sql`.

b) `VentaCreate` (`backend/app/schemas/venta.py`):
   - `client_request_id: UUID | None = None` (idempotencia del POS offline)
   - `fecha: datetime | None = None` (opcional; validada)

c) `registrar_venta` (`backend/app/services/ventas.py`):
   - Si ya existe una venta con ese `client_request_id`, devuelve la existente
     con `creada=False` **sin** crear fila, ni descontar stock, ni escribir movimiento.
   - Fecha: se rechaza futuro o > 72 h atrás → **422** `FechaVentaInvalidaError`;
     la fecha `naive` se interpreta como UTC (`_como_utc`).
   - La fecha enviada se guarda en `venta.fecha` y en los movimientos.
   - Devuelve `ResultadoRegistroVenta(venta, creada)` (el servicio **no** conoce HTTP).

d) Endpoint `POST /api/ventas` (`backend/app/api/ventas.py`):
   - **201** al crear, **200** en la repetición idempotente (ajusta `Response.status_code`).
   - `FechaVentaInvalidaError` mapeado a 422 en `backend/app/main.py`.

e) Pruebas: `backend/tests/test_ventas_idempotencia.py` (7 tests de integración).

--- PUNTO 2: FRONTEND — src/offline/ y POS ---

Implementado (`frontend/src/offline/`):
- `almacenamiento.ts`: `localStorage` versionado y separado por usuario; manejo de
  cuota llena con aviso (nunca descartes silenciosos).
- `useConexion.ts`: estado `online` + `marcarOffline()`.
- `useColaVentas.ts`: cola FIFO en `localStorage`; sincroniza una venta a la vez
  reintentando con el mismo `client_request_id`; 401 pausa sin perder la cola,
  409/422/403 → `requiere_revision` y continúa, error de red detiene.
- `useCatalogoCache.ts`: caché del catálogo; descuenta y persiste existencia al
  vender sin conexión.
- `ProveedorOffline.tsx` + `contexto.ts` + `useOffline.ts`: estado compartido;
  remonta al cambiar de usuario (`key=usuarioId`) para hidratar la cola correcta.
- `BarraConexion.tsx`: indicador en la barra superior (Sin conexión / N pendientes /
  Sincronizando… / Al día).
- POS `VentaNueva.tsx`: con `online=false` busca en el caché, guarda la venta en la
  cola con folio provisional y navega a `/ventas/pendientes`.
- `VentasPendientes.tsx`: revisar, **Reintentar** y **Descartar**.

--- PUNTO 3: DOCUMENTACIÓN ---

- `DECISIONES.md`: sección **P27** + nota de actualización (2026-10-12) + nota en R4.
- `docs/GUION_DEMO.md`: paso **3.7 Modo sin conexión del POS**; version F5;
  tabla de puntos clave y limitaciones actualizadas.

--- PUNTO 4: ESTADO DE LOS COMMITS ---

Todo el trabajo de F5 está **sin confirmar** (working tree). No se hicieron commits.

--- DESVIACIONES / AMBIGÜEDADES ---

1. **Servicio ajeno a HTTP (resuelto)**: el primer borrador lanzaba `HTTPException`
   desde `registrar_venta`. Se sustituyó por `ResultadoRegistroVenta` para que los
   servicios sigan sin conocer HTTP y el endpoint decida el código (200/201).
2. **Esquema de pruebas**: `00_test_schema.sql` ya incluye `client_request_id`; la
   base `DATABASE_URL_TEST` debe tener el esquema aplicado (se aplicó el 2026-10-12).
3. **Frontend offline**: se implementa en F5 dentro del alcance Web (no hay app móvil).
4. **Sin Service Worker (P2)**: la app debe estar cargada; solo el POS opera sin
   conexión; el stock del caché puede quedar desactualizado y los conflictos caen en
   revisión manual. No se introducen PWA/IndexedDB.

--- RESUMEN EJECUTIVO ---

Hecho en F5:
  [x] Migración SQL `16_add_client_request_id_venta.sql`
  [x] `client_request_id` y `fecha` en `VentaCreate`/`VentaRead`
  [x] Idempotencia en `registrar_venta` (200 al repetir, 201 al crear)
  [x] Validación de fecha (≤ ahora, ≤ 72 h atrás → 422)
  [x] Esquema de pruebas con la nueva columna (aplicado a `DATABASE_URL_TEST`)
  [x] Frontend `src/offline/` + POS sin conexión + pantalla de pendientes
  [x] Documentación (P27 + guion de demo)

Pruebas (conteos reales de la salida):
  - Frontend `npx vitest run`: **22 archivos (22) · 113 pruebas (113) aprobadas**
  - Frontend `npm run typecheck`: limpio; `npm run lint`: 0 errores (1 warning previo en ToastProvider)
  - Backend unitarias `pytest -q`: **116 aprobadas, 152 deseleccionadas, 1 warning**
  - Backend integración completa (`pytest -m integracion`, run 2026-10-12): **151 aprobadas, 1 fallo** — el fallo era únicamente
    `test_paridad_esquemas` porque la migración 16 no estaba aplicada al esquema `public` de producción.
  - Tras aplicar la migración 16 al esquema `public` (2026-10-12, vía `DATABASE_URL` con asyncpg, aprobado por el usuario):
    `test_paridad_esquemas.py` + `test_ventas.py` + `test_ventas_idempotencia.py -m integracion` → **24 aprobadas en 221.64s**.
    Con la paridad corregida, la suite completa de integración queda **152/152** por composición (los otros 148
    tests ya habían pasado en el run completo).
