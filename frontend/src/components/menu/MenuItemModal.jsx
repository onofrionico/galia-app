import { useState, useEffect, useMemo } from 'react'
import { Trash2, Plus, Link2, Unlink, ImagePlus } from 'lucide-react'
import ModalShell from './ModalShell'
import FudoProductPicker from './FudoProductPicker'
import ItemPicker from './ItemPicker'
import menuService from '../../services/menuService'
import { formatPrice, errorMessage } from '../../utils/menuFormat'

const emptyVariant = () => ({ label: '', fudo_product_id: null, price: '' })

const toFormVariant = (v) => ({
  label: v.label || '',
  fudo_product_id: v.fudo_product_id || null,
  price: v.price ?? '',
  fudo_status: v.fudo_status || null,
})

// item: ítem existente o null. allItems: lista plana { id, name, categoryName, variants } para unir ítems.
const MenuItemModal = ({ item, allItems = [], categories, tags, defaultCategoryId, onClose, onSaved }) => {
  const source = item || {}
  const [form, setForm] = useState({
    name: source.name || '',
    description: source.description || '',
    category_id: source.category_id || defaultCategoryId || categories[0]?.id || '',
    is_visible: source.is_visible ?? true,
    is_featured: source.is_featured || false,
    tag_ids: source.tag_ids || [],
  })
  const [variants, setVariants] = useState(source.variants?.length ? source.variants.map(toFormVariant) : [emptyVariant()])
  const [products, setProducts] = useState([])
  const [pickerIndex, setPickerIndex] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(item?.image_url || null)
  const [removeImage, setRemoveImage] = useState(false)
  const [savedItemId, setSavedItemId] = useState(item?.id || null)
  const [mergePicker, setMergePicker] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    menuService.getFudoProducts().then(setProducts).catch(() => setProducts([]))
  }, [])

  useEffect(() => () => {
    if (imagePreview?.startsWith('blob:')) URL.revokeObjectURL(imagePreview)
  }, [imagePreview])

  const isLinked = variants.some((v) => v.fudo_product_id)
  const categoryName = categories.find((c) => c.id === form.category_id)?.name
  const productsById = useMemo(() => Object.fromEntries(products.map((p) => [p.fudo_id, p])), [products])
  const ownFudoIds = useMemo(() => new Set((item?.variants || []).map((v) => v.fudo_product_id).filter(Boolean)), [item])

  const updateVariant = (index, changes) => setVariants((vs) => vs.map((v, i) => (i === index ? { ...v, ...changes } : v)))
  const removeVariant = (index) => setVariants((vs) => vs.filter((_, i) => i !== index))

  const toggleTag = (id) =>
    setForm((f) => ({ ...f, tag_ids: f.tag_ids.includes(id) ? f.tag_ids.filter((t) => t !== id) : [...f.tag_ids, id] }))

  const handleImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setImageFile(file)
    setRemoveImage(false)
    setImagePreview(URL.createObjectURL(file))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    const { category_id: _category, ...rest } = form
    const payload = {
      ...rest,
      ...(isLinked ? {} : { category_id: Number(form.category_id) }),
      variants: variants.map((v) => ({
        label: v.label.trim() || null,
        fudo_product_id: v.fudo_product_id,
        price: v.fudo_product_id ? null : v.price,
      })),
    }
    try {
      const saved = savedItemId ? await menuService.updateItem(savedItemId, payload) : await menuService.createItem(payload)
      setSavedItemId(saved.id)
      if (imageFile) await menuService.uploadItemImage(saved.id, imageFile)
      else if (removeImage && saved.image_key) await menuService.deleteItemImage(saved.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al guardar el ítem'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`¿Borrar "${item.name}" de la carta?`)) return
    setSaving(true)
    try {
      await menuService.deleteItem(item.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al borrar el ítem'))
      setSaving(false)
    }
  }

  const handleMerge = async (target) => {
    if (!window.confirm(`¿Unir "${item.name}" dentro de "${target.name}"? Sus precios pasan a ese ítem y este se elimina.`)) return
    setSaving(true)
    try {
      await menuService.mergeItem(target.id, item.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al unir los ítems'))
      setSaving(false)
    }
  }

  const handleIgnore = async () => {
    if (!window.confirm(`¿Ignorar "${item.name}"? Se quita de la carta y no se vuelve a crear al sincronizar.`)) return
    setSaving(true)
    try {
      await menuService.ignoreItem(item.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al ignorar el ítem'))
      setSaving(false)
    }
  }

  // Si el ítem se creó en esta sesión (ej. falló la foto), cerrar debe refrescar la lista.
  const handleClose = () => (!item && savedItemId ? onSaved() : onClose())

  const usedFudoIds = (exceptIndex) =>
    new Set(variants.filter((v, i) => i !== exceptIndex && v.fudo_product_id).map((v) => v.fudo_product_id))

  return (
    <ModalShell
      title={item ? 'Editar ítem' : 'Nuevo ítem'}
      onClose={handleClose}
      footer={
        <>
          {item && (
            <div className="mr-auto flex flex-wrap gap-1">
              {!isLinked && (
                <button type="button" onClick={handleDelete} disabled={saving} className="px-3 py-2 text-red-600 hover:bg-red-50 rounded">
                  Borrar
                </button>
              )}
              <button type="button" onClick={() => setMergePicker((v) => !v)} disabled={saving} className="px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                Unir con otro ítem
              </button>
              <button type="button" onClick={handleIgnore} disabled={saving} className="px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                Ignorar
              </button>
            </div>
          )}
          <button type="button" onClick={handleClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancelar</button>
          <button type="submit" form="item-form" disabled={saving} className="px-4 py-2 bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </>
      }
    >
      <form id="item-form" onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

        {item && mergePicker && (
          <ItemPicker items={allItems} excludeId={item.id} onSelect={handleMerge} onCancel={() => setMergePicker(false)} />
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>

        <div>
          {isLinked ? (
            <p className="text-sm text-gray-700">Categoría: <strong>{categoryName}</strong> <span className="text-xs text-gray-500">(de Fudo)</span></p>
          ) : (
            <>
              <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
              <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded">
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </>
          )}
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-1">Foto</span>
          <div className="flex items-center gap-3">
            {imagePreview && !removeImage ? (
              <img src={imagePreview} alt="" className="h-20 w-20 rounded object-cover" />
            ) : (
              <div className="h-20 w-20 rounded bg-gray-100" />
            )}
            <label className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded cursor-pointer hover:bg-gray-50">
              <ImagePlus className="h-4 w-4" /> {imagePreview && !removeImage ? 'Cambiar' : 'Subir'}
              <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImage} className="hidden" />
            </label>
            {imagePreview && !removeImage && (
              <button type="button" onClick={() => { setRemoveImage(true); setImageFile(null) }} className="text-sm text-red-600 hover:underline">
                Quitar
              </button>
            )}
          </div>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-1">Precios *</span>
          <div className="space-y-2">
            {variants.map((variant, index) => {
              const product = variant.fudo_product_id ? productsById[variant.fudo_product_id] : null
              return (
                <div key={index} className="border border-gray-200 rounded p-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      value={variant.label}
                      onChange={(e) => updateVariant(index, { label: e.target.value })}
                      placeholder={variants.length > 1 ? 'Etiqueta (ej: Porción)' : 'Etiqueta (opcional)'}
                      className="flex-1 min-w-[8rem] px-2 py-1.5 border border-gray-300 rounded text-sm"
                    />
                    {variant.fudo_product_id ? (
                      <span className="text-sm text-gray-800 px-2" title="Precio tomado de Fudo">
                        {formatPrice(product?.price ?? variant.price)} <span className="text-xs text-gray-500">de Fudo</span>
                      </span>
                    ) : (
                      <input
                        type="number"
                        min="0"
                        step="any"
                        value={variant.price}
                        onChange={(e) => updateVariant(index, { price: e.target.value })}
                        placeholder="Precio"
                        required
                        className="w-28 px-2 py-1.5 border border-gray-300 rounded text-sm"
                      />
                    )}
                    {variants.length > 1 && (
                      <button type="button" onClick={() => removeVariant(index)} className="p-1 text-gray-500 hover:text-red-600" aria-label="Quitar precio">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <div className="mt-1 text-xs">
                    {variant.fudo_product_id ? (
                      <button type="button" onClick={() => updateVariant(index, { fudo_product_id: null, fudo_status: null, price: product?.price ?? variant.price })} className="inline-flex items-center gap-1 text-gray-600 hover:text-gray-900">
                        <Unlink className="h-3 w-3" /> Vinculado a "{product?.name || variant.fudo_product_id}" — desvincular
                      </button>
                    ) : (
                      <button type="button" onClick={() => setPickerIndex(index)} className="inline-flex items-center gap-1 text-rose-700 hover:underline">
                        <Link2 className="h-3 w-3" /> Vincular con Fudo
                      </button>
                    )}
                    {variant.fudo_product_id && (variant.fudo_status === 'missing' || variant.fudo_status === 'inactive') && (
                      <p className="mt-1 text-amber-700">
                        {variant.fudo_status === 'missing'
                          ? 'Este producto ya no existe en Fudo — desvinculalo y cargá el precio a mano o vinculá otro.'
                          : 'Este producto está desactivado en Fudo.'}
                      </p>
                    )}
                  </div>
                  {pickerIndex === index && (
                    <FudoProductPicker
                      products={products}
                      allowedIds={ownFudoIds}
                      excludedIds={usedFudoIds(index)}
                      onCancel={() => setPickerIndex(null)}
                      onSelect={(p) => {
                        updateVariant(index, { fudo_product_id: p.fudo_id, fudo_status: null, price: p.price })
                        setPickerIndex(null)
                      }}
                    />
                  )}
                </div>
              )
            })}
          </div>
          <button type="button" onClick={() => setVariants([...variants, emptyVariant()])} className="mt-2 inline-flex items-center gap-1 text-sm text-rose-700 hover:underline">
            <Plus className="h-4 w-4" /> Agregar otro precio
          </button>
        </div>

        {tags.length > 0 && (
          <div>
            <span className="block text-sm font-medium text-gray-700 mb-1">Etiquetas</span>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => {
                const active = form.tag_ids.includes(tag.id)
                return (
                  <button
                    key={tag.id}
                    type="button"
                    onClick={() => toggleTag(tag.id)}
                    className={`text-sm px-2 py-1 rounded border ${active ? 'text-white' : 'text-gray-700 bg-white'}`}
                    style={active ? { backgroundColor: tag.color, borderColor: tag.color } : { borderColor: tag.color }}
                  >
                    {tag.name}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_featured} onChange={(e) => setForm({ ...form, is_featured: e.target.checked })} />
            Destacado ★
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_visible} onChange={(e) => setForm({ ...form, is_visible: e.target.checked })} />
            Visible en la carta
          </label>
        </div>
      </form>
    </ModalShell>
  )
}

export default MenuItemModal
