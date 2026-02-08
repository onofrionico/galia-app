import api from './api';

const payrollService = {
  calculatePayroll: async (employeeId, year, month) => {
    const response = await api.get(`/payroll/calculate/${employeeId}/${year}/${month}`);
    return response.data;
  },

  generatePayroll: async (data) => {
    const response = await api.post('/payroll/generate', data);
    return response.data;
  },

  getPayrolls: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.month) params.append('month', filters.month);
    if (filters.year) params.append('year', filters.year);
    if (filters.employee_id) params.append('employee_id', filters.employee_id);
    if (filters.status) params.append('status', filters.status);
    
    const response = await api.get(`/payroll/?${params.toString()}`);
    return response.data;
  },

  getPayrollDetail: async (payrollId) => {
    const response = await api.get(`/payroll/${payrollId}`);
    return response.data;
  },

  updatePayroll: async (payrollId, data) => {
    const response = await api.put(`/payroll/${payrollId}`, data);
    return response.data;
  },

  validatePayroll: async (payrollId) => {
    const response = await api.post(`/payroll/${payrollId}/validate`);
    return response.data;
  },

  getWorkBlocks: async (payrollId) => {
    const response = await api.get(`/payroll/${payrollId}/work-blocks`);
    return response.data;
  },

  updateWorkBlock: async (blockId, data) => {
    const response = await api.put(`/payroll/work-blocks/${blockId}`, data);
    return response.data;
  },

  deleteWorkBlock: async (blockId) => {
    const response = await api.delete(`/payroll/work-blocks/${blockId}`);
    return response.data;
  },

  getMonthlySummary: async (year, month) => {
    const response = await api.get(`/payroll/summary/${year}/${month}`);
    return response.data;
  },

  getHistoricalSummary: async (months = 12) => {
    const response = await api.get(`/payroll/summary/historical?months=${months}`);
    return response.data;
  },

  generatePDF: async (payrollId) => {
    const response = await api.post(`/payroll/${payrollId}/generate-pdf`, {}, {
      responseType: 'blob'
    });
    return response.data;
  },

  downloadPDF: async (payrollId) => {
    const response = await api.get(`/payroll/${payrollId}/pdf`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Employee endpoints
  async getMyPayrolls(params = {}) {
    const response = await api.get('/payroll/my-payrolls', { params });
    return response.data;
  },

  async getMyPayrollDetail(payrollId) {
    const response = await api.get(`/payroll/my-payrolls/${payrollId}`);
    return response.data;
  },

  async validateMyPayroll(payrollId) {
    const response = await api.post(`/payroll/my-payrolls/${payrollId}/validate`);
    return response.data;
  },

  async downloadMyPayrollPDF(payrollId) {
    const response = await api.get(`/payroll/my-payrolls/${payrollId}/pdf`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

export default payrollService;
