import api from '../api'

const configurationApi = {
  // ============================================================================
  // Configurable Lists
  // ============================================================================
  
  // Get all items for a specific list type
  getConfigurableList: async (listType, activeOnly = true) => {
    const response = await api.get(`/configurable-lists/${listType}`, {
      params: { active_only: activeOnly }
    })
    return response.data
  },

  // Get just the values for a specific list type (simplified)
  getConfigurableListValues: async (listType) => {
    const response = await api.get(`/configurable-lists/${listType}/values`)
    return response.data
  },

  // Create new configurable list item
  createConfigurableListItem: async (itemData) => {
    const response = await api.post('/configurable-lists', itemData)
    return response.data
  },

  // Update configurable list item
  updateConfigurableListItem: async (itemId, itemData) => {
    const response = await api.put(`/configurable-lists/${itemId}`, itemData)
    return response.data
  },

  // Deactivate configurable list item
  deactivateConfigurableListItem: async (itemId) => {
    const response = await api.delete(`/configurable-lists/${itemId}`)
    return response.data
  },

  // Reorder items in a list
  reorderConfigurableList: async (listType, items) => {
    const response = await api.post(`/configurable-lists/${listType}/reorder`, { items })
    return response.data
  },

  // ============================================================================
  // Exchange Rates
  // ============================================================================

  // Get all exchange rates with filters
  getExchangeRates: async (params = {}) => {
    const response = await api.get('/exchange-rates', { params })
    return response.data
  },

  // Get latest exchange rates for all currency pairs
  getLatestExchangeRates: async () => {
    const response = await api.get('/exchange-rates/latest')
    return response.data
  },

  // Get exchange rate for specific currency pair and date
  getExchangeRateForDate: async (fromCurrency, toCurrency, date = null) => {
    const params = {
      from_currency: fromCurrency,
      to_currency: toCurrency
    }
    if (date) {
      params.date = date
    }
    const response = await api.get('/exchange-rates/rate', { params })
    return response.data
  },

  // Create new exchange rate
  createExchangeRate: async (rateData) => {
    const response = await api.post('/exchange-rates', rateData)
    return response.data
  },

  // Update exchange rate
  updateExchangeRate: async (rateId, rateData) => {
    const response = await api.put(`/exchange-rates/${rateId}`, rateData)
    return response.data
  },

  // Delete exchange rate
  deleteExchangeRate: async (rateId) => {
    const response = await api.delete(`/exchange-rates/${rateId}`)
    return response.data
  }
}

export default configurationApi
