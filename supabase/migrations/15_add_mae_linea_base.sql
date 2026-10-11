ALTER TABLE prediccion
ADD COLUMN IF NOT EXISTS mae_linea_base numeric(12,2)
CHECK (mae_linea_base IS NULL OR mae_linea_base >= 0);

COMMENT ON COLUMN prediccion.mae_linea_base IS 'MAE de la línea base (promedio móvil 7 días) en la misma ventana de validación; NULL si no aplica (P3/P3a/P13).';