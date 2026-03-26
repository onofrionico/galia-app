import api from '../api';

export const dashboardApi = {
  getSuppliersDashboard: async (params = {}) => {
    const { period = 'month', currency = 'ARS', start_date, end_date } = params;
    
    const queryParams = new URLSearchParams({
      period,
      currency,
    });
    
    if (start_date) queryParams.append('start_date', start_date);
    if (end_date) queryParams.append('end_date', end_date);
    
    const response = await api.get(`/dashboards/suppliers?${queryParams}`);
    return response.data;
  },

  compareSuppliers: async (supplierIds, params = {}) => {
    const response = await api.get('/dashboards/suppliers/compare', {
      params: {
        supplier_ids: supplierIds.join(','),
        ...params
      }
    });
    return response.data;
  },

  getPurchaseFrequency: async (params = {}) => {
    const response = await api.get('/dashboards/frequency', { params });
    return response.data;
  }
};

export default dashboardApi;
