import api from './api'

const menuService = {
  async getMenu() {
    return (await api.get('/menu')).data
  },

  async updateCategory(id, data) {
    return (await api.put(`/menu/categories/${id}`, data)).data
  },

  async deleteCategory(id) {
    return (await api.delete(`/menu/categories/${id}`)).data
  },

  async reorderCategories(groupId, ids) {
    return (await api.put('/menu/categories/reorder', { group_id: groupId, ids })).data
  },

  async createGroup(data) {
    return (await api.post('/menu/groups', data)).data
  },

  async updateGroup(id, data) {
    return (await api.put(`/menu/groups/${id}`, data)).data
  },

  async deleteGroup(id) {
    return (await api.delete(`/menu/groups/${id}`)).data
  },

  async reorderGroups(ids) {
    return (await api.put('/menu/groups/reorder', { ids })).data
  },

  async mergeItem(targetId, sourceId) {
    return (await api.post(`/menu/items/${targetId}/merge`, { source_item_id: sourceId })).data
  },

  async ignoreItem(id) {
    return (await api.post(`/menu/items/${id}/ignore`)).data
  },

  async createItem(data) {
    return (await api.post('/menu/items', data)).data
  },

  async updateItem(id, data) {
    return (await api.put(`/menu/items/${id}`, data)).data
  },

  async deleteItem(id) {
    return (await api.delete(`/menu/items/${id}`)).data
  },

  async reorderItems(categoryId, ids) {
    return (await api.put(`/menu/categories/${categoryId}/items/reorder`, { ids })).data
  },

  async uploadItemImage(id, file) {
    const formData = new FormData()
    formData.append('image', file)
    const response = await api.post(`/menu/items/${id}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async deleteItemImage(id) {
    return (await api.delete(`/menu/items/${id}/image`)).data
  },

  async createTag(data) {
    return (await api.post('/menu/tags', data)).data
  },

  async updateTag(id, data) {
    return (await api.put(`/menu/tags/${id}`, data)).data
  },

  async deleteTag(id) {
    return (await api.delete(`/menu/tags/${id}`)).data
  },

  async getSettings() {
    return (await api.get('/menu/settings')).data
  },

  async updateSettings(data) {
    return (await api.put('/menu/settings', data)).data
  },

  async getFudoProducts(params = {}) {
    return (await api.get('/menu/fudo-products', { params })).data
  },

  async getInbox() {
    return (await api.get('/menu/inbox')).data
  },

  async syncFudo() {
    return (await api.post('/menu/sync')).data
  },

  async publish() {
    return (await api.post('/menu/publish')).data
  },
}

export default menuService
