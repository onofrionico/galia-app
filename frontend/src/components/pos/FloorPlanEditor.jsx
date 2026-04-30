import { useState } from 'react'
import { Save, X, Plus, Trash2 } from 'lucide-react'
import salonsService from '../../services/salonsService'

const FloorPlanEditor = ({ salon, mesas, onSave, onClose }) => {
  const [editingMesas, setEditingMesas] = useState(mesas)
  const [draggingMesa, setDraggingMesa] = useState(null)
  const [resizingMesa, setResizingMesa] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [newMesaForm, setNewMesaForm] = useState({
    number: '',
    name: '',
    capacity: '',
    pos_x: 50,
    pos_y: 50,
    width: 8,
    height: 8,
  })
  const [showNewMesaForm, setShowNewMesaForm] = useState(false)

  const handleMesaDragStart = (e, mesa) => {
    setDraggingMesa(mesa)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handlePlanDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handlePlanDrop = (e) => {
    e.preventDefault()
    if (!draggingMesa) return

    const rect = e.currentTarget.getBoundingClientRect()
    const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100))
    const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100))

    setEditingMesas(
      editingMesas.map((m) =>
        m.id === draggingMesa.id ? { ...m, pos_x: x, pos_y: y } : m
      )
    )
    setDraggingMesa(null)
  }

  const handleResizeStart = (e, mesa) => {
    e.preventDefault()
    setResizingMesa({
      ...mesa,
      startX: e.clientX,
      startY: e.clientY,
      startWidth: mesa.width,
      startHeight: mesa.height,
    })
  }

  const handleMouseMove = (e) => {
    if (!resizingMesa) return

    const deltaX = e.clientX - resizingMesa.startX
    const deltaY = e.clientY - resizingMesa.startY

    const newWidth = Math.max(5, resizingMesa.startWidth + deltaX / 10)
    const newHeight = Math.max(5, resizingMesa.startHeight + deltaY / 10)

    setEditingMesas(
      editingMesas.map((m) =>
        m.id === resizingMesa.id
          ? { ...m, width: newWidth, height: newHeight }
          : m
      )
    )
  }

  const handleMouseUp = () => {
    setResizingMesa(null)
  }

  const handleDeleteMesa = (mesaId) => {
    if (window.confirm('¿Desactivar esta mesa?')) {
      setEditingMesas(editingMesas.filter((m) => m.id !== mesaId))
    }
  }

  const handleAddNewMesa = async () => {
    if (!newMesaForm.number) {
      setError('El número de mesa es requerido')
      return
    }

    try {
      const newMesa = await salonsService.createMesa(salon.id, {
        number: parseInt(newMesaForm.number),
        name: newMesaForm.name || null,
        capacity: newMesaForm.capacity ? parseInt(newMesaForm.capacity) : null,
        pos_x: newMesaForm.pos_x,
        pos_y: newMesaForm.pos_y,
        width: newMesaForm.width,
        height: newMesaForm.height,
        status: 'libre',
      })

      setEditingMesas([...editingMesas, newMesa])
      setNewMesaForm({
        number: '',
        name: '',
        capacity: '',
        pos_x: 50,
        pos_y: 50,
        width: 8,
        height: 8,
      })
      setShowNewMesaForm(false)
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear mesa')
    }
  }

  const handleSaveLayout = async () => {
    setSaving(true)
    try {
      for (const mesa of editingMesas) {
        if (mesa.id) {
          await salonsService.updateMesa(salon.id, mesa.id, {
            pos_x: mesa.pos_x,
            pos_y: mesa.pos_y,
            width: mesa.width,
            height: mesa.height,
          })
        }
      }

      setError('')
      onSave()
    } catch (err) {
      setError('Error al guardar plano')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Editar Plano - {salon.name}</h2>
          <button
            onClick={onClose}
            disabled={saving}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden flex gap-4 p-6">
          <div className="flex-1 flex flex-col">
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Arrastra las mesas para reposicionarlas. Haz click y arrastra desde la esquina inferior derecha para redimensionar.
              </p>
            </div>

            <div
              className="flex-1 bg-slate-100 border-2 border-slate-300 rounded-lg relative overflow-hidden cursor-move"
              onDragOver={handlePlanDragOver}
              onDrop={handlePlanDrop}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            >
              {editingMesas.map((mesa) => (
                <div
                  key={mesa.id}
                  draggable
                  onDragStart={(e) => handleMesaDragStart(e, mesa)}
                  style={{
                    position: 'absolute',
                    left: `${mesa.pos_x}%`,
                    top: `${mesa.pos_y}%`,
                    width: `${mesa.width}%`,
                    height: `${mesa.height}%`,
                    minWidth: '60px',
                    minHeight: '60px',
                  }}
                  className="border-2 border-blue-500 bg-blue-100 rounded-lg p-2 cursor-move flex flex-col justify-between group"
                >
                  <div className="text-center">
                    <div className="font-bold text-sm">Mesa {mesa.number}</div>
                    {mesa.name && <div className="text-xs">{mesa.name}</div>}
                  </div>

                  <div
                    className="absolute bottom-0 right-0 w-4 h-4 bg-blue-500 cursor-se-resize opacity-0 group-hover:opacity-100 rounded-tl"
                    onMouseDown={(e) => handleResizeStart(e, mesa)}
                  />

                  <button
                    onClick={() => handleDeleteMesa(mesa.id)}
                    className="absolute -top-3 -right-3 bg-red-500 text-white p-1 rounded-full hover:bg-red-600 opacity-0 group-hover:opacity-100 transition"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="w-80 border-l pl-4 flex flex-col">
            <h3 className="font-bold text-lg mb-4">Mesas ({editingMesas.length})</h3>

            <div className="flex-1 overflow-y-auto mb-4 space-y-2 text-sm">
              {editingMesas.map((mesa) => (
                <div key={mesa.id} className="bg-gray-50 p-2 rounded border">
                  <div className="font-medium">Mesa {mesa.number}</div>
                  <div className="text-xs text-gray-600">
                    Pos: ({mesa.pos_x.toFixed(1)}, {mesa.pos_y.toFixed(1)})
                  </div>
                  <div className="text-xs text-gray-600">
                    Tamaño: {mesa.width.toFixed(1)} x {mesa.height.toFixed(1)}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Agregar Mesa</h4>

              {!showNewMesaForm ? (
                <button
                  onClick={() => setShowNewMesaForm(true)}
                  className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 flex items-center justify-center gap-2 text-sm font-medium"
                >
                  <Plus size={16} /> Nueva Mesa
                </button>
              ) : (
                <div className="space-y-2 text-sm">
                  <input
                    type="number"
                    placeholder="Número"
                    value={newMesaForm.number}
                    onChange={(e) =>
                      setNewMesaForm({
                        ...newMesaForm,
                        number: e.target.value,
                      })
                    }
                    className="w-full border rounded px-2 py-1"
                  />
                  <input
                    type="text"
                    placeholder="Nombre (opcional)"
                    value={newMesaForm.name}
                    onChange={(e) =>
                      setNewMesaForm({ ...newMesaForm, name: e.target.value })
                    }
                    className="w-full border rounded px-2 py-1"
                  />
                  <input
                    type="number"
                    placeholder="Capacidad (opcional)"
                    value={newMesaForm.capacity}
                    onChange={(e) =>
                      setNewMesaForm({
                        ...newMesaForm,
                        capacity: e.target.value,
                      })
                    }
                    className="w-full border rounded px-2 py-1"
                  />

                  <div className="grid grid-cols-2 gap-1">
                    <input
                      type="number"
                      placeholder="Pos X"
                      value={newMesaForm.pos_x}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          pos_x: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                    <input
                      type="number"
                      placeholder="Pos Y"
                      value={newMesaForm.pos_y}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          pos_y: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-1">
                    <input
                      type="number"
                      placeholder="Ancho"
                      value={newMesaForm.width}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          width: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                    <input
                      type="number"
                      placeholder="Alto"
                      value={newMesaForm.height}
                      onChange={(e) =>
                        setNewMesaForm({
                          ...newMesaForm,
                          height: parseFloat(e.target.value),
                        })
                      }
                      className="border rounded px-2 py-1 text-xs"
                      step="1"
                    />
                  </div>

                  <div className="flex gap-1">
                    <button
                      onClick={handleAddNewMesa}
                      className="flex-1 bg-green-600 text-white py-1 rounded text-xs font-medium hover:bg-green-700"
                    >
                      Agregar
                    </button>
                    <button
                      onClick={() => setShowNewMesaForm(false)}
                      className="flex-1 bg-gray-300 text-gray-700 py-1 rounded text-xs font-medium hover:bg-gray-400"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="border-t pt-4 flex gap-2">
              <button
                onClick={handleSaveLayout}
                disabled={saving}
                className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2 font-medium"
              >
                <Save size={18} />
                {saving ? 'Guardando...' : 'Guardar'}
              </button>
              <button
                onClick={onClose}
                className="flex-1 border-2 border-gray-300 py-2 rounded hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FloorPlanEditor
