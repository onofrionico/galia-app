// Índice de la última sección cuyo top es <= threshold; 0 si ninguna.
export function activeSectionIndex(tops, threshold) {
  let index = 0
  for (let i = 0; i < tops.length; i += 1) {
    if (tops[i] <= threshold) index = i
  }
  return index
}
