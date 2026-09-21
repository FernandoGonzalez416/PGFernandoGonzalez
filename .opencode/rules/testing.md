# Reglas de testing

Las funcionalidades importantes requieren pruebas razonables. No se crean pruebas falsas para inflar cobertura.

## Funcionalidades que deben tener pruebas

Especialmente:

- Lógica de inventario.
- Movimientos de inventario.
- Ventas (creación, folio, descuento de stock, disponibilidad).
- Cálculos (totales, desperdicios, umbrales).
- Reglas de alertas (stock bajo, vencimiento próximo).
- Autenticación y autorización.
- Predicciones (método de respaldo, marcado de baja confianza).
- Endpoints críticos (contratos y errores).

## Reglas

- **No crear pruebas falsas** ni tests que siempre pasan sin verificar comportamiento real.
- Cada prueba debe verificar un comportamiento observable y determinista.
- Mantener las pruebas alineadas con los contratos de API y el modelo de datos reales.
- Preferir pruebas enfocadas (unitarias e integración) sobre cobertura genérica sin valor.
- Antes de finalizar una tarea, **ejecutar las pruebas correspondientes** (y lint/typecheck si el proyecto los define) y reportar el resultado.
- No inventar datos de entrenamiento ni resultados: cualquier test con datos simulados debe etiquetarse como tal.

## Organización

- Colocar las pruebas junto al código que verifican, siguiendo la convención que se adopte al inicializar cada parte (a definir con el usuario si no existe).