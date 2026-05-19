import api from './api'

const salesService = {
  async getSales(params = {}) {
    const response = await api.get('/sales', { params })
    return response.data
  },

  async getSale(id) {
    const response = await api.get(`/sales/${id}`)
    return response.data
  },

  async createSale(data) {
    const response = await api.post('/sales', data)
    return response.data
  },

  async updateSale(id, data) {
    const response = await api.put(`/sales/${id}`, data)
    return response.data
  },

  async addItemToSale(saleId, data) {
    // This endpoint would need to be implemented in the backend
    // For now, we'll use a generic add item approach
    const response = await api.post(`/sales/${saleId}/items`, data)
    return response.data
  },

  async registerPayment(saleId, data) {
    const response = await api.post(`/sales/${saleId}/payments`, data)
    return response.data
  },

  async closeSale(saleId) {
    const response = await api.post(`/sales/${saleId}/close`)
    return response.data
  },

  async getDailySummary() {
    const response = await api.get('/sales/daily-summary')
    return response.data
  },

  async getTopProducts(params = {}) {
    const response = await api.get('/sales/top-products', { params })
    return response.data
  },
}

export default salesService
