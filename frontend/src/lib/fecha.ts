function aISO(fecha: Date): string {
  const año = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${año}-${mes}-${dia}`
}

export function hoyISO(): string {
  return aISO(new Date())
}

export function haceDiasISO(dias: number): string {
  const fecha = new Date()
  fecha.setDate(fecha.getDate() - dias)
  return aISO(fecha)
}

export function formatFechaCorta(iso: string): string {
  const fecha = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(fecha.getTime())) return iso
  return new Intl.DateTimeFormat('es-GT', { day: 'numeric', month: 'short' }).format(fecha)
}