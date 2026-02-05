import api from './api'

export const employeeService = {
  async getEmployees() {
    const response = await api.get('/employees')
    return response.data
  },

  async getEmployee(id) {
    const response = await api.get(`/employees/${id}`)
    return response.data
  },

  async getEmployeeSchedule(id) {
    const response = await api.get(`/employees/${id}/schedule`)
    return response.data
  },
}
