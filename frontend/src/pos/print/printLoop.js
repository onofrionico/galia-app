export const DEAD_PRINTER_ERROR = 'La impresora no respondió al trabajo anterior'
export const RECONNECT_EVERY_MS = 10_000

// Imprime los trabajos tomados: cada impresora en paralelo, y dentro de cada una en orden.
// Si una impresora falla, el resto de sus trabajos se informa como fallido sin esperar otro timeout
// (el backend los reintenta a los 15 s), así una impresora apagada no frena a las demás.
export function printByPrinter(jobs, printOne, onFail) {
  const groups = new Map()
  for (const job of jobs) {
    if (!groups.has(job.printer.id)) groups.set(job.printer.id, [])
    groups.get(job.printer.id).push(job)
  }
  return Promise.all([...groups.values()].map(async (group) => {
    let dead = false
    for (const job of group) {
      if (dead) {
        await onFail(job, DEAD_PRINTER_ERROR)
        continue
      }
      try {
        await printOne(job)
      } catch (error) {
        dead = true
        await onFail(job, String(error?.message ?? error ?? 'Error de impresión').slice(0, 255))
      }
    }
  }))
}

// QZ Tray puede arrancar después que el navegador o reiniciarse: se reintenta solo, con una espera entre intentos.
export function shouldReconnect({ simulate, ready, lastAttemptAt, now, waitMs = RECONNECT_EVERY_MS }) {
  return !simulate && !ready && now - lastAttemptAt >= waitMs
}

// Una consulta al backend o un envío a QZ colgados (red caída, spooler trabado) dejaban el bucle esperando
// para siempre: nunca más tomaba trabajos hasta recargar la página.
export function withTimeout(promise, ms, message) {
  let timer
  const timeout = new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(message)), ms) })
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer))
}
