import { useEffect, useRef, useState } from 'react'

export const sectionId = (slug) => `cat-${slug}`

export default function CategoryNav({ categories }) {
  const [activeSlug, setActiveSlug] = useState(categories[0]?.slug)
  const chipRefs = useRef({})

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting)
        if (visible.length > 0) setActiveSlug(visible[0].target.dataset.slug)
      },
      { rootMargin: '-180px 0px -60% 0px' },
    )
    categories.forEach((c) => {
      const el = document.getElementById(sectionId(c.slug))
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [categories])

  useEffect(() => {
    chipRefs.current[activeSlug]?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
  }, [activeSlug])

  return (
    <nav aria-label="Categorías" className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      {categories.map((c) => (
        <a
          key={c.slug}
          ref={(el) => { chipRefs.current[c.slug] = el }}
          href={`#${sectionId(c.slug)}`}
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
