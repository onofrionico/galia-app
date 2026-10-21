// Lógica pura de la pestaña "Productos" de Reportes.

const normalize = (text) =>
  (text || '').toString().normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export const productLabel = (product) =>
  product.variante ? `${product.producto} (${product.variante})` : product.producto

// Filtra por texto (producto, variante o categoría, sin tildes) y por categoría, y ordena.
export const filterAndSortProducts = (products, { query = '', category = '', sortKey = 'facturacion', sortDir = 'desc' } = {}) => {
  const q = normalize(query.trim())
  const filtered = (products || []).filter((p) => {
    if (category && p.categoria !== category) return false
    if (!q) return true
    return [p.producto, p.variante, p.categoria].some((field) => normalize(field).includes(q))
  })
  const factor = sortDir === 'asc' ? 1 : -1
  return [...filtered].sort((a, b) => {
    const av = sortKey === 'producto' ? productLabel(a) : a[sortKey]
    const bv = sortKey === 'producto' ? productLabel(b) : b[sortKey]
    if (av == null && bv == null) return 0
    if (av == null) return 1 // sin dato siempre al final
    if (bv == null) return -1
    if (typeof av === 'string') return av.localeCompare(bv, 'es') * factor
    return (av - bv) * factor
  })
}

// Qué tan completo es el detalle por producto del período.
export const coverageLevel = (pct) => {
  if (pct >= 95) return 'ok'
  if (pct >= 70) return 'partial'
  return 'low'
}

export const nextSort = (current, key) => {
  if (current.sortKey === key) return { sortKey: key, sortDir: current.sortDir === 'desc' ? 'asc' : 'desc' }
  return { sortKey: key, sortDir: key === 'producto' ? 'asc' : 'desc' }
}
