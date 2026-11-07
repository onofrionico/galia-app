import api from './api'

const recipesService = {
  async list({ q, bases } = {}) {
    const params = {}
    if (q) params.q = q
    if (bases) params.bases = 1
    const response = await api.get('/recipes', { params })
    return response.data
  },

  async supplies() {
    const response = await api.get('/recipes/supplies')
    return response.data
  },

  async get(id) {
    const response = await api.get(`/recipes/${id}`)
    return response.data
  },

  async create(data) {
    const response = await api.post('/recipes', data)
    return response.data
  },

  async update(id, data) {
    const response = await api.put(`/recipes/${id}`, data)
    return response.data
  },

  async remove(id) {
    const response = await api.delete(`/recipes/${id}`)
    return response.data
  },

  async linkProduct(id, data) {
    const response = await api.put(`/recipes/${id}/product`, data)
    return response.data
  },
}

export default recipesService
