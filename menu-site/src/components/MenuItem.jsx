import { formatVariant } from '../lib/format'

function Tags({ slugs, tagsBySlug }) {
  if (slugs.length === 0) return null
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {slugs.map((slug) => tagsBySlug[slug] && (
        <span key={slug} className="rounded-full px-2 py-0.5 text-xs font-medium text-white" style={{ backgroundColor: tagsBySlug[slug].color }}>
          {tagsBySlug[slug].name}
        </span>
      ))}
    </div>
  )
}

export default function MenuItem({ item, tagsBySlug, onOpenPhoto }) {
  const prices = item.variants.map(formatVariant).join(' · ')
  return (
    <li className={`flex gap-3 py-3 ${item.featured ? 'rounded-xl bg-white/70 px-3' : ''}`}>
      {item.image && (
        <button type="button" onClick={() => onOpenPhoto(item)} className="flex-shrink-0" aria-label={`Ver foto de ${item.name}`}>
          <img src={item.image} alt="" loading="lazy" className="h-20 w-20 rounded-lg object-cover" />
        </button>
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="font-bold leading-tight">
            {item.featured && <span className="mr-1 text-coral" role="img" aria-label="Destacado">★</span>}
            {item.name}
          </h3>
          {item.variants.length === 1 && <span className="whitespace-nowrap font-bold">{prices}</span>}
        </div>
        {item.description && <p className="mt-0.5 text-sm text-plum-light">{item.description}</p>}
        {item.variants.length > 1 && <p className="mt-1 text-sm font-bold">{prices}</p>}
        <Tags slugs={item.tags} tagsBySlug={tagsBySlug} />
      </div>
    </li>
  )
}
