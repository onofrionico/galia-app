import api from './api';

const fudoService = {
  testConnection: async () => {
    const response = await api.get('/fudo/test-connection');
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get('/fudo/categories');
    return response.data;
  },

  getPaymentMethods: async () => {
    const response = await api.get('/fudo/payment-methods');
    return response.data;
  },

  syncSales: async (startDate, endDate, updateExisting = false) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (updateExisting) params.append('update_existing', 'true');
    
    const response = await api.post(`/fudo/sync/sales?${params.toString()}`);
    return response.data;
  },

  syncExpenses: async (startDate, endDate, categoryMapping, updateExisting = false) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (updateExisting) params.append('update_existing', 'true');
    
    const response = await api.post(`/fudo/sync/expenses?${params.toString()}`, {
      category_mapping: categoryMapping
    });
    return response.data;
  }
};

export default fudoService;
