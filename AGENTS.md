# AGENTS.md — Plataforma inteligente de inventarios y reabastecimiento

Guía principal para los agentes de IA que trabajan en este proyecto. Leer antes de cualquier tarea.

---

## Contexto del proyecto

Plataforma inteligente para la optimización de inventarios y reabastecimiento en tiendas de cosméticos. Está basada en el proyecto de graduación *"Plataforma inteligente basada en la nube con capacidad offline para la gestión de inventarios y reabastecimiento en tiendas cosméticas"* (Universidad Mariano Gálvez de Guatemala). El documento de referencia es la tesis **`Fernando Gonzalez PG 2 UNIVERSIDAD MARIANO GALVEZ DE GUATEMALA.docx`**, ubicada en la raíz de este repositorio.

Caso de estudio piloto: negocio familiar de venta de cosméticos en un mercado municipal de **Villa Nueva, Guatemala**. La implementación actual debe resolver ese caso concreto sin cerrar la puerta a otros comercios.

## Alcance actual

> Actualmente solo se desarrolla la aplicación Web. La aplicación móvil queda para una fase posterior.

- Se construye: frontend web (React.js), API (FastAPI), tareas livianas con Node.js cuando corresponda, base de datos (Supabase), autenticación, lógica de negocio, productos, categorías, proveedores, inventario, ventas, alertas, reabastecimiento, reportes, predicción, testing y documentación técnica.
- **Prohibido en esta fase**: crear aplicación React Native, carpetas mobile, instalar React Native/Expo, navegación, componentes, stores o servicios móviles. No preparar una app móvil "por si acaso".
- La arquitectura sí debe mantener separados frontend y backend, la lógica de negocio fuera de componentes React, contratos de API claros y presentación/lógica/datos separados, para que una futura app móvil no requiera reescribir la base.

## Fuentes de verdad y jerarquía de autoridad

Ante cualquier conflicto, esta es la prioridad:

1. Instrucciones explícitas del usuario.
2. Requisitos confirmados del proyecto (tesis + decisiones documentadas del usuario).
3. Código y arquitectura existente.
4. Este `AGENTS.md`.
5. Reglas específicas en `.opencode/rules/`.
6. Decisiones documentadas en `DECISIONES.md`.
7. Convenciones generales de frameworks/lenguajes.

Una convención genérica o una moda tecnológica **nunca** se impone sobre una decisión explícita del proyecto.

## Regla fundamental: no inventar

> **Si algo no está definido, el agente NO debe inventarlo.**

Antes de agregar una dependencia, crear un servicio/módulo/tabla o cambiar arquitectura:

1. Detectar la ambigüedad o ausencia.
2. Explicar exactamente qué falta definir.
3. Proponer alternativas si corresponde.
4. Solicitar confirmación antes de tomar una decisión arquitectónica importante.

No asumir que una tecnología es correcta "porque es popular". Primero revisar si ya existe una solución en el proyecto.

## Arquitectura conocida (definida por la tesis + decisiones confirmadas)

- **Aplicación Web**: React.js — cliente actual.
- **API / Backend**: FastAPI — backend/API principal; concentra la lógica de negocio (API REST).
- **Base de datos / Auth / Storage**: Supabase (PostgreSQL). Ya existe un proyecto de Supabase; no crear otro (ver `DECISIONES.md`).
- **Node.js**: adoptado para **tareas livianas/serverless cuando corresponda** (actualizaciones o procesos puntuales, notificaciones, tareas auxiliares). Cada función Node.js debe justificarse; no trasladar lógica arbitraria desde FastAPI (P1).
- **IA / predicción**: Scikit-learn — estrategia **aprobada** en `DECISIONES.md` (P3/P3a/P13): Random Forest principal + HistGB/Ridge de contraste, comparación contra el promedio móvil de 7 días, horizonte de 7 días, umbral 75 días + densidad, confianza por evidencia (se eliminó el «MAE ≤ 30 %»). **No implementar hasta que se autorice el desarrollo.**
- **Aplicación móvil**: React Native — futura, fuera de alcance.

## Tecnologías confirmadas

- React.js (web)
- FastAPI (API principal)
- Node.js (tareas livianas/serverless, según P1)
- Supabase (PostgreSQL, Auth, Storage)
- Scikit-learn (predicción)

Las **versiones** fueron investigadas y aprobadas en `DECISIONES.md` (**P16**): backend con **pines exactos**, frontend con **rangos `^` + `package-lock.json`**, Node **24 LTS sin pin**. **No instalar dependencias** hasta que se autorice el desarrollo; revalidar Vite/react-router al hacer el scaffold (P11).

## Decisiones clave adoptadas (resumen; ver `DECISIONES.md`)

- **Offline**: no es obligatorio en la primera versión; se construye primero una versión funcional y se itera. No asumir IndexedDB/PWA/Service Workers. La estrategia definitiva se documentará cuando se implemente (P2).
- **Usuarios y roles**: administrador, dueño del negocio y padre del dueño. **Permisos aprobados en P14**: el padre opera (ventas, consultas, alertas, sugerencias) y **puede anular solo sus propias ventas**; no administra usuarios, roles ni configuración. Sin roles empresariales complejos (P5).
- **Diseño web**: aplicación **web de escritorio responsive** (prioridad: escritorio; luego teléfono por navegador). Conservar la identidad visual oficial **nude/terracota/café** de "Familia de la Cruz" (blanco crema, rosa nude, terracota, café oscuro, gloss soft; títulos Playfair Display + cuerpo Montserrat) sin copiar navegación móvil (P7).
- **Comprobante de venta**: recibo interno con folio único, imprimible y descargable en PDF; **no** es factura tributaria ni SAT/FEL (P8).
- **Datos**: durante desarrollo se usan **datos ficticios claramente identificados como prueba**; en el piloto se acumulan datos reales desde el inicio. Nunca presentar ficticios como reales (P4).
- **Predicción**: estrategia **aprobada** (P3/P3a/P13) — Random Forest/HistGB/Ridge vs promedio móvil de 7 días, horizonte de 7 días, suficiencia por 75 días + densidad, confianza por evidencia. Los datos ficticios sirven para desarrollo/pruebas, **no demuestran precisión real** del modelo.
- **Git**: se usa desde el inicio; repositorio remoto existente `https://github.com/FernandoGonzalez416/PGFernandoGonzalez`; `.gitignore` obligatorio; nunca subir secretos (P10). La tesis `.docx` de 4.5 MB **SÍ se incluye** en el repositorio (documento de referencia principal; no está en `.gitignore`).
- **Hosting**: fuera de las prioridades actuales (P12).
- **Iteración**: desarrollo incremental; primera versión funcional sin complejidad innecesaria, sin cerrar posibilidades futuras.

## Modelo de datos de referencia (entidades nombradas en la tesis)

Producto, Categoría, Proveedor, Cliente, Usuario, Venta, DetalleVenta, Almacén, Existencia, MovimientoInventario, Predicción, Sugerencia, Notificación.

El **esquema inicial está APROBADO** en `DECISIONES.md` (**P15**): las 13 entidades con campos, tipos, PK/FK y restricciones. **Sin entidad `Lote`** en esta fase: el vencimiento se maneja con `Producto.fechaVencimiento` (lote activo; NULL = no perecedero) y el diseño no cierra la incorporación de lotes a futuro (verificar relaciones/restricciones antes de crear tablas). No crear entidades innecesarias (P6).

## Requerimientos funcionales confirmados (tesis, Cap. IV)

1. Registrar productos con datos básicos (nombre, categoría, cantidad, proveedor, fecha de ingreso, precio).
2. Consultar la cantidad disponible de un producto (búsqueda por nombre, código o categoría).
3. Alertas: producto en **nivel bajo de existencias** (umbral mínimo configurado por producto) y **vencimiento próximo**.
4. Registrar **ventas** con descuento automático del inventario, folio único, **comprobante (recibo interno)** y validación de disponibilidad.
5. Gestión de **proveedores** habituales (precios y condiciones de entrega).
6. **Reportes** sencillos de productos más vendidos en un periodo.
7. **Predicción de demanda** (job programado diario): usa historial de ventas por producto, inventario actual y estacionalidad; si el historial es insuficiente se aplica promedio móvil y el pronóstico se marca como de baja confianza; genera sugerencia de compra y notifica al responsable.

Requerimientos no funcionales confirmados: interfaz intuitiva (sin conocimientos técnicos), autenticación obligatoria, respuesta breve en consultas. La **operación sin conexión** sigue siendo un requisito de la solución final, pero no bloquea la primera versión funcional (P2).

## Reglas generales de desarrollo

- Analizar antes de modificar; nunca "saltar a escribir código".
- Reutilizar código existente cuando corresponda; evitar duplicación.
- Mantener separación de responsabilidades.
- Evitar cambios innecesarios; implementar la solución mínima.
- Mantener coherencia arquitectónica con lo ya existente.
- Documentar decisiones importantes (en memoria persistente y en el código cuando proceda).
- Realizar pruebas cuando corresponda.
- No refactorizaciones masivas si la tarea no las requiere.
- No modificar archivos no relacionados sin justificación.
- Desarrollar de forma **incremental** (regla de iteración): base correcta → versión funcional → iterar.

## Testing

Las funcionalidades importantes requieren pruebas razonables: inventario, movimientos de inventario, ventas, cálculos, reglas de alertas, autenticación, predicciones y endpoints críticos. No crear pruebas falsas para inflar cobertura.

## Seguridad

- Secretos siempre en variables de entorno; nunca en archivos del repositorio ni en código.
- No desactivar seguridad solo para que algo funcione.
- No ignorar errores de autenticación o autorización.
- Revisar consumidores antes de modificar contratos de endpoints.
- Nunca subir secretos al repositorio (remoto GitHub incluido).

## Tesis vs implementación

La tesis y la implementación deben mantenerse relacionadas, pero **no modificar el documento académico para que coincida con el código**. Si se detecta una diferencia entre lo documentado y lo implementado (o entre requisitos y código), se debe **señalar** la discrepancia, nunca corregirla silenciosamente ni afirmar que una funcionalidad existe cuando no existe.

## Reglas específicas del proyecto

Reglas detalladas por dominio: `.opencode/rules/` (se cargan automáticamente vía `opencode.json`).

| Archivo | Tema |
|---|---|
| `general.md` | Reglas generales del proyecto |
| `arquitectura.md` | Arquitectura |
| `frontend-web.md` | Frontend web (React.js) |
| `diseno.md` | Diseño visual del frontend (paleta, tipografía, motion) |
| `backend.md` | Backend (FastAPI + Node.js) |
| `base-de-datos.md` | Base de datos (Supabase) |
| `offline-sincronizacion.md` | Offline / sincronización |
| `ia-prediccion.md` | Inteligencia artificial / predicción |
| `seguridad.md` | Seguridad |
| `testing.md` | Testing |
| `workflow.md` | Workflow de desarrollo |

NOTA: **no existe** `mobile.md`: la app móvil está fuera del alcance actual.