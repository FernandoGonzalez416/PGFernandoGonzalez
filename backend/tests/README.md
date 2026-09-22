# tests

Pruebas del backend (pytest). Convención: colocar cada test junto al dominio que verifica, p. ej. `tests/test_ventas.py`, `tests/test_inventario.py`, `tests/test_alertas.py` (regla `testing.md`).

Configuración: `pytest.ini` (testpaths, `asyncio_mode=auto`).

Fase 1: sin pruebas de negocio todavía — se escriben cuando exista lógica que probar (totales de venta, descuento de inventario, alertas, auth por rol P14, criterio de predicción); ver `testing.md`.