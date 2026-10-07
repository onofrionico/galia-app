const numberFormat = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 })

export function formatPrice(price) {
  return `$${numberFormat.format(price)}`
}

export function formatVariant(variant) {
  return variant.label ? `${variant.label} ${formatPrice(variant.price)}` : formatPrice(variant.price)
}
