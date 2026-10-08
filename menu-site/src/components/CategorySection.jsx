import MenuItem from './MenuItem'

export default function CategorySection({ category, nested = false, tagsBySlug, onOpenPhoto }) {
  const Title = nested ? 'h3' : 'h2'
  const titleClass = nested
    ? 'mt-4 font-display text-2xl uppercase tracking-wide text-plum-light'
    : 'font-display text-3xl uppercase tracking-wide'
  return (
    <section id={`cat-${category.slug}`} data-slug={category.slug} className="scroll-mt-48 py-4">
      {category.show_title && <Title className={titleClass}>{category.name}</Title>}
      {category.description && <p className="mt-1 text-sm italic text-plum-light">{category.description}</p>}
      <ul className="mt-2 divide-y divide-plum/10">
        {category.items.map((item) => (
          <MenuItem key={item.id} item={item} tagsBySlug={tagsBySlug} onOpenPhoto={onOpenPhoto} />
        ))}
      </ul>
    </section>
  )
}
