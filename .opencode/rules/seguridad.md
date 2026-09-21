# Reglas de seguridad

## Prohibiciones absolutas

- **No colocar contraseñas directamente en el código.**
- **No colocar API keys reales en el repositorio.**
- **No colocar secretos en archivos públicos** o en archivos versionados.
- **No desactivar seguridad únicamente para evitar un error.**
- **No ignorar errores de autenticación o autorización.**

## Reglas obligatorias

- Usar **variables de entorno** para secretos (claves de Supabase, JWT, credenciales, etc.) mediante mecanismos apropiados (`.env` no versionado, gestor de secretos) y documentar su configuración sin exponer valores.
- **Nunca commitear** archivos de secretos ni `.env` con valores reales (mantener plantillas `.env.example` sin valores sensibles); el `.gitignore` debe excluirlos (P10).
- Autenticación obligatoria para operaciones sensibles (Supabase Auth según la tesis).
- **Autorización por roles** alineada con la matriz aprobada (P14): usuarios del sistema = administrador, dueño del negocio y padre del dueño (P5). El padre opera (ventas, consultas, alertas, sugerencias) y puede **anular solo sus propias ventas**; no administra usuarios, roles ni configuración. Aplicar RLS y políticas por rol al crear las tablas.
- Activar **Row Level Security (RLS)** en Supabase y definir políticas de acceso por tabla/rol.
- Usar HTTPS en entornos desplegados y cifrado apropiado en tránsito.
- Manejar errores sin exponer detalles internos (no filtrar errores de BD, stacks, ni secretos en respuestas).
- Validar y sanitizar entradas (evitar inyección SQL/NoSQL/XSS).
- Revisar consumidores antes de modificar contratos de endpoints para no abrir vías de acceso indebido.

## Reporte de incidencias

- Cualquier hallazgo de seguridad (secreto expuesto, endpoint sin auth, RLS ausente) se **señala al usuario** de inmediato y no se silencia.
- Al terminar tareas sensibles, verificar que no haya secretos en los archivos modificados.