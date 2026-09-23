CREATE TABLE IF NOT EXISTS venta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    folio text NOT NULL,
    fecha timestamptz NOT NULL DEFAULT now(),
    cliente_id uuid REFERENCES cliente(id) ON DELETE SET NULL,
    usuario_id uuid NOT NULL REFERENCES usuario(id) ON DELETE RESTRICT,
    metodo_pago text NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    descuento numeric(12,2) NOT NULL DEFAULT 0,
    total numeric(12,2) NOT NULL,
    estado text NOT NULL DEFAULT 'activa',
    motivo_anulacion text,
    created_at timestamptz NOT NULL DEFAULT now(),
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

CREATE INDEX IF NOT EXISTS idx_venta_fecha ON venta (fecha);
CREATE INDEX IF NOT EXISTS idx_venta_cliente ON venta (cliente_id);
CREATE INDEX IF NOT EXISTS idx_venta_usuario ON venta (usuario_id);

COMMENT ON TABLE venta IS 'Nunca se hace DELETE; anulación es estado=anulada. La regla de "el padre solo anula sus propias ventas" (P14) se aplica en la capa de servicio, no aquí — la BD solo garantiza que toda anulación tenga motivo.';