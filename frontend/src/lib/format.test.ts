import { describe, expect, it } from 'vitest'
import { formatCantidad, formatFecha, formatQ, parseDecimal } from './format'

describe('parseDecimal', () => {
  it('convierte cadenas y números a número', () => {
    expect(parseDecimal('150.50')).toBe(150.5)
    expect(parseDecimal(12)).toBe(12)
    expect(parseDecimal('-3.25')).toBe(-3.25)
  })

  it('devuelve null para vacíos e inválidos', () => {
    expect(parseDecimal('')).toBeNull()
    expect(parseDecimal('   ')).toBeNull()
    expect(parseDecimal('abc')).toBeNull()
    expect(parseDecimal(null)).toBeNull()
    expect(parseDecimal(undefined)).toBeNull()
    expect(parseDecimal(Number.NaN)).toBeNull()
  })
})

describe('formatQ', () => {
  it('formatea con el símbolo de quetzal y dos decimales', () => {
    const resultado = formatQ('150.5')
    expect(resultado).toContain('Q')
    expect(resultado).toContain('150.50')
  })

  it('devuelve el marcador de vacío cuando no hay valor', () => {
    expect(formatQ(null)).toBe('—')
    expect(formatQ(undefined)).toBe('—')
  })
})

describe('formatCantidad', () => {
  it('formatea cantidades sin decimales innecesarios', () => {
    expect(formatCantidad('12')).toBe('12')
    expect(formatCantidad('12.5')).toContain('12.5')
  })
})

describe('formatFecha', () => {
  it('devuelve el marcador para fechas ausentes o inválidas', () => {
    expect(formatFecha(null)).toBe('—')
    expect(formatFecha('')).toBe('—')
    expect(formatFecha('no-es-fecha')).toBe('—')
  })

  it('formatea una fecha ISO válida', () => {
    expect(formatFecha('2026-03-15')).not.toBe('—')
  })
})
