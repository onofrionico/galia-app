import api from '../api'

const productsApi = {
  // Get all products for a supplier
  getBySupplier: async (supplierId, params = {}) => {
    const response = await api.get(`/suppliers/${supplierId}/products`, { params })
    return response.data
  },

  // Get single product by ID
  getById: async (id) => {
    const response = await api.get(`/products/${id}`)
    return response.data
  },

  // Create new product
  create: async (supplierId, productData) => {
    const response = await api.post(`/suppliers/${supplierId}/products`, productData)
    return response.data
  },

  // Update existing product
  update: async (id, productData) => {
    const response = await api.put(`/products/${id}`, productData)
    return response.data
  },

  // Delete/archive product
  delete: async (id) => {
    const response = await api.delete(`/products/${id}`)
    return response.data
  },

  // Search products across all suppliers
  search: async (query, filters = {}) => {
    const response = await api.get('/products/search', {
      params: { q: query, ...filters }
    })
    return response.data
  },

  // Get price history for a product
  getPriceHistory: async (id, params = {}) => {
    const response = await api.get(`/products/${id}/price-history`, { params })
    return response.data
  },

  // Link product to ProductMaster
  linkToMaster: async (productId, productMasterId) => {
    const response = await api.post(`/products/${productId}/link`, {
      product_master_id: productMasterId
    })
    return response.data
  },

  // Unlink product from ProductMaster
  unlinkFromMaster: async (productId) => {
    const response = await api.delete(`/products/${productId}/link`)
    return response.data
  }
}

export default productsApi
