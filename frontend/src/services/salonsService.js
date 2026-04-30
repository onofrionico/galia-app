import api from './api'

const salonsService = {
  async getSalons(params = {}) {
    const response = await api.get('/salons', { params })
    return response.data
  },

  async getSalon(id) {
    const response = await api.get(`/salons/${id}`)
    return response.data
  },

  async createSalon(data) {
    const response = await api.post('/salons', data)
    return response.data
  },

  async updateSalon(id, data) {
    const response = await api.put(`/salons/${id}`, data)
    return response.data
  },

  async deleteSalon(id) {
    const response = await api.delete(`/salons/${id}`)
    return response.data
  },

  async getMesas(salonId) {
    const response = await api.get(`/salons/${salonId}/mesas`)
    return response.data
  },

  async getMesa(salonId, mesaId) {
    const response = await api.get(`/salons/${salonId}/mesas/${mesaId}`)
    return response.data
  },

  async createMesa(salonId, data) {
    const response = await api.post(`/salons/${salonId}/mesas`, data)
    return response.data
  },

  async updateMesa(salonId, mesaId, data) {
    const response = await api.put(`/salons/${salonId}/mesas/${mesaId}`, data)
    return response.data
  },

  async deleteMesa(salonId, mesaId) {
    const response = await api.delete(`/salons/${salonId}/mesas/${mesaId}`)
    return response.data
  },
}

export default salonsService
