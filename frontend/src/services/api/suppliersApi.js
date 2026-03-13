import api from '../api'

const suppliersApi = {
  // Get all suppliers with pagination and filters
  getAll: async (params = {}) => {
    const response = await api.get('/suppliers', { params })
    return response.data
  },

  // Get single supplier by ID
  getById: async (id) => {
    const response = await api.get(`/suppliers/${id}`)
    return response.data
  },

  // Create new supplier
  create: async (supplierData) => {
    const response = await api.post('/suppliers', supplierData)
    return response.data
  },

  // Update existing supplier
  update: async (id, supplierData) => {
    const response = await api.put(`/suppliers/${id}`, supplierData)
    return response.data
  },

  // Delete/archive supplier
  delete: async (id) => {
    const response = await api.delete(`/suppliers/${id}`)
    return response.data
  },

  // Search suppliers
  search: async (query, filters = {}) => {
    const response = await api.get('/suppliers', {
      params: { search: query, ...filters }
    })
    return response.data
  },

  // Get supplier sales history
  getSalesHistory: async (id, params = {}) => {
    const response = await api.get(`/suppliers/${id}/sales-history`, { params })
    return response.data
  },

  // Export supplier data
  export: async (id, format = 'csv') => {
    const response = await api.get(`/suppliers/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
    return response.data
  }
}

export default suppliersApi
