import { round2 } from './money'

const STEPS = [1000, 5000, 10000, 20000]

// Vista previa del vuelto; el vuelto real lo calcula el backend al registrar el pago.
export function changeFor(amount, tendered) {
  if (!Number.isFinite(amount) || !Number.isFinite(tendered) || tendered < amount) return null
  return round2(tendered - amount)
}

export function quickTenders(amount) {
  if (!(amount > 0)) return []
  const values = [round2(amount)]
  for (const step of STEPS) {
    const value = Math.ceil(amount / step) * step
    if (value > amount && !values.includes(value)) values.push(value)
  }
  return values.slice(0, 4)
}
