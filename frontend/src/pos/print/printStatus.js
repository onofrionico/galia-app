const KIND_LABELS = { order: 'Comanda', void: 'Anulación', bill: 'Precuenta', receipt: 'Ticket', test: 'Prueba', invoice: 'Factura' }

// Estado del indicador de impresión de la caja.
export function printHealth(status) {
  if (!status) return 'unknown'
  if ((status.problems ?? []).length || (status.points ?? []).some((p) => p.down)) return 'alert'
  return status.pending > 0 ? 'busy' : 'ok'
}

export function jobLabel(job) {
  return [KIND_LABELS[job.kind] ?? job.kind, job.station_name ?? 'Caja', job.place].filter(Boolean).join(' · ')
}
