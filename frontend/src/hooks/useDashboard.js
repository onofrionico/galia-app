import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../services/api/dashboardApi';

export const useDashboard = (params = {}) => {
  return useQuery({
    queryKey: ['dashboard', 'suppliers', params],
    queryFn: () => dashboardApi.getSuppliersDashboard(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useSupplierComparison = (supplierIds, params = {}) => {
  return useQuery(
    ['supplier-comparison', supplierIds, params],
    () => dashboardApi.compareSuppliers(supplierIds, params),
    { enabled: supplierIds && supplierIds.length > 0 }
  );
};

export const usePurchaseFrequency = (params = {}) => {
  return useQuery({
    queryKey: ['purchase-frequency', params],
    queryFn: () => dashboardApi.getPurchaseFrequency(params),
    staleTime: 5 * 60 * 1000,
  });
};

export default useDashboard;
