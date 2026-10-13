// Datos de Productos que vienen de Fudo durante la transición (ver spec 2026-10-13-products-fudo-sync).

export const FUDO_LOCK_HINT = 'Se edita en Fudo'

export const FUDO_STATUS_LABELS = {
  ok: 'Fudo',
  inactive: 'Inactiva en Fudo',
  missing: 'Ya no existe en Fudo',
}

export const isFudoLocked = (product, field) => Boolean(product?.fudo_locked_fields?.includes(field))

export const variantFudoStatus = (variant) =>
  variant?.fudo_product_id ? variant.fudo_status || 'ok' : null

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

export const syncSummary = (result) => {
  const c = result?.catalog || {}
  const parts = [
    plural(c.variants_updated || 0, 'variante actualizada', 'variantes actualizadas'),
    plural(c.products_created || 0, 'producto nuevo', 'productos nuevos'),
  ]
  if (c.alerts) parts.push(plural(c.alerts, 'alerta', 'alertas'))
  return `Fudo sincronizado: ${parts.join(' · ')}`
}

export const candidateLegend = (candidate, productId) => {
  if (candidate.product_id === productId) return 'ya en este producto'
  if (candidate.product_id) return `se moverá desde «${candidate.product_name}»`
  return candidate.is_active === false ? 'inactivo en Fudo' : null
}
