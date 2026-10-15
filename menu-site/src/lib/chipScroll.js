// Desplazamiento horizontal de la barra de categorías que deja el chip activo centrado, sin pasarse de los bordes.
export function centeredScrollLeft({ chipLeft, chipWidth, navWidth, scrollWidth }) {
  const target = chipLeft + chipWidth / 2 - navWidth / 2
  const max = Math.max(0, scrollWidth - navWidth)
  return Math.min(Math.max(0, target), max)
}
