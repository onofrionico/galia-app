import { useEffect, useRef, useState } from 'react'
import { activeSectionIndex } from '../lib/activeSection'
import { centeredScrollLeft } from '../lib/chipScroll'

const CLICK_LOCK_MS = 700

export default function CategoryNav({ entries }) {
  const [storedSlug, setStoredSlug] = useState(entries[0]?.slug)
  const navRef = useRef(null)
  const chipRefs = useRef({})
  const lockUntil = useRef(0)

  const activeSlug = entries.some((e) => e.slug === storedSlug) ? storedSlug : entries[0]?.slug

  useEffect(() => {
    if (entries.length === 0) return undefined
    let frame = 0

    const update = () => {
      frame = 0
      if (performance.now() < lockUntil.current) return
      const bar = navRef.current?.closest('.sticky')
      const threshold = (bar ? bar.getBoundingClientRect().bottom : 0) + 8
      const tops = entries.map((e) => {
        const el = document.getElementById(e.targetId)
        return el ? el.getBoundingClientRect().top : Infinity
      })
      setStoredSlug(entries[activeSectionIndex(tops, threshold)].slug)
    }
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update)
    }

    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      if (frame) cancelAnimationFrame(frame)
    }
  }, [entries])

  // Centra el chip activo moviendo solo la barra. No usar scrollIntoView: en iPhone también mueve la página
  // (calcula la posición de la barra sticky como si no estuviera pegada) y no deja volver al principio.
  useEffect(() => {
    const nav = navRef.current
    const chip = chipRefs.current[activeSlug]
    if (!nav || !chip) return
    nav.scrollTo({
      left: centeredScrollLeft({
        chipLeft: chip.offsetLeft, chipWidth: chip.offsetWidth, navWidth: nav.clientWidth, scrollWidth: nav.scrollWidth,
      }),
      behavior: 'smooth',
    })
  }, [activeSlug])

  const onChipClick = (slug) => {
    lockUntil.current = performance.now() + CLICK_LOCK_MS
    setStoredSlug(slug)
  }

  return (
    <nav ref={navRef} aria-label="Categorías" className="no-scrollbar relative -mx-4 flex gap-2 overflow-x-auto px-4">
      {entries.map((e) => (
        <a
          key={e.slug}
          ref={(el) => { chipRefs.current[e.slug] = el }}
          href={`#${e.targetId}`}
          onClick={() => onChipClick(e.slug)}
          className={`whitespace-nowrap rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            e.slug === activeSlug ? 'bg-plum text-cream' : 'bg-plum/5 text-plum'
          }`}
        >
          {e.label}
        </a>
      ))}
    </nav>
  )
}
