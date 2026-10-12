import { useEffect, useMemo, type ReactNode } from 'react'
import { useAuth } from '../auth/useAuth'
import type { ProductoRead } from '../api/types'
import { listarProductos } from '../services/catalogo'
import { ContextoOffline, type EstadoOffline } from './contexto'
import { useConexion } from './useConexion'
import { useColaVentas } from './useColaVentas'
import { useCatalogoCache } from './useCatalogoCache'
import type { ProductoCache } from './types'

const TAMANO_PAGINA = 100

/** Descarga el catálogo completo paginando (el backend limita a 100 por página). */
async function descargarCatalogo(): Promise<ProductoRead[]> {
  const productos: ProductoRead[] = []
  let desplazamiento = 0
  for (;;) {
    const pagina = await listarProductos({ limite: TAMANO_PAGINA, desplazamiento })
    productos.push(...pagina)
    if (pagina.length < TAMANO_PAGINA) return productos
    desplazamiento += TAMANO_PAGINA
  }
}

function aCache(producto: ProductoRead): ProductoCache {
  return {
    id: producto.id,
    codigo: producto.codigo,
    nombre: producto.nombre,
    precio_venta: Number(producto.precio_venta),
    existencia: Number(producto.existencia),
    unidad_medida: producto.unidad_medida,
    fecha_descarga: new Date().toISOString(),
  }
}

/**
 * Provee el estado offline a toda la aplicación (P27/F5): conexión, cola de
 * ventas y caché del catálogo. Descarga el catálogo y reanuda la sincronización
 * cuando hay conexión.
 *
 * Al cambiar de usuario se remonta `ContenidoOffline` (vía `key`), de modo que
 * la cola y el catálogo se hidratan desde la clave correcta de localStorage.
 */
export function ProveedorOffline({ children }: { children: ReactNode }) {
  const { perfil } = useAuth()
  const usuarioId = perfil?.id ?? null

  return (
    <ContenidoOffline key={usuarioId ?? 'anonimo'} usuarioId={usuarioId}>
      {children}
    </ContenidoOffline>
  )
}

function ContenidoOffline({
  usuarioId,
  children,
}: {
  usuarioId: string | null
  children: ReactNode
}) {
  const { online } = useConexion()
  const cola = useColaVentas(usuarioId, online)
  const catalogo = useCatalogoCache(usuarioId)
  const { actualizarCache } = catalogo

  // Al recuperar conexión, refrescar el catálogo para poder vender offline.
  useEffect(() => {
    if (!online || usuarioId === null) return
    let activo = true
    descargarCatalogo()
      .then((productos) => {
        if (activo) actualizarCache(productos.map(aCache))
      })
      .catch(() => {
        // Sin conexión real: se conserva el catálogo cacheado anterior.
      })
    return () => {
      activo = false
    }
  }, [online, usuarioId, actualizarCache])

  // Reanudar la sincronización pendiente al volver la conexión. No reintenta si
  // falta autenticación, para no golpear el backend en bucle con 401.
  const { ventas, sincronizar, authRequerida } = cola
  useEffect(() => {
    if (!online || authRequerida) return
    if (!ventas.some((v) => v.estado === 'pendiente')) return
    void sincronizar()
  }, [online, authRequerida, ventas, sincronizar])

  const valor = useMemo<EstadoOffline>(
    () => ({
      usuarioId,
      online,
      sincronizando: cola.sincronizando,
      authRequerida: cola.authRequerida,
      pendientes: cola.ventas.filter((v) => v.estado !== 'sincronizada').length,
      ventas: cola.ventas,
      productos: catalogo.productos,
      catalogoCargando: catalogo.cargando,
      fechaDescarga: catalogo.fechaDescarga,
      agregarVenta: cola.agregarVenta,
      actualizarEstado: cola.actualizarEstado,
      eliminarVenta: cola.eliminarVenta,
      sincronizar: cola.sincronizar,
      reintentar: cola.reintentar,
      actualizarCache: catalogo.actualizarCache,
      buscarPorCodigo: catalogo.buscarPorCodigo,
      buscarPorNombre: catalogo.buscarPorNombre,
      descontarExistencia: catalogo.descontarExistencia,
    }),
    [usuarioId, online, cola, catalogo],
  )

  return <ContextoOffline.Provider value={valor}>{children}</ContextoOffline.Provider>
}
