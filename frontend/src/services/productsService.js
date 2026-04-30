import api from './api'

const productsService = {
  async getProducts(params = {}) {
    const response = await api.get('/products', { params })
    return response.data
  },

  async getProduct(id) {
    const response = await api.get(`/products/${id}`)
    return response.data
  },

  async createProduct(data) {
    const response = await api.post('/products', data)
    return response.data
  },

  async updateProduct(id, data) {
    const response = await api.put(`/products/${id}`, data)
    return response.data
  },

  async deleteProduct(id) {
    const response = await api.delete(`/products/${id}`)
    return response.data
  },

  async getVariants(productId) {
    const response = await api.get(`/products/${productId}/variants`)
    return response.data
  },

  async createVariant(productId, data) {
    const response = await api.post(`/products/${productId}/variants`, data)
    return response.data
  },

  async updateVariant(productId, variantId, data) {
    const response = await api.put(`/products/${productId}/variants/${variantId}`, data)
    return response.data
  },

  async deleteVariant(productId, variantId) {
    const response = await api.delete(`/products/${productId}/variants/${variantId}`)
    return response.data
  },

  async getRecipe(productId) {
    const response = await api.get(`/products/${productId}/recipe`)
    return response.data
  },

  async saveRecipe(productId, items) {
    const response = await api.put(`/products/${productId}/recipe`, { items })
    return response.data
  },

  async getLowStock() {
    const response = await api.get('/products/low-stock')
    return response.data
  },

  async adjustStock(productId, variantId, stockQuantity) {
    const response = await api.put(
      `/products/${productId}/variants/${variantId}/stock`,
      { stock_quantity: stockQuantity }
    )
    return response.data
  },
}

export default productsService
