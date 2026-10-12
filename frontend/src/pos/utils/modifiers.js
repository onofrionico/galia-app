import { round2 } from './money'

export function toggleOption(group, selected, optionId) {
  const inGroup = group.options.map((o) => o.id)
  const current = selected.filter((id) => inGroup.includes(id))
  if (current.includes(optionId)) return selected.filter((id) => id !== optionId)
  if (group.max_select === 1) return [...selected.filter((id) => !inGroup.includes(id)), optionId]
  if (current.length >= group.max_select) return selected
  return [...selected, optionId]
}

export function selectionError(groups, selected) {
  for (const group of groups) {
    const count = group.options.filter((o) => selected.includes(o.id)).length
    if (count < group.min_select) return `Elegí al menos ${group.min_select} en "${group.name}"`
  }
  return null
}

// Vista previa del importe del renglón; el importe real lo devuelve el backend al agregarlo.
export function linePreview(variant, groups, selected, quantity) {
  const deltas = groups
    .flatMap((g) => g.options)
    .filter((o) => selected.includes(o.id))
    .reduce((sum, o) => sum + Number(o.price_delta), 0)
  return round2((Number(variant.price) + deltas) * quantity)
}

export function groupHint(group) {
  if (group.min_select > 0) {
    const range = group.min_select === group.max_select ? group.min_select : `de ${group.min_select} a ${group.max_select}`
    return `elegí ${range}, obligatorio`
  }
  return `opcional, hasta ${group.max_select}`
}
