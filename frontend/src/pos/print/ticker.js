// Timer del bucle de impresión. Chrome frena los setInterval de una pestaña oculta (hasta una vez por minuto),
// pero no los de un Web Worker dedicado: la página de impresión sigue tomando trabajos aunque la caja use otra pestaña.
const WORKER_SOURCE = 'let id = null; onmessage = (e) => { clearInterval(id); if (e.data > 0) id = setInterval(() => postMessage(0), e.data) }'

export function startTicker(callback, ms) {
  if (typeof Worker !== 'undefined' && typeof Blob !== 'undefined' && typeof URL?.createObjectURL === 'function') {
    try {
      const url = URL.createObjectURL(new Blob([WORKER_SOURCE], { type: 'text/javascript' }))
      const worker = new Worker(url)
      worker.onmessage = () => callback()
      worker.postMessage(ms)
      return () => {
        worker.terminate()
        URL.revokeObjectURL(url)
      }
    } catch {
      // Sin workers (política del navegador): se usa el timer común.
    }
  }
  const id = setInterval(callback, ms)
  return () => clearInterval(id)
}
