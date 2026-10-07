const numberFormat = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 })

export function formatPrice(price) {
  return `$${numberFormat.format(price)}`
}

export function formatVariant(variant) {
  return variant.label ? `${variant.label} ${formatPrice(variant.price)}` : formatPrice(variant.price)
}

export function instagramHandle(value) {
  if (typeof value !== 'string') return ''
  let handle = value.trim()
  const match = handle.match(/instagram\.com\/([^/?#]*)/i)
  if (match) handle = match[1]
  return handle.trim().replace(/^@/, '')
}
