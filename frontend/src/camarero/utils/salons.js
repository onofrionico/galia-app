// Salón a mostrar: el de la URL, si no el guardado en el dispositivo, si no el primero activo.
export function pickSalonId({ fromUrl = null, saved = null, salons = [] }) {
  const ids = salons.map((s) => s.id)
  if (fromUrl != null && ids.includes(fromUrl)) return fromUrl
  if (saved != null && ids.includes(saved)) return saved
  return ids[0] ?? null
}
