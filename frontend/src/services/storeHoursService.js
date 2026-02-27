import api from './api';

const storeHoursService = {
  async getStoreHours(params = {}) {
    const response = await api.get('/store-hours', { params });
    return response.data;
  },

  async createStoreHours(data) {
    const response = await api.post('/store-hours', data);
    return response.data;
  },

  async updateStoreHours(id, data) {
    const response = await api.put(`/store-hours/${id}`, data);
    return response.data;
  },

  async deleteStoreHours(id) {
    const response = await api.delete(`/store-hours/${id}`);
    return response.data;
  },

  async getLocations() {
    const response = await api.get('/store-hours/locations');
    return response.data;
  }
};

export default storeHoursService;
