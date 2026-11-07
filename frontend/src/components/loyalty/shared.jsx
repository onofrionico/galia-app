import { useMutation, useQueryClient } from '@tanstack/react-query'
import { errorMessage } from '../../pos/utils/errors'

export const loyaltyKeys = {
  all: ['loyalty-admin'],
  customers: (q) => ['loyalty-admin', 'customers', q],
  customer: (id) => ['loyalty-admin', 'customer', id],
  rewards: ['loyalty-admin', 'rewards'],
  variants: (q) => ['loyalty-admin', 'variants', q],
  settings: ['loyalty-admin', 'settings'],
  changeLog: (entity) => ['loyalty-admin', 'change-log', entity],
  report: (name, range) => ['loyalty-admin', 'report', name, range],
}

export const input = 'min-h-[40px] rounded-lg border border-gray-300 px-3 focus:border-galia-plum focus:outline-none'
export const button = (primary = false) => `inline-flex min-h-[40px] items-center justify-center gap-2 rounded-lg px-4 font-medium disabled:opacity-40 ${
  primary ? 'bg-galia-plum text-galia-cream hover:opacity-90' : 'border border-gray-300 bg-white hover:bg-gray-50'
}`

// Mutación que invalida todo el módulo y devuelve el error como texto.
export function useLoyaltyMutation(fn) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: fn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: loyaltyKeys.all }),
  })
  return { ...mutation, errorText: mutation.error ? errorMessage(mutation.error) : '' }
}

export function ErrorText({ children }) {
  return children ? <p className="mt-2 text-sm text-red-700">{children}</p> : null
}

export const kindLabel = {
  earn: 'Compra', earn_reversal: 'Compra anulada', redeem: 'Canje', redeem_reversal: 'Canje anulado',
  adjustment: 'Ajuste',
}

export const dateTime = (iso) => (iso ? new Date(`${iso}Z`).toLocaleString('es-AR') : '—')
