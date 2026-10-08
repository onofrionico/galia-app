import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, EyeOff, AlertTriangle, Sparkles } from 'lucide-react'
import menuService from '../services/menuService'
import MenuItemModal from '../components/menu/MenuItemModal'
import ItemPicker from '../components/menu/ItemPicker'
import { variantSummary, errorMessage } from '../utils/menuFormat'

const STATUS_TEXT = {
  inactive: 'El producto está desactivado en Fudo',
  missing: 'El producto ya no existe en Fudo',
}

const MenuInbox = () => {
  const [inbox, setInbox] = useState({ new_items: [], alerts: [] })
  const [menu, setMenu] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalItem, setModalItem] = useState(null)
  const [mergingId, setMergingId] = useState(null) // ítem nuevo que se está uniendo a otro

  const load = useCallback(async () => {
    try {
      const [inboxData, menuData] = await Promise.all([menuService.getInbox(), menuService.getMenu()])
      setInbox({ new_items: inboxData.new_items || [], alerts: inboxData.alerts || [] })
      setMenu(menuData)
      setError('')
    } catch (err) {
      setError(errorMessage(err, 'Error al cargar la bandeja'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const allItems = useMemo(
    () => (menu?.categories || []).flatMap((c) => c.items.map((i) => ({ ...i, categoryName: c.name }))),
    [menu],
  )
  const itemsById = useMemo(() => Object.fromEntries(allItems.map((i) => [i.id, i])), [allItems])

  const run = async (action, fallback) => {
    try {
      await action()
      setMergingId(null)
      await load()
    } catch (err) {
      setError(errorMessage(err, fallback))
    }
  }

  const show = (item) => run(() => menuService.updateItem(item.id, { is_visible: true }), 'Error al mostrar el ítem')
  const ignore = (item) => {
    if (!window.confirm(`¿Ignorar "${item.name}"? Se quita de la carta y no se vuelve a crear al sincronizar.`)) return
    run(() => menuService.ignoreItem(item.id), 'Error al ignorar el ítem')
  }
  const merge = (item, target) => {
    if (!window.confirm(`¿Unir "${item.name}" dentro de "${target.name}"? Sus precios pasan a ese ítem y este se elimina.`)) return
    run(() => menuService.mergeItem(target.id, item.id), 'Error al unir los ítems')
  }

  const closeAndReload = () => {
    setModalItem(null)
    load()
  }

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600" /></div>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/menu" className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" /> Volver a la carta
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-1">Nuevos y alertas</h1>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="bg-white rounded-lg border border-gray-200">
        <h2 className="font-semibold text-gray-900 p-4 border-b border-gray-100 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-rose-600" /> Nuevos por revisar ({inbox.new_items.length})
        </h2>
        <ul className="divide-y divide-gray-100">
          {inbox.new_items.length === 0 && <li className="p-4 text-sm text-gray-500">No hay ítems nuevos por revisar.</li>}
          {inbox.new_items.map((item) => (
            <li key={item.id} className="p-4">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {item.name}
                    {!item.is_visible && <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">oculto</span>}
                  </div>
                  <div className="text-sm text-gray-600">{item.category_name} · {variantSummary(item.variants)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => setModalItem(itemsById[item.id] || item)} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                    Editar
                  </button>
                  <button type="button" onClick={() => show(item)} className="px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700">
                    Mostrar en la carta
                  </button>
                  <button type="button" onClick={() => setMergingId(mergingId === item.id ? null : item.id)} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                    Unir con…
                  </button>
                  <button type="button" onClick={() => ignore(item)} className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 rounded hover:bg-gray-100">
                    <EyeOff className="h-4 w-4" /> Ignorar
                  </button>
                </div>
              </div>
              {mergingId === item.id && (
                <ItemPicker items={allItems} excludeId={item.id} onSelect={(target) => merge(item, target)} onCancel={() => setMergingId(null)} />
              )}
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white rounded-lg border border-gray-200">
        <h2 className="font-semibold text-gray-900 p-4 border-b border-gray-100 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600" /> Alertas ({inbox.alerts.length})
        </h2>
        <ul className="divide-y divide-gray-100">
          {inbox.alerts.length === 0 && <li className="p-4 text-sm text-gray-500">Sin alertas.</li>}
          {inbox.alerts.map((alert) => (
            <li key={`${alert.type}-${alert.id}`} className="p-4 flex flex-col sm:flex-row sm:items-center gap-2">
              {alert.type === 'category' ? (
                <>
                  <div className="flex-1 text-sm text-amber-700">
                    La categoría <strong>{alert.category_name}</strong> ya no existe en Fudo (quedó oculta).
                  </div>
                  <Link to="/menu" className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">Ver en la carta</Link>
                </>
              ) : (
                <>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">
                      {alert.item_name}{alert.label && <span className="text-gray-500"> · {alert.label}</span>}
                    </div>
                    <div className="text-sm text-amber-700">{STATUS_TEXT[alert.fudo_status]}{alert.fudo_name && ` ("${alert.fudo_name}")`}</div>
                  </div>
                  {itemsById[alert.item_id] && (
                    <button type="button" onClick={() => setModalItem(itemsById[alert.item_id])} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                      Editar ítem
                    </button>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      </section>

      {modalItem && menu && (
        <MenuItemModal
          item={modalItem}
          allItems={allItems}
          defaultCategoryId={modalItem.category_id}
          categories={menu.categories}
          tags={menu.tags}
          onClose={() => setModalItem(null)}
          onSaved={closeAndReload}
        />
      )}
    </div>
  )
}

export default MenuInbox
