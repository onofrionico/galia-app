# POS + Camarero UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign POS Admin (fullscreen grid + right panel) and Camarero (mobile tab navigation) with GALIA Café brand colors and modern minimalist aesthetics.

**Architecture:** Create color constants, refactor existing components (MesaCard, OrderDrawer, Pos.jsx), create new layouts (PosLayout, CamareroLayout), and new bottom sheet for payment flow. All tied to existing Order/OrderItem backend.

**Tech Stack:** React 18, Tailwind CSS (arbitrary color values), lucide-react icons, existing Vite build.

---

## File Structure Overview

```
frontend/src/
├── constants/
│   └── colors.js (NEW) — GALIA palette hex values
├── components/
│   ├── layout/
│   │   ├── PosLayout.jsx (NEW) — Fullscreen layout for POS
│   │   └── CamareroLayout.jsx (NEW) — Mobile layout for Camarero
│   └── pos/
│       ├── MesaCard.jsx (MODIFY) — Color + styling updates
│       ├── PosHeader.jsx (NEW) — Header with salon selector
│       ├── OrderDrawer.jsx (MODIFY) — Right panel styling
│       ├── CobrarBottomSheet.jsx (NEW) — Payment method selection
│       └── PosMain.jsx (NEW) — Grid container for mesas
└── pages/
    ├── Pos.jsx (REFACTOR) — Integrate new layout + components
    ├── Camarero.jsx (REFACTOR) — Tab 1: salón view
    └── CamareroMesa.jsx (REFACTOR) — Tab 2: orden view
```

---

## Tasks

### Task 1: Color Constants

**Files:**
- Create: `frontend/src/constants/colors.js`

- [ ] **Step 1: Create GALIA color palette file**

```javascript
// frontend/src/constants/colors.js

export const GALIA = {
  amarillo: '#D4E157',      // Primary accent
  marron: '#6B4C5C',        // Secondary/brand
  crema: '#E8DCC4',         // Main background
  blanco: '#FFFBF8',        // Card/overlay background
  grisClaro: '#8A8A8A',     // Secondary text
  grisLigero: '#E5E5E5',    // Borders
  verde: '#7CB342',         // Status: Libre
}

// Tailwind color utility object for config extension (optional for later)
export const galiaTailwind = {
  'galia-amarillo': GALIA.amarillo,
  'galia-marron': GALIA.marron,
  'galia-crema': GALIA.crema,
  'galia-blanco': GALIA.blanco,
  'galia-gris-claro': GALIA.grisClaro,
  'galia-gris-ligero': GALIA.grisLigero,
  'galia-verde': GALIA.verde,
}

export default GALIA
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/constants/colors.js
git commit -m "feat: add GALIA color palette constants"
```

---

### Task 2: PosLayout Component

**Files:**
- Create: `frontend/src/components/layout/PosLayout.jsx`

- [ ] **Step 1: Create PosLayout fullscreen layout**

```jsx
// frontend/src/components/layout/PosLayout.jsx
import { Outlet } from 'react-router-dom'
import GALIA from '../../constants/colors'

const PosLayout = () => {
  return (
    <div className="h-screen w-screen flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* POS Header will be rendered inside Pos.jsx */}
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}

export default PosLayout
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/layout/PosLayout.jsx
git commit -m "feat: create PosLayout for fullscreen POS"
```

---

### Task 3: CamareroLayout Component

**Files:**
- Create: `frontend/src/components/layout/CamareroLayout.jsx`

- [ ] **Step 1: Create CamareroLayout mobile layout**

```jsx
// frontend/src/components/layout/CamareroLayout.jsx
import { Outlet } from 'react-router-dom'
import GALIA from '../../constants/colors'

const CamareroLayout = () => {
  return (
    <div className="h-screen w-screen flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* Camarero Header - sticky */}
      <header className="h-14 flex items-center justify-center" style={{ backgroundColor: GALIA.marron }}>
        <h1 className="text-white text-lg font-semibold">Mi Turno - Camarero</h1>
      </header>
      
      {/* Content area */}
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}

export default CamareroLayout
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/layout/CamareroLayout.jsx
git commit -m "feat: create CamareroLayout for mobile camarero"
```

---

### Task 4: MesaCard Component Refactor

**Files:**
- Modify: `frontend/src/components/pos/MesaCard.jsx`

- [ ] **Step 1: Update MesaCard with GALIA colors and new styling**

```jsx
// frontend/src/components/pos/MesaCard.jsx
import GALIA from '../../constants/colors'

const MesaCard = ({ mesa, onClick, isDragging, style }) => {
  const getStatusBadgeColor = () => {
    switch (mesa.status) {
      case 'libre':
        return { bg: GALIA.verde, text: 'white' }
      case 'ocupada':
        return { bg: GALIA.amarillo, text: GALIA.marron }
      case 'reservada':
        return { bg: GALIA.grisLigero, text: GALIA.grisClaro }
      default:
        return { bg: GALIA.grisLigero, text: GALIA.grisClaro }
    }
  }

  const getStatusText = () => {
    switch (mesa.status) {
      case 'libre':
        return 'Libre'
      case 'ocupada':
        return 'Ocupada'
      case 'reservada':
        return 'Reservada'
      default:
        return 'Desconocido'
    }
  }

  const statusColors = getStatusBadgeColor()

  return (
    <div
      onClick={onClick}
      style={style}
      className="rounded-lg p-4 cursor-pointer transition-all duration-200"
      style={{
        backgroundColor: GALIA.blanco,
        borderWidth: '2px',
        borderColor: isDragging ? GALIA.amarillo : GALIA.grisLigero,
        boxShadow: isDragging ? '0 10px 15px rgba(0, 0, 0, 0.1)' : 'none',
      }}
    >
      {/* Mesa Number */}
      <div className="text-4xl font-bold mb-2" style={{ color: GALIA.marron }}>
        {mesa.number}
      </div>

      {/* Status Badge */}
      <div
        className="rounded-full px-3 py-1 text-xs font-semibold mb-2 inline-block"
        style={{ backgroundColor: statusColors.bg, color: statusColors.text }}
      >
        {getStatusText()}
      </div>

      {/* Items & Total (only if occupied) */}
      {mesa.status === 'ocupada' && mesa.openOrder && (
        <div className="text-sm mt-2" style={{ color: GALIA.grisClaro }}>
          <div>{mesa.openOrder.items?.length || 0} ítems</div>
          <div className="font-semibold" style={{ color: GALIA.marron }}>
            ${parseFloat(mesa.openOrder.total).toFixed(2)}
          </div>
        </div>
      )}

      {/* Capacity */}
      {mesa.capacity && (
        <div className="text-xs mt-2" style={{ color: GALIA.grisClaro }}>
          Cap: {mesa.capacity}
        </div>
      )}
    </div>
  )
}

export default MesaCard
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/pos/MesaCard.jsx
git commit -m "refactor: update MesaCard with GALIA colors and new styling"
```

---

### Task 5: PosHeader Component

**Files:**
- Create: `frontend/src/components/pos/PosHeader.jsx`

- [ ] **Step 1: Create PosHeader with salon selector**

```jsx
// frontend/src/components/pos/PosHeader.jsx
import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import GALIA from '../../constants/colors'

const PosHeader = ({ salons, activeSalon, onSalonChange }) => {
  const navigate = useNavigate()

  const handleExit = () => {
    navigate('/dashboard')
  }

  return (
    <header
      className="h-16 flex items-center justify-between px-6"
      style={{ backgroundColor: GALIA.crema }}
    >
      {/* Logo/Title */}
      <h1 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
        GALIA POS
      </h1>

      {/* Salon Selector - Tabs */}
      <div className="flex gap-4">
        {salons.map((salon) => (
          <button
            key={salon.id}
            onClick={() => onSalonChange(salon.id)}
            className="px-4 py-2 text-sm font-medium transition-colors duration-200"
            style={{
              color: activeSalon === salon.id ? GALIA.marron : GALIA.grisClaro,
              borderBottom: activeSalon === salon.id ? `2px solid ${GALIA.amarillo}` : 'none',
            }}
          >
            {salon.name}
          </button>
        ))}
      </div>

      {/* Exit Button */}
      <button
        onClick={handleExit}
        className="flex items-center gap-2 px-4 py-2 rounded transition-colors duration-200"
        style={{
          color: GALIA.marron,
          backgroundColor: 'transparent',
        }}
        onMouseEnter={(e) => (e.target.style.backgroundColor = GALIA.amarillo)}
        onMouseLeave={(e) => (e.target.style.backgroundColor = 'transparent')}
      >
        <LogOut size={18} />
        Salir
      </button>
    </header>
  )
}

export default PosHeader
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/pos/PosHeader.jsx
git commit -m "feat: create PosHeader with salon selector"
```

---

### Task 6: PosMain Grid Container

**Files:**
- Create: `frontend/src/components/pos/PosMain.jsx`

- [ ] **Step 1: Create grid container for mesas**

```jsx
// frontend/src/components/pos/PosMain.jsx
import GALIA from '../../constants/colors'
import MesaCard from './MesaCard'

const PosMain = ({ mesas, onMesaClick, activeSalonMesas }) => {
  // Responsive grid: 6 cols (1440+), 4 cols (1080), 3 cols (768), 2 cols (mobile)
  const gridColsClass = 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6'

  return (
    <div
      className={`flex-1 overflow-auto p-6 ${gridColsClass} gap-4 auto-rows-max`}
      style={{ backgroundColor: GALIA.crema }}
    >
      {activeSalonMesas.map((mesa) => (
        <MesaCard
          key={mesa.id}
          mesa={mesa}
          onClick={() => onMesaClick(mesa)}
        />
      ))}
    </div>
  )
}

export default PosMain
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/pos/PosMain.jsx
git commit -m "feat: create PosMain grid container for mesas"
```

---

### Task 7: OrderDrawer Refactor

**Files:**
- Modify: `frontend/src/components/pos/OrderDrawer.jsx`

- [ ] **Step 1: Read current OrderDrawer to understand structure**

Current file: `frontend/src/components/pos/OrderDrawer.jsx` (already exists from prior work)

- [ ] **Step 2: Update OrderDrawer with GALIA colors and new styling**

```jsx
// frontend/src/components/pos/OrderDrawer.jsx
import { X } from 'lucide-react'
import GALIA from '../../constants/colors'

const OrderDrawer = ({ order, isOpen, onClose, onAddItem, onRemoveItem, onCobrar }) => {
  if (!isOpen || !order) return null

  return (
    <div
      className="fixed right-0 top-0 h-full w-80 flex flex-col shadow-lg z-50"
      style={{ backgroundColor: GALIA.blanco, borderLeft: `4px solid ${GALIA.amarillo}` }}
    >
      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ backgroundColor: GALIA.crema }}>
        <h2 className="text-lg font-semibold" style={{ color: GALIA.marron }}>
          Orden #{order.id}
        </h2>
        <button onClick={onClose} className="p-1">
          <X size={20} style={{ color: GALIA.marron }} />
        </button>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {order.items && order.items.length > 0 ? (
          order.items.map((item) => (
            <div
              key={item.id}
              className="rounded px-3 py-2 flex items-center justify-between"
              style={{ backgroundColor: GALIA.crema }}
            >
              <div className="flex-1">
                <div className="text-sm font-medium" style={{ color: GALIA.marron }}>
                  {item.product_name}
                </div>
                <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                  x{item.quantity}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold" style={{ color: GALIA.marron }}>
                  ${(item.unit_price * item.quantity).toFixed(2)}
                </span>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="p-1"
                  style={{ color: GALIA.grisClaro }}
                  onMouseEnter={(e) => (e.target.style.color = '#ef4444')}
                  onMouseLeave={(e) => (e.target.style.color = GALIA.grisClaro)}
                >
                  ×
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8" style={{ color: GALIA.grisClaro }}>
            Sin items
          </div>
        )}
      </div>

      {/* Total Section */}
      <div
        className="border-t px-4 py-4"
        style={{ borderColor: GALIA.grisLigero }}
      >
        <div className="text-2xl font-bold mb-4" style={{ color: GALIA.amarillo }}>
          ${parseFloat(order.total || 0).toFixed(2)}
        </div>

        {/* Buttons */}
        <div className="space-y-2">
          <button
            onClick={onAddItem}
            className="w-full py-2 rounded font-semibold transition-opacity duration-200"
            style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
            onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.target.style.opacity = '1')}
          >
            Agregar Item
          </button>
          <button
            onClick={onCobrar}
            className="w-full py-3 rounded font-bold text-lg transition-opacity duration-200"
            style={{ backgroundColor: GALIA.marron, color: 'white' }}
            onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.target.style.opacity = '1')}
          >
            COBRAR
          </button>
        </div>
      </div>
    </div>
  )
}

export default OrderDrawer
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/pos/OrderDrawer.jsx
git commit -m "refactor: update OrderDrawer with GALIA colors and styling"
```

---

### Task 8: CobrarBottomSheet Component

**Files:**
- Create: `frontend/src/components/pos/CobrarBottomSheet.jsx`

- [ ] **Step 1: Create bottom sheet for payment method selection**

```jsx
// frontend/src/components/pos/CobrarBottomSheet.jsx
import { useState } from 'react'
import { X } from 'lucide-react'
import GALIA from '../../constants/colors'

const CobrarBottomSheet = ({ isOpen, orderId, total, onConfirm, onClose }) => {
  const [selectedMethod, setSelectedMethod] = useState(null)

  if (!isOpen) return null

  const handleConfirm = () => {
    if (selectedMethod) {
      onConfirm(selectedMethod)
      setSelectedMethod(null)
    }
  }

  const metodos = ['Efectivo', 'Tarjeta', 'Otro']

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div
        className="fixed bottom-0 left-0 right-0 z-50 rounded-t-xl max-h-[60vh] flex flex-col"
        style={{ backgroundColor: GALIA.blanco }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3"
          style={{ backgroundColor: GALIA.marron }}
        >
          <h2 className="text-white text-lg font-semibold">Método de Pago</h2>
          <button onClick={onClose} className="p-1">
            <X size={20} color="white" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {/* Total Display */}
          <div className="mb-4">
            <p className="text-sm" style={{ color: GALIA.grisClaro }}>
              Total a pagar:
            </p>
            <p className="text-3xl font-bold" style={{ color: GALIA.amarillo }}>
              ${total.toFixed(2)}
            </p>
          </div>

          {/* Method Selection */}
          <div className="grid grid-cols-3 gap-2">
            {metodos.map((metodo) => (
              <button
                key={metodo}
                onClick={() => setSelectedMethod(metodo)}
                className="py-3 rounded border-2 font-semibold transition-colors duration-200"
                style={{
                  borderColor:
                    selectedMethod === metodo ? GALIA.amarillo : GALIA.grisLigero,
                  backgroundColor:
                    selectedMethod === metodo ? GALIA.amarillo : 'transparent',
                  color:
                    selectedMethod === metodo ? GALIA.marron : GALIA.marron,
                }}
              >
                {metodo}
              </button>
            ))}
          </div>
        </div>

        {/* Confirm Button */}
        <div className="px-4 py-4 border-t" style={{ borderColor: GALIA.grisLigero }}>
          <button
            onClick={handleConfirm}
            disabled={!selectedMethod}
            className="w-full py-3 rounded font-bold text-lg transition-opacity duration-200"
            style={{
              backgroundColor: selectedMethod ? GALIA.marron : GALIA.grisLigero,
              color: 'white',
              opacity: selectedMethod ? 1 : 0.6,
              cursor: selectedMethod ? 'pointer' : 'not-allowed',
            }}
          >
            Confirmar
          </button>
        </div>
      </div>
    </>
  )
}

export default CobrarBottomSheet
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/pos/CobrarBottomSheet.jsx
git commit -m "feat: create CobrarBottomSheet for payment method selection"
```

---

### Task 9: Pos.jsx Refactor (Main Integration)

**Files:**
- Modify: `frontend/src/pages/Pos.jsx`

- [ ] **Step 1: Refactor Pos.jsx to use new components and colors**

```jsx
// frontend/src/pages/Pos.jsx
import { useState, useEffect } from 'react'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import salesService from '../services/salesService'
import PosHeader from '../components/pos/PosHeader'
import PosMain from '../components/pos/PosMain'
import OrderDrawer from '../components/pos/OrderDrawer'
import CobrarBottomSheet from '../components/pos/CobrarBottomSheet'
import AddItemModal from '../components/pos/AddItemModal'

const Pos = () => {
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showOrderDrawer, setShowOrderDrawer] = useState(false)
  const [showAddItemModal, setShowAddItemModal] = useState(false)
  const [showCobrarSheet, setShowCobrarSheet] = useState(false)

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchAll = async () => {
    try {
      const [salonRes, ordersRes] = await Promise.all([
        salonsService.getSalons({ include_inactive: false }),
        ordersService.getOrders({ status: 'abierta' }),
      ])

      setSalons(salonRes.salons || [])
      setOpenOrders(ordersRes.orders || [])

      // Fetch mesas for all salons
      const mesasMap = {}
      for (const salon of salonRes.salons || []) {
        const mesasRes = await salonsService.getMesas(salon.id)
        const mesasWithOrders = (mesasRes.mesas || []).map((mesa) => ({
          ...mesa,
          openOrder: (ordersRes.orders || []).find((o) => o.mesa_id === mesa.id),
        }))
        mesasMap[salon.id] = mesasWithOrders
      }
      setAllMesas(mesasMap)

      if (salonRes.salons && salonRes.salons.length > 0 && !activeSalon) {
        setActiveSalon(salonRes.salons[0].id)
      }

      setLoading(false)
    } catch (err) {
      setError('Error al cargar datos')
      setLoading(false)
    }
  }

  const handleMesaClick = async (mesa) => {
    if (mesa.status === 'libre') {
      try {
        const order = await ordersService.createOrder({
          mesa_id: mesa.id,
          salon_id: activeSalon,
        })
        setSelectedOrder(order)
        setShowOrderDrawer(true)
        await fetchAll()
      } catch (err) {
        setError('Error al crear orden')
      }
    } else if (mesa.status === 'ocupada' && mesa.openOrder) {
      setSelectedOrder(mesa.openOrder)
      setShowOrderDrawer(true)
    }
  }

  const handleAddItem = async (productVariantId, quantity) => {
    try {
      await ordersService.addItem(selectedOrder.id, {
        product_variant_id: productVariantId,
        quantity,
      })
      const updated = await ordersService.getOrder(selectedOrder.id)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al agregar item')
    }
  }

  const handleRemoveItem = async (itemId) => {
    try {
      await ordersService.removeItem(selectedOrder.id, itemId)
      const updated = await ordersService.getOrder(selectedOrder.id)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al eliminar item')
    }
  }

  const handleCobrar = async (metodo_pago) => {
    try {
      await ordersService.cobrar(selectedOrder.id, { metodo_pago })
      setShowCobrarSheet(false)
      setShowOrderDrawer(false)
      setSelectedOrder(null)
      await fetchAll()
    } catch (err) {
      setError('Error al cobrar')
    }
  }

  if (loading) {
    return <div className="p-6">Cargando...</div>
  }

  const activeSalonMesas = allMesas[activeSalon] || []

  return (
    <div className="h-full flex flex-col">
      <PosHeader
        salons={salons}
        activeSalon={activeSalon}
        onSalonChange={setActiveSalon}
      />

      <div className="flex flex-1 overflow-hidden">
        <PosMain
          mesas={allMesas}
          onMesaClick={handleMesaClick}
          activeSalonMesas={activeSalonMesas}
        />

        <OrderDrawer
          order={selectedOrder}
          isOpen={showOrderDrawer}
          onClose={() => setShowOrderDrawer(false)}
          onAddItem={() => setShowAddItemModal(true)}
          onRemoveItem={handleRemoveItem}
          onCobrar={() => setShowCobrarSheet(true)}
        />
      </div>

      <CobrarBottomSheet
        isOpen={showCobrarSheet}
        orderId={selectedOrder?.id}
        total={selectedOrder?.total || 0}
        onConfirm={handleCobrar}
        onClose={() => setShowCobrarSheet(false)}
      />

      <AddItemModal
        isOpen={showAddItemModal}
        onClose={() => setShowAddItemModal(false)}
        onAddItem={handleAddItem}
      />

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
          {error}
        </div>
      )}
    </div>
  )
}

export default Pos
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Pos.jsx
git commit -m "refactor: integrate new POS components and layouts"
```

---

### Task 10: Camarero.jsx Refactor (Tab 1 - Salón View)

**Files:**
- Modify: `frontend/src/pages/Camarero.jsx`

- [ ] **Step 1: Update Camarero.jsx for tab 1 (salón view)**

```jsx
// frontend/src/pages/Camarero.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import MesaCard from '../components/pos/MesaCard'
import GALIA from '../constants/colors'

const Camarero = () => {
  const navigate = useNavigate()
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [activeSalonMesas, setActiveSalonMesas] = useState([])
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchAll = async () => {
    try {
      const [salonRes, ordersRes] = await Promise.all([
        salonsService.getSalons({ include_inactive: false }),
        ordersService.getOrders({ status: 'abierta' }),
      ])

      setSalons(salonRes.salons || [])
      setOpenOrders(ordersRes.orders || [])

      if (salonRes.salons && salonRes.salons.length > 0) {
        if (!activeSalon) {
          setActiveSalon(salonRes.salons[0].id)
        }

        // Fetch mesas for active salon
        const activeSalonId = activeSalon || salonRes.salons[0].id
        const mesasRes = await salonsService.getMesas(activeSalonId)
        const mesasWithOrders = (mesasRes.mesas || []).map((mesa) => ({
          ...mesa,
          openOrder: (ordersRes.orders || []).find((o) => o.mesa_id === mesa.id),
        }))
        setActiveSalonMesas(mesasWithOrders)
      }

      setLoading(false)
    } catch (err) {
      console.error('Error fetching:', err)
      setLoading(false)
    }
  }

  const handleMesaClick = (mesa) => {
    const order = openOrders.find((o) => o.mesa_id === mesa.id)
    if (order || mesa.status === 'libre') {
      navigate(`/camarero/mesa/${mesa.id}`, {
        state: {
          orderId: order?.id,
          mesaId: mesa.id,
          salonId: activeSalon,
        },
      })
    }
  }

  if (loading) {
    return <div className="p-6">Cargando...</div>
  }

  return (
    <div
      className="flex-1 p-3 overflow-auto"
      style={{ backgroundColor: GALIA.crema }}
    >
      {/* Salon Selector */}
      <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
        {salons.map((salon) => (
          <button
            key={salon.id}
            onClick={() => setActiveSalon(salon.id)}
            className="px-4 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors duration-200"
            style={{
              backgroundColor: activeSalon === salon.id ? GALIA.amarillo : GALIA.blanco,
              color: activeSalon === salon.id ? GALIA.marron : GALIA.marron,
              border: `1px solid ${GALIA.grisLigero}`,
            }}
          >
            {salon.name}
          </button>
        ))}
      </div>

      {/* Mesas Grid - 2 columns on mobile */}
      <div className="grid grid-cols-2 gap-3">
        {activeSalonMesas.map((mesa) => (
          <div key={mesa.id} onClick={() => handleMesaClick(mesa)}>
            <MesaCard mesa={mesa} onClick={() => handleMesaClick(mesa)} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default Camarero
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Camarero.jsx
git commit -m "refactor: update Camarero for mobile salón view with GALIA colors"
```

---

### Task 11: CamareroMesa.jsx Refactor (Tab 2 - Orden View)

**Files:**
- Modify: `frontend/src/pages/CamareroMesa.jsx`

- [ ] **Step 1: Update CamareroMesa.jsx for tab 2 (orden/items view)**

```jsx
// frontend/src/pages/CamareroMesa.jsx
import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import ordersService from '../services/ordersService'
import productsService from '../services/productsService'
import CobrarBottomSheet from '../components/pos/CobrarBottomSheet'
import GALIA from '../constants/colors'

const CamareroMesa = () => {
  const { mesaId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  const { orderId, salonId } = location.state || {}

  const [order, setOrder] = useState(null)
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showCobrarSheet, setShowCobrarSheet] = useState(false)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [orderId])

  const fetchData = async () => {
    try {
      if (orderId) {
        const orderRes = await ordersService.getOrder(orderId)
        setOrder(orderRes)
      }

      const productsRes = await productsService.getProducts({ include_inactive: false })
      setProducts(productsRes.products || [])

      const categoriesRes = await productsService.getCategories()
      setCategories(categoriesRes.categories || [])
      if ((categoriesRes.categories || []).length > 0) {
        setActiveCategory(categoriesRes.categories[0].id)
      }

      setLoading(false)
    } catch (err) {
      console.error('Error fetching:', err)
      setLoading(false)
    }
  }

  const handleAddItem = async (productVariantId, quantity) => {
    try {
      if (!order) {
        const newOrder = await ordersService.createOrder({
          mesa_id: mesaId,
          salon_id: salonId,
        })
        setOrder(newOrder)
        await ordersService.addItem(newOrder.id, { product_variant_id: productVariantId, quantity })
      } else {
        await ordersService.addItem(order.id, { product_variant_id: productVariantId, quantity })
      }
      await fetchData()
    } catch (err) {
      console.error('Error adding item:', err)
    }
  }

  const handleRemoveItem = async (itemId) => {
    try {
      await ordersService.removeItem(order.id, itemId)
      await fetchData()
    } catch (err) {
      console.error('Error removing item:', err)
    }
  }

  const handleCobrar = async (metodo_pago) => {
    try {
      await ordersService.cobrar(order.id, { metodo_pago })
      setShowCobrarSheet(false)
      navigate('/camarero')
    } catch (err) {
      console.error('Error al cobrar:', err)
    }
  }

  if (loading) {
    return <div className="p-6">Cargando...</div>
  }

  const filteredProducts = activeCategory
    ? products.filter((p) => p.category_id === activeCategory)
    : products

  return (
    <div
      className="h-full flex flex-col pb-20"
      style={{ backgroundColor: GALIA.crema }}
    >
      {/* Sticky Header */}
      <div
        className="sticky top-0 h-12 flex items-center gap-3 px-3 z-10"
        style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}
      >
        <button onClick={() => navigate('/camarero')} className="p-1">
          <ChevronLeft size={20} style={{ color: GALIA.marron }} />
        </button>
        <h2 className="text-lg font-semibold" style={{ color: GALIA.marron }}>
          Mesa {mesaId}
        </h2>
      </div>

      {/* Categories Scroll */}
      <div
        className="flex overflow-x-auto gap-2 px-3 py-2"
        style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}
      >
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className="px-4 py-1 rounded-full text-sm whitespace-nowrap transition-colors duration-200"
            style={{
              backgroundColor: activeCategory === cat.id ? GALIA.amarillo : 'transparent',
              color: activeCategory === cat.id ? GALIA.marron : GALIA.marron,
              border: `1px solid ${activeCategory === cat.id ? GALIA.amarillo : GALIA.grisLigero}`,
            }}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Products Grid */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="grid grid-cols-2 gap-2">
          {filteredProducts.map((product) => (
            <div
              key={product.id}
              className="rounded-lg overflow-hidden cursor-pointer"
              style={{ backgroundColor: GALIA.blanco }}
              onClick={() => handleAddItem(product.id, 1)}
            >
              {product.image && (
                <img src={product.image} alt={product.name} className="w-full h-20 object-cover" />
              )}
              <div className="p-2">
                <p className="text-sm font-semibold" style={{ color: GALIA.marron }}>
                  {product.name}
                </p>
                <p className="text-xs" style={{ color: GALIA.grisClaro }}>
                  ${product.price?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Bar - Fixed */}
      <div
        className="fixed bottom-0 left-0 right-0 h-20 flex items-center justify-between px-4 py-3"
        style={{ backgroundColor: GALIA.marron }}
      >
        <div className="flex flex-col">
          <p className="text-xs text-white">Total:</p>
          <p className="text-2xl font-bold" style={{ color: GALIA.amarillo }}>
            ${(order?.total || 0).toFixed(2)}
          </p>
        </div>
        <button
          onClick={() => setShowCobrarSheet(true)}
          disabled={!order || order.items.length === 0}
          className="px-6 py-3 rounded-lg font-bold text-lg transition-opacity duration-200"
          style={{
            backgroundColor: GALIA.amarillo,
            color: GALIA.marron,
            opacity: order && order.items.length > 0 ? 1 : 0.5,
            cursor: order && order.items.length > 0 ? 'pointer' : 'not-allowed',
          }}
        >
          COBRAR
        </button>
      </div>

      <CobrarBottomSheet
        isOpen={showCobrarSheet}
        orderId={order?.id}
        total={order?.total || 0}
        onConfirm={handleCobrar}
        onClose={() => setShowCobrarSheet(false)}
      />
    </div>
  )
}

export default CamareroMesa
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/CamareroMesa.jsx
git commit -m "refactor: update CamareroMesa for mobile orden view with GALIA colors"
```

---

### Task 12: Verify App.jsx Routes (No Changes Needed)

**Files:**
- Verify: `frontend/src/App.jsx`

- [ ] **Step 1: Verify routes are correctly set up for new layouts**

Expected state (from prior context):
```jsx
<Route element={<ProtectedRoute><PosLayout /></ProtectedRoute>}>
  <Route path="/pos" element={<Pos />} />
</Route>

<Route element={<ProtectedRoute><CamareroLayout /></ProtectedRoute>}>
  <Route path="/camarero" element={<Camarero />} />
  <Route path="/camarero/mesa/:mesaId" element={<CamareroMesa />} />
</Route>
```

If not already present, make sure these layouts wrap the routes. No additional changes needed if layout routing is already correct.

- [ ] **Step 2: Commit** (if any changes made)

```bash
git add frontend/src/App.jsx
git commit -m "verify: confirm App.jsx routing for new layouts"
```

---

### Task 13: Smoke Test POS Fullscreen

**Manual Testing:**

- [ ] **Step 1: Start frontend dev server**

```bash
cd frontend
npm run dev -- --port 5173
```

Expected: Server starts on http://localhost:5173

- [ ] **Step 2: Start backend API**

```bash
cd backend
python run.py
```

Expected: Flask runs on http://localhost:5001, logs show no errors

- [ ] **Step 3: Open POS in browser**

Navigate to `http://localhost:5173/pos`

Expected:
- POS header visible with "GALIA POS" title
- Salon tabs shown
- Mesas grid displays in crema background
- Mesa cards show in blanco with marrón text
- Colors match GALIA palette
- Click mesa → OrderDrawer opens on right with amarillo border
- Hover mesa → border changes to amarillo, shadow appears

- [ ] **Step 4: Test OrderDrawer interaction**

- Click "Agregar Item" → AddItemModal should open
- Add item → item appears in order with GALIA colors
- Click delete (X) → item removed
- Click "COBRAR" → CobrarBottomSheet appears from bottom

- [ ] **Step 5: Test payment flow**

- Select method of pago (Efectivo, Tarjeta, Otro)
- Click "Confirmar" → order closed, mesa refreshed
- Mesa status should update to "Libre"

- [ ] **Step 6: Commit smoke test observations** (if no issues found)

```bash
git commit -m "test: verify POS fullscreen visual design and interactions"
```

---

### Task 14: Smoke Test Camarero Mobile

**Manual Testing:**

- [ ] **Step 1: Open Camarero in browser**

Navigate to `http://localhost:5173/camarero`

Expected:
- Header with maroon background, white "Mi Turno - Camarero" text
- Salon selector tabs below header
- Mesas grid (2 columns) with crema background
- Mesa cards styled with GALIA colors

- [ ] **Step 2: Test Pantalla 1 (Salón)**

- Click mesa → navigates to `/camarero/mesa/:mesaId`
- Verify URL updates

- [ ] **Step 3: Test Pantalla 2 (Orden)**

Navigate directly to `/camarero/mesa/1` (or use navigation)

Expected:
- Header with back button, "Mesa X" title
- Category tabs with scroll
- Product grid (2 columns)
- Fixed bottom bar with total in amarillo
- "COBRAR" button in amarillo

- [ ] **Step 4: Test product addition**

- Click product → added to order
- Bottom bar total updates
- Items appear in bottom bar (if there's a summary)

- [ ] **Step 5: Test cobrar flow**

- Click "COBRAR" → CobrarBottomSheet appears
- Select payment method
- Click "Confirmar" → order closed, navigate back to `/camarero`

- [ ] **Step 6: Commit smoke test observations**

```bash
git commit -m "test: verify Camarero mobile visual design and tab navigation"
```

---

### Task 15: Final Visual Verification & Polish

**Refinement Checklist:**

- [ ] **Step 1: Check color consistency**

Verify all colors match GALIA palette (hex values from colors.js):
- Amarillo buttons, active states, totals
- Marrón text, borders, headers
- Crema backgrounds
- Blanco cards
- Gris secondary text

- [ ] **Step 2: Check responsive behavior**

Test on multiple widths:
- Desktop (1440px): 6-col mesa grid
- Tablet (768px): 3-col mesa grid, narrower panel
- Mobile (375px): 2-col mesa grid, camarero mobile optimized

- [ ] **Step 3: Check transitions & animations**

- Button hovers smooth (200ms)
- Bottom sheet slides up smoothly
- Tab switches without jank

- [ ] **Step 4: Check accessibility**

- Text contrast adequate (dark text on light bg)
- Buttons have :focus states
- No keyboard traps

- [ ] **Step 5: Make minor adjustments if needed**

If any visual tweaks needed (spacing, colors, sizes), update components and test again.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "refactor: complete POS + Camarero visual redesign with GALIA colors"
```

---

## Success Criteria

- ✅ All components refactored with GALIA color palette (#D4E157, #6B4C5C, #E8DCC4, etc.)
- ✅ POS fullscreen shows grid + right panel layout
- ✅ Camarero mobile uses tab navigation (salón + orden)
- ✅ Bottom sheet payment flow works end-to-end
- ✅ Responsive design: 6 cols desktop → 2 cols mobile
- ✅ All transitions smooth, no layout shift
- ✅ Colors verified in browser (not just code)
- ✅ Smoke tests pass on desktop and mobile browsers
- ✅ No console errors or warnings
