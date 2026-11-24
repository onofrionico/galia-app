# POS: acciones visibles en el panel de venta

Cambio chico (solo frontend, `frontend/src/pos/sale/`). Diseño corto.

## Intención y por qué
Hoy hay acciones escondidas en el panel de venta: el botón "Más" del pie (Descuento a la venta, Precuenta, Mover de mesa, Dividir, Cerrar con saldo 0, Anular venta) y el menú que se abre al tocar cada ítem (Borrar, Descuento al ítem, Anular). El usuario quiere que todo esté visible, sin tocar "Ver más" para llegar a una acción.

## Objetivos
- Ninguna acción del panel queda detrás de un toque extra.
- Mismos permisos y reglas que hoy (`saleActions` / `itemActions` en `utils/permissions.js` no cambian): solo se muestran las acciones que corresponden al estado.
- Funciona en el panel lateral (400–440 px) y en pantalla completa de celular.

## No objetivos / anti-objetivos
- No cambiar permisos, endpoints ni el backend.
- No sumar acciones nuevas.
- Que una acción destructiva quede a un toque sin protección: Anular (ítem y venta) sigue pidiendo motivo en `CancelReasonModal`.

## Approaches considerados
- Pie: A) dos filas con todo visible (elegido); B) barra de íconos con etiqueta; C) acciones contextuales según estado.
- Ítems: D) iconos siempre visibles en la fila (elegido); E) deslizar para accionar (sigue oculto).
- Elegido por el usuario: **A + D**, tras ver maquetas.

## Diseño
**Pie (`SaleFooter.jsx`)**
- Se mantiene el total/saldo.
- Fila principal: Agregar, Confirmar tanda (N), Reabrir, Pedir cuenta y Cobrar, como hoy (grilla de 2 columnas). Se elimina el botón "Más" y el estado `moreOpen`.
- Debajo, una fila de chips con ícono y texto, que se envuelven: Descuento a la venta, Precuenta, Mover de mesa, Dividir la cuenta, Cerrar con saldo 0. Cada uno aparece solo si su acción está habilitada.
- "Anular la venta" va aparte, a la derecha de la fila de chips, en rojo.
- Venta cerrada o anulada: sin cambios.

**Ítems (`TicketItem.jsx`)**
- Se elimina el menú que se despliega al tocar la fila (`menuOpen`).
- A la derecha del importe, botones de ícono de 36–40 px mínimo de alto táctil, con `aria-label`: tacho (Borrar, ítem pendiente en venta abierta), % (Descuento al ítem), ⊘ (Anular, con permiso). Solo los que `itemActions` habilita.
- Anular abre `CancelReasonModal` como hoy. Borrar de un ítem pendiente sigue siendo inmediato, como hoy.

## Constraints
- Estilos con las clases y tokens Galia ya usados (`btn(...)`, `galia-plum`); íconos de `lucide-react`.
- El ancho de 400 px debe alojar el importe más los iconos sin cortar el nombre del producto (truncar con elipsis, nombre en dos líneas permitido).

## Queda a criterio de quien construye
- Íconos exactos de lucide, tamaños y espaciado.
- Si "Pedir cuenta" queda en la grilla principal (es lo que hace hoy) o pasa a los chips: se deja en la principal.
- Tests: actualizar/agregar tests de componente si existen para estos archivos; verificar a mano el panel con una venta de salón (pendiente, confirmada, billing) en desktop y en ancho de celular.
