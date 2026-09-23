CREATE TABLE IF NOT EXISTS categoria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    descripcion text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Unicidad case-insensitive: evita "Labiales" y "labiales" como categorías distintas.
CREATE UNIQUE INDEX IF NOT EXISTS uq_categoria_nombre ON categoria (lower(nombre));

CREATE TRIGGER trg_categoria_updated_at
    BEFORE UPDATE ON categoria
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE categoria IS 'Catálogo de categorías de producto. Soft delete vía activo=false; nunca DELETE.';