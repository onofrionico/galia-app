// Convierte un documento de impresión (JSON del backend) en texto de ancho fijo y en comandos ESC/POS.
// Funciones puras: las usan la página de impresión (QZ Tray), el modo simulación y los tests.
const ESC = '\x1b'
const GS = '\x1d'
const INDENT = '    '

export const columnsFor = (width) => (Number(width) === 58 ? 32 : 48)

export function formatTicketMoney(amount) {
  const value = Number(amount)
  const sign = value < 0 ? '-' : ''
  const [whole, cents] = Math.abs(value).toFixed(2).split('.')
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${sign}$ ${grouped}${cents === '00' ? '' : `,${cents}`}`
}

const REPLACEMENTS = [[/[‒-―−]/g, '-'], [/[“”„]/g, '"'], [/[‘’‚]/g, "'"],
  [/…/g, '...']]

// La impresora usa CP858: acentos compuestos (NFC), comillas y rayas a ASCII, y fuera lo que no existe (emojis).
export function toCp858(text) {
  let out = String(text ?? '').normalize('NFC')
  for (const [pattern, replacement] of REPLACEMENTS) out = out.replace(pattern, replacement)
  return out.replace(/[^\x20-\x7E -ÿ€]/g, '')
}

// Corta en palabras sin pasar `cols`; las palabras más largas que el renglón se parten.
// Los renglones de continuación llevan `indent` y también entran en `cols`.
function wrap(text, cols, indent = '') {
  const room = cols - indent.length
  const lines = []
  let current = ''
  for (const word of toCp858(text).split(/\s+/).filter(Boolean)) {
    const pieces = []
    for (let rest = word; rest.length; rest = rest.slice(room)) pieces.push(rest.slice(0, room))
    for (const piece of pieces) {
      const candidate = current ? `${current} ${piece}` : piece
      const limit = lines.length ? room : cols
      if (candidate.length <= limit) current = candidate
      else {
        lines.push(current)
        current = piece
      }
    }
  }
  if (current || !lines.length) lines.push(current)
  return lines.map((line, i) => (i === 0 ? line : `${indent}${line}`))
}

// Todos los renglones con sangría (detalles: modificadores y notas).
const indented = (text, cols) => wrap(text, cols - INDENT.length).map((line) => `${INDENT}${line}`)

function withAmount(left, amount, cols) {
  const right = formatTicketMoney(amount)
  const lines = wrap(left, cols - right.length - 1, INDENT)
  const last = lines.pop()
  return [...lines, `${last}${' '.repeat(cols - last.length - right.length)}${right}`]
}

const center = (text, cols) => {
  const pad = Math.max(0, Math.floor((cols - text.length) / 2))
  return `${' '.repeat(pad)}${text}`.trimEnd()
}

function headerLines(doc, cols) {
  return (doc.header ?? []).flatMap((header) => wrap(header, cols))
}

function bodyLines(doc, cols) {
  const out = []
  const rule = '-'.repeat(cols)
  out.push(rule)
  for (const line of doc.lines ?? []) {
    const left = `${line.strike ? 'XX ' : ''}${line.qty} x ${line.text}`
    out.push(...(line.amount != null ? withAmount(left, line.amount, cols) : wrap(left, cols, INDENT)))
    for (const detail of line.details ?? []) out.push(...indented(detail, cols))
  }
  if ((doc.totals ?? []).length) {
    out.push(rule)
    for (const total of doc.totals) out.push(...withAmount(total.label, total.amount, cols))
  }
  if ((doc.footer ?? []).length) {
    out.push('')
    for (const text of doc.footer) for (const piece of wrap(text, cols)) out.push(center(piece, cols))
  }
  return out
}

export function renderText(doc, width) {
  const cols = columnsFor(width)
  const bodyCols = doc.large_body ? Math.floor(cols / 2) : cols
  const lines = [...wrap(doc.title ?? '', cols).map((t) => center(t, cols)), ...headerLines(doc, cols),
    ...bodyLines({ ...doc, lines: doc.lines, totals: doc.large_body ? [] : doc.totals, footer: doc.large_body ? [] : doc.footer }, bodyCols),
    ...(doc.large_body && (doc.footer ?? []).length ? bodyLines({ lines: [], totals: [], footer: doc.footer }, cols) : [])]
  if (doc.qr) lines.push('', ...wrap(`QR: ${doc.qr}`, cols))
  return lines
}

// QR de ARCA (modelo 2, módulo 6, corrección M): guardar los datos y después imprimirlos.
export function qrCommand(data) {
  const len = data.length + 3
  return `${GS}(k\x04\x001A2\x00` + `${GS}(k\x03\x001C\x06` + `${GS}(k\x03\x001E1`
    + `${GS}(k${String.fromCharCode(len % 256)}${String.fromCharCode(Math.floor(len / 256))}1P0${data}`
    + `${GS}(k\x03\x001Q0`
}

export function renderEscPos(doc, width) {
  const cols = columnsFor(width)
  let out = `${ESC}@${ESC}t\x13`
  // El título va a doble ancho: entran la mitad de las columnas.
  out += `${ESC}a\x01${GS}!\x11${wrap(doc.title ?? '', Math.floor(cols / 2)).join('\n')}\n${GS}!\x00${ESC}a\x00`
  out += `${ESC}E\x01${headerLines(doc, cols).join('\n')}\n${ESC}E\x00`
  if (doc.large_body) {
    // Comandas de cocina: ítems en doble alto y ancho (GS ! 0x11); entran la mitad de columnas.
    const kitchenCols = Math.floor(cols / 2)
    out += `${GS}!\x11${bodyLines({ ...doc, lines: doc.lines, totals: [], footer: [] }, kitchenCols).join('\n')}\n${GS}!\x00`
    if ((doc.footer ?? []).length) {
      out += `${bodyLines({ lines: [], totals: [], footer: doc.footer }, cols).join('\n')}\n`
    }
  } else {
    out += `${bodyLines(doc, cols).join('\n')}\n`
  }
  if (doc.qr) out += `${ESC}a\x01${qrCommand(doc.qr)}\n${ESC}a\x00`
  out += `\n\n\n\n\n${GS}V\x01`
  return out
}
