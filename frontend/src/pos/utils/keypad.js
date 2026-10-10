// Aplica una tecla del teclado numérico. `fresh` indica que el valor actual es una sugerencia
// (por ejemplo, el saldo) y la primera tecla lo reemplaza.
export function applyKey(text, key, fresh) {
  if (key === 'back') return fresh ? '' : text.slice(0, -1)
  if (key === ',') {
    if (fresh || text === '') return '0,'
    return text.includes(',') ? text : `${text},`
  }
  if (fresh || text === '0') return key
  const decimals = text.split(',')[1]
  if (decimals !== undefined && decimals.length >= 2) return text
  return text + key
}
