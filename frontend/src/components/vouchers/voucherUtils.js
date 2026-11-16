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

// Al imprimir se oculta la app entera (display:none, para que no sume páginas en blanco) y queda solo
// la hoja de vouchers, que vive en un portal bajo <body>. Los fondos de la marca se fuerzan a imprimir.
export const PRINT_CSS = `
@media screen { #voucher-print-portal { display: none; } }
@media print {
  @page { size: A4; margin: 8mm; }
  #root { display: none !important; }
  #voucher-print-portal { display: block; }
  #voucher-print-portal, #voucher-print-portal * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .voucher-page { break-after: page; }
  .voucher-page:last-child { break-after: auto; }
}`

// Identifica el conjunto de vouchers imprimibles: si cambia (por ejemplo, uno se canjea), hay que regenerar los QR.
export function availableKey(batch) {
  return batch.vouchers.filter((v) => v.status === 'available').map((v) => v.id).join(',')
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
