import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import suppliersApi from '../services/api/suppliersApi'

export const useSuppliers = (params = {}) => {
  return useQuery({
    queryKey: ['suppliers', params],
    queryFn: () => suppliersApi.getAll(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useSupplier = (id) => {
  return useQuery({
    queryKey: ['supplier', id],
    queryFn: () => suppliersApi.getById(id),
    enabled: !!id,
  })
}

export const useCreateSupplier = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: suppliersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
    },
  })
}

export const useUpdateSupplier = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }) => suppliersApi.update(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      queryClient.invalidateQueries({ queryKey: ['supplier', variables.id] })
    },
  })
}

export const useDeleteSupplier = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: suppliersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
    },
  })
}

export const useSearchSuppliers = (query, filters = {}) => {
  return useQuery({
    queryKey: ['suppliers', 'search', query, filters],
    queryFn: () => suppliersApi.search(query, filters),
    enabled: !!query,
  })
}
