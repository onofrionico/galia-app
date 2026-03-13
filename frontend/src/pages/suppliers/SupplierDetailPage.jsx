import React from 'react'
import { useParams } from 'react-router-dom'

export default function SupplierDetailPage() {
  const { id } = useParams()
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Detalle de Proveedor #{id}</h1>
      <p className="text-gray-600">Módulo de proveedores - En desarrollo</p>
    </div>
  )
}
