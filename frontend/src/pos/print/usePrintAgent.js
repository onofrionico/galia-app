import { useCallback, useEffect, useRef, useState } from 'react'
import { posPrintApi } from '../api/posApi'
import { renderEscPos, renderText } from './escpos'
import { connectQz, printRaw, qzReady } from './qz'
import { printByPrinter, shouldReconnect, withTimeout } from './printLoop'
import { jobLabel } from './printStatus'
import { startTicker } from './ticker'

export const POINT_KEY = 'pos.printPoint'
const TICK_MS = 1000
const CLAIM_TIMEOUT_MS = 10_000
const PRINT_TIMEOUT_MS = 20_000
// Un solo agente por navegador: si la caja y la página de impresión (o dos pestañas) están abiertas,
// imprime una y las demás esperan; al cerrarse esa pestaña toma la posta otra.
const LOCK_NAME = 'galia-print-agent'

export const readPrintPoint = () => { try { return localStorage.getItem(POINT_KEY) ?? '' } catch { return '' } }
export const writePrintPoint = (value) => {
  try { localStorage.setItem(POINT_KEY, value) } catch { /* sin storage: solo esta sesión */ }
}

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

// Espera el candado del agente (Web Locks). Sin soporte, cada pestaña imprime por su cuenta
// (el backend igual reparte cada trabajo a una sola).
function useAgentLock(enabled) {
  const [held, setHeld] = useState(false)
  useEffect(() => {
    if (!enabled) return undefined
    if (!navigator.locks?.request) {
      setHeld(true)
      return () => setHeld(false)
    }
    const controller = new AbortController()
    let release
    navigator.locks.request(LOCK_NAME, { signal: controller.signal }, () => {
      setHeld(true)
      return new Promise((resolve) => { release = resolve })
    }).catch(() => { /* abortado al desmontar */ })
    return () => {
      controller.abort()
      release?.()
      setHeld(false)
    }
  }, [enabled])
  return held
}

// Toma los trabajos del punto de impresión y los imprime con QZ Tray (o los simula).
export function usePrintAgent({ point, simulate = false, onPreview }) {
  const active = useAgentLock(Boolean(point))
  const [qzState, setQzState] = useState('idle')
  const [log, setLog] = useState([])
  const busy = useRef(false)
  const lastAttempt = useRef(0)

  const addLog = useCallback((job, ok, error) => {
    setLog((current) => [{ at: new Date().toISOString(), label: jobLabel(job), printer: job.printer.name, ok, error },
      ...current].slice(0, 50))
  }, [])

  const connect = useCallback(async () => {
    lastAttempt.current = Date.now()
    setQzState('connecting')
    try {
      await connectQz()
      setQzState('ready')
    } catch {
      setQzState('error')
    }
  }, [])

  useEffect(() => {
    if (active && !simulate) connect()
  }, [active, simulate, connect])

  const printOne = useCallback(async (job) => {
    const { paper_width: width, chars_per_line: chars } = job.printer
    if (simulate) onPreview?.({ label: jobLabel(job), text: renderText(job.document, width, chars).join('\n') })
    else {
      await withTimeout(printRaw(job.printer, renderEscPos(job.document, width, chars)), PRINT_TIMEOUT_MS,
        'La impresora no respondió a tiempo')
    }
    addLog(job, true)
    // Si avisar falla, el backend lo devuelve a la cola a los 60 s.
    await posPrintApi.done(job.id).catch(() => {})
  }, [simulate, onPreview, addLog])

  const onFail = useCallback(async (job, message) => {
    addLog(job, false, message)
    beep()
    try { await posPrintApi.failed(job.id, message) } catch { /* el backend lo recupera a los 60 s */ }
  }, [addLog])

  useEffect(() => {
    if (!active || !point) return undefined
    const tick = async () => {
      if (busy.current) return
      if (!simulate && !qzReady()) {
        // QZ Tray se cerró o todavía no arrancó (por ejemplo al prender la PC): aviso y reintento solo.
        setQzState((state) => (state === 'ready' ? 'error' : state))
        if (shouldReconnect({ simulate, ready: false, lastAttemptAt: lastAttempt.current, now: Date.now() })) connect()
        return
      }
      busy.current = true
      try {
        const jobs = await withTimeout(posPrintApi.claim(point), CLAIM_TIMEOUT_MS, 'Sin respuesta del servidor')
        await printByPrinter(jobs, printOne, onFail)
      } catch {
        // Sin red o backend caído: se reintenta en el próximo ciclo.
      } finally {
        busy.current = false
      }
    }
    const stop = startTicker(tick, TICK_MS)
    tick()
    return stop
  }, [active, point, simulate, printOne, onFail, connect])

  return { active, qzState, connect, log }
}
