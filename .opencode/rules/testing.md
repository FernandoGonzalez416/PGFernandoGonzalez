# Reglas de testing

Las funcionalidades importantes requieren pruebas razonables. No se crean pruebas falsas para inflar cobertura.

## Stack de testing (decidido 2026-09-21)

Instalado como dependencias de **desarrollo** únicamente (Fase 1; las pruebas de negocio se escriben cuando exista lógica que probar).

**Backend** (Python 3.14.x, FastAPI 0.141.1, Starlette 1.6.0) — pines exactos en `backend/requirements-dev.txt` (mismo criterio que P16):

| Paquete | Versión | Nota |
|---|---|---|
| pytest | 9.1.1 | requires_python ≥ 3.10 |
| pytest-asyncio | 1.4.0 | `asyncio_mode = auto` en `backend/pytest.ini` |
| httpx2 | 2.13.0 | **reemplaza a httpx**: Starlette 1.6.0 deprecó `httpx` en `TestClient` y recomienda `httpx2` (decisión confirmada por el usuario — ver **P18** en `DECISIONES.md`) |

Configuración: `backend/pytest.ini` (`testpaths = tests`, `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`, `pythonpath = .`).

**Frontend** (React 19.3.0, Vite 8.3.0, TypeScript 6.0.3) — devDependencies con rango `^` + `package-lock.json` (mismo criterio que P16):

| Paquete | Versión | Nota |
|---|---|---|
| vitest | 5.0.1 | exige Vite ^6.4\|^7\|^8 (ok 8.3.0); Node ^22.12\|^24 (ok) |
| @testing-library/react | 16.3.3 | peer: React ^18\|^19, @testing-library/dom ^10 |
| @testing-library/jest-dom | 7.0.1 | peer: vitest ≥ 0.32, @testing-library/dom <11 |
| @testing-library/dom | 10.4.2 | peer obligatorio de los dos anteriores |
| jsdom | 30.1.1 | entorno de pruebas |

Configuración: `frontend/vitest.config.ts` (entorno `jsdom`, `setupFiles = ./src/test/setup.ts`), script `npm run test` (`vitest run`). El setup importa `@testing-library/jest-dom/vitest`. `vitest.config.ts` está incluido en `tsconfig.node.json`.

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

- **Backend**: pytest con `testpaths = tests` en `backend/tests/`, un archivo por dominio (p. ej. `tests/test_ventas.py`, `tests/test_inventario.py`, `tests/test_alertas.py`).
- **Frontend**: vitest coloca los tests junto al código que verifican (patrón `*.test.ts(x)`); ver ejemplo de convención en cuanto exista el primer test real.