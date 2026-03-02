import api from './api'

export const timeTrackingService = {
  recordCheckIn: async (date) => {
    const response = await api.post('/time-tracking/check-in', { date })
    return response.data
  },

  recordCheckOut: async (date) => {
    const response = await api.post('/time-tracking/check-out', { date })
    return response.data
  },

  getTodayRecord: async () => {
    const response = await api.get('/time-tracking/today')
    return response.data
  },

  getRecords: async (startDate, endDate) => {
    const response = await api.get('/time-tracking/records', {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  },

  getMonthlyRecords: async (year, month) => {
    const response = await api.get('/time-tracking/monthly', {
      params: { year, month }
    })
    return response.data
  },

  recordPastDayHours: async (date, checkInTime, checkOutTime) => {
    const response = await api.post('/time-tracking/record-hours', {
      date,
      check_in: checkInTime,
      check_out: checkOutTime
    })
    return response.data
  },

  adminGetAllRecords: async (filters = {}) => {
    const response = await api.get('/time-tracking/admin/records', {
      params: filters
    })
    return response.data
  },

  adminCreateRecord: async (employeeId, date, checkInTime, checkOutTime) => {
    const response = await api.post(`/time-tracking/admin/record/${employeeId}`, {
      date,
      check_in: checkInTime,
      check_out: checkOutTime
    })
    return response.data
  },

  adminUpdateWorkBlock: async (blockId, startTime, endTime) => {
    const response = await api.put(`/time-tracking/admin/work-block/${blockId}`, {
      start_time: startTime,
      end_time: endTime
    })
    return response.data
  },

  adminDeleteWorkBlock: async (blockId) => {
    const response = await api.delete(`/time-tracking/admin/work-block/${blockId}`)
    return response.data
  }
}
