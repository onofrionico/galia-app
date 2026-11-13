import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import loyaltyService from '../../services/loyaltyService'
import { ErrorText, button, input, loyaltyKeys, useLoyaltyMutation } from './shared'

const EMPTY = { name: '', product_variant_id: '', cost: '' }

export default function RewardsTab() {
  const { data: rewards = [] } = useQuery({ queryKey: loyaltyKeys.rewards, queryFn: loyaltyService.listRewards })
  const { data: variants = [] } = useQuery({ queryKey: loyaltyKeys.variants(''), queryFn: () => loyaltyService.listVariants('') })
  const [form, setForm] = useState(EMPTY)
  const create = useLoyaltyMutation(() => loyaltyService.createReward({
    name: form.name, product_variant_id: Number(form.product_variant_id), cost: Number(form.cost),
  }))
  const update = useLoyaltyMutation(({ id, body }) => loyaltyService.updateReward(id, body))

  return (
    <div className="space-y-4">
      <table className="w-full text-sm">
        <thead><tr className="text-left text-gray-500"><th className="py-1">Premio</th><th>Entrega</th><th>Costo</th><th>Activo</th></tr></thead>
        <tbody>
          {rewards.map((r) => (
            <tr key={r.id} className="border-t">
              <td className="py-2 font-medium">{r.name}</td>
              <td>{r.product_name} · {r.variant_name}</td>
              <td>
                <input className={`${input} w-24`} type="number" min="1" defaultValue={r.cost}
                  onBlur={(e) => { const cost = Number(e.target.value); if (cost !== r.cost) update.mutate({ id: r.id, body: { cost } }) }} />
                {' '}☕
              </td>
              <td>
                <input type="checkbox" checked={r.is_active} aria-label={`Activo ${r.name}`}
                  onChange={(e) => update.mutate({ id: r.id, body: { is_active: e.target.checked } })} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <ErrorText>{update.errorText}</ErrorText>
      <form className="flex flex-wrap gap-2 rounded-lg border p-3"
        onSubmit={(e) => { e.preventDefault(); create.mutate(undefined, { onSuccess: () => setForm(EMPTY) }) }}>
        <input className={input} placeholder="Nombre (ej.: Café gratis)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <select className={input} value={form.product_variant_id} onChange={(e) => setForm({ ...form, product_variant_id: e.target.value })}>
          <option value="">Producto que entrega…</option>
          {variants.map((v) => <option key={v.id} value={v.id}>{v.product_name} · {v.variant_name}</option>)}
        </select>
        <input className={`${input} w-28`} type="number" min="1" placeholder="Cafecitos" value={form.cost} onChange={(e) => setForm({ ...form, cost: e.target.value })} />
        <button type="submit" className={button(true)} disabled={create.isPending}>Agregar premio</button>
        <ErrorText>{create.errorText}</ErrorText>
      </form>
    </div>
  )
}
