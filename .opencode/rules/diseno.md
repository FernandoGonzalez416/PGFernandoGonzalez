# Reglas de diseño visual (frontend web)

Reglas obligatorias para todo el trabajo visual del frontend web. El objetivo es que la interfaz se vea como la haría un diseñador senior: premium, coherente, con jerarquía visual clara y sin patrones genéricos de IA.

## Skills de diseño disponibles (usarlas SIEMPRE en tareas visuales)

Este proyecto tiene instaladas skills de diseño que deben cargarse y aplicarse en cualquier tarea visual (componentes, vistas, animaciones, layout):

- `high-end-visual-design` (`.agents/skills/high-end-visual-design`) — nivel agencia: tipografías, espacios, sombras, doble-bezel, motion premium.
- `emil-design-eng` (`.agents/skills/emil-design-eng`) — decisiones de motion, micro-interaciones, curvas de easing, estado activo de botones.
- `design-taste-frontend` (`.agents/skills/design-taste-frontend`) — anti-slop: evitar los defaults de IA y referencias reales de diseño.
- `responsive-design` (`.agents/skills/responsive-design`) — layout responsive correcto: container queries, tipografía fluida, CSS Grid, mobile-first.
- `animate` (`.agents/skills/animate`) — construye animaciones bien pensadas con Motion.
- `pick-ui-library` (`.agents/skills/pick-ui-library`) — elegir librería correcta antes de inventar.
- `review-animations` / `find-animation-opportunities` / `improve-animations` — auditar/mejorar motion existente.

Si la tarea incluye animación, cargar también la documentación de **Motion** (`motion/react` en el proyecto; docs oficiales en https://motion.dev/docs/react) como fuente de API correcta.

## Directivas permanentes de diseño (preferencia explícita del usuario)

1. **Animaciones siempre presentes y premium**: micro-animaciones de interfaz, botones, transiciones y estados. Nada debe "aparecer de golpe"; todo entra/sale con motion deliberado (entrada, hover, tap, cambio de estado, layout).
2. **Botones con física real**: feedback en `:active` (scale ~0.97), hover con elevación sutil, curvas `cubic-bezier` custom (nunca `linear` ni `ease-in-out` genéricos; usar curvas del skill `emil-design-eng`).
3. **Micro-interacciones**: valor para el usuario: feedback de estados (carga, error, vacío), stagger en entradas de listas/tarjetas, transform-origin correcto en popovers.
4. **Ajuste fino de espacios y estructura**: macros y micros zonificación con ritmo; paddings generosos (`py-24`+ en secciones), separación clara entre bloques; nada apretado ni desbalanceado.
5. **Jerarquía visual óptima**: un H1 por vista, jerarquía tipográfica y de color definida, el elemento más importante destaca primero; más de 3 niveles de énfasis es señal de problema.
6. **Layout bien compuesto**: usar CSS Grid; evitar rejillas simétricas aburridas 3-col; permitir asimetría intencional (bento, split, cascade) que colapse bien en móvil; nada de flexbox-math con porcentajes.
7. **Nada de patrones genéricos de IA**: prohibido el cliché (gradientes morados "IA", 3 tarjetas iguales, glassmorphism por doquier, Inter + slate-900, glow neón). Basar decisiones en referencias reales de diseño (Linear, Vercel, Apple, Radix UI, shadcn, Emil Kowalski, awwwards) y en las skills.
8. **Responsive siempre**: mobile-first correcto (no "funciona en escritorio y se achica"), container queries para componentes, tipografía fluida, breakpoints estándar, colapso explícito por sección bajo 768px.
9. **Respetar `prefers-reduced-motion`**: cualquier motion debe degradar a estático con `@media (prefers-reduced-motion: reduce)`; hover gated con `@media (hover:hover) and (pointer:fine)`.
10. **Performance**: animar solo `transform` y `opacity` (nunca top/left/width/height); `backdrop-blur` solo en elementos fixed/sticky; sin `window.addEventListener('scroll')` (usar IntersectionObserver/Motion `useScroll`).

## Paleta de colores (diseño aprobado)

Base de la identidad de la tesis: **morado / blanco con acento dorado suave**. Estados: ámbar = stock bajo; rojo = vencimiento próximo / agotado. No usar otros acentos de color para no romper la coherencia.

| Rol | Variable | Valor | Uso |
|---|---|---|---|
| Fondo | `--bg` | `#F6F4FA` | Fondo general (lila-blancuzco frío) |
| Superficie | `--surface` | `#FFFFFF` | Tarjetas, sidebar |
| Superficie suave | `--surface-soft` | `#FBF9FE` | Filas hover, fondos sutiles |
| Tinta principal | `--ink` | `#211A33` | Texto principal (muy cercano al negro del brand, no #000) |
| Tinta suave | `--ink-soft` | `#6B6480` | Texto secundario |
| Tinta tenue | `--ink-faint` | `#9B94B0` | Labels, placeholders, iconos |
| Primario | `--primary` | `#6A47C7` | Botones principales, enlaces, acentos |
| Primario profundo | `--primary-deep` | `#5734B0` | Hover/gradientes primario |
| Primario suave | `--primary-soft` | `#EDE6FB` | Fondo de items activos |
| Dorado suave | `--gold` | `#C8A35C` | Acento premium (CTA destacados, marca) |
| Dorado suave | `--gold-soft` | `#F7EFDD` | Fondos de acento dorado |
| Ámbar (stock bajo) | `--amber` | `#B0781F` | Texto/iconos alerta stock bajo |
| Ámbar suave | `--amber-soft` | `#FBF1D9` | Fondos/badges ámbar |
| Rojo (vencer/agotado) | `--red` | `#C04A4A` | Texto/iconos vencimiento o agotado |
| Rojo suave | `--red-soft` | `#FBE7E3` | Fondos/badges rojo |
| OK | `--ok` | `#3E8C6B` | Estados positivos (disponible, completo) |
| OK suave | `--ok-soft` | `#E4F2EA` | Badges positivos |
| Línea | `--line` | `rgba(107,100,128,0.14)` | Hairlines/bordes suaves (no gris puro) |

Reglas de la paleta:
- **Un solo acento de color por vista**: morado. El dorado es el segundo acento reservado a momentos premium (CTA principal destacado, marca). Ámbar/rojo/verde son semánticos (estados), no decorativos.
- **Shadow con tinte del fondo**: nunca sombras negras puras; usar `rgba(87,52,176,…)` o equivalente.
- **Contraste WCAG AA**: texto sobre fondo ≥ 4.5:1; botones con texto legible (revisar antes de entregar).
- **Sin #000 ni #FFF puros** en fondos/textos de marca; usar `--ink` y `--surface`.

## Tipografía

- **Familia**: Plus Jakarta Sans (instalada vía Google Fonts como referencia; en producción usar `next/font` o self-hosted). Prohibido Inter, Roboto, Arial, Open Sans, Helvetica como default.
- Display: `font-weight 800`, `letter-spacing -0.02em`, `leading 1.1`.
- Body: `font-weight 400-600`, `color var(--ink-soft)`, `max-width 65ch` en párrafos largos.
- Números/datos: `font-variant-numeric: tabular-nums` en KPIs, tablas y montos.
- Prohibido el serif como default; solo si la identidad de marca lo pide.

## Motion (valores de referencia)

- Curvas: `--ease-out: cubic-bezier(0.23,1,0.32,1)`; `--ease-exp: cubic-bezier(0.32,0.72,0,1)`; `--ease-in-out: cubic-bezier(0.77,0,0.175,1)`.
- Duración UI: botones 100-160ms; tooltips/popovers 125-250ms; modales 200-500ms; marketing puede ser más largo. Entrada en stagger 30-80ms entre items.
- Botones: `:active { transform: scale(0.97) }` siempre.
- Entrada: nunca desde `scale(0)`; empezar `scale(0.95) + opacity 0`, origin-aware.
- En React usar `motion/react` (librería **motion**) con `whileHover`, `whileTap`, `whileInView`, `layout`, `AnimatePresence` cuando aporte jerarquía/feedback.
- El motion debe ser motivado (comunica jerarquía/estado/transición), no decorativo sin sentido.

## Referencias reales de diseño

Cuando se busque inspiración/dirección visual, pensar en trabajos reales de calidad senior: Linear, Vercel, Apple, Radix UI, shadcn/ui, Emil Kowalski (Sonner, Vaul, Basscss), Rauno Freiberg, Awwwards winners. Nunca "plantilla genérica con buenas fuentes".

## Checklist previo a entregar UI

- [ ] Se cargaron las skills de diseño pertinentes.
- [ ] No hay fuentes prohibidas, ni 1px gris genérico, ni sombras negras.
- [ ] Micro-interacciones presentes (hover, active, entrada) sin sobre-animar.
- [ ] Jerarquía: 1 H1 por vista, niveles ≤ 3, contraste AA verificado.
- [ ] Layout responsive correcto (prueba visual mobile-first), colapso bajo 768px.
- [ ] Motion con curvas custom y `prefers-reduced-motion` respetado.
- [ ] Solo se anima transform/opacity; sin scroll-listener de ventana.
- [ ] Paleta según tabla (morado/dorado/semánticos), un acento por vista.