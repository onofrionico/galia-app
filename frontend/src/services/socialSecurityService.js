import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const getAuthHeader = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

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

    const response = await axios.post(
      `${API_URL}/api/v1/social-security/upload`,
      formData,
      {
        headers: {
          ...getAuthHeader(),
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

    const response = await axios.get(
      `${API_URL}/api/v1/social-security/employee/${employeeId}?${params.toString()}`,
      { headers: getAuthHeader() }
    )
    return response.data
  },

  getAllDocuments: async (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.employee_id) params.append('employee_id', filters.employee_id)
    if (filters.document_type) params.append('document_type', filters.document_type)
    if (filters.period_year) params.append('period_year', filters.period_year)
    if (filters.period_month) params.append('period_month', filters.period_month)

    const response = await axios.get(
      `${API_URL}/api/v1/social-security/all?${params.toString()}`,
      { headers: getAuthHeader() }
    )
    return response.data
  },

  getDocumentDetail: async (documentId) => {
    const response = await axios.get(
      `${API_URL}/api/v1/social-security/${documentId}`,
      { headers: getAuthHeader() }
    )
    return response.data
  },

  downloadDocument: async (documentId) => {
    const response = await axios.get(
      `${API_URL}/api/v1/social-security/download/${documentId}`,
      {
        headers: getAuthHeader(),
        responseType: 'blob'
      }
    )
    return response
  },

  getDownloadUrl: async (documentId, expiration = 3600) => {
    const response = await axios.get(
      `${API_URL}/api/v1/social-security/download-url/${documentId}?expiration=${expiration}`,
      { headers: getAuthHeader() }
    )
    return response.data
  },

  deleteDocument: async (documentId) => {
    const response = await axios.delete(
      `${API_URL}/api/v1/social-security/${documentId}`,
      { headers: getAuthHeader() }
    )
    return response.data
  },

  getDocumentTypes: async () => {
    const response = await axios.get(
      `${API_URL}/api/v1/social-security/types`,
      { headers: getAuthHeader() }
    )
    return response.data
  }
}

export default socialSecurityService
