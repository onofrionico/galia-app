import api from './api'

const employeeService = {
  async getEmployees(params = {}) {
    const response = await api.get('/employees', { params })
    return response.data
  },

  async getEmployee(id) {
    const response = await api.get(`/employees/${id}`)
    return response.data
  },

  async createEmployee(employeeData) {
    const response = await api.post('/employees', employeeData)
    return response.data
  },

  async updateEmployee(id, employeeData) {
    const response = await api.put(`/employees/${id}`, employeeData)
    return response.data
  },

  async deactivateEmployee(id) {
    const response = await api.patch(`/employees/${id}/deactivate`)
    return response.data
  },

  async changeEmployeeStatus(id, status) {
    const response = await api.patch(`/employees/${id}/change-status`, { status })
    return response.data
  },

  async getEmployeeJobHistory(id) {
    const response = await api.get(`/employees/${id}/job-history`)
    return response.data
  },

  async getEmployeeSchedule(id) {
    const response = await api.get(`/employees/${id}/schedule`)
    return response.data
  },

  async getMyProfile() {
    const response = await api.get('/employees/me')
    return response.data
  },

  async updateMyProfile(profileData) {
    const response = await api.put('/employees/me', profileData)
    return response.data
  },
}

export default employeeService
