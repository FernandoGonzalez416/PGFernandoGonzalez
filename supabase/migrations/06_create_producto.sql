CREATE TABLE IF NOT EXISTS producto (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo text NOT NULL,
    nombre text NOT NULL,
    descripcion text,
    categoria_id uuid NOT NULL REFERENCES categoria(id) ON DELETE RESTRICT,
    proveedor_id uuid REFERENCES proveedor(id) ON DELETE SET NULL,
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

CREATE INDEX IF NOT EXISTS idx_producto_categoria ON producto (categoria_id);
CREATE INDEX IF NOT EXISTS idx_producto_proveedor ON producto (proveedor_id);
CREATE INDEX IF NOT EXISTS idx_producto_nombre ON producto (lower(nombre));
CREATE INDEX IF NOT EXISTS idx_producto_vencimiento ON producto (fecha_vencimiento) WHERE fecha_vencimiento IS NOT NULL;

CREATE TRIGGER trg_producto_updated_at
    BEFORE UPDATE ON producto
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON COLUMN producto.fecha_vencimiento IS 'NULL = no perecedero. Diseño abierto a una futura entidad lote sin romper este esquema (P15).';