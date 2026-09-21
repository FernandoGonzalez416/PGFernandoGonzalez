# Reglas de offline / sincronización

## Situación actual (decisión P2)

- Para las primeras versiones **no es obligatorio** implementar toda la funcionalidad offline desde el primer momento.
- La prioridad inicial es construir una primera versión funcional de la plataforma web y luego **iterar**.
- La estrategia concreta para la fase web **no está definida todavía** (decisión pendiente R4); se documentará cuando llegue el momento de implementarla.

## Regla fundamental

> **No implementar una arquitectura offline compleja sin necesidad y sin autorización.**

**NO se asume automáticamente** el uso de:

- IndexedDB;
- Service Workers;
- PWA;
- colas de sincronización;
- resolución automática de conflictos;
- almacenamiento local específico;
- u otra tecnología determinada.

La funcionalidad offline sigue siendo un **requisito importante de la solución final**, pero **no debe bloquear** la construcción de la primera versión funcional.

## Qué hacer

1. Al abordar offline, verificar primero qué está realmente definido en la tesis, el código y `DECISIONES.md`.
2. Si la estrategia no está definida, **marcarla como decisión pendiente** y solicitar confirmación antes de implementar.
3. Mientras tanto, mantener la arquitectura "offline-friendly": operaciones idempotentes donde sea posible, contratos de API claros, y lógica de negocio desacoplada del cliente, de modo que la estrategia elegida después se pueda integrar **sin cerrar posibilidades futuras**.
4. Cualquier protocolo de sincronización propuesto debe contemplar: prevención de duplicados/pérdidas, manejo de folios temporales (la tesis menciona folio temporal para ventas sin conexión) y reconciliación al restablecer la red.

## Alcance

- No desarrollar PWA ni funcionalidad offline web completa en esta fase salvo confirmación explícita.
- No preparar la estrategia offline de la app móvil (fuera de alcance).