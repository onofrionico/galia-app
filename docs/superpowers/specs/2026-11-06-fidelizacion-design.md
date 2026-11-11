# Módulo de fidelización ("cafecitos") — diseño

Fecha: 2026-11-06
Origen: spec "Especificación de requerimientos - Módulo de fidelización Galia" (Google Doc), revisada y cerrada en conversación con el dueño. Donde este documento y el Google Doc difieren, manda este documento.

## 1. Para qué

Hoy la fidelización es una tarjeta de sellos de papel (8 cafés = 1 gratis). No deja datos: no sabemos quiénes son los clientes, cada cuánto vuelven ni cuánto gastan. El módulo reemplaza la tarjeta por un **programa de puntos ("cafecitos") con wallet**, atado a las ventas del POS nativo, y da reportes de clientes activos/inactivos, canjes y gasto de registrados vs. no registrados.

**Éxito:** el barista asocia al cliente en segundos en hora pico, los cafecitos se acreditan solos, el cliente ve su saldo en el celular y el dueño ve quién vuelve y cuánto vale el programa.

## 2. Alcance

**Entra**
- Entidad Cliente con autoregistro desde la carta digital (Google).
- Cafecitos configurables por producto; acreditación automática al cerrar una venta del POS.
- Wallet como libro de movimientos; canje hecho por el empleado en el POS.
- Catálogo de premios configurable.
- Ajustes manuales y configuración solo para admins del módulo, con historial.
- Reportes 5.1–5.4 (ver §8).

**No entra (esta etapa)**
- Mails/promociones a inactivos (sí se guarda el consentimiento, ver §3).
- Pedidos anticipados desde la app.
- Canje iniciado por el cliente desde el celular.
- Unir registros duplicados.
- Vencimiento de cafecitos (no vencen).
- Ventas de Fudo: no se asocian a clientes; cuentan como "no registrado".

**Anti-objetivos (sería un fracaso aunque funcione)**
- Que identificar al cliente frene la caja en hora pico.
- Que el saldo de un cliente pueda quedar mal sin rastro de por qué (todo movimiento tiene origen).
- Que un empleado común pueda regalar cafecitos.

## 3. Cliente

- Se registra **solo**, desde la carta digital (`menu-site`), con **"Entrar con Google"**. De Google se toman nombre, apellido y mail. El teléfono es opcional y lo puede cargar el cliente después.
- Al registrarse acepta términos y, aparte y opcional, el consentimiento para recibir promociones por mail (casilla sin tildar por defecto). Se guarda fecha de aceptación de cada uno.
- **Sellos de papel al registrarse:** los pasa un admin del módulo con un ajuste manual (`adjustment`, motivo "sellos de tarjeta de papel"). El barista no carga saldo.
- Quien no tiene smartphone o Google **no se registra**: sigue con la tarjeta de sellos de papel, por fuera del sistema. El empleado mantiene la consistencia a mano. El sistema no modela la tarjeta de papel.
- No hay tarjetas físicas con QR. El QR vive solo en la app.
- El QR codifica un **token opaco** del cliente (no su id ni su mail), que un admin puede regenerar si hace falta.
- No se unen duplicados.

## 4. Cafecitos y wallet

- Cada **variante de producto** (`product_variants`, que es donde vive el precio) tiene un campo `cafecitos` entero ≥ 0, default 0. *Decisión mía:* va en la variante porque un café chico y uno grande pueden valer distinto; la pantalla de configuración permite cargar el mismo valor a todas las variantes de un producto de una vez.
- No hace falta que sean cafés: cualquier producto puede dar cafecitos.
- **Wallet = libro de movimientos.** El saldo es la suma de los movimientos del cliente (se puede cachear en el cliente, pero el libro es la verdad). Tipos de movimiento:
  - `earn` — acreditación por venta cerrada.
  - `earn_reversal` — reversa de una acreditación porque la venta se anuló.
  - `redeem` — canje de un premio.
  - `redeem_reversal` — reversa de un canje (ítem de canje o venta anulados).
  - `adjustment` — ajuste manual de un admin, con motivo obligatorio.
- Cada movimiento guarda: cliente, cantidad (con signo), tipo, venta POS y/o ítem de origen, premio (si aplica), usuario que lo originó, fecha, motivo.
- Los cafecitos **no vencen**.
- El saldo nunca puede quedar negativo por un canje. Un ajuste manual que lo dejaría negativo se rechaza.

### Cuándo se acredita
- Al **cerrar** la venta del POS (el punto de enganche es `close_sale_rows` en `services/pos/closing.py`), si la venta tiene cliente.
- Se acredita, por cada ítem confirmado que no sea de canje: `cantidad × cafecitos de la variante en ese momento`. El valor queda congelado en el movimiento: si después cambia la configuración, lo ganado no cambia.
- Ítems cancelados no suman. Ítems de canje no suman. Ventas de práctica (`is_practice`) no suman ni descuentan nada.
- *Decisión mía:* los descuentos de precio no afectan los cafecitos (se cuenta por unidad, no por pesos). Cantidades fraccionarias se redondean hacia abajo.
- Si la venta se divide (`split_from_id`), cada venta resultante acredita lo suyo a su propio cliente.

### Cuándo se revierte
- Si una venta **cerrada** se anula (`cancel_sale`, que ya contempla anular cerradas sin pagos), se genera `earn_reversal` por lo acreditado y `redeem_reversal` por los canjes de esa venta.
- Una venta cerrada puede volver a `billing` (por ejemplo, al anular un pago con `cancel_payment`) y cerrarse de nuevo. *Decisión mía:* al reabrirse se revierte lo acreditado (`earn_reversal`) y al recerrarse se acredita de nuevo según los ítems de ese momento. Los canjes no se tocan al reabrir, solo si se cancela el ítem de canje o la venta.
- Si la reversa de un `earn` dejara el saldo negativo (el cliente ya gastó esos cafecitos), se registra igual y el saldo queda negativo; el cliente no puede canjear hasta volver a positivo. *Decisión mía:* es raro y no vale la pena bloquear la anulación.

## 5. Identificar al cliente en el POS

Dos lugares, ambos con el mismo buscador:

1. **Botón "Cliente" en la cabecera de la venta** (`frontend/src/pos/sale/SaleHeader.jsx`), disponible en cualquier momento mientras la venta está abierta o en cobro. Muestra el saldo del cliente y cuántos cafecitos suma la venta actual.
2. **En el modal de cobro** (`frontend/src/pos/modals/PaymentModal.jsx`): si la venta no tiene cliente, ofrece asociarlo. Es opcional y no bloquea el cobro.

El buscador:
- Campo de texto que busca por nombre, apellido, mail o teléfono. Muestra todas las coincidencias con mail/teléfono parcialmente enmascarados para desambiguar homónimos.
- Botón "QR" que abre la cámara del dispositivo y lee el token. *Decisión mía:* además, si se pega/tipea un token en el campo (lector de QR USB que actúa como teclado), lo resuelve directo.
- Objetivo de rapidez: resultados en < 300 ms con 10.000 clientes (índices adecuados, búsqueda desde 2 caracteres, debounce).
- Se puede quitar o cambiar el cliente mientras la venta no está cerrada.

`pos_sales` gana `customer_id` (FK nullable). El `customer_name` de texto libre existente se mantiene para lo que ya se usa (nombre en comanda/mesa); al asociar un cliente se completa con su nombre si estaba vacío.

## 6. Canje

- Lo hace **siempre el empleado en el POS**, con el cliente ya asociado a la venta. Botón "Canjear" junto al cliente.
- Lista los premios activos; los que no alcanzan aparecen deshabilitados con "faltan N".
- Al confirmar: entra a la venta un ítem del producto del premio a **$0**, marcado como ítem de canje, y se registra un `redeem` por el costo del premio. El resto del saldo queda en el wallet.
- El canje se descuenta **al agregarlo** (no al cerrar), para que el saldo no se pueda gastar dos veces en dos ventas abiertas a la vez.
- Si se cancela el ítem de canje o la venta, se genera `redeem_reversal`.
- El ítem de canje sigue el circuito normal del POS (comanda, stock), pero no suma cafecitos.
- Cada canje guarda: premio, costo en cafecitos vigente en ese momento, **valor en pesos** (precio de la variante del premio en ese momento), venta, empleado, fecha.
- Canje siempre total: un premio se paga entero con cafecitos, no se combina con pesos.
- **Modificadores:** el ítem de canje pide los modificadores obligatorios como cualquier ítem, pero los recargos **se regalan**: la línea queda en $0 con modificadores incluidos. El valor en pesos del canje (5.2) es el precio de la variante más los recargos de los modificadores elegidos.

## 7. Premios y configuración

- **Premio:** nombre, variante de producto que entrega, costo en cafecitos, activo/inactivo. Ejemplos iniciales: café gratis = 8, focaccia = 10.
- Cambiar el costo de un premio no afecta canjes ya hechos (quedan congelados). No hay "canjes alcanzados" pendientes: el saldo es el saldo y el costo vigente es el que se cobra al canjear.
- **Configuración del módulo:** período de cliente activo (días, default 30).
- **Permisos:** nuevo módulo `Fidelizacion` en `modules`. Asociar clientes y canjear es **solo de la caja** (permiso `POS`); los mozos (`Camarero`) y el permiso `Cobrar` no ven el botón "Cliente" ni "Canjear", y las rutas nuevas lo validan con `module_required('POS')`. Los cafecitos se acreditan igual al cerrar, aunque la venta la haya abierto un mozo, si la caja asoció al cliente. Configurar cafecitos por producto, premios, período, y hacer ajustes manuales: solo usuarios con permiso del módulo Fidelización (usa `module_required`).
- **Historial de cambios:** todo cambio de configuración (cafecitos de una variante, alta/baja/cambio de premio, período) y todo ajuste manual queda registrado con usuario, fecha, valor anterior y nuevo. Visible en el módulo.

## 8. App de premios en la carta

Nueva sección "Mis cafecitos" en `menu-site`:
- Sin sesión: botón "Entrar con Google" y explicación corta del programa.
- Con sesión: saldo grande, QR para mostrar en la caja, premios (los que alcanzan y cuánto falta para el resto), historial de movimientos, editar teléfono, cerrar sesión.
- Solo lectura: el cliente no canjea desde acá.
- Autenticación de clientes **separada** de la de empleados: el backend valida el ID token de Google y emite su propio token de cliente, que solo sirve para los endpoints públicos de la wallet. Nunca da acceso a la app de gestión.
- Requiere crear un OAuth Client ID de Google para el dominio de la carta (tarea del dueño, ver §11).

## 9. Reportes

Una sección de reportes dentro del módulo Fidelización. Todos aceptan filtro por mes o por rango libre de fechas, salvo que se diga otra cosa.

- **Visita:** cualquier venta del POS cerrada, no anulada, no de práctica, con cliente asociado. Fecha = `business_date` (fecha comercial).
- **5.1 Activos:** clientes con al menos una visita en los últimos N días (N = período configurado), a la fecha de hoy. Total y listado.
- **5.3 Inactivos:** clientes registrados sin visitas en ese mismo período (incluye registrados que nunca vinieron, marcados como tales). Total y listado con fecha de última visita.
- **5.2 Canjes:** total de canjes del período, desglose por premio, cafecitos canjeados y valor en pesos, ambos con los valores congelados en cada canje. Excluye canjes revertidos.
- **5.4 Registrados vs. no registrados:** para cada grupo, total facturado y ticket promedio **por venta**, en el período. *Decisión mía:* "facturado" es el total vendido (el `total` de la venta), tenga o no comprobante fiscal de ARCA. Registrado = la venta tenía cliente asociado. Las ventas sin cliente (incluidas todas las importadas de Fudo) cuentan como no registradas, y la pantalla lo aclara con una nota visible.

## 10. Lo que dejo al builder

- Nombres de tablas/columnas, forma exacta de los endpoints y del token de cliente.
- Librería de lectura de QR por cámara y de Google Sign-In.
- Cómo cachear el saldo (si se cachea).
- Diseño visual fino de las pantallas, siguiendo los bocetos: botón "Cliente" en la cabecera de la venta con saldo y "+N", buscador con QR, lista de premios con "faltan N", y en la carta saldo grande + QR + premios + movimientos.
- Orden de entrega en etapas.

## 11. Dependencias y pendientes fuera del código

- Crear el OAuth Client ID de Google (dueño) y cargarlo como variable de entorno en backend y carta.
- Texto de términos y del consentimiento de promociones (dueño).
- Cargar cafecitos a los productos y los premios iniciales antes de lanzar.
