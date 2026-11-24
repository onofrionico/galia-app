// Rangos de fechas (YYYY-MM-DD, hora local, sin pasar por UTC) para los filtros rápidos.
const pad = (n) => String(n).padStart(2, '0')
const ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const range = (from, to) => ({ from: ymd(from), to: ymd(to) })

// month: 1-12
export function monthRangeOf({ year, month }) {
  return range(new Date(year, month - 1, 1), new Date(year, month, 0))
}

export const DEFAULT_PERIOD = 'diario'

export function currentMonthRange(now = new Date()) {
  return monthRangeOf({ year: now.getFullYear(), month: now.getMonth() + 1 })
}

export function shiftMonth({ year, month }, delta) {
  const d = new Date(year, month - 1 + delta, 1)
  return { year: d.getFullYear(), month: d.getMonth() + 1 }
}

// period: 'diario' | 'semanal' (lunes a domingo) | 'mensual' | 'trimestral' | 'anual'
export function periodRange(period, now = new Date()) {
  const y = now.getFullYear()
  const m = now.getMonth()
  const day = now.getDate()
  switch (period) {
    case 'diario':
      return range(new Date(y, m, day), new Date(y, m, day))
    case 'semanal': {
      const sinceMonday = (now.getDay() + 6) % 7
      return range(new Date(y, m, day - sinceMonday), new Date(y, m, day - sinceMonday + 6))
    }
    case 'trimestral': {
      const start = Math.floor(m / 3) * 3
      return range(new Date(y, start, 1), new Date(y, start + 3, 0))
    }
    case 'anual':
      return range(new Date(y, 0, 1), new Date(y, 12, 0))
    default:
      return currentMonthRange(now)
  }
}

// Vista inicial de Ventas y Gastos: hoy.
export const defaultRange = () => periodRange(DEFAULT_PERIOD)
