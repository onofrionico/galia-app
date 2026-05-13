import api from './api'

const ordersService = {
  async createOrder(data) {
    const response = await api.post('/orders', data)
    return response.data
  },

  async getOrders(params = {}) {
    const response = await api.get('/orders', { params })
    return response.data
  },

  async getOrder(orderId) {
    const response = await api.get(`/orders/${orderId}`)
    return response.data
  },

  async addItem(orderId, data) {
    const response = await api.post(`/orders/${orderId}/items`, data)
    return response.data
  },

  async updateItem(orderId, itemId, data) {
    const response = await api.put(`/orders/${orderId}/items/${itemId}`, data)
    return response.data
  },

  async removeItem(orderId, itemId) {
    const response = await api.delete(`/orders/${orderId}/items/${itemId}`)
    return response.data
  },

  async cobrar(orderId, medioPago = 'Efectivo') {
    const response = await api.post(`/orders/${orderId}/cobrar`, {
      medio_pago: medioPago,
    })
    return response.data
  },

  async cancelOrder(orderId) {
    const response = await api.delete(`/orders/${orderId}`)
    return response.data
  },
}

export default ordersService
