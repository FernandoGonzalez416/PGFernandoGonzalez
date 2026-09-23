-- 14_enable_rls.sql
-- Habilita RLS en las 13 tablas con denegación total por defecto (sin políticas).
-- service_role (usado por FastAPI) NO se ve afectado por RLS bajo ninguna circunstancia.
-- anon/authenticated quedan sin acceso hasta que se agreguen políticas explícitas,
-- una vez decidido el patrón de acceso del frontend.

ALTER TABLE categoria ENABLE ROW LEVEL SECURITY;
ALTER TABLE proveedor ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE almacen ENABLE ROW LEVEL SECURITY;
ALTER TABLE producto ENABLE ROW LEVEL SECURITY;
ALTER TABLE existencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE venta ENABLE ROW LEVEL SECURITY;
ALTER TABLE detalle_venta ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimiento_inventario ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediccion ENABLE ROW LEVEL SECURITY;
ALTER TABLE sugerencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificacion ENABLE ROW LEVEL SECURITY;