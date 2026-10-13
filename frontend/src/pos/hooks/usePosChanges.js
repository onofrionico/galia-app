import { useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posApi } from '../api/posApi'
import { cashChanged, keysToInvalidate, rememberEventIds, unseenChanges } from '../utils/changes'
import { posKeys } from './keys'

const POLL_MS = 3000

// Consulta /pos/changes cada 3 s con la pestaña visible e invalida solo lo que cambió.
// El backend repite una ventana de eventos ya informados: se recuerdan los ids vistos y solo se
// invalidan las ventas con eventos nuevos. Si falla la red, al reconectar refresca todo el POS.
// onResult(ok, error): informa cada consulta (el celular lo usa para detectar la falta de conexión).
export function usePosChanges({ onResult } = {}) {
  const queryClient = useQueryClient()
  const lastId = useRef(null)
  const failed = useRef(false)
  const seen = useRef(new Set())
  const cashVersion = useRef(null)
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult

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
        if (cashChanged(cashVersion.current, response.cash_version)) {
          queryClient.invalidateQueries({ queryKey: posKeys.cash })
        }
        if (response.cash_version != null) cashVersion.current = response.cash_version
        seen.current = rememberEventIds(seen.current, response.event_ids)
        lastId.current = response.last_event_id
        onResultRef.current?.(true)
        return response.last_event_id
      } catch (error) {
        failed.current = true
        onResultRef.current?.(false, error)
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
