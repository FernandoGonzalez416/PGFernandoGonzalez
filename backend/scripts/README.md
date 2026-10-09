# Scripts locales

Herramientas de línea de comandos. **Ninguno es un endpoint** y ninguna se expone por HTTP.

## `semilla.py`

Siembra el almacén por defecto (`ALMACEN_PREDETERMINADO`) y un catálogo mínimo
**ficticio**, con existencias y su movimiento de tipo `inicial`.

Los datos que siembra están marcados con `SIMULACION` y **no son datos reales del negocio**.

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\semilla.py
```

Es **idempotente**: se puede ejecutar las veces que sea. La primera vez crea los
registros y lo dice; las siguientes imprimen `0 creados`.

Para borrar lo sembrado hay que hacerlo a mano, con cuidado: no hay comando de
limpieza porque nunca se debe eliminar información real por accidente.

Requiere `DATABASE_URL` en `backend/.env` apuntando a la base donde se quiera
sembrar. El script **no** lee `DATABASE_URL_TEST`: para sembrar en el esquema de
pruebas hay que ejecutar la sesión con `search_path=test` o apuntar
temporalmente `DATABASE_URL` a esa base, nunca mezclar ambas a la vez.

## `crear_usuarios_prueba.py`

Crea los **usuarios de prueba** `propietario@prueba.com` y `padre@prueba.com`:
da de alta la cuenta en Supabase Auth (API Admin con `service_role`) y su perfil
en la tabla `usuario`. Son usuarios **ficticios de prueba** (P4), no usuarios
reales del negocio.

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\crear_usuarios_prueba.py
```

Es **idempotente**: si el usuario ya existe en Auth, reutiliza su `auth_id` y
actualiza el perfil. **No** crea al administrador; solo avisa si no hay uno
activo. La contraseña por defecto es de prueba (`123456`) y se puede cambiar con
la variable de entorno `CONTRASENA_USUARIOS_PRUEBA`.

Requiere `DATABASE_URL`, `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en
`backend/.env`. Modifica datos reales de Supabase, así que se ejecuta solo con
autorización explícita (P17).