export const formatPrice = (value) =>
  `$${Number(value || 0).toLocaleString('es-AR', { maximumFractionDigits: 2 })}`

export const variantSummary = (variants = []) =>
  variants.map((v) => (v.label ? `${v.label} ${formatPrice(v.price)}` : formatPrice(v.price))).join(' · ')

// Devuelve una copia con los elementos i y j intercambiados, o null si j está fuera de rango.
export const swap = (list, i, j) => {
  if (j < 0 || j >= list.length) return null
  const copy = [...list]
  ;[copy[i], copy[j]] = [copy[j], copy[i]]
  return copy
}

export const normalizeText = (text = '') =>
  text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export const errorMessage = (err, fallback) => err?.response?.data?.error || fallback

export const PUBLIC_MENU_URL = import.meta.env.VITE_PUBLIC_MENU_URL || 'https://galia-carta.onrender.com'
