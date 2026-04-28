import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Building2, ArrowLeft, Link, Save, Trash2 } from 'lucide-react'
import suppliersService from '@/services/suppliersService'

const TABS = ['Contacto', 'Historial de compras']

export default function SupplierDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [supplier, setSupplier] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [expenses, setExpenses] = useState([])
  const [expTotal, setExpTotal] = useState(0)
  const [tab, setTab] = useState('Contacto')
  const [form, setForm] = useState({})
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [linking, setLinking] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')

  const loadSupplier = async () => {
    try {
      const data = await suppliersService.getSupplier(id)
      setSupplier(data)
      setForm(data)
    } catch {
      setError('No se encontró el proveedor')
    } finally {
      setLoading(false)
    }
  }

  const loadExpenses = async () => {
    try {
      const params = {}
      if (fechaDesde) params.fecha_desde = fechaDesde
      if (fechaHasta) params.fecha_hasta = fechaHasta
      const data = await suppliersService.getSupplierExpenses(id, params)
      setExpenses(data.expenses)
      setExpTotal(data.total)
    } catch {
      setError('Error cargando historial')
    }
  }

  const loadAnalytics = async () => {
    try {
      const params = {}
      if (fechaDesde) params.fecha_desde = fechaDesde
      if (fechaHasta) params.fecha_hasta = fechaHasta
      const data = await suppliersService.getSupplierAnalytics(id, params)
      setAnalytics(data)
    } catch {
      setError('Error cargando analítica')
    }
  }

  useEffect(() => { loadSupplier() }, [id])
  useEffect(() => {
    if (tab === 'Historial de compras') {
      loadExpenses()
      loadAnalytics()
    }
  }, [tab, fechaDesde, fechaHasta, id])

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await suppliersService.updateSupplier(id, form)
      setSupplier(updated)
      setEditing(false)
    } catch {
      setError('Error actualizando proveedor')
    } finally {
      setSaving(false)
    }
  }

  const handleLink = async () => {
    setLinking(true)
    try {
      const result = await suppliersService.linkExpenses(id)
      alert(`Se vincularon ${result.linked} gastos`)
      loadExpenses()
      loadAnalytics()
    } catch {
      setError('Error vinculando gastos')
    } finally {
      setLinking(false)
    }
  }

  const handleDeactivate = async () => {
    if (!confirm('¿Desactivar este proveedor?')) return
    try {
      await suppliersService.deactivateSupplier(id)
      navigate('/suppliers')
    } catch {
      setError('Error desactivando proveedor')
    }
  }

  if (loading) return <div className="p-6 text-sm text-gray-500">Cargando...</div>
  if (error && !supplier) return <div className="p-6 text-sm text-red-600">{error}</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={() => navigate('/suppliers')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Volver a proveedores
      </button>

      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{supplier.name}</h1>
            {supplier.cuit && <p className="text-sm text-gray-500">CUIT: {supplier.cuit}</p>}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleLink}
            disabled={linking}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <Link className="w-4 h-4" />
            {linking ? 'Vinculando...' : 'Vincular gastos'}
          </button>
          <button
            onClick={handleDeactivate}
            className="flex items-center gap-2 px-3 py-2 border border-red-200 rounded-lg text-sm text-red-600 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4" />
            Desactivar
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === t
                ? 'border-orange-500 text-orange-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Contacto' && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Datos de contacto</h2>
            {!editing ? (
              <button onClick={() => setEditing(true)} className="text-sm text-orange-600 hover:text-orange-700 font-medium">Editar</button>
            ) : (
              <div className="flex gap-2">
                <button onClick={handleSave} disabled={saving} className="flex items-center gap-1 text-sm text-white bg-orange-600 hover:bg-orange-700 px-3 py-1.5 rounded-lg disabled:opacity-50">
                  <Save className="w-3.5 h-3.5" />
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
                <button onClick={() => { setEditing(false); setForm(supplier) }} className="text-sm text-gray-600 hover:text-gray-800 px-3 py-1.5 border border-gray-300 rounded-lg">Cancelar</button>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { key: 'name', label: 'Nombre *', required: true },
              { key: 'cuit', label: 'CUIT' },
              { key: 'email', label: 'Email', type: 'email' },
              { key: 'phone', label: 'Teléfono' },
            ].map(({ key, label, type = 'text', required }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
                {editing ? (
                  <input
                    type={type}
                    required={required}
                    value={form[key] || ''}
                    onChange={e => setForm({ ...form, [key]: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                ) : (
                  <p className="text-sm text-gray-900">{supplier[key] || <span className="text-gray-400">—</span>}</p>
                )}
              </div>
            ))}
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-gray-500 mb-1">Notas</label>
              {editing ? (
                <textarea
                  value={form.notes || ''}
                  onChange={e => setForm({ ...form, notes: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              ) : (
                <p className="text-sm text-gray-900">{supplier.notes || <span className="text-gray-400">—</span>}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === 'Historial de compras' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Desde</label>
              <input type="date" value={fechaDesde} onChange={e => setFechaDesde(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Hasta</label>
              <input type="date" value={fechaHasta} onChange={e => setFechaHasta(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500" />
            </div>
          </div>

          {analytics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Total período', value: `$${analytics.total_periodo.toLocaleString('es-AR', { maximumFractionDigits: 0 })}` },
                { label: 'Promedio mensual', value: `$${analytics.promedio_mensual.toLocaleString('es-AR', { maximumFractionDigits: 0 })}` },
                { label: 'Última compra', value: analytics.ultima_compra ? new Date(analytics.ultima_compra + 'T00:00:00').toLocaleDateString('es-AR') : '—' },
                { label: 'Total gastos', value: expTotal },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">{label}</p>
                  <p className="text-lg font-bold text-gray-900">{value}</p>
                </div>
              ))}
            </div>
          )}

          {analytics && analytics.por_categoria.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Por categoría</h3>
              <div className="space-y-2">
                {analytics.por_categoria.map(c => (
                  <div key={c.categoria} className="flex justify-between text-sm">
                    <span className="text-gray-600">{c.categoria}</span>
                    <span className="font-medium text-gray-900">${c.total.toLocaleString('es-AR', { maximumFractionDigits: 0 })}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {expenses.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">No hay gastos vinculados</div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Fecha</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Categoría</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Comentario</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Importe</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {expenses.map(e => (
                    <tr key={e.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-700">
                        {new Date(e.fecha + 'T00:00:00').toLocaleDateString('es-AR')}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{e.category_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{e.comentario || '—'}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">
                        ${e.importe.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
