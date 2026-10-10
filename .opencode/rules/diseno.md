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

## Paleta de colores (diseño aprobado — identidad oficial "Familia de la Cruz")

Base de la identidad oficial: **blanco crema / rosa nude / terracota / café oscuro / gloss soft**. Reemplaza la paleta morado-blanco con dorado (descartada el 2026-09-26, ver P7 en `DECISIONES.md`). Estados: ámbar = stock bajo; rojo = vencimiento próximo/agotado; verde = disponible. No usar otros acentos de color para no romper la coherencia.

### Colores de marca

| Rol | Variable | Valor | Uso |
|---|---|---|---|
| Blanco crema | `--crema` | `#FAF6F0` | Fondo general y áreas de lectura limpia |
| Rosa nude suave | `--nude` | `#E0C9BB` | Fondos secundarios, tarjetas de productos y secciones destacadas |
| Terracota | `--terracota` | `#C87D71` | Acento primario: CTA, precios y etiquetas destacadas, bordes y estados activos |
| Café oscuro profundo | `--cafe` | `#2D2424` | Tipografía, títulos, iconos y encabezados (reemplaza al negro puro) |
| Gloss soft | `--gloss` | `#D8B4A0` | Estados *hover*, bordes activos e interacciones secundarias |

### Roles semánticos (derivados de la marca)

| Rol | Variable | Valor | Uso |
|---|---|---|---|
| Fondo | `--bg` | `#FAF6F0` | Fondo general de la aplicación |
| Superficie | `--surface` | `#FFFDFB` | Tarjetas, paneles, sidebar (blanco cálido, nunca `#FFFFFF` puro) |
| Superficie suave | `--surface-soft` | `#F6EFE9` | Filas *hover*, fondos sutiles, campos de formulario |
| Tinte terracota | `--primary-soft` | `#F2E1DA` | Fondos de elementos activos o en hover |
| Tinta principal | `--ink` | `#2D2424` | Texto principal, títulos, iconos (muy cercano al negro, no `#000`) |
| Tinta suave | `--ink-soft` | `#6B5A54` | Texto secundario (6.1:1 sobre crema) |
| Tinta tenue | `--ink-faint` | `#75655E` | Labels, placeholders, iconos inactivos (5.2:1 sobre crema) |
| Primario | `--primary` | `#C87D71` | Relleno de CTA y de estados activos (NO como color de texto) |
| Primario hover | `--primary-hover` | `#D8B4A0` | Fondo en *hover* de CTA y de estados activos |
| Nude suave | `--nude-soft` | `#F3E7DF` | Fondos de apoyo, chips y degradados de panel |
| Ámbar (stock bajo) | `--amber` | `#B0781F` | Texto/iconos de alerta por stock bajo |
| Ámbar suave | `--amber-soft` | `#FAF1E0` | Fondos/badges ámbar |
| Rojo (vencer/agotado) | `--red` | `#C04A4A` | Texto/iconos de vencimiento o agotado |
| Rojo suave | `--red-soft` | `#FAEAE6` | Fondos/badges rojo |
| OK | `--ok` | `#3E8C6B` | Estados positivos (disponible, completo) |
| OK suave | `--ok-soft` | `#E7F1EB` | Badges positivos |
| Línea | `--line` | `rgba(45, 36, 36, 0.12)` | Hairlines/bordes suaves (nunca gris puro) |

Reglas de la paleta:
- **Un solo acento de color por vista**: terracota. El crema es el fondo, el nude y el gloss son tonos de apoyo de la misma familia cálida.
- **El terracota nunca es color de texto sobre crema**: `#C87D71` sobre `#FAF6F0` da 2.9:1 y no cumple AA. El terracota se usa como **relleno, borde, subrayado o estado activo**, y el texto sobre relleno terracota es siempre **café `#2D2424`** (4.8:1 ✓ AA).
- **Sobre fondo `nude` todo el texto es café**: `--ink-soft` y `--ink-faint` no alcanzan AA sobre `#E0C9BB`; se sube a `--ink` y la jerarquía se marca con tamaño y peso.
- **`--gloss` nunca es color de texto ni de icono**: `#D8B4A0` sobre crema da 1.9:1 y sobre `nude-soft` 1.6:1, ambos ilegibles. El gloss es exclusivamente relleno de *hover* y borde. Para íconos con significado usar `--ink-soft` o `--ink` (≥ 4.5:1).
- **Colores semánticos solo para estados**: ámbar/rojo/verde comunican urgencia o salud del stock; nunca se usan como decoración ni como acento de vista.
- **Sombras con tinte del fondo**: `rgba(45,36,36,…)` o `rgba(200,125,113,…)`; nunca sombras negras puras.
- **Contraste WCAG AA**: texto ≥ 4.5:1; bordes, iconos con significado y elementos gráficos ≥ 3:1. El anillo de foco va en `--ink` con halo `--terracota` (el terracota solo no llega a 3:1 sobre crema).
- **Sin `#000` ni `#FFFFFF` puros** en fondos o textos de marca; usar `--ink` y `--surface`.

## Tipografía

- **Títulos y encabezados (H1, H2, H3, nombres de líneas, nombre del establecimiento)**: **Playfair Display** (serif) 500/600/700. `font-weight: 700`, `letter-spacing: -0.01em`, `leading: 1.15`.
- **Cuerpo de texto, precios, filtros, navegación, botones y etiquetas**: **Montserrat** (sans-serif) 400/500/600/700/800. `font-weight: 400-600`, `color: var(--ink-soft)`, `max-width: 65ch` en párrafos largos.
- Ambas familias son de uso libre; en producción servirlas como archivos locales (self-hosted) en vez de cargar Google Fonts en caliente.
- Números/datos: `font-variant-numeric: tabular-nums` en KPIs, tablas y montos.
- Prohibido Inter, Roboto, Arial, Open Sans, Helvetica como default.
- El serif solo aparece en títulos, donde lo pide la identidad de marca; el cuerpo es siempre Montserrat.

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
- [ ] Paleta según tabla (crema/nude/terracota/café/gloss + semánticos), un acento por vista.