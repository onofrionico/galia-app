import MenuItem from './MenuItem'
import { sectionId } from './CategoryNav'

export default function CategorySection({ category, tagsBySlug, onOpenPhoto }) {
  return (
    <section id={sectionId(category.slug)} data-slug={category.slug} className="scroll-mt-48 py-4">
      <h2 className="font-display text-3xl uppercase tracking-wide">{category.name}</h2>
      {category.description && <p className="mt-1 text-sm italic text-plum-light">{category.description}</p>}
      <ul className="mt-2 divide-y divide-plum/10">
        {category.items.map((item) => (
          <MenuItem key={item.id} item={item} tagsBySlug={tagsBySlug} onOpenPhoto={onOpenPhoto} />
        ))}
      </ul>
    </section>
  )
}
