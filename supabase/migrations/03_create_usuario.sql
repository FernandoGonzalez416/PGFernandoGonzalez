CREATE TABLE IF NOT EXISTS usuario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id uuid NOT NULL,
    nombre text NOT NULL,
    email text NOT NULL,
    rol text NOT NULL,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_usuario_auth_id UNIQUE (auth_id),
    CONSTRAINT uq_usuario_email UNIQUE (email),
    CONSTRAINT fk_usuario_auth FOREIGN KEY (auth_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT chk_usuario_rol CHECK (rol IN ('administrador', 'propietario', 'padre'))
);

CREATE INDEX IF NOT EXISTS idx_usuario_rol_activo ON usuario (rol) WHERE activo = true;

CREATE TRIGGER trg_usuario_updated_at
    BEFORE UPDATE ON usuario
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE usuario IS 'Perfil de aplicación 1:1 con auth.users de Supabase Auth. Roles según P14: administrador, propietario, padre.';