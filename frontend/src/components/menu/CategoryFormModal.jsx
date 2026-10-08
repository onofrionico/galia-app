import { useState } from 'react'
import ModalShell from './ModalShell'
import menuService from '../../services/menuService'
import { errorMessage } from '../../utils/menuFormat'

const CategoryFormModal = ({ category, onClose, onSaved }) => {
  const isManual = !category.fudo_category_id
  const [form, setForm] = useState({
    name: category.name || '',
    description: category.description || '',
    is_visible: category.is_visible ?? true,
    show_title: category.show_title ?? true,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { description: form.description, is_visible: form.is_visible, show_title: form.show_title }
      if (isManual) payload.name = form.name
      await menuService.updateCategory(category.id, payload)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al guardar la categoría'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`¿Borrar la categoría "${category.name}"?`)) return
    setSaving(true)
    setError('')
    try {
      await menuService.deleteCategory(category.id)
      onSaved()
    } catch (err) {
      setError(errorMessage(err, 'Error al borrar la categoría'))
      setSaving(false)
    }
  }

  return (
    <ModalShell
      title="Editar categoría"
      onClose={onClose}
      footer={
        <>
          {isManual && (
            <button type="button" onClick={handleDelete} disabled={saving} className="mr-auto px-4 py-2 text-red-600 hover:bg-red-50 rounded">
              Borrar
            </button>
          )}
          <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Cancelar</button>
          <button type="submit" form="category-form" disabled={saving} className="px-4 py-2 bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </>
      }
    >
      <form id="category-form" onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            readOnly={!isManual}
            className={`w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-rose-500 ${isManual ? '' : 'bg-gray-50 text-gray-600'}`}
          />
          {!isManual && <p className="text-xs text-gray-500 mt-1">Viene de Fudo</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nota (se muestra bajo el título)</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2}
            placeholder="Ej: Contanos si lo preferís con azúcar, stevia o sin nada"
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-rose-500"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={form.is_visible} onChange={(e) => setForm({ ...form, is_visible: e.target.checked })} />
          Visible en la carta
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={form.show_title} onChange={(e) => setForm({ ...form, show_title: e.target.checked })} />
          Mostrar título en la carta
        </label>
      </form>
    </ModalShell>
  )
}

export default CategoryFormModal
