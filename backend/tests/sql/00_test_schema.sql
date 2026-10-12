-- 00_test_schema.sql
--
-- ESQUEMA DE PRUEBAS. NO ES UNA MIGRACION DE SUPABASE.
--
-- Ubicado en backend/tests/sql/ y NO en supabase/migrations/ precisamente para
-- que el flujo de migraciones de Supabase no lo aplique nunca a la base de la
-- aplicacion: aqui solo crea el esquema `test`.
--
-- Proposito (P20): un espejo del DDL de las migraciones 00..13 dentro del
-- esquema `test`, para que las pruebas de integracion ejerciten de verdad los
-- CHECK, los UNIQUE, los FK y los triggers, sin tocar los datos reales.
--
-- COMO APLICAR (manual, una vez):
--   psql "$DATABASE_URL_TEST" -v ON_ERROR_STOP=1 -f backend/tests/sql/00_test_schema.sql
-- o bien desde el panel/MCP de Supabase, con el mismo contenido.
-- Si `DATABASE_URL_TEST` no esta definida, las pruebas de integracion se omiten
-- (ver backend/tests/conftest.py). Nunca debe apuntar a la base de desarrollo.
--
-- COMO REAPLICAR DESDE CERO:
--   psql "$DATABASE_URL_TEST" -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS test CASCADE;"
--   y volver a aplicar este archivo. CREATE TRIGGER no es idempotente, por eso
--   el reinicio requiere dropear el esquema.
--
-- DESVIACION DELIBERADA RESPECTO DE 14_enable_rls.sql: aqui NO se habilita RLS.
-- Razon (P20): las pruebas de integracion conectan como propietario, y el
-- propietario no pasa por RLS de todas formas; activarlo solo haria que una
-- futura conexion con otro rol fallara en silencio. RLS no se prueba aqui: la
-- autorizacion se verifica en la capa de FastAPI (requiere(), P14).
--
-- RIESGO CONOCIDO: este archivo es una COPIA MANUAL de las migraciones 01..13 y
-- puede quedar desactualizado si se agregan columnas o tablas. Al tocar el
-- esquema hay que actualizar tambien este archivo.

CREATE SCHEMA IF NOT EXISTS test;

-- ---------------------------------------------------------------------------
-- 01 categoria (misma definicion que 01_create_categoria.sql)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.categoria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    descripcion text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_categoria_nombre ON test.categoria (lower(nombre));

CREATE TRIGGER trg_categoria_updated_at
    BEFORE UPDATE ON test.categoria
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 02 proveedor
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.proveedor (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    contacto text,
    telefono text,
    email text,
    condiciones_entrega text,
    precio_habitual numeric(12,2),
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_proveedor_precio_habitual CHECK (precio_habitual IS NULL OR precio_habitual >= 0)
);

CREATE INDEX IF NOT EXISTS idx_proveedor_nombre ON test.proveedor (lower(nombre));

CREATE TRIGGER trg_proveedor_updated_at
    BEFORE UPDATE ON test.proveedor
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 03 usuario
-- NOTA: la FK a auth.users se mantiene igual que en la migracion. Por eso una
-- prueba que necesite un usuario debe insertar primero su fila en auth.users.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.usuario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id uuid NOT NULL,
    nombre text NOT NULL,
    email text NOT NULL,
    rol text NOT NULL,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_usuario_auth_id UNIQUE (auth_id),
    CONSTRAINT uq_usuario_email UNIQUE (email),
    CONSTRAINT fk_usuario_auth FOREIGN KEY (auth_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT chk_usuario_rol CHECK (rol IN ('administrador', 'propietario', 'padre'))
);

CREATE INDEX IF NOT EXISTS idx_usuario_rol_activo ON test.usuario (rol) WHERE activo = true;

CREATE TRIGGER trg_usuario_updated_at
    BEFORE UPDATE ON test.usuario
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 04 cliente
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    telefono text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cliente_nombre ON test.cliente (lower(nombre));

CREATE TRIGGER trg_cliente_updated_at
    BEFORE UPDATE ON test.cliente
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 05 almacen
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.almacen (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    ubicacion text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_almacen_nombre UNIQUE (nombre)
);

CREATE TRIGGER trg_almacen_updated_at
    BEFORE UPDATE ON test.almacen
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 06 producto
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.producto (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo text NOT NULL,
    nombre text NOT NULL,
    descripcion text,
    categoria_id uuid NOT NULL REFERENCES test.categoria(id) ON DELETE RESTRICT,
    proveedor_id uuid REFERENCES test.proveedor(id) ON DELETE SET NULL,
    precio_venta numeric(12,2) NOT NULL,
    precio_costo numeric(12,2) NOT NULL,
    unidad_medida text NOT NULL DEFAULT 'unidad',
    umbral_minimo numeric(12,2) NOT NULL DEFAULT 0,
    dias_vencimiento_aviso integer NOT NULL DEFAULT 30,
    fecha_vencimiento date,
    fecha_ingreso date,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_producto_codigo UNIQUE (codigo),
    CONSTRAINT chk_producto_precio_venta CHECK (precio_venta >= 0),
    CONSTRAINT chk_producto_precio_costo CHECK (precio_costo >= 0),
    CONSTRAINT chk_producto_umbral CHECK (umbral_minimo >= 0),
    CONSTRAINT chk_producto_dias_aviso CHECK (dias_vencimiento_aviso >= 0)
);

CREATE INDEX IF NOT EXISTS idx_producto_categoria ON test.producto (categoria_id);
CREATE INDEX IF NOT EXISTS idx_producto_proveedor ON test.producto (proveedor_id);
CREATE INDEX IF NOT EXISTS idx_producto_nombre ON test.producto (lower(nombre));
CREATE INDEX IF NOT EXISTS idx_producto_vencimiento ON test.producto (fecha_vencimiento) WHERE fecha_vencimiento IS NOT NULL;

CREATE TRIGGER trg_producto_updated_at
    BEFORE UPDATE ON test.producto
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 07 existencia
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.existencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id uuid NOT NULL REFERENCES test.producto(id) ON DELETE RESTRICT,
    almacen_id uuid NOT NULL REFERENCES test.almacen(id) ON DELETE RESTRICT,
    cantidad numeric(12,2) NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_existencia_producto_almacen UNIQUE (producto_id, almacen_id),
    CONSTRAINT chk_existencia_cantidad CHECK (cantidad >= 0)
);

CREATE INDEX IF NOT EXISTS idx_existencia_almacen ON test.existencia (almacen_id);

CREATE TRIGGER trg_existencia_updated_at
    BEFORE UPDATE ON test.existencia
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 08 venta
-- NOTA: chk_venta_folio_formato exige 'F-AAAA-NNNN' con 4 digitos minimo.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.venta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    folio text NOT NULL,
    fecha timestamptz NOT NULL DEFAULT now(),
    cliente_id uuid REFERENCES test.cliente(id) ON DELETE SET NULL,
    usuario_id uuid NOT NULL REFERENCES test.usuario(id) ON DELETE RESTRICT,
    metodo_pago text NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    descuento numeric(12,2) NOT NULL DEFAULT 0,
    total numeric(12,2) NOT NULL,
    estado text NOT NULL DEFAULT 'activa',
    motivo_anulacion text,
    created_at timestamptz NOT NULL DEFAULT now(),
    client_request_id uuid NULL,
    CONSTRAINT uq_venta_folio UNIQUE (folio),
    CONSTRAINT chk_venta_folio_formato CHECK (folio ~ '^F-\d{4}-\d{4,}$'),
    CONSTRAINT chk_venta_metodo_pago CHECK (metodo_pago IN ('efectivo', 'tarjeta', 'transferencia', 'otro')),
    CONSTRAINT chk_venta_subtotal CHECK (subtotal >= 0),
    CONSTRAINT chk_venta_descuento CHECK (descuento >= 0 AND descuento <= subtotal),
    CONSTRAINT chk_venta_total CHECK (total >= 0),
    CONSTRAINT chk_venta_total_calculo CHECK (total = subtotal - descuento),
    CONSTRAINT chk_venta_estado CHECK (estado IN ('activa', 'anulada')),
    CONSTRAINT chk_venta_anulacion_motivo CHECK (estado <> 'anulada' OR motivo_anulacion IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_venta_client_request_id ON test.venta (client_request_id) WHERE client_request_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_venta_fecha ON test.venta (fecha);
CREATE INDEX IF NOT EXISTS idx_venta_cliente ON test.venta (cliente_id);
CREATE INDEX IF NOT EXISTS idx_venta_usuario ON test.venta (usuario_id);

-- ---------------------------------------------------------------------------
-- 09 detalle_venta
-- NOTA: uq_detalle_venta_producto impide repetir producto en la misma venta.
-- NOTA: chk_detalle_venta_calculo exige subtotal = cantidad * precio_unitario
-- exacto; con cantidad entera y precio ya cuantizado a 2 decimales (P21) se
-- cumple sin redondear la linea.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.detalle_venta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    venta_id uuid NOT NULL REFERENCES test.venta(id) ON DELETE RESTRICT,
    producto_id uuid NOT NULL REFERENCES test.producto(id) ON DELETE RESTRICT,
    cantidad integer NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    CONSTRAINT uq_detalle_venta_producto UNIQUE (venta_id, producto_id),
    CONSTRAINT chk_detalle_venta_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_detalle_venta_precio CHECK (precio_unitario >= 0),
    CONSTRAINT chk_detalle_venta_subtotal CHECK (subtotal >= 0),
    CONSTRAINT chk_detalle_venta_calculo CHECK (subtotal = cantidad * precio_unitario)
);

CREATE INDEX IF NOT EXISTS idx_detalle_venta_producto ON test.detalle_venta (producto_id);

-- ---------------------------------------------------------------------------
-- 10 movimiento_inventario
-- NOTA: chk_movimiento_cantidad exige cantidad > 0, por lo que una anulacion
-- se registra como tipo='entrada' compensatorio, nunca como cantidad negativa.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.movimiento_inventario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id uuid NOT NULL REFERENCES test.producto(id) ON DELETE RESTRICT,
    almacen_id uuid REFERENCES test.almacen(id) ON DELETE SET NULL,
    tipo text NOT NULL,
    referencia_tipo text NOT NULL,
    referencia_id uuid,
    cantidad numeric(12,2) NOT NULL,
    usuario_id uuid REFERENCES test.usuario(id) ON DELETE SET NULL,
    nota text,
    fecha timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_movimiento_tipo CHECK (tipo IN ('entrada', 'salida', 'ajuste')),
    CONSTRAINT chk_movimiento_referencia_tipo CHECK (referencia_tipo IN ('venta', 'compra', 'ajuste', 'vencimiento', 'devolucion', 'inicial')),
    CONSTRAINT chk_movimiento_cantidad CHECK (cantidad > 0)
);

CREATE INDEX IF NOT EXISTS idx_movimiento_producto_fecha ON test.movimiento_inventario (producto_id, fecha);
CREATE INDEX IF NOT EXISTS idx_movimiento_referencia ON test.movimiento_inventario (referencia_tipo, referencia_id);

-- ---------------------------------------------------------------------------
-- 11 prediccion
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.prediccion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id uuid NOT NULL REFERENCES test.producto(id) ON DELETE RESTRICT,
    fecha_generacion timestamptz NOT NULL DEFAULT now(),
    inicio_horizonte date NOT NULL,
    fin_horizonte date NOT NULL,
    demanda_pronosticada numeric(12,2) NOT NULL,
    demanda_real numeric(12,2),
    intervalo_inf numeric(12,2),
    intervalo_sup numeric(12,2),
    metodo text NOT NULL,
    nivel_confianza text NOT NULL,
    mae_validacion numeric(12,2),
    wape_validacion numeric(12,2),
    nmae numeric(12,2),
    observaciones_usadas integer,
    datos_ficticios boolean NOT NULL DEFAULT false,
    mae_linea_base numeric(12,2),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_prediccion_demanda CHECK (demanda_pronosticada >= 0),
    CONSTRAINT chk_prediccion_metodo CHECK (metodo IN ('promedio_movil', 'random_forest', 'hist_gradient_boosting', 'ridge', 'sin_historial')),
    CONSTRAINT chk_prediccion_confianza CHECK (nivel_confianza IN ('alta', 'baja', 'simulacion')),
    CONSTRAINT chk_prediccion_horizonte CHECK (fin_horizonte >= inicio_horizonte),
    CONSTRAINT chk_prediccion_intervalo CHECK (intervalo_inf IS NULL OR intervalo_sup IS NULL OR intervalo_inf <= intervalo_sup),
    CONSTRAINT chk_prediccion_mae_linea_base CHECK (mae_linea_base IS NULL OR mae_linea_base >= 0)
);

CREATE INDEX IF NOT EXISTS idx_prediccion_producto_fecha ON test.prediccion (producto_id, fecha_generacion DESC);

-- ---------------------------------------------------------------------------
-- 12 sugerencia
-- NOTA: prediccion_id es NOT NULL; sin una prediccion previa no se puede crear
-- una sugerencia. Es el bloqueo B6 del plan.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.sugerencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    prediccion_id uuid NOT NULL REFERENCES test.prediccion(id) ON DELETE RESTRICT,
    producto_id uuid NOT NULL REFERENCES test.producto(id) ON DELETE RESTRICT,
    fecha timestamptz NOT NULL DEFAULT now(),
    demanda_pronosticada numeric(12,2) NOT NULL,
    stock_proyectado numeric(12,2) NOT NULL,
    cantidad_sugerida numeric(12,2) NOT NULL,
    prioridad text NOT NULL,
    estado text NOT NULL DEFAULT 'pendiente',
    CONSTRAINT uq_sugerencia_prediccion_producto UNIQUE (prediccion_id, producto_id),
    CONSTRAINT chk_sugerencia_demanda CHECK (demanda_pronosticada >= 0),
    CONSTRAINT chk_sugerencia_stock CHECK (stock_proyectado >= 0),
    CONSTRAINT chk_sugerencia_cantidad CHECK (cantidad_sugerida >= 0),
    CONSTRAINT chk_sugerencia_prioridad CHECK (prioridad IN ('alta', 'media', 'baja')),
    CONSTRAINT chk_sugerencia_estado CHECK (estado IN ('pendiente', 'atendida', 'descartada'))
);

CREATE INDEX IF NOT EXISTS idx_sugerencia_producto ON test.sugerencia (producto_id);
CREATE INDEX IF NOT EXISTS idx_sugerencia_pendiente ON test.sugerencia (estado) WHERE estado = 'pendiente';

-- ---------------------------------------------------------------------------
-- 13 notificacion
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test.notificacion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid REFERENCES test.usuario(id) ON DELETE SET NULL,
    tipo text NOT NULL,
    mensaje text NOT NULL,
    leida boolean NOT NULL DEFAULT false,
    fecha timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_notificacion_tipo CHECK (tipo IN ('bajo_stock', 'vencimiento_proximo', 'sugerencia_compra', 'sistema'))
);

CREATE INDEX IF NOT EXISTS idx_notificacion_usuario_no_leida ON test.notificacion (usuario_id) WHERE leida = false;