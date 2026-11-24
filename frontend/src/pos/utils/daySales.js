// Helpers de la pestaña Ventas del POS: día comercial (fecha de Argentina) y resumen del día.

// Fecha AAAA-MM-DD en Argentina (el backend asigna el día comercial con esa misma zona).
export const argentinaToday = (now = new Date()) =>
  now.toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })

export function shiftDay(day, delta) {
  const date = new Date(`${day}T12:00:00Z`)
  date.setUTCDate(date.getUTCDate() + delta)
  return date.toISOString().slice(0, 10)
}

export const isToday = (day, now = new Date()) => day === argentinaToday(now)

// Las anuladas no suman al total cobrado. Se redondea a centavos para evitar residuos de coma flotante.
export function daySummary(sales) {
  const closed = sales.filter((sale) => sale.status === 'closed')
  return {
    closed: closed.length,
    cancelled: sales.filter((sale) => sale.status === 'cancelled').length,
    total: Math.round(closed.reduce((sum, sale) => sum + Number(sale.total), 0) * 100) / 100,
  }
}
