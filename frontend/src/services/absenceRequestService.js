import api from './api'

export const absenceRequestService = {
  createRequest: async (formData) => {
    const response = await api.post('/absence-requests/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  getMyRequests: async (params = {}) => {
    const response = await api.get('/absence-requests/my-requests', { params })
    return response.data
  },

  getMyRequestDetail: async (id) => {
    const response = await api.get(`/absence-requests/my-requests/${id}`)
    return response.data
  },

  deleteRequest: async (id) => {
    const response = await api.delete(`/absence-requests/my-requests/${id}`)
    return response.data
  },

  getAllRequests: async (params = {}) => {
    const response = await api.get('/absence-requests/', { params })
    return response.data
  },

  getRequestDetail: async (id) => {
    const response = await api.get(`/absence-requests/${id}`)
    return response.data
  },

  approveRequest: async (id, data) => {
    const response = await api.post(`/absence-requests/${id}/approve`, data)
    return response.data
  },

  rejectRequest: async (id, data) => {
    const response = await api.post(`/absence-requests/${id}/reject`, data)
    return response.data
  },

  downloadAttachment: async (id) => {
    const response = await api.get(`/absence-requests/${id}/attachment`, {
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    const contentDisposition = response.headers['content-disposition']
    let filename = 'comprobante'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  getPendingCount: async () => {
    const response = await api.get('/absence-requests/pending-count')
    return response.data
  }
}
