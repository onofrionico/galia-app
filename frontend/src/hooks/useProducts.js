import { useState, useCallback } from 'react'
import productsApi from '../services/api/productsApi'

export const useProducts = () => {
  const [products, setProducts] = useState([])
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 25,
    pages: 0
  })

  const fetchProductsBySupplier = useCallback(async (supplierId, params = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.getBySupplier(supplierId, params)
      setProducts(data.products || [])
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        per_page: data.per_page || 25,
        pages: data.pages || 0
      })
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al cargar productos'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchProductById = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.getById(id)
      setProduct(data)
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al cargar producto'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const createProduct = useCallback(async (supplierId, productData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.create(supplierId, productData)
      setProducts(prev => [data, ...prev])
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al crear producto'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const updateProduct = useCallback(async (id, productData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.update(id, productData)
      setProducts(prev => prev.map(p => p.id === id ? data : p))
      if (product?.id === id) {
        setProduct(data)
      }
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al actualizar producto'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [product])

  const deleteProduct = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    try {
      await productsApi.delete(id)
      setProducts(prev => prev.filter(p => p.id !== id))
      if (product?.id === id) {
        setProduct(null)
      }
      return true
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al eliminar producto'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [product])

  const searchProducts = useCallback(async (query, filters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.search(query, filters)
      setProducts(data.products || [])
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        per_page: data.per_page || 25,
        pages: data.pages || 0
      })
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al buscar productos'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const linkToMaster = useCallback(async (productId, productMasterId) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.linkToMaster(productId, productMasterId)
      setProducts(prev => prev.map(p => p.id === productId ? data : p))
      if (product?.id === productId) {
        setProduct(data)
      }
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al vincular producto'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [product])

  const unlinkFromMaster = useCallback(async (productId) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.unlinkFromMaster(productId)
      setProducts(prev => prev.map(p => p.id === productId ? data : p))
      if (product?.id === productId) {
        setProduct(data)
      }
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al desvincular producto'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [product])

  return {
    products,
    product,
    loading,
    error,
    pagination,
    fetchProductsBySupplier,
    fetchProductById,
    createProduct,
    updateProduct,
    deleteProduct,
    searchProducts,
    linkToMaster,
    unlinkFromMaster
  }
}

export const useProductMasters = () => {
  const [productMasters, setProductMasters] = useState([])
  const [productMaster, setProductMaster] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 25,
    pages: 0
  })

  const fetchProductMasters = useCallback(async (params = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.productMasters.getAll(params)
      setProductMasters(data.product_masters || [])
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        per_page: data.per_page || 25,
        pages: data.pages || 0
      })
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al cargar product masters'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchProductMasterById = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.productMasters.getById(id)
      setProductMaster(data)
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al cargar product master'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const createProductMaster = useCallback(async (data) => {
    setLoading(true)
    setError(null)
    try {
      const result = await productsApi.productMasters.create(data)
      setProductMasters(prev => [result, ...prev])
      return result
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al crear product master'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const searchProductMasters = useCallback(async (query, filters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.productMasters.search(query, filters)
      setProductMasters(data.product_masters || [])
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        per_page: data.per_page || 25,
        pages: data.pages || 0
      })
      return data
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Error al buscar product masters'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    productMasters,
    productMaster,
    loading,
    error,
    pagination,
    fetchProductMasters,
    fetchProductMasterById,
    createProductMaster,
    searchProductMasters
  }
}
