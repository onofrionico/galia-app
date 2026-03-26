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
  search: async (query) => {
    const response = await api.get('/suppliers', {
      params: { search: query }
    })
    return response.data
  },

  // Get sales history for a supplier
  getSalesHistory: async (id, params = {}) => {
    const response = await api.get(`/suppliers/${id}/sales-history`, { params })
    return response.data
  },

  // Export supplier data
  exportData: async (id, params = {}) => {
    const response = await api.get(`/suppliers/${id}/export`, {
      params,
      responseType: 'blob'
    })
    return response
  }
}

export default suppliersApi
