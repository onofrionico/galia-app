import api from '../api'

const purchasesApi = {
  // Get all purchases with pagination and filters
  getAll: async (params = {}) => {
    const response = await api.get('/purchases', { params })
    return response.data
  },

  // Get single purchase by ID
  getById: async (id) => {
    const response = await api.get(`/purchases/${id}`)
    return response.data
  },

  // Create new purchase
  create: async (purchaseData) => {
    const response = await api.post('/purchases', purchaseData)
    return response.data
  },

  // Update existing purchase
  update: async (id, purchaseData) => {
    const response = await api.put(`/purchases/${id}`, purchaseData)
    return response.data
  },

  // Delete purchase (soft delete with 7-day restriction)
  delete: async (id) => {
    const response = await api.delete(`/purchases/${id}`)
    return response.data
  },

  // Create purchase from existing expense
  createFromExpense: async (expenseId) => {
    const response = await api.get(`/purchases/from-expense/${expenseId}`)
    return response.data
  },

  // Get purchases by supplier
  getBySupplier: async (supplierId, params = {}) => {
    const response = await api.get('/purchases', {
      params: { supplier_id: supplierId, ...params }
    })
    return response.data
  },

  // Update product catalog prices from purchase
  updateProductPrices: async (purchaseId, priceUpdates) => {
    const response = await api.post(`/purchases/${purchaseId}/update-prices`, {
      price_updates: priceUpdates
    })
    return response.data
  }
}

export default purchasesApi
