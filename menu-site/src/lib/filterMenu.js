import { normalize } from './text'

function matchesQuery(item, needle) {
  if (!needle) return true
  return normalize(`${item.name} ${item.description || ''}`).includes(needle)
}

export function filterMenu(categories, { query = '', tagSlugs = [] } = {}) {
  const needle = normalize(query).trim()
  if (!needle && tagSlugs.length === 0) return categories
  return categories
    .map((category) => ({
      ...category,
      items: category.items.filter(
        (item) => matchesQuery(item, needle) && tagSlugs.every((slug) => item.tags.includes(slug)),
      ),
    }))
    .filter((category) => category.items.length > 0)
}
