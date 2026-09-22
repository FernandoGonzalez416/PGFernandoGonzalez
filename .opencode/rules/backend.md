# Reglas del backend (FastAPI + Node.js)

FastAPI es la tecnología definida para la API/backend principal, salvo que el análisis del repositorio demuestre otra situación.

## División de responsabilidades (P1)

- **FastAPI**: backend/API principal y **concentra la lógica de negocio** (API REST).
- **Node.js**: solo para **tareas livianas/serverless cuando corresponda** (actualizaciones o procesos puntuales, notificaciones, tareas auxiliares).
  - Cada función Node.js debe **justificarse** según P1 (qué aporta, por qué no va en FastAPI). Si no hay una razón clara para que sea serverless, la lógica va en FastAPI.
  - **No trasladar lógica arbitrariamente** de FastAPI a Node.js.
  - **No crear funciones Node.js** solo porque la tecnología está disponible.

## Organización

- **Rutas/endpoints separados** de la lógica de negocio: los endpoint handlers son delgados; la lógica vive en servicios/módulos dedicados.
- **Routers separados por dominio**: `routers/productos.py`, `routers/ventas.py`, `routers/inventario.py`, `routers/proveedores.py`, `routers/alertas.py`, `routers/prediccion.py` (y los que el dominio justifique), cada uno con su prefijo y responsabilidad.
- **Esquemas Pydantic para todo request/response** (schemas): nunca exponer `dict` sueltos en los handlers; todo payload que entra o sale de la API pasa por un modelo Pydantic.
- **Lógica de negocio en la capa de servicio**, no en el router: el handler solo orquesta (valida entrada, llama al servicio, devuelve la respuesta). Si un handler crece, se extrae lógica al servicio.
- **Validación en dos niveles**:
  1. **Pydantic en el borde** (formato/tipos/obligatoriedad de los campos);
  2. **Reglas de negocio explícitas en el servicio** (p. ej. stock suficiente antes de descontar inventario, folio no repetido, vencimiento válido).
  La validación de negocio nunca vive solo en el schema.
- **Manejo consistente de errores**: respuestas de error con formato uniforme, códigos HTTP coherentes (4xx/5xx) y mensajes accionables sin exponer detalles internos.
- **Excepciones tipadas propias del dominio** (p. ej. `StockInsuficienteError`, `ProductoNoEncontradoError`): el mapeo a códigos HTTP ocurre una sola vez, en un handler global de errores. **Prohibido capturar excepciones y silenciarlas** sin loguear o re-lanzar. No ocultar fallos para "que pase la prueba".
- **Contratos claros**: documentar los endpoints (nombres, métodos, payloads, códigos de respuesta) y mantenerlos coherentes con el frontend.

## Reglas de negocio del backend

La lógica de negocio reside aquí y debe cuidar, al menos:

- **Inventario**: descuento/ajuste de existencias únicamente a través de movimientos de inventario trazables.
- **Ventas**: folio único, validación de disponibilidad antes del cobro, **comprobante (recibo interno no tributario)** y efectos atómicos (no se puede descontar inventario si falla la venta, y viceversa).
- **Alertas**: comparación de stock contra umbral mínimo configurado por producto y vencimientos próximos.
- **Predicción**: orquestar el microservicio de IA y persistir resultados (ver `ia-prediccion.md`).

## Contratos y cambios

- **No crear endpoints duplicados**: revisar lo existente antes de añadir.
- **No modificar contratos existentes sin revisar sus consumidores** (frontend y, a futuro, móvil). Si un cambio es necesario, evaluar compatibilidad y comunicarlo.
- Mantener la separación para que una futura app móvil consuma la misma API sin reescribir.

## Seguridad

- Autenticación/autorización obligatorias en endpoints sensibles (ver `seguridad.md`).
- Nunca colocar secretos en código ni en el repositorio.
- No desactivar seguridad para "que funcione".

## Versionado / documentación

- Usar la documentación automática de FastAPI (OpenAPI) como fuente de consulta y verificación de contratos.
- Al finalizar cada backend, verificar que la API arranca y los endpoints responden.