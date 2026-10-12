import { formatMoney } from './money'

export const normalize = (text) =>
  String(text ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()

export function filterProducts(products, { query = '', categoryId = null } = {}) {
  const q = normalize(query)
  return products.filter(
    (p) => (categoryId == null || p.category_id === categoryId) && (!q || normalize(p.name).includes(q)),
  )
}

export function priceLabel(product) {
  const prices = product.variants.map((v) => v.price)
  const min = Math.min(...prices)
  return prices.length > 1 ? `desde ${formatMoney(min)}` : formatMoney(min)
}

export const needsDetail = (product) => product.variants.length > 1 || product.modifier_groups.length > 0

export function addedSummary(added) {
  if (added.length === 0) return ''
  const counts = new Map()
  for (const { name, quantity } of added) counts.set(name, (counts.get(name) ?? 0) + quantity)
  const total = [...counts.values()].reduce((a, b) => a + b, 0)
  const parts = [...counts.entries()].map(([name, quantity]) => `${quantity} ${name}`)
  return `${total} agregados: ${parts.join(', ')}`
}
