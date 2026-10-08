import { useEffect, useRef, useState } from 'react'
import { activeSectionIndex } from '../lib/activeSection'

export const sectionId = (slug) => `cat-${slug}`

const CLICK_LOCK_MS = 700

export default function CategoryNav({ categories }) {
  const [storedSlug, setStoredSlug] = useState(categories[0]?.slug)
  const navRef = useRef(null)
  const chipRefs = useRef({})
  const lockUntil = useRef(0)

  const activeSlug = categories.some((c) => c.slug === storedSlug) ? storedSlug : categories[0]?.slug

  useEffect(() => {
    if (categories.length === 0) return undefined
    let frame = 0

    const update = () => {
      frame = 0
      if (performance.now() < lockUntil.current) return
      const bar = navRef.current?.closest('.sticky')
      const threshold = (bar ? bar.getBoundingClientRect().bottom : 0) + 8
      const tops = categories.map((c) => {
        const el = document.getElementById(sectionId(c.slug))
        return el ? el.getBoundingClientRect().top : Infinity
      })
      setStoredSlug(categories[activeSectionIndex(tops, threshold)].slug)
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
  }, [categories])

  useEffect(() => {
    chipRefs.current[activeSlug]?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
  }, [activeSlug])

  const onChipClick = (slug) => {
    lockUntil.current = performance.now() + CLICK_LOCK_MS
    setStoredSlug(slug)
  }

  return (
    <nav ref={navRef} aria-label="Categorías" className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      {categories.map((c) => (
        <a
          key={c.slug}
          ref={(el) => { chipRefs.current[c.slug] = el }}
          href={`#${sectionId(c.slug)}`}
          onClick={() => onChipClick(c.slug)}
          className={`whitespace-nowrap rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            c.slug === activeSlug ? 'bg-plum text-cream' : 'bg-plum/5 text-plum'
          }`}
        >
          {c.name}
        </a>
      ))}
    </nav>
  )
}
