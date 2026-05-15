# POS Extended Features — Complete Specification

**Goal:** Expand the POS system with separated admin configuration, enhanced sale flow with payments and discounts, printing capabilities, and real-time notifications.

**Architecture:** Three independent modules (Configuration, Sale System, Notifications) that integrate through shared data models and events.

**Tech Stack:** React 18, Flask backend, SQLAlchemy ORM, WebSocket for real-time notifications, thermal printer support (via system print queue).

---

## System Overview

```
┌─ CONFIGURACIÓN (Admin Panel)
│  ├─ CRUD Mesas
│  ├─ CRUD Salones  
│  └─ CRUD Dispositivos de Impresión
│
├─ SISTEMA DE VENTA (Replaces OrderDrawer)
│  ├─ Abrir Venta (personas, comentarios)
│  ├─ Agregar Items + Confirmación (imprime comanda)
│  ├─ Imprimir Control (cambia a "pagando")
│  ├─ Descuentos (% o monto)
│  ├─ Pagos Parciales/Totales
│  └─ Cierre y Registro de Pagos
│
└─ NOTIFICACIONES (Real-time)
   ├─ Evento: Comanda impresa → Cocinero + Impresora
   └─ Evento: Venta cerrada → Caja
```

---

## Module 1: Configuration Panel

**Location:** Sidebar → "Configuración" → "POS" (admin-only)

### 1.1 CRUD Mesas

**Features:**
- List all mesas for selected salon
- Add: number (unique per salon), capacity, salon
- Edit: number, capacity
- Delete: soft-delete (mark as inactive)
- Activate/deactivate inactive mesas
- Table view with edit/delete actions

**Data:**
- Mesa model: `id, salon_id, number, capacity, pos_x, pos_y, width, height, status, is_active, created_at`

**Validation:**
- Mesa number must be unique per salon
- Capacity > 0
- Cannot delete mesa if active sale exists

### 1.2 CRUD Salones

**Features:**
- List all salons
- Add: name, description (optional)
- Edit: name, description
- Delete: soft-delete
- Activate/deactivate
- Show mesa count per salon

**Data:**
- Salon model: `id, name, description, is_active, created_at`

**Validation:**
- Name is required and unique
- Cannot delete salon with mesas

### 1.3 CRUD Dispositivos de Impresión

**Features:**
- List all printer devices
- Add: name, type (comanda/control), connection (IP/port), status
- Edit: name, type, connection
- Delete
- Test connection button (poll device status)
- Show last use timestamp

**Data:**
- PrinterDevice model: `id, name, type (enum: comanda, control), ip_address, port, status (online/offline), last_used, created_at`

**Validation:**
- Name required
- Valid IP format
- Port 1-65535
- Connection string cannot be empty

---

## Module 2: Enhanced Sale System

**Replaces OrderDrawer completely. Integrated into Pos.jsx as a full panel.**

### 2.1 Sale States

```
ABIERTA → PAGANDO → CERRADA
  ↓
  └─ Can transition at any step
```

- **ABIERTA**: Sale created, items being added
- **PAGANDO**: Print control pressed, ready for payment (no more items added)
- **CERRADA**: All payments registered, mesa becomes available

### 2.2 Flow: Abrir Venta (Open Sale)

**Trigger:** Click on mesa in floor plan

**Modal: "Abrir Venta"**
- Fields:
  - Personas (number): positive integer, required
  - Comentarios (optional): free text
- Buttons: "Abrir", "Cancelar"

**Action:**
- Creates new Sale record: `status='abierta', numero_personas=X, comentarios=Y`
- Links to Mesa (mesa_id)
- Opens SalePanel

### 2.3 Flow: Agregar Items (Add Items to Sale)

**Right Panel: Sale Details**
- Header: Mesa #X, Personas: Y, Comentarios: Z
- Two sections:
  - **Left:** Product catalog (categories + products)
  - **Right:** Items added to this sale

**Add Items:**
- Click product → modal "Cantidad y Variante"
- Select quantity and variant
- Confirm → item added to sale
- **Trigger: Comanda Print** (see 2.5)
- Item appears in right section: `Product | Qty | Unit Price | Subtotal`
- Remove button (X) to delete item before confirmation

**Item Confirmation:**
- Button: "Confirmar Items" (confirm the batch)
- Action:
  - Items marked as confirmed
  - **Prints COMANDA with only new items (not previously confirmed)**
  - Triggers notification event
  - Running total updated

**Display:**
- Subtotal (sum of confirmed items)
- Descuento (if added): shows amount
- Total Final

### 2.4 Flow: Imprimir Control (Print Table Check)

**Button: "Imprimir Control de Mesa"**
- Prints document with:
  - Mesa number
  - Number of people
  - All items (name, qty, unit price, subtotal)
  - Descuentos (if any): amount and type (% or fixed)
  - Total final
  - Camarero name (if assigned)
  - Current datetime

**Action:**
- Sends to correct printer device (type: control)
- **Changes sale state to PAGANDO**
- Disables "Agregar Items" button (items locked)

### 2.5 Printing: Comanda (Kitchen Ticket)

**Trigger:** When user clicks "Confirmar Items"

**Document contains:**
- Mesa number
- **ONLY NEW ITEMS from this batch** (not items from previous batches)
  - Item name
  - Quantity
  - Special notes (if any)
- Current timestamp
- "LOTE X" (batch number)

**Action:**
- Sends to printer device (type: comanda)
- Triggers notification event → Cocinero + PrinterDevice

### 2.6 Flow: Agregar Descuento (Add Discount)

**Button: "Agregar Descuento"**

**Modal: "Descuento"**
- Type: Radio buttons
  - Porcentaje (%)
  - Monto Fijo ($)
- Value: number input
- Reason/Notes: optional text
- Confirm button

**Action:**
- Calculates discount:
  - If %: `discount_amount = subtotal * (value / 100)`
  - If fixed: `discount_amount = value`
- Updates total: `total_final = subtotal - discount_amount`
- Stores discount data: `type, value, amount, reason`
- Cannot add multiple discounts (edit existing or clear)
- Show discount breakdown in panel

### 2.7 Flow: Finalizar Venta (Close Sale / Payments)

**Button: "Finalizar Venta"** (visible only when sale is in PAGANDO state)

**Modal: "Pagos"**

**Display:**
- Subtotal
- Descuento (if any)
- **Total a Pagar**

**Payment Flow:**
1. Show payment methods (dropdown or buttons):
   - Efectivo (Cash)
   - Tarjeta (Card)
   - Transferencia (Transfer)
   - Otro (Other)

2. Monto Pago (Amount to pay):
   - Input field
   - Max = remaining balance
   - Validation: must be > 0 and ≤ balance

3. Buttons:
   - "Registrar Pago Parcial" → registers payment, shows remaining balance
   - "Cerrar Venta" → visible only when balance = 0

**Payment Registration:**
- Creates Payment record: `sale_id, amount, method, timestamp, user_id`
- Updates sale: `total_paid += amount`
- If `total_paid >= total_final`: mark as fully paid
- Shows payment history in modal (all registered payments)

**Close Sale:**
- Button "Cerrar Venta" (enabled when fully paid)
- Action:
  - Changes sale state to CERRADA
  - Releases mesa: `mesa.status = libre`
  - Triggers notification event → Caja
  - Closes SalePanel
  - Returns to POS view

---

## Module 3: Notifications (Real-time)

**System:** Event-based notifications that appear in POS interface and can be configured.

### 3.1 Events

**Event 1: Comanda Printed**
- Trigger: User confirms items (batch)
- Destination: Impresora + Cocinero
- Notification text: "Nueva comanda en Mesa 5"
- Action: Print document, show toast in POS

**Event 2: Venta Cerrada**
- Trigger: Sale closed (all payments registered)
- Destination: Caja
- Notification text: "Venta cerrada - Mesa 5 - $XXX"
- Action: Show toast in POS

### 3.2 Notification Display

**Real-time Toast:**
- Bottom-right corner of POS
- Auto-dismiss after 5 seconds
- Type: success (green) or info (blue)
- Icon + message

**Sound (optional):** beep when notification arrives

### 3.3 Configuration Panel

**Location:** Sidebar → Configuración → Notificaciones (admin-only)

**Checkboxes:**
- [ ] Notificar comanda a Cocinero
- [ ] Notificar venta cerrada a Caja

**Save button:** Persists preferences in DB (NotificationPreference model)

### 3.4 Technical Implementation

- **Backend:** Event-based system (emit events on Sale state changes, Payment registration)
- **Frontend:** WebSocket or polling (5s interval) for real-time updates
- **DB:** NotificationPreference model: `user_id, event_type, enabled`

---

## Data Models (New/Modified)

### New Models

```python
class PrinterDevice(db.Model):
    __tablename__ = 'printer_devices'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)  # 'comanda' or 'control'
    ip_address = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    status = Column(String(20), default='offline')  # 'online', 'offline'
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String(50), nullable=False)  # 'efectivo', 'tarjeta', 'transferencia', 'otro'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    comanda_enabled = Column(Boolean, default=True)
    venta_cerrada_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Modified Models

```python
class Sale(db.Model):  # Add fields
    status = Column(String(20), default='abierta')  # 'abierta', 'pagando', 'cerrada'
    numero_personas = Column(Integer, nullable=False)
    comentarios = Column(Text, nullable=True)
    descuento_tipo = Column(String(20), nullable=True)  # 'porcentaje', 'monto_fijo'
    descuento_valor = Column(Numeric(10, 2), nullable=True)
    descuento_monto = Column(Numeric(10, 2), nullable=True)  # calculated
    total_paid = Column(Numeric(10, 2), default=0)
    # Keep existing fields: total, items, etc.

class Mesa(db.Model):  # Already has pos_x, pos_y, width, height
    # No changes needed, structure is correct
```

---

## API Endpoints (New/Modified)

### Configuration

```
POST   /api/v1/mesas                  - Create mesa
GET    /api/v1/salons/:id/mesas       - List mesas for salon
PUT    /api/v1/salons/:id/mesas/:id   - Update mesa
DELETE /api/v1/salons/:id/mesas/:id   - Delete mesa (soft)

POST   /api/v1/salons                 - Create salon
GET    /api/v1/salons                 - List salons
PUT    /api/v1/salons/:id             - Update salon
DELETE /api/v1/salons/:id             - Delete salon (soft)

POST   /api/v1/printer-devices        - Create device
GET    /api/v1/printer-devices        - List devices
PUT    /api/v1/printer-devices/:id    - Update device
DELETE /api/v1/printer-devices/:id    - Delete device
POST   /api/v1/printer-devices/:id/test - Test connection
```

### Sales

```
POST   /api/v1/sales                  - Create sale (open venta)
GET    /api/v1/sales/:id              - Get sale details
PUT    /api/v1/sales/:id              - Update sale (add discount, change status)
POST   /api/v1/sales/:id/print-comanda - Print comanda
POST   /api/v1/sales/:id/print-control - Print control (changes status to pagando)
POST   /api/v1/sales/:id/payments     - Register payment
POST   /api/v1/sales/:id/close        - Close sale (changes status to cerrada)
```

### Notifications

```
GET    /api/v1/notification-preferences - Get user preferences
PUT    /api/v1/notification-preferences - Update preferences
```

---

## Frontend Components (New/Modified)

### New Components
- `POSConfiguration.jsx` - Admin panel wrapper
- `MesasManager.jsx` - CRUD mesas
- `SalonesManager.jsx` - CRUD salones
- `PrinterDevicesManager.jsx` - CRUD devices
- `SalePanel.jsx` - Replaces OrderDrawer (complete sale flow)
- `OpenSaleModal.jsx` - Modal to open venta
- `ProductCatalog.jsx` - Category + product selection
- `AddItemModal.jsx` - Item quantity/variant selection
- `DiscountModal.jsx` - Add discount
- `PaymentModal.jsx` - Payment flow
- `NotificationToast.jsx` - Real-time notifications
- `NotificationPreferences.jsx` - Config panel

### Modified Components
- `Pos.jsx` - Replace OrderDrawer with SalePanel
- `PosHeader.jsx` - Add Configuration link
- `Sidebar.jsx` - Add Configuración section

---

## Responsive Design

- Desktop (1440px+): Full SalePanel (same width as current OrderDrawer)
- Tablet (768px-1439px): SalePanel adjusts to available space
- Mobile: Full-screen SalePanel (no POS floor plan visible)

---

## Success Criteria

1. ✅ Admin can CRUD mesas and salones in separate config panel
2. ✅ Admin can add/test printer devices
3. ✅ User can open venta with people count and comments
4. ✅ User can add items in batches, each batch prints comanda (new items only)
5. ✅ User can print control de mesa (changes status to pagando)
6. ✅ User can add discount (% or fixed amount)
7. ✅ User can register partial and total payments with different methods
8. ✅ Sale closes when fully paid, mesa becomes available
9. ✅ Comanda notification appears in real-time (cocinero)
10. ✅ Venta cerrada notification appears in real-time (caja)
11. ✅ Admin can enable/disable notifications
12. ✅ All payments recorded with timestamps and methods
13. ✅ Printing works with configured devices
14. ✅ UI is responsive across desktop/tablet/mobile
