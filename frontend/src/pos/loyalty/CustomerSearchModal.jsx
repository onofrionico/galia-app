import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { QrCode } from 'lucide-react'
import { posLoyaltyApi } from '../api/posApi'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import QrScanner from './QrScanner'

function useDebounced(value, ms) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(id)
  }, [value, ms])
  return debounced
}

// Buscador de clientes de la caja. Un lector de QR USB "tipea" el código en el campo: el backend lo resuelve igual.
export default function CustomerSearchModal({ sale, onClose }) {
  const [text, setText] = useState('')
  const [scanning, setScanning] = useState(false)
  const query = useDebounced(text.trim(), 200)
  const { run, busy } = useSaleMutation()
  const { data: results = [], isFetching } = useQuery({
    queryKey: ['pos', 'loyalty', 'search', query],
    queryFn: () => posLoyaltyApi.searchCustomers(query),
    enabled: query.length >= 2,
    staleTime: 10_000,
  })

  const pick = async (customerId) => {
    if (await run(sale.id, () => posLoyaltyApi.setSaleCustomer(sale.id, customerId))) onClose()
  }

  return (
    <Modal title="Cliente con cafecitos" onClose={onClose}
      footer={sale.customer && (
        <button type="button" className={btn('danger', 'w-full')} disabled={busy} onClick={() => pick(null)}>
          Quitar a {sale.customer.full_name} de la venta
        </button>
      )}>
      <div className="flex gap-2">
        <input autoFocus value={text} onChange={(e) => setText(e.target.value)} placeholder="Nombre, mail o teléfono"
          className="min-h-[44px] w-full rounded-lg border border-gray-300 px-3 focus:border-galia-plum focus:outline-none" />
        <button type="button" className={btn(scanning ? 'primary' : 'secondary')} onClick={() => setScanning((s) => !s)}>
          <QrCode size={18} /> QR
        </button>
      </div>
      {scanning && (
        <div className="mt-3">
          <QrScanner onScan={(code) => { setScanning(false); setText(code) }} />
        </div>
      )}
      <ul className="mt-3 divide-y">
        {results.map((c) => (
          <li key={c.id}>
            <button type="button" disabled={busy} onClick={() => pick(c.id)}
              className="flex w-full items-center justify-between gap-3 px-1 py-3 text-left hover:bg-gray-50">
              <span>
                <span className="block font-medium">{c.full_name}</span>
                <span className="block text-sm text-gray-500">
                  {[c.email_masked, c.phone_masked].filter(Boolean).join(' · ')}
                </span>
              </span>
              <span className="whitespace-nowrap font-semibold text-galia-plum">{c.balance} ☕</span>
            </button>
          </li>
        ))}
      </ul>
      {query.length >= 2 && !isFetching && results.length === 0 && (
        <p className="mt-3 text-sm text-gray-500">No hay clientes con “{query}”. Se registran solos desde la carta.</p>
      )}
    </Modal>
  )
}
