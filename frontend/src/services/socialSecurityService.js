import api from './api'

const socialSecurityService = {
  uploadDocument: async (employeeId, documentType, periodMonth, periodYear, file, notes = '') => {
    const formData = new FormData()
    formData.append('employee_id', employeeId)
    formData.append('document_type', documentType)
    formData.append('period_month', periodMonth)
    formData.append('period_year', periodYear)
    formData.append('file', file)
    if (notes) {
      formData.append('notes', notes)
    }

    const response = await api.post(
      '/social-security/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  getEmployeeDocuments: async (employeeId, filters = {}) => {
    const params = new URLSearchParams()
    if (filters.document_type) params.append('document_type', filters.document_type)
    if (filters.period_year) params.append('period_year', filters.period_year)
    if (filters.period_month) params.append('period_month', filters.period_month)

    const response = await api.get(
      `/social-security/employee/${employeeId}?${params.toString()}`
    )
    return response.data
  },

  getAllDocuments: async (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.employee_id) params.append('employee_id', filters.employee_id)
    if (filters.document_type) params.append('document_type', filters.document_type)
    if (filters.period_year) params.append('period_year', filters.period_year)
    if (filters.period_month) params.append('period_month', filters.period_month)

    const response = await api.get(
      `/social-security/all?${params.toString()}`
    )
    return response.data
  },

  getDocumentDetail: async (documentId) => {
    const response = await api.get(
      `/social-security/${documentId}`
    )
    return response.data
  },

  downloadDocument: async (documentId) => {
    const response = await api.get(
      `/social-security/download/${documentId}`,
      {
        responseType: 'blob'
      }
    )
    return response
  },

  getDownloadUrl: async (documentId, expiration = 3600) => {
    const response = await api.get(
      `/social-security/download-url/${documentId}?expiration=${expiration}`
    )
    return response.data
  },

  deleteDocument: async (documentId) => {
    const response = await api.delete(
      `/social-security/${documentId}`
    )
    return response.data
  },

  getDocumentTypes: async () => {
    const response = await api.get(
      '/social-security/types'
    )
    return response.data
  }
}

export default socialSecurityService
