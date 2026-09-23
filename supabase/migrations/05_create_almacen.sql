CREATE TABLE IF NOT EXISTS almacen (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    ubicacion text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_almacen_nombre UNIQUE (nombre)
);

CREATE TRIGGER trg_almacen_updated_at
    BEFORE UPDATE ON almacen
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE almacen IS 'P15: un solo almacén en esta fase; existe como tabla desde ahora para no requerir migración estructural si se agrega una sucursal.';