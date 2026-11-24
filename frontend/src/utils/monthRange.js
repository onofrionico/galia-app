const pad = (n) => String(n).padStart(2, '0')
const ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

// Primer y último día del mes de `now`, en fecha local (YYYY-MM-DD), sin pasar por UTC.
export function currentMonthRange(now = new Date()) {
  const first = new Date(now.getFullYear(), now.getMonth(), 1)
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  return { from: ymd(first), to: ymd(last) }
}
