import { ArrowUp, ArrowDown, Trash2 } from 'lucide-react'

const inputClass = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-base text-gray-900'

const Field = ({ label, children }) => (
  <label className="block text-sm text-gray-600">
    {label}
    {children}
  </label>
)

export default function StepEditor({ step, index, total, onChange, onRemove, onMove }) {
  const num = (field, label) => (
    <Field label={label}>
      <input
        type="number"
        inputMode="numeric"
        min="0"
        value={step[field]}
        onChange={(e) => onChange({ [field]: e.target.value })}
        className={inputClass}
      />
    </Field>
  )

  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-white space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold text-galia-plum">Paso {index + 1}</span>
        <div className="flex gap-1">
          <button type="button" onClick={() => onMove(-1)} disabled={index === 0} aria-label="Subir paso"
            className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30">
            <ArrowUp className="w-5 h-5" />
          </button>
          <button type="button" onClick={() => onMove(1)} disabled={index === total - 1} aria-label="Bajar paso"
            className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30">
            <ArrowDown className="w-5 h-5" />
          </button>
          <button type="button" onClick={onRemove} aria-label="Quitar paso"
            className="p-2 rounded-lg text-red-600 hover:bg-red-50">
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>
      <Field label="Título (opcional)">
        <input type="text" value={step.title} onChange={(e) => onChange({ title: e.target.value })} className={inputClass} />
      </Field>
      <Field label="Indicación">
        <textarea rows={3} value={step.instruction} onChange={(e) => onChange({ instruction: e.target.value })} className={inputClass} />
      </Field>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {num('temperature_c', 'Temperatura (°C)')}
        {num('time_min', 'Tiempo mín. (min)')}
        {num('time_max', 'Tiempo máx. (min)')}
        <Field label="Punto">
          <input type="text" value={step.doneness} onChange={(e) => onChange({ doneness: e.target.value })}
            placeholder="Ej: dorado" className={inputClass} />
        </Field>
      </div>
      <Field label="Consejo (opcional)">
        <input type="text" value={step.tip} onChange={(e) => onChange({ tip: e.target.value })} className={inputClass} />
      </Field>
    </div>
  )
}
