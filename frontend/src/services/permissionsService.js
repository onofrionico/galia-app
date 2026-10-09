import api from './api'

const permissionsService = {
  async getMyModules() {
    const response = await api.get('/permissions/modules/my-modules')
    return response.data.modules || []
  },

  async getRolePermissions(role) {
    const response = await api.get(`/permissions/role/${role}`)
    return response.data.permissions || []
  },

  async updateRolePermissions(role, permissions) {
    await api.put(`/permissions/role/${role}`, { permissions })
  },

  async getUserPermissions(userId) {
    const response = await api.get(`/permissions/user/${userId}`)
    return response.data.permissions || []
  },

  async updateUserPermissions(userId, permissions) {
    await api.put(`/permissions/user/${userId}`, { permissions })
  },

  async resetUserPermissions(userId) {
    await api.post(`/permissions/user/${userId}/reset`)
  },
}

export default permissionsService
