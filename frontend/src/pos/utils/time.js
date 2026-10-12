// El backend guarda UTC sin zona ("2026-10-10T12:00:00"): se la agregamos para no leerla como hora local.
export function parseServerDate(iso) {
  if (!iso) return null
  return new Date(/[zZ]$|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`)
}

export function elapsedLabel(iso, now = new Date()) {
  const date = parseServerDate(iso)
  if (!date) return ''
  const minutes = Math.max(0, Math.floor((now - date) / 60000))
  if (minutes < 60) return `${minutes} min`
  return `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, '0')}`
}

export function timeLabel(iso) {
  const date = parseServerDate(iso)
  return date ? date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false }) : ''
}
