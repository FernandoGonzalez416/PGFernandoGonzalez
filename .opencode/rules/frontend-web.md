# Reglas del frontend web (React.js)

React.js es el único cliente en desarrollo en esta fase.

## Estructura y componentes

- **Componentes reutilizables**: extraer piezas repetidas en componentes compartidos; evitar duplicación de JSX.
- **Evitar componentes excesivamente grandes**: dividir por responsabilidad cuando crezcan.
- **Separar presentación y lógica**: la lógica de negocio y el acceso a datos no viven en los componentes; usar servicios/hooks/almacenes coherentes con el resto del proyecto.
- **Estructura clara**: mantener consistencia con la estructura del proyecto cuando exista.

## Estados y UX

- Manejar **estados de carga, error y vacíos** de forma explícita en cada vista.
- **Consistencia visual** basada en las decisiones de diseño del proyecto (ver tesis, Cap. IV): paleta morado/blanco con acento dorado suave; ámbar para bajo stock y rojo para vencimiento próximo/agotado; tipografía sans-serif legible; interfaz intuitiva para personas sin formación técnica.
- La aplicación busca ser principalmente una **web de escritorio responsive**: prioridad de experiencia en computadora/escritorio y, como vista secundaria, en teléfono mediante navegador. **No copiar la navegación móvil** de la tesis (menú inferior, etc.); usar una estructura apropiada para aplicación web (P7).
- El diseño debe ser **responsive** para funcionar correctamente desde un teléfono sin necesidad de instalar una aplicación.

## Librerías y dependencias

- **No inventar librerías de UI** sin necesidad: preferir componentes propios sencillos a menos que exista una decisión documentada.
- No añadir dependencias solo porque son comunes; confirmar con el proyecto.

## Reglas de negocio

- El frontend **consume** la API; no implementa reglas de negocio críticas (descuento de inventario, folios, umbrales, validaciones de venta).
- Ninguna pantalla debe mostrar datos como "confirmados" si el backend no los validó.

## Alcance

- No desarrollar funcionalidades móviles (React Native/Expo/PWA móvil) en esta fase.