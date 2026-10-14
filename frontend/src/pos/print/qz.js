import qz from 'qz-tray'
import { posPrintApi } from '../api/posApi'

let securityReady = false

// Firma los pedidos con el certificado del backend: sin certificado, QZ pide permiso en cada impresión.
function setupSecurity() {
  if (securityReady) return
  securityReady = true
  qz.security.setCertificatePromise((resolve) => {
    posPrintApi.qzCertificate().then(resolve).catch(() => resolve())
  })
  qz.security.setSignatureAlgorithm('SHA512')
  qz.security.setSignaturePromise((toSign) => (resolve) => {
    posPrintApi.qzSign(toSign).then(resolve).catch(() => resolve())
  })
}

export const qzReady = () => qz.websocket.isActive()

export async function connectQz() {
  setupSecurity()
  if (!qz.websocket.isActive()) await qz.websocket.connect({ retries: 1, delay: 1 })
}

// printer: { connection, host, port, os_name } tal como llega en el trabajo.
export async function printRaw(printer, data) {
  const target = printer.connection === 'network' ? { host: printer.host, port: printer.port } : printer.os_name
  const config = qz.configs.create(target, { encoding: 'CP858' })
  await qz.print(config, [{ type: 'raw', format: 'command', flavor: 'plain', data }])
}
