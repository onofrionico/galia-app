import { useState, useCallback } from 'react'
import purchasesApi from '../services/api/purchasesApi'

export const usePurchases = () => {
  const [purchases, setPurchases] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPurchases = useCallback(async (filters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.getAll(filters)
      setPurchases(data.purchases || [])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar compras')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchPurchaseById = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.getById(id)
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar compra')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const createPurchase = useCallback(async (purchaseData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.create(purchaseData)
      setPurchases(prev => [data, ...prev])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear compra')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const updatePurchase = useCallback(async (id, purchaseData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.update(id, purchaseData)
      setPurchases(prev => prev.map(p => p.id === id ? data : p))
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar compra')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const deletePurchase = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    try {
      await purchasesApi.delete(id)
      setPurchases(prev => prev.filter(p => p.id !== id))
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar compra')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchPurchasesBySupplier = useCallback(async (supplierId, filters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.getBySupplier(supplierId, filters)
      setPurchases(data.purchases || [])
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar compras del proveedor')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const updateProductPrices = useCallback(async (purchaseId, priceUpdates) => {
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.updateProductPrices(purchaseId, priceUpdates)
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar precios')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    purchases,
    loading,
    error,
    fetchPurchases,
    fetchPurchaseById,
    createPurchase,
    updatePurchase,
    deletePurchase,
    fetchPurchasesBySupplier,
    updateProductPrices
  }
}

export const usePurchase = (id) => {
  const [purchase, setPurchase] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPurchase = useCallback(async () => {
    if (!id) return
    
    setLoading(true)
    setError(null)
    try {
      const data = await purchasesApi.getById(id)
      setPurchase(data)
      return data
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar compra')
      throw err
    } finally {
      setLoading(false)
    }
  }, [id])

  return {
    purchase,
    loading,
    error,
    fetchPurchase,
    refetch: fetchPurchase
  }
}
