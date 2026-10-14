import { describe, expect, it } from 'vitest'
import { columnsFor, formatTicketMoney, renderEscPos, renderText } from './escpos'

const order = {
  title: 'COCINA',
  header: ['Mesa 1', 'Mozo: Ana', 'Tanda 1', '14/10/2026 13:05'],
  lines: [
    { qty: '2', text: 'Tostado', amount: null, details: ['Nota: sin sal'], strike: false },
    { qty: '1', text: 'Sándwich de jamón crudo, rúcula y parmesano en pan de campo', amount: null, details: [], strike: false },
  ],
  totals: [],
  footer: [],
}

const bill = {
  title: 'PRECUENTA',
  header: ['Mesa 1', 'Venta #3'],
  lines: [{ qty: '2', text: 'Medialuña', amount: '1800.00', details: [], strike: false }],
  totals: [{ label: 'Subtotal', amount: '1800.00' }, { label: 'Descuento', amount: '-180.00' }, { label: 'TOTAL', amount: '1620.00' }],
  footer: ['No válido como factura'],
}

describe('columnsFor', () => {
  it('usa 32 columnas en 58 mm y 48 en 80 mm', () => {
    expect(columnsFor(58)).toBe(32)
    expect(columnsFor(80)).toBe(48)
  })
})

describe('formatTicketMoney', () => {
  it('formatea en pesos argentinos', () => {
    expect(formatTicketMoney('1800.00')).toBe('$ 1.800')
    expect(formatTicketMoney('1234.50')).toBe('$ 1.234,50')
    expect(formatTicketMoney('-180.00')).toBe('-$ 180')
  })
})

describe('renderText', () => {
  it('nunca supera el ancho y corta renglones largos con sangría', () => {
    for (const width of [58, 80]) {
      const lines = renderText(order, width)
      expect(lines.every((l) => l.length <= columnsFor(width))).toBe(true)
    }
    const lines = renderText(order, 58)
    expect(lines).toContain('2 x Tostado')
    expect(lines).toContain('    Nota: sin sal')
    expect(lines.filter((l) => l.startsWith('1 x Sándwich')).length).toBe(1)
    expect(lines.some((l) => l.startsWith('    ') && l.includes('parmesano'))).toBe(true)
  })

  it('alinea los montos a la derecha y muestra los totales', () => {
    const lines = renderText(bill, 58)
    const item = lines.find((l) => l.startsWith('2 x Medialuña'))
    expect(item.endsWith('$ 1.800')).toBe(true)
    expect(item.length).toBe(32)
    expect(lines.find((l) => l.startsWith('TOTAL'))).toBe(`TOTAL${' '.repeat(32 - 5 - '$ 1.620'.length)}$ 1.620`)
    // Centrado: Math.floor((32 - 22) / 2) = 5 espacios a la izquierda.
    expect(lines).toContain(`${' '.repeat(5)}No válido como factura`)
  })

  it('marca los renglones anulados', () => {
    const voided = { ...order, lines: [{ ...order.lines[0], strike: true }] }
    expect(renderText(voided, 80)).toContain('XX 2 x Tostado')
  })

  it('parte palabras más largas que el renglón sin pasarse del ancho', () => {
    const long = { ...order, lines: [{ qty: '1', text: 'Superextraordinariamentelargoyacentuadísimoñandú', amount: '10.00', details: [], strike: false }] }
    const lines = renderText(long, 58)
    expect(lines.every((l) => l.length <= 32)).toBe(true)
    expect(lines.some((l) => l.endsWith('$ 10'))).toBe(true)
  })
})

describe('renderEscPos', () => {
  it('inicializa, usa CP858, título doble, conserva acentos y corta el papel', () => {
    const data = renderEscPos(bill, 80)
    expect(data.startsWith('\x1b@\x1bt\x13')).toBe(true)
    expect(data).toContain('\x1d!\x11PRECUENTA')
    expect(data).toContain('Medialuña')
    expect(data.endsWith('\x1dV\x01')).toBe(true)
  })
})
