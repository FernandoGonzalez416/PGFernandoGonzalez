CREATE TABLE IF NOT EXISTS sugerencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    prediccion_id uuid NOT NULL REFERENCES prediccion(id) ON DELETE RESTRICT,
    producto_id uuid NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
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

CREATE INDEX IF NOT EXISTS idx_sugerencia_producto ON sugerencia (producto_id);
CREATE INDEX IF NOT EXISTS idx_sugerencia_pendiente ON sugerencia (estado) WHERE estado = 'pendiente';