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

## Pruebas obligatorias

Deben existir pruebas para, al menos:

- **Cálculo de totales de venta** (subtotal, descuento, total; incluye las reglas de redondeo usadas).
- **Descuento de inventario** al registrar una venta (stock correcto antes/después, y el movimiento trazable correspondiente).
- **Reglas de alertas**: umbral de stock bajo (`umbralMinimo`) y vencimiento próximo (`diasVencimientoAviso`).
- **Autenticación y permisos por rol** conforme a la matriz P14 (qué puede hacer cada uno de los 3 usuarios, incluida la anulación del padre solo de sus propias ventas).
- **Criterio de selección del modelo de predicción vs. línea base (promedio móvil)**: que el candidato solo se despliegue si vence a la línea base en validación temporal, y que sin historial suficiente se use el respaldo con "baja confianza" (P3/P3a/P13).

## Datos de prueba

- Usar siempre **datos ficticios marcados explícitamente como prueba** (coherente con P4 de `DECISIONES.md`): deben etiquetarse como simulación y jamás presentarse como datos reales del negocio.
- No inventar datos de entrenamiento ni resultados: cualquier test con datos simulados debe etiquetarse como tal.

## Reglas

- **No crear pruebas falsas** ni tests que siempre pasan sin verificar comportamiento real.
- **Prohibidas las pruebas triviales** que solo verifican "no truena" (que no lanza excepción) sin comprobar el resultado esperado.
- **Prohibido inflar cobertura** con pruebas de getters/setters u otros accesores sin lógica real detrás.
- Cada prueba debe verificar un comportamiento observable y determinista.
- Mantener las pruebas alineadas con los contratos de API y el modelo de datos reales.
- Preferir pruebas enfocadas (unitarias e integración) sobre cobertura genérica sin valor.
- Antes de finalizar una tarea, **ejecutar las pruebas correspondientes** (y lint/typecheck si el proyecto los define) y reportar el resultado.

## Organización

- Colocar las pruebas junto al código que verifican, siguiendo la convención que se adopte al inicializar cada parte (a definir con el usuario si no existe).