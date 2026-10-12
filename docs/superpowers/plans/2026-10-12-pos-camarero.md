# Camarero en el celular (sub-proyecto 1c) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vista móvil `/camarero` (PWA) para que los mozos tomen pedidos desde el celular, reutilizando los componentes y hooks del POS de caja (1b).

**Architecture:** Lo propio del 1c vive en `frontend/src/camarero/`: layout, pantalla de mesas (Lista/Plano), pantalla de venta, conectividad, PWA y preferencias por dispositivo. La venta y sus acciones son los componentes del 1b en `frontend/src/pos/`, con cambios chicos y compatibles: `Modal` aprende un modo "hoja inferior" por contexto y `SalePanel` una variante de pantalla completa. En el backend solo se agrega `pending_count` a `GET /floor`.

**Tech Stack:** React 18, React Router 6, TanStack React Query 5, Tailwind 3.4 (paleta Galia), lucide-react, axios, Vitest 1.6, vite-plugin-pwa 0.20 (Workbox 7). Flask, Flask-SQLAlchemy, pytest.

**Spec:** `docs/superpowers/specs/2026-10-10-pos-camarero-design.md`

## Global Constraints

- **Worktree:** `C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base`, rama `feature/pos-camarero` (sale de `main`, que ya incluye el 1a y el 1b). Las rutas del plan son relativas a esa raíz.
- **Python:** `C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe` (en el plan, `PY`). Los tests corren con cwd = `backend/`: `PY -m pytest -q -p no:cacheprovider <archivos>`. Si Bash rechaza el comando, usar PowerShell: `Set-Location C:\Users\onofr\Desktop\galia-app\.claude\worktrees\pos-base\backend; & C:\Users\onofr\Desktop\galia-app\backend\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider <archivos>`.
- **Node:** los comandos de frontend corren con cwd = `frontend/`. La Task 2 corre `npm install`, porque el `node_modules` del worktree es anterior al 1b.
- **Encoding:** los archivos son UTF-8 con acentos. Editar solo con Edit/Write, nunca con PowerShell `Get-Content`/`Set-Content`.
- **Línea base del backend:** `backend/scripts/compare_baseline.py` contra `docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt`. Criterio: `Sin fallas nuevas.`
- **Lint:** `npm run lint` no funciona (no hay configuración de ESLint). La verificación del frontend es `npm test` (Vitest) y `npm run build`.
- **Vitest:** entorno `node` y sin Testing Library. Solo se testea lógica pura (`src/**/*.test.js`). En los tests, importar con rutas relativas, sin `@/`.
- **Montos:** el frontend nunca calcula importes reales; solo los muestra tal como vienen del backend.
- **La caja (1b) no cambia de comportamiento:** todo cambio en `frontend/src/pos/` tiene un valor por defecto que deja la caja igual (modal centrado, `Escape` cierra, panel lateral de 400 px, selector de mozo para `POS`).
- **Textos de la UI:** castellano rioplatense, con los mismos términos del 1b ("Confirmar tanda", "Pedir cuenta", "Cobrar", "Anular", "Mesas").
- **Objetivos táctiles:** al menos 44 px; en las tarjetas de mesa y en los controles propios de `/camarero`, 48 px.
- **Storage:** todo acceso a `localStorage`/`sessionStorage` va dentro de `try/catch`, y la pantalla funciona igual sin él.
- **Verificación en el navegador:** las tareas de UI terminan con una verificación en el preview, cuyo entorno arma la Task 10, Step 1. Si quien ejecuta la tarea no tiene herramientas de navegador, la deja anotada en su reporte y la hace quien coordina.
- **Commits:** terminan con la línea de atribución que pida el harness.

## Review Focus

1. **"Atrás" con hojas apiladas** (Cobrar → anular un pago): cada "atrás" cierra solo la hoja de arriba. Cerrar con ✕ no debe obligar, en producción, a tocar "atrás" de más. Lo cubre la Task 2, Step 6.
2. **Salón guardado que ya no está activo, o `?salon=` de un salón borrado:** la pantalla de mesas cae al primer salón activo y no queda en bucle. Lo cubre `pickSalonId` (Task 5).
3. **Sesión vencida en `/camarero/venta/12`:** después del login se vuelve a esa venta, sin quedar nunca en `/login` ni salir a una URL externa. Lo cubre `postLoginPath` (Task 4).
4. **La caja en escritorio no cambia:** modales centrados, `Escape`, panel de 400 px y selector de mozo. Lo cubren la Task 3, Step 8 y la Task 10, punto 11.
5. **El id del mozo comparado con el usuario actual cuando uno es número y el otro texto:** "Mías" y "Vos" siguen funcionando. Lo cubre el test de `isMine` (Task 5).

## Mapa de archivos

**Backend**
- Modify: `backend/app/routes/pos_floor.py`: `_pending_counts` y `pending_count` en `floor`.
- Create: `backend/tests/test_pos_floor_pending.py`.
- Modify: `backend/scripts/seed_pos_demo.py`: usuario `mozo2@galia.test` (Task 10).

**Frontend: cambios en `src/pos/` (compatibles con la caja)**
- Create: `src/pos/ui/ModalPresentation.js`: contexto `'dialog' | 'sheet'`.
- Create: `src/pos/hooks/useBackToClose.js`.
- Modify:
  - `src/pos/ui/Modal.jsx`: modo hoja.
  - `src/pos/modals/PaymentModal.jsx`: sin teclado en pantalla en modo hoja.
  - `src/pos/modals/AddProductsModal.jsx`: sin autofoco en modo hoja.
  - `src/pos/modals/OpenTableModal.jsx`: `allowWaiterPick`.
  - `src/pos/sale/SalePanel.jsx`: `variant`, `closeLabel`.
  - `src/pos/sale/SaleHeader.jsx`: `closeLabel`.
  - `src/pos/floor/TableTile.jsx`, `src/pos/floor/FloorPlan.jsx`: `dimmed` / `isDimmed`.
  - `src/pos/hooks/usePosQueries.js`: `useFloor(salonId, { enabled })`.
  - `src/pos/hooks/usePosChanges.js`: `onResult`.
  - `src/pos/layout/PosLayout.jsx`: `MobileHint`.
- Create: `src/pos/floor/tableStyles.js` (colores por estado compartidos), `src/pos/layout/MobileHint.jsx`.

**Frontend: `src/camarero/`**
- `CamareroLayout.jsx`, `ConnectivityBanner.jsx`, `UpdateBanner.jsx`.
- `TablesScreen.jsx`, `TablesTopBar.jsx`, `TableList.jsx`, `TableCard.jsx`, `FloorView.jsx`.
- `SaleScreen.jsx`, `MoveSheet.jsx`.
- `hooks/useDevicePrefs.js`, `hooks/useConnectivity.js`, `hooks/useWakeLock.js`, `hooks/usePinchZoom.js`.
- `utils/tableFilters.js`, `utils/salons.js`, `utils/zoom.js`, `utils/connectivity.js`, con sus `*.test.js`.

**Frontend: resto**
- Create: `src/utils/postLogin.js` y `src/utils/postLogin.test.js`.
- Modify:
  - `src/context/AuthContext.jsx`, `src/pages/Login.jsx`, `src/components/ProtectedRoute.jsx`, `src/services/api.js`;
  - `src/App.jsx`, `src/components/layout/Sidebar.jsx`;
  - `vite.config.js`, `package.json`, `public/site.webmanifest`, `index.html`.

---

### Task 1: `pending_count` en el plano (backend)

**Files:**
- Modify: `backend/app/routes/pos_floor.py` (función `floor`, imports)
- Test: `backend/tests/test_pos_floor_pending.py`

**Interfaces:**
- Produces: en `GET /api/v1/pos/floor`, cada elemento de `tables[].sales[]` suma `pending_count: int`, la cantidad de ítems con `status == 'pending'`.

- [ ] **Step 1: Escribir los tests que fallan**: crear `backend/tests/test_pos_floor_pending.py`:

```python
from sqlalchemy import event

from app.extensions import db
from app.services.pos import sale_service
from pos_helpers import auth_headers, make_catalog, make_floor, make_user, pos_app  # noqa: F401


def _floor_sales(client, headers):
    data = client.get('/api/v1/pos/floor', headers=headers).get_json()
    return {sale['id']: sale for table in data['tables'] for sale in table['sales']}


def test_floor_counts_pending_items_per_sale(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS', 'Anular'))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    # Mesa 1: una venta con un ítem confirmado y dos pendientes.
    first = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(boss, first.id, cat.unidad.id)
    sale_service.confirm_batch(boss, first.id)
    sale_service.add_item(boss, first.id, cat.unidad.id)
    sale_service.add_item(boss, first.id, cat.unidad.id)
    # Mesa 2: dos confirmados, uno anulado; ninguno pendiente.
    second = sale_service.open_sale(boss, 'salon', table_id=t2.id, people=1)
    sale_service.add_item(boss, second.id, cat.unidad.id)
    sale_service.add_item(boss, second.id, cat.unidad.id)
    second = sale_service.confirm_batch(boss, second.id)
    sale_service.cancel_item(boss, second.id, second.items[0].id, 'Error de carga')

    sales = _floor_sales(client, auth_headers(client, boss))
    assert sales[first.id]['pending_count'] == 2
    assert sales[second.id]['pending_count'] == 0


def test_floor_counts_each_account_of_a_split_table(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, _t2 = make_floor()
    original = sale_service.open_sale(boss, 'salon', table_id=t1.id, people=2)
    sale_service.add_item(boss, original.id, cat.unidad.id)
    original = sale_service.confirm_batch(boss, original.id)
    confirmed_id = original.items[0].id
    sale_service.add_item(boss, original.id, cat.unidad.id)
    other = sale_service.split_sale(boss, original.id, [{'item_id': confirmed_id, 'quantity': 1}])
    sale_service.reopen(boss, other.id)
    sale_service.add_item(boss, other.id, cat.unidad.id)
    sale_service.add_item(boss, other.id, cat.unidad.id)

    sales = _floor_sales(client, auth_headers(client, boss))
    assert sales[original.id]['pending_count'] == 1
    assert sales[other.id]['pending_count'] == 2


def test_floor_counts_pending_with_a_single_grouped_query(pos_app):
    client = pos_app.test_client()
    boss = make_user('jefe@test.com', modules=('POS',))
    cat = make_catalog()
    _s, t1, t2 = make_floor()
    for table in (t1, t2):
        sale = sale_service.open_sale(boss, 'salon', table_id=table.id, people=1)
        sale_service.add_item(boss, sale.id, cat.unidad.id)
    headers = auth_headers(client, boss)
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, 'before_cursor_execute', capture)
    try:
        client.get('/api/v1/pos/floor', headers=headers)
    finally:
        event.remove(db.engine, 'before_cursor_execute', capture)
    grouped = [s for s in statements if 'pos_sale_items' in s and 'GROUP BY' in s.upper()]
    assert len(grouped) == 1


def test_floor_without_sales_still_works(pos_app):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    make_floor()
    data = client.get('/api/v1/pos/floor', headers=auth_headers(client, waiter)).get_json()
    assert all(table['sales'] == [] for table in data['tables'])
```

- [ ] **Step 2: Correr y ver que fallen**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_floor_pending.py`
Expected: los tres primeros fallan con `KeyError: 'pending_count'` o `assert 0 == 1`; el cuarto pasa.

- [ ] **Step 3: Implementar.** En `backend/app/routes/pos_floor.py`:

Agregar `PosSaleItem` al import de `app.models.pos` (en orden alfabético, después de `PosSaleEvent`):

```python
from app.models.pos import (ACTIVE_SALE_STATUSES, CancelReason, DiscountTemplate, ModifierGroup, PaymentMethod, PosSale, PosSaleEvent, PosSaleItem, PosTable,
                            ProductModifierGroup, Salon)
```

Agregar este helper antes de `floor` (después de la línea `bp = Blueprint(...)`):

```python
def _pending_counts(sale_ids):
    """Ítems sin confirmar por venta, en una sola consulta agrupada."""
    if not sale_ids:
        return {}
    rows = (db.session.query(PosSaleItem.sale_id, func.count(PosSaleItem.id))
            .filter(PosSaleItem.sale_id.in_(sale_ids), PosSaleItem.status == 'pending')
            .group_by(PosSaleItem.sale_id).all())
    return dict(rows)
```

En `floor`, reemplazar:

```python
    by_table = defaultdict(list)
    for sale in active:
        by_table[sale.table_id].append(sale_to_dict(sale, include_items=False))
```

por:

```python
    pending = _pending_counts([sale.id for sale in active])
    by_table = defaultdict(list)
    for sale in active:
        by_table[sale.table_id].append({**sale_to_dict(sale, include_items=False),
                                        'pending_count': pending.get(sale.id, 0)})
```

(`db` y `func` ya están importados en el archivo.)

- [ ] **Step 4: Correr los tests**

Run: `PY -m pytest -q -p no:cacheprovider tests/test_pos_floor_pending.py tests/test_pos_cash_ui_api.py tests/test_pos_sales_api.py`
Expected: todos pasan.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/pos_floor.py backend/tests/test_pos_floor_pending.py
git commit -m "feat(pos): add pending item count to floor sales"
```

---

### Task 2: Modal en modo hoja inferior

**Files:**
- Create: `frontend/src/pos/ui/ModalPresentation.js`
- Create: `frontend/src/pos/hooks/useBackToClose.js`
- Modify: `frontend/src/pos/ui/Modal.jsx`
- Modify: `frontend/src/pos/modals/PaymentModal.jsx`
- Modify: `frontend/src/pos/modals/AddProductsModal.jsx`

**Interfaces:**
- Produces:
  - `ModalPresentationContext` (React context, valor `'dialog' | 'sheet'`, por defecto `'dialog'`);
  - `useModalPresentation(): 'dialog' | 'sheet'`;
  - `useBackToClose(enabled: boolean, onClose: () => void): void`.
  - Todos los modales del 1b se dibujan como hoja inferior cuando un ancestro provee `'sheet'`.

- [ ] **Step 1: Instalar dependencias del worktree**

Run (cwd `frontend/`): `npm install`
Expected: termina sin errores. Después, `npx vitest --version` imprime `1.6.x`.

- [ ] **Step 2: Contexto de presentación**: crear `frontend/src/pos/ui/ModalPresentation.js`:

```js
import { createContext, useContext } from 'react'

// Cómo se dibujan los modales del POS: 'dialog' (caja, centrados) o 'sheet' (celular, hoja inferior).
export const ModalPresentationContext = createContext('dialog')

export const useModalPresentation = () => useContext(ModalPresentationContext)
```

- [ ] **Step 3: "Atrás" cierra la hoja**: crear `frontend/src/pos/hooks/useBackToClose.js`:

```js
import { useEffect, useRef } from 'react'

let counter = 0

// En el celular, el "atrás" del teléfono cierra la hoja abierta en lugar de salir de la pantalla.
// Cada hoja agrega una entrada al historial (conservando idx/key/usr de React Router, así el router no
// ve un cambio de ruta) y la quita al cerrarse con su botón. El retiro se difiere un tick: en desarrollo,
// StrictMode monta dos veces y un history.back() inmediato cerraría la hoja recién montada.
export function useBackToClose(enabled, onClose) {
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!enabled) return undefined
    counter += 1
    const id = `pos-sheet-${counter}`
    window.history.pushState({ ...window.history.state, posSheet: id }, '')
    let closedByBack = false
    const onPop = () => {
      if (window.history.state?.posSheet !== id) {
        closedByBack = true
        onCloseRef.current()
      }
    }
    window.addEventListener('popstate', onPop)
    return () => {
      window.removeEventListener('popstate', onPop)
      if (closedByBack) return
      setTimeout(() => {
        if (window.history.state?.posSheet === id) window.history.back()
      }, 0)
    }
  }, [enabled])
}
```

- [ ] **Step 4: `Modal` con modo hoja**: reemplazar `frontend/src/pos/ui/Modal.jsx` completo por:

```jsx
import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { useBackToClose } from '../hooks/useBackToClose'
import { useModalPresentation } from './ModalPresentation'

// Pila de modales abiertos: Escape cierra solo el de arriba.
const stack = []
const WIDTHS = { sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-3xl' }

const OVERLAY = {
  dialog: 'fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4',
  sheet: 'fixed inset-0 z-40 flex items-end justify-center bg-black/40',
}
const PANEL = {
  dialog: (size) => `flex max-h-[90vh] w-full ${WIDTHS[size]} flex-col rounded-xl bg-white shadow-xl`,
  sheet: () => 'flex max-h-[92vh] w-full flex-col rounded-t-2xl bg-white pb-[env(safe-area-inset-bottom)] shadow-xl',
}

export default function Modal({ title, onClose, children, footer, size = 'md' }) {
  const presentation = useModalPresentation()
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose
  useBackToClose(presentation === 'sheet', onClose)

  useEffect(() => {
    const entry = {}
    stack.push(entry)
    const onKey = (event) => {
      if (event.key === 'Escape' && stack[stack.length - 1] === entry) onCloseRef.current()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      stack.splice(stack.indexOf(entry), 1)
      window.removeEventListener('keydown', onKey)
    }
  }, [])

  return (
    <div
      className={OVERLAY[presentation]}
      onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}
    >
      <div role="dialog" aria-modal="true" aria-label={title} className={PANEL[presentation](size)}>
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h2 className="text-lg font-semibold text-galia-plum">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Cerrar" className="rounded-lg p-2 hover:bg-gray-100">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="border-t px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}
```

- [ ] **Step 5: `PaymentModal` y `AddProductsModal` según el modo**

En `frontend/src/pos/modals/PaymentModal.jsx`, agregar el import (junto a los de `../ui/`):

```js
import { useModalPresentation } from '../ui/ModalPresentation'
```

Dentro del componente, después de `const { run, busy } = useSaleMutation()`:

```js
  // En el celular se usa el teclado del teléfono (los campos tienen inputMode="decimal").
  const showKeypad = useModalPresentation() !== 'sheet'
```

Reemplazar:

```jsx
          <div className="mt-3"><NumericKeypad onKey={onKey} /></div>
```

por:

```jsx
          {showKeypad && <div className="mt-3"><NumericKeypad onKey={onKey} /></div>}
```

En `frontend/src/pos/modals/AddProductsModal.jsx`, agregar el import:

```js
import { useModalPresentation } from '../ui/ModalPresentation'
```

Dentro del componente, después de `const inputRef = useRef(null)`:

```js
  // En el celular no se enfoca el buscador: el teclado taparía la carta.
  const autoFocus = useModalPresentation() !== 'sheet'
```

Reemplazar:

```js
  useEffect(() => {
    if (!detail) inputRef.current?.focus()
  }, [detail])
```

por:

```js
  useEffect(() => {
    if (!detail && autoFocus) inputRef.current?.focus()
  }, [detail, autoFocus])
```

- [ ] **Step 6: Verificar**

Run (cwd `frontend/`): `npm test` y después `npm run build`.
Expected: Vitest pasa (los tests del 1b) y el build termina sin errores.

Verificación en el navegador: se hace en la Task 6, que es la primera que monta modales dentro de `/camarero`. Ahí hay que confirmar:
- **Caja (`/pos`):** "Cobrar" se ve centrado, con teclado en pantalla, y `Escape` cierra.
- **Viewport 375×812 en `/camarero`:**
  - cobrar abre una hoja inferior sin teclado en pantalla;
  - dentro del cobro, anular un pago abre una segunda hoja; "atrás" del navegador cierra solo esa, y otro "atrás" cierra el cobro sin salir de la venta;
  - cerrar con ✕ y después tocar "atrás" vuelve a la pantalla de mesas, sin "atrás" de más.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pos/ui/ModalPresentation.js frontend/src/pos/hooks/useBackToClose.js frontend/src/pos/ui/Modal.jsx frontend/src/pos/modals/PaymentModal.jsx frontend/src/pos/modals/AddProductsModal.jsx
git commit -m "feat(pos): bottom sheet presentation for POS modals"
```

---

### Task 3: Variantes del 1b para el celular

**Files:**
- Modify: `frontend/src/pos/sale/SalePanel.jsx`
- Modify: `frontend/src/pos/sale/SaleHeader.jsx`
- Modify: `frontend/src/pos/modals/OpenTableModal.jsx`
- Create: `frontend/src/pos/floor/tableStyles.js`
- Modify: `frontend/src/pos/floor/TableTile.jsx`
- Modify: `frontend/src/pos/floor/FloorPlan.jsx`
- Modify: `frontend/src/pos/hooks/usePosQueries.js`
- Modify: `frontend/src/pos/hooks/usePosChanges.js`

**Interfaces:**
- Produces:
  - `SalePanel({ saleId, siblings, initialModal, onSelect, onClose, onStartMove, variant = 'panel' | 'screen', closeLabel = null })`;
  - `SaleHeader({ ..., closeLabel = null })`;
  - `OpenTableModal({ table, onClose, onOpened, allowWaiterPick })`, donde `allowWaiterPick` por defecto es `perms.pos`;
  - `TABLE_STATUS_STYLES: { free, open, billing }` (clases de Tailwind) en `pos/floor/tableStyles.js`;
  - `TableTile({ ..., dimmed = false })`;
  - `FloorPlan({ ..., isDimmed = () => false })`;
  - `useFloor(salonId, { enabled = true } = {})`;
  - `usePosChanges({ onResult } = {})`, donde `onResult(ok: boolean, error?: unknown)` se llama después de cada consulta a `/changes`.

- [ ] **Step 1: `SaleHeader` con `closeLabel`**: reemplazar `frontend/src/pos/sale/SaleHeader.jsx` completo por:

```jsx
import { ArrowLeft, X } from 'lucide-react'
import StatusBadge from '../ui/StatusBadge'
import { saleTitle } from '../modals/AddProductsModal'
import { timeLabel } from '../utils/time'

// closeLabel: en el celular, el cierre es un "← Mesas" arriba a la izquierda en lugar de la ✕.
export default function SaleHeader({ sale, onClose, canChangeWaiter, onChangeWaiter, closeLabel = null }) {
  return (
    <div className="border-b px-4 py-3">
      {closeLabel && (
        <button type="button" onClick={onClose}
          className="-ml-1 mb-1 flex min-h-[44px] items-center gap-1 font-medium text-galia-plum">
          <ArrowLeft size={18} /> {closeLabel}
        </button>
      )}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold text-galia-plum">
            {saleTitle(sale)}{sale.customer_name ? ` · ${sale.customer_name}` : ''}
          </h2>
          <p className="text-sm text-gray-600">
            #{sale.number}{sale.people ? ` · ${sale.people} pers.` : ''} · abierta {timeLabel(sale.opened_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={sale.status} />
          {!closeLabel && (
            <button type="button" onClick={onClose} aria-label="Cerrar panel" className="rounded-lg p-2 hover:bg-gray-100">
              <X size={20} />
            </button>
          )}
        </div>
      </div>
      <p className="mt-1 text-sm text-gray-700">
        Mozo: {sale.waiter?.name ?? '—'}
        {canChangeWaiter && (
          <button type="button" className="ml-2 text-galia-plum underline" onClick={onChangeWaiter}>Cambiar</button>
        )}
      </p>
    </div>
  )
}
```

- [ ] **Step 2: `SalePanel` con `variant`**. En `frontend/src/pos/sale/SalePanel.jsx`:

Cambiar el import de lucide a:

```js
import { ArrowLeft, X } from 'lucide-react'
```

Reemplazar `PanelShell` y `PanelMessage` por:

```jsx
const SHELLS = {
  panel: 'flex h-full w-[400px] flex-shrink-0 flex-col border-l border-gray-200 bg-white xl:w-[440px]',
  screen: 'flex h-full w-full flex-col bg-white pt-[env(safe-area-inset-top)]',
}

function PanelShell({ variant, children }) {
  return <aside aria-label="Venta" className={SHELLS[variant]}>{children}</aside>
}

function PanelMessage({ variant, closeLabel, onClose, children }) {
  return (
    <PanelShell variant={variant}>
      <div className={`flex p-2 ${closeLabel ? 'justify-start' : 'justify-end'}`}>
        {closeLabel ? (
          <button type="button" onClick={onClose} className="flex min-h-[44px] items-center gap-1 px-2 font-medium text-galia-plum">
            <ArrowLeft size={18} /> {closeLabel}
          </button>
        ) : (
          <button type="button" onClick={onClose} aria-label="Cerrar panel" className="rounded-lg p-2 hover:bg-gray-100"><X size={20} /></button>
        )}
      </div>
      <p className="p-6 text-center text-gray-500">{children}</p>
    </PanelShell>
  )
}
```

Cambiar la firma y los mensajes de carga:

```jsx
// siblings: ventas activas de la misma mesa (pestañas "Cuenta 1", "Cuenta 2").
// variant: 'panel' (caja, lateral de 400 px) o 'screen' (celular, pantalla completa con "← closeLabel").
export default function SalePanel({ saleId, siblings = [], initialModal = null, onSelect, onClose, onStartMove,
  variant = 'panel', closeLabel = null }) {
```

```jsx
  if (isLoading) return <PanelMessage variant={variant} closeLabel={closeLabel} onClose={onClose}>Cargando venta…</PanelMessage>
  if (isError || !sale) return <PanelMessage variant={variant} closeLabel={closeLabel} onClose={onClose}>No se encontró la venta.</PanelMessage>
```

En el `return` principal:
- cambiar `<PanelShell>` por `<PanelShell variant={variant}>`;
- cambiar `<SaleHeader sale={sale} onClose={onClose} canChangeWaiter={actions.changeWaiter} onChangeWaiter={handlers.changeWaiter} />` por:

```jsx
      <SaleHeader sale={sale} onClose={onClose} closeLabel={closeLabel}
        canChangeWaiter={actions.changeWaiter} onChangeWaiter={handlers.changeWaiter} />
```

- cambiar `<SaleFooter sale={sale} actions={actions} handlers={handlers} busy={busy} />` por:

```jsx
      <div className="bg-gray-50 pb-[env(safe-area-inset-bottom)]">
        <SaleFooter sale={sale} actions={actions} handlers={handlers} busy={busy} />
      </div>
```

- [ ] **Step 3: `OpenTableModal` con `allowWaiterPick`**. En `frontend/src/pos/modals/OpenTableModal.jsx`:

Reemplazar el comentario y la firma por:

```jsx
// onOpened(saleId, isNew): isNew = false cuando la mesa ya tenía una venta (409) y se muestra esa.
// allowWaiterPick: por defecto solo la caja (POS) elige mozo; el celular pasa false (el mozo es quien abre).
export default function OpenTableModal({ table, onClose, onOpened, allowWaiterPick }) {
  const perms = usePosPermissions()
  const pickWaiter = allowWaiterPick ?? perms.pos
```

Reemplazar `const { data: waiters = [] } = useLookup('waiters', perms.pos)` por:

```js
  const { data: waiters = [] } = useLookup('waiters', pickWaiter)
```

Reemplazar `if (perms.pos && waiterId && waiterId !== user?.id) body.waiter_id = waiterId` por:

```js
    if (pickWaiter && waiterId && waiterId !== user?.id) body.waiter_id = waiterId
```

Reemplazar `{perms.pos && (` (el bloque del selector "Mozo") por `{pickWaiter && (`.

- [ ] **Step 4: Colores compartidos y mesa atenuada**: crear `frontend/src/pos/floor/tableStyles.js`:

```js
// Colores de la mesa por estado (tableStatus): los usan el plano de la caja y las tarjetas del celular.
export const TABLE_STATUS_STYLES = {
  free: 'border-gray-300 bg-white text-gray-700',
  open: 'border-amber-400 bg-amber-100 text-amber-900',
  billing: 'border-red-400 bg-red-100 text-red-900',
}
```

En `frontend/src/pos/floor/TableTile.jsx`:
- borrar la constante local `STATUS_STYLES` y agregar `import { TABLE_STATUS_STYLES } from './tableStyles'`;
- cambiar la firma a `export default function TableTile({ table, scale, selected, picking, now, onClick, dimmed = false })`;
- en el `className` del botón, reemplazar `${STATUS_STYLES[status]}` por `${TABLE_STATUS_STYLES[status]}` y `${disabled ? 'opacity-40' : ''}` por `${disabled || dimmed ? 'opacity-40' : ''}`.

En `frontend/src/pos/floor/FloorPlan.jsx`:
- cambiar la firma a `export default function FloorPlan({ tables, selectedTableId, picking = false, onTableClick, isDimmed = () => false })`;
- en el `<TableTile ...>`, agregar la prop `dimmed={isDimmed(table)}`.

- [ ] **Step 5: `useFloor` con `enabled`**: en `frontend/src/pos/hooks/usePosQueries.js`, reemplazar `useFloor` por:

```js
// Los intervalos son de respaldo: el refresco normal lo dispara usePosChanges.
export const useFloor = (salonId, { enabled = true } = {}) => useQuery({
  queryKey: posKeys.floor(salonId),
  queryFn: () => posApi.getFloor(salonId),
  enabled,
  refetchInterval: 60_000,
  staleTime: 10_000,
})
```

(El comentario ya está arriba de `useFloor`; no duplicarlo.)

- [ ] **Step 6: `usePosChanges` con `onResult`**: en `frontend/src/pos/hooks/usePosChanges.js`:

Cambiar el comentario y la firma:

```js
// Consulta /pos/changes cada 3 s con la pestaña visible e invalida solo lo que cambió.
// El backend repite una ventana de eventos ya informados: se recuerdan los ids vistos y solo se
// invalidan las ventas con eventos nuevos. Si falla la red, al reconectar refresca todo el POS.
// onResult(ok, error): informa cada consulta (el celular lo usa para detectar la falta de conexión).
export function usePosChanges({ onResult } = {}) {
```

Después de `const seen = useRef(new Set())`:

```js
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult
```

Dentro del `try`, justo antes de `return response.last_event_id`:

```js
        onResultRef.current?.(true)
```

Dentro del `catch`, antes de `throw error`:

```js
        onResultRef.current?.(false, error)
```

- [ ] **Step 7: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 8: Verificación en el navegador (caja)**: en `/pos` (escritorio, 1280 px de ancho), comprobar que:
  - el panel lateral sigue de 400 px con la ✕;
  - "Abrir mesa" con un usuario `POS` sigue mostrando el selector de mozo;
  - los colores del plano no cambian.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pos
git commit -m "feat(pos): screen variant and hooks options for the waiter view"
```

---

### Task 4: Destino después del login

**Files:**
- Create: `frontend/src/utils/postLogin.js`
- Test: `frontend/src/utils/postLogin.test.js`
- Modify: `frontend/src/context/AuthContext.jsx` (función `login`)
- Modify: `frontend/src/pages/Login.jsx`
- Modify: `frontend/src/components/ProtectedRoute.jsx`
- Modify: `frontend/src/services/api.js`

**Interfaces:**
- Produces:
  - `postLoginPath({ from?: string|null, stored?: string|null, isAdmin?: boolean, modules?: Array<string|{name}> }): string`;
  - `storeRedirect(path: string): void`;
  - `takeStoredRedirect(): string|null`.
  - `AuthContext.login(email, password)` ahora devuelve `{ user, modules }`.

- [ ] **Step 1: Tests que fallan**: crear `frontend/src/utils/postLogin.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { postLoginPath } from './postLogin'

describe('postLoginPath', () => {
  it('manda al Camarero a quien tiene Camarero sin POS', () => {
    expect(postLoginPath({ modules: [{ name: 'Camarero' }] })).toBe('/camarero')
    expect(postLoginPath({ modules: ['Camarero', 'Cobrar'] })).toBe('/camarero')
  })

  it('deja en el dashboard a admin, caja y al resto', () => {
    expect(postLoginPath({ isAdmin: true, modules: [] })).toBe('/dashboard')
    expect(postLoginPath({ modules: [{ name: 'Camarero' }, { name: 'POS' }] })).toBe('/dashboard')
    expect(postLoginPath({ modules: [{ name: 'MySchedule' }] })).toBe('/dashboard')
    expect(postLoginPath()).toBe('/dashboard')
  })

  it('vuelve a la ruta de origen: primero la del router, después la guardada', () => {
    const waiter = { modules: [{ name: 'Camarero' }] }
    expect(postLoginPath({ ...waiter, from: '/camarero/venta/12', stored: '/camarero' })).toBe('/camarero/venta/12')
    expect(postLoginPath({ ...waiter, stored: '/camarero/venta/7?add=1' })).toBe('/camarero/venta/7?add=1')
  })

  it('ignora rutas de origen inválidas', () => {
    const waiter = { modules: [{ name: 'Camarero' }] }
    expect(postLoginPath({ ...waiter, from: '/login' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, stored: '/login?x=1' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, from: '//evil.example' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, from: 'https://evil.example' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, from: 42 })).toBe('/camarero')
  })
})
```

- [ ] **Step 2: Correr y ver que falle**

Run (cwd `frontend/`): `npx vitest run src/utils/postLogin.test.js`
Expected: FAIL (no se puede resolver `./postLogin`).

- [ ] **Step 3: Implementar**: crear `frontend/src/utils/postLogin.js`:

```js
const STORAGE_KEY = 'postLoginRedirect'

const isInternalPath = (path) =>
  typeof path === 'string' && path.startsWith('/') && !path.startsWith('//') && !path.startsWith('/login')

// Adónde va el usuario al iniciar sesión: la ruta de la que venía (si es válida) o, si no, según sus permisos.
// Un mozo (Camarero sin POS ni admin) va directo a la vista del celular.
export function postLoginPath({ from = null, stored = null, isAdmin = false, modules = [] } = {}) {
  if (isInternalPath(from)) return from
  if (isInternalPath(stored)) return stored
  const names = modules.map((m) => (typeof m === 'string' ? m : m?.name))
  if (!isAdmin && names.includes('Camarero') && !names.includes('POS')) return '/camarero'
  return '/dashboard'
}

// Ruta de origen cuando un 401 manda al login con window.location (se pierde el estado del router).
export function storeRedirect(path) {
  try {
    sessionStorage.setItem(STORAGE_KEY, path)
  } catch {
    // Sin storage: el login usa el destino según permisos.
  }
}

export function takeStoredRedirect() {
  try {
    const path = sessionStorage.getItem(STORAGE_KEY)
    sessionStorage.removeItem(STORAGE_KEY)
    return path
  } catch {
    return null
  }
}
```

- [ ] **Step 4: Correr el test**

Run: `npx vitest run src/utils/postLogin.test.js`
Expected: PASS.

- [ ] **Step 5: `login` devuelve los módulos**: en `frontend/src/context/AuthContext.jsx`, reemplazar la función `login` por:

```js
  // Devuelve también los módulos: el login decide adónde ir sin esperar a que se actualice el estado.
  const login = async (email, password) => {
    const userData = await authService.login(email, password)
    const modules = await loadModules(userData)
    setUser(userData)
    setUserModules(modules)
    return { user: userData, modules }
  }
```

- [ ] **Step 6: `Login` usa `postLoginPath`**: en `frontend/src/pages/Login.jsx`:

Cambiar el import del router a `import { useLocation, useNavigate } from 'react-router-dom'`. Agregar:

```js
import { postLoginPath, takeStoredRedirect } from '@/utils/postLogin'
```

Después de `const navigate = useNavigate()`:

```js
  const location = useLocation()
```

Reemplazar:

```js
      await login(email, password)
      navigate('/dashboard')
```

por:

```js
      const { user, modules } = await login(email, password)
      navigate(postLoginPath({
        from: location.state?.from,
        stored: takeStoredRedirect(),
        isAdmin: user?.role === 'admin',
        modules,
      }), { replace: true })
```

- [ ] **Step 7: `ProtectedRoute` guarda el origen**: reemplazar `frontend/src/components/ProtectedRoute.jsx` completo por:

```jsx
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Cargando...</div>
      </div>
    )
  }

  if (!user) {
    // Después del login se vuelve a esta ruta (p. ej. una venta abierta en el celular).
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />
  }

  return children
}

export default ProtectedRoute
```

- [ ] **Step 8: Interceptores**: en `frontend/src/services/api.js`:

Agregar arriba, después de `import axios from 'axios'`:

```js
import { storeRedirect } from '@/utils/postLogin'
```

En el manejo del 401, antes de `window.location.href = '/login'`:

```js
      storeRedirect(`${window.location.pathname}${window.location.search}`)
```

En el manejo del 403, reemplazar el comentario y la condición:

```js
      // Si no estamos en la página de inicio, redirigir después de 2 segundos.
      // En el POS y en el Camarero no: una acción sin permiso no debe sacar a nadie de la pantalla.
      if (!window.location.pathname.includes('/dashboard') &&
          !window.location.pathname.includes('/home') &&
          !window.location.pathname.startsWith('/pos') &&
          !window.location.pathname.startsWith('/camarero')) {
```

- [ ] **Step 9: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (con el preview de la Task 10, Step 1): `mozo@galia.test` va a `/camarero`; esa ruta recién existe desde la Task 5, así que esta verificación se completa ahí. Hoy se puede comprobar que `admin@galia.test` sigue entrando a `/dashboard`.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/utils/postLogin.js frontend/src/utils/postLogin.test.js frontend/src/context/AuthContext.jsx frontend/src/pages/Login.jsx frontend/src/components/ProtectedRoute.jsx frontend/src/services/api.js
git commit -m "feat(auth): return to the origin route after login and send waiters to /camarero"
```

---

### Task 5: Pantalla de mesas del Camarero

**Files:**
- Create: `frontend/src/camarero/utils/tableFilters.js` y `tableFilters.test.js`
- Create: `frontend/src/camarero/utils/salons.js` y `salons.test.js`
- Create: `frontend/src/camarero/hooks/useDevicePrefs.js`
- Create: `frontend/src/camarero/CamareroLayout.jsx`
- Create: `frontend/src/camarero/TablesTopBar.jsx`
- Create: `frontend/src/camarero/TableCard.jsx`
- Create: `frontend/src/camarero/TableList.jsx`
- Create: `frontend/src/camarero/TablesScreen.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`

**Interfaces:**
- Consumes:
  - `useFloor`, `FloorPlan` (`isDimmed`), `OpenTableModal` (`allowWaiterPick`), `TABLE_STATUS_STYLES` (Task 3);
  - `ModalPresentationContext` (Task 2);
  - `tableStatus`, `tableSummary` (`pos/utils/floor`), `elapsedLabel` (`pos/utils/time`), `formatMoney` (`pos/utils/money`), `useNow` (`pos/hooks/useNow`);
  - `PosRoute`, `ToastProvider`, `usePosChanges`, `CenteredMessage` (1b).
- Produces:
  - `isMine(table, userId): boolean`, `hasPending(table): boolean`, `filterTables(tables, filter: 'all'|'mine', userId)`, `isDimmed(table, filter, userId)`, `waiterLabel(table, userId): string|null`;
  - `pickSalonId({ fromUrl, saved, salons }): number|null`;
  - `useDevicePrefs(): [prefs: { salonId: number|null, view: 'list'|'floor', filter: 'all'|'mine' }, update(patch)]`;
  - `CamareroLayout`, que la Task 8 amplía;
  - las rutas `/camarero` (index `TablesScreen`) en `App.jsx`, a las que la Task 6 agrega `venta/:saleId`.

- [ ] **Step 1: Tests de las utilidades**: crear `frontend/src/camarero/utils/tableFilters.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { filterTables, hasPending, isDimmed, isMine, waiterLabel } from './tableFilters'

const sale = (id, waiterId, pending = 0, status = 'open') => ({
  id, status, waiter: waiterId ? { id: waiterId, name: `Mozo ${waiterId}` } : null, pending_count: pending,
})
const free = { id: 1, label: 'Mesa 1', sales: [] }
const mine = { id: 2, label: 'Mesa 2', sales: [sale(10, 7, 1)] }
const other = { id: 3, label: 'Mesa 3', sales: [sale(11, 8)] }
const shared = { id: 4, label: 'Mesa 4', sales: [sale(12, 8), sale(13, 7, 0, 'billing')] }
const tables = [free, mine, other, shared]

describe('tableFilters', () => {
  it('isMine compara el mozo de cualquier cuenta, aunque el id venga como texto', () => {
    expect(isMine(mine, 7)).toBe(true)
    expect(isMine(mine, '7')).toBe(true)
    expect(isMine(shared, 7)).toBe(true)
    expect(isMine(other, 7)).toBe(false)
    expect(isMine(free, 7)).toBe(false)
    expect(isMine(other, undefined)).toBe(false)
  })

  it('filterTables: "Todas" muestra todo; "Mías" las propias más las libres', () => {
    expect(filterTables(tables, 'all', 7)).toEqual(tables)
    expect(filterTables(tables, 'mine', 7).map((t) => t.id)).toEqual([1, 2, 4])
  })

  it('isDimmed atenúa en el plano solo las ocupadas ajenas con el filtro "Mías"', () => {
    expect(isDimmed(other, 'mine', 7)).toBe(true)
    expect(isDimmed(free, 'mine', 7)).toBe(false)
    expect(isDimmed(mine, 'mine', 7)).toBe(false)
    expect(isDimmed(other, 'all', 7)).toBe(false)
  })

  it('hasPending detecta ítems sin confirmar en cualquier cuenta', () => {
    expect(hasPending(mine)).toBe(true)
    expect(hasPending(shared)).toBe(false)
    expect(hasPending(free)).toBe(false)
    expect(hasPending({ sales: [{ id: 1 }] })).toBe(false)
  })

  it('waiterLabel muestra "Vos" para el usuario actual', () => {
    expect(waiterLabel(mine, 7)).toBe('Vos')
    expect(waiterLabel(other, 7)).toBe('Mozo 8')
    expect(waiterLabel(free, 7)).toBe(null)
  })
})
```

Crear `frontend/src/camarero/utils/salons.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { pickSalonId } from './salons'

const salons = [{ id: 3, name: 'Salón' }, { id: 5, name: 'Patio' }]

describe('pickSalonId', () => {
  it('prefiere el salón de la URL si está activo', () => {
    expect(pickSalonId({ fromUrl: 5, saved: 3, salons })).toBe(5)
  })

  it('si no, el guardado en el dispositivo', () => {
    expect(pickSalonId({ fromUrl: null, saved: 5, salons })).toBe(5)
  })

  it('cae al primer salón activo si el pedido ya no existe', () => {
    expect(pickSalonId({ fromUrl: 99, saved: 98, salons })).toBe(3)
    expect(pickSalonId({ fromUrl: null, saved: null, salons })).toBe(3)
  })

  it('sin salones activos devuelve null', () => {
    expect(pickSalonId({ fromUrl: 5, saved: 3, salons: [] })).toBe(null)
  })
})
```

- [ ] **Step 2: Correr y ver que fallen**

Run (cwd `frontend/`): `npx vitest run src/camarero`
Expected: FAIL (no existen los módulos).

- [ ] **Step 3: Implementar las utilidades**: crear `frontend/src/camarero/utils/tableFilters.js`:

```js
import { tableStatus } from '../../pos/utils/floor'

const sameId = (a, b) => a != null && b != null && Number(a) === Number(b)

// La mesa es "mía" si alguna de sus cuentas tiene como mozo al usuario actual.
export const isMine = (table, userId) => (table.sales ?? []).some((s) => sameId(s.waiter?.id, userId))

export const hasPending = (table) => (table.sales ?? []).some((s) => (s.pending_count ?? 0) > 0)

// "Mías": las propias más las libres (para poder abrir una mesa nueva).
export function filterTables(tables, filter, userId) {
  if (filter !== 'mine') return tables
  return tables.filter((t) => tableStatus(t) === 'free' || isMine(t, userId))
}

// En el plano no se ocultan mesas: con "Mías" se atenúan las ocupadas ajenas.
export const isDimmed = (table, filter, userId) =>
  filter === 'mine' && tableStatus(table) !== 'free' && !isMine(table, userId)

export function waiterLabel(table, userId) {
  const waiter = table.sales?.[0]?.waiter
  if (!waiter) return null
  return sameId(waiter.id, userId) ? 'Vos' : waiter.name
}
```

Crear `frontend/src/camarero/utils/salons.js`:

```js
// Salón a mostrar: el de la URL, si no el guardado en el dispositivo, si no el primero activo.
export function pickSalonId({ fromUrl = null, saved = null, salons = [] }) {
  const ids = salons.map((s) => s.id)
  if (fromUrl != null && ids.includes(fromUrl)) return fromUrl
  if (saved != null && ids.includes(saved)) return saved
  return ids[0] ?? null
}
```

- [ ] **Step 4: Correr los tests**

Run: `npx vitest run src/camarero`
Expected: PASS.

- [ ] **Step 5: Preferencias por dispositivo**: crear `frontend/src/camarero/hooks/useDevicePrefs.js`:

```js
import { useCallback, useState } from 'react'

const KEY = 'camarero.prefs'
const DEFAULTS = { salonId: null, view: 'list', filter: 'all' }

function read() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) ?? '{}') }
  } catch {
    return DEFAULTS
  }
}

// Salón, vista (Lista/Plano) y filtro (Todas/Mías) de este celular.
export function useDevicePrefs() {
  const [prefs, setPrefs] = useState(read)
  const update = useCallback((patch) => {
    setPrefs((current) => {
      const next = { ...current, ...patch }
      try {
        localStorage.setItem(KEY, JSON.stringify(next))
      } catch {
        // Sin storage: las preferencias duran mientras la app está abierta.
      }
      return next
    })
  }, [])
  return [prefs, update]
}
```

- [ ] **Step 6: Layout**: crear `frontend/src/camarero/CamareroLayout.jsx`:

```jsx
import { Outlet } from 'react-router-dom'
import { usePosChanges } from '@/pos/hooks/usePosChanges'
import { ModalPresentationContext } from '@/pos/ui/ModalPresentation'
import { ToastProvider } from '@/pos/ui/Toasts'

function CamareroShell() {
  usePosChanges()
  return (
    <div className="flex h-dvh flex-col bg-galia-cream">
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  )
}

// Vista del celular: los modales del POS se dibujan como hojas inferiores.
export default function CamareroLayout() {
  return (
    <ToastProvider>
      <ModalPresentationContext.Provider value="sheet">
        <CamareroShell />
      </ModalPresentationContext.Provider>
    </ToastProvider>
  )
}
```

- [ ] **Step 7: Barra superior**: crear `frontend/src/camarero/TablesTopBar.jsx`:

```jsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LayoutGrid, Map as MapIcon, Menu } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

const pill = (active) =>
  `min-h-[44px] whitespace-nowrap rounded-full px-4 text-sm font-medium ${
    active ? 'bg-galia-cream text-galia-plum' : 'bg-white/10 text-galia-cream'
  }`

const VIEWS = [['list', 'Lista', LayoutGrid], ['floor', 'Plano', MapIcon]]
const FILTERS = [['all', 'Todas'], ['mine', 'Mías']]

export default function TablesTopBar({ salons, salonId, onSalon, view, onView, filter, onFilter }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const signOut = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="bg-galia-plum pt-[env(safe-area-inset-top)] text-galia-cream">
      <div className="flex items-center gap-2 px-3 py-2">
        <span className="font-display text-lg tracking-wide">CAMARERO</span>
        <div className="ml-auto flex gap-1" role="group" aria-label="Vista">
          {VIEWS.map(([value, label, Icon]) => (
            <button key={value} type="button" aria-pressed={view === value} onClick={() => onView(value)}
              className={`${pill(view === value)} flex items-center gap-1`}>
              <Icon size={16} /> {label}
            </button>
          ))}
        </div>
        <button type="button" aria-label="Menú" aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}
          className="flex min-h-[48px] min-w-[48px] items-center justify-center rounded-lg hover:bg-white/10">
          <Menu size={22} />
        </button>
      </div>
      {menuOpen && (
        <div className="border-t border-white/10 px-3 py-2 text-sm">
          <p className="py-2 text-galia-cream/80">{user?.email}</p>
          <Link to="/dashboard" className="flex min-h-[48px] items-center">Salir a Galia</Link>
          <button type="button" onClick={signOut} className="flex min-h-[48px] w-full items-center text-left">Cerrar sesión</button>
        </div>
      )}
      <nav className="flex gap-2 overflow-x-auto px-3 pb-2" aria-label="Salones">
        {salons.map((salon) => (
          <button key={salon.id} type="button" aria-pressed={salon.id === salonId} onClick={() => onSalon(salon.id)}
            className={pill(salon.id === salonId)}>
            {salon.name}
          </button>
        ))}
      </nav>
      <div className="flex gap-2 px-3 pb-3" role="group" aria-label="Filtro de mesas">
        {FILTERS.map(([value, label]) => (
          <button key={value} type="button" aria-pressed={filter === value} onClick={() => onFilter(value)}
            className={pill(filter === value)}>
            {label}
          </button>
        ))}
      </div>
    </header>
  )
}
```

- [ ] **Step 8: Tarjetas y lista**: crear `frontend/src/camarero/TableCard.jsx`:

```jsx
import { TABLE_STATUS_STYLES } from '@/pos/floor/tableStyles'
import { tableStatus, tableSummary } from '@/pos/utils/floor'
import { formatMoney } from '@/pos/utils/money'
import { elapsedLabel } from '@/pos/utils/time'
import { hasPending, waiterLabel } from './utils/tableFilters'

export default function TableCard({ table, userId, now, onClick }) {
  const status = tableStatus(table)
  const summary = tableSummary(table)
  const pending = hasPending(table)

  return (
    <button type="button" onClick={onClick}
      aria-label={`${table.label}${status === 'free' ? ', libre' : `, ${formatMoney(summary.total)}`}${pending ? ', con ítems sin confirmar' : ''}`}
      className={`relative flex min-h-[104px] flex-col justify-between rounded-xl border-2 p-3 text-left ${TABLE_STATUS_STYLES[status]}`}>
      <span className="flex w-full items-start justify-between gap-2">
        <span className="text-lg font-semibold leading-tight">{table.label}</span>
        {summary.count > 1 && (
          <span className="whitespace-nowrap rounded-full bg-galia-plum px-2 py-0.5 text-xs text-galia-cream">{summary.count} cuentas</span>
        )}
      </span>
      {status === 'free' ? (
        <span className="text-sm">Libre</span>
      ) : (
        <span className="text-sm leading-tight">
          <span className="block text-base font-semibold">{formatMoney(summary.total)}</span>
          <span className="block truncate">{waiterLabel(table, userId)}</span>
          <span className="block">{elapsedLabel(summary.openedAt, now)}</span>
        </span>
      )}
      {pending && <span className="absolute bottom-3 right-3 h-3 w-3 rounded-full bg-galia-plum" aria-hidden="true" />}
    </button>
  )
}
```

Crear `frontend/src/camarero/TableList.jsx`:

```jsx
import { useNow } from '@/pos/hooks/useNow'
import CenteredMessage from '@/pos/ui/CenteredMessage'
import TableCard from './TableCard'

export default function TableList({ tables, userId, onTableClick }) {
  const now = useNow()
  if (tables.length === 0) return <CenteredMessage>No hay mesas para mostrar.</CenteredMessage>
  return (
    <div className="grid grid-cols-2 gap-3 p-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] min-[600px]:grid-cols-3">
      {tables.map((table) => (
        <TableCard key={table.id} table={table} userId={userId} now={now} onClick={() => onTableClick(table)} />
      ))}
    </div>
  )
}
```

- [ ] **Step 9: Pantalla de mesas**: crear `frontend/src/camarero/TablesScreen.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import FloorPlan from '@/pos/floor/FloorPlan'
import { useFloor } from '@/pos/hooks/usePosQueries'
import OpenTableModal from '@/pos/modals/OpenTableModal'
import CenteredMessage from '@/pos/ui/CenteredMessage'
import { useDevicePrefs } from './hooks/useDevicePrefs'
import { pickSalonId } from './utils/salons'
import { filterTables, isDimmed } from './utils/tableFilters'
import TableList from './TableList'
import TablesTopBar from './TablesTopBar'

export default function TablesScreen() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const [prefs, setPrefs] = useDevicePrefs()
  const [openTable, setOpenTable] = useState(null)
  const fromUrl = Number(params.get('salon')) || null
  const requested = fromUrl ?? prefs.salonId ?? undefined
  const { data, isLoading, isError } = useFloor(requested)
  const chosen = data ? pickSalonId({ fromUrl, saved: prefs.salonId, salons: data.salons }) : null

  const selectSalon = (id) => {
    setPrefs({ salonId: id })
    setParams(id ? { salon: String(id) } : {}, { replace: true })
  }

  // Si el salón pedido ya no está activo (o no había ninguno), se pasa al elegido; el de la URL queda guardado.
  useEffect(() => {
    if (!data || chosen === null) return
    if (chosen !== requested) selectSalon(chosen)
    else if (prefs.salonId !== chosen) setPrefs({ salonId: chosen })
  }, [data, chosen, requested]) // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) return <CenteredMessage>Cargando mesas…</CenteredMessage>
  if (isError || !data) return <CenteredMessage>No se pudieron cargar las mesas.</CenteredMessage>
  if (data.salons.length === 0) {
    return <CenteredMessage>No hay salones configurados. Pedile a la caja que los cree.</CenteredMessage>
  }

  const userId = user?.id
  const ready = chosen === data.salon_id

  const onTableClick = (table) => {
    if (table.sales.length > 0) navigate(`/camarero/venta/${table.sales[0].id}`)
    else setOpenTable(table)
  }

  return (
    <div className="flex h-full flex-col">
      <TablesTopBar salons={data.salons} salonId={chosen} onSalon={selectSalon}
        view={prefs.view} onView={(view) => setPrefs({ view })}
        filter={prefs.filter} onFilter={(filter) => setPrefs({ filter })} />
      <div className="min-h-0 flex-1 overflow-auto">
        {!ready && <CenteredMessage>Cargando mesas…</CenteredMessage>}
        {ready && prefs.view === 'floor' && (
          <div className="p-3">
            <FloorPlan tables={data.tables} isDimmed={(table) => isDimmed(table, prefs.filter, userId)}
              onTableClick={onTableClick} />
          </div>
        )}
        {ready && prefs.view !== 'floor' && (
          <TableList tables={filterTables(data.tables, prefs.filter, userId)} userId={userId} onTableClick={onTableClick} />
        )}
      </div>
      {openTable && (
        <OpenTableModal table={openTable} allowWaiterPick={false} onClose={() => setOpenTable(null)}
          onOpened={(id, isNew) => {
            setOpenTable(null)
            navigate(`/camarero/venta/${id}${isNew ? '?add=1' : ''}`)
          }} />
      )}
    </div>
  )
}
```

- [ ] **Step 10: Rutas y Sidebar**

En `frontend/src/App.jsx`, agregar los imports después de `import PosConfigPage from './pos/config/PosConfigPage'`:

```js
import CamareroLayout from './camarero/CamareroLayout'
import TablesScreen from './camarero/TablesScreen'
```

Después del bloque `<Route path="/pos" ...>…</Route>`, agregar:

```jsx
          <Route path="/camarero" element={<ProtectedRoute><PosRoute><CamareroLayout /></PosRoute></ProtectedRoute>}>
            <Route index element={<TablesScreen />} />
          </Route>
```

En `frontend/src/components/layout/Sidebar.jsx`:
- agregar `Smartphone,` a la lista del import multilínea de `lucide-react` (el que incluye `Store,`);
- después de la línea `{ to: '/pos', icon: Store, label: 'Abrir POS', anyModule: ['POS', 'Camarero'] },`, agregar:

```js
      { to: '/camarero', icon: Smartphone, label: 'Camarero', anyModule: ['POS', 'Camarero'] },
```

- [ ] **Step 11: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (preview de la Task 10, Step 1; viewport 375×812):
1. Login con `mozo@galia.test`: va a `/camarero` (cierra la verificación de la Task 4).
2. Las tarjetas se ven en 2 columnas con colores por estado.
3. Cambiar de salón actualiza la URL; recargar mantiene el salón, la vista y el filtro.
4. "Mías" deja las propias y las libres; en "Plano", las ajenas aparecen atenuadas.
5. Tocar una mesa libre abre la hoja "Abrir Mesa n" sin selector de mozo. Al abrir navega a `/camarero/venta/<id>?add=1`; esa ruta llega en la Task 6, así que por ahora la pantalla queda vacía.
6. En el Sidebar de Galia (escritorio, como admin) aparece "Camarero".

- [ ] **Step 12: Commit**

```bash
git add frontend/src/camarero frontend/src/App.jsx frontend/src/components/layout/Sidebar.jsx
git commit -m "feat(camarero): tables screen with list, floor and mine filter"
```

---

### Task 6: Pantalla de venta y mover de mesa

**Files:**
- Create: `frontend/src/camarero/SaleScreen.jsx`
- Create: `frontend/src/camarero/MoveSheet.jsx`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Consumes:
  - `SalePanel` (`variant`, `closeLabel`) y `useFloor(salonId, { enabled })` (Task 3);
  - `useSale`, `useSaleMutation`, `posApi.move(id, tableId)`, `Modal`, `Chip`, `btn`, `useToast`, `tableStatus`, `saleTitle` (1b).
- Produces: la ruta `/camarero/venta/:saleId` (`?add=1` abre "Agregar productos").

- [ ] **Step 1: Hoja para mover**: crear `frontend/src/camarero/MoveSheet.jsx`:

```jsx
import { useState } from 'react'
import { posApi } from '@/pos/api/posApi'
import { useFloor } from '@/pos/hooks/usePosQueries'
import { useSaleMutation } from '@/pos/hooks/useSaleMutation'
import { saleTitle } from '@/pos/modals/AddProductsModal'
import Chip from '@/pos/ui/Chip'
import Modal from '@/pos/ui/Modal'
import { useToast } from '@/pos/ui/Toasts'
import { btn } from '@/pos/ui/buttons'
import { tableStatus } from '@/pos/utils/floor'

// En el celular, mover es elegir una mesa libre de una lista (en la caja se toca en el plano).
export default function MoveSheet({ sale, onClose }) {
  const [salonId, setSalonId] = useState(sale.table?.salon_id)
  const { data, isLoading } = useFloor(salonId)
  const { run, busy } = useSaleMutation()
  const toast = useToast()
  const freeTables = (data?.tables ?? []).filter((table) => tableStatus(table) === 'free')

  const move = async (table) => {
    const moved = await run(sale.id, () => posApi.move(sale.id, table.id))
    if (moved) {
      toast.success(`Venta movida a ${table.label}`)
      onClose()
    }
  }

  return (
    <Modal title={`Mover ${saleTitle(sale)}`} onClose={onClose}>
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(data?.salons ?? []).map((salon) => (
          <Chip key={salon.id} active={salon.id === data?.salon_id} onClick={() => setSalonId(salon.id)}>
            {salon.name}
          </Chip>
        ))}
      </div>
      {isLoading && <p className="py-6 text-center text-gray-500">Cargando mesas…</p>}
      {!isLoading && freeTables.length === 0 && (
        <p className="py-6 text-center text-gray-500">No hay mesas libres en este salón.</p>
      )}
      <div className="mt-2 grid grid-cols-3 gap-2">
        {freeTables.map((table) => (
          <button key={table.id} type="button" disabled={busy} onClick={() => move(table)}
            className={btn('secondary', 'min-h-[56px] text-lg')}>
            {table.label}
          </button>
        ))}
      </div>
    </Modal>
  )
}
```

- [ ] **Step 2: Pantalla de venta**: crear `frontend/src/camarero/SaleScreen.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useFloor, useSale } from '@/pos/hooks/usePosQueries'
import SalePanel from '@/pos/sale/SalePanel'
import MoveSheet from './MoveSheet'

// La venta a pantalla completa: el panel de la caja en su variante 'screen'.
export default function SaleScreen() {
  const saleId = Number(useParams().saleId)
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  // "Agregar productos" se abre solo al llegar con ?add=1 (recién abierta la mesa), una vez.
  const [initial] = useState(() => ({ saleId, modal: params.get('add') === '1' ? 'add' : null }))
  const [moving, setMoving] = useState(false)
  const { data: sale } = useSale(saleId)
  const salonId = sale?.table?.salon_id
  const { data: floor } = useFloor(salonId, { enabled: Boolean(salonId) })
  const siblings = floor?.tables.find((table) => table.id === sale?.table?.id)?.sales ?? []

  useEffect(() => {
    if (params.has('add')) setParams({}, { replace: true })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const backToTables = () => navigate(salonId ? `/camarero?salon=${salonId}` : '/camarero')

  return (
    <div className="h-full">
      <SalePanel key={saleId} saleId={saleId} variant="screen" closeLabel="Mesas" siblings={siblings}
        initialModal={initial.saleId === saleId ? initial.modal : null}
        onSelect={(id) => navigate(`/camarero/venta/${id}`, { replace: true })}
        onClose={backToTables}
        onStartMove={() => setMoving(true)} />
      {moving && sale && <MoveSheet sale={sale} onClose={() => setMoving(false)} />}
    </div>
  )
}
```

- [ ] **Step 3: Ruta**: en `frontend/src/App.jsx`:
  - agregar `import SaleScreen from './camarero/SaleScreen'` junto a los imports del Camarero;
  - dentro de `<Route path="/camarero" ...>`, después de `<Route index element={<TablesScreen />} />`, agregar:

```jsx
            <Route path="venta/:saleId" element={<SaleScreen />} />
```

- [ ] **Step 4: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (viewport 375×812):

Con `mozo@galia.test`:
1. Abrir una mesa: la hoja "Agregar a Mesa n" aparece abajo, sin teclado abierto.
2. Agregar un producto con variante y modificadores (el detalle se ve dentro de la hoja) y tocar "Listo".
3. El ticket muestra "Pendientes de confirmar"; "← Mesas" vuelve y la tarjeta tiene el punto de pendientes; volver a la venta y "Confirmar tanda".
4. "Pedir cuenta", "Reabrir".
5. "Más" → "Dividir la cuenta": crea la cuenta y aparecen las pestañas "Cuenta 1 / Cuenta 2".
6. "Más" → "Mover de mesa": hoja con mesas libres; mover cambia la mesa del encabezado.
7. Sin `Cobrar`, no aparece "Cobrar".

Con `mozo2@galia.test` (Task 10, Step 1):
1. "Cobrar" abre una hoja sin teclado en pantalla; pagar en efectivo con "Justo" muestra "Venta cerrada"; "Listo" vuelve a mesas.
2. Las comprobaciones de "atrás" con hojas apiladas de la Task 2, Step 6.
3. Anular un ítem confirmado con un motivo del catálogo.

En `/pos` (escritorio), las comprobaciones de la caja de la Task 2, Step 6.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/camarero/SaleScreen.jsx frontend/src/camarero/MoveSheet.jsx frontend/src/App.jsx
git commit -m "feat(camarero): full-screen sale view and move sheet"
```

---

### Task 7: Plano con zoom

**Files:**
- Create: `frontend/src/camarero/utils/zoom.js` y `zoom.test.js`
- Create: `frontend/src/camarero/hooks/usePinchZoom.js`
- Create: `frontend/src/camarero/FloorView.jsx`
- Modify: `frontend/src/camarero/TablesScreen.jsx`

**Interfaces:**
- Consumes: `FloorPlan` (`isDimmed`), `isDimmed` de `tableFilters`.
- Produces:
  - `MIN_ZOOM = 1`, `MAX_ZOOM = 3`, `ZOOM_STEP = 0.5`;
  - `clampZoom(z)`, `stepZoom(z, direction: 1|-1)`, `pinchZoom(startZoom, startDistance, distance)`;
  - `usePinchZoom(): { zoom, setZoom, handlers }`;
  - `FloorView({ tables, filter, userId, onTableClick })`.

- [ ] **Step 1: Tests**: crear `frontend/src/camarero/utils/zoom.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { MAX_ZOOM, MIN_ZOOM, clampZoom, pinchZoom, stepZoom } from './zoom'

describe('zoom', () => {
  it('clampZoom limita entre 1× y 3× y corrige valores inválidos', () => {
    expect(clampZoom(0.5)).toBe(MIN_ZOOM)
    expect(clampZoom(4)).toBe(MAX_ZOOM)
    expect(clampZoom(1.7)).toBe(1.7)
    expect(clampZoom(Number.NaN)).toBe(MIN_ZOOM)
  })

  it('stepZoom avanza de a 0,5 y redondea al paso', () => {
    expect(stepZoom(1, 1)).toBe(1.5)
    expect(stepZoom(1.7, 1)).toBe(2)
    expect(stepZoom(1, -1)).toBe(1)
    expect(stepZoom(3, 1)).toBe(3)
  })

  it('pinchZoom escala según la distancia entre los dedos', () => {
    expect(pinchZoom(1, 100, 200)).toBe(2)
    expect(pinchZoom(2, 100, 50)).toBe(1)
    expect(pinchZoom(2, 100, 1000)).toBe(3)
    expect(pinchZoom(1.5, 0, 50)).toBe(1.5)
  })
})
```

- [ ] **Step 2: Correr y ver que falle**

Run: `npx vitest run src/camarero/utils/zoom.test.js`
Expected: FAIL (no existe `./zoom`).

- [ ] **Step 3: Implementar**: crear `frontend/src/camarero/utils/zoom.js`:

```js
export const MIN_ZOOM = 1
export const MAX_ZOOM = 3
export const ZOOM_STEP = 0.5

export const clampZoom = (zoom) =>
  Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number.isFinite(zoom) ? zoom : MIN_ZOOM))

// Botones +/−: de a ZOOM_STEP, alineado al paso.
export const stepZoom = (zoom, direction) =>
  clampZoom(Math.round((zoom + direction * ZOOM_STEP) / ZOOM_STEP) * ZOOM_STEP)

// Pellizco: el zoom acompaña la proporción entre la distancia actual y la inicial de los dos dedos.
export const pinchZoom = (startZoom, startDistance, distance) =>
  clampZoom(startDistance > 0 ? (startZoom * distance) / startDistance : startZoom)
```

- [ ] **Step 4: Correr el test**

Run: `npx vitest run src/camarero/utils/zoom.test.js`
Expected: PASS.

- [ ] **Step 5: Hook de pellizco**: crear `frontend/src/camarero/hooks/usePinchZoom.js`:

```js
import { useRef, useState } from 'react'
import { pinchZoom } from '../utils/zoom'

// Zoom con dos dedos sobre un contenedor (pointer events). El desplazamiento lo hace el scroll nativo:
// el contenedor debe tener touch-action: pan-x pan-y para que el navegador no haga su propio zoom.
export function usePinchZoom() {
  const [zoom, setZoom] = useState(1)
  const pointers = useRef(new Map())
  const start = useRef(null)

  const distance = () => {
    const [a, b] = [...pointers.current.values()]
    return Math.hypot(a.x - b.x, a.y - b.y)
  }

  const end = (event) => {
    pointers.current.delete(event.pointerId)
    if (pointers.current.size < 2) start.current = null
  }

  const handlers = {
    onPointerDown: (event) => {
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (pointers.current.size === 2) start.current = { zoom, distance: distance() }
    },
    onPointerMove: (event) => {
      if (!pointers.current.has(event.pointerId)) return
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (pointers.current.size === 2 && start.current) {
        setZoom(pinchZoom(start.current.zoom, start.current.distance, distance()))
      }
    },
    onPointerUp: end,
    onPointerCancel: end,
    onPointerLeave: end,
  }

  return { zoom, setZoom, handlers }
}
```

- [ ] **Step 6: Vista de plano**: crear `frontend/src/camarero/FloorView.jsx`:

```jsx
import { Minus, Plus } from 'lucide-react'
import FloorPlan from '@/pos/floor/FloorPlan'
import { usePinchZoom } from './hooks/usePinchZoom'
import { isDimmed } from './utils/tableFilters'
import { MAX_ZOOM, MIN_ZOOM, stepZoom } from './utils/zoom'

const zoomButton =
  'flex h-12 w-12 items-center justify-center rounded-full bg-white text-galia-plum shadow-md disabled:opacity-40'

// Plano de solo lectura con zoom (pellizco o +/−); FloorPlan se escala al ancho de su contenedor.
export default function FloorView({ tables, filter, userId, onTableClick }) {
  const { zoom, setZoom, handlers } = usePinchZoom()

  return (
    <div className="relative h-full">
      <div className="h-full overflow-auto p-3" style={{ touchAction: 'pan-x pan-y' }} {...handlers}>
        <div style={{ width: `${zoom * 100}%` }}>
          <FloorPlan tables={tables} isDimmed={(table) => isDimmed(table, filter, userId)} onTableClick={onTableClick} />
        </div>
      </div>
      <div className="absolute bottom-[calc(env(safe-area-inset-bottom)+1rem)] right-4 flex flex-col gap-2">
        <button type="button" aria-label="Acercar" disabled={zoom >= MAX_ZOOM}
          onClick={() => setZoom((z) => stepZoom(z, 1))} className={zoomButton}>
          <Plus size={22} />
        </button>
        <button type="button" aria-label="Alejar" disabled={zoom <= MIN_ZOOM}
          onClick={() => setZoom((z) => stepZoom(z, -1))} className={zoomButton}>
          <Minus size={22} />
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: Usarla en `TablesScreen`**. En `frontend/src/camarero/TablesScreen.jsx`:
  - reemplazar `import FloorPlan from '@/pos/floor/FloorPlan'` por `import FloorView from './FloorView'`;
  - quitar `isDimmed` del import de `./utils/tableFilters`, que queda `import { filterTables } from './utils/tableFilters'`;
  - reemplazar el bloque:

```jsx
        {ready && prefs.view === 'floor' && (
          <div className="p-3">
            <FloorPlan tables={data.tables} isDimmed={(table) => isDimmed(table, prefs.filter, userId)}
              onTableClick={onTableClick} />
          </div>
        )}
```

por:

```jsx
        {ready && prefs.view === 'floor' && (
          <FloorView tables={data.tables} filter={prefs.filter} userId={userId} onTableClick={onTableClick} />
        )}
```
- [ ] **Step 8: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (viewport 375×812, vista "Plano"):
- con + y −, el plano crece hasta 3× y se desplaza con scroll;
- − se deshabilita en 1×;
- tocar una mesa sigue abriéndola;
- con "Mías", las ajenas quedan atenuadas.

El pellizco real se prueba en un teléfono (Task 10, punto 2) o con la emulación táctil de DevTools.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/camarero
git commit -m "feat(camarero): zoomable floor view"
```

---

### Task 8: Conectividad y pantalla encendida

**Files:**
- Create: `frontend/src/camarero/utils/connectivity.js` y `connectivity.test.js`
- Create: `frontend/src/camarero/hooks/useConnectivity.js`
- Create: `frontend/src/camarero/hooks/useWakeLock.js`
- Create: `frontend/src/camarero/ConnectivityBanner.jsx`
- Modify: `frontend/src/camarero/CamareroLayout.jsx`

**Interfaces:**
- Consumes: `usePosChanges({ onResult })` (Task 3).
- Produces:
  - `initialConnectivity`;
  - `connectivityReducer(state, event)`, con eventos `'offline' | 'online' | 'poll-ok' | 'poll-network-error' | 'poll-http-error'`;
  - `pollEvent(ok, error)`;
  - `useConnectivity(): { online: boolean, report(ok, error) }`;
  - `useWakeLock(): void`.

- [ ] **Step 1: Tests**: crear `frontend/src/camarero/utils/connectivity.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { connectivityReducer, initialConnectivity, pollEvent } from './connectivity'

const run = (events, state = initialConnectivity) => events.reduce(connectivityReducer, state)

describe('connectivityReducer', () => {
  it('arranca conectado', () => {
    expect(initialConnectivity.online).toBe(true)
  })

  it('un fallo de red no alcanza; dos seguidos pasan a sin conexión', () => {
    expect(run(['poll-network-error']).online).toBe(true)
    expect(run(['poll-network-error', 'poll-network-error']).online).toBe(false)
  })

  it('una respuesta HTTP con error no cuenta como falta de red y reinicia el contador', () => {
    expect(run(['poll-network-error', 'poll-http-error', 'poll-network-error']).online).toBe(true)
  })

  it('el evento offline corta de inmediato', () => {
    expect(run(['offline']).online).toBe(false)
  })

  it('online no reconecta solo: espera una consulta exitosa', () => {
    expect(run(['offline', 'online']).online).toBe(false)
    expect(run(['offline', 'online', 'poll-ok']).online).toBe(true)
    expect(run(['poll-network-error', 'poll-network-error', 'poll-ok'])).toEqual({ online: true, failures: 0 })
  })

  it('ignora eventos desconocidos', () => {
    expect(run(['otro'])).toEqual(initialConnectivity)
  })
})

describe('pollEvent', () => {
  it('clasifica el resultado de la consulta', () => {
    expect(pollEvent(true)).toBe('poll-ok')
    expect(pollEvent(false, { response: { status: 500 } })).toBe('poll-http-error')
    expect(pollEvent(false, new Error('Network Error'))).toBe('poll-network-error')
    expect(pollEvent(false)).toBe('poll-network-error')
  })
})
```

- [ ] **Step 2: Correr y ver que falle**

Run: `npx vitest run src/camarero/utils/connectivity.test.js`
Expected: FAIL (no existe `./connectivity`).

- [ ] **Step 3: Implementar el reducer**: crear `frontend/src/camarero/utils/connectivity.js`:

```js
const FAILURES_TO_OFFLINE = 2

export const initialConnectivity = { online: true, failures: 0 }

// Estado de conexión del celular a partir de los eventos del navegador y del polling a /changes.
// Solo una consulta exitosa reconecta: el evento 'online' del navegador no garantiza llegar al servidor.
export function connectivityReducer(state, event) {
  switch (event) {
    case 'offline':
      return { ...state, online: false }
    case 'poll-ok':
      return { online: true, failures: 0 }
    case 'poll-http-error':
      return { ...state, failures: 0 }
    case 'poll-network-error': {
      const failures = state.failures + 1
      return { online: state.online && failures < FAILURES_TO_OFFLINE, failures }
    }
    default:
      return state
  }
}

// Un error con respuesta HTTP (4xx/5xx) significa que el servidor respondió: no es falta de red.
export const pollEvent = (ok, error) => {
  if (ok) return 'poll-ok'
  return error?.response ? 'poll-http-error' : 'poll-network-error'
}
```

- [ ] **Step 4: Correr el test**

Run: `npx vitest run src/camarero/utils/connectivity.test.js`
Expected: PASS.

- [ ] **Step 5: Hooks**: crear `frontend/src/camarero/hooks/useConnectivity.js`:

```js
import { useCallback, useEffect, useReducer } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { connectivityReducer, initialConnectivity, pollEvent } from '../utils/connectivity'

// Combina los eventos online/offline del navegador con el resultado de cada consulta a /changes.
export function useConnectivity() {
  const [state, dispatch] = useReducer(connectivityReducer, initialConnectivity)
  const queryClient = useQueryClient()

  useEffect(() => {
    const onOffline = () => dispatch('offline')
    const onOnline = () => {
      dispatch('online')
      // Consultar ya, sin esperar al próximo intervalo: la respuesta exitosa reconecta.
      queryClient.refetchQueries({ queryKey: ['pos-changes'] })
    }
    window.addEventListener('offline', onOffline)
    window.addEventListener('online', onOnline)
    if (navigator.onLine === false) dispatch('offline')
    return () => {
      window.removeEventListener('offline', onOffline)
      window.removeEventListener('online', onOnline)
    }
  }, [queryClient])

  const report = useCallback((ok, error) => dispatch(pollEvent(ok, error)), [])
  return { online: state.online, report }
}
```

Crear `frontend/src/camarero/hooks/useWakeLock.js`:

```js
import { useEffect } from 'react'

// Mantiene la pantalla encendida mientras la app está visible (si el navegador lo soporta).
// El navegador suelta el bloqueo al ocultarse la página; se vuelve a pedir al volver al frente.
export function useWakeLock() {
  useEffect(() => {
    if (!('wakeLock' in navigator)) return undefined
    let lock = null
    let cancelled = false

    const request = async () => {
      if (document.visibilityState !== 'visible') return
      try {
        lock = await navigator.wakeLock.request('screen')
        if (cancelled) lock.release().catch(() => {})
      } catch {
        lock = null
      }
    }
    const onVisibility = () => {
      if (document.visibilityState === 'visible') request()
    }

    request()
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', onVisibility)
      lock?.release().catch(() => {})
    }
  }, [])
}
```

- [ ] **Step 6: Banda y layout**: crear `frontend/src/camarero/ConnectivityBanner.jsx`:

```jsx
// Sin conexión: aviso fijo arriba y una capa que bloquea los toques (ninguna acción sale sin red).
export default function ConnectivityBanner({ online }) {
  if (online) return null
  return (
    <>
      <div className="fixed inset-0 z-[55]" aria-hidden="true" />
      <div role="status"
        className="fixed inset-x-0 top-0 z-[60] bg-red-700 px-4 pb-2 pt-[calc(env(safe-area-inset-top)+0.5rem)] text-center text-sm font-medium text-white">
        Sin conexión — reintentando…
      </div>
    </>
  )
}
```

Reemplazar `frontend/src/camarero/CamareroLayout.jsx` completo por:

```jsx
import { Outlet } from 'react-router-dom'
import { usePosChanges } from '@/pos/hooks/usePosChanges'
import { ModalPresentationContext } from '@/pos/ui/ModalPresentation'
import { ToastProvider } from '@/pos/ui/Toasts'
import ConnectivityBanner from './ConnectivityBanner'
import { useConnectivity } from './hooks/useConnectivity'
import { useWakeLock } from './hooks/useWakeLock'

function CamareroShell() {
  const { online, report } = useConnectivity()
  usePosChanges({ onResult: report })
  useWakeLock()
  return (
    <div className="flex h-dvh flex-col bg-galia-cream">
      <ConnectivityBanner online={online} />
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  )
}

// Vista del celular: los modales del POS se dibujan como hojas inferiores.
export default function CamareroLayout() {
  return (
    <ToastProvider>
      <ModalPresentationContext.Provider value="sheet">
        <CamareroShell />
      </ModalPresentationContext.Provider>
    </ToastProvider>
  )
}
```

- [ ] **Step 7: Verificar**

Run (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

Verificación en el navegador (viewport 375×812, en `/camarero/venta/<id>`):
1. DevTools → Network → Offline: aparece la banda roja y los botones no responden.
2. Volver a Online: en unos segundos se va la banda y la venta se refresca.
3. Detener el backend (sin tocar el modo offline): en unos 6 s aparece la banda; al levantarlo se va sola.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/camarero
git commit -m "feat(camarero): connectivity banner and screen wake lock"
```

---

### Task 9: PWA y aviso en la caja angosta

**Files:**
- Modify: `frontend/package.json` y `frontend/package-lock.json` (vía npm)
- Modify: `frontend/vite.config.js`
- Modify: `frontend/public/site.webmanifest`
- Modify: `frontend/index.html`
- Create: `frontend/src/camarero/UpdateBanner.jsx`
- Modify: `frontend/src/camarero/CamareroLayout.jsx`
- Create: `frontend/src/pos/layout/MobileHint.jsx`
- Modify: `frontend/src/pos/layout/PosLayout.jsx`

**Interfaces:**
- Produces:
  - un service worker `sw.js` (Workbox, `scope: '/camarero'`) que precachea solo los estáticos;
  - `UpdateBanner`, montado en `CamareroLayout`;
  - `MobileHint`, montado en `PosLayout`.

- [ ] **Step 1: Dependencias**

Run (cwd `frontend/`): `npm install -D vite-plugin-pwa@0.20.5 workbox-window@7.1.0`
Expected: se agregan a `devDependencies` sin errores.

- [ ] **Step 2: `vite.config.js`**: reemplazar el archivo completo por:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    // Service worker solo para el Camarero (scope /camarero): el resto de Galia no queda cacheado.
    // El manifest es public/site.webmanifest (lo enlaza index.html); la API nunca se cachea.
    VitePWA({
      registerType: 'prompt',
      injectRegister: false,
      manifest: false,
      scope: '/camarero',
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
        globIgnores: ['uploads/**'],
        navigateFallback: '/index.html',
        navigateFallbackAllowlist: [/^\/camarero/],
        navigateFallbackDenylist: [/^\/api/],
        runtimeCaching: [],
      },
      devOptions: { enabled: false },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.js'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Manifest e `index.html`**: reemplazar `frontend/public/site.webmanifest` completo por:

```json
{
  "name": "Galia Camarero",
  "short_name": "Camarero",
  "description": "Pedidos del salón de Galia Café desde el celular",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png"
    }
  ],
  "theme_color": "#5C2E46",
  "background_color": "#F5EFE6",
  "display": "standalone",
  "start_url": "/camarero",
  "scope": "/"
}
```

Antes de guardar, revisar en `frontend/tailwind.config.js` el valor real de `galia.cream` y usar ese hex en `background_color` (`#F5EFE6` es solo un valor de partida).

En `frontend/index.html`, reemplazar:

```html
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
```

por:

```html
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```

- [ ] **Step 4: Aviso de versión nueva**: crear `frontend/src/camarero/UpdateBanner.jsx`:

```jsx
import { useRegisterSW } from 'virtual:pwa-register/react'
import { btn } from '@/pos/ui/buttons'

// Registra el service worker del Camarero y avisa cuando hay una versión nueva del frontend.
export default function UpdateBanner() {
  const { needRefresh: [needRefresh, setNeedRefresh], updateServiceWorker } = useRegisterSW()
  if (!needRefresh) return null
  return (
    <div className="flex items-center justify-between gap-3 bg-galia-lime/40 px-4 py-2 pt-[calc(env(safe-area-inset-top)+0.5rem)] text-sm">
      <span>Hay una versión nueva</span>
      <span className="flex items-center gap-2">
        <button type="button" className={btn('primary', 'min-h-[40px]')} onClick={() => updateServiceWorker(true)}>
          Actualizar
        </button>
        <button type="button" aria-label="Más tarde" className="min-h-[40px] px-2" onClick={() => setNeedRefresh(false)}>×</button>
      </span>
    </div>
  )
}
```

En `frontend/src/camarero/CamareroLayout.jsx`:
- agregar `import UpdateBanner from './UpdateBanner'`;
- dentro de `CamareroShell`, después de `<ConnectivityBanner online={online} />`, agregar `<UpdateBanner />`.

- [ ] **Step 5: Aviso en la caja angosta**: crear `frontend/src/pos/layout/MobileHint.jsx`:

```jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'

const KEY = 'pos.mobileHintDismissed'

function initiallyVisible() {
  try {
    return window.matchMedia('(max-width: 767px)').matches && localStorage.getItem(KEY) !== '1'
  } catch {
    return false
  }
}

// En un celular, la caja sugiere la vista del Camarero (sin forzarla).
export default function MobileHint() {
  const [visible, setVisible] = useState(initiallyVisible)
  if (!visible) return null

  const dismiss = () => {
    try {
      localStorage.setItem(KEY, '1')
    } catch {
      // Sin storage: el aviso se oculta solo por ahora.
    }
    setVisible(false)
  }

  return (
    <div className="flex items-center gap-3 bg-galia-lime/40 px-4 py-2 text-sm">
      <span className="flex-1">
        ¿Estás en el celular? <Link to="/camarero" className="font-semibold underline">Abrí la vista Camarero</Link>
      </span>
      <button type="button" aria-label="Cerrar aviso" className="min-h-[40px] px-2" onClick={dismiss}>×</button>
    </div>
  )
}
```

En `frontend/src/pos/layout/PosLayout.jsx`:
- agregar `import MobileHint from './MobileHint'`;
- en `PosShell`, después de `<PosTopBar />`, agregar `<MobileHint />`.

- [ ] **Step 6: Verificar**

Run (cwd `frontend/`): `npm test`, `npm run build` y después `ls dist/sw.js dist/workbox-*.js`.
Expected:
- Vitest pasa;
- el build termina y lista los archivos precacheados, sin incluir `uploads/`;
- `dist/sw.js` existe.

Verificación en el navegador:
- **`/pos` con viewport 375 de ancho:** aparece el aviso; "×" lo oculta y no vuelve al recargar.
- **Instalabilidad:** la verifica la Task 10 sobre `vite preview`.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/public/site.webmanifest frontend/index.html frontend/src/camarero frontend/src/pos/layout
git commit -m "feat(camarero): installable PWA with update prompt and mobile hint in the POS"
```

---

### Task 10: Datos de prueba y verificación final

**Files:**
- Modify: `backend/scripts/seed_pos_demo.py`
- Create (no se commitea): `.claude/launch.json` en la raíz del worktree y `<scratch>/prep_sqlite_preview.py`

- [ ] **Step 1: Entorno de preview.** Esto lo usan también las verificaciones de las Tasks 3 a 9; quien coordina puede hacerlo antes de la Task 3.

En `backend/scripts/seed_pos_demo.py`:
- en el docstring, después de la línea de `mozo@galia.test`, agregar `    mozo2@galia.test  Camarero, Cobrar, Anular`;
- en `seed()`, después de `_user('mozo@galia.test', 'employee', ('Camarero',))`, agregar:

```python
    _user('mozo2@galia.test', 'employee', ('Camarero', 'Cobrar', 'Anular'))
```

Crear `<scratch>/prep_sqlite_preview.py` (`<scratch>` es el scratchpad de la sesión). Crea una base SQLite descartable, porque Docker no está disponible:

```python
"""Base SQLite descartable para el preview del POS/Camarero.

Uso: cwd = backend/ del worktree, DATABASE_URL=sqlite:///<ruta>, POS_DEMO_SEED=1, PY prep_sqlite_preview.py
Crea las tablas con create_all, carga lo que en Postgres cargan las migraciones (módulos del POS,
medios de pago, motivos de anulación) y corre seed_pos_demo.
"""
import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'scripts'))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Module  # noqa: E402
from app.models.pos import CancelReason, PaymentMethod  # noqa: E402

app = create_app('production')
with app.app_context():
    db.create_all()
    for name in ('POS', 'Camarero', 'Cobrar', 'Anular', 'Descuentos', 'Products', 'Stock', 'Sales'):
        if not Module.query.filter_by(name=name).first():
            db.session.add(Module(name=name, display_name=name, is_active=True))
    db.session.flush()
    for name, kind, position in [('Efectivo', 'cash', 0), ('Débito', 'card', 1), ('Crédito', 'card', 2),
                                 ('Transferencia', 'transfer', 3), ('MercadoPago', 'other', 4)]:
        if not PaymentMethod.query.filter_by(name=name).first():
            db.session.add(PaymentMethod(name=name, kind=kind, position=position))
    for position, name in enumerate(('Error de carga', 'Cliente se arrepintió', 'Invitación de la casa',
                                     'Producto agotado')):
        if not CancelReason.query.filter_by(name=name).first():
            db.session.add(CancelReason(name=name, position=position))
    db.session.commit()
    import seed_pos_demo
    seed_pos_demo.seed()
    print('ok')
```

Run (Git Bash, cwd `backend/`):

```
DATABASE_URL='sqlite:///<scratch>/camarero_preview.db' POS_DEMO_SEED=1 FLASK_ENV=production PY <scratch>/prep_sqlite_preview.py
```

Expected: imprime `ok`.

Crear `.claude/launch.json` en la raíz del worktree (no se commitea), reemplazando `<scratch>` por la ruta real con barras `/`:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "camarero-backend",
      "runtimeExecutable": "C:\\Program Files\\Git\\bin\\bash.exe",
      "runtimeArgs": ["-c", "cd /c/Users/onofr/Desktop/galia-app/.claude/worktrees/pos-base/backend && FLASK_ENV=production DATABASE_URL='sqlite:///<scratch>/camarero_preview.db' /c/Users/onofr/Desktop/galia-app/backend/venv/Scripts/python.exe -m flask --app run.py run --port 5001"],
      "port": 5001
    },
    {
      "name": "camarero-frontend",
      "runtimeExecutable": "C:\\Program Files\\Git\\bin\\bash.exe",
      "runtimeArgs": ["-c", "cd /c/Users/onofr/Desktop/galia-app/.claude/worktrees/pos-base/frontend && npm run dev"],
      "port": 5173
    },
    {
      "name": "camarero-preview-build",
      "runtimeExecutable": "C:\\Program Files\\Git\\bin\\bash.exe",
      "runtimeArgs": ["-c", "cd /c/Users/onofr/Desktop/galia-app/.claude/worktrees/pos-base/frontend && npm run build && npx vite preview --port 4173"],
      "port": 4173
    }
  ]
}
```

Si los puertos 5001 o 5173 están ocupados por los previews de otra sesión (`pos-caja-*`), detenerlos o usar otros puertos.

- [ ] **Step 2: Suites completas**

Backend (cwd `backend/`):

```
PY -m pytest -q -p no:cacheprovider -rfE > <scratch>/pos_camarero_pytest.txt
PY scripts/compare_baseline.py <scratch>/pos_camarero_pytest.txt ../docs/superpowers/plans/2026-10-08-pos-base-test-baseline.txt
```

Expected: `Sin fallas nuevas.` (el test de `test_timezone_fix.py::TestIntegrationScenarios::test_full_day_workflow_argentina_timezone` falla a veces también en `main`).

Frontend (cwd `frontend/`): `npm test` y `npm run build`.
Expected: todo pasa.

- [ ] **Step 3: Verificación manual completa**: preview con `camarero-backend` y `camarero-frontend`, viewport 375×812. Contraseña de los usuarios demo: `DEMO_PASSWORD` de `seed_pos_demo.py`.

1. Login como `mozo@galia.test` → `/camarero`.
2. Lista y Plano (zoom), Mías y Todas, cambio de salón. Recargar conserva las preferencias.
3. Abrir una mesa (sin selector de mozo) → "Agregar productos" en hoja inferior; cargar con variante, modificadores y nota; confirmar la tanda.
4. El punto de pendientes aparece en la tarjeta antes de confirmar y desaparece después.
5. Pedir la cuenta, dividir (pestañas de cuentas) y mover de mesa con `MoveSheet`.
6. `mozo2@galia.test`: cobrar en efectivo con vuelto, sin teclado en pantalla → "Venta cerrada" → mesas. Con `mozo@galia.test` no aparece "Cobrar".
7. `mozo2@galia.test`: anular un ítem confirmado con un motivo del catálogo.
8. El "atrás" del navegador cierra la hoja abierta sin salir de la venta; con dos hojas, cierra de a una.
9. La caja (`/pos`, como `caja@galia.test`, en otra ventana del preview) ve los cambios del celular en unos 3 s, y al revés.
10. DevTools en modo offline: banda, toques bloqueados, recuperación al volver la red.
11. La caja en escritorio (1280 px) sigue igual: modales centrados, `Escape` cierra, panel lateral de 400 px, selector de mozo al abrir mesa.
12. Con `camarero-preview-build` (puerto 4173):
    - DevTools → Application muestra el manifest "Galia Camarero" sin errores de instalabilidad y el service worker con scope `/camarero`;
    - `/dashboard` no queda controlado por el service worker;
    - después de cambiar un texto, reconstruir y recargar `/camarero`, aparece "Hay una versión nueva" (descartar después el cambio de prueba).
13. Sesión vencida: en `/camarero/venta/<id>`, borrar `auth_token` de `localStorage` y recargar → login → vuelve a esa venta.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/seed_pos_demo.py
git commit -m "chore(pos): demo waiter user with charge and cancel permissions"
```
