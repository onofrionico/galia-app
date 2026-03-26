import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, Search, Package, Loader2, AlertCircle } from 'lucide-react'
import { useProducts } from '../../hooks/useProducts'
import { useSupplier } from '../../hooks/useSuppliers'
import ProductForm from '../../components/suppliers/ProductForm'
import ProductList from '../../components/suppliers/ProductList'

export default function ProductCatalogPage() {
  const { supplierId } = useParams()
  const [showProductForm, setShowProductForm] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data: supplier, isLoading: supplierLoading } = useSupplier(supplierId)
  const {
    products,
    loading: productsLoading,
    error,
    fetchProductsBySupplier,
    createProduct,
    updateProduct,
    deleteProduct
  } = useProducts()

  useEffect(() => {
    if (supplierId) {
      loadProducts()
    }
  }, [supplierId, searchTerm, categoryFilter, statusFilter])

  const loadProducts = () => {
    const params = {}
    if (searchTerm) params.search = searchTerm
    if (categoryFilter) params.category = categoryFilter
    if (statusFilter) params.status = statusFilter
    
    fetchProductsBySupplier(supplierId, params)
  }

  const handleCreateProduct = async (productData) => {
    try {
      await createProduct(supplierId, productData)
      setShowProductForm(false)
      alert('Producto creado exitosamente')
    } catch (error) {
      alert(error.response?.data?.message || 'Error al crear el producto')
    }
  }

  const handleUpdateProduct = async (productData) => {
    try {
      await updateProduct(editingProduct.id, productData)
      setEditingProduct(null)
      setShowProductForm(false)
      alert('Producto actualizado exitosamente')
    } catch (error) {
      alert(error.response?.data?.message || 'Error al actualizar el producto')
    }
  }

  const handleEdit = (product) => {
    setEditingProduct(product)
    setShowProductForm(true)
  }

  const handleDelete = async (productId) => {
    await deleteProduct(productId)
  }

  const handleAddProduct = () => {
    setEditingProduct(null)
    setShowProductForm(true)
  }

  const handleCancelForm = () => {
    setShowProductForm(false)
    setEditingProduct(null)
  }

  if (supplierLoading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex justify-center items-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Cargando...</span>
        </div>
      </div>
    )
  }

  if (!supplier) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 text-lg">Proveedor no encontrado</h3>
            <Link to="/suppliers" className="text-red-600 hover:text-red-800 underline mt-2 inline-block">
              Volver a la lista de proveedores
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <Link
          to={`/suppliers/${supplierId}`}
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver a {supplier.name}</span>
        </Link>

        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Catálogo de Productos</h1>
            <p className="text-gray-600 mt-1">{supplier.name}</p>
          </div>
          <button
            onClick={handleAddProduct}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Agregar Producto</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Buscar por nombre o SKU..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Todas las categorías</option>
              <option value="Alimentos">Alimentos</option>
              <option value="Bebidas">Bebidas</option>
              <option value="Lácteos">Lácteos</option>
              <option value="Carnes">Carnes</option>
              <option value="Verduras">Verduras</option>
              <option value="Frutas">Frutas</option>
              <option value="Panadería">Panadería</option>
              <option value="Limpieza">Limpieza</option>
              <option value="Descartables">Descartables</option>
              <option value="Otros">Otros</option>
            </select>
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Todos los estados</option>
              <option value="active">Activo</option>
              <option value="discontinued">Discontinuado</option>
              <option value="archived">Archivado</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      <ProductList
        products={products}
        onEdit={handleEdit}
        onDelete={handleDelete}
        loading={productsLoading}
      />

      {showProductForm && (
        <ProductForm
          product={editingProduct}
          supplierId={parseInt(supplierId)}
          onSubmit={editingProduct ? handleUpdateProduct : handleCreateProduct}
          onCancel={handleCancelForm}
          isLoading={productsLoading}
        />
      )}
    </div>
  )
}
