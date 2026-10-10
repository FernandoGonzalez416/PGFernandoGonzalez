# Plataforma Inteligente de Inventarios y Reabastecimiento

Sistema web para optimización de inventarios y reabastecimiento en tiendas de cosméticos — caso de estudio: **Familia de la Cruz** (Villa Nueva, Guatemala).

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Frontend Web | React 19 + TypeScript + Vite 8 |
| Backend / API | FastAPI 0.141 (Python 3.14) |
| Base de datos / Auth | Supabase (PostgreSQL) |
| Tareas auxiliares | Node.js 24 LTS (serverless) |
| Predicción (futuro) | Scikit-learn (Random Forest + contraste) |
| Estilos | CSS vanilla (paleta crema/nude/terracota/café) |
| Animaciones | Motion (motion/react) |

## Requisitos previos

- Node.js 24 LTS
- Python 3.14
- Cuenta Supabase (proyecto existente)

## Instalación

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
# Configurar .env con credenciales Supabase
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm ci
# Generar tipos TypeScript desde la API (requiere backend corriendo en :8000)
npm run gen:api
npm run dev
```

## Scripts principales

| Comando | Descripción |
|---------|-------------|
| `npm run dev` | Servidor de desarrollo Vite |
| `npm run build` | Build de producción (tsc + vite build) |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript check (tsc --noEmit) |
| `npm run test` | Vitest (unit + integración) |
| `npm run gen:api` | Genera `src/api/schema.d.ts` desde OpenAPI |

## Estructura del proyecto

```
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints (ventas, alertas, reportes, sugerencias, notificaciones)
│   │   ├── services/      # Lógica de negocio
│   │   ├── schemas/       # Pydantic models
│   │   └── core/          # Auth, capacidades, config
│   └── tests/             # Pytest (unit + integración)
├── frontend/
│   ├── src/
│   │   ├── api/           # Cliente HTTP + tipos generados
│   │   ├── components/    # UI reutilizable (panel, notificaciones, layout)
│   │   ├── hooks/         # Custom hooks (useResumenVentas, useAlertas, etc.)
│   │   ├── pages/         # Vistas (Panel, Alertas, Reportes, Sugerencias, Notificaciones)
│   │   ├── services/      # Llamadas a la API
│   │   ├── styles/        # app.css (paleta, responsive, motion)
│   │   └── App.tsx        # Rutas + lazy loading + ErrorBoundary
│   └── tests/             # Vitest + Testing Library
├── docs/
│   └── GUION_DEMO.md      # Guion de demostración
└── tesis/                 # Documento de referencia académica
```

## Funcionalidades implementadas (F3)

| Pantalla | Ruta | Capacidad | Descripción |
|----------|------|-----------|-------------|
| **Panel** | `/` | — | Resumen semanal (ventas, gráfico SVG, alertas, top vendidos, últimas ventas, sugerencias pendientes) |
| **Alertas** | `/alertas` | `alertas:ver` | Stock bajo/agotado + vencimientos (píldoras Agotado/Bajo/Vencido/Próximo) |
| **Reportes** | `/reportes` | `reportes:ver` | Productos más vendidos con filtro de fechas (7/30/60 días), barras horizontales |
| **Sugerencias** | `/sugerencias` | `sugerencias:ver` / `sugerencias:atender` / `prediccion:ver` | Generar (solo admin), Atender/Descartar, error 409 visible, mensaje de confianza baja |
| **Notificaciones** | `/notificaciones` | `alertas:ver` | Historial, marcar leída, filtro Todas/Sin leer/Leídas, botón "Marcar todas" |
| **Campana** | Topbar | `alertas:ver` | Badge contador, panel desplegable, click para marcar leída |

## Capacidades (RBAC)

| Capacidad | Descripción | Roles |
|-----------|-------------|-------|
| `stock:consultar` | Ver inventario, ventas, panel | admin, propietario, padre |
| `ventas:registrar` | Crear ventas | admin, propietario |
| `ventas:anular` | Anular ventas (padre solo las suyas) | admin, propietario, padre |
| `alertas:ver` | Alertas, notificaciones, campana | admin, propietario, padre |
| `reportes:ver` | Reportes de más vendidos | admin, propietario |
| `sugerencias:ver` | Listar sugerencias | admin, propietario, padre |
| `sugerencias:atender` | Atender/Descartar sugerencias | admin, propietario, padre |
| `prediccion:ver` | Generar sugerencias (futuro IA) | admin |

## Paleta de colores (Identidad "Familia de la Cruz")

| Variable | Valor | Uso |
|----------|-------|-----|
| `--crema` | `#FAF6F0` | Fondo general |
| `--nude` | `#E0C9BB` | Tarjetas, secciones |
| `--terracota` | `#C87D71` | Acento primario (CTA, bordes activos) |
| `--cafe` | `#2D2424` | Texto principal, títulos |
| `--gloss` | `#D8B4A0` | Hover, bordes activos |
| `--amber` | `#B0781F` | Stock bajo |
| `--red` | `#C04A4A` | Vencido/agotado |
| `--ok` | `#3E8C6B` | Disponible |

## Tipografía

- **Títulos**: Playfair Display (serif) — 500/600/700
- **Cuerpo**: Montserrat (sans) — 400–600

## Responsive

- Breakpoints: 390px / 768px / 960px / 1080px
- Sidebar colapsable en móvil (<860px)
- Tablas → tarjetas en <768px
- `prefers-reduced-motion` respetado

## Testing

```bash
# Frontend
cd frontend && npm run test

# Backend (solo unitarios rápidos)
cd backend && python -m pytest -q

# Backend (integración - lento ~15 min)
cd backend && python -m pytest -m integracion
```

## Variables de entorno (Backend)

Crear `backend/.env`:
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
JWT_SECRET=...
```

## Licencia

Proyecto de graduación — Universidad Mariano Gálvez de Guatemala.