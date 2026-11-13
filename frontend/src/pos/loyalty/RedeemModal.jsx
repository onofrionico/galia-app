import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { posLoyaltyApi } from '../api/posApi'
import { useCatalog } from '../hooks/usePosQueries'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Chip from '../ui/Chip'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { groupHint, selectionError, toggleOption } from '../utils/modifiers'
import { missingFor } from './loyaltyFormat'

// Canje de premios: lo hace solo la caja. El premio entra a la venta en $0 y los recargos se regalan.
export default function RedeemModal({ sale, onClose }) {
  const balance = sale.customer?.balance ?? 0
  const { data: rewards = [] } = useQuery({
    queryKey: ['pos', 'loyalty', 'rewards'], queryFn: posLoyaltyApi.getRewards, staleTime: 60_000,
  })
  const { data: catalog } = useCatalog()
  const { run, busy } = useSaleMutation()
  const [chosen, setChosen] = useState(null)
  const [selected, setSelected] = useState([])

  const product = chosen && (catalog?.products ?? []).find((p) => p.id === chosen.product_id)
  const groups = product?.modifier_groups ?? []
  const error = chosen ? selectionError(groups, selected) : null

  const redeem = async (reward, optionIds) => {
    if (await run(sale.id, () => posLoyaltyApi.addRedemption(sale.id, reward.id, optionIds))) onClose()
  }
  const start = (reward) => {
    const target = (catalog?.products ?? []).find((p) => p.id === reward.product_id)
    if (target && target.modifier_groups.length > 0) {
      setChosen(reward)
      setSelected([])
    } else {
      redeem(reward, [])
    }
  }

  return (
    <Modal title={`Canjear · ${sale.customer?.full_name ?? ''} · ${balance} ☕`} onClose={onClose}>
      {!chosen && (
        <ul className="divide-y">
          {rewards.map((reward) => {
            const missing = missingFor(balance, reward.cost)
            return (
              <li key={reward.id} className="flex items-center justify-between gap-3 py-3">
                <span className={missing ? 'text-gray-400' : ''}>
                  <span className="block font-medium">{reward.name}</span>
                  <span className="text-sm">{reward.cost} ☕{missing ? ` · faltan ${missing}` : ''}</span>
                </span>
                <button type="button" className={btn('primary')} disabled={busy || missing > 0}
                  onClick={() => start(reward)}>Canjear</button>
              </li>
            )
          })}
          {rewards.length === 0 && <li className="py-3 text-sm text-gray-500">No hay premios activos.</li>}
        </ul>
      )}
      {chosen && (
        <div className="space-y-4">
          <p className="font-medium">{chosen.name} · {chosen.cost} ☕ <span className="text-sm text-gray-500">(los agregados van sin cargo)</span></p>
          {groups.map((group) => (
            <fieldset key={group.id}>
              <legend className="text-sm font-medium text-gray-700">
                {group.name} <span className="font-normal text-gray-500">({groupHint(group)})</span>
              </legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {group.options.map((option) => (
                  <Chip key={option.id} active={selected.includes(option.id)}
                    onClick={() => setSelected((current) => toggleOption(group, current, option.id))}>
                    {option.name}
                  </Chip>
                ))}
              </div>
            </fieldset>
          ))}
          {error && <p className="text-sm text-amber-700">{error}</p>}
          <div className="flex justify-between gap-2">
            <button type="button" className={btn('secondary')} onClick={() => setChosen(null)}>Volver</button>
            <button type="button" className={btn('primary')} disabled={busy || Boolean(error)}
              onClick={() => redeem(chosen, selected)}>Confirmar canje</button>
          </div>
        </div>
      )}
    </Modal>
  )
}
