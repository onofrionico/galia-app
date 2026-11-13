import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import loyaltyService from '../../services/loyaltyService'
import { ErrorText, button, dateTime, input, kindLabel, loyaltyKeys, useLoyaltyMutation } from './shared'

function CustomerDetail({ id, onBack }) {
  const { data: customer } = useQuery({ queryKey: loyaltyKeys.customer(id), queryFn: () => loyaltyService.getCustomer(id) })
  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('Sellos de tarjeta de papel')
  const adjust = useLoyaltyMutation(() => loyaltyService.adjust(id, Number(amount), reason))
  const regenerate = useLoyaltyMutation(() => loyaltyService.regenerateQr(id))
  if (!customer) return <p className="text-gray-500">Cargando…</p>

  return (
    <div className="space-y-4">
      <button type="button" className="text-sm text-galia-plum underline" onClick={onBack}>← Volver a la lista</button>
      <div>
        <h3 className="text-lg font-semibold">{customer.full_name}</h3>
        <p className="text-sm text-gray-600">{[customer.email, customer.phone].filter(Boolean).join(' · ')}</p>
        <p className="mt-1 text-2xl font-bold text-galia-plum">{customer.balance} ☕</p>
        <p className="text-xs text-gray-500">Promociones por mail: {customer.promo_opt_in ? 'sí' : 'no'}</p>
      </div>
      <form className="rounded-lg border p-3" onSubmit={(e) => { e.preventDefault(); adjust.mutate() }}>
        <p className="mb-2 font-medium">Ajustar cafecitos</p>
        <div className="flex flex-wrap gap-2">
          <input className={`${input} w-28`} type="number" step="1" value={amount} placeholder="+6 o −2"
            onChange={(e) => setAmount(e.target.value)} />
          <input className={`${input} min-w-[220px] flex-1`} value={reason} maxLength={255} placeholder="Motivo (obligatorio)"
            onChange={(e) => setReason(e.target.value)} />
          <button type="submit" className={button(true)} disabled={adjust.isPending || !amount || !reason.trim()}>Ajustar</button>
        </div>
        <ErrorText>{adjust.errorText}</ErrorText>
      </form>
      <button type="button" className={button()} disabled={regenerate.isPending}
        onClick={() => { if (window.confirm('El QR actual deja de servir. ¿Generar uno nuevo?')) regenerate.mutate() }}>
        Regenerar QR
      </button>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-gray-500"><th className="py-1">Fecha</th><th>Movimiento</th><th className="text-right">Cafecitos</th></tr></thead>
        <tbody>
          {customer.movements.map((m) => (
            <tr key={m.id} className="border-t">
              <td className="py-1.5">{dateTime(m.created_at)}</td>
              <td>{kindLabel[m.kind]}{m.reward ? ` · ${m.reward}` : ''}{m.reason ? ` · ${m.reason}` : ''}</td>
              <td className={`text-right font-medium ${m.amount < 0 ? 'text-red-700' : 'text-green-700'}`}>
                {m.amount > 0 ? `+${m.amount}` : m.amount}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function CustomersTab() {
  const [q, setQ] = useState('')
  const [selected, setSelected] = useState(null)
  const { data: customers = [], isLoading } = useQuery({
    queryKey: loyaltyKeys.customers(q), queryFn: () => loyaltyService.listCustomers(q),
  })
  if (selected) return <CustomerDetail id={selected} onBack={() => setSelected(null)} />
  return (
    <div className="space-y-3">
      <input className={`${input} w-full`} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar por nombre, mail o teléfono" />
      {isLoading && <p className="text-gray-500">Cargando…</p>}
      <ul className="divide-y rounded-lg border">
        {customers.map((c) => (
          <li key={c.id}>
            <button type="button" className="flex w-full justify-between px-3 py-2 text-left hover:bg-gray-50" onClick={() => setSelected(c.id)}>
              <span><span className="font-medium">{c.full_name}</span> <span className="text-sm text-gray-500">{c.email}</span></span>
              <span className="font-semibold text-galia-plum">{c.balance} ☕</span>
            </button>
          </li>
        ))}
        {!isLoading && customers.length === 0 && <li className="px-3 py-2 text-sm text-gray-500">Sin clientes.</li>}
      </ul>
    </div>
  )
}
