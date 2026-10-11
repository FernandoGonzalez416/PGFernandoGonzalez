import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Predicciones } from './Predicciones'

const mocks = vi.hoisted(() => ({
  predicciones: [
    {
      id: 'pred1',
      producto_id: 'p1',
      codigo: 'SIM-001',
      nombre: 'Labial rojo',
      metodo: 'random_forest',
      nivel_confianza: 'alta',
      demanda_pronosticada: 20.5,
      intervalo_inf: 15.2,
      intervalo_sup: 25.8,
      mae_validacion: 1.2,
      mae_linea_base: 2.5,
      mejora_pct: 52.0,
      observaciones_usadas: 60,
      fecha_generacion: '2026-10-10T12:00:00Z',
      motivo: null,
    },
    {
      id: 'pred2',
      producto_id: 'p2',
      codigo: 'SIM-002',
      nombre: 'Crema facial',
      metodo: 'promedio_movil',
      nivel_confianza: 'baja',
      demanda_pronosticada: 15.0,
      intervalo_inf: null,
      intervalo_sup: null,
      mae_validacion: 2.5,
      mae_linea_base: 2.5,
      mejora_pct: 0.0,
      observaciones_usadas: 45,
      fecha_generacion: '2026-10-10T12:00:00Z',
      motivo: 'el modelo no supera a la línea base',
    },
    {
      id: 'pred3',
      producto_id: 'p3',
      codigo: 'SIM-003',
      nombre: 'Shampoo',
      metodo: 'sin_historial',
      nivel_confianza: 'baja',
      demanda_pronosticada: 0,
      intervalo_inf: null,
      intervalo_sup: null,
      mae_validacion: null,
      mae_linea_base: null,
      mejora_pct: null,
      observaciones_usadas: 0,
      fecha_generacion: '2026-10-10T12:00:00Z',
      motivo: null,
    },
  ],
  serie: {
    historial: [
      { fecha: '2026-08-15', unidades: 5 },
      { fecha: '2026-08-16', unidades: 3 },
      { fecha: '2026-08-17', unidades: 7 },
    ],
    pronostico: [
      { fecha: '2026-10-11', unidades: 4.2 },
      { fecha: '2026-10-12', unidades: 3.8 },
      { fecha: '2026-10-13', unidades: 4.5 },
    ],
    metodo: 'random_forest',
    mae_modelo: 1.2,
    mae_linea_base: 2.5,
    nivel_confianza: 'alta',
    suficiente: true,
    motivo: null,
  },
  generar: { sugerencias_creadas: 3, predicciones_creadas: 2, por_metodo: { random_forest: 1, promedio_movil: 1 } },
  error409: { response: { status: 409, data: { detail: 'Sugerencia no está pendiente' } } },
  perfil: {
    id: 'u1', auth_id: 'a1', nombre: 'Admin', email: 'admin@c.com', rol: 'administrador', activo: true,
    capacidades: ['stock:consultar', 'sugerencias:ver', 'sugerencias:atender', 'prediccion:ver'],
  },
  canMap: { current: new Map<string, boolean>() },
  actualizarError: { current: false },
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: mocks.perfil, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../hooks/usePredicciones', () => ({
  usePredicciones: () => ({
    predicciones: mocks.predicciones,
    cargando: false,
    error: null,
    recargar: vi.fn(),
  }),
  useSeriePrediccion: (productoId: string | null) => {
    if (!productoId || productoId !== 'p1') {
      return { serie: null, cargando: false, error: null }
    }
    return { serie: mocks.serie, cargando: false, error: null }
  },
}))

vi.mock('../services/sugerencias', () => ({
  generarSugerencias: vi.fn(() => Promise.resolve(mocks.generar)),
}))

vi.mock('../auth/useCan', () => ({
  useCan: (cap: string) => mocks.canMap.current.get(cap) ?? false,
}))

function renderPredicciones() {
  mocks.canMap.current.set('prediccion:ver', true)
  return render(
    <MemoryRouter initialEntries={['/predicciones']}>
      <ToastProvider>
        <Predicciones />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('Predicciones', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.canMap.current.clear()
    mocks.canMap.current.set('prediccion:ver', true)
    mocks.actualizarError.current = false
  })

  it('renderiza el título y resumen superior', () => {
    renderPredicciones()
    expect(screen.getByText('Predicción de demanda')).toBeInTheDocument()
    expect(screen.getByText(/Productos con modelo ML/i)).toBeInTheDocument()
    expect(screen.getByText(/Productos en línea base/i)).toBeInTheDocument()
    expect(screen.getByText(/Mejora media vs. línea base/i)).toBeInTheDocument()
  })

  it('muestra los nombres legibles de métodos en la tabla', () => {
    renderPredicciones()
    expect(screen.getByText('Random Forest')).toBeInTheDocument()
    expect(screen.getByText('Gradient Boosting')).toBeInTheDocument()
    expect(screen.getByText('Regresión Ridge')).toBeInTheDocument()
    expect(screen.getByText('Promedio móvil')).toBeInTheDocument()
    expect(screen.getByText('Sin historial')).toBeInTheDocument()
  })

  it('pinta la mejora en verde cuando es positiva', () => {
    renderPredicciones()
    const mejoraPositiva = screen.getByText('+52.0%')
    expect(mejoraPositiva).toHaveClass('mejora-positiva')
  })

  it('pinta la mejora en neutro cuando es cero', () => {
    renderPredicciones()
    const mejoraNeutra = screen.getByText('0.0%')
    expect(mejoraNeutra).not.toHaveClass('mejora-positiva')
  })

  it('muestra el aviso de simulación siempre', () => {
    renderPredicciones()
    expect(screen.getByText(/Datos de simulación/i)).toBeInTheDocument()
    expect(screen.getByText(/no su desempeño real en el negocio/i)).toBeInTheDocument()
  })

  it('al elegir una fila, carga el detalle con gráfico y motivo', async () => {
    renderPredicciones()
    // Click on the row with "Promedio móvil" and motivo
    const rowPromedio = screen.getByText('Promedio móvil').closest('tr')
    fireEvent.click(rowPromedio!)
    await waitFor(() => expect(screen.getByText('Detalle: Crema facial (SIM-002)')).toBeInTheDocument())
    expect(screen.getByText('¿Por qué se usa la línea base?')).toBeInTheDocument()
    expect(screen.getByText('el modelo no supera a la línea base')).toBeInTheDocument()
  })

  it('un rol sin permiso no accede', () => {
    mocks.canMap.current.set('prediccion:ver', false)
    renderPredicciones()
    expect(screen.getByText('No autorizado')).toBeInTheDocument()
  })

  it('el gráfico maneja historial vacío', async () => {
    // Select the sin_historial product
    const rowSinHistorial = screen.getByText('Sin historial').closest('tr')
    fireEvent.click(rowSinHistorial!)
    await waitFor(() => expect(screen.getByText('Detalle: Shampoo (SIM-003)')).toBeInTheDocument())
    expect(screen.getByText('Sin historial de ventas')).toBeInTheDocument()
  })

  it('botón Actualizar predicciones llama a generarSugerencias y recarga', async () => {
    renderPredicciones()
    const btnActualizar = screen.getByRole('button', { name: /actualizar predicciones/i })
    await fireEvent.click(btnActualizar)
    await waitFor(() => expect(screen.getByText(/Predicciones actualizadas/i)).toBeInTheDocument())
  })
})