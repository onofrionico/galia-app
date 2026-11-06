import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import loyaltyService from '../../services/loyaltyService'
import { ErrorText, input, loyaltyKeys, useLoyaltyMutation } from './shared'

// Cafecitos por variante, agrupados por producto. "Todas" aplica el mismo valor a todas las variantes del producto.
export default function VariantsTab() {
  const [q, setQ] = useState('')
  const { data: variants = [] } = useQuery({ queryKey: loyaltyKeys.variants(q), queryFn: () => loyaltyService.listVariants(q) })
  const save = useLoyaltyMutation(({ ids, value }) => loyaltyService.setVariantCafecitos(ids, value))
  const products = useMemo(() => {
    const map = new Map()
    variants.forEach((v) => {
      if (!map.has(v.product_id)) map.set(v.product_id, { id: v.product_id, name: v.product_name, variants: [] })
      map.get(v.product_id).variants.push(v)
    })
    return [...map.values()]
  }, [variants])

  const commit = (ids, raw, current) => {
    const value = Number(raw)
    if (Number.isInteger(value) && value >= 0 && value !== current) save.mutate({ ids, value })
  }

  return (
    <div className="space-y-3">
      <input className={`${input} w-full`} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar producto" />
      <ErrorText>{save.errorText}</ErrorText>
      <ul className="divide-y rounded-lg border">
        {products.map((p) => (
          <li key={p.id} className="px-3 py-2">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{p.name}</span>
              {p.variants.length > 1 && (
                <span className="flex items-center gap-1 text-sm">
                  Todas:
                  <input className={`${input} w-20`} type="number" min="0" placeholder="—" aria-label={`Cafecitos de todas las variantes de ${p.name}`}
                    onKeyDown={(e) => { if (e.key === 'Enter') commit(p.variants.map((v) => v.id), e.target.value, null) }} />
                  <span className="text-gray-500">(Enter)</span>
                </span>
              )}
            </div>
            <div className="mt-1 flex flex-wrap gap-3">
              {p.variants.map((v) => (
                <label key={`${v.id}-${v.cafecitos}`} className="flex items-center gap-1 text-sm">
                  {v.variant_name}
                  <input className={`${input} w-20`} type="number" min="0" defaultValue={v.cafecitos}
                    onBlur={(e) => commit([v.id], e.target.value, v.cafecitos)} /> ☕
                </label>
              ))}
            </div>
          </li>
        ))}
      </ul>
      {save.isPending && <p className="text-sm text-gray-500">Guardando…</p>}
    </div>
  )
}
