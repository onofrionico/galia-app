import { useState, useEffect } from 'react'
import { Plus, Trash2, Save } from 'lucide-react'
import menuService from '../../services/menuService'
import { errorMessage } from '../../utils/menuFormat'

const TagRow = ({ tag, onChanged, onError }) => {
  const [name, setName] = useState(tag.name)
  const [color, setColor] = useState(tag.color)
  const dirty = name !== tag.name || color !== tag.color

  const save = async () => {
    try {
      await menuService.updateTag(tag.id, { name, color })
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al guardar la etiqueta'))
    }
  }

  const remove = async () => {
    if (!window.confirm(`¿Borrar la etiqueta "${tag.name}"? Se quita de todos los ítems.`)) return
    try {
      await menuService.deleteTag(tag.id)
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al borrar la etiqueta'))
    }
  }

  return (
    <li className="flex items-center gap-2 py-2">
      <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="h-8 w-10 border border-gray-300 rounded" />
      <input value={name} onChange={(e) => setName(e.target.value)} className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
      {dirty && (
        <button type="button" onClick={save} className="p-1.5 text-rose-700 hover:bg-rose-50 rounded" aria-label="Guardar etiqueta">
          <Save className="h-4 w-4" />
        </button>
      )}
      <button type="button" onClick={remove} className="p-1.5 text-gray-500 hover:text-red-600 rounded" aria-label="Borrar etiqueta">
        <Trash2 className="h-4 w-4" />
      </button>
    </li>
  )
}

const MenuSettingsPanel = ({ tags, onChanged }) => {
  const [settings, setSettings] = useState({ footer_text: '', instagram: '' })
  const [newTag, setNewTag] = useState({ name: '', color: '#5C2E46' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    menuService.getSettings().then(setSettings).catch((err) => setError(errorMessage(err, 'Error al cargar la configuración')))
  }, [])

  const saveSettings = async (e) => {
    e.preventDefault()
    setError('')
    try {
      setSettings(await menuService.updateSettings(settings))
      setNotice('Configuración guardada. Publicá la carta para que se vea.')
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al guardar la configuración'))
    }
  }

  const addTag = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await menuService.createTag(newTag)
      setNewTag({ name: '', color: '#5C2E46' })
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al crear la etiqueta'))
    }
  }

  return (
    <div className="space-y-6">
      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      {notice && <div className="p-3 bg-green-50 text-green-700 rounded text-sm">{notice}</div>}

      <section className="bg-white rounded-lg border border-gray-200 p-4">
        <h2 className="font-semibold text-gray-900 mb-2">Etiquetas</h2>
        <ul className="divide-y divide-gray-100">
          {tags.map((tag) => <TagRow key={`${tag.id}-${tag.name}-${tag.color}`} tag={tag} onChanged={onChanged} onError={setError} />)}
        </ul>
        <form onSubmit={addTag} className="flex items-center gap-2 mt-3">
          <input type="color" value={newTag.color} onChange={(e) => setNewTag({ ...newTag, color: e.target.value })} className="h-8 w-10 border border-gray-300 rounded" />
          <input value={newTag.name} onChange={(e) => setNewTag({ ...newTag, name: e.target.value })} placeholder="Nueva etiqueta (ej: Sin TACC)" required className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
          <button type="submit" className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700">
            <Plus className="h-4 w-4" /> Agregar
          </button>
        </form>
      </section>

      <form onSubmit={saveSettings} className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h2 className="font-semibold text-gray-900">Textos de la carta</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mensaje al pie</label>
          <textarea value={settings.footer_text} onChange={(e) => setSettings({ ...settings, footer_text: e.target.value })} rows={4} className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Instagram</label>
          <input value={settings.instagram} onChange={(e) => setSettings({ ...settings, instagram: e.target.value })} placeholder="@galia" className="w-full px-3 py-2 border border-gray-300 rounded" />
        </div>
        <button type="submit" className="px-4 py-2 bg-rose-600 text-white rounded hover:bg-rose-700">Guardar textos</button>
      </form>
    </div>
  )
}

export default MenuSettingsPanel
