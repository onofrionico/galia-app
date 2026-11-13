import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Save, X, Plus, Trash2, ArrowLeft, Lock, Link2, Unlink } from 'lucide-react'
import productsService from '../services/productsService'
import recipesService from '../services/recipesService'
import { useAuth } from '../context/AuthContext'
import { formatMoney } from '../utils/moneyFormat'
import { formatYield } from '../components/recipes/format'
import productCategoriesService from '../services/productCategoriesService'
import EditableNumberInput from '../components/EditableNumberInput'
import ProductModifiersTab from '../components/products/ProductModifiersTab'
import ProductComponentsTab from '../components/products/ProductComponentsTab'
import FudoProductPicker from '../components/menu/FudoProductPicker'
import {
  FUDO_LOCK_HINT,
  FUDO_STATUS_LABELS,
  candidateLegend,
  isFudoLocked,
  variantFudoStatus,
} from '../utils/fudoLock'

const ProductDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { hasModuleAccess } = useAuth()
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
    track_stock: false,
  })

  const [variants, setVariants] = useState([])
  const [recipeDetail, setRecipeDetail] = useState(null)
  const [newVariantForm, setNewVariantForm] = useState({
    name: '',
    price: '',
    stock_quantity: '',
    min_stock: '',
  })
  const [imageFile, setImageFile] = useState(null)
  const [imageUploading, setImageUploading] = useState(false)
  const [imageError, setImageError] = useState('')
  const [fudoCandidates, setFudoCandidates] = useState(null)

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => {
    if (!isNew) {
      setLoading(true)
      fetchProduct()
    }
  }, [id])

  useEffect(() => {
    const linked = product?.recipe
    setRecipeDetail(null)
    if (!linked || !hasModuleAccess('Recipes')) return undefined
    let ignore = false
    recipesService
      .get(linked.id)
      .then((r) => { if (!ignore) setRecipeDetail(r) })
      .catch(() => {})
    return () => { ignore = true }
  }, [product?.recipe?.id])

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
        track_stock: response.track_stock || false,
      })
      setVariants(response.variants || [])
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
        navigate(`/products/${newProduct.id}`, { replace: true })
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
      setVariants((prev) => [...prev, newVariant])
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
        setVariants((prev) => prev.filter((v) => v.id !== variantId))
        setError('')
      } catch (error) {
        setError(error.response?.data?.error || 'Error al desactivar variante')
      }
    }
  }

  const handleUpdateVariant = async (variantId, field, raw) => {
    const num = Number(raw)
    if (raw === '' || !Number.isFinite(num) || num < 0) {
      setError('Ingresá un número válido mayor o igual a 0')
      return false
    }
    try {
      const updated = await productsService.updateVariant(id || product.id, variantId, {
        [field]: num,
      })
      setVariants((prev) =>
        prev.map((v) => (v.id === variantId ? { ...v, ...updated } : v))
      )
      setError('')
      return true
    } catch (error) {
      setError(error.response?.data?.error || 'Error al actualizar variante')
      return false
    }
  }

  const openFudoPicker = async () => {
    try {
      setFudoCandidates(await productsService.getFudoCandidates())
    } catch (error) {
      setError(error.response?.data?.error || 'Error al cargar productos de Fudo')
    }
  }

  const handleAttachFudo = async (candidate) => {
    if (candidate.product_id && !window.confirm(`«${candidate.name}» se moverá desde «${candidate.product_name}». ¿Continuar?`)) {
      return
    }
    try {
      const updated = await productsService.attachFudoVariant(product.id, candidate.fudo_id)
      setFudoCandidates(null)
      setProduct(updated)
      setVariants(updated.variants || [])
      setError('')
    } catch (error) {
      setError(error.response?.data?.error || 'Error al agregar la variante de Fudo')
    }
  }

  const handleDetachVariant = async (variant) => {
    if (!window.confirm(`¿Separar «${variant.name}» en un producto propio?`)) return
    try {
      await productsService.detachVariant(product.id, variant.id)
      fetchProduct()
    } catch (error) {
      setError(error.response?.data?.error || 'Error al separar la variante')
    }
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!validTypes.includes(file.type)) {
      setImageError('Formato inválido. Solo se permiten: JPEG, PNG, WebP')
      return
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      setImageError('Archivo muy grande. Máximo 10MB')
      return
    }

    setImageFile(file)
    setImageError('')
    setImageUploading(true)

    try {
      const uploadedUrl = await productsService.uploadProductImage(file)
      setFormData({ ...formData, image_url: uploadedUrl })
      setImageError('')
    } catch (err) {
      setImageError(err.response?.data?.error || 'Error al subir imagen')
      setImageFile(null)
    } finally {
      setImageUploading(false)
    }
  }

  const handleDeleteImage = () => {
    setFormData({ ...formData, image_url: '' })
    setImageFile(null)
    setImageError('')
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

      {product?.fudo_linked && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-4 py-3 rounded mb-4 flex items-center gap-2">
          <Lock size={16} /> Nombre, categoría, precios y estado se editan en Fudo.
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="border-b flex">
          {['info', 'variantes', 'receta', 'modificadores', 'componentes', 'historial'].map((tab) => (
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
              {tab === 'modificadores' && 'Modificadores'}
              {tab === 'componentes' && 'Componentes'}
              {tab === 'historial' && 'Historial'}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'info' && (
            <div className="space-y-4 max-w-2xl">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Nombre *
                  {isFudoLocked(product, 'name') && <Lock size={12} className="inline ml-1 text-gray-500" />}
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  required
                  disabled={isFudoLocked(product, 'name')}
                  title={isFudoLocked(product, 'name') ? FUDO_LOCK_HINT : undefined}
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
                <label className="block text-sm font-medium mb-1">
                  Categoría *
                  {isFudoLocked(product, 'category_id') && <Lock size={12} className="inline ml-1 text-gray-500" />}
                </label>
                <select
                  value={formData.category_id}
                  onChange={(e) =>
                    setFormData({ ...formData, category_id: e.target.value === '' ? '' : parseInt(e.target.value, 10) })
                  }
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  required
                  disabled={isFudoLocked(product, 'category_id')}
                  title={isFudoLocked(product, 'category_id') ? FUDO_LOCK_HINT : undefined}
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
                <label className="block text-sm font-medium mb-3">Imagen del Producto</label>

                {imageError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded mb-3">
                    {imageError}
                  </div>
                )}

                {formData.image_url && (
                  <div className="mb-4">
                    <img
                      src={formData.image_url}
                      alt="preview"
                      className="h-32 w-32 object-cover rounded border border-gray-300"
                    />
                    <button
                      onClick={handleDeleteImage}
                      type="button"
                      className="mt-2 text-red-600 text-sm hover:text-red-700 font-medium"
                    >
                      Eliminar imagen
                    </button>
                  </div>
                )}

                <label className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-300 rounded-lg p-6 cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageUpload}
                    disabled={imageUploading}
                    className="hidden"
                  />
                  <span className="text-gray-700 font-medium">
                    {imageUploading ? 'Subiendo...' : 'Selecciona una imagen'}
                  </span>
                </label>
                <p className="text-xs text-gray-500 mt-2">
                  Formatos: JPEG, PNG, WebP • Máximo 10MB
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="track_stock"
                  checked={formData.track_stock}
                  onChange={(e) =>
                    setFormData({ ...formData, track_stock: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label htmlFor="track_stock" className="font-medium">
                  Control de stock
                </label>
                <span className="text-xs text-gray-500">
                  (si está activo, verifica disponibilidad antes de agregar a una orden)
                </span>
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
                    <th className="text-left px-4 py-2 text-sm font-medium">Fudo</th>
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
                  {variants.map((variant) => {
                    const status = variantFudoStatus(variant)
                    const linked = status !== null
                    return (
                      <tr key={variant.id} className={`border-b ${variant.is_active ? '' : 'opacity-60'}`}>
                        <td className="px-4 py-2">{variant.name}</td>
                        <td className="px-4 py-2">
                          {linked && (
                            <span
                              className={`text-xs px-2 py-1 rounded ${
                                status === 'ok' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {FUDO_STATUS_LABELS[status]}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2">
                          {linked ? (
                            <span title={FUDO_LOCK_HINT}>${variant.price}</span>
                          ) : (
                            <EditableNumberInput
                              value={variant.price}
                              onCommit={(raw) => handleUpdateVariant(variant.id, 'price', raw)}
                              className="w-20 border rounded px-2 py-1"
                              step="0.01"
                            />
                          )}
                        </td>
                        <td className="px-4 py-2">
                          <EditableNumberInput
                            value={variant.stock_quantity}
                            onCommit={(raw) => handleUpdateVariant(variant.id, 'stock_quantity', raw)}
                            className="w-20 border rounded px-2 py-1"
                            disabled={Boolean(product?.has_recipe)}
                          />
                        </td>
                        <td className="px-4 py-2">
                          <EditableNumberInput
                            value={variant.min_stock}
                            onCommit={(raw) => handleUpdateVariant(variant.id, 'min_stock', raw)}
                            className="w-20 border rounded px-2 py-1"
                            disabled={Boolean(product?.has_recipe)}
                          />
                        </td>
                        <td className="px-4 py-2">
                          {linked && status !== 'missing' ? (
                            variants.length > 1 && (
                              <button
                                onClick={() => handleDetachVariant(variant)}
                                className="flex items-center gap-1 text-sm text-gray-700 hover:bg-gray-100 px-2 py-1 rounded"
                                title="Separar en un producto propio"
                              >
                                <Unlink size={16} /> Separar
                              </button>
                            )
                          ) : (
                            <button
                              onClick={() => handleDeleteVariant(variant.id)}
                              className="text-red-600 hover:bg-red-50 p-1 rounded"
                            >
                              <Trash2 size={18} />
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              <div className="mb-6">
                {fudoCandidates === null ? (
                  <button
                    onClick={openFudoPicker}
                    className="flex items-center gap-2 border border-emerald-300 text-emerald-800 px-3 py-2 rounded text-sm hover:bg-emerald-50"
                  >
                    <Link2 size={16} /> Agregar variante desde Fudo
                  </button>
                ) : (
                  <FudoProductPicker
                    products={fudoCandidates}
                    isDisabled={(p) => p.product_id === product.id}
                    describe={(p) => candidateLegend(p, product.id)}
                    emptyLabel='No hay productos de Fudo: tocá "Sincronizar con Fudo" en Productos.'
                    onSelect={handleAttachFudo}
                    onCancel={() => setFudoCandidates(null)}
                  />
                )}
              </div>

              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Agregar variante manual</h3>
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
                    disabled={Boolean(product?.has_recipe)}
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
                    disabled={Boolean(product?.has_recipe)}
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

          {activeTab === 'receta' && !product && (
            <div className="text-gray-500 text-center py-8">Guardá el producto para poder vincularle una receta.</div>
          )}

          {activeTab === 'receta' && product && product.recipe && (
            <div className="space-y-2 max-w-2xl">
              <h3 className="text-lg font-semibold">{product.recipe.name}</h3>
              {recipeDetail && formatYield(recipeDetail.yield_quantity, recipeDetail.yield_unit) && (
                <p className="text-gray-700">
                  Rinde {formatYield(recipeDetail.yield_quantity, recipeDetail.yield_unit)}
                </p>
              )}
              <p className="text-gray-700">
                {product.has_recipe
                  ? 'Esta receta descuenta el stock de insumos al vender.'
                  : 'Esta receta no descuenta stock.'}
              </p>
              {product.recipe_cost?.unit_cost != null && (
                <p className="text-gray-700">
                  Costo por unidad: {formatMoney(product.recipe_cost.unit_cost)}
                  {!product.recipe_cost.complete && ' (incompleto)'}
                </p>
              )}
              {hasModuleAccess('Recipes') && (
                <Link to={`/recipes/${product.recipe.id}`} className="inline-block text-blue-600 underline">
                  Ver receta
                </Link>
              )}
            </div>
          )}

          {activeTab === 'receta' && product && !product.recipe && (
            <div className="text-gray-500 py-8 text-center">
              <p>Sin receta</p>
              {hasModuleAccess('RecipesAdmin') && (
                <Link to="/recipes/new" className="inline-block mt-2 text-blue-600 underline">
                  Crear receta
                </Link>
              )}
            </div>
          )}

          {activeTab === 'modificadores' && product && <ProductModifiersTab productId={product.id} />}
          {activeTab === 'modificadores' && !product && (
            <div className="py-8 text-center text-gray-500">Guardá el producto para asignarle modificadores.</div>
          )}

          {activeTab === 'componentes' && product && <ProductComponentsTab productId={product.id} />}
          {activeTab === 'componentes' && !product && (
            <div className="py-8 text-center text-gray-500">Guardá el producto para cargarle componentes.</div>
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
