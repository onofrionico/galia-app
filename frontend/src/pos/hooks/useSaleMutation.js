import { useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '../ui/Toasts'
import { errorMessage, isRetryable } from '../utils/errors'
import { posKeys } from './keys'

// Ejecuta una acción sobre una venta. La respuesta (la venta completa) reemplaza la caché.
// `run` devuelve la venta o null si falló (el error ya se mostró como aviso).
export function useSaleMutation() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: ({ fn }) => fn(),
    onSuccess: async (sale) => {
      if (sale?.id) {
        // Un refetch en vuelo (iniciado antes de la acción) pisaría la venta recién devuelta.
        await queryClient.cancelQueries({ queryKey: posKeys.sale(sale.id) })
        queryClient.setQueryData(posKeys.sale(sale.id), sale)
        queryClient.invalidateQueries({ queryKey: posKeys.events(sale.id) })
      }
      queryClient.invalidateQueries({ queryKey: posKeys.floors })
      queryClient.invalidateQueries({ queryKey: posKeys.sales })
    },
  })

  const run = useCallback(async (saleId, fn, { onError } = {}) => {
    try {
      return await mutateAsync({ fn })
    } catch (error) {
      if (onError?.(error)) return null
      const retry = isRetryable(error)
        ? { label: 'Reintentar', onClick: () => run(saleId, fn, { onError }) }
        : undefined
      toast.error(errorMessage(error), retry)
      if (saleId) queryClient.invalidateQueries({ queryKey: posKeys.sale(saleId) })
      return null
    }
  }, [mutateAsync, queryClient, toast])

  return { run, busy: isPending }
}
