import { useEffect, useMemo, useState } from 'react'
import { loadMenu } from './lib/loadMenu'
import { filterMenu } from './lib/filterMenu'
import Header from './components/Header'
import SearchBar from './components/SearchBar'
import TagFilters from './components/TagFilters'
import CategoryNav from './components/CategoryNav'
import GroupSection from './components/GroupSection'
import Lightbox from './components/Lightbox'
import Footer from './components/Footer'
import MenuMessage from './components/MenuMessage'

const MENU_URL = import.meta.env.VITE_MENU_URL || (import.meta.env.DEV ? '/menu.sample.json' : '')

export default function App() {
  const [state, setState] = useState({ status: 'loading', menu: null })
  const [query, setQuery] = useState('')
  const [activeTags, setActiveTags] = useState([])
  const [photoItem, setPhotoItem] = useState(null)

  useEffect(() => {
    loadMenu({ url: MENU_URL })
      .then(({ menu }) => setState({ status: 'ready', menu }))
      .catch(() => setState({ status: 'error', menu: null }))
  }, [])

  const menu = state.menu
  const groups = useMemo(
    () => (menu ? filterMenu(menu.groups, { query, tagSlugs: activeTags }) : []),
    [menu, query, activeTags],
  )
  const navEntries = useMemo(() => {
    if (groups.length === 1 && groups[0].name === null) {
      return groups[0].categories.map((c) => ({ slug: c.slug, label: c.name, targetId: `cat-${c.slug}` }))
    }
    return groups.map((g) => ({ slug: g.slug, label: g.name, targetId: `grupo-${g.slug}` }))
  }, [groups])
  const tagsBySlug = useMemo(() => Object.fromEntries((menu?.tags || []).map((t) => [t.slug, t])), [menu])

  const toggleTag = (slug) =>
    setActiveTags((tags) => (tags.includes(slug) ? tags.filter((t) => t !== slug) : [...tags, slug]))

  return (
    <div className="mx-auto min-h-screen max-w-xl">
      <Header />
      {state.status === 'loading' && <MenuMessage title="Cargando la carta…" />}
      {state.status === 'error' && (
        <MenuMessage title="No pudimos cargar la carta">Pedile la carta a nuestro equipo 💛</MenuMessage>
      )}
      {state.status === 'ready' && (
        <>
          <div className="sticky top-0 z-10 space-y-2 bg-cream/95 px-4 pb-3 pt-2 backdrop-blur">
            <SearchBar value={query} onChange={setQuery} />
            <TagFilters tags={menu.tags} active={activeTags} onToggle={toggleTag} />
            <CategoryNav entries={navEntries} />
          </div>
          <main className="px-4">
            {groups.length === 0 ? (
              <MenuMessage title="Sin resultados">Probá con otra palabra o sacá algún filtro.</MenuMessage>
            ) : (
              groups.map((group) => (
                <GroupSection key={group.slug} group={group} tagsBySlug={tagsBySlug} onOpenPhoto={setPhotoItem} />
              ))
            )}
          </main>
          <Footer settings={menu.settings} />
        </>
      )}
      {photoItem && <Lightbox item={photoItem} onClose={() => setPhotoItem(null)} />}
    </div>
  )
}
