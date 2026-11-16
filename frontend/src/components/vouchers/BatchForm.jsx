import { useState } from 'react'
import voucherService from '../../services/voucherService'
import { ErrorText, button, input } from '../loyalty/shared'
import { useVoucherMutation } from './voucherUtils'

const EMPTY = { name: '', amount: '', quantity: '', expires_at: '', min_sale_amount: '', terms: '' }

export default function BatchForm({ onCreated, onCancel }) {
  const [form, setForm] = useState(EMPTY)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })
  const create = useVoucherMutation(() => voucherService.createBatch({
    name: form.name,
    amount: form.amount,
    quantity: Number(form.quantity),
    expires_at: form.expires_at,
    min_sale_amount: form.min_sale_amount || null,
    terms: form.terms,
  }))

  const submit = (e) => {
    e.preventDefault()
    create.mutate(undefined, { onSuccess: (batch) => onCreated(batch) })
  }

  return (
    <form onSubmit={submit} className="grid gap-3 rounded-lg border p-4 md:grid-cols-2">
      <label className="flex flex-col gap-1 text-sm md:col-span-2">Nombre del concurso
        <input className={input} value={form.name} onChange={set('name')} maxLength={100} placeholder="Sorteo de Instagram" required />
      </label>
      <label className="flex flex-col gap-1 text-sm">Monto de descuento ($)
        <input className={input} type="number" min="1" step="any" inputMode="decimal" value={form.amount} onChange={set('amount')} required />
      </label>
      <label className="flex flex-col gap-1 text-sm">Cantidad de vouchers
        <input className={input} type="number" min="1" max="500" value={form.quantity} onChange={set('quantity')} required />
      </label>
      <label className="flex flex-col gap-1 text-sm">Vence el
        <input className={input} type="date" value={form.expires_at} onChange={set('expires_at')} required />
      </label>
      <label className="flex flex-col gap-1 text-sm">Consumo mínimo ($, opcional)
        <input className={input} type="number" min="0" step="any" inputMode="decimal" value={form.min_sale_amount} onChange={set('min_sale_amount')} />
      </label>
      <label className="flex flex-col gap-1 text-sm md:col-span-2">Condiciones (se imprimen en el voucher)
        <textarea className={`${input} py-2`} rows={3} value={form.terms} onChange={set('terms')} maxLength={2000}
          placeholder="Válido para consumo en el local. No acumulable." />
      </label>
      <div className="flex items-center gap-2 md:col-span-2">
        <button type="submit" className={button(true)} disabled={create.isPending}>Crear tanda</button>
        <button type="button" className={button()} onClick={onCancel}>Cancelar</button>
      </div>
      <ErrorText>{create.errorText}</ErrorText>
    </form>
  )
}
