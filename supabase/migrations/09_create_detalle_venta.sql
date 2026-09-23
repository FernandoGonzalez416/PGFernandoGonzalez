CREATE TABLE IF NOT EXISTS detalle_venta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    venta_id uuid NOT NULL REFERENCES venta(id) ON DELETE RESTRICT,
    producto_id uuid NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    cantidad integer NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    CONSTRAINT uq_detalle_venta_producto UNIQUE (venta_id, producto_id),
    CONSTRAINT chk_detalle_venta_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_detalle_venta_precio CHECK (precio_unitario >= 0),
    CONSTRAINT chk_detalle_venta_subtotal CHECK (subtotal >= 0),
    CONSTRAINT chk_detalle_venta_calculo CHECK (subtotal = cantidad * precio_unitario)
);

CREATE INDEX IF NOT EXISTS idx_detalle_venta_producto ON detalle_venta (producto_id);

COMMENT ON TABLE detalle_venta IS 'precio_unitario se congela al momento de la venta; no se recalcula si producto.precio_venta cambia después.';