import { useCallback, useEffect, useReducer } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { connectivityReducer, initialConnectivity, pollEvent } from '../utils/connectivity'

// Combina los eventos online/offline del navegador con el resultado de cada consulta a /changes.
export function useConnectivity() {
  const [state, dispatch] = useReducer(connectivityReducer, initialConnectivity)
  const queryClient = useQueryClient()

  useEffect(() => {
    const onOffline = () => dispatch('offline')
    const onOnline = () => {
      dispatch('online')
      // Consultar ya, sin esperar al próximo intervalo: la respuesta exitosa reconecta.
      queryClient.refetchQueries({ queryKey: ['pos-changes'] })
    }
    window.addEventListener('offline', onOffline)
    window.addEventListener('online', onOnline)
    if (navigator.onLine === false) dispatch('offline')
    return () => {
      window.removeEventListener('offline', onOffline)
      window.removeEventListener('online', onOnline)
    }
  }, [queryClient])

  const report = useCallback((ok, error) => dispatch(pollEvent(ok, error)), [])
  return { online: state.online, report }
}
