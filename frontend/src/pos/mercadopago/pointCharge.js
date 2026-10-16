import { parseServerDate } from '../utils/time'

export const POLL_MS = 3000
const WAITING = ['creating', 'created', 'processing', 'canceling']
const FINAL = ['approved', 'failed', 'canceled', 'expired']

export const isWaiting = (status) => WAITING.includes(status)
export const isFinal = (status) => FINAL.includes(status)

export function waitingLabel(order) {
  if (order.status === 'processing') return 'Cobrando en el Point…'
  if (order.status === 'canceling') return 'Cancelando en el Point…'
  return 'Esperando el cobro en el Point…'
}

export function resultMessage(order) {
  if (order.status === 'approved') {
    return order.error ? { tone: 'warn', text: order.error } : { tone: 'ok', text: 'Cobro aprobado' }
  }
  const fallback = { failed: 'No se pudo cobrar', canceled: 'Se canceló el cobro', expired: 'El cobro venció sin pagarse' }
  return { tone: 'error', text: order.error || fallback[order.status] || 'No se pudo cobrar' }
}

export function elapsedText(createdAt, now = new Date()) {
  const seconds = Math.max(0, Math.floor((now - parseServerDate(createdAt)) / 1000))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}
