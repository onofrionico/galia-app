import { useState, useCallback } from 'react'
import configurationApi from '../services/api/configurationApi'

export const useConfigurableList = (listType) => {
  const [items, setItems] = useState([])
  const [values, setValues] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchItems = useCallback(async (activeOnly = true) => {
    if (!listType) return
    
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.getConfigurableList(listType, activeOnly)
      setItems(data.items || [])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar lista configurable')
      throw err
    } finally {
      setLoading(false)
    }
  }, [listType])

  const fetchValues = useCallback(async () => {
    if (!listType) return
    
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.getConfigurableListValues(listType)
      setValues(data.values || [])
      return data.values
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar valores')
      throw err
    } finally {
      setLoading(false)
    }
  }, [listType])

  const createItem = useCallback(async (itemData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.createConfigurableListItem({
        ...itemData,
        list_type: listType
      })
      setItems(prev => [...prev, data])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear item')
      throw err
    } finally {
      setLoading(false)
    }
  }, [listType])

  const updateItem = useCallback(async (itemId, itemData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.updateConfigurableListItem(itemId, itemData)
      setItems(prev => prev.map(item => item.id === itemId ? data : item))
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar item')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const deactivateItem = useCallback(async (itemId) => {
    setLoading(true)
    setError(null)
    try {
      await configurationApi.deactivateConfigurableListItem(itemId)
      setItems(prev => prev.filter(item => item.id !== itemId))
    } catch (err) {
      setError(err.response?.data?.error || 'Error al desactivar item')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const reorderItems = useCallback(async (itemOrders) => {
    setLoading(true)
    setError(null)
    try {
      await configurationApi.reorderConfigurableList(listType, itemOrders)
      await fetchItems()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al reordenar items')
      throw err
    } finally {
      setLoading(false)
    }
  }, [listType, fetchItems])

  return {
    items,
    values,
    loading,
    error,
    fetchItems,
    fetchValues,
    createItem,
    updateItem,
    deactivateItem,
    reorderItems
  }
}

export const useExchangeRates = () => {
  const [rates, setRates] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchRates = useCallback(async (filters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.getExchangeRates(filters)
      setRates(data.rates || [])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar tipos de cambio')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchLatestRates = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.getLatestExchangeRates()
      setRates(data.rates || [])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar tipos de cambio')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const getRateForDate = useCallback(async (fromCurrency, toCurrency, date = null) => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.getExchangeRateForDate(fromCurrency, toCurrency, date)
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al obtener tipo de cambio')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const createRate = useCallback(async (rateData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.createExchangeRate(rateData)
      setRates(prev => [data, ...prev])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear tipo de cambio')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const updateRate = useCallback(async (rateId, rateData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await configurationApi.updateExchangeRate(rateId, rateData)
      setRates(prev => prev.map(rate => rate.id === rateId ? data : rate))
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar tipo de cambio')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteRate = useCallback(async (rateId) => {
    setLoading(true)
    setError(null)
    try {
      await configurationApi.deleteExchangeRate(rateId)
      setRates(prev => prev.filter(rate => rate.id !== rateId))
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar tipo de cambio')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    rates,
    loading,
    error,
    fetchRates,
    fetchLatestRates,
    getRateForDate,
    createRate,
    updateRate,
    deleteRate
  }
}
