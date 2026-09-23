CREATE TABLE IF NOT EXISTS proveedor (
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

CREATE INDEX IF NOT EXISTS idx_proveedor_nombre ON proveedor (lower(nombre));

CREATE TRIGGER trg_proveedor_updated_at
    BEFORE UPDATE ON proveedor
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE proveedor IS 'P15: relación uno-a-uno con producto (proveedor habitual), no muchos-a-muchos en esta fase.';