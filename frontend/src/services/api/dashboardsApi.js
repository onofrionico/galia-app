import api from '../api'

const dashboardsApi = {
  // Get suppliers dashboard data
  getSuppliersDashboard: async (params = {}) => {
    const response = await api.get('/dashboards/suppliers', { params })
    return response.data
  },

  // Get purchase frequency dashboard data
  getFrequencyDashboard: async (params = {}) => {
    const response = await api.get('/dashboards/frequency', { params })
    return response.data
  },

  // Get price volatility data
  getPriceVolatility: async (params = {}) => {
    const response = await api.get('/products/volatile', { params })
    return response.data
  }
}

export default dashboardsApi
