import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useWakeLock } from '@/camarero/hooks/useWakeLock'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { btn } from '../ui/buttons'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { timeLabel } from '../utils/time'
import { renderEscPos, renderText } from './escpos'
import { connectQz, printRaw, qzReady } from './qz'
import { jobLabel } from './printStatus'

const POINT_KEY = 'pos.printPoint'
const SIMULATE_KEY = 'pos.printSimulate'
const TICK_MS = 2000

const read = (key) => { try { return localStorage.getItem(key) } catch { return null } }
const write = (key, value) => { try { localStorage.setItem(key, value) } catch { /* sin storage: solo esta sesión */ } }

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    osc.connect(ctx.destination)
    osc.frequency.value = 880
    osc.start()
    osc.stop(ctx.currentTime + 0.25)
  } catch { /* sin audio */ }
}

// Punto de impresión: toma los trabajos de sus impresoras y los imprime con QZ Tray (o los simula).
export default function PrintPage() {
  useWakeLock()
  const toast = useToast()
  const [point, setPoint] = useState(() => read(POINT_KEY) ?? '')
  const [simulate, setSimulate] = useState(() => read(SIMULATE_KEY) === '1')
  const [qzState, setQzState] = useState('idle')
  const [log, setLog] = useState([])
  const [preview, setPreview] = useState(null)
  const busy = useRef(false)
  const { data: points = [] } = useQuery({ queryKey: posKeys.printPoints, queryFn: posPrintApi.points })
  const printers = points.find((p) => p.name === point)?.printers ?? []

  const addLog = useCallback((job, ok, error) => {
    setLog((current) => [{ at: new Date().toISOString(), label: jobLabel(job), printer: job.printer.name, ok, error },
      ...current].slice(0, 50))
  }, [])

  const connect = useCallback(async () => {
    setQzState('connecting')
    try {
      await connectQz()
      setQzState('ready')
    } catch {
      setQzState('error')
    }
  }, [])

  useEffect(() => {
    if (point && !simulate) connect()
  }, [point, simulate, connect])

  const handle = useCallback(async (job) => {
    const width = job.printer.paper_width
    try {
      if (simulate) setPreview({ label: jobLabel(job), text: renderText(job.document, width).join('\n') })
      else await printRaw(job.printer, renderEscPos(job.document, width))
      await posPrintApi.done(job.id)
      addLog(job, true)
    } catch (error) {
      const message = String(error?.message ?? error ?? 'Error de impresión').slice(0, 255)
      addLog(job, false, message)
      beep()
      try { await posPrintApi.failed(job.id, message) } catch { /* el backend lo recupera a los 60 s */ }
    }
  }, [simulate, addLog])

  useEffect(() => {
    if (!point) return undefined
    const tick = async () => {
      if (busy.current || (!simulate && !qzReady())) return
      busy.current = true
      try {
        const jobs = await posPrintApi.claim(point)
        for (const job of jobs) await handle(job)
      } catch {
        // Sin red o backend caído: se reintenta en el próximo ciclo.
      } finally {
        busy.current = false
      }
    }
    const id = setInterval(tick, TICK_MS)
    tick()
    return () => clearInterval(id)
  }, [point, simulate, handle])

  const choosePoint = (value) => { setPoint(value); write(POINT_KEY, value) }
  const toggleSimulate = (value) => { setSimulate(value); write(SIMULATE_KEY, value ? '1' : '0') }
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
        <Link to="/pos" className="ml-auto text-sm underline">Volver al POS</Link>
      </header>

      {!simulate && point && qzState !== 'ready' && (
        <div className="rounded-lg bg-amber-50 p-4 text-amber-900">
          {qzState === 'connecting' ? 'Conectando con QZ Tray…' : 'QZ Tray no está abierto.'}{' '}
          <button type="button" className="underline" onClick={connect}>Reintentar</button>{' · '}
          <a className="underline" href="https://qz.io/download/" target="_blank" rel="noreferrer">Descargar QZ Tray</a>
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
                  {' · '}{printer.paper_width} mm · {printer.is_cashier ? 'Caja' : (printer.station_name ?? 'Sin estación')}
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
