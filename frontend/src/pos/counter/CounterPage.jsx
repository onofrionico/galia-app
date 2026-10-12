import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { useCounterSales } from '../hooks/usePosQueries'
import { useNow } from '../hooks/useNow'
import NewCounterSaleModal from '../modals/NewCounterSaleModal'
import SalePanel from '../sale/SalePanel'
import StatusBadge from '../ui/StatusBadge'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { elapsedLabel } from '../utils/time'

export default function CounterPage() {
  const [params, setParams] = useSearchParams()
  const saleId = Number(params.get('sale')) || null
  const { data: sales = [], isLoading, isError } = useCounterSales()
  const [creating, setCreating] = useState(false)
  const [initialModal, setInitialModal] = useState(null)
  const now = useNow()

  const select = (id, modal = null) => {
    setInitialModal(modal)
    setParams(id ? { sale: String(id) } : {})
  }

  return (
    <div className="flex h-full">
      <div className="min-w-0 flex-1 overflow-auto p-4">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl">Mostrador</h1>
          <button type="button" className={btn('primary')} onClick={() => setCreating(true)}>
            <Plus size={18} /> Nueva venta
          </button>
        </div>
        {isLoading && <p className="text-gray-500">Cargando…</p>}
        {isError && <p className="text-red-700">No se pudieron cargar las ventas.</p>}
        {!isLoading && !isError && sales.length === 0 && <p className="text-gray-500">No hay ventas de mostrador abiertas.</p>}
        <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
          {sales.map((sale) => (
            <button key={sale.id} type="button" onClick={() => select(sale.id)}
              className={`rounded-xl border-2 bg-white p-3 text-left ${sale.id === saleId ? 'border-galia-plum' : 'border-gray-200'}`}>
              <span className="flex items-center justify-between">
                <span className="font-semibold">#{sale.number}</span>
                <StatusBadge status={sale.status} />
              </span>
              <span className="mt-1 block truncate text-gray-700">{sale.customer_name ?? 'Sin nombre'}</span>
              <span className="mt-2 block text-lg font-bold text-galia-plum">{formatMoney(sale.total)}</span>
              <span className="block text-xs text-gray-500">{elapsedLabel(sale.opened_at, now)}</span>
            </button>
          ))}
        </div>
      </div>
      {saleId && (
        <SalePanel key={saleId} saleId={saleId} initialModal={initialModal}
          onSelect={(id) => select(id)} onClose={() => select(null)} onStartMove={() => {}} />
      )}
      {creating && (
        <NewCounterSaleModal onClose={() => setCreating(false)}
          onCreated={(id) => { setCreating(false); select(id, 'add') }} />
      )}
    </div>
  )
}
