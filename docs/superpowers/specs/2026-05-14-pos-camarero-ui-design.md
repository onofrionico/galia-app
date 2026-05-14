# POS Admin + Camarero Mobile — UI/UX Design

> **For agentic workers:** Use superpowers:subagent-driven-development to implement this spec task-by-task.

**Goal:** Redesign the POS fullscreen (admin) and Camarero mobile (waiter) interfaces with modern, minimalist aesthetics using GALIA Café's brand colors.

**Architecture:** Two separate layouts (POS fullscreen, Camarero mobile-first) with unified color system. POS uses grid + right panel; Camarero uses tab navigation. Both connect to existing Order/OrderItem backend.

**Tech Stack:** React, Tailwind CSS, lucide-react icons. Existing components refactored (MesaCard, OrderDrawer, AddItemModal); new components for layouts.

---

## Color Palette

Extracted from GALIA Café branding:

| Color | Hex | Usage | Role |
|-------|-----|-------|------|
| Amarillo Limón | `#D4E157` | Buttons, CTAs, highlights, active states | Primary accent |
| Marrón Vino | `#6B4C5C` | Text, borders, headers, dark elements | Secondary/brand |
| Crema/Beige | `#E8DCC4` | Main backgrounds, neutral spaces | Background primary |
| Blanco Cremoso | `#FFFBF8` | Cards, overlays, clean spaces | Background secondary |
| Gris Suave | `#8A8A8A` | Secondary text, disabled states | Neutral |
| Gris Claro | `#E5E5E5` | Borders, dividers, subtle separators | Borders |
| Verde Suave | `#7CB342` | "Libre" (free table) status badge | Status libre |

---

## POS Admin — Fullscreen Layout

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────┬──────────────────┐
│ HEADER (h-16, bg-[#E8DCC4])                                     │                  │
│ ├─ Logo/Title "GALIA POS" (text-[#6B4C5C])                      │  PANEL DERECHO   │
│ ├─ Salon Tabs (underline active: bg-[#D4E157])                  │  (w-80, sticky)  │
│ └─ Exit Button (text-[#6B4C5C], hover: bg-yellow)               │                  │
├─────────────────────────────────────────────────────────────────┤                  │
│                                                                 │ ┌────────────────┤
│  MAIN GRID AREA (bg-[#F5F1ED])                                  │ │ Orden #123     │
│  ├─ Mesas Cards (4-6 per row on 1080p+)                        │ │ ────────────── │
│  │  ├─ bg-[#FFFBF8], border-2 border-[#E5E5E5]                │ │ Items:         │
│  │  ├─ Número: text-4xl text-[#6B4C5C]                        │ │ ─ Item 1 ... $ │
│  │  ├─ Estado badge + border color                            │ │ ─ Item 2 ... $ │
│  │  ├─ Items count + total (text-sm text-[#8A8A8A])           │ │ ─ Item 3 ... $ │
│  │  └─ Hover: border-[#D4E157], shadow-md                     │ │                │
│  └─ Responsive: 6 cols (1440+) → 4 cols (1080) → 3 cols (768) │ │ Total: $XX.XX  │
│                                                                 │ │ (text-2xl      │
│                                                                 │ │  text-[#D4E157])
│                                                                 │ │                │
│                                                                 │ │ Botones:       │
│                                                                 │ │ [Agregar Item] │
│                                                                 │ │ [COBRAR]       │
│                                                                 │ └────────────────┤
└─────────────────────────────────────────────────────────────────┴──────────────────┘
```

### MesaCard Component

**Props:** `mesa`, `onClick`, `isDragging`

**Visual:**
- **Container:** `bg-[#FFFBF8] border-2 border-[#E5E5E5] rounded-lg p-4 cursor-pointer`
  - Hover: `border-[#D4E157] shadow-md`
  - Transition: all 200ms ease
- **Número:** `text-4xl font-bold text-[#6B4C5C]` (e.g., "5")
- **Estado Badge:**
  - Libre: `bg-[#7CB342] text-white` + text "Libre"
  - Ocupada: `bg-[#D4E157] text-[#6B4C5C]` + text "Ocupada" (attracts attention)
  - Reservada: `bg-[#E5E5E5] text-[#8A8A8A]` + text "Reservada"
  - Badge styling: `rounded-full px-3 py-1 text-xs font-semibold`
- **Info Row:** `{items.length} ítems | ${total.toFixed(2)}`
  - Style: `text-sm text-[#8A8A8A]`

### Header Component

**PosLayout Header:**
- Background: `bg-[#E8DCC4]`
- Content: `h-16 flex items-center justify-between px-6`
- Logo/Title: `text-2xl font-bold text-[#6B4C5C]` → "GALIA POS"
- Salon Selector: Buttons with border-b-2, active underline in `border-[#D4E157]`
- Exit Button: `text-[#6B4C5C] hover:bg-[#D4E157] hover:text-[#6B4C5C]` (rounded, px-4 py-2)

### Right Panel (OrderDrawer)

**Structure:**
- Width: `w-80` (fixed/sticky)
- Background: `bg-[#FFFBF8]`
- Border-left: `border-l-4 border-[#D4E157]`
- Header: `bg-[#E8DCC4] px-4 py-3`, title "Orden #X" in `text-[#6B4C5C]`

**Items List:**
- Container: `flex-1 overflow-y-auto px-4 py-3 space-y-2`
- Each item:
  - `bg-[#F5F1ED] rounded px-3 py-2`
  - Name + quantity: `text-sm text-[#6B4C5C]`
  - Price: `text-sm font-semibold text-[#6B4C5C]`
  - Delete button (X): `text-[#8A8A8A] hover:text-red-600`

**Total Section:**
- Border-t: `border-t border-[#E5E5E5]`
- Content: `px-4 py-4`
- Text: `Total: ` + amount `text-2xl font-bold text-[#D4E157]`

**Buttons:**
- "Agregar Item" (secondary):
  - `bg-[#D4E157] text-[#6B4C5C] font-semibold py-2 rounded`
  - Hover: `opacity-90`
- "COBRAR" (primary CTA):
  - `bg-[#6B4C5C] text-white font-bold py-3 rounded text-lg`
  - Hover: `bg-opacity-90`

---

## Camarero Mobile — Tab Navigation

### Overall Layout

**PosLayout (Mobile):**
- `h-screen flex flex-col bg-[#E8DCC4]`
- Header: Sticky, `bg-[#6B4C5C] text-white h-14`
- Main content: `flex-1 overflow-hidden`

### Pantalla 1: Vista Salón

**Header:**
- Text: "Mi Turno - [Salón]" centered, white, `text-lg font-semibold`
- Action: Back button (if on second screen)

**Mesas Grid:**
- Background: `bg-[#E8DCC4]` (inherited)
- Grid: `grid-cols-2 gap-3 p-3` (2 columns on mobile)
- Mesa Card (smaller than desktop):
  - `bg-[#FFFBF8] border border-[#E5E5E5] rounded-lg p-3`
  - Estado ocupada: `border-2 border-[#D4E157]`
  - Número: `text-2xl font-bold text-[#6B4C5C]`
  - Estado: Small badge, same colors as desktop
  - Tap → navigate to Pantalla 2 with mesa/order ID

### Pantalla 2: Vista Orden

**Header:**
- Text: "Mesa X - Orden" in white, `text-lg font-semibold`

**Categorías (Scroll Horizontal):**
- Container: `flex overflow-x-auto gap-2 p-3 bg-[#FFFBF8] border-b border-[#E5E5E5]`
- Botones: `px-4 py-2 rounded-full border border-[#E5E5E5] text-sm`
  - Active: `bg-[#D4E157] text-[#6B4C5C] border-[#D4E157]`
  - Inactive: `bg-transparent text-[#6B4C5C]`

**Productos Grid:**
- Container: `grid-cols-2 gap-2 p-3 overflow-y-auto pb-20` (extra bottom padding for fixed bottom bar)
- Producto Card:
  - `bg-[#FFFBF8] rounded-lg overflow-hidden cursor-pointer`
  - Image: Full width, 100px height
  - Content: `p-2`
    - Nombre: `text-sm font-semibold text-[#6B4C5C]`
    - Precio: `text-sm text-[#8A8A8A]`

**Bottom Bar (Fixed):**
- Position: `fixed bottom-0 left-0 right-0 h-16`
- Background: `bg-[#6B4C5C]`
- Layout: `flex items-center justify-between px-4`
- Total: `text-white text-lg font-semibold` + amount in `text-[#D4E157] text-xl`
- Botón "COBRAR":
  - `bg-[#D4E157] text-[#6B4C5C] font-bold py-2 px-6 rounded-lg`
  - Tap → show bottom sheet

---

## Bottom Sheet — Cobro (Payment)

**Trigger:** "COBRAR" button anywhere

**Sheet Structure:**
- Background: `bg-[#FFFBF8]`
- Appears from bottom, covers ~60% of viewport on mobile
- Header: `bg-[#6B4C5C] text-white px-4 py-3`
  - Title: "Método de Pago"
  - Close button: (X) on right

**Content:**
- Padding: `px-4 py-4`
- Total display: `text-sm text-[#8A8A8A]` label + `text-2xl text-[#D4E157]` amount

**Método Pago Options:**
- Grid: `grid-cols-3 gap-2` (3 buttons)
- Botones: `px-3 py-3 rounded border-2`
  - Inactive: `border-[#E5E5E5] text-[#6B4C5C]`
  - Active: `border-[#D4E157] bg-[#D4E157] text-[#6B4C5C]`
- Options: "Efectivo" | "Tarjeta" | "Otro"

**CTA Button:**
- Full width: `w-full py-3 bg-[#6B4C5C] text-white font-bold rounded-lg`
- Text: "Confirmar"
- On success: Close sheet → show toast "Venta registrada" → refresh order list

---

## Icons & Typography

**Icons:** lucide-react (existing integration)
- Sizes: `size-4` (small), `size-5` (medium), `size-6` (large)
- Colors: Match text color context

**Typography:**
- Headings: Inter, Poppins, or similar modern sans-serif
- Body: Same (system font fallback acceptable)
- Sizes:
  - Header titles: `text-2xl font-bold`
  - Section headings: `text-lg font-semibold`
  - Body: `text-sm` / `text-base`
  - Small text: `text-xs text-[#8A8A8A]`

---

## Interactions & Animations

**Transitions:**
- All color/border changes: `transition-all duration-200`
- Opacity changes: `transition-opacity duration-150`

**Hover States:**
- MesaCard: Border color + shadow
- Buttons: Opacity or slight scale
- Links/text: Color change + underline optional

**Mobile-specific:**
- Tab switch: Smooth slide (or fade)
- Bottom sheet: Slide up from bottom (or Modal overlay)
- No hover effects on touch devices (use :active instead)

---

## Component Changes

**Refactored/New:**
- `MesaCard.jsx` — Updated colors, sizing, status badges
- `PosLayout.jsx` — New header + grid container
- `CamareroLayout.jsx` — Mobile header + tab logic
- `OrderDrawer.jsx` — Right panel styling
- `CobrarBottomSheet.jsx` — New component for payment flow
- `Camarero.jsx` — Tab 1: salón view
- `CamareroMesa.jsx` — Tab 2: orden view

**Utilities:**
- `useResponsiveGrid()` — Helper to adjust mesa card grid columns by viewport
- Color constants: `colors.js` with GALIA palette

---

## Responsive Breakpoints

| Breakpoint | Desktop | Tablet | Mobile |
|------------|---------|--------|--------|
| Width | 1440px+ | 768px–1439px | <768px |
| Mesas Grid | 6 cols | 4 cols | 2 cols |
| Panel Width | w-80 | w-72 | hidden (full-screen order) |
| Font Scale | 100% | 90% | 85% |

---

## Success Criteria

1. ✅ POS fullscreen shows mesas in grid + right panel with order details
2. ✅ Colors match GALIA branding (amarillo, marrón, crema)
3. ✅ Camarero has two views: salón (mesas) + orden (items)
4. ✅ Payment flow via bottom sheet, smooth UX
5. ✅ Responsive on 1080p desktop, 768px tablet, mobile <768px
6. ✅ No accessibility regressions (contrast, keyboard nav, semantic HTML)
7. ✅ Animations smooth, no jank
