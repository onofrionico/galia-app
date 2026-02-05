import api from './api'

export const employeeScheduleService = {
  async getMyWeeklySchedule(startDate = null) {
    const params = {}
    if (startDate) params.start_date = startDate
    
    const response = await api.get('/employee/schedule/my-schedule/weekly', { params })
    return response.data
  },

  async getMyMonthlySchedule(year = null, month = null) {
    const params = {}
    if (year) params.year = year
    if (month) params.month = month
    
    const response = await api.get('/employee/schedule/my-schedule/monthly', { params })
    return response.data
  },

  async getMyUpcomingShifts(days = 30) {
    const response = await api.get('/employee/schedule/my-schedule/upcoming', { 
      params: { days } 
    })
    return response.data
  },

  async getMyCurrentWeek() {
    const response = await api.get('/employee/schedule/my-schedule/current-week')
    return response.data
  },

  async getMyNextWeek() {
    const response = await api.get('/employee/schedule/my-schedule/next-week')
    return response.data
  },

  async getMyScheduleSummary(startDate = null, endDate = null) {
    const params = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    const response = await api.get('/employee/schedule/my-schedule/summary', { params })
    return response.data
  },
}
