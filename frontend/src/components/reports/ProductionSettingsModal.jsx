import { useEffect, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { reportsService } from '@/services/reportsService'

// Turnos del día y cuántas semanas / meses de feriados se comparan. Los turnos no se borran: se desactivan.
const ProductionSettingsModal = ({ onClose, onSaved }) => {
  const [form, setForm] = useState(null)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    reportsService.getProductionSettings()
      .then(setForm)
      .catch((err) => setError(err.response?.data?.error || 'No se pudo cargar la configuración'))
  }, [])

  const updatePart = (index, changes) =>
    setForm((prev) => ({
      ...prev,
      day_parts: prev.day_parts.map((part, i) => (i === index ? { ...part, ...changes } : part)),
    }))

  const addPart = () =>
    setForm((prev) => ({
      ...prev,
      day_parts: [...prev.day_parts, { name: '', start: '20:00', end: '22:00', is_active: true }],
    }))

  const save = async () => {
    setSaving(true)
    setError(null)
    try {
      await reportsService.updateProductionSettings({
        ...form,
        comparable_weeks: Number(form.comparable_weeks),
        holiday_window_months: Number(form.holiday_window_months),
      })
      onSaved()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo guardar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold text-gray-900">Turnos y comparación</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Cerrar">
            <X size={20} />
          </button>
        </div>

        {!form && !error && <p className="p-4 text-sm text-gray-500">Cargando…</p>}

        {form && (
          <div className="p-4 space-y-5">
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Turnos</p>
              {form.day_parts.map((part, index) => (
                <div key={part.id ?? `new-${index}`} className={`flex flex-wrap items-center gap-2 ${part.is_active ? '' : 'opacity-50'}`}>
                  <input
                    value={part.name}
                    onChange={(e) => updatePart(index, { name: e.target.value })}
                    placeholder="Nombre"
                    className="flex-1 min-w-[8rem] border rounded-lg px-2 py-1.5 text-sm"
                  />
                  <input type="time" value={part.start} onChange={(e) => updatePart(index, { start: e.target.value })}
                    className="border rounded-lg px-2 py-1.5 text-sm" aria-label="Inicio" />
                  <span className="text-gray-400">a</span>
                  <input type="time" value={part.end} onChange={(e) => updatePart(index, { end: e.target.value })}
                    className="border rounded-lg px-2 py-1.5 text-sm" aria-label="Fin" />
                  <label className="flex items-center gap-1 text-sm text-gray-600">
                    <input type="checkbox" checked={part.is_active}
                      onChange={(e) => updatePart(index, { is_active: e.target.checked })} />
                    Activo
                  </label>
                </div>
              ))}
              <button type="button" onClick={addPart}
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700">
                <Plus size={14} /> Agregar turno
              </button>
              <p className="text-xs text-gray-500">
                Cada venta cae en el turno de su hora de cierre (el inicio cuenta, el fin no). Lo que queda afuera
                aparece como “Fuera de turno”.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm text-gray-700">
                Semanas a comparar
                <input type="number" min="1" max="26" value={form.comparable_weeks}
                  onChange={(e) => setForm({ ...form, comparable_weeks: e.target.value })}
                  className="mt-1 w-full border rounded-lg px-2 py-1.5 text-sm" />
              </label>
              <label className="text-sm text-gray-700">
                Meses de feriados
                <input type="number" min="1" max="36" value={form.holiday_window_months}
                  onChange={(e) => setForm({ ...form, holiday_window_months: e.target.value })}
                  className="mt-1 w-full border rounded-lg px-2 py-1.5 text-sm" />
              </label>
            </div>
          </div>
        )}

        {error && <p className="mx-4 mb-2 text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2 p-4 border-t">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">
            Cancelar
          </button>
          <button type="button" onClick={save} disabled={!form || saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProductionSettingsModal
