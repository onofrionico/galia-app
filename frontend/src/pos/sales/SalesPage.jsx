import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useDaySales, useInProgressSales } from '../hooks/usePosQueries'
import SalePanel from '../sale/SalePanel'
import StatusBadge from '../ui/StatusBadge'
import { useToast } from '../ui/Toasts'
import { btn } from '../ui/buttons'
import { argentinaToday, daySummary, isToday, shiftDay } from '../utils/daySales'
import { formatMoney } from '../utils/money'
import { timeLabel } from '../utils/time'

const place = (sale) => (sale.table ? `${sale.table.label} - ${sale.table.salon_name}` : `Mostrador #${sale.number}`)

const moment = (sale) => {
  if (sale.status === 'closed') return sale.closed_at
  if (sale.status === 'cancelled') return sale.cancelled_at
  return sale.opened_at
}

function SaleRow({ sale, selected, onSelect }) {
  return (
    <button type="button" onClick={() => onSelect(sale.id)}
      className={`flex w-full flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border-2 bg-white px-3 py-2 text-left ${
        selected ? 'border-galia-plum' : 'border-gray-200'}`}>
      <span className="min-w-[140px] font-medium">{place(sale)}</span>
      <StatusBadge status={sale.status} />
      <span className="text-sm text-gray-600">#{sale.number}</span>
      <span className="text-sm text-gray-600">{sale.waiter?.name ?? '—'}</span>
      <span className="text-sm text-gray-600">{timeLabel(moment(sale))}</span>
      <span className={`ml-auto font-semibold ${sale.status === 'cancelled' ? 'text-gray-400 line-through' : 'text-galia-plum'}`}>
        {formatMoney(sale.total)}
      </span>
    </button>
  )
}

function Section({ query, empty, selectedId, onSelect }) {
  if (query.isLoading) return <p className="text-gray-500">Cargando…</p>
  if (query.isError) return <p className="text-red-700">No se pudieron cargar las ventas.</p>
  if (query.data.length === 0) return <p className="text-gray-500">{empty}</p>
  return (
    <div className="space-y-2">
      {query.data.map((sale) => <SaleRow key={sale.id} sale={sale} selected={sale.id === selectedId} onSelect={onSelect} />)}
    </div>
  )
}

export default function SalesPage() {
  const [params, setParams] = useSearchParams()
  const saleId = Number(params.get('sale')) || null
  const navigate = useNavigate()
  const toast = useToast()
  const [view, setView] = useState('in-progress')
  const [day, setDay] = useState(() => argentinaToday())
  const inProgress = useInProgressSales()
  const daySales = useDaySales(day)

  const select = (id) => setParams(id ? { sale: String(id) } : {})
  const selected = [...(inProgress.data ?? []), ...(daySales.data ?? [])].find((sale) => sale.id === saleId)
  const summary = daySummary(daySales.data ?? [])

  // Mover de mesa necesita el plano: se abre la venta en su salón y se elige ahí la mesa libre.
  const startMove = () => {
    if (!selected?.table) return
    toast.info('Tocá "Mover de mesa" para elegir la mesa libre')
    navigate(`/pos/salon/${selected.table.salon_id}?sale=${selected.id}`)
  }

  const tabClass = (active) =>
    `rounded-lg px-4 py-2 font-medium ${active ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100 text-gray-700'}`

  return (
    <div className="flex h-full">
      <div className="min-w-0 flex-1 overflow-auto p-4">
        <h1 className="mb-3 text-2xl">Ventas</h1>
        <div className="mb-4 flex gap-2" role="tablist" aria-label="Vista de ventas">
          <button type="button" role="tab" aria-selected={view === 'in-progress'} className={tabClass(view === 'in-progress')}
            onClick={() => setView('in-progress')}>
            En curso{inProgress.data ? ` (${inProgress.data.length})` : ''}
          </button>
          <button type="button" role="tab" aria-selected={view === 'day'} className={tabClass(view === 'day')}
            onClick={() => setView('day')}>Del día</button>
        </div>

        {view === 'in-progress' ? (
          <Section query={inProgress} empty="No hay ventas en curso." selectedId={saleId} onSelect={select} />
        ) : (
          <>
            <div className="mb-3 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1">
                <button type="button" className={btn('secondary', 'w-11 px-0')} aria-label="Día anterior"
                  onClick={() => setDay((d) => shiftDay(d, -1))}><ChevronLeft size={18} /></button>
                <input type="date" value={day} max={argentinaToday()} aria-label="Día"
                  onChange={(event) => event.target.value && setDay(event.target.value)}
                  className="min-h-[44px] rounded-lg border border-gray-300 px-3" />
                <button type="button" className={btn('secondary', 'w-11 px-0')} aria-label="Día siguiente"
                  disabled={isToday(day)} onClick={() => setDay((d) => shiftDay(d, 1))}><ChevronRight size={18} /></button>
                {!isToday(day) && (
                  <button type="button" className={btn('ghost')} onClick={() => setDay(argentinaToday())}>Hoy</button>
                )}
              </div>
              <p className="text-sm text-gray-700">
                {summary.closed} cerradas · cobrado <span className="font-semibold">{formatMoney(summary.total)}</span>
                {summary.cancelled > 0 && ` · ${summary.cancelled} anuladas`}
              </p>
            </div>
            <Section query={daySales} empty="No hay ventas cerradas ese día." selectedId={saleId} onSelect={select} />
          </>
        )}
      </div>
      {saleId && (
        <SalePanel key={saleId} saleId={saleId} onSelect={select} onClose={() => select(null)} onStartMove={startMove} />
      )}
    </div>
  )
}
