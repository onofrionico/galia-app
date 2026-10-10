export default function Chip({ active = false, onClick, children, disabled = false }) {
  return (
    <button type="button" onClick={onClick} disabled={disabled} aria-pressed={active}
      className={`min-h-[40px] rounded-full border px-4 text-sm transition-colors disabled:opacity-40 ${
        active ? 'border-galia-plum bg-galia-plum text-galia-cream' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
      }`}>
      {children}
    </button>
  )
}
