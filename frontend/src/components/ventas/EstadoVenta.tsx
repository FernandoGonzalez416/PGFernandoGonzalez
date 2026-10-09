export function PillEstadoVenta({ estado }: { estado: string }) {
  if (estado === 'anulada') return <span className="pill pill-red">Anulada</span>
  return <span className="pill pill-good">Registrada</span>
}
