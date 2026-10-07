export function normalize(text) {
  return (text || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}
