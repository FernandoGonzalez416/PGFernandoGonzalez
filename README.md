# Plataforma de inventarios y reabastecimiento

Plataforma web para la gestión de inventarios y reabastecimiento en tiendas de cosméticos (proyecto de graduación, UMG Guatemala). Documentación de referencia: tesis en la raíz y `AGENTS.md` + `DECISIONES.md`.

## Estructura

```
backend/      API FastAPI (lógica de negocio, API REST)
frontend/     Aplicación web React + Vite (cliente)
node-tasks/   Tareas livianas/serverless con Node.js (sin servicios por ahora)
```

## Requisitos

- Node.js **24 LTS**
- Python **3.14.x**
- Para el backend, crear un entorno virtual: `backend/.venv`

## Cómo levantar el backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # completar SUPABASE_* cuando se configure (fase 2)
uvicorn app.main:app --reload
```

- API disponible en `http://127.0.0.1:8000`
- Documentación interactiva (OpenAPI): `http://127.0.0.1:8000/docs`
- Verificación rápida: `http://127.0.0.1:8000/health` → `{"status":"ok"}`

## Cómo levantar el frontend (React + Vite)

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local   # completar VITE_SUPABASE_* cuando se configure (fase 2)
npm run dev
```

- Aplicación disponible en `http://localhost:5173`

## Variables de entorno

Nunca se versionan archivos `.env`; se usan `.env.example` como plantilla. Secretos reales solo en variables de entorno locales (ver `AGENTS.md` / `seguridad.md`).