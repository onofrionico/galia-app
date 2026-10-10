// Mensaje para mostrar a partir de un error de axios. El backend del POS responde {error: "..."} en castellano.
export function errorMessage(error) {
  const status = error?.response?.status
  const message = error?.response?.data?.error
  if (!error?.response) return 'Sin conexión con el servidor. Probá de nuevo.'
  if (status === 403) return message ? `No tenés permiso para esta acción: ${message}` : 'No tenés permiso para esta acción'
  if (status < 500 && message) return message
  return 'Error interno, probá de nuevo'
}

export const isRetryable = (error) => !error?.response || error.response.status >= 500

// Si abrir una mesa choca con otra venta, el backend devuelve 409 con el id de esa venta.
export const conflictSaleId = (error) =>
  error?.response?.status === 409 ? error.response.data?.sale_id ?? null : null
