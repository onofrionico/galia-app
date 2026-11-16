import { useMutation, useQueryClient } from '@tanstack/react-query'
import { errorMessage } from '../../pos/utils/errors'

export const STATUS_LABEL = {
  available: 'Disponible',
  in_use: 'En uso',
  redeemed: 'Canjeado',
  expired: 'Vencido',
  voided: 'Anulado',
}

export const voucherKeys = {
  all: ['vouchers'],
  batches: ['vouchers', 'batches'],
  batch: (id) => ['vouchers', 'batch', id],
}

// Páginas de `size` elementos: la hoja A4 lleva 8 vouchers.
export function chunk(list, size) {
  const pages = []
  for (let i = 0; i < list.length; i += size) pages.push(list.slice(i, i + size))
  return pages
}

// '2026-12-31' → '31/12/2026'
export function formatExpiry(isoDate) {
  if (!isoDate) return '—'
  const [year, month, day] = isoDate.split('-')
  return `${day}/${month}/${year}`
}

// Mutación que invalida todo el módulo y devuelve el error como texto.
export function useVoucherMutation(fn) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: fn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: voucherKeys.all }),
  })
  return { ...mutation, errorText: mutation.error ? errorMessage(mutation.error) : '' }
}
