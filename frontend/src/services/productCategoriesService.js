import api from './api'

const productCategoriesService = {
  async getCategories(params = {}) {
    const response = await api.get('/product-categories', { params })
    return response.data
  },

  async getCategory(id) {
    const response = await api.get(`/product-categories/${id}`)
    return response.data
  },

  async createCategory(data) {
    const response = await api.post('/product-categories', data)
    return response.data
  },

  async updateCategory(id, data) {
    const response = await api.put(`/product-categories/${id}`, data)
    return response.data
  },

  async deleteCategory(id) {
    const response = await api.delete(`/product-categories/${id}`)
    return response.data
  },
}

export default productCategoriesService
