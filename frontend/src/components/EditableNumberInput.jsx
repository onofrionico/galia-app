import { useState } from 'react'

// Input numérico con borrador local: guarda al perder foco o con Enter,
// solo si el valor cambió. `onCommit(raw)` devuelve una promesa con true si
// se guardó (el valor nuevo llega por `value`) o false si hay que revertir.
const EditableNumberInput = ({ value, onCommit, className = '', step = '0.1', disabled = false }) => {
  const [draft, setDraft] = useState(String(value ?? ''))
  const [prevValue, setPrevValue] = useState(value)
  const [saving, setSaving] = useState(false)

  if (value !== prevValue) {
    setPrevValue(value)
    setDraft(String(value ?? ''))
  }

  const commit = async () => {
    const raw = draft.trim()
    if (raw !== '' && Number(raw) === Number(value)) {
      setDraft(String(value ?? ''))
      return
    }
    setSaving(true)
    const ok = await onCommit(raw)
    setSaving(false)
    if (!ok) setDraft(String(value ?? ''))
  }

  return (
    <span className="inline-flex flex-col items-end">
      <input
        type="number"
        value={draft}
        step={step}
        min="0"
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') e.currentTarget.blur()
        }}
        disabled={disabled}
        className={className}
      />
      {saving && <span className="text-xs text-gray-500">guardando…</span>}
    </span>
  )
}

export default EditableNumberInput
