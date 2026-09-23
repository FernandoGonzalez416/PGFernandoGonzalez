-- Extensión para gen_random_uuid() (P15: UUID como identificador en todas las tablas).
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Función compartida para mantener updated_at sincronizado en cada UPDATE.
-- No estaba en P15 explícitamente; se agrega como buena práctica de auditoría (ver nota al final).
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;