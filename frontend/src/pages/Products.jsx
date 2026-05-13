import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import productsService from '../services/productsService'
import productCategoriesService from '../services/productCategoriesService'

const Products = () => {
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => {
    fetchProducts()
  }, [page, search, categoryFilter])

  const fetchCategories = async () => {
    try {
      const response = await productCategoriesService.getCategories({
        include_inactive: false,
      })
      setCategories(response.categories || [])
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        per_page: 20,
        search: search.trim(),
      }
      if (categoryFilter) {
        params.category_id = categoryFilter
      }

      const response = await productsService.getProducts(params)
      setProducts(response.products || [])
      setTotalPages(response.pages || 1)
      setError('')
    } catch (error) {
      console.error('Error fetching products:', error)
      setError('Error al cargar los productos')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('¿Desactivar este producto?')) {
      try {
        await productsService.deleteProduct(id)
        fetchProducts()
      } catch (error) {
        setError('Error al desactivar el producto')
      }
    }
  }

  const handleSearch = (e) => {
    setSearch(e.target.value)
    setPage(1)
  }

  const handleCategoryFilter = (e) => {
    setCategoryFilter(e.target.value)
    setPage(1)
  }

  if (loading && products.length === 0) {
    return <div className="p-4">Cargando productos...</div>
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Productos</h1>
        <button
          onClick={() => navigate('/products/new')}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          <Plus size={20} /> Nuevo Producto
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex gap-4 mb-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por nombre..."
              value={search}
              onChange={handleSearch}
              className="w-full border rounded px-3 py-2 pl-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={handleCategoryFilter}
            className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">Todas las categorías</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.icon} {cat.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Producto
              </th>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Categoría
              </th>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Variantes
              </th>
              <th className="text-left px-6 py-3 font-medium text-sm text-gray-700">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {products.length === 0 ? (
              <tr>
                <td colSpan="4" className="px-6 py-4 text-center text-gray-500">
                  No hay productos
                </td>
              </tr>
            ) : (
              products.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <button
                      onClick={() => navigate(`/products/${product.id}`)}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {product.name}
                    </button>
                    {product.has_recipe && (
                      <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                        Receta
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {product.category_icon && (
                      <span className="mr-2">{product.category_icon}</span>
                    )}
                    {product.category_name || '-'}
                  </td>
                  <td className="px-6 py-4">
                    {product.variants && product.variants.length > 0 ? (
                      <div className="flex gap-1 flex-wrap">
                        {product.variants.map((variant) => (
                          <span
                            key={variant.id}
                            className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                          >
                            {variant.name}: ${variant.price}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => navigate(`/products/${product.id}`)}
                        className="p-1 hover:bg-blue-50 rounded text-blue-600"
                        title="Editar"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(product.id)}
                        className="p-1 hover:bg-red-50 rounded text-red-600"
                        title="Desactivar"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1 border rounded hover:bg-gray-50 disabled:text-gray-400"
          >
            Anterior
          </button>
          <span className="px-3 py-1">
            Página {page} de {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 border rounded hover:bg-gray-50 disabled:text-gray-400"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}

export default Products
