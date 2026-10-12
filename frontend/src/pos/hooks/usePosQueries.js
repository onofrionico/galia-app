import { useQuery } from '@tanstack/react-query'
import { posApi } from '../api/posApi'
import { posKeys } from './keys'

// Los intervalos son de respaldo: el refresco normal lo dispara usePosChanges.
export const useFloor = (salonId, { enabled = true } = {}) => useQuery({
  queryKey: posKeys.floor(salonId),
  queryFn: () => posApi.getFloor(salonId),
  enabled,
  refetchInterval: 60_000,
  staleTime: 10_000,
})

export const useSale = (id) => useQuery({
  queryKey: posKeys.sale(id),
  queryFn: () => posApi.getSale(id),
  enabled: Boolean(id),
  refetchInterval: 30_000,
  staleTime: 5_000,
})

export const useCounterSales = () => useQuery({
  queryKey: posKeys.counter,
  queryFn: () => posApi.listSales({ type: 'counter' }),
  refetchInterval: 60_000,
  staleTime: 10_000,
})

export const useCatalog = () => useQuery({
  queryKey: posKeys.catalog,
  queryFn: posApi.getCatalog,
  staleTime: 5 * 60_000,
})

export const useSaleEvents = (id) => useQuery({
  queryKey: posKeys.events(id),
  queryFn: () => posApi.getEvents(id),
  enabled: Boolean(id),
})

const LOOKUPS = {
  waiters: posApi.getWaiters,
  'cancel-reasons': posApi.getCancelReasons,
  'payment-methods': posApi.getPaymentMethods,
  'discount-templates': posApi.getDiscountTemplates,
}

export const useLookup = (name, enabled = true) => useQuery({
  queryKey: posKeys.lookup(name),
  queryFn: LOOKUPS[name],
  enabled,
  staleTime: 5 * 60_000,
})
