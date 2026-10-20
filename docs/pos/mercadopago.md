# MercadoPago: cobro con el Point y conciliación

## 1. Integración en MercadoPago (una vez, admin)

1. Entrar a **Tus integraciones** en el panel de desarrolladores de MercadoPago con la cuenta del café y crear una aplicación de **Pagos presenciales → Point**.
2. Copiar el **Access token** de prueba y el de producción (sección "Credenciales").
3. En **Webhooks → Configurar notificaciones**:
   - pegar la URL que muestra Galia en Ajustes → MercadoPago (`…/api/v1/mercadopago/webhook`);
   - marcar el evento de **órdenes** ("Order");
   - guardar y **revelar la clave secreta**.

## 2. Configurar en Galia (Sistema → MercadoPago)

1. **Entorno:** empezar en **Prueba**. Pegar el token de prueba y tocar "Guardar token": Galia verifica la cuenta.
2. **Terminal:** "Buscar terminales" y "Usar esta" en el Point Smart. Si no está en **modo PDV**, tocar "Pasar a modo PDV" y **reiniciar el Point**.
3. **Webhook:** pegar la clave secreta y tocar "Guardar clave".
4. **Medio de pago:** en Ajustes del POS → Medios de pago, crear "MercadoPago Point" (tipo Tarjeta, con "Es de MercadoPago" y "Lo factura otro sistema") y elegirlo en el paso 4.
5. **Probar conexión.**
6. Cuando ande en prueba: pasar a **Producción**, cargar el token de producción y volver a probar.

Marcá también "Es de MercadoPago" en los otros medios que entran a la cuenta (QR, transferencias a la cuenta de MercadoPago, links de pago): son los que se concilian.

## 3. Cobrar con el Point

En la caja o en Camarero (con POS o el permiso "Cobrar"):

1. Abrir **Cobrar**, elegir **MercadoPago Point** y el monto. Por defecto es el saldo; se puede cobrar una parte.
2. Tocar **Enviar al Point**: el Point muestra el cobro.
3. El mozo lleva el Point a la mesa y el cliente paga. Galia registra el pago sola y, si cubre el saldo, cierra la venta.

- **Cancelar:** se puede mientras no terminó. Si el cliente ya estaba pagando, queda "Cancelando…" hasta que MercadoPago lo confirma.
- **Si se cierra la pantalla:** la venta muestra "Cobro en Point pendiente" con **Ver** y **Cancelar**.
- **Rechazos:** Galia muestra el motivo y se puede reintentar o cobrar con otro medio.
- **Vencimiento:** un cobro que no se paga en 10 minutos lo vence MercadoPago.
- **Un cobro a la vez:** mientras el Point está cobrando una mesa, no acepta otro cobro.
- Si el Point cobró más que el saldo (porque mientras tanto se cobró de otra forma), Galia registra hasta el saldo y avisa "Cobrado de más": revisalo en Conciliación.

## 4. Anular un pago del Point

Al anular el pago (permiso "Anular") se elige **"Devolver también en MercadoPago"** (devolución total, desde Galia) o **"Solo anular en Galia"**. Si MercadoPago rechaza la devolución o no responde, el pago **no** se anula. La opción aparece solo en pagos que vinieron de un cobro con el Point.

## 5. Conciliación (permiso "Conciliar")

En **Finanzas → Conciliación MP**:

1. Elegir el día y tocar **Traer de MercadoPago** (se puede repetir: no duplica nada).
2. Revisar las tres listas:
   - **Coinciden:** los cobros del Point se cruzan solos.
   - **Solo en MercadoPago:** asociar a un pago sugerido (mismo monto, ±15 minutos), crear el pago en una venta en cobro, o "No es una venta" con nota.
   - **Solo en Galia:** "Marcar revisado" con nota.
3. Cada resolución se puede **deshacer**. Deshacer un pago creado desde la conciliación no lo anula: se anula aparte, desde la venta.

El calendario muestra en verde los días conciliados, en rojo los que tienen diferencias y en gris los que no se trajeron.

## Desarrollo

Con `MP_FAKE=1` y base SQLite, Galia usa un MercadoPago de mentira: el cobro muestra "Simular en el Point: aprobar / rechazar / vencer".

## Pendiente de verificar contra MercadoPago real

- El formato exacto de la firma del webhook (`x-signature`) y si `data.id` llega en la URL o en el cuerpo.
- La llamada que pasa la terminal a modo PDV (`PATCH /terminals/v1/setup`).
- Hay un test opcional: `tests/test_mp_sandbox.py` con `MP_TEST_TOKEN` y `MP_TEST_TERMINAL`.
