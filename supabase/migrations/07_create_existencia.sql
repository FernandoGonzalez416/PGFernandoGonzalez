CREATE TABLE IF NOT EXISTS existencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id uuid NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    almacen_id uuid NOT NULL REFERENCES almacen(id) ON DELETE RESTRICT,
    cantidad numeric(12,2) NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_existencia_producto_almacen UNIQUE (producto_id, almacen_id),
    CONSTRAINT chk_existencia_cantidad CHECK (cantidad >= 0)
);

CREATE INDEX IF NOT EXISTS idx_existencia_almacen ON existencia (almacen_id);

CREATE TRIGGER trg_existencia_updated_at
    BEFORE UPDATE ON existencia
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE existencia IS 'Stock agregado por producto y almacén, sin granularidad por lote en esta fase (P15).';