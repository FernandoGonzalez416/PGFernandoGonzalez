-- 16_add_client_request_id_venta.sql
--
-- Idempotencia para la sincronización offline (P27/F5): el POS genera un
-- client_request_id (UUID v4) por venta y lo reenvía en cada reintento con el
-- mismo valor. El UNIQUE parcial garantiza una sola fila por id sin impedir
-- ventas sin id (NULL).
ALTER TABLE venta
ADD COLUMN IF NOT EXISTS client_request_id uuid NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_venta_client_request_id
ON venta (client_request_id)
WHERE client_request_id IS NOT NULL;

COMMENT ON COLUMN venta.client_request_id IS 'UUID generado por el cliente (POS offline) para reintentos idempotentes; UNIQUE parcial, NULL = venta en línea sin id.';
