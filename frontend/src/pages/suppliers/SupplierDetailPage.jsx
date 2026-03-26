import React, { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Edit, Trash2, Building2, Phone, Mail, MapPin, Calendar, Package, ShoppingCart, AlertCircle, Loader2, TrendingUp } from 'lucide-react'
import { useSupplier, useUpdateSupplier, useDeleteSupplier } from '../../hooks/useSuppliers'
import SupplierForm from '../../components/suppliers/SupplierForm'
import SalesHistoryTab from '../../components/suppliers/SalesHistoryTab'

export default function SupplierDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [showEditForm, setShowEditForm] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [activeTab, setActiveTab] = useState('details')

  const { data: supplier, isLoading, error } = useSupplier(id)
  const updateMutation = useUpdateSupplier()
  const deleteMutation = useDeleteSupplier()

  const handleEdit = () => {
    setShowEditForm(true)
  }

  const handleDelete = () => {
    setShowDeleteConfirm(true)
  }

  const confirmDelete = async () => {
    try {
      await deleteMutation.mutateAsync(id)
      navigate('/suppliers')
    } catch (error) {
      alert(error.response?.data?.message || 'Error al eliminar el proveedor')
      setShowDeleteConfirm(false)
    }
  }

  const handleUpdate = async (formData) => {
    try {
      await updateMutation.mutateAsync({ id, data: formData })
      setShowEditForm(false)
      alert('Proveedor actualizado exitosamente')
    } catch (error) {
      alert(error.response?.data?.message || 'Error al actualizar el proveedor')
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      archived: 'bg-red-100 text-red-800'
    }
    const labels = {
      active: 'Activo',
      inactive: 'Inactivo',
      archived: 'Archivado'
    }
    return (
      <span className={`px-3 py-1 text-sm font-semibold rounded-full ${badges[status] || badges.active}`}>
        {labels[status] || status}
      </span>
    )
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex justify-center items-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Cargando proveedor...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 text-lg">Error al cargar proveedor</h3>
            <p className="text-red-700 mt-1">{error.message}</p>
            <Link to="/suppliers" className="text-red-600 hover:text-red-800 underline mt-2 inline-block">
              Volver a la lista de proveedores
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!supplier) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="text-center py-12">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Proveedor no encontrado</h3>
          <Link to="/suppliers" className="text-blue-600 hover:text-blue-800 underline">
            Volver a la lista de proveedores
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <Link
          to="/suppliers"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver a proveedores</span>
        </Link>

        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{supplier.name}</h1>
            <p className="text-gray-600 mt-1">CUIT: {supplier.tax_id}</p>
          </div>
          <div className="flex items-center gap-3">
            {getStatusBadge(supplier.status)}
            <button
              onClick={handleEdit}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Edit className="w-4 h-4" />
              <span>Editar</span>
            </button>
            <button
              onClick={handleDelete}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Eliminar</span>
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Link to={`/suppliers/${supplier.id}/products`} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <Package className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Productos</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">{supplier.products_count || 0}</p>
          <p className="text-sm text-gray-600 mt-1">En catálogo</p>
          <p className="text-xs text-blue-600 mt-2">Ver catálogo →</p>
        </Link>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-2">
            <ShoppingCart className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold text-gray-900">Compras</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">{supplier.purchases_count || 0}</p>
          <p className="text-sm text-gray-600 mt-1">Registradas</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-2">
            <Calendar className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">Creado</h3>
          </div>
          <p className="text-lg font-semibold text-gray-900">{formatDate(supplier.created_at)}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('details')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'details'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Building2 className="w-5 h-5" />
              <span>Detalles</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'history'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <TrendingUp className="w-5 h-5" />
              <span>Historial de Compras</span>
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'details' && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Información de Contacto</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {supplier.contact_person && (
            <div className="flex items-start gap-3">
              <Building2 className="w-5 h-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Persona de Contacto</p>
                <p className="font-medium text-gray-900">{supplier.contact_person}</p>
              </div>
            </div>
          )}

          {supplier.phone && (
            <div className="flex items-start gap-3">
              <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Teléfono</p>
                <p className="font-medium text-gray-900">{supplier.phone}</p>
              </div>
            </div>
          )}

          {supplier.email && (
            <div className="flex items-start gap-3">
              <Mail className="w-5 h-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <a href={`mailto:${supplier.email}`} className="font-medium text-blue-600 hover:text-blue-800">
                  {supplier.email}
                </a>
              </div>
            </div>
          )}

          {supplier.address && (
            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Dirección</p>
                <p className="font-medium text-gray-900">{supplier.address}</p>
              </div>
            </div>
          )}

          {supplier.payment_terms && (
            <div className="flex items-start gap-3">
              <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-600">Términos de Pago</p>
                <p className="font-medium text-gray-900">{supplier.payment_terms}</p>
              </div>
            </div>
          )}
        </div>
        </div>
      )}

      {activeTab === 'history' && (
        <SalesHistoryTab supplierId={id} />
      )}

      {showEditForm && (
        <SupplierForm
          supplier={supplier}
          onSubmit={handleUpdate}
          onCancel={() => setShowEditForm(false)}
          isLoading={updateMutation.isPending}
        />
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Confirmar Eliminación</h3>
            <p className="text-gray-600 mb-6">
              ¿Estás seguro de que deseas eliminar el proveedor <strong>{supplier.name}</strong>?
              Esta acción no se puede deshacer.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={deleteMutation.isPending}
              >
                Cancelar
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-red-300"
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
