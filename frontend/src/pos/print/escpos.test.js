import { describe, expect, it } from 'vitest'
import { columnsFor, formatTicketMoney, qrCommand, renderEscPos, renderText } from './escpos'

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
  it('usa los caracteres por renglón de la impresora si están configurados', () => {
    expect(columnsFor(80, 42)).toBe(42)
    expect(columnsFor(58, null)).toBe(32)
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
    expect(renderText(bill, 80, 42).every((l) => l.length <= 42)).toBe(true)
    expect(renderText(bill, 80, 42).some((l) => l.length > 32)).toBe(true)
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

describe('caracteres fuera de CP858', () => {
  it('reemplaza la raya y los emojis, y normaliza acentos descompuestos', () => {
    const doc = { ...order, header: ['Mozo: —'], lines: [{ qty: '1', text: 'Café 🍰', amount: null, details: ['Nota: sin “azúcar”'], strike: false }] }
    const lines = renderText(doc, 80)
    expect(lines).toContain('Mozo: -')
    expect(lines).toContain('1 x Café')
    expect(lines).toContain('    Nota: sin "azúcar"')
  })
})

describe('renderEscPos', () => {
  it('parte el título doble a la mitad de columnas sin cortar palabras', () => {
    const data = renderEscPos({ ...order, title: 'ANULACIÓN · COCINA' }, 58)
    expect(data).toContain('\x1d!\x11ANULACIÓN ·\nCOCINA\n')
  })

  it('respeta los caracteres por renglón de la impresora', () => {
    // Sin los comandos ESC/GS (byte de control + 1 o 2 bytes de parámetros) quedan solo los renglones impresos.
    const lines = renderEscPos(bill, 80, 42).split('\n').map((l) => l.replace(/[\x1b\x1d][\s\S]{1,2}/g, ''))
    expect(lines.every((l) => l.length <= 42)).toBe(true)
  })

  it('inicializa, usa CP858, título doble, conserva acentos y corta el papel', () => {
    const data = renderEscPos(bill, 80)
    expect(data.startsWith('\x1b@\x1bt\x13')).toBe(true)
    expect(data).toContain('\x1d!\x11PRECUENTA')
    expect(data).toContain('Medialuña')
    expect(data.endsWith('\x1dV\x01')).toBe(true)
  })
})

describe('QR de ARCA', () => {
  it('arma la secuencia GS ( k con el largo correcto y muestra la URL en simulación', () => {
    const url = 'https://www.afip.gob.ar/fe/qr/?p=abc'
    const cmd = qrCommand(url)
    expect(cmd.startsWith('\x1d(k\x04\x001A2\x00')).toBe(true)
    const len = url.length + 3
    expect(cmd).toContain(`\x1d(k${String.fromCharCode(len % 256)}${String.fromCharCode(Math.floor(len / 256))}1P0${url}`)
    expect(cmd.endsWith('\x1d(k\x03\x001Q0')).toBe(true)
    const doc = { ...bill, qr: url }
    expect(renderEscPos(doc, 80)).toContain(cmd)
    expect(renderText(doc, 80).join('')).toContain('afip.gob.ar/fe/qr')
    expect(renderEscPos(bill, 80)).not.toContain('\x1d(k')
  })
})
