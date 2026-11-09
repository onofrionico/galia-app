const FLOWERS = ['/brand/flower-coral.png', '/brand/flower-lime.png']

// Flor que representa a cada categoría en los productos sin foto. Se calcula sobre la carta
// completa, así una categoría conserva su color aunque la búsqueda oculte a las demás.
export function flowerByCategory(groups) {
  const categories = groups.flatMap((group) => group.categories)
  return Object.fromEntries(categories.map((category, index) => [category.slug, FLOWERS[index % FLOWERS.length]]))
}
