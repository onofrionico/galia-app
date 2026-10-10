// Identificador para que un pago reintentado no se registre dos veces (client_request_id).
export function newRequestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const random = () => Math.random().toString(36).slice(2, 10)
  return `${Date.now().toString(36)}-${random()}-${random()}`
}
