# Guía de caja: Galia POS

Para imprimir y tener al lado de la caja. Si algo no sale, llamá al encargado.

## Abrir la caja (al empezar el turno)

1. Entrá a **Galia POS** y tocá **Caja** arriba.
2. Tocá **Abrir caja**.
3. En **Fondo inicial**, poné el efectivo con el que arranca la caja (contalo antes).
4. Confirmá. Arriba deja de decir **Caja cerrada**.

Sin la caja abierta se puede vender igual, pero los pagos quedan "sin caja": abrila siempre primero.

## Cobrar

1. En la mesa (o en **Mostrador**), tocá **Pedir cuenta** y después **Cobrar**.
2. Elegí el medio de pago:
   - **Efectivo**: anotá lo que te dieron en **Recibido** y Galia calcula el vuelto.
   - **Tarjeta** (débito o crédito de la terminal): elegí el medio y el monto.
   - **MercadoPago Point**: tocá **Enviar al Point**, llevá el Point a la mesa y esperá "Cobro aprobado". No cierres la pantalla hasta que termine; si la cerrás, la mesa muestra **Cobro en Point pendiente** con **Ver** y **Cancelar**.
3. Se puede cobrar una parte con un medio y el resto con otro. Cuando el saldo llega a 0, la venta se cierra sola.
4. **Imprimir ticket** si el cliente lo pide. **Facturar** solo si el cliente pide factura.

## Anular un pago

1. En **Cobrar**, tocá la **X** al lado del pago.
2. Elegí el **Motivo** (o escribilo) y tocá **Anular**.
3. Si el pago fue con el **Point**, elegí:
   - **Devolver también en MercadoPago**: se le devuelve la plata al cliente.
   - **Solo anular en Galia**: si el cobro en realidad no se hizo.

Para anular hace falta el permiso **Anular**.

## Movimientos de caja

En **Caja**, con la caja abierta:

- **Gasto**: algo que se pagó con plata de la caja (hielo, un proveedor). Elegí la categoría y escribí qué fue.
- **Retiro**: plata que se saca de la caja (por ejemplo, para guardar).
- **Ingreso**: plata que se agrega a la caja (por ejemplo, cambio).

Siempre con el motivo. Un movimiento mal cargado lo anula el encargado.

## Cerrar la caja (al terminar el turno)

1. Cobrá o anulá todas las mesas abiertas: con mesas abiertas no se puede cerrar.
2. En **Caja**, tocá **Cerrar caja**.
3. Contá el efectivo y anotalo en **Contado**. Para cada medio, Galia muestra lo **Esperado** y la **Diferencia**.
4. Confirmá con **Cerrar caja**.

### Si el arqueo no cierra

- Volvé a contar el efectivo.
- Revisá en **Movimientos** que no falte un gasto o un retiro.
- Revisá en las ventas del día que ningún pago esté cargado con el medio equivocado (por ejemplo, efectivo en vez de débito).
- Si sigue la diferencia, cerrá igual y escribí en la nota lo que pasó. El encargado lo revisa en **Cajas**.

## Si Galia falla

1. Si no anda Galia (no carga, no hay internet, se colgó la tablet), cargá las ventas **en Fudo**, como antes.
2. **Nunca cargues la misma venta en los dos sistemas.** Si una venta se empezó en Galia y se terminó en Fudo, anulala en Galia (motivo: "Pasada a Fudo").
3. Avisá al encargado: después Galia trae de Fudo lo que se cargó ahí.

## La franja "PRÁCTICA"

Si arriba aparece la franja amarilla **PRÁCTICA: nada de esto cuenta**, Galia está en modo práctica:

- todo lo que cargues es de prueba: no cuenta en las ventas, la caja ni el stock;
- no se puede facturar ni cobrar con el Point;
- los tickets salen con **PRÁCTICA** arriba.

Con la franja visible **no atiendas clientes reales**: avisá al encargado para que la saque.
