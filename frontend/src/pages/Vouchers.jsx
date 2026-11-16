import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Ticket } from 'lucide-react'
import BatchDetail from '../components/vouchers/BatchDetail'
import BatchForm from '../components/vouchers/BatchForm'
import voucherService from '../services/voucherService'
import { formatMoney } from '../pos/utils/money'
import { button } from '../components/loyalty/shared'
import { formatExpiry, voucherKeys } from '../components/vouchers/voucherUtils'

export default function Vouchers() {
  const [selected, setSelected] = useState(null)
  const [creating, setCreating] = useState(false)
  const { data: batches = [], isLoading } = useQuery({ queryKey: voucherKeys.batches, queryFn: voucherService.listBatches })

  return (
    <div className="space-y-4 p-4 md:p-6">
      <h1 className="flex items-center gap-2 text-2xl font-bold text-galia-plum"><Ticket /> Vouchers</h1>
      <div className="rounded-xl bg-white p-4 shadow-sm">
        {selected ? (
          <BatchDetail batchId={selected} onBack={() => setSelected(null)} />
        ) : creating ? (
          <BatchForm onCreated={(batch) => { setCreating(false); setSelected(batch.id) }} onCancel={() => setCreating(false)} />
        ) : (
          <div className="space-y-4">
            <button type="button" className={button(true)} onClick={() => setCreating(true)}>Nueva tanda</button>
            {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
            {!isLoading && batches.length === 0 && <p className="text-sm text-gray-500">Todavía no hay tandas.</p>}
            {batches.length > 0 && (
              <table className="w-full text-sm">
                <thead><tr className="text-left text-gray-500">
                  <th className="py-1">Concurso</th><th>Monto</th><th>Vence</th><th>Emitidos</th><th>Disponibles</th><th>Canjeados</th><th>Descuento dado</th>
                </tr></thead>
                <tbody>
                  {batches.map((b) => (
                    <tr key={b.id} className="cursor-pointer border-t hover:bg-gray-50" onClick={() => setSelected(b.id)}>
                      <td className="py-2 font-medium">{b.name}</td>
                      <td>{formatMoney(b.amount)}</td>
                      <td>{formatExpiry(b.expires_at)}</td>
                      <td>{b.issued}</td>
                      <td>{b.available}</td>
                      <td>{b.redeemed + b.in_use}</td>
                      <td>{formatMoney(b.discount_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
