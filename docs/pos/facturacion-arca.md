# Facturación electrónica con ARCA

Galia emite desde la caja la factura que pide un cliente, sobre una venta cobrada. Solo factura lo cobrado con medios que **no** factura otro sistema (en Ajustes del POS → Medios de pago, la columna "Lo factura otro sistema"; viene marcada en todo lo que no es efectivo).

## 1. Punto de venta para Galia

En ARCA ("Administración de puntos de venta y domicilios"), dar de alta un punto de venta nuevo del tipo **"RECE para aplicativo y web services"**. Anotar el número.

## 2. Configurar en Galia (admin)

**Ajustes → Facturación:**

1. **Emisor:** CUIT, razón social, domicilio, ingresos brutos, inicio de actividades y condición (hoy, Monotributo). Cargar el punto de venta del paso 1. Guardar.
2. **Certificado de homologación** (pruebas):
   1. Tocar "Generar pedido de certificado (CSR)". Se descarga `galia-homologacion.csr`.
   2. En ARCA, entrar a **WSASS – Autogestión de certificados de homologación**. Crear un certificado con ese CSR y autorizarlo para el servicio **wsfe**.
   3. Pegar el certificado en Galia y "Guardar certificado".
3. **Probar conexión:** tiene que decir "Conectado. Último comprobante: …".
4. Probar facturas y notas de crédito en homologación (salen con "SIN VALIDEZ FISCAL – PRUEBA").
5. **Producción:**
   1. En la pestaña Producción, generar el CSR.
   2. En ARCA, "Administración de certificados digitales": crear el certificado con ese CSR.
   3. En "Administrador de relaciones de clave fiscal", asociarlo al servicio **"Facturación electrónica"**.
   4. Pegar el certificado en Galia, pasar el entorno a **Producción** y probar la conexión.

La clave privada la genera Galia y queda guardada cifrada. Si alguien cambia `SECRET_KEY` en Render, Galia avisa que no la puede leer, y hay que repetir el paso del certificado. El certificado vence (normalmente a los 2 años): Galia avisa 30 días antes.

**Opcional:** "Identificar al consumidor final desde $" es el monto desde el cual ARCA exige los datos del cliente. Consultar el valor vigente con el contador.

## 3. Facturar

En la caja, en una venta cerrada:
1. Tocar **Facturar** (también aparece al terminar de cobrar).
2. Elegir Consumidor final o Con datos (DNI o CUIT; los clientes se sugieren solos).
3. Tocar **Emitir factura**. Sale impresa en la térmica de caja, con el QR.

Si se factura solo una parte (el resto se cobró con tarjeta o QR), la factura lleva un renglón "Consumo – Venta #N" por ese monto.

- **"No pudimos confirmar con ARCA":** tocar **Verificar** en unos segundos. Galia pregunta a ARCA si la factura quedó hecha y nunca emite dos veces.
- **Anular factura:** emite la nota de crédito; hace falta el permiso "Anular". Mientras la venta tenga factura, no se puede anular la venta ni los pagos que cubre la factura.

**Finanzas → Comprobantes:** lista facturas y notas de crédito, con sus estados, la opción de reimprimir y la de verificar las que quedaron sin confirmar.
