import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { posKeys } from './keys'

// Mutations de la configuración del POS (salones y mesas): refrescan la configuración y el plano.
export function useConfigMutation(mutationFn) {
  const queryClient = useQueryClient()
  const toast = useToast()
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: posKeys.config })
      queryClient.invalidateQueries({ queryKey: posKeys.floors })
    },
    onError: (error) => toast.error(errorMessage(error)),
  })
}
