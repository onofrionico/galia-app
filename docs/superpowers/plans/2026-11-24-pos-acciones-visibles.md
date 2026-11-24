# POS: acciones visibles en el panel de venta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que todas las acciones del panel de venta del POS estén visibles (sin botón "Más" ni menú al tocar un ítem).

**Architecture:** La lista y el orden de acciones se deciden en un helper puro y testeado (`utils/saleLayout.js`), que consume lo que ya devuelven `saleActions`/`itemActions`. `SaleFooter` y `TicketItem` solo renderizan esa lista. Backend y permisos no cambian.

**Tech Stack:** React, Tailwind (clases Galia), lucide-react, vitest (el repo solo testea utilidades puras `*.test.js`; no hay testing-library).

**Spec:** `docs/superpowers/specs/2026-11-24-pos-acciones-visibles-design.md`

## Global Constraints

- Mismos permisos y reglas que hoy: `saleActions` e `itemActions` en `frontend/src/pos/utils/permissions.js` no se modifican.
- Anular (ítem y venta) sigue pasando por `CancelReasonModal`; "Borrar" de un ítem pendiente sigue siendo inmediato.
- Venta cerrada/anulada: el pie no cambia.
- "Pedir cuenta" se queda en la grilla principal junto a "Cobrar".
- Botones táctiles de al menos 36 px de alto/ancho en ítems; funciona en panel de 400 px y en pantalla completa de celular.
- Íconos de `lucide-react` (^0.303.0): verificar que cada nombre exista en esa versión antes de importarlo.

## Review Focus

- Venta sin ninguna acción secundaria habilitada (p. ej. sin ítems confirmados): no debe aparecer una fila vacía de chips.
- Usuario sin permiso de anular: no aparece "Anular la venta" ni el ⊘ en ítems.
- Ítem pendiente: solo tacho; ítem confirmado: solo % y ⊘ (nunca los tres a la vez).
- Ítem cancelado o venta en `billing` con ítem pendiente: no muestra Borrar.
- Nombre de producto largo no empuja los íconos fuera del panel de 400 px.

---

### Task 1: Helper de acciones visibles

**Files:**
- Create: `frontend/src/pos/utils/saleLayout.js`
- Test: `frontend/src/pos/utils/saleLayout.test.js`

**Interfaces:**
- Consumes: el objeto que devuelve `saleActions(sale, perms)` (claves `discount`, `printBill`, `move`, `split`, `close`, `cancelSale`) y el que devuelve `itemActions(item, sale, perms)` (claves `remove`, `discount`, `cancel`), ambos en `utils/permissions.js`.
- Produces:
  - `footerChips(actions) -> Array<{ key: 'discount'|'printBill'|'move'|'split'|'close'|'cancelSale', label: string, danger: boolean }>` — orden fijo: discount, printBill, move, split, close, cancelSale (siempre último); solo las habilitadas. Labels: "Descuento", "Precuenta", "Mover de mesa", "Dividir la cuenta", "Cerrar con saldo 0", "Anular la venta". `danger` solo en `cancelSale`.
  - `itemButtons(actions) -> Array<{ key: 'remove'|'discount'|'cancel', label: string, danger: boolean }>` — orden fijo: remove, discount, cancel; solo las habilitadas. Labels: "Borrar", "Descuento al ítem", "Anular". `danger` en remove y cancel.

- [ ] **Step 1: Write the failing tests** in `saleLayout.test.js`: `footerChips` con todo habilitado devuelve las 6 keys en el orden indicado y solo `cancelSale` con `danger: true`; con `{}` devuelve `[]`; con `{ cancelSale: false, split: true }` devuelve solo `split`. `itemButtons({ remove: true })` → solo `remove`; `itemButtons({ discount: true, cancel: true })` → keys `['discount','cancel']`; `itemButtons({})` → `[]`.
- [ ] **Step 2: Run** `npm test -- saleLayout` (desde `frontend/`). Expected: FAIL, módulo no existe.
- [ ] **Step 3: Implement** `footerChips` e `itemButtons` en `saleLayout.js` con una tabla constante de definiciones filtrada por `actions[key]`.
- [ ] **Step 4: Run** `npm test -- saleLayout`. Expected: PASS.
- [ ] **Step 5: Commit**
```bash
git add frontend/src/pos/utils/saleLayout.js frontend/src/pos/utils/saleLayout.test.js
git commit -m "feat(pos): helper de acciones visibles del panel de venta"
```

### Task 2: Pie y filas de ítem sin menús ocultos

**Files:**
- Modify: `frontend/src/pos/sale/SaleFooter.jsx` (estado abierto/cerrado: líneas 31–82)
- Modify: `frontend/src/pos/sale/TicketItem.jsx` (todo el cuerpo del componente)

**Interfaces:**
- Consumes: `footerChips(actions)` e `itemButtons(actions)` de Task 1. Los handlers existentes: `handlers.discount|printBill|move|split|close|cancelSale` en `SaleFooter`; `handlers.remove|discount|cancel` en `TicketItem`.
- Produces: nada que otras tareas consuman.

- [ ] **Step 1: `SaleFooter.jsx`** — quitar `useState`, `moreOpen`, el import de `MoreHorizontal` y el bloque desplegable. Mantener la grilla principal (Agregar, Confirmar, Pedir cuenta, Reabrir, Cobrar). Debajo, si `footerChips(actions)` no está vacío, renderizar una fila `flex flex-wrap gap-2` de chips (botones `btn('secondary', 'min-h-[40px] px-3 text-sm')` con ícono lucide de 16 px por `key` y el `label`), todos `disabled={busy}`, llamando `handlers[key]()`. El chip con `danger` usa `btn('danger', …)` y va con `ml-auto`. Íconos sugeridos: discount `Percent`, printBill `Printer`, move `ArrowRightLeft`, split `SplitSquareHorizontal`, close `CheckCircle2`, cancelSale `Ban`.
- [ ] **Step 2: `TicketItem.jsx`** — quitar `useState`, `menuOpen`, `pick` y el bloque desplegable; la fila deja de ser un `<button>` y pasa a `div` con el texto (nombre con `truncate`/`min-w-0`, detalles y nota como hoy) y, a la derecha, el importe seguido de los botones de `itemButtons(actions)`: cada uno un `<button type="button">` cuadrado de 36×36 px mínimo, con `aria-label={label}`, `title={label}`, ícono de 18 px (remove `Trash2`, discount `Percent`, cancel `Ban`), color rojo para `danger`, `disabled={busy}` solo en remove; `onClick={() => handlers[key](item)}`. Mantener tal cual el motivo de anulación y la lista de descuentos del ítem.
- [ ] **Step 3: Verificar tests y lint** — `npm test` y `npm run lint` (si existe) desde `frontend/`. Expected: todo en verde.
- [ ] **Step 4: Verificación manual** — levantar el frontend con backend local y revisar una venta de salón en tres estados: (a) con ítem pendiente y confirmado en venta `open`, (b) en `billing`, (c) cerrada. Comprobar contra Review Focus: no hay botón "Más" ni menú al tocar ítems; íconos correctos por estado; sin chips vacíos; nombre largo no rompe el ancho; ancho de celular (375 px). Anular ítem y anular venta siguen pidiendo motivo. Si algo no se pudo probar, decirlo.
- [ ] **Step 5: Commit**
```bash
git add frontend/src/pos/sale/SaleFooter.jsx frontend/src/pos/sale/TicketItem.jsx
git commit -m "feat(pos): acciones del panel de venta siempre visibles"
```
