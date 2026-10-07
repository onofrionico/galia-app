export default function SearchBar({ value, onChange }) {
  return (
    <label className="relative block">
      <span className="sr-only">Buscar en la carta</span>
      <svg aria-hidden="true" viewBox="0 0 20 20" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 fill-plum-light">
        <path d="M8.5 3a5.5 5.5 0 014.38 8.83l3.65 3.64-1.06 1.06-3.64-3.65A5.5 5.5 0 118.5 3zm0 1.5a4 4 0 100 8 4 4 0 000-8z" />
      </svg>
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Buscar… (ej: frutilla)"
        className="w-full rounded-full border border-plum/20 bg-white py-2.5 pl-9 pr-4 text-base text-plum placeholder:text-plum-light focus:outline-none focus:ring-2 focus:ring-coral"
      />
    </label>
  )
}
