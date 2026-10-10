# Reglas del frontend web (React.js)

React.js es el único cliente en desarrollo en esta fase.

## Estructura y componentes

- **Componentes reutilizables**: extraer piezas repetidas en componentes compartidos; evitar duplicación de JSX.
- **Evitar componentes excesivamente grandes**: dividir por responsabilidad cuando crezcan.
- **Separar presentación y lógica**: la lógica de negocio y el acceso a datos no viven en los componentes; usar servicios/hooks/almacenes coherentes con el resto del proyecto.
- **Estructura clara**: mantener consistencia con la estructura del proyecto cuando exista.

## TypeScript estricto

- Usar **TypeScript estricto**: `"strict": true` en `tsconfig.json` y no relajar nunca esa configuración.
- **CERO uso de `any`**: si el tipo no se conoce de antemano, se usa `unknown` + *type narrowing* (guardas, `typeof`, validación en runtime) antes de reducir a un tipo concreto.
- **No añadir librerías de tipos decorativas**: los tipos reflejan contratos reales; no maquetar falsos con `as`.

## Arquitectura por componentes

- **Separación presentación/lógica**: los componentes exponen JSX puro (presentación); la lógica de negocio y el acceso a datos viven en **hooks personalizados** y **servicios**.
- **Ningún `fetch` ni lógica de negocio directamente en el JSX de un componente**: la obtención de datos siempre pasa por un servicio y lo consume un hook (o almacén); el componente solo renderiza.
- **Tipar las respuestas de la API** con tipos que reflejen los esquemas Pydantic del backend; mantenerlos **sincronizados manualmente por ahora** (evaluar generación automática más adelante, sin decidirlo aún).
- **Prohibido `as` forzado** (type assertion) para silenciar errores de tipos: si el tipo no matchea, se corrige el tipo o se valida el dato (`unknown` → narrowing), nunca se oculta el error con `as`.

## Tamaño y responsabilidad

- **Un componente por archivo, una responsabilidad**: cada archivo exporta un único componente principal.
- Si un componente supera **~200 líneas**, extraer subcomponentes u hooks; el archivo grande es señal de que acumuló responsabilidades.

## Estados y UX

- **Todo componente que consuma datos async** debe manejar explícitamente los cuatro estados: **cargando, error, vacío y éxito**. Nunca dejar una vista ni en blanco ni "colgada" sin feedback.
- Manejar **estados de carga, error y vacíos** de forma explícita en cada vista.
- **Consistencia visual** basada en la identidad oficial del proyecto (P7 y `.opencode/rules/diseno.md`): paleta crema/nude/terracota/café de "Familia de la Cruz"; ámbar para bajo stock, rojo para vencimiento próximo/agotado y verde para disponible; títulos en Playfair Display y cuerpo en Montserrat; interfaz intuitiva para personas sin formación técnica.
- Aplicar siempre las reglas de **diseño premium** (animaciones, micro-interacciones, jerarquía, layout, paleta, tipografía) de `.opencode/rules/diseno.md` y cargar las skills de diseño instaladas antes de tareas visuales.
- La aplicación busca ser principalmente una **web de escritorio responsive**: prioridad de experiencia en computadora/escritorio y, como vista secundaria, en teléfono mediante navegador. **No copiar la navegación móvil** de la tesis (menú inferior, etc.); usar una estructura apropiada para aplicación web (P7).
- El diseño debe ser **responsive** para funcionar correctamente desde un teléfono sin necesidad de instalar una aplicación.

## Librerías y dependencias

- **No inventar librerías de UI** sin necesidad: preferir componentes propios sencillos a menos que exista una decisión documentada.
- No añadir dependencias solo porque son comunes; confirmar con el proyecto.
- **Animación**: usar **Motion** (`motion/react`, ya instalado) para animaciones React (entrada, hover, tap, layout, exit). Usar la skill `animate` y la documentación oficial de Motion para la API correcta.

## Reglas de negocio

- El frontend **consume** la API; no implementa reglas de negocio críticas (descuento de inventario, folios, umbrales, validaciones de venta).
- Ninguna pantalla debe mostrar datos como "confirmados" si el backend no los validó.

## Alcance

- No desarrollar funcionalidades móviles (React Native/Expo/PWA móvil) en esta fase.