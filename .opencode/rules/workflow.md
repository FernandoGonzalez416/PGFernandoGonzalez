# Reglas de workflow de desarrollo

Antes de modificar código:

1. **Entender la tarea**: objetivo, entradas, salidas esperadas y contexto.
2. **Inspeccionar el código relacionado**: leer los archivos que se van a tocar y sus alrededores.
3. **Buscar implementaciones existentes**: reutilizar antes de crear.
4. **Identificar dependencias**: librerías, servicios, tablas, contratos y consumidores afectados.
5. **Determinar el alcance del cambio**: qué se modifica y qué no.
6. **Implementar la solución mínima necesaria**.
7. **Ejecutar las pruebas correspondientes** (y lint/typecheck si aplica).
8. **Revisar los cambios**: verificar el diff y el comportamiento antes de terminar.
9. **Informar qué se modificó**: archivos, decisiones y pendientes.

## Reglas

- **No realizar refactorizaciones masivas** cuando la tarea no las requiere.
- **No modificar archivos no relacionados** sin justificación.
- Si el cambio toca arquitectura, modelo de datos, dependencias importantes o contratos de API, **confirmar antes de implementar** (ver `AGENTS.md` para la jerarquía de autoridad).
- Todo cambio debe mantener la coherencia con las reglas del proyecto.
- Al terminar, verificar que no hayan quedado secretos, archivos temporales ni código sin usar.

## Git

- **Solo commitear cuando el usuario lo pida explícitamente**; en ese caso revisar `git status`/`git diff`, preparar solo lo intencionado y nunca incluir secretos.
- Repositorio remoto del proyecto: `https://github.com/FernandoGonzalez416/PGFernandoGonzalez`.
- Mantener el `.gitignore` actualizado (Node.js, Python, `.env`, credenciales, temporales, builds, dependencias).

## Decisiones pendientes detectadas durante el trabajo

- Registrarlas en `DECISIONES.md` cuando corresponda y señalarlas al usuario.
- Nunca resolver una decisión arquitectónica importante por cuenta propia sin confirmación.