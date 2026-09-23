CREATE TABLE IF NOT EXISTS notificacion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid REFERENCES usuario(id) ON DELETE SET NULL,
    tipo text NOT NULL,
    mensaje text NOT NULL,
    leida boolean NOT NULL DEFAULT false,
    fecha timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_notificacion_tipo CHECK (tipo IN ('bajo_stock', 'vencimiento_proximo', 'sugerencia_compra', 'sistema'))
);

CREATE INDEX IF NOT EXISTS idx_notificacion_usuario_no_leida ON notificacion (usuario_id) WHERE leida = false;