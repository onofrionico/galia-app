import api from '../api'

const productsApi = {
  // Get all products (global listing)
  getAll: async (params = {}) => {
    const response = await api.get('/products', { params })
    return response.data
  },

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
      params: { search: query, ...filters }
    })
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
    const response = await api.post(`/products/${productId}/unlink`)
    return response.data
  },

  // Bulk update products
  bulkUpdate: async (productIds, operation, data) => {
    const response = await api.post('/products/bulk-update', {
      product_ids: productIds,
      operation,
      data
    })
    return response.data
  },

  // Export products to CSV
  exportToCSV: async (params = {}) => {
    const response = await api.get('/products/export', {
      params,
      responseType: 'blob'
    })
    return response
  },

  // Import products from Excel
  importFromExcel: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/products/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // Get price history for a product
  getPriceHistory: async (productId, params = {}) => {
    const response = await api.get(`/products/${productId}/price-history`, { params })
    return response.data
  },

  // Get volatile products
  getVolatileProducts: async (params = {}) => {
    const response = await api.get('/products/volatile', { params })
    return response.data
  },

  // ProductMaster endpoints
  productMasters: {
    getAll: async (params = {}) => {
      const response = await api.get('/products/masters', { params })
      return response.data
    },

    getById: async (id) => {
      const response = await api.get(`/products/masters/${id}`)
      return response.data
    },

    create: async (data) => {
      const response = await api.post('/products/masters', data)
      return response.data
    },

    search: async (query, filters = {}) => {
      const response = await api.get('/products/masters', {
        params: { search: query, ...filters }
      })
      return response.data
    }
  }
}

export default productsApi
