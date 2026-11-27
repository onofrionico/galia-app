// Marca de una apertura cargada con hora anterior.
export default function BackdatedTag({ title }) {
  return (
    <span title={title} className="ml-1 inline-block whitespace-nowrap rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
      cargada después
    </span>
  )
}
