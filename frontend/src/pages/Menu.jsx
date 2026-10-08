import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { RefreshCw, Upload, ExternalLink, AlertTriangle, Inbox } from 'lucide-react'
import menuService from '../services/menuService'
import CategoryCard from '../components/menu/CategoryCard'
import GroupsPanel from '../components/menu/GroupsPanel'
import CategoryFormModal from '../components/menu/CategoryFormModal'
import MenuItemModal from '../components/menu/MenuItemModal'
import MenuSettingsPanel from '../components/menu/MenuSettingsPanel'
import { swap, errorMessage, PUBLIC_MENU_URL } from '../utils/menuFormat'

const Menu = () => {
  const [menu, setMenu] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(null)
  const [tab, setTab] = useState('carta')
  const [categoryModal, setCategoryModal] = useState(null) // { category } | null
  const [itemModal, setItemModal] = useState(null) // { item, categoryId } | null

  const load = useCallback(async () => {
    try {
      setMenu(await menuService.getMenu())
      setError('')
    } catch (err) {
      setError(errorMessage(err, 'Error al cargar la carta'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const tagsById = useMemo(() => Object.fromEntries((menu?.tags || []).map((t) => [t.id, t])), [menu])

  const run = async (key, action, successMessage) => {
    setBusy(key)
    setError('')
    setNotice('')
    try {
      const result = await action()
      if (successMessage) setNotice(typeof successMessage === 'function' ? successMessage(result) : successMessage)
      await load()
    } catch (err) {
      setError(errorMessage(err, 'Ocurrió un error'))
    } finally {
      setBusy(null)
    }
  }

  const handleSync = () =>
    run('sync', menuService.syncFudo, (r) => `Fudo sincronizado: ${r.products} productos, ${r.price_changes} precios actualizados.`)

  const handlePublish = () => run('publish', menuService.publish, 'Carta publicada. Los clientes ya ven los cambios.')

  const sections = useMemo(() => {
    if (!menu) return []
    const byGroup = (groupId) => menu.categories.filter((c) => (c.group_id ?? null) === groupId)
    return [
      ...menu.groups.map((g) => ({ key: `g${g.id}`, groupId: g.id, title: g.name, categories: byGroup(g.id) })),
      { key: 'none', groupId: null, title: menu.groups.length ? 'Sin grupo' : null, categories: byGroup(null) },
    ].filter((s) => s.categories.length > 0 || s.groupId !== null)
  }, [menu])

  const moveCategory = (section, index, direction) => {
    const ids = swap(section.categories.map((c) => c.id), index, index + direction)
    if (ids) run('reorder', () => menuService.reorderCategories(section.groupId, ids))
  }

  const moveItem = (category, index, direction) => {
    const ids = swap(category.items.map((i) => i.id), index, index + direction)
    if (ids) run('reorder', () => menuService.reorderItems(category.id, ids))
  }

  const closeModalsAndReload = () => {
    setCategoryModal(null)
    setItemModal(null)
    load()
  }

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600" /></div>
  }

  if (!menu) {
    return (
      <div className="space-y-3">
        <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error || 'No se pudo cargar la carta'}</div>
        <button type="button" onClick={() => { setLoading(true); load() }} className="px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">
          Reintentar
        </button>
      </div>
    )
  }

  const status = menu.status
  const legacy = menu.categories.filter((c) => !c.fudo_category_id)
  const pendingCount = (status?.new_count || 0) + (status?.alerts_count || 0)

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Carta</h1>
          <p className="text-sm text-gray-600">
            {status?.last_published_at
              ? `Última publicación: ${formatDistanceToNow(new Date(status.last_published_at), { addSuffix: true, locale: es })}`
              : 'Todavía no se publicó'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a href={PUBLIC_MENU_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">
            <ExternalLink className="h-4 w-4" /> Ver carta
          </a>
          <button type="button" onClick={handleSync} disabled={!!busy} className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${busy === 'sync' ? 'animate-spin' : ''}`} /> Sincronizar Fudo
          </button>
          <button type="button" onClick={handlePublish} disabled={!!busy} className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-rose-600 text-white rounded hover:bg-rose-700 disabled:opacity-50">
            <Upload className="h-4 w-4" /> {busy === 'publish' ? 'Publicando…' : 'Publicar'}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {status?.has_unpublished_changes && (
          <span className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded bg-amber-50 text-amber-800">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> Hay cambios sin publicar
          </span>
        )}
        {pendingCount > 0 && (
          <Link to="/menu/inbox" className="inline-flex items-center gap-1 text-sm px-2 py-1 rounded bg-blue-50 text-blue-800 hover:bg-blue-100">
            <Inbox className="h-4 w-4" />
            {status.new_count > 0 && <>{status.new_count} nuevos por revisar</>}
            {status.alerts_count > 0 && <><AlertTriangle className="h-4 w-4 ml-1 text-amber-600" /> {status.alerts_count} alertas</>}
          </Link>
        )}
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      {notice && <div className="p-3 bg-green-50 text-green-700 rounded text-sm">{notice}</div>}

      <div className="flex gap-4 border-b border-gray-200">
        {[['carta', 'Carta'], ['grupos', 'Grupos'], ['config', 'Configuración']].map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`pb-2 text-sm font-medium border-b-2 ${tab === key ? 'border-rose-600 text-rose-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'carta' ? (
        <div className="space-y-5">
          {legacy.length > 0 && (
            <div className="p-3 bg-amber-50 text-amber-800 rounded text-sm">
              Hay {legacy.length} categorías creadas a mano (no vienen de Fudo). Mové sus ítems o borralas.
            </div>
          )}
          {sections.map((section) => (
            <div key={section.key} className="space-y-3">
              {section.title && (
                <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{section.title}</h2>
              )}
              {section.categories.map((category, index) => (
                <CategoryCard
                  key={category.id}
                  category={category}
                  index={index}
                  total={section.categories.length}
                  tagsById={tagsById}
                  groups={menu.groups}
                  onChangeGroup={(c, groupId) => run('group', () => menuService.updateCategory(c.id, { group_id: groupId }))}
                  onMove={(i, direction) => moveCategory(section, i, direction)}
                  onEdit={() => setCategoryModal({ category })}
                  onToggle={() => run('toggle', () => menuService.updateCategory(category.id, { is_visible: !category.is_visible }))}
                  onAddItem={() => setItemModal({ item: null, categoryId: category.id })}
                  onEditItem={(item) => setItemModal({ item, categoryId: category.id })}
                  onToggleItem={(item) => run('toggle', () => menuService.updateItem(item.id, { is_visible: !item.is_visible }))}
                  onMoveItem={moveItem}
                />
              ))}
            </div>
          ))}
        </div>
      ) : tab === 'grupos' ? (
        <GroupsPanel groups={menu.groups} onChanged={load} />
      ) : (
        <MenuSettingsPanel tags={menu.tags} onChanged={load} />
      )}

      {categoryModal && (
        <CategoryFormModal category={categoryModal.category} onClose={() => setCategoryModal(null)} onSaved={closeModalsAndReload} />
      )}
      {itemModal && (
        <MenuItemModal
          item={itemModal.item}
          defaultCategoryId={itemModal.categoryId}
          categories={menu.categories}
          tags={menu.tags}
          onClose={() => setItemModal(null)}
          onSaved={closeModalsAndReload}
        />
      )}
    </div>
  )
}

export default Menu
