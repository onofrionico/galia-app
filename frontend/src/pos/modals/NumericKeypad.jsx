import { Delete } from 'lucide-react'

const KEYS = ['7', '8', '9', '4', '5', '6', '1', '2', '3', ',', '0', 'back']

export default function NumericKeypad({ onKey }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {KEYS.map((key) => (
        <button key={key} type="button" onClick={() => onKey(key)} aria-label={key === 'back' ? 'Borrar' : key}
          className="min-h-[52px] rounded-lg border border-gray-200 bg-gray-50 text-xl font-medium hover:bg-gray-100">
          {key === 'back' ? <Delete size={20} className="mx-auto" /> : key}
        </button>
      ))}
    </div>
  )
}
