import { posKeys } from '../hooks/keys'

// Traduce la respuesta de GET /pos/changes a las claves de React Query que hay que invalidar.
export function keysToInvalidate(response) {
  if (!response) return []
  if (response.reset) return [posKeys.all]
  const sales = response.sales ?? []
  if (sales.length === 0) return []
  const keys = []
  for (const sale of sales) keys.push(posKeys.sale(sale.id), posKeys.events(sale.id))
  if (sales.some((s) => s.sale_type === 'salon')) keys.push(posKeys.floors)
  if (sales.some((s) => s.sale_type === 'counter')) keys.push(posKeys.sales)
  return keys
}

// Deja solo las ventas con algún evento no visto. /pos/changes repite una ventana de eventos
// anteriores a `since` (un evento puede confirmarse tarde con un id menor al último informado).
// Una venta sin `event_ids` (backend anterior) se considera cambiada.
export function unseenChanges(response, seenIds) {
  if (!response || response.reset) return response
  const sales = (response.sales ?? []).filter(
    (sale) => !sale.event_ids || sale.event_ids.some((id) => !seenIds.has(id)),
  )
  return { ...response, sales }
}

// Agrega los ids vistos y conserva solo los `max` más altos: la ventana del backend no retrocede.
export function rememberEventIds(seenIds, eventIds, max = 1000) {
  if (!eventIds || eventIds.length === 0) return seenIds
  const merged = new Set(seenIds)
  for (const id of eventIds) merged.add(id)
  if (merged.size <= max) return merged
  return new Set([...merged].sort((a, b) => b - a).slice(0, max))
}

// La caja se refresca cuando cambia `cash_version` (último id de cash_events). La primera lectura no cuenta.
export function cashChanged(previous, next) {
  return previous != null && next != null && previous !== next
}
