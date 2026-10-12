// Selector de cantidad de a uno, entre 0 y `max` (que puede no ser entero).
export function stepQuantity(current, max, delta) {
  const next = current + delta
  if (next <= 0) return 0
  return next >= max ? max : next
}
