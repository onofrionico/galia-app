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

  importHistory: async (fromMonth = null, force = false) => {
    const params = new URLSearchParams();
    if (fromMonth) params.append('from_month', fromMonth);
    if (force) params.append('force', 'true');
    const response = await api.post(`/fudo/sync/sales/history?${params.toString()}`);
    return response.data;
  },

  importMonths: async () => {
    const response = await api.get('/fudo/import/months');
    return response.data.months;
  },

  syncExpenses: async (startDate, endDate) => {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    const response = await api.post(`/fudo/sync/expenses?${params.toString()}`);
    return response.data;
  },

  getSyncRun: async (runId) => {
    const response = await api.get(`/fudo/sync/runs/${runId}`);
    return response.data;
  },

  getSyncRuns: async (kind = 'expenses', limit = 1) => {
    const response = await api.get('/fudo/sync/runs', { params: { kind, limit } });
    return response.data.runs;
  }
};

export default fudoService;
