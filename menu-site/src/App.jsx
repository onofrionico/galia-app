import { useEffect, useMemo, useState } from 'react'
import { loadMenu } from './lib/loadMenu'
import { filterMenu } from './lib/filterMenu'
import Header from './components/Header'
import SearchBar from './components/SearchBar'
import TagFilters from './components/TagFilters'
import CategoryNav from './components/CategoryNav'
import CategorySection from './components/CategorySection'
import Lightbox from './components/Lightbox'
import Footer from './components/Footer'
import MenuMessage from './components/MenuMessage'

const MENU_URL = import.meta.env.VITE_MENU_URL || '/menu.sample.json'

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
  const categories = useMemo(
    () => (menu ? filterMenu(menu.categories, { query, tagSlugs: activeTags }) : []),
    [menu, query, activeTags],
  )
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
            <CategoryNav categories={categories} />
          </div>
          <main className="px-4">
            {categories.length === 0 ? (
              <MenuMessage title="Sin resultados">Probá con otra palabra o sacá algún filtro.</MenuMessage>
            ) : (
              categories.map((category) => (
                <CategorySection key={category.slug} category={category} tagsBySlug={tagsBySlug} onOpenPhoto={setPhotoItem} />
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
