import api from './api'

const suppliersService = {
  async getSuppliers(params = {}) {
    const response = await api.get('/suppliers', { params })
    return response.data
  },

  async getSupplier(id) {
    const response = await api.get(`/suppliers/${id}`)
    return response.data
  },

  async createSupplier(data) {
    const response = await api.post('/suppliers', data)
    return response.data
  },

  async updateSupplier(id, data) {
    const response = await api.put(`/suppliers/${id}`, data)
    return response.data
  },

  async deactivateSupplier(id) {
    const response = await api.delete(`/suppliers/${id}`)
    return response.data
  },

  async getSupplierExpenses(id, params = {}) {
    const response = await api.get(`/suppliers/${id}/expenses`, { params })
    return response.data
  },

  async linkExpenses(id) {
    const response = await api.post(`/suppliers/${id}/link-expenses`)
    return response.data
  },

  async getSupplierAnalytics(id, params = {}) {
    const response = await api.get(`/suppliers/${id}/analytics`, { params })
    return response.data
  },
}

export default suppliersService
