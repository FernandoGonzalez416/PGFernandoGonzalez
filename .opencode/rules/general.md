# Reglas generales del proyecto

Reglas transversales de trabajo para cualquier tarea en este repositorio. Aplican en combinación con `AGENTS.md`.

## Antes de escribir código

- Entender la tarea y su contexto antes de modificar.
- Inspeccionar el código relacionado.
- Buscar implementaciones existentes que se puedan reutilizar.
- Identificar dependencias y consumidores afectados.
- Determinar el alcance real del cambio.

## Fundamentales

- **No inventar**: si algo no está definido, no se inventa. Detectar la ambigüedad, explicar qué falta decidir, proponer alternativas y pedir confirmación.
- **Solución mínima**: implementar lo mínimo necesario para resolver la tarea. No añadir funcionalidades no solicitadas.
- **Sin duplicación**: reutilizar código existente antes de crear versiones paralelas.
- **Separación de responsabilidades**: presentación, lógica de negocio y acceso a datos permanecen separados.
- **Coherencia**: mantener el estilo, patrones y convenciones ya presentes en el proyecto.
- **Documentar**: registrar decisiones importantes (ver `DECISIONES.md`) y en el código cuando proceda.
- **Probar**: ejecutar las pruebas correspondientes y verificar el comportamiento antes de dar por terminada una tarea.

## Qué NO hacer

- No refactorizar en masa sin justificación.
- No modificar archivos no relacionados con la tarea.
- No omitir comprobaciones de pruebas/lint si el proyecto las define.
- No asumir que el código previo es correcto sin verificarlo.
- No mezclar categorías: lo confirmado, lo documentado, lo pendiente de implementar y lo pendiente de decidir deben distinguirse.

## Iteración (regla de iteración)

- Desarrollar de forma **incremental**: base correcta → primera versión funcional → probar → detectar problemas → mejorar.
- No sacrificar la arquitectura por velocidad, pero **no añadir complejidad innecesaria** para problemas que todavía no existen.
- Una solución simple inicial es válida si no cierra innecesariamente posibilidades futuras.

## Calidad del código

- **Nombres explícitos**, sin abreviaturas crípticas ni siglas inventadas: el identificador debe comunicar su propósito por sí solo (p. ej. `calcularTotalVenta`, no `calcTV`).
- **Funciones con una sola responsabilidad**: una función hace una cosa y la hace bien; si hay que explicar su comportamiento en una frase compleja, conviene dividirla.
- **Prohibido código muerto**, código comentado "por si acaso" y TODOs sin nota en `DECISIONES.md`. Si un bloque no se usa, se elimina; si se deja un pendiente, se registra la decisión/nota y se referencia aquí.
- **Antes de cambiar una firma de función o un contrato de API, revisar todos los consumidores existentes** (frontend, servicios, tests, tareas y, a futuro, móvil) y evaluar compatibilidad antes de aplicar el cambio.

## Control de versiones (P10)

- El proyecto usa **Git** desde el inicio con repositorio remoto **https://github.com/FernandoGonzalez416/PGFernandoGonzalez** (no crear otro).
- Mantener el **`.gitignore`** cubriendo Node.js, Python, React, FastAPI, `.env`, credenciales, temporales, builds y dependencias.
- **Nunca subir secretos** al repositorio (local ni remoto).
- Los mensajes de commit se escriben en español y describen el cambio real.
- **Un commit = un cambio lógico coherente**: agrupar los cambios por unidad de trabajo; no mezclar tareas independientes en un mismo commit.
- **Formato de mensaje**: imperativo + prefijo `tipo: descripción` con tipos `feat` / `fix` / `refactor` / `test` / `docs` / `chore`. Ejemplo: `feat: registrar ventas con descuento de inventario`.

## Idioma y estilo

- El proyecto, la documentación y los mensajes de commit se escriben en **español** (los identificadores siguen las convenciones del lenguaje usado).
- Sin comentarios innecesarios en el código; el código debe ser autoexplicativo.