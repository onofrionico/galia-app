const STATUS = { conciliado: 'Conciliado', con_diferencias: 'Con diferencias', sin_traer: 'Sin traer' }
const CHANNELS = { point: 'Point', qr: 'QR', link: 'Link de pago', transfer: 'Transferencia', other: 'Otro' }

export const statusLabel = (status) => STATUS[status] ?? status
export const channelLabel = (channel) => CHANNELS[channel] ?? 'Otro'

export function monthDays(year, month) {
  const last = new Date(Date.UTC(year, month, 0)).getUTCDate()
  const mm = String(month).padStart(2, '0')
  return Array.from({ length: last }, (_, i) => `${year}-${mm}-${String(i + 1).padStart(2, '0')}`)
}
