import api from './api'

export const notificationService = {
  async getMyNotifications(unreadOnly = false) {
    const params = {}
    if (unreadOnly) params.unread_only = true
    
    const response = await api.get('/notifications', { params })
    return response.data
  },

  async markAsRead(notificationId) {
    const response = await api.put(`/notifications/${notificationId}/read`)
    return response.data
  },

  async markAllAsRead() {
    const response = await api.put('/notifications/mark-all-read')
    return response.data
  },
}
