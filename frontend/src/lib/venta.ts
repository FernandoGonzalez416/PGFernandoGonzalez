const ETIQUETAS_METODO = new Map<string, string>([
  ['efectivo', 'Efectivo'],
  ['tarjeta', 'Tarjeta'],
  ['transferencia', 'Transferencia'],
  ['otro', 'Otro'],
])

export function etiquetaMetodo(metodo: string): string {
  return ETIQUETAS_METODO.get(metodo) ?? metodo
}
