import { parseAmount, round2 } from './money'
import { parseServerDate, timeLabel } from './time'

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

// Valida el cierre: el efectivo es obligatorio y una diferencia exige nota. Los medios vacíos
// no se envían: el backend toma su esperado actual (el del cliente puede estar desactualizado).
export function closeValidation(methods, texts, note) {
  const counts = []
  let hasDifference = false
  for (const method of methods) {
    const text = String(texts[method.payment_method_id] ?? '').trim()
    if (!text) {
      if (method.kind === 'cash') return { ok: false, error: 'Cargá lo contado en efectivo', counts: [] }
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

// --- Apertura con hora anterior. Argentina no tiene horario de verano: el offset es siempre -03:00.
const AR_TZ = 'America/Argentina/Buenos_Aires'

function argentinaParts(date) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: AR_TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date)
  return Object.fromEntries(parts.map((p) => [p.type, p.value]))
}

// Valor de un <input type="datetime-local"> (hora de Argentina) → ISO con offset para el backend.
export function toArgentinaIso(localValue) {
  if (!localValue) return null
  return `${localValue.slice(0, 16)}:00-03:00`
}

// Instante → valor de datetime-local en hora de Argentina ("YYYY-MM-DDTHH:mm").
export function argentinaLocalInput(date) {
  const p = argentinaParts(date)
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`
}

// "2026-11-26T08:00" → "26/11 08:00".
export function localInputLabel(localValue) {
  const [day, time] = localValue.split('T')
  const [, month, dd] = day.split('-')
  return `${dd}/${month} ${time.slice(0, 5)}`
}

// Hora UTC del backend → día de Argentina ("YYYY-MM-DD").
export function argentinaDate(iso) {
  const date = parseServerDate(iso)
  if (!date) return null
  const p = argentinaParts(date)
  return `${p.year}-${p.month}-${p.day}`
}

// Hora UTC del backend → "dd/mm HH:MM" en hora de Argentina.
export function dateTimeLabel(iso) {
  const date = parseServerDate(iso)
  return date ? localInputLabel(argentinaLocalInput(date)) : ''
}

export function openedBeforeToday(session, today) {
  return Boolean(session?.opened_at) && argentinaDate(session.opened_at) < today
}
