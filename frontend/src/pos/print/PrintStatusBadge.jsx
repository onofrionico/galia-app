import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Printer } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { elapsedLabel } from '../utils/time'
import { jobLabel, printHealth } from './printStatus'

// La cola se mide en segundos: "hace 0 min" se lee como un error.
const ago = (iso) => {
  const label = elapsedLabel(iso)
  return label === '0 min' ? 'menos de 1 min' : label
}

const TONES = {
  alert: 'bg-red-600 text-white',
  busy: 'bg-amber-200 text-amber-900',
  ok: 'bg-white/15 text-galia-cream',
  unknown: 'bg-white/15 text-galia-cream',
}

// Indicador de impresión de la caja: rojo si hay trabajos con problemas o un punto de impresión sin señal.
export default function PrintStatusBadge() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const toast = useToast()
  const { data: status } = useQuery({ queryKey: posKeys.printStatus, queryFn: posPrintApi.status, refetchInterval: 15_000 })
  const action = useMutation({
    mutationFn: ({ fn, id }) => fn(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: posKeys.print }),
    onError: (error) => toast.error(errorMessage(error)),
  })
  const health = printHealth(status)
  const problems = status?.problems ?? []
  const points = status?.points ?? []

  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open}
        className={`flex min-h-[40px] items-center gap-1 rounded-full px-3 text-xs font-medium ${TONES[health]}`}>
        <Printer size={14} /> Impresión{problems.length ? ` · ${problems.length}` : ''}
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-96 max-w-[90vw] rounded-xl bg-white p-3 text-sm text-gray-800 shadow-xl">
          <p className="font-semibold">Puntos de impresión</p>
          <ul className="mb-2">
            {points.map((p) => (
              <li key={p.name} className={p.down ? 'text-red-700' : 'text-green-700'}>
                {p.name} · {p.down ? (p.last_seen_at ? `sin señal hace ${ago(p.last_seen_at)}` : 'nunca se conectó') : 'conectado'}
              </li>
            ))}
            {points.length === 0 && <li className="text-gray-500">No hay impresoras configuradas.</li>}
          </ul>
          <p className="font-semibold">Con problemas</p>
          <ul className="divide-y">
            {problems.map((job) => (
              <li key={job.id} className="py-2">
                <p>{jobLabel(job)} · hace {ago(job.created_at)}{job.error ? ` · ${job.error}` : ''}</p>
                <div className="mt-1 flex gap-3">
                  <button type="button" className="text-galia-plum underline" disabled={action.isPending}
                    onClick={() => action.mutate({ fn: posPrintApi.retry, id: job.id })}>Reintentar</button>
                  <button type="button" className="text-galia-plum underline" disabled={action.isPending}
                    onClick={() => action.mutate({ fn: posPrintApi.markPrinted, id: job.id })}>Marcar como impresa</button>
                </div>
              </li>
            ))}
            {problems.length === 0 && <li className="py-2 text-gray-500">Todo impreso.</li>}
          </ul>
          <Link to="/pos/impresion" className="mt-2 block text-right text-galia-plum underline">Abrir la página de impresión</Link>
        </div>
      )}
    </div>
  )
}
