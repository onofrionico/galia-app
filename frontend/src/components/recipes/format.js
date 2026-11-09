const numberFormat = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 3 })

const hasValue = (v) => v !== null && v !== undefined && v !== ''

function formatMinutes(total) {
  const hours = Math.floor(total / 60)
  const minutes = total % 60
  if (hours === 0) return `${minutes} min`
  if (minutes === 0) return `${hours} h`
  return `${hours} h ${minutes} min`
}

export function formatStepTime(min, max) {
  const a = hasValue(min) ? Number(min) : null
  const b = hasValue(max) ? Number(max) : null
  if (a === null && b === null) return ''
  if (a === null || b === null || a === b) return formatMinutes(a ?? b)
  const [lo, hi] = a < b ? [a, b] : [b, a]
  if (hi < 60) return `${lo}–${hi} min`
  return `${formatMinutes(lo)} – ${formatMinutes(hi)}`
}

function withUnit(quantity, unit) {
  const n = Number(quantity)
  const text = numberFormat.format(n)
  if (!unit) return text
  const label = unit === 'unidad' && n !== 1 ? 'unidades' : unit
  return `${text} ${label}`
}

export function formatQuantity(quantity, unit, note) {
  if (hasValue(quantity)) return withUnit(quantity, unit)
  return hasValue(note) ? note : 'a completar'
}

export function formatYield(quantity, unit) {
  return hasValue(quantity) ? withUnit(quantity, unit) : ''
}
