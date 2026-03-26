import React from 'react'
import { Link } from 'react-router-dom'
import { Building2, Phone, Mail, Calendar, Edit, Trash2 } from 'lucide-react'

export default function SupplierCard({ supplier, onEdit, onDelete }) {
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
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${badges[status] || badges.active}`}>
        {labels[status] || status}
      </span>
    )
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('es-AR')
  }

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <Link 
            to={`/suppliers/${supplier.id}`}
            className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors"
          >
            {supplier.name}
          </Link>
          <p className="text-sm text-gray-500 mt-1">CUIT: {supplier.tax_id}</p>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge(supplier.status)}
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {supplier.contact_person && (
          <div className="flex items-center text-sm text-gray-600">
            <Building2 className="w-4 h-4 mr-2" />
            <span>{supplier.contact_person}</span>
          </div>
        )}
        {supplier.phone && (
          <div className="flex items-center text-sm text-gray-600">
            <Phone className="w-4 h-4 mr-2" />
            <span>{supplier.phone}</span>
          </div>
        )}
        {supplier.email && (
          <div className="flex items-center text-sm text-gray-600">
            <Mail className="w-4 h-4 mr-2" />
            <span>{supplier.email}</span>
          </div>
        )}
        {supplier.payment_terms && (
          <div className="flex items-center text-sm text-gray-600">
            <Calendar className="w-4 h-4 mr-2" />
            <span>Pago: {supplier.payment_terms}</span>
          </div>
        )}
      </div>

      {(supplier.products_count !== undefined || supplier.purchases_count !== undefined) && (
        <div className="flex gap-4 mb-4 pt-4 border-t border-gray-200">
          {supplier.products_count !== undefined && (
            <div className="text-sm">
              <span className="text-gray-500">Productos:</span>
              <span className="ml-1 font-semibold text-gray-900">{supplier.products_count}</span>
            </div>
          )}
          {supplier.purchases_count !== undefined && (
            <div className="text-sm">
              <span className="text-gray-500">Compras:</span>
              <span className="ml-1 font-semibold text-gray-900">{supplier.purchases_count}</span>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2 pt-4 border-t border-gray-200">
        <button
          onClick={() => onEdit(supplier)}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Edit className="w-4 h-4" />
          <span>Editar</span>
        </button>
        <button
          onClick={() => onDelete(supplier)}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
