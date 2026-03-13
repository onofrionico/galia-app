import api from '../api'

const configurableListsApi = {
  // Get configurable list by type
  getByType: async (listType) => {
    const response = await api.get(`/configurable-lists/${listType}`)
    return response.data
  },

  // Create new list item
  create: async (listData) => {
    const response = await api.post('/configurable-lists', listData)
    return response.data
  },

  // Update list item
  update: async (id, listData) => {
    const response = await api.put(`/configurable-lists/${id}`, listData)
    return response.data
  },

  // Deactivate list item (cannot delete if in use)
  deactivate: async (id) => {
    const response = await api.delete(`/configurable-lists/${id}`)
    return response.data
  },

  // Get exchange rates
  getExchangeRates: async (params = {}) => {
    const response = await api.get('/exchange-rates', { params })
    return response.data
  },

  // Create exchange rate
  createExchangeRate: async (rateData) => {
    const response = await api.post('/exchange-rates', rateData)
    return response.data
  }
}

export default configurableListsApi
