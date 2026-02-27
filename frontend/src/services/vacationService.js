import api from './api';

const vacationService = {
  getVacationPeriods: async (filters = {}) => {
    const response = await api.get('/vacation-periods', { params: filters });
    return response.data;
  },

  createVacationPeriod: async (data) => {
    const response = await api.post('/vacation-periods', data);
    return response.data;
  },

  updateVacationPeriod: async (id, data) => {
    const response = await api.put(`/vacation-periods/${id}`, data);
    return response.data;
  },

  deleteVacationPeriod: async (id) => {
    const response = await api.delete(`/vacation-periods/${id}`);
    return response.data;
  },

  checkAvailability: async (employeeId, startDate, endDate) => {
    const response = await api.get(`/vacation-periods/check-availability/${employeeId}`, {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  }
};

export default vacationService;
