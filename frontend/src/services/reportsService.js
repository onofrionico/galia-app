import api from './api'

export const reportsService = {
  getDashboard: async (period = 'mensual', date = null, startDate = null, endDate = null) => {
    const params = {}
    
    // Prioridad: rango de fechas > período
    if (startDate && endDate) {
      params.start_date = startDate
      params.end_date = endDate
    } else {
      params.period = period || 'mensual'
      if (date) params.date = date
    }
    
    const response = await api.get('/reports/dashboard', { params })
    return response.data
  },

  getGoals: async () => {
    const response = await api.get('/reports/goals')
    return response.data
  },

  createGoal: async (goalData) => {
    const response = await api.post('/reports/goals', goalData)
    return response.data
  },

  updateGoal: async (goalId, goalData) => {
    const response = await api.put(`/reports/goals/${goalId}`, goalData)
    return response.data
  },

  deleteGoal: async (goalId) => {
    const response = await api.delete(`/reports/goals/${goalId}`)
    return response.data
  },

  getSalesReport: async (params = {}) => {
    const response = await api.get('/reports/sales', { params })
    return response.data
  },

  getSalesByEmployee: async (params = {}) => {
    const response = await api.get('/reports/sales/by-employee', { params })
    return response.data
  },

  getSalesEvolution: async (params = {}) => {
    const response = await api.get('/reports/sales/evolution', { params })
    return response.data
  },

  getExpensesReport: async (params = {}) => {
    const response = await api.get('/reports/expenses', { params })
    return response.data
  },

  getExpensesEvolution: async (params = {}) => {
    const response = await api.get('/reports/expenses/evolution', { params })
    return response.data
  },

  getBalanceReport: async (params = {}) => {
    const response = await api.get('/reports/balance', { params })
    return response.data
  },

  getProductivityReport: async (params = {}) => {
    const response = await api.get('/reports/productivity', { params })
    return response.data
  },

  getExpenseCategories: async () => {
    const response = await api.get('/reports/expense-categories')
    return response.data
  },

  createExpenseCategory: async (categoryData) => {
    const response = await api.post('/reports/expense-categories', categoryData)
    return response.data
  },

  updateExpenseCategory: async (categoryId, categoryData) => {
    const response = await api.put(`/reports/expense-categories/${categoryId}`, categoryData)
    return response.data
  }
}

export default reportsService
