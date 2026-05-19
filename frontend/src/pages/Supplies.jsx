import { useState, useEffect } from 'react'
import { Plus, Trash2, Edit2, X } from 'lucide-react'
import suppliesService from '../services/suppliesService'

 const UNIT_OPTIONS = ['unidades', 'kg', 'g', 'L', 'ml', 'caja', 'paquete']

const Supplies = () => {
  const [supplies, setSupplies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    unit: '',
    stock_quantity: 0,
    min_stock: 0,
  })
  const [showPrices, setShowPrices] = useState(null)
  const [priceData, setPriceData] = useState({
    price: '',
    supplier: '',
    notes: '',
  })

  useEffect(() => {
    fetchSupplies()
  }, [])

  const fetchSupplies = async () => {
    try {
      const res = await suppliesService.getSupplies({ include_inactive: false })
      setSupplies(res.supplies || [])
      setLoading(false)
    } catch (err) {
      setError('Error al cargar insumos')
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingId) {
        await suppliesService.updateSupply(editingId, formData)
      } else {
        await suppliesService.createSupply(formData)
      }
      await fetchSupplies()
      setShowForm(false)
      setEditingId(null)
      setFormData({ name: '', unit: '', stock_quantity: 0, min_stock: 0 })
    } catch (err) {
      setError(err.response?.data?.error || 'Error al guardar')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este insumo?')) return
    try {
      await suppliesService.deleteSupply(id)
      await fetchSupplies()
    } catch (err) {
      setError('Error al eliminar')
    }
  }

  const handleAddPrice = async (e) => {
    e.preventDefault()
    if (!showPrices || !priceData.price) return
    try {
      await suppliesService.addPrice(showPrices, {
        price: parseFloat(priceData.price),
        supplier: priceData.supplier,
        notes: priceData.notes,
      })
      setPriceData({ price: '', supplier: '', notes: '' })
      const res = await suppliesService.getSupply(showPrices)
      setSupplies(supplies.map(s => s.id === showPrices ? res : s))
    } catch (err) {
      setError('Error al registrar precio')
    }
  }

  const handleEdit = (supply) => {
    setFormData({
      name: supply.name,
      unit: supply.unit,
      stock_quantity: supply.stock_quantity,
      min_stock: supply.min_stock,
    })
    setEditingId(supply.id)
    setShowForm(true)
  }

  if (loading) return <div className="p-6">Cargando...</div>

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Gestión de Insumos</h1>
        <button
          onClick={() => {
            setShowForm(true)
            setEditingId(null)
            setFormData({ name: '', unit: '', stock_quantity: 0, min_stock: 0 })
          }}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 flex items-center gap-2"
        >
          <Plus size={20} /> Nuevo Insumo
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {showForm && (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">
            {editingId ? 'Editar Insumo' : 'Nuevo Insumo'}
          </h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nombre</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border rounded px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Unidad</label>
              <select
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                className="w-full border rounded px-3 py-2"
                required
              >
                <option value="" disabled>Seleccionar unidad</option>
                {formData.unit && !UNIT_OPTIONS.includes(formData.unit) && (
                  <option value={formData.unit}>{formData.unit}</option>
                )}
                {UNIT_OPTIONS.map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Stock Actual</label>
              <input
                type="number"
                value={formData.stock_quantity || ''}
                onChange={(e) => setFormData({ ...formData, stock_quantity: e.target.value === '' ? 0 : parseFloat(e.target.value) })}
                className="w-full border rounded px-3 py-2"
                step="0.001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Stock Mínimo</label>
              <input
                type="number"
                value={formData.min_stock || ''}
                onChange={(e) => setFormData({ ...formData, min_stock: e.target.value === '' ? 0 : parseFloat(e.target.value) })}
                className="w-full border rounded px-3 py-2"
                step="0.001"
              />
            </div>
            <div className="col-span-2 flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Guardar
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="border px-4 py-2 rounded hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {supplies.map((supply) => (
          <div key={supply.id} className="bg-white border rounded-lg p-4">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h3 className="text-lg font-bold">{supply.name}</h3>
                <p className="text-sm text-gray-600">Unidad: {supply.unit}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(supply)}
                  className="p-2 hover:bg-gray-100 rounded"
                >
                  <Edit2 size={18} />
                </button>
                <button
                  onClick={() => handleDelete(supply.id)}
                  className="p-2 hover:bg-red-100 rounded text-red-600"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4 bg-gray-50 p-3 rounded">
              <div>
                <p className="text-xs text-gray-600">Stock Actual</p>
                <p className="font-bold">{supply.stock_quantity.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Stock Mínimo</p>
                <p className="font-bold">{supply.min_stock.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Estado</p>
                <p className={`font-bold ${supply.stock_quantity < supply.min_stock ? 'text-red-600' : 'text-green-600'}`}>
                  {supply.stock_quantity < supply.min_stock ? 'Bajo Stock' : 'OK'}
                </p>
              </div>
            </div>

            {showPrices === supply.id && (
              <div className="border-t pt-4">
                <h4 className="font-bold mb-3">Registrar Precio</h4>
                <form onSubmit={handleAddPrice} className="grid grid-cols-3 gap-2 mb-3">
                  <input
                    type="number"
                    placeholder="Precio"
                    value={priceData.price}
                    onChange={(e) => setPriceData({ ...priceData, price: e.target.value })}
                    className="border rounded px-2 py-1"
                    step="0.01"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Proveedor"
                    value={priceData.supplier}
                    onChange={(e) => setPriceData({ ...priceData, supplier: e.target.value })}
                    className="border rounded px-2 py-1"
                  />
                  <div className="flex gap-1">
                    <button
                      type="submit"
                      className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 flex-1"
                    >
                      Registrar
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowPrices(null)}
                      className="border px-3 py-1 rounded"
                    >
                      Cerrar
                    </button>
                  </div>
                </form>

                {supply.recent_prices && supply.recent_prices.length > 0 && (
                  <div className="text-sm">
                    <p className="font-medium mb-2">Últimos Precios:</p>
                    <div className="space-y-1">
                      {supply.recent_prices.map((p) => (
                        <div key={p.id} className="bg-gray-100 px-2 py-1 rounded">
                          <span className="font-bold">${p.price}</span>
                          {p.supplier && <span className="text-gray-600 ml-2">({p.supplier})</span>}
                          <span className="text-gray-500 text-xs ml-2">{p.recorded_at}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {showPrices !== supply.id && (
              <button
                onClick={() => setShowPrices(supply.id)}
                className="text-blue-600 text-sm hover:underline"
              >
                Registrar Precio
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default Supplies
