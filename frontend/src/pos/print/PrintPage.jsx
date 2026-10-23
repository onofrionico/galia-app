import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useWakeLock } from '@/camarero/hooks/useWakeLock'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { btn } from '../ui/buttons'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { timeLabel } from '../utils/time'
import { readPrintPoint, usePrintAgent, writePrintPoint } from './usePrintAgent'

// Punto de impresión: elige qué impresoras atiende esta PC y muestra el estado. El mismo agente corre en la
// caja (PosLayout), así que con la caja abierta no hace falta tener esta página abierta.
export default function PrintPage() {
  useWakeLock()
  const toast = useToast()
  const [point, setPoint] = useState(readPrintPoint)
  // La simulación no se guarda: al reabrir la página siempre imprime de verdad.
  const [simulate, setSimulate] = useState(false)
  const [preview, setPreview] = useState(null)
  const { active, qzState, connect, log } = usePrintAgent({ point, simulate, onPreview: setPreview })
  const { data: points = [] } = useQuery({ queryKey: posKeys.printPoints, queryFn: posPrintApi.points })
  const printers = points.find((p) => p.name === point)?.printers ?? []

  const choosePoint = (value) => { setPoint(value); writePrintPoint(value) }
  const toggleSimulate = (value) => setSimulate(value)
  // Descarga el .bat que instala el certificado de Galia en QZ Tray (el mismo para todas las PCs).
  const downloadSetup = () => posPrintApi.qzSetup()
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'preparar-impresion-galia.bat'
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    })
    .catch((error) => toast.error(errorMessage(error)))
  const testPrint = (printerId) => posPrintApi.testPrint(printerId)
    .then(() => toast.success('Prueba enviada a la cola'))
    .catch((error) => toast.error(errorMessage(error)))

  return (
    <div className="min-h-screen space-y-4 bg-galia-cream p-6">
      <header className="flex flex-wrap items-center gap-4">
        <h1 className="text-2xl font-semibold text-galia-plum">Impresión</h1>
        <label className="text-sm">Punto de impresión
          <select value={point} onChange={(e) => choosePoint(e.target.value)} className="ml-2 rounded border px-2 py-1">
            <option value="">Elegí uno</option>
            {points.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={simulate} onChange={(e) => toggleSimulate(e.target.checked)} />
          Modo simulación (sin impresoras)
        </label>
        <button type="button" className="ml-auto text-sm underline" onClick={downloadSetup}
          title="Instala el certificado de Galia en QZ Tray para imprimir sin confirmaciones">
          Preparar esta PC
        </button>
        <Link to="/pos" className="text-sm underline">Volver al POS</Link>
      </header>

      {point && !active && (
        <div className="rounded-lg bg-blue-50 p-4 text-blue-900">
          La caja u otra pestaña de este navegador ya está imprimiendo para {point}. Esta página solo muestra el estado.
        </div>
      )}
      {point && active && !simulate && (
        <p className="text-sm text-gray-600">
          Mientras la caja esté abierta en esta PC, imprime sola: no hace falta dejar esta página abierta.
        </p>
      )}
      {active && !simulate && point && qzState !== 'ready' && (
        <div className="space-y-2 rounded-lg bg-amber-50 p-4 text-amber-900">
          <p>
            {qzState === 'connecting' ? 'Conectando con QZ Tray…' : 'QZ Tray no está abierto.'}{' '}
            <button type="button" className="underline" onClick={connect}>Reintentar</button>
          </p>
          <p className="text-sm">¿PC nueva? Es una sola vez:</p>
          <ol className="list-decimal space-y-1 pl-5 text-sm">
            <li>
              Instalá QZ Tray:{' '}
              <a className="underline" href="https://qz.io/download/" target="_blank" rel="noreferrer">descargar</a>.
            </li>
            <li>
              Tocá <button type="button" className="font-semibold underline" onClick={downloadSetup}>Preparar esta PC</button>,
              abrí el archivo descargado y aceptá el permiso de Windows.
            </li>
            <li>Esta página se conecta sola en unos segundos.</li>
          </ol>
        </div>
      )}
      {simulate && (
        <div className="rounded-lg bg-red-50 p-4 font-medium text-red-800">
          Modo simulación: los trabajos se marcan como impresos pero no sale nada por las impresoras.
        </div>
      )}
      {!point && <p className="text-gray-600">Elegí el punto de impresión de esta PC para empezar.</p>}

      {point && (
        <section className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Impresoras de {point}</h2>
          <ul className="mt-2 divide-y">
            {printers.map((printer) => (
              <li key={printer.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                <span>
                  {printer.name} · {printer.connection === 'network' ? `${printer.host}:${printer.port}` : printer.os_name}
                  {' · '}{printer.paper_width} mm{printer.chars_per_line ? ` (${printer.chars_per_line} caracteres)` : ''} · {printer.is_cashier ? 'Caja' : (printer.station_name ?? 'Sin estación')}
                </span>
                <button type="button" className={btn('secondary', 'min-h-[36px]')} onClick={() => testPrint(printer.id)}>
                  Imprimir prueba
                </button>
              </li>
            ))}
            {printers.length === 0 && <li className="py-2 text-sm text-gray-500">Este punto no tiene impresoras activas.</li>}
          </ul>
        </section>
      )}

      {simulate && preview && (
        <section className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Última impresión simulada · {preview.label}</h2>
          <pre className="mt-2 overflow-x-auto rounded bg-gray-900 p-3 font-mono text-sm text-green-200">{preview.text}</pre>
        </section>
      )}

      <section className="rounded-xl bg-white p-4 shadow-sm">
        <h2 className="font-semibold">Registro</h2>
        <ul className="mt-2 space-y-1 text-sm">
          {log.map((entry, i) => (
            <li key={`${entry.at}-${i}`} className={entry.ok ? '' : 'text-red-700'}>
              {timeLabel(entry.at)} · {entry.printer} · {entry.label} · {entry.ok ? 'impreso' : `error: ${entry.error}`}
            </li>
          ))}
          {log.length === 0 && <li className="text-gray-500">Todavía no se imprimió nada.</li>}
        </ul>
      </section>
    </div>
  )
}
