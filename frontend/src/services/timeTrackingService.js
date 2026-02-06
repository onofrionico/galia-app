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
  }
}
