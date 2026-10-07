import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Plus, EyeOff, AlertTriangle, Link2 } from 'lucide-react'
import menuService from '../services/menuService'
import MenuItemModal from '../components/menu/MenuItemModal'
import { formatPrice, errorMessage } from '../utils/menuFormat'

const STATUS_TEXT = {
  inactive: 'El producto está desactivado en Fudo',
  missing: 'El producto ya no existe en Fudo',
}

const MenuInbox = () => {
  const [inbox, setInbox] = useState({ unassigned: [], alerts: [] })
  const [menu, setMenu] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modal, setModal] = useState(null) // { item } | { prefill }
  const [attaching, setAttaching] = useState(null) // fudo_id que se está agregando a un ítem existente
  const [targetItemId, setTargetItemId] = useState('')

  const load = useCallback(async () => {
    try {
      const [inboxData, menuData] = await Promise.all([menuService.getInbox(), menuService.getMenu()])
      setInbox(inboxData)
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

  const ignore = async (product) => {
    try {
      await menuService.ignoreFudoProduct(product.fudo_id)
      load()
    } catch (err) {
      setError(errorMessage(err, 'Error al ignorar el producto'))
    }
  }

  const attachToItem = async (product) => {
    const item = itemsById[Number(targetItemId)]
    if (!item) return
    const variants = [
      ...item.variants.map((v) => ({ label: v.label, fudo_product_id: v.fudo_product_id, price: v.price })),
      { label: product.name, fudo_product_id: product.fudo_id, price: null },
    ]
    try {
      await menuService.updateItem(item.id, { variants })
      setAttaching(null)
      setTargetItemId('')
      load()
    } catch (err) {
      setError(errorMessage(err, 'Error al agregar el precio al ítem'))
    }
  }

  const closeAndReload = () => {
    setModal(null)
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
        <h1 className="text-2xl font-bold text-gray-900 mt-1">Sin asignar y alertas</h1>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="bg-white rounded-lg border border-gray-200">
        <h2 className="font-semibold text-gray-900 p-4 border-b border-gray-100 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600" /> Alertas ({inbox.alerts.length})
        </h2>
        <ul className="divide-y divide-gray-100">
          {inbox.alerts.length === 0 && <li className="p-4 text-sm text-gray-500">Sin alertas.</li>}
          {inbox.alerts.map((alert) => (
            <li key={alert.id} className="p-4 flex flex-col sm:flex-row sm:items-center gap-2">
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  {alert.item_name}{alert.label && <span className="text-gray-500"> · {alert.label}</span>}
                </div>
                <div className="text-sm text-amber-700">{STATUS_TEXT[alert.fudo_status]}{alert.fudo_name && ` ("${alert.fudo_name}")`}</div>
              </div>
              <button type="button" onClick={() => setModal({ item: itemsById[alert.item_id] })} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                Editar ítem
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white rounded-lg border border-gray-200">
        <h2 className="font-semibold text-gray-900 p-4 border-b border-gray-100">
          Productos de Fudo sin asignar ({inbox.unassigned.length})
        </h2>
        <ul className="divide-y divide-gray-100">
          {inbox.unassigned.length === 0 && <li className="p-4 text-sm text-gray-500">Todos los productos de Fudo están en la carta o ignorados.</li>}
          {inbox.unassigned.map((product) => (
            <li key={product.fudo_id} className="p-4 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{product.name}</div>
                  <div className="text-sm text-gray-600">{product.category_name || 'Sin categoría'} · {formatPrice(product.price)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setModal({ prefill: { name: product.name, variants: [{ label: null, fudo_product_id: product.fudo_id, price: product.price }] } })}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700"
                  >
                    <Plus className="h-4 w-4" /> Crear ítem
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAttaching(product.fudo_id); setTargetItemId('') }}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                  >
                    <Link2 className="h-4 w-4" /> Agregar a un ítem
                  </button>
                  <button type="button" onClick={() => ignore(product)} className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 rounded hover:bg-gray-100">
                    <EyeOff className="h-4 w-4" /> Ignorar
                  </button>
                </div>
              </div>
              {attaching === product.fudo_id && (
                <div className="flex flex-col sm:flex-row gap-2">
                  <select value={targetItemId} onChange={(e) => setTargetItemId(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm">
                    <option value="">Elegí el ítem…</option>
                    {allItems.map((i) => <option key={i.id} value={i.id}>{i.categoryName} · {i.name}</option>)}
                  </select>
                  <button type="button" disabled={!targetItemId} onClick={() => attachToItem(product)} className="px-3 py-2 text-sm bg-rose-600 text-white rounded disabled:opacity-50">
                    Agregar como precio
                  </button>
                  <button type="button" onClick={() => setAttaching(null)} className="px-3 py-2 text-sm text-gray-600">Cancelar</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>

      {modal && menu && (
        <MenuItemModal
          item={modal.item || null}
          prefill={modal.prefill}
          defaultCategoryId={modal.item?.category_id}
          categories={menu.categories}
          tags={menu.tags}
          onClose={() => setModal(null)}
          onSaved={closeAndReload}
        />
      )}
    </div>
  )
}

export default MenuInbox
