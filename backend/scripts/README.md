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