import { normalize } from './text'

function matchesQuery(item, needle) {
  if (!needle) return true
  return normalize(`${item.name} ${item.description || ''}`).includes(needle)
}

export function filterMenu(groups, { query = '', tagSlugs = [] } = {}) {
  const needle = normalize(query).trim()
  if (!needle && tagSlugs.length === 0) return groups
  return groups
    .map((group) => ({
      ...group,
      categories: group.categories
        .map((category) => ({
          ...category,
          items: category.items.filter(
            (item) => matchesQuery(item, needle) && tagSlugs.every((slug) => item.tags.includes(slug)),
          ),
        }))
        .filter((category) => category.items.length > 0),
    }))
    .filter((group) => group.categories.length > 0)
}
