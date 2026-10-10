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
