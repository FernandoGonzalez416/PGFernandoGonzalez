# Reglas de arquitectura

## Arquitectura de referencia (tesis + decisiones confirmadas)

- **Frontend web**: React.js (aplicación web de escritorio responsive).
- **API / Backend**: FastAPI — backend/API principal; concentra la lógica de negocio (API REST).
- **Tareas livianas**: Node.js — adoptado para funciones serverless cuando corresponda (actualizaciones/procesos puntuales, notificaciones, tareas auxiliares). Cada función debe justificarse; no trasladar lógica arbitraria desde FastAPI.
- **Datos / Auth / Storage**: Supabase (PostgreSQL) — proyecto existente, no crear otro.
- **IA / predicción**: Scikit-learn — estrategia **aprobada** en `DECISIONES.md` (P3/P3a/P13). No implementar hasta autorización del desarrollo.
- **Móvil**: React Native — futura, fuera del alcance actual.

Cualquier desviación de esta arquitectura requiere justificación y confirmación del usuario.

## Principios obligatorios

- **Separación de capas**: presentación, lógica de negocio y acceso a datos son independientes.
- **Lógica de negocio fuera de los componentes React**: la UI consume servicios/contratos; no implementa reglas de negocio.
- **Frontend y backend bien separados**: comunicación únicamente vía contratos de API claros.
- **Sin acoplamiento innecesario al navegador** en la lógica de negocio: esto preserva la compatibilidad con una futura app móvil.
- **Backend como concentrador de lógica**: el frontend no debe duplicar validaciones de negocio críticas (inventario, ventas, alertas).

## Antes de decidir arquitectura

1. Revisar si ya existe una solución en el proyecto.
2. Revisar la tesis y `DECISIONES.md` para confirmar alcance.
3. Si la decisión es importante (dependencias grandes, nuevos servicios, cambios de modelo de datos o despliegue), **pedir confirmación antes de implementar**.
4. No adoptar tecnologías "porque son populares"; solo por decisión explícita del proyecto.

## Preparación para la futura app móvil (sin desarrollarla)

- Mantener contratos de API razonablemente claros y reutilizables.
- Mantener la lógica de negocio desacoplada de la UI web.
- NO crear código, carpetas ni configuraciones móviles en esta fase.

## Puntos abiertos (no decidir unilateralmente)

- Estrategia concreta de **offline/sincronización** para la fase web (no bloquea la primera versión). Ver `DECISIONES.md` y `offline-sincronizacion.md`.
- **Hosting/despliegue** (P12): pospuesto hasta que la aplicación esté avanzada.
- **Conexión MCP de Supabase (P17)**: pendiente de configuración; requiere el Project Ref del usuario. No modificar Supabase hasta que se indique.
- **Inicio del desarrollo** (código, dependencias, tablas, job de IA): solo tras orden explícita del usuario. La predicción (P3/P3a/P13), los permisos (P14), el esquema (P15) y las versiones (P16) ya están **aprobados**.

## Pautas adoptadas (resumen)

- **Iteración**: primera versión funcional y luego mejorar; sin complejidad innecesaria para problemas que no existen.
- **Offline**: no implementar arquitectura compleja en la primera versión; mantener la arquitectura abierta a offline/sincronización futura.
- **Despliegue/hosting**: fuera de las prioridades actuales.