CREATE TABLE IF NOT EXISTS cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    telefono text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cliente_nombre ON cliente (lower(nombre));

CREATE TRIGGER trg_cliente_updated_at
    BEFORE UPDATE ON cliente
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();