export function construirConsulta(
  parametros: Record<string, string | number | boolean | null | undefined>,
): string {
  const busqueda = new URLSearchParams()
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor === null || valor === undefined || valor === '' || valor === false) continue
    busqueda.set(clave, String(valor))
  }
  const cadena = busqueda.toString()
  return cadena === '' ? '' : `?${cadena}`
}
