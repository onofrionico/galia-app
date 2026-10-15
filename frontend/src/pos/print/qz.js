import qz from 'qz-tray'
import { posPrintApi } from '../api/posApi'

let setupDone = false
let connected = false
let connecting = null

// Firma los pedidos con el certificado del backend: sin certificado, QZ pide permiso en cada impresión.
function setup() {
  if (setupDone) return
  setupDone = true
  qz.security.setCertificatePromise((resolve) => {
    posPrintApi.qzCertificate().then(resolve).catch(() => resolve())
  })
  qz.security.setSignatureAlgorithm('SHA512')
  qz.security.setSignaturePromise((toSign) => (resolve) => {
    posPrintApi.qzSign(toSign).then(resolve).catch(() => resolve())
  })
  qz.websocket.setClosedCallbacks(() => { connected = false })
}

// qz.websocket.isActive() también da true mientras se está conectando: solo se imprime con la conexión hecha.
export const qzReady = () => connected && qz.websocket.isActive()

// Un solo intento a la vez: QZ rechaza un segundo connect mientras el primero no terminó.
export function connectQz() {
  setup()
  if (qzReady()) return Promise.resolve()
  if (!connecting) {
    connecting = qz.websocket.connect({ retries: 1, delay: 1 })
      .then(() => { connected = true })
      .finally(() => { connecting = null })
  }
  return connecting
}

// printer: { connection, host, port, os_name } tal como llega en el trabajo.
export async function printRaw(printer, data) {
  const target = printer.connection === 'network' ? { host: printer.host, port: printer.port } : printer.os_name
  const config = qz.configs.create(target, { encoding: 'CP858' })
  await qz.print(config, [{ type: 'raw', format: 'command', flavor: 'plain', data }])
}
