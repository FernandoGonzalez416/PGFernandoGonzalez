const formateadorQuetzales = new Intl.NumberFormat('es-GT', {
  style: 'currency',
  currency: 'GTQ',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const formateadorCantidad = new Intl.NumberFormat('es-GT', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

const VACIO = '—'

export function parseDecimal(valor: string | number | null | undefined): number | null {
  if (valor === null || valor === undefined) return null
  if (typeof valor === 'number') return Number.isFinite(valor) ? valor : null
  const limpio = valor.trim()
  if (limpio === '') return null
  const numero = Number(limpio)
  return Number.isFinite(numero) ? numero : null
}

export function formatQ(valor: string | number | null | undefined): string {
  const numero = parseDecimal(valor)
  if (numero === null) return VACIO
  return formateadorQuetzales.format(numero)
}

export function formatCantidad(valor: string | number | null | undefined): string {
  const numero = parseDecimal(valor)
  if (numero === null) return VACIO
  return formateadorCantidad.format(numero)
}

export function formatFecha(valor: string | null | undefined): string {
  if (!valor) return VACIO
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return VACIO
  return new Intl.DateTimeFormat('es-GT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(fecha)
}
