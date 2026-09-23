CREATE TABLE IF NOT EXISTS movimiento_inventario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id uuid NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    almacen_id uuid REFERENCES almacen(id) ON DELETE SET NULL,
    tipo text NOT NULL,
    referencia_tipo text NOT NULL,
    referencia_id uuid,
    cantidad numeric(12,2) NOT NULL,
    usuario_id uuid REFERENCES usuario(id) ON DELETE SET NULL,
    nota text,
    fecha timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_movimiento_tipo CHECK (tipo IN ('entrada', 'salida', 'ajuste')),
    CONSTRAINT chk_movimiento_referencia_tipo CHECK (referencia_tipo IN ('venta', 'compra', 'ajuste', 'vencimiento', 'devolucion', 'inicial')),
    CONSTRAINT chk_movimiento_cantidad CHECK (cantidad > 0)
);

CREATE INDEX IF NOT EXISTS idx_movimiento_producto_fecha ON movimiento_inventario (producto_id, fecha);
CREATE INDEX IF NOT EXISTS idx_movimiento_referencia ON movimiento_inventario (referencia_tipo, referencia_id);

COMMENT ON TABLE movimiento_inventario IS 'Bitácora inmutable: solo INSERT, nunca UPDATE ni DELETE.';
COMMENT ON COLUMN movimiento_inventario.referencia_id IS 'Referencia polimórfica manual (apunta a venta.id u otra tabla según referencia_tipo). Sin FK real por diseño — limitación conocida de este patrón; la integridad se valida en la capa de servicio, no en la BD.';