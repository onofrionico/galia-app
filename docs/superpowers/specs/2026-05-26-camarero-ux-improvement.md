# Camarero UX Improvement - Design Spec

**Date:** 2026-05-26  
**Status:** In Design  
**Priority:** Medium  

## Overview

Improve the waiter (camarero) experience by adding a map/list view toggle for table visualization and redesigning the order sheet to use a bottom sheet pattern with a cleaner visual design inspired by the POS system.

## Goals

1. Provide two viewing modes for tables: visual floor plan map and simple list view
2. Improve order visualization with a bottom sheet that maintains visibility of tables
3. Align visual design with the more polished POS system
4. Maintain all existing functionality while improving UX

## Current State

**Camarero.jsx:**
- Shows salon tabs and a 2-column grid of tables
- Each table card shows: number, status (libre/ocupada), and item count
- Polling every 10 seconds for data updates
- Click on table navigates to detail page

**CamareroMesa.jsx:**
- Full page view of a single table's order
- Category tabs and product grid (2 columns)
- Fixed bottom bar showing order items and payment options
- Can add/remove items and process payment (cobrar)

**Problems identified:**
- Limited viewing modes (only grid view, no list option)
- Order detail page is awkward - navigates away from table view
- Design is less polished than POS system

## Design Solution

### 1. View Mode Toggle in Camarero.jsx

**Changes:**
- Add toggle in header: "Mapa" / "Lista"
- Store view mode in component state
- Persist view preference in localStorage (optional, for next session)

**Map View:**
- Use `SalonFloorPlan` component from POS (shows tables positioned by pos_x/pos_y)
- No edit mode (camarero cannot move tables)
- Click table → open order in BottomSheet

**List View:**
- Show new `CamareroTableListView` component
- Table columns: Mesa | Estado | Total
- Row includes: mesa number, status badge (Libre/Ocupada), total amount with item count
- Clickable rows → open order in BottomSheet
- Same data sources and polling as map view

### 2. New Component: CamareroTableListView

**Path:** `frontend/src/components/camarero/CamareroTableListView.jsx`

**Props:**
- `mesas` (array): List of tables with order data
- `onMesaClick` (function): Called when user selects a table

**Structure:**
```
┌─────────────────────────────────────────┐
│ Mesa │ Estado    │ Total                 │
├─────────────────────────────────────────┤
│  1   │ Libre     │ -                     │
│  2   │ Ocupada   │ $45.50 (3 ítems)     │
│  3   │ Libre     │ -                     │
│  4   │ Ocupada   │ $120.00 (5 ítems)    │
└─────────────────────────────────────────┘
```

**Features:**
- Responsive table using Tailwind
- Status badge: Green for "Libre", Yellow for "Ocupada"
- Show total only if mesa is occupied
- Show item count in parentheses
- Hover effect on rows
- Click anywhere on row → calls onMesaClick with mesa object

**Styling:**
- Use GALIA color constants
- Alternating row backgrounds (light/lighter)
- Clear typography hierarchy

### 3. New Component: CamareroOrderBottomSheet

**Path:** `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx`

**Props:**
- `isOpen` (boolean): Whether bottom sheet is visible
- `order` (object): Order object with items, total, mesa info
- `onClose` (function): Called when user closes the sheet
- `onAddItem` (function): Called when add item is clicked
- `onRemoveItem` (function): Called with itemId when removing item
- `onCobrar` (function): Called with payment method when user clicks COBRAR
- `mesaNumber` (string): Display table number in header

**Layout:**

**Header (sticky):**
- Back arrow + Mesa #{mesaNumber}
- Right side: "Total" label and amount in yellow
- Background: GALIA.crema

**Content Area (scrollable):**
- Category tabs (horizontal scroll) - same categories as products
- Product grid (2 columns) with product cards
- Each product card shows: name, variant (if applicable), price
- Click product → add to order

**Order Summary (collapsible):**
- Header: "Orden ({count} ítems)" with chevron icon
- Expandable/collapsible state
- When expanded shows:
  - List of items with: product name, variant, quantity, unit price, subtotal
  - Delete button (X icon) for each item
  - Scrollable if many items

**Footer (sticky):**
When order summary expanded:
- [Agregar Item] button (yellow/gold)
- [Control Mesa] button (blue, print comanda)
- [COBRAR] button (brown, main action)
- Optional [Cancelar Orden] button if order is empty

**Styling:**
- Use GALIA colors matching POS OrderDrawer
- Responsive padding and sizing
- Smooth animations for expand/collapse
- Icons from lucide-react

**Functionality:**
- Opens as modal BottomSheet (fixed position from bottom)
- Close button (X) and back arrow to close
- Fetches and displays current order data
- Real-time updates when items added/removed
- Payment method selection via modal (existing flow)

### 4. Modified Component: Camarero.jsx

**Changes:**
- Add viewMode state (useState): "map" | "list"
- Add viewMode toggle buttons in header
- Conditional rendering: Show SalonFloorPlan or CamareroTableListView based on viewMode
- Integrate CamareroOrderBottomSheet:
  - Show/hide state via showOrderSheet boolean
  - Pass selected mesa and order data to sheet
  - Handle onClose, onAddItem, onRemoveItem, onCobrar callbacks

**Structure:**
```
Camarero
├── Header
│   ├── Title + Salon tabs
│   └── View mode toggle [Mapa | Lista]
├── Main Content (conditionally rendered)
│   ├── Map View: SalonFloorPlan
│   └── List View: CamareroTableListView
└── Modal (conditionally rendered)
    └── CamareroOrderBottomSheet
```

**Behavior:**
- Same polling interval (10 seconds)
- Same data sources (salonsService, ordersService)
- Click table in any view → open BottomSheet
- BottomSheet manages its own open/close state
- Refreshing order data after actions (add item, remove, pay)

### 5. Deprecated/Removed Component

**CamareroMesa.jsx:**
- This page will be replaced by CamareroOrderBottomSheet
- No longer used as a route after changes
- Can be removed after successful migration and testing

## Data Flow

```
Camarero.jsx (main)
├── Fetches: salons, open orders, all mesas per salon
├── State: viewMode, activeSalon, allMesas, openOrders, selectedOrder, showOrderSheet
│
├── Renders:
│   ├── Header (with viewMode toggle)
│   ├── SalonFloorPlan (if viewMode === 'map')
│   └── CamareroTableListView (if viewMode === 'list')
│
├── On mesa click:
│   ├── Set selectedOrder
│   └── Set showOrderSheet = true
│
└── CamareroOrderBottomSheet
    ├── Displays: categories, products, order items
    ├── On add product: Call ordersService.addItem()
    ├── On remove item: Call ordersService.removeItem()
    └── On cobrar: Call ordersService.cobrar() then close
```

## Files to Create

1. `frontend/src/components/camarero/CamareroTableListView.jsx`
2. `frontend/src/components/camarero/CamareroOrderBottomSheet.jsx`

## Files to Modify

1. `frontend/src/pages/Camarero.jsx` - Add view toggle, integrate new components
2. `frontend/src/pages/CamareroMesa.jsx` - Deprecated (can remove after testing)

## Files to Reuse (No Changes)

- `frontend/src/components/pos/SalonFloorPlan.jsx` - Used directly for map view
- `frontend/src/services/salonsService.js` - Existing service
- `frontend/src/services/ordersService.js` - Existing service
- `frontend/src/services/productCategoriesService.js` - Existing service
- `frontend/src/services/productsService.js` - Existing service

## Styling and Colors

All components use `frontend/src/constants/colors.js` (GALIA object):
- `GALIA.crema` - Light background
- `GALIA.marron` - Dark brown (text, primary)
- `GALIA.amarillo` - Yellow/gold (accent, important buttons)
- `GALIA.grisLigero` - Light gray (borders)
- `GALIA.grisClaro` - Medium gray (secondary text)
- `GALIA.blanco` - White (cards background)
- `GALIA.verde` - Green (status: libre)

## Responsive Design

- **Mobile (< 768px):** Bottom sheet takes full height, categories and products scroll
- **Tablet (768px - 1024px):** Same as mobile, optimized touch targets
- **Desktop (> 1024px):** Same layout but with better spacing and font sizes

## Testing Plan

1. **View Toggle:**
   - Toggle between map and list views
   - Verify map shows correct table positions
   - Verify list shows correct table data (number, status, total)

2. **Table Selection:**
   - Click table in map view → bottom sheet opens with order
   - Click table in list view → bottom sheet opens with order
   - Multiple mesa selections work correctly

3. **Order Management:**
   - Add product to order → item appears in bottom sheet
   - Remove item from order → item is removed from list
   - Total updates correctly after changes
   - Payment flow works (select method, cobrar)

4. **Data Persistence:**
   - Polling works (data updates every 10 seconds)
   - Changes from POS sync correctly to camarero
   - No stale data issues

5. **Responsive:**
   - Layout works on mobile, tablet, desktop
   - Touch interactions work on mobile
   - Bottom sheet behavior is smooth

## Success Criteria

- ✓ View toggle works (map/list)
- ✓ Map view displays accurate table layout
- ✓ List view shows all required information
- ✓ Bottom sheet opens smoothly without navigation away
- ✓ Order operations (add, remove, pay) work correctly
- ✓ Visual design matches POS system quality
- ✓ No performance degradation
- ✓ Mobile responsive and touch-friendly

## Future Improvements (Out of Scope)

- Add table filters in list view (by status, by camarero assignment)
- Add waiter assignment tracking
- Add real-time notifications for new orders
- Integrate with kitchen display system (KDS)
- Add order history/analytics
