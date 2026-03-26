import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Search, Filter, Download, Package, Eye, Edit, Trash2, Link2, X, Loader2, Upload, Plus } from 'lucide-react'
import productsApi from '../../services/api/productsApi'
import ProductForm from '../../components/products/ProductForm'

export default function ProductsListPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    supplier_id: '',
    category: '',
    status: '',
    min_price: '',
    max_price: ''
  })
  const [showFilters, setShowFilters] = useState(false)
  
  // Pagination
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 25,
    total: 0,
    pages: 0
  })
  
  // Selection for bulk operations
  const [selectedProducts, setSelectedProducts] = useState([])
  const [showBulkPanel, setShowBulkPanel] = useState(false)
  
  // Product form
  const [showProductForm, setShowProductForm] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [formLoading, setFormLoading] = useState(false)
  
  // Import
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    fetchProducts()
  }, [pagination.page, searchTerm, filters])

  const fetchProducts = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        search: searchTerm || undefined,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      }
      
      const data = await productsApi.getAll(params)
      setProducts(data.products || [])
      setPagination(prev => ({
        ...prev,
        total: data.total,
        pages: data.pages
      }))
    } catch (err) {
      setError(err.response?.data?.message || 'Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPagination(prev => ({ ...prev, page: 1 }))
    fetchProducts()
  }

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const clearFilters = () => {
    setFilters({
      supplier_id: '',
      category: '',
      status: '',
      min_price: '',
      max_price: ''
    })
    setSearchTerm('')
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleExport = async () => {
    try {
      const params = {
        search: searchTerm || undefined,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      }
      
      const response = await productsApi.exportToCSV(params)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'productos.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      setError('Error al exportar productos')
    }
  }

  const toggleProductSelection = (productId) => {
    setSelectedProducts(prev => 
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedProducts.length === products.length) {
      setSelectedProducts([])
    } else {
      setSelectedProducts(products.map(p => p.id))
    }
  }

  const handleBulkOperation = async (operation, data) => {
    try {
      await productsApi.bulkUpdate(selectedProducts, operation, data)
      setSelectedProducts([])
      setShowBulkPanel(false)
      fetchProducts()
    } catch (err) {
      setError(err.response?.data?.message || 'Error en operación masiva')
    }
  }

  const handleCreateProduct = () => {
    setEditingProduct(null)
    setShowProductForm(true)
  }

  const handleSaveProduct = async (productData) => {
    setFormLoading(true)
    setError(null)
    try {
      if (editingProduct) {
        await productsApi.update(editingProduct.id, productData)
        setSuccess('Producto actualizado exitosamente')
      } else {
        await productsApi.create(productData.supplier_id, productData)
        setSuccess('Producto creado exitosamente')
      }
      setShowProductForm(false)
      setEditingProduct(null)
      fetchProducts()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.message || 'Error al guardar producto')
    } finally {
      setFormLoading(false)
    }
  }

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setImporting(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await productsApi.importFromExcel(file)
      setSuccess(
        `Importación completada: ${result.created} creados, ${result.updated} actualizados` +
        (result.failed > 0 ? `, ${result.failed} fallidos` : '')
      )
      if (result.errors && result.errors.length > 0) {
        console.error('Errores de importación:', result.errors)
      }
      fetchProducts()
      setTimeout(() => setSuccess(null), 5000)
    } catch (err) {
      setError(err.response?.data?.message || 'Error al importar productos')
    } finally {
      setImporting(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Package className="w-8 h-8 text-blue-600" />
          Productos
        </h1>
        <p className="text-gray-600 mt-1">Gestión global de productos de todos los proveedores</p>
      </div>

      {/* Search and Actions Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por nombre o SKU..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </form>
          
          <div className="flex gap-2">
            <button
              onClick={handleCreateProduct}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Nuevo
            </button>
            
            <button
              onClick={handleImportClick}
              disabled={importing}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {importing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Importando...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Importar
                </>
              )}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xls,.xlsx"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                showFilters ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter className="w-5 h-5" />
              Filtros
            </button>
            
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              Exportar
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
              <input
                type="text"
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                placeholder="Filtrar por categoría"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                <option value="active">Activo</option>
                <option value="inactive">Inactivo</option>
                <option value="discontinued">Discontinuado</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
              >
                <X className="w-5 h-5" />
                Limpiar Filtros
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bulk Operations Panel */}
      {selectedProducts.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-blue-900 font-medium">
              {selectedProducts.length} producto(s) seleccionado(s)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setShowBulkPanel(!showBulkPanel)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Operaciones Masivas
              </button>
              <button
                onClick={() => setSelectedProducts([])}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
          
          {showBulkPanel && (
            <div className="mt-4 pt-4 border-t border-blue-200 grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => {
                  const category = prompt('Ingrese la nueva categoría:')
                  if (category) handleBulkOperation('update_category', { category })
                }}
                className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors"
              >
                Cambiar Categoría
              </button>
              
              <button
                onClick={() => {
                  const status = prompt('Ingrese el nuevo estado (active/inactive/discontinued):')
                  if (status) handleBulkOperation('update_status', { status })
                }}
                className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors"
              >
                Cambiar Estado
              </button>
              
              <button
                onClick={() => {
                  const masterId = prompt('Ingrese el ID del ProductMaster:')
                  if (masterId) handleBulkOperation('link_master', { product_master_id: parseInt(masterId) })
                }}
                className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors flex items-center justify-center gap-2"
              >
                <Link2 className="w-4 h-4" />
                Vincular a Maestro
              </button>
            </div>
          )}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <p className="text-green-800">{success}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Products Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">No se encontraron productos</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedProducts.length === products.length}
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Producto</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Proveedor</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Categoría</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Precio</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Estado</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {products.map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedProducts.includes(product.id)}
                          onChange={() => toggleProductSelection(product.id)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium text-gray-900">{product.name}</div>
                          <div className="text-sm text-gray-500">SKU: {product.sku}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/suppliers/${product.supplier_id}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {product.supplier?.name || 'N/A'}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{product.category || '-'}</td>
                      <td className="px-4 py-3">
                        <span className="font-medium text-gray-900">
                          ${parseFloat(product.current_price).toFixed(2)}
                        </span>
                        <span className="text-sm text-gray-500 ml-1">/{product.unit_of_measure}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          product.status === 'active' ? 'bg-green-100 text-green-800' :
                          product.status === 'inactive' ? 'bg-gray-100 text-gray-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {product.status === 'active' ? 'Activo' :
                           product.status === 'inactive' ? 'Inactivo' : 'Discontinuado'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => navigate(`/products/${product.id}`)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="px-4 py-3 border-t flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Mostrando {((pagination.page - 1) * pagination.per_page) + 1} - {Math.min(pagination.page * pagination.per_page, pagination.total)} de {pagination.total} productos
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                    disabled={pagination.page === 1}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Anterior
                  </button>
                  <span className="px-4 py-2 text-gray-700">
                    Página {pagination.page} de {pagination.pages}
                  </span>
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    disabled={pagination.page === pagination.pages}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Product Form Modal */}
      {showProductForm && (
        <ProductForm
          product={editingProduct}
          onSave={handleSaveProduct}
          onCancel={() => {
            setShowProductForm(false)
            setEditingProduct(null)
          }}
          loading={formLoading}
        />
      )}
    </div>
  )
}
