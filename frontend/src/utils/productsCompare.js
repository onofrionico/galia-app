// Lógica pura de "Comparar meses" en la pestaña Productos de Reportes.

const num = (value) => Number(value) || 0

// Productos ordenados por el mes B según la medida ('amount' | 'quantity'); a igualdad, por nombre.
export const rankProducts = (products, measure) =>
  [...(products || [])].sort((x, y) => num(y.b[measure]) - num(x.b[measure]) || x.name.localeCompare(y.name))

// Variación porcentual entera de A a B; null si A es 0 (no hay contra qué comparar).
export const variation = (a, b) => {
  const before = num(a)
  if (before === 0) return null
  return Math.round(((num(b) - before) / before) * 100)
}

// Ancho de cada barra (0-100), escalado al mayor valor de los dos meses.
export const barWidths = (products, measure) => {
  const max = Math.max(0, ...(products || []).flatMap((p) => [num(p.a[measure]), num(p.b[measure])]))
  return (products || []).map((p) => ({
    key: p.key,
    a: max ? Math.round((num(p.a[measure]) / max) * 100) : 0,
    b: max ? Math.round((num(p.b[measure]) / max) * 100) : 0,
  }))
}

const monthKey = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

// [mes anterior, mes actual] en formato YYYY-MM.
export const defaultMonths = (today = new Date()) => {
  const previous = new Date(today.getFullYear(), today.getMonth() - 1, 1)
  return [monthKey(previous), monthKey(today)]
}
