export default function TagFilters({ tags, active, onToggle }) {
  if (tags.length === 0) return null
  return (
    <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      {tags.map((tag) => {
        const isActive = active.includes(tag.slug)
        return (
          <button
            key={tag.slug}
            type="button"
            aria-pressed={isActive}
            onClick={() => onToggle(tag.slug)}
            className="whitespace-nowrap rounded-full border px-3 py-1 text-sm font-medium transition-colors"
            style={isActive ? { backgroundColor: tag.color, borderColor: tag.color, color: '#fff' } : { borderColor: tag.color, color: tag.color }}
          >
            {tag.name}
          </button>
        )
      })}
    </div>
  )
}
