import { parseAmount, round2 } from './money'
import { timeLabel } from './time'

// Diferencia en vivo del arqueo (contado − esperado). Lo guardado lo calcula el backend.
export function countDifference(expected, text) {
  const counted = parseAmount(text)
  if (!Number.isFinite(counted)) return null
  return round2(counted - Number(expected))
}

export function differenceTone(diff) {
  if (diff == null) return null
  if (diff < 0) return 'missing'
  if (diff > 0) return 'over'
  return 'even'
}

// Valida el cierre: el efectivo es obligatorio, lo vacío vale lo esperado y una diferencia exige nota.
export function closeValidation(methods, texts, note) {
  const counts = []
  let hasDifference = false
  for (const method of methods) {
    const text = String(texts[method.payment_method_id] ?? '').trim()
    if (!text) {
      if (method.kind === 'cash') return { ok: false, error: 'Cargá lo contado en efectivo', counts: [] }
      counts.push({ payment_method_id: method.payment_method_id, counted: Number(method.expected) })
      continue
    }
    const counted = parseAmount(text)
    if (!Number.isFinite(counted) || counted < 0) {
      return { ok: false, error: `Revisá lo contado en ${method.method_name}`, counts: [] }
    }
    if (round2(counted - Number(method.expected)) !== 0) hasDifference = true
    counts.push({ payment_method_id: method.payment_method_id, counted })
  }
  if (hasDifference && !String(note ?? '').trim()) {
    return { ok: false, error: 'Explicá la diferencia en la nota', counts: [] }
  }
  return { ok: true, error: null, counts }
}

export function cashStatusLabel(register, formatTime = timeLabel) {
  if (!register) return 'Sin caja configurada'
  if (!register.open_session) return 'Caja cerrada'
  return `Caja abierta · desde ${formatTime(register.open_session.opened_at)}`
}
