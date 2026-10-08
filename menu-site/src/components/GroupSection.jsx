import CategorySection from './CategorySection'

export default function GroupSection({ group, tagsBySlug, onOpenPhoto }) {
  return (
    <section id={`grupo-${group.slug}`} className="scroll-mt-48 py-4">
      {group.name && <h2 className="font-display text-4xl uppercase tracking-wide">{group.name}</h2>}
      {group.categories.map((category) => (
        <CategorySection key={category.slug} category={category} nested={Boolean(group.name)} tagsBySlug={tagsBySlug} onOpenPhoto={onOpenPhoto} />
      ))}
    </section>
  )
}
