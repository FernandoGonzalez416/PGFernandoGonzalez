# Reglas de workflow de desarrollo

Antes de cualquier tarea que cree, modifique o borre archivos, ejecutar `pwd` (o `Get-Location`) y `git remote -v`, y confirmar explícitamente que el remote apunta a FernandoGonzalez416/PGFernandoGonzalez antes de continuar. Si no coincide, detenerse y reportarlo — nunca asumir que el directorio es el correcto.

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

## Antes de escribir código de una fase

- **Releer** `AGENTS.md`, `DECISIONES.md` y la regla del dominio correspondiente (`.opencode/rules/`) antes de empezar a modificar código.
- Si la fase introduce código nuevo, confirmar primero el estado de lo aprobado y de lo pendiente de decisión en `DECISIONES.md`.

## Regla "no inventar" aplicada al workfow

- Si algo **no está definido** (característica, campo, contrato, dependencia, arquitectura), **detener**, **explicar qué falta definir**, **proponer alternativas** y **pedir confirmación explícita** al usuario antes de decidir.
- No resolver ambigüedades con suposiciones "razonables" cuando la decisión afecte arquitectura, modelo de datos, dependencias o contratos de API.

## Reglas

- **No realizar refactorizaciones masivas** cuando la tarea no las requiere.
- **No modificar archivos no relacionados** sin justificación.
- Los **cambios de arquitectura, aunque parezcan una mejora obvia, requieren confirmación explícita** del usuario antes de aplicarse. Confirmar siempre antes de: agregar una dependencia nueva, crear un servicio/módulo/tabla, cambiar un esquema o desplegar.
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