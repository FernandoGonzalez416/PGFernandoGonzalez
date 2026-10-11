CREATE TABLE IF NOT EXISTS prediccion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id uuid NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    fecha_generacion timestamptz NOT NULL DEFAULT now(),
    inicio_horizonte date NOT NULL,
    fin_horizonte date NOT NULL,
    demanda_pronosticada numeric(12,2) NOT NULL,
    demanda_real numeric(12,2),
    intervalo_inf numeric(12,2),
    intervalo_sup numeric(12,2),
    metodo text NOT NULL,
    nivel_confianza text NOT NULL,
    mae_validacion numeric(12,2),
    wape_validacion numeric(12,2),
    nmae numeric(12,2),
    observaciones_usadas integer,
    datos_ficticios boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_prediccion_demanda CHECK (demanda_pronosticada >= 0),
    CONSTRAINT chk_prediccion_metodo CHECK (metodo IN ('promedio_movil', 'random_forest', 'hist_gradient_boosting', 'ridge', 'sin_historial')),
    CONSTRAINT chk_prediccion_confianza CHECK (nivel_confianza IN ('alta', 'baja', 'simulacion')),
    CONSTRAINT chk_prediccion_horizonte CHECK (fin_horizonte >= inicio_horizonte),
    CONSTRAINT chk_prediccion_intervalo CHECK (intervalo_inf IS NULL OR intervalo_sup IS NULL OR intervalo_inf <= intervalo_sup)
);

CREATE INDEX IF NOT EXISTS idx_prediccion_producto_fecha ON prediccion (producto_id, fecha_generacion DESC);

COMMENT ON TABLE prediccion IS 'Método y métricas según P13 (Random Forest/HistGB/Ridge vs. promedio móvil de 7 días).';
COMMENT ON COLUMN prediccion.datos_ficticios IS 'true mientras se use el dataset de prueba; nunca se mezcla con datos reales del piloto en el mismo análisis (P4).';