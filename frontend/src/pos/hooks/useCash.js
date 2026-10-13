import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { posCashApi } from '../api/posApi'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { posKeys } from './keys'

export const useRegisters = (enabled = true) => useQuery({
  queryKey: posKeys.cashRegisters,
  queryFn: posCashApi.registers,
  enabled,
  refetchInterval: 60_000,
  staleTime: 10_000,
})

// Hoy hay una sola caja: la primera activa.
export function useMainRegister(enabled = true) {
  const query = useRegisters(enabled)
  const register = query.data?.[0] ?? null
  return { register, openSessionId: register?.open_session?.id ?? null, isLoading: query.isLoading, isError: query.isError }
}

export const useCashSession = (id) => useQuery({
  queryKey: posKeys.cashSession(id),
  queryFn: () => posCashApi.session(id),
  enabled: Boolean(id),
  staleTime: 5_000,
})

export const useExpenseCategories = (enabled = true) => useQuery({
  queryKey: posKeys.expenseCategories,
  queryFn: posCashApi.expenseCategories,
  enabled,
  staleTime: 5 * 60_000,
})

// Acción de caja: la sesión devuelta reemplaza la caché; se refrescan cajas e historial.
export function useCashMutation() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: (fn) => fn(),
    onSuccess: (session) => {
      if (session?.id) queryClient.setQueryData(posKeys.cashSession(session.id), session)
      queryClient.invalidateQueries({ queryKey: posKeys.cashRegisters })
      queryClient.invalidateQueries({ queryKey: ['pos', 'cash', 'sessions'] })
    },
  })
  const run = useCallback(async (fn) => {
    try {
      return await mutateAsync(fn)
    } catch (error) {
      toast.error(errorMessage(error))
      return null
    }
  }, [mutateAsync, toast])
  return { run, busy: isPending }
}
