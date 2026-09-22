# Reglas de base de datos (Supabase / PostgreSQL)

Supabase (PostgreSQL) es la plataforma definida por el proyecto para base de datos, autenticación y storage. **Ya existe un proyecto de Supabase gratuito para este proyecto; no crear otro** (P9). La interacción con Supabase se gestiona preferentemente mediante MCP; si el acceso MCP no está configurado, indicarlo en lugar de asumirlo.

## Antes de crear o modificar tablas

1. Revisar el estado actual del esquema existente (tablas, vistas, índices, funciones).
2. Revisar relaciones y restricciones (claves, unicidad, cascadas).
3. Revisar migraciones aplicadas y el historial de cambios.
4. Revisar el código que consume esas tablas (backend, servicios, tests).
5. Confirmar con el usuario cuando el cambio altere entidades o relaciones importantes.
6. Verificar coherencia con el esquema aprobado (P15) y comprobar que las relaciones/restricciones no cierren la incorporación futura de lotes (vencimiento por `Producto.fechaVencimiento`).

## Operaciones destructivas

- Antes de operaciones destructivas o cambios importantes en la BD: **revisar el estado actual**, confirmar qué se va a modificar, evitar eliminar información innecesariamente.
- Usar **migraciones o mecanismos reproducibles** cuando corresponda.
- No ejecutar cambios destructivos sin confirmación explícita.

## Reglas

- **No crear tablas duplicadas**: verificar que no exista ya una tabla equivalente.
- **Todo cambio de esquema va por migración versionada**, nunca cambios manuales directos en Supabase (aunque el acceso MCP esté disponible). Las migraciones se numeran/versionan y quedan registradas en el repositorio; un cambio de esquema sin migración versionada se rechaza.
- **Restricciones a nivel de base de datos** (CHECK, FK, NOT NULL, UNIQUE) además de la validación en la app: la base es la última línea de defensa de la integridad; no confiar solo en la validación del backend.
- **Índices en columnas de búsqueda/filtrado frecuente**: nombre de producto, folio de venta, fechas de vencimiento, y combinaciones usadas por movimientos/predicción (p. ej. `(producto_id, fecha)` como recomienda P15).
- **Soft delete en catálogo** (`estado`/`activo`): los registros de catálogo se desactivan, no se borran. **Prohibido `DELETE` destructivo en `Venta` y `DetalleVenta`** (la anulación es por `estado='anulada'`, los detalles se conservan por auditoría; ya definido en P15, reforzado aquí como regla de implementación). Tampoco `DELETE` ni `UPDATE` destructivo en `MovimientoInventario`.
- **No cambiar nombres de entidades o relaciones importantes sin justificación**: los nombres de las entidades de la tesis son referencia obligatoria (Producto, Categoría, Proveedor, Cliente, Usuario, Venta, DetalleVenta, Almacén, Existencia, MovimientoInventario, Predicción, Sugerencia, Notificación).
- **Esquema inicial APROBADO (P15)**: ver `DECISIONES.md` (13 entidades con campos, tipos, PK/FK y restricciones). **Sin entidad `Lote`** en esta fase; el vencimiento se maneja con `Producto.fechaVencimiento` (lote activo; NULL = no perecedero). **Antes de crear las tablas, verificar** que relaciones y restricciones (unicidades, FK, CHECK) no cierren la posibilidad de incorporar lotes posteriormente (los productos podrían eventualmente tener distintas fechas de vencimiento).
- **Traza de movimientos**: el inventario se gestiona mediante movimientos; no se debe sobrescribir existencias sin dejar rastro.
- **Seguridad por defecto (RLS)**: activar Row Level Security en Supabase y definir políticas de acceso por rol. Ver `seguridad.md`.
- Documentar migraciones y cambios de esquema de forma ordenada y versionada.

## Integridad

- Usar transacciones para operaciones atómicas (ventas, movimientos de inventario).
- Definir restricciones de unicidad donde aplique (folios de venta, códigos de producto, etc.).
- No añadir secretos ni credenciales en scripts de migración ni en el repositorio.