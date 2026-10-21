import { useQuery } from '@tanstack/react-query'
import cutoverService from '@/services/cutoverService'

export const CUTOVER_KEY = ['cutover']
const OFF = { catalog_in_galia: false, fudo_off: false, practice_mode: false }

// Estado de los interruptores del corte con Fudo (para la franja de práctica y los botones de Fudo).
export function useCutover() {
  const { data } = useQuery({ queryKey: CUTOVER_KEY, queryFn: cutoverService.get, staleTime: 60_000 })
  return data ?? OFF
}
