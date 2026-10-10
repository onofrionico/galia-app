import { useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posApi } from '../api/posApi'
import { keysToInvalidate, rememberEventIds, unseenChanges } from '../utils/changes'
import { posKeys } from './keys'

const POLL_MS = 3000

// Consulta /pos/changes cada 3 s con la pestaña visible e invalida solo lo que cambió.
// El backend repite una ventana de eventos ya informados: se recuerdan los ids vistos y solo se
// invalidan las ventas con eventos nuevos. Si falla la red, al reconectar refresca todo el POS.
export function usePosChanges() {
  const queryClient = useQueryClient()
  const lastId = useRef(null)
  const failed = useRef(false)
  const seen = useRef(new Set())

  useQuery({
    queryKey: ['pos-changes'],
    queryFn: async () => {
      try {
        const response = await posApi.getChanges(lastId.current)
        if (failed.current) {
          failed.current = false
          queryClient.invalidateQueries({ queryKey: posKeys.all })
        } else if (lastId.current !== null) {
          keysToInvalidate(unseenChanges(response, seen.current))
            .forEach((queryKey) => queryClient.invalidateQueries({ queryKey }))
        }
        seen.current = rememberEventIds(seen.current, response.event_ids)
        lastId.current = response.last_event_id
        return response.last_event_id
      } catch (error) {
        failed.current = true
        throw error
      }
    },
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: false,
    retry: false,
    staleTime: 0,
    gcTime: 0,
  })
}
