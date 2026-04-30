import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Save, X, Plus, Trash2, ArrowLeft } from 'lucide-react'
import productsService from '../services/productsService'
import productCategoriesService from '../services/productCategoriesService'

const ProductDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const isNew = id === undefined || id === 'new'

  const [product, setProduct] = useState(null)
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('info')

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category_id: '',
    image_url: '',
    has_recipe: false,
  })

  const [variants, setVariants] = useState([])
  const [recipe, setRecipe] = useState([])
  const [newVariantForm, setNewVariantForm] = useState({
    name: '',
    price: '',
    stock_quantity: '',
    min_stock: '',
  })
  const [newRecipeForm, setNewRecipeForm] = useState({
    supply_id: '',
    quantity: '',
    unit: '',
  })

  useEffect(() => {
    fetchCategories()
    if (!isNew) {
      fetchProduct()
    }
  }, [])

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

  const fetchProduct = async () => {
    try {
      const response = await productsService.getProduct(id)
      setProduct(response)
      setFormData({
        name: response.name,
        description: response.description || '',
        category_id: response.category_id,
        image_url: response.image_url || '',
        has_recipe: response.has_recipe,
      })
      setVariants(response.variants || [])
      setRecipe(response.recipe || [])
      setError('')
    } catch (error) {
      console.error('Error fetching product:', error)
      setError('Error al cargar el producto')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveProduct = async () => {
    if (!formData.name.trim() || !formData.category_id) {
      setError('Nombre y categoría son requeridos')
      return
    }

    setSaving(true)
    try {
      if (isNew) {
        const newProduct = await productsService.createProduct(formData)
        navigate(`/products/${newProduct.id}`)
      } else {
        await productsService.updateProduct(id, formData)
        fetchProduct()
      }
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const handleAddVariant = async () => {
    if (!newVariantForm.name.trim() || !newVariantForm.price) {
      setError('Nombre y precio son requeridos')
      return
    }

    try {
      const newVariant = await productsService.createVariant(id || product.id, {
        name: newVariantForm.name,
        price: parseFloat(newVariantForm.price),
        stock_quantity: parseFloat(newVariantForm.stock_quantity || 0),
        min_stock: parseFloat(newVariantForm.min_stock || 0),
      })
      setVariants([...variants, newVariant])
      setNewVariantForm({ name: '', price: '', stock_quantity: '', min_stock: '' })
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al crear variante')
    }
  }

  const handleDeleteVariant = async (variantId) => {
    if (window.confirm('¿Desactivar esta variante?')) {
      try {
        await productsService.deleteVariant(id || product.id, variantId)
        setVariants(variants.filter((v) => v.id !== variantId))
        setError('')
      } catch (error) {
        setError('Error al desactivar variante')
      }
    }
  }

  const handleUpdateVariant = async (variantId, field, value) => {
    try {
      const variant = variants.find((v) => v.id === variantId)
      const updated = { ...variant, [field]: value }
      await productsService.updateVariant(id || product.id, variantId, updated)
      setVariants(
        variants.map((v) => (v.id === variantId ? { ...v, [field]: value } : v))
      )
    } catch (error) {
      setError('Error al actualizar variante')
    }
  }

  const handleAddRecipeItem = async () => {
    if (!newRecipeForm.supply_id || !newRecipeForm.quantity) {
      setError('Insumo y cantidad son requeridos')
      return
    }

    try {
      const items = [
        ...recipe,
        {
          supply_id: parseInt(newRecipeForm.supply_id),
          quantity: parseFloat(newRecipeForm.quantity),
          unit: newRecipeForm.unit,
        },
      ]
      await productsService.saveRecipe(id || product.id, items)
      setRecipe(items)
      setNewRecipeForm({ supply_id: '', quantity: '', unit: '' })
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al agregar a receta')
    }
  }

  const handleDeleteRecipeItem = async (index) => {
    try {
      const items = recipe.filter((_, i) => i !== index)
      await productsService.saveRecipe(id || product.id, items)
      setRecipe(items)
    } catch (error) {
      setError('Error al eliminar de receta')
    }
  }

  if (loading) {
    return <div className="p-4">Cargando...</div>
  }

  return (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/products')}
          className="p-2 hover:bg-gray-100 rounded"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-3xl font-bold">
          {isNew ? 'Nuevo Producto' : product?.name}
        </h1>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="border-b flex">
          {['info', 'variantes', 'receta', 'historial'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-medium ${
                activeTab === tab
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'info' && 'Información'}
              {tab === 'variantes' && 'Variantes'}
              {tab === 'receta' && 'Receta'}
              {tab === 'historial' && 'Historial'}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'info' && (
            <div className="space-y-4 max-w-2xl">
              <div>
                <label className="block text-sm font-medium mb-1">Nombre *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Descripción</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows="3"
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Categoría *</label>
                <select
                  value={formData.category_id}
                  onChange={(e) =>
                    setFormData({ ...formData, category_id: parseInt(e.target.value) })
                  }
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Seleccionar categoría</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">URL de Imagen</label>
                <input
                  type="text"
                  value={formData.image_url}
                  onChange={(e) =>
                    setFormData({ ...formData, image_url: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://..."
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="has_recipe"
                  checked={formData.has_recipe}
                  onChange={(e) =>
                    setFormData({ ...formData, has_recipe: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label htmlFor="has_recipe" className="font-medium">
                  Este producto tiene receta (compuesto de insumos)
                </label>
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  onClick={handleSaveProduct}
                  disabled={saving}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  <Save size={18} />
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => navigate('/products')}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {activeTab === 'variantes' && product && (
            <div>
              <table className="w-full mb-6 border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left px-4 py-2 text-sm font-medium">Nombre</th>
                    <th className="text-left px-4 py-2 text-sm font-medium">Precio</th>
                    <th className="text-left px-4 py-2 text-sm font-medium">
                      Stock
                    </th>
                    <th className="text-left px-4 py-2 text-sm font-medium">
                      Min Stock
                    </th>
                    <th className="text-left px-4 py-2 text-sm font-medium">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {variants.map((variant) => (
                    <tr key={variant.id} className="border-b">
                      <td className="px-4 py-2">{variant.name}</td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          value={variant.price}
                          onChange={(e) =>
                            handleUpdateVariant(
                              variant.id,
                              'price',
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-20 border rounded px-2 py-1"
                          step="0.01"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          value={variant.stock_quantity}
                          onChange={(e) =>
                            handleUpdateVariant(
                              variant.id,
                              'stock_quantity',
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-20 border rounded px-2 py-1"
                          step="0.1"
                          disabled={formData.has_recipe}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          value={variant.min_stock}
                          onChange={(e) =>
                            handleUpdateVariant(
                              variant.id,
                              'min_stock',
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-20 border rounded px-2 py-1"
                          step="0.1"
                          disabled={formData.has_recipe}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <button
                          onClick={() => handleDeleteVariant(variant.id)}
                          className="text-red-600 hover:bg-red-50 p-1 rounded"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Agregar Variante</h3>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Nombre (Chico, Mediano...)"
                    value={newVariantForm.name}
                    onChange={(e) =>
                      setNewVariantForm({ ...newVariantForm, name: e.target.value })
                    }
                    className="border rounded px-3 py-2 text-sm"
                  />
                  <input
                    type="number"
                    placeholder="Precio"
                    value={newVariantForm.price}
                    onChange={(e) =>
                      setNewVariantForm({ ...newVariantForm, price: e.target.value })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    step="0.01"
                  />
                  <input
                    type="number"
                    placeholder="Stock"
                    value={newVariantForm.stock_quantity}
                    onChange={(e) =>
                      setNewVariantForm({
                        ...newVariantForm,
                        stock_quantity: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    disabled={formData.has_recipe}
                  />
                  <input
                    type="number"
                    placeholder="Min Stock"
                    value={newVariantForm.min_stock}
                    onChange={(e) =>
                      setNewVariantForm({
                        ...newVariantForm,
                        min_stock: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    disabled={formData.has_recipe}
                  />
                </div>
                <button
                  onClick={handleAddVariant}
                  className="mt-3 flex items-center gap-2 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700"
                >
                  <Plus size={16} /> Agregar
                </button>
              </div>
            </div>
          )}

          {activeTab === 'receta' && product?.has_recipe && product && (
            <div>
              {recipe.length > 0 && (
                <table className="w-full mb-6 border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Insumo
                      </th>
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Cantidad
                      </th>
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Unidad
                      </th>
                      <th className="text-left px-4 py-2 text-sm font-medium">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recipe.map((item, index) => (
                      <tr key={index} className="border-b">
                        <td className="px-4 py-2">{item.supply_name}</td>
                        <td className="px-4 py-2">{item.quantity}</td>
                        <td className="px-4 py-2">{item.unit}</td>
                        <td className="px-4 py-2">
                          <button
                            onClick={() => handleDeleteRecipeItem(index)}
                            className="text-red-600 hover:bg-red-50 p-1 rounded"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Agregar Insumo a Receta</h3>
                <p className="text-sm text-gray-600 mb-3">
                  (Las cantidades se deducirán del stock de insumos al vender)
                </p>
                <div className="grid grid-cols-3 gap-3">
                  <select
                    value={newRecipeForm.supply_id}
                    onChange={(e) =>
                      setNewRecipeForm({
                        ...newRecipeForm,
                        supply_id: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                  >
                    <option value="">Seleccionar insumo</option>
                  </select>
                  <input
                    type="number"
                    placeholder="Cantidad"
                    value={newRecipeForm.quantity}
                    onChange={(e) =>
                      setNewRecipeForm({
                        ...newRecipeForm,
                        quantity: e.target.value,
                      })
                    }
                    className="border rounded px-3 py-2 text-sm"
                    step="0.01"
                  />
                  <input
                    type="text"
                    placeholder="Unidad (kg, litro...)"
                    value={newRecipeForm.unit}
                    onChange={(e) =>
                      setNewRecipeForm({ ...newRecipeForm, unit: e.target.value })
                    }
                    className="border rounded px-3 py-2 text-sm"
                  />
                </div>
                <button
                  onClick={handleAddRecipeItem}
                  className="mt-3 flex items-center gap-2 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700"
                >
                  <Plus size={16} /> Agregar a Receta
                </button>
              </div>
            </div>
          )}

          {activeTab === 'receta' && !product?.has_recipe && (
            <div className="text-gray-500 text-center py-8">
              Este producto no tiene receta. Activa la opción "Tiene receta" en la
              pestaña Información para poder definir insumos.
            </div>
          )}

          {activeTab === 'historial' && (
            <div className="text-gray-500 text-center py-8">
              El historial de ventas se mostrará aquí (próximamente)
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProductDetail
