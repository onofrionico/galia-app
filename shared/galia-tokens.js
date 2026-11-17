// Paleta oficial de Galia. Fuente: sistema de diseño "Galia" (tokens.json).
// https://claude.ai/artifact/DVadrPwPoMSXDUZxmVWvbi
export const GALIA_COLORS = {
  plum: '#673b4c',
  terracotta: '#dd8c76',
  lime: '#cbd159',
  cream: '#edece4',
  sand100: '#e1ded0',
  sand200: '#d1cdba',
  white: '#ffffff',
}

function luminance(hex) {
  const n = parseInt(hex.replace('#', '').slice(0, 6), 16)
  const channels = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const c = v / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

// Relación de contraste WCAG entre dos colores hex (#rrggbb).
export function contrastRatio(fg, bg) {
  const [hi, lo] = [luminance(fg), luminance(bg)].sort((a, b) => b - a)
  return (hi + 0.05) / (lo + 0.05)
}
