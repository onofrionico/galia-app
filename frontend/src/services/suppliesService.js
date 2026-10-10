import api from './api'

const suppliesService = {
  async getSupplies(params = {}) {
    const response = await api.get('/supplies', { params })
    return response.data
  },

  async getSupply(id) {
    const response = await api.get(`/supplies/${id}`)
    return response.data
  },

  async createSupply(data) {
    const response = await api.post('/supplies', data)
    return response.data
  },

  async updateSupply(id, data) {
    const response = await api.put(`/supplies/${id}`, data)
    return response.data
  },

  async deleteSupply(id) {
    const response = await api.delete(`/supplies/${id}`)
    return response.data
  },

  async addPrice(supplyId, priceData) {
    const response = await api.post(`/supplies/${supplyId}/prices`, priceData)
    return response.data
  },
}

export default suppliesService
