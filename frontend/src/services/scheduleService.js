import api from './api'

export const scheduleService = {
  async getSchedules() {
    const response = await api.get('/schedules')
    return response.data
  },

  async getSchedule(id) {
    const response = await api.get(`/schedules/${id}`)
    return response.data
  },

  async createSchedule(data) {
    const response = await api.post('/schedules', data)
    return response.data
  },

  async updateSchedule(id, data) {
    const response = await api.put(`/schedules/${id}`, data)
    return response.data
  },

  async deleteSchedule(id) {
    const response = await api.delete(`/schedules/${id}`)
    return response.data
  },

  async publishSchedule(id) {
    const response = await api.post(`/schedules/${id}/publish`)
    return response.data
  },

  async getScheduleSummary(id) {
    const response = await api.get(`/schedules/${id}/summary`)
    return response.data
  },

  async createShift(data) {
    const response = await api.post('/shifts', data)
    return response.data
  },

  async updateShift(id, data) {
    const response = await api.put(`/shifts/${id}`, data)
    return response.data
  },

  async deleteShift(id) {
    const response = await api.delete(`/shifts/${id}`)
    return response.data
  },

  async getEmployeeShifts(employeeId, startDate, endDate) {
    const params = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    const response = await api.get(`/shifts/employee/${employeeId}`, { params })
    return response.data
  },
}
