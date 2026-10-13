const whole = new Intl.NumberFormat('es-AR', {
  style: 'currency', currency: 'ARS', minimumFractionDigits: 0, maximumFractionDigits: 0,
})
const cents = new Intl.NumberFormat('es-AR', {
  style: 'currency', currency: 'ARS', minimumFractionDigits: 2, maximumFractionDigits: 2,
})

export const round2 = (value) => Math.round(value * 100) / 100

export function formatMoney(value) {
  const number = Number(value) || 0
  return Number.isInteger(round2(number)) ? whole.format(number) : cents.format(number)
}

// Texto tipeado por la caja: los puntos son de miles y la coma es decimal.
export function parseAmount(text) {
  const raw = String(text ?? '').replace(/\$/g, '').replace(/\s/g, '')
  // Un único punto seguido de 1-2 dígitos, sin coma, es decimal ("12.50"); si no, los puntos son de miles.
  const dotDecimal = /^\d*\.\d{1,2}$/.test(raw)
  const clean = dotDecimal ? raw : raw.replace(/\./g, '').replace(',', '.')
  if (clean === '') return NaN
  const number = Number(clean)
  return Number.isFinite(number) ? round2(number) : NaN
}

export function amountToText(value) {
  const number = round2(Number(value) || 0)
  return Number.isInteger(number) ? String(number) : number.toFixed(2).replace('.', ',')
}

export function formatQuantity(value) {
  return Number(value).toLocaleString('es-AR', { maximumFractionDigits: 3 })
}

export function discountLabel(discount) {
  return discount.kind === 'percent' ? `${Number(discount.value)}%` : formatMoney(discount.value)
}
