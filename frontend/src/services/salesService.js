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

  async createSale(items, mesaId = null, medioPago = 'Efectivo') {
    const response = await api.post('/sales', {
      items,
      mesa_id: mesaId,
      medio_pago: medioPago,
    })
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
