# Camarero UX Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add map/list view toggle and redesign order visualization using a bottom sheet, improving the waiter (camarero) experience to match POS system quality.

**Architecture:** Refactor Camarero main component to support two view modes (map/list), create a reusable TableListView component, and replace the page-based order view with a BottomSheet modal. Reuse existing SalonFloorPlan from POS without modification.

**Tech Stack:** React 18, Tailwind CSS, Lucide icons, existing services (salonsService, ordersService, productCategoriesService, productsService), GALIA color constants.

---

## File Structure

**New Components:**
- `frontend/src/components/camarero/CamareroTableListView.jsx` - Table list view for mesas
- `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx` - Order bottom sheet modal

**Modified Components:**
- `frontend/src/pages/Camarero.jsx` - Add view toggle, integrate new components, manage order sheet state

**Reused (no changes):**
- `frontend/src/components/pos/SalonFloorPlan.jsx` - Map visualization
- `frontend/src/services/*.js` - Existing service layer

**Deprecated:**
- `frontend/src/pages/CamareroMesa.jsx` - Replaced by BottomSheet (remove after testing)

---

## Task 1: Create CamareroTableListView Component

**Files:**
- Create: `frontend/src/components/camarero/CamareroTableListView.jsx`

**Description:** Build a simple, responsive table list component that displays all mesas with status and total. This is the list view alternative to the map view.

- [ ] **Step 1: Create component file with imports**

Create `frontend/src/components/camarero/CamareroTableListView.jsx`:

```jsx
import GALIA from '../../constants/colors'

const CamareroTableListView = ({ mesas = [], onMesaClick }) => {
  return (
    <div className="w-full h-full overflow-y-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-white border-b" style={{ borderColor: GALIA.grisLigero }}>
          <tr>
            <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: GALIA.marron }}>
              Mesa
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: GALIA.marron }}>
              Estado
            </th>
            <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: GALIA.marron }}>
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {mesas.map((mesa, index) => (
            <tr
              key={mesa.id}
              onClick={() => onMesaClick(mesa)}
              className="border-b cursor-pointer hover:bg-gray-50 transition-colors"
              style={{ borderColor: GALIA.grisLigero, backgroundColor: index % 2 === 0 ? 'white' : GALIA.crema }}
            >
              <td className="px-4 py-4 text-base font-semibold" style={{ color: GALIA.marron }}>
                {mesa.numero}
              </td>
              <td className="px-4 py-4">
                <span
                  className="inline-block px-3 py-1 rounded-full text-sm font-semibold"
                  style={{
                    backgroundColor: mesa.status === 'libre' ? GALIA.verde : GALIA.amarillo,
                    color: mesa.status === 'libre' ? 'white' : GALIA.marron
                  }}
                >
                  {mesa.status === 'libre' ? 'Libre' : 'Ocupada'}
                </span>
              </td>
              <td className="px-4 py-4 text-right font-semibold" style={{ color: GALIA.marron }}>
                {mesa.openOrder ? (
                  <div>
                    <div style={{ color: GALIA.amarillo }}>
                      ${parseFloat(mesa.openOrder.total || 0).toFixed(2)}
                    </div>
                    <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                      ({mesa.openOrder.items?.length || 0} ítems)
                    </div>
                  </div>
                ) : (
                  <span style={{ color: GALIA.grisClaro }}>-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default CamareroTableListView
```

- [ ] **Step 2: Verify component structure**

Check the file exists and has correct structure:
```bash
ls -la frontend/src/components/camarero/CamareroTableListView.jsx
```

Expected: File exists at that path

---

## Task 2: Create CamareroOrderBottomSheet Component

**Files:**
- Create: `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx`

**Description:** Build a bottom sheet modal that displays order details, product categories, and allows add/remove items and payment processing.

- [ ] **Step 1: Create component file with imports and header structure**

Create `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx`:

```jsx
import { useState, useEffect } from 'react'
import { X, ChevronDown, Trash2, Printer } from 'lucide-react'
import GALIA from '../../constants/colors'
import productCategoriesService from '../../services/productCategoriesService'
import productsService from '../../services/productsService'
import salePrinting from '../../services/salePrinting'

const CamareroOrderBottomSheet = ({
  isOpen,
  order,
  mesaNumber,
  onClose,
  onAddItem,
  onRemoveItem,
  onCobrar
}) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [showOrderItems, setShowOrderItems] = useState(false)
  const [loading, setLoading] = useState(false)
  const [printing, setPrinting] = useState(false)

  useEffect(() => {
    if (isOpen && order) {
      fetchCategoriesAndProducts()
    }
  }, [isOpen, order])

  const fetchCategoriesAndProducts = async () => {
    try {
      setLoading(true)
      const [catRes, prodRes] = await Promise.all([
        productCategoriesService.getCategories(),
        productsService.getProducts({ per_page: 100 })
      ])
      setCategories(catRes.product_categories || [])
      setProducts(prodRes.products || [])
      if (catRes.product_categories && catRes.product_categories.length > 0) {
        setActiveCategory(catRes.product_categories[0].id)
      }
    } catch (err) {
      console.error('Error fetching categories/products:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePrintControl = async () => {
    if (!order) return
    setPrinting(true)
    try {
      await salePrinting.printControl(order, order.items || [], order.total || 0, 0)
    } catch (err) {
      console.error('Error al imprimir control:', err)
    } finally {
      setPrinting(false)
    }
  }

  const handleProductVariantClick = async (variant) => {
    try {
      await onAddItem(variant.id, 1)
    } catch (err) {
      console.error('Error adding item:', err)
    }
  }

  if (!isOpen || !order) return null

  const categoryProducts = products.filter(p => p.category_id === activeCategory)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-end">
      <div className="w-screen bg-white rounded-t-lg max-h-[90vh] overflow-y-auto flex flex-col" onClick={(e) => e.stopPropagation()}>
        
        {/* Header - Sticky */}
        <div className="sticky top-0 z-10 px-4 py-3 shadow-sm border-b flex items-center justify-between" style={{ backgroundColor: GALIA.marron, borderColor: GALIA.grisLigero }}>
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white hover:opacity-80"
          >
            <X className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Mesa {mesaNumber}</h2>
          </button>
          <div className="text-right">
            <div className="text-xs text-white opacity-80">Total</div>
            <div className="text-xl font-bold" style={{ color: GALIA.amarillo }}>
              ${parseFloat(order.total || 0).toFixed(2)}
            </div>
          </div>
        </div>

        {/* Categories tabs - Sticky */}
        <div className="sticky top-0 z-9 flex gap-2 px-3 py-2 overflow-x-auto" style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className="px-4 py-2 whitespace-nowrap text-sm rounded-full border transition"
              style={{
                backgroundColor: activeCategory === cat.id ? GALIA.amarillo : 'transparent',
                color: GALIA.marron,
                borderColor: activeCategory === cat.id ? GALIA.amarillo : GALIA.grisLigero
              }}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Products grid - Scrollable */}
        <div className="flex-1 overflow-y-auto px-3 py-3 pb-80">
          {loading ? (
            <div className="text-center py-8" style={{ color: GALIA.grisClaro }}>
              Cargando productos...
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {categoryProducts.map(product => (
                <div key={product.id} className="rounded-lg overflow-hidden" style={{ backgroundColor: GALIA.blanco }}>
                  {product.variants && product.variants.length > 0 ? (
                    <div className="space-y-1">
                      {product.variants.map(variant => (
                        <button
                          key={variant.id}
                          onClick={() => handleProductVariantClick(variant)}
                          className="w-full text-left p-2 transition hover:bg-gray-50"
                          style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}
                        >
                          <div className="font-semibold text-sm" style={{ color: GALIA.marron }}>
                            {product.name}
                          </div>
                          <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                            {variant.name}
                          </div>
                          <div className="text-sm font-bold" style={{ color: GALIA.amarillo }}>
                            ${parseFloat(variant.price).toFixed(2)}
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <button className="w-full p-2 text-center">
                      <div className="font-medium" style={{ color: GALIA.marron }}>
                        {product.name}
                      </div>
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Order items section - Fixed at bottom */}
        <div className="fixed bottom-0 left-0 right-0 rounded-t-lg shadow-lg bg-white max-h-1/3 overflow-y-auto" style={{ backgroundColor: GALIA.blanco }}>
          
          {/* Order header - Collapsible */}
          <div className="sticky top-0 px-4 py-2 flex items-center justify-between border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
            <span className="font-semibold" style={{ color: GALIA.marron }}>
              Orden ({order.items?.length || 0} ítems)
            </span>
            <button
              onClick={() => setShowOrderItems(!showOrderItems)}
              className="p-1 rounded transition"
              style={{ color: GALIA.marron }}
            >
              <ChevronDown className={`h-5 w-5 transition-transform ${showOrderItems ? 'rotate-180' : ''}`} />
            </button>
          </div>

          {/* Order items - Shown when expanded */}
          {showOrderItems && (
            <>
              <div className="px-4 py-2 space-y-2 max-h-32 overflow-y-auto">
                {order.items && order.items.length > 0 ? (
                  order.items.map(item => (
                    <div
                      key={item.id}
                      className="flex justify-between items-center py-1"
                      style={{ borderBottom: `1px solid ${GALIA.grisLigero}` }}
                    >
                      <div className="flex-1">
                        <div className="text-sm font-medium" style={{ color: GALIA.marron }}>
                          {item.product_name}
                        </div>
                        <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                          {item.variant_name}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm" style={{ color: GALIA.marron }}>
                          {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)}
                        </div>
                        <button
                          onClick={() => onRemoveItem(item.id)}
                          className="p-1 rounded transition"
                          style={{ color: '#dc2626' }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4" style={{ color: GALIA.grisClaro }}>
                    Sin items
                  </div>
                )}
              </div>

              {/* Action buttons */}
              <div className="px-4 py-3 space-y-2" style={{ borderTop: `1px solid ${GALIA.grisLigero}` }}>
                <button
                  onClick={() => {}}
                  className="w-full py-2 rounded font-semibold transition-opacity text-sm"
                  style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
                  onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
                  onMouseLeave={(e) => (e.target.style.opacity = '1')}
                >
                  Agregar Item
                </button>
                <button
                  onClick={handlePrintControl}
                  disabled={!order.items || order.items.length === 0 || printing}
                  className="w-full py-2 rounded font-semibold transition-opacity text-sm flex items-center justify-center gap-2 disabled:opacity-50"
                  style={{ backgroundColor: '#3B82F6', color: 'white' }}
                  onMouseEnter={(e) => {
                    if (!e.target.disabled) e.target.style.opacity = '0.9'
                  }}
                  onMouseLeave={(e) => {
                    if (!e.target.disabled) e.target.style.opacity = '1'
                  }}
                >
                  <Printer size={16} />
                  {printing ? 'Imprimiendo...' : 'Control Mesa'}
                </button>
                <button
                  onClick={() => onCobrar('Efectivo')}
                  disabled={!order.items || order.items.length === 0}
                  className="w-full py-3 font-bold rounded-lg transition text-base disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ backgroundColor: GALIA.marron, color: 'white' }}
                  onMouseEnter={(e) => {
                    if (!e.target.disabled) e.target.style.opacity = '0.9'
                  }}
                  onMouseLeave={(e) => {
                    if (!e.target.disabled) e.target.style.opacity = '1'
                  }}
                >
                  COBRAR
                </button>
              </div>
            </>
          )}

          {/* Collapsed view - Just show total */}
          {!showOrderItems && (
            <div className="px-4 py-3 text-center">
              <div className="text-2xl font-bold" style={{ color: GALIA.amarillo }}>
                ${parseFloat(order.total || 0).toFixed(2)}
              </div>
              <div className="text-xs mt-1" style={{ color: GALIA.grisClaro }}>
                {order.items?.length || 0} ítems
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CamareroOrderBottomSheet
```

- [ ] **Step 2: Verify component structure**

Check the file exists:
```bash
ls -la frontend/src/components/camarero/CamareroOrderBottomSheet.jsx
```

Expected: File exists at that path

---

## Task 3: Refactor Camarero.jsx - Add View Toggle and Integrate Components

**Files:**
- Modify: `frontend/src/pages/Camarero.jsx`

**Description:** Update main Camarero component to support map/list view toggle and integrate the new BottomSheet for order display.

- [ ] **Step 1: Update imports to include new components and icon**

Replace the imports section of `frontend/src/pages/Camarero.jsx` with:

```jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Map, List } from 'lucide-react'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import GALIA from '../constants/colors'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'
import CamareroTableListView from '../components/camarero/CamareroTableListView'
import CamareroOrderBottomSheet from '../components/camarero/CamareroOrderBottomSheet'
```

- [ ] **Step 2: Update component state to include viewMode and order sheet state**

Replace the `const Camarero = () => {` section up to and including the state declarations with:

```jsx
const Camarero = () => {
  const navigate = useNavigate()

  // View and salon state
  const [viewMode, setViewMode] = useState('map') // 'map' or 'list'
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Order sheet state
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showOrderSheet, setShowOrderSheet] = useState(false)
  const [selectedMesa, setSelectedMesa] = useState(null)
```

- [ ] **Step 3: Keep existing fetchAll function unchanged**

The `fetchAll` and polling logic remain the same (no changes needed).

- [ ] **Step 4: Update handleMesaClick to open BottomSheet instead of navigating**

Replace the `handleMesaClick` function with:

```jsx
  const handleMesaClick = async (mesa) => {
    setSelectedMesa(mesa)
    if (mesa.status === 'libre') {
      // Create new order
      try {
        const order = await ordersService.createOrder({
          mesa_id: mesa.id,
          salon_id: activeSalon
        })
        setSelectedOrder(order)
        setShowOrderSheet(true)
      } catch (err) {
        setError('Error al crear orden')
      }
    } else if (mesa.status === 'ocupada') {
      // Open existing order
      const order = openOrders.find(o => o.mesa_id === mesa.id)
      if (order) {
        try {
          const fullOrder = await ordersService.getOrder(order.id)
          setSelectedOrder(fullOrder)
          setShowOrderSheet(true)
        } catch (err) {
          setError('Error al cargar la orden')
        }
      }
    }
  }
```

- [ ] **Step 5: Add handler for adding items to order**

Add this new function after `handleMesaClick`:

```jsx
  const handleAddItem = async (productVariantId, quantity) => {
    try {
      const updated = await ordersService.addItem(selectedOrder.id, {
        product_variant_id: productVariantId,
        quantity
      })
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al agregar item')
    }
  }
```

- [ ] **Step 6: Add handler for removing items**

Add this function after `handleAddItem`:

```jsx
  const handleRemoveItem = async (itemId) => {
    try {
      const updated = await ordersService.removeItem(selectedOrder.id, itemId)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al eliminar item')
    }
  }
```

- [ ] **Step 7: Add handler for cobrar (payment)**

Add this function after `handleRemoveItem`:

```jsx
  const handleCobrar = async (methodoPago) => {
    try {
      await ordersService.cobrar(selectedOrder.id, methodoPago)
      setShowOrderSheet(false)
      setSelectedOrder(null)
      setSelectedMesa(null)
      // Refresh data after payment
      await fetchAll()
    } catch (err) {
      setError('Error al cobrar')
    }
  }
```

- [ ] **Step 8: Update JSX return statement**

Replace the entire return statement (starting from `return (`) with:

```jsx
  return (
    <div className="h-full w-full flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-4 text-white font-semibold text-lg" style={{ backgroundColor: GALIA.marron }}>
        <span>Mi Turno - Camarero</span>
        {/* View mode toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('map')}
            className="p-2 rounded transition"
            title="Vista Mapa"
            style={{
              backgroundColor: viewMode === 'map' ? GALIA.amarillo : 'transparent',
              color: viewMode === 'map' ? GALIA.marron : 'white'
            }}
          >
            <Map size={20} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className="p-2 rounded transition"
            title="Vista Lista"
            style={{
              backgroundColor: viewMode === 'list' ? GALIA.amarillo : 'transparent',
              color: viewMode === 'list' ? GALIA.marron : 'white'
            }}
          >
            <List size={20} />
          </button>
        </div>
      </div>

      {/* Salon tabs */}
      <div className="flex gap-2 px-3 py-2 overflow-x-auto border-b" style={{ borderColor: GALIA.grisLigero }}>
        {salons.map(salon => (
          <button
            key={salon.id}
            onClick={() => setActiveSalon(salon.id)}
            className="px-4 py-2 whitespace-nowrap text-sm rounded transition"
            style={{
              borderBottom: activeSalon === salon.id ? `3px solid ${GALIA.amarillo}` : 'none',
              color: activeSalon === salon.id ? GALIA.marron : GALIA.grisClaro,
              fontWeight: activeSalon === salon.id ? '600' : '400'
            }}
          >
            {salon.name}
          </button>
        ))}
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full" style={{ color: GALIA.grisClaro }}>
            Cargando...
          </div>
        ) : viewMode === 'map' ? (
          <div className="h-full w-full p-2 md:p-4">
            <SalonFloorPlan
              mesas={allMesas[activeSalon] || []}
              onMesaClick={handleMesaClick}
              isEditMode={false}
            />
          </div>
        ) : (
          <div className="h-full w-full">
            <CamareroTableListView
              mesas={(allMesas[activeSalon] || []).map(m => ({
                ...m,
                openOrder: openOrders.find(o => o.mesa_id === m.id) || null
              }))}
              onMesaClick={handleMesaClick}
            />
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="p-3 text-sm" style={{ backgroundColor: '#fee', color: '#c33' }}>
          {error}
        </div>
      )}

      {/* Order Bottom Sheet */}
      <CamareroOrderBottomSheet
        isOpen={showOrderSheet}
        order={selectedOrder}
        mesaNumber={selectedMesa?.numero || selectedMesa?.id}
        onClose={() => {
          setShowOrderSheet(false)
          setSelectedOrder(null)
          setSelectedMesa(null)
        }}
        onAddItem={handleAddItem}
        onRemoveItem={handleRemoveItem}
        onCobrar={handleCobrar}
      />
    </div>
  )
}

export default Camarero
```

- [ ] **Step 9: Verify file syntax**

Run linter check:
```bash
cd frontend && npm run lint
```

Expected: No errors in Camarero.jsx

- [ ] **Step 10: Commit changes**

```bash
git add frontend/src/pages/Camarero.jsx
git commit -m "feat: add map/list view toggle and bottom sheet order display to camarero"
```

---

## Task 4: Test the Implementation

**Files:**
- Test: `frontend/src/pages/Camarero.jsx` (manual testing)
- Test: `frontend/src/components/camarero/CamareroTableListView.jsx` (manual testing)
- Test: `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx` (manual testing)

**Description:** Verify that all functionality works correctly in both map and list views.

- [ ] **Step 1: Start the development server**

```bash
cd frontend && npm run dev
```

Expected: Server running on http://localhost:5173

- [ ] **Step 2: Navigate to the camarero view**

Open browser: `http://localhost:5173/camarero`

Expected: See the camarero interface with table view

- [ ] **Step 3: Test map view toggle**

Click the map icon in the header.

Expected: 
- View switches to map view (SalonFloorPlan)
- Tables displayed with their positions
- Yellow highlight on map icon

- [ ] **Step 4: Test list view toggle**

Click the list icon in the header.

Expected:
- View switches to list view
- Table shows: Mesa, Estado, Total columns
- All mesas from active salon visible
- Yellow highlight on list icon

- [ ] **Step 5: Test salon switching**

Click on different salon tabs.

Expected:
- Tables update to show selected salon
- View mode remains the same (map or list)
- Data refreshes correctly

- [ ] **Step 6: Test creating order on free table (map view)**

In map view, click on a free (green) table.

Expected:
- BottomSheet opens from bottom
- Correct mesa number shown in header
- Total shows $0.00
- Order items section collapsed
- Product categories and products visible

- [ ] **Step 7: Test creating order on free table (list view)**

Switch to list view, click on a free table.

Expected:
- Same behavior as Step 6
- BottomSheet opens correctly from list view

- [ ] **Step 8: Test adding product to order**

With BottomSheet open, click on any product.

Expected:
- Product added to order
- Total amount updates
- Item count increases

- [ ] **Step 9: Test expanding order items**

Click the chevron on "Orden" header.

Expected:
- Order items section expands
- Shows list of added items with quantity, price
- Trash icon visible for each item
- Chevron points down (rotated)

- [ ] **Step 10: Test removing item from order**

Click trash icon on any item.

Expected:
- Item removed from order
- Total updates
- Item count decreases
- If last item removed, collapse indicator updates

- [ ] **Step 11: Test printing control (comanda)**

With items in order, click "Control Mesa" button.

Expected:
- Button shows "Imprimiendo..." temporarily
- No errors in console
- (Actual printing depends on printer setup)

- [ ] **Step 12: Test payment flow**

With items in order, click "COBRAR" button.

Expected:
- BottomSheet closes
- Order marked as paid
- Returns to table view
- Data refreshes
- Table status changes to libre

- [ ] **Step 13: Test occupied table**

On a table with existing order, click it.

Expected:
- BottomSheet opens
- Shows existing order with items
- Total displays correctly
- Can add more items
- Can print and pay

- [ ] **Step 14: Test data polling**

Make a change in another window (e.g., add item via POS).

Expected:
- Every 10 seconds data refreshes
- Changes appear in camarero view (if not actively editing)

- [ ] **Step 15: Test error handling**

Try to perform action with network offline (dev tools → offline).

Expected:
- Error message appears at bottom
- Interface remains usable
- Can retry when back online

- [ ] **Step 16: Verify responsive design on mobile**

Resize browser to mobile width (375px) or use Chrome DevTools.

Expected:
- All elements readable on mobile
- Buttons large enough to tap
- BottomSheet takes full height
- No horizontal scrolling
- Header icons visible and usable

---

## Task 5: Clean Up and Final Adjustments

**Files:**
- Modify: Routes configuration (if CamareroMesa route still exists)
- Delete: `frontend/src/pages/CamareroMesa.jsx` (after verifying BottomSheet works)

**Description:** Remove deprecated files and verify no broken routes remain.

- [ ] **Step 1: Check for references to CamareroMesa route**

Search the codebase:
```bash
grep -r "camarero/mesa" frontend/src --include="*.jsx" --include="*.js"
```

Expected: No matches (we removed navigation to this page in Camarero.jsx)

- [ ] **Step 2: Check router configuration**

Look at `frontend/src/App.jsx` or main routing file:
```bash
grep -A2 -B2 "CamareroMesa\|camarero/mesa" frontend/src/App.jsx
```

If found, note the line numbers for removal in next step.

- [ ] **Step 3: Remove CamareroMesa route if it exists**

If the route exists in your router config, remove it. For example, if in App.jsx:

```jsx
// REMOVE THIS:
{
  path: '/camarero/mesa/:mesaId',
  element: <CamareroMesa />
}

// Also remove the import:
import CamareroMesa from './pages/CamareroMesa'
```

- [ ] **Step 4: Verify no import errors**

Check for any remaining imports of CamareroMesa:
```bash
grep -r "CamareroMesa" frontend/src --include="*.jsx" --include="*.js"
```

Expected: No matches

- [ ] **Step 5: Delete the deprecated file**

```bash
rm frontend/src/pages/CamareroMesa.jsx
```

- [ ] **Step 6: Run linter to verify no errors**

```bash
cd frontend && npm run lint
```

Expected: No errors

- [ ] **Step 7: Test routing still works**

Navigate in app to camarero view:
```
http://localhost:5173/camarero
```

Expected: Page loads without errors, no 404 messages

- [ ] **Step 8: Commit cleanup**

```bash
git add frontend/src/App.jsx frontend/src/components/camarero/
git rm frontend/src/pages/CamareroMesa.jsx
git commit -m "feat: deprecate CamareroMesa page, use bottom sheet instead"
```

---

## Task 6: Visual Polish and Fine-Tuning

**Files:**
- Modify: `frontend/src/components/camarero/CamareroTableListView.jsx`
- Modify: `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx`

**Description:** Improve visual details and ensure consistent spacing and typography.

- [ ] **Step 1: Review and adjust spacing in CamareroTableListView**

Open `frontend/src/components/camarero/CamareroTableListView.jsx` and review the table padding. If font sizes or padding need adjustment for mobile, update the className and style props to use responsive sizes.

No specific changes required if existing sizing works well. This is a review step.

- [ ] **Step 2: Verify color consistency**

Check that all color values match GALIA constants:
```bash
grep -n "color:" frontend/src/components/camarero/CamareroTableListView.jsx
grep -n "backgroundColor:" frontend/src/components/camarero/CamareroTableListView.jsx
```

Expected: All colors use GALIA constants (no hardcoded hex values except possibly white/black)

- [ ] **Step 3: Test font sizes on mobile**

Open Dev Tools, set mobile width (375px), navigate to `/camarero` in list view.

Expected:
- Table headers readable
- Mesa numbers clear
- Status badges appropriately sized
- Total amounts visible

If any text is too small or too large, note it for adjustment in the next step.

- [ ] **Step 4: Verify BottomSheet scrolling behavior**

On mobile, open an order with many items, expand order items section.

Expected:
- Items scroll smoothly
- Buttons remain accessible at bottom
- No content cut off
- Padding appropriate on all sides

- [ ] **Step 5: Test category tab overflow**

With many product categories, scroll through category tabs.

Expected:
- Tabs scroll horizontally
- Selected tab stays visible
- No lag or scroll issues

- [ ] **Step 6: Verify button states and hover effects**

Test hover states on desktop and tap states on mobile.

Expected:
- Buttons show opacity change on hover (0.9)
- Disabled buttons show correct styling (0.5 opacity)
- Touch feedback on mobile

- [ ] **Step 7: Test with different data volumes**

Create several orders with varying item counts (1 item, 5 items, 20 items).

Expected:
- UI scales correctly
- No performance degradation
- Scrolling remains smooth
- Totals calculate correctly

- [ ] **Step 8: Final visual review**

Compare visual appearance with POS OrderDrawer for consistency.

Expected:
- Similar spacing and typography hierarchy
- Consistent color usage
- Professional appearance

- [ ] **Step 9: Commit polish changes**

```bash
git add frontend/src/components/camarero/
git commit -m "style: refine spacing, typography, and responsive design in camarero components"
```

---

## Self-Review Checklist

- [ ] **Spec Coverage:** 
  - ✓ View mode toggle (map/list) implemented in Camarero.jsx
  - ✓ SalonFloorPlan reused for map view
  - ✓ CamareroTableListView created for list view with mesa/estado/total
  - ✓ CamareroOrderBottomSheet created with categories, products, order items
  - ✓ Add/remove/cobrar functionality integrated
  - ✓ All existing functionality maintained

- [ ] **Placeholder Scan:** No "TBD", "TODO", or incomplete references in code
  
- [ ] **Type Consistency:** 
  - Prop names consistent across components
  - Function signatures match between calling code and implementations
  - State variable names consistent

- [ ] **No Hardcoded Values:** All colors use GALIA constants, no magic numbers in spacing

- [ ] **Complete Code:** Every step contains full, working code (not pseudocode or skipped details)

- [ ] **Testable:** Each task produces working, observable results

- [ ] **Commits:** Each major task has a clear commit with descriptive message

---

## Execution Options

Plan is complete and saved. Two options to proceed:

**Option 1: Subagent-Driven (Recommended)**
- I dispatch a fresh subagent per task
- Each task reviewed before moving to next
- Fast iteration, clear checkpoints
- Best for: Parallel work, complex tasks, need oversight

**Option 2: Inline Execution**
- Execute tasks sequentially in this session
- Batch review at completion checkpoints
- More efficient for straightforward implementation
- Best for: Quick implementation, simple tasks, prefer direct guidance

Which approach would you like?
