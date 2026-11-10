// Utilidades del reporte de Producción (pronóstico por turno).

const normalize = (text) =>
  (text || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

// Agrupa por categoría manteniendo el orden del backend; filtra por nombre (sin tildes ni mayúsculas).
export const groupByCategory = (products, query) => {
  const needle = normalize(query).trim()
  const groups = []
  const byCategory = new Map()
  for (const product of products || []) {
    if (needle && !normalize(`${product.producto} ${product.variante || ''}`).includes(needle)) continue
    if (!byCategory.has(product.categoria)) {
      const group = { categoria: product.categoria, products: [] }
      byCategory.set(product.categoria, group)
      groups.push(group)
    }
    byCategory.get(product.categoria).products.push(product)
  }
  return groups
}

export const formatUnits = (value) =>
  new Intl.NumberFormat('es-AR', { maximumFractionDigits: 1 }).format(value || 0)

export const productName = (product) =>
  product.variante && product.variante !== 'Unidad' ? `${product.producto} (${product.variante})` : product.producto

// 'YYYY-MM-DD' + n días, en aritmética local (new Date('YYYY-MM-DD') es UTC y en Argentina corre un día).
export const addDays = (iso, days) => {
  const [year, month, day] = iso.split('-').map(Number)
  const date = new Date(year, month - 1, day + days)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const WEEKDAYS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb']

// 'YYYY-MM-DD' → 'sáb 7/11'
export const shortDay = (iso) => {
  const [year, month, day] = iso.split('-').map(Number)
  return `${WEEKDAYS[new Date(year, month - 1, day).getDay()]} ${day}/${month}`
}

// Mañana en hora Argentina, como 'YYYY-MM-DD'.
export const tomorrowArgentina = () => {
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' }).format(new Date())
  return addDays(today, 1)
}
