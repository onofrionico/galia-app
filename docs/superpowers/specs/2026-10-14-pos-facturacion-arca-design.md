# Facturación electrónica ARCA (sub-proyecto 4) — diseño

**Estado:** aprobado en conversación el 2026-10-14. Rama `feature/pos-facturacion` (sale de `main` en `7f7c6de`).

## Contexto y objetivo

Galia reemplaza a Fudo como POS (sub-proyectos 0–3 en producción).

**Cómo se factura hoy:**
- El café es **Monotributo** y emite **Factura C**.
- Se factura **cuando el cliente la pide**.
- Los **pagos electrónicos** (tarjeta, QR, transferencia) los factura automáticamente **otro sistema** (MercadoPago o la plataforma de la terminal). Fudo no factura.
- Cuando hace falta facturar algo pagado en efectivo, lo hace el contador después.

**Objetivo:** que la caja emita desde Galia la factura que pide un cliente sobre una venta cobrada, con CAE de ARCA, y que la imprima en la térmica de caja. Galia nunca factura lo que ya factura el otro sistema.

**Criterios de éxito:**
1. Desde una venta cerrada, la caja emite una Factura C con los datos del cliente o como consumidor final, obtiene el CAE y la imprime con el QR de ARCA.
2. Nunca hay dos comprobantes autorizados por la misma venta vigente, ni una factura perdida por un corte de red.
3. "Anular factura" emite la nota de crédito, y mientras haya una factura vigente no se puede anular la venta ni los pagos que cubre.
4. El admin configura todo desde Galia: datos del emisor, punto de venta, certificado y entorno, sin tocar variables de Render.
5. El diseño soporta pasar a Responsable Inscripto (Factura A/B con IVA discriminado) cambiando la configuración.

## Decisiones

| Tema | Decisión |
|---|---|
| Condición fiscal | Hoy Monotributo (Factura C). Se soporta Responsable Inscripto (A/B) por configuración. |
| Alcance | Factura a pedido sobre una venta cerrada. Galia no factura automáticamente. |
| Pagos electrónicos | Cada medio de pago tiene "Lo factura otro sistema". Galia factura solo la suma de los pagos con medios que no lo tienen marcado. |
| Detalle | Ítems si se factura la venta completa; un renglón genérico "Consumo – Venta #N" si se factura una parte. |
| Clientes | Se guardan y se sugieren. Sin consulta al padrón de ARCA. |
| Anulación | "Anular factura" emite la Nota de crédito por el total. Mientras haya una factura vigente, se bloquea anular la venta y los pagos cubiertos. |
| Punto de venta y certificado | Propios de Galia: un punto de venta "RECE – web services" nuevo, y clave y CSR generados por Galia. |
| Permisos | Facturar con POS; la nota de crédito, con POS y "Anular"; la configuración, solo admin. |
| Integración | Cliente propio para WSAA y WSFEv1 (`zeep` + `cryptography`), con homologación y producción. Sin `pyafipws` ni servicios de terceros. |

## Arquitectura

```
Caja (React)                Backend (Flask)                              ARCA
 Facturar ──POST──▶ invoice_service ──▶ arca.wsfe ──(SOAP)──▶ WSFEv1 (CAE)
                      │     ▲                 │
                      │     └─ arca.wsaa ─────┴──(SOAP)──▶ WSAA (token 12 h)
                      ├─▶ invoices / invoice_payments / fiscal_customers
                      └─▶ print_service.add_job('invoice') ──▶ cola ──▶ /pos/impresion (QZ)
```

**Módulos nuevos** en `backend/app/services/fiscal/`:
- `settings.py`: lee y valida la configuración, y cifra y descifra la clave privada.
- `arca/wsaa.py`: arma y firma el TRA, hace `LoginCms` y guarda el token en caché.
- `arca/wsfe.py`: `dummy`, `last_authorized`, `request_cae` y `query`. Errores tipados (`ArcaUnavailable`, `ArcaRejected`).
- `amounts.py`: cálculo puro del monto facturable, del modo de detalle, de los renglones y del neto o IVA.
- `invoice_service.py`: emitir, resolver `pending`, anular con nota de crédito y listar.
- `invoice_documents.py`: documento de impresión y URL del QR.

## Datos

Migración `b4a0_add_fiscal_invoicing`, con `down_revision = 'b3a0_add_print_stations'`.

### `fiscal_settings` (una sola fila, `id = 1`)

- **Emisor:**
  - `cuit` (11 dígitos, se valida el dígito verificador);
  - `business_name`, `address`, `gross_income` (ingresos brutos, texto), `activity_start` (fecha);
  - `iva_condition` (`monotributo` | `responsable_inscripto`).
- **Facturación:**
  - `point_of_sale` (entero de 1 a 99999);
  - `environment` (`homologacion` | `produccion`, por defecto `homologacion`);
  - `cf_id_threshold` (Numeric: monto desde el cual el consumidor final debe identificarse);
  - `default_iva_rate` (Numeric, por defecto 21, solo para A/B).
- **Credenciales** (por entorno, columnas `homo_*` y `prod_*`):
  - `*_private_key` (texto cifrado);
  - `*_csr` (PEM);
  - `*_certificate` (PEM);
  - `*_cert_expires_at`.
- `updated_at`.

**Cifrado de la clave:** Fernet con una clave derivada de `SECRET_KEY` con HKDF-SHA256 (`info = b'galia-fiscal-key'`). Si no se puede descifrar, por ejemplo porque rotó `SECRET_KEY`, el estado de la configuración es "La clave del certificado no se puede leer: generá un certificado nuevo".

### `arca_tokens`

- `service` (`wsfe`), `environment`, `token`, `sign`, `expires_at`.
- Índice único en (`service`, `environment`).
- Se renueva cuando faltan menos de 10 minutos para el vencimiento.

### `payment_methods.invoiced_externally`

- Boolean, no nulo.
- La migración lo pone en `true` para todo medio con `kind <> 'cash'` y en `false` para efectivo.
- Al crear un medio nuevo: `true` salvo si es `cash`.
- Se edita en Ajustes del POS → Medios de pago.

### `fiscal_customers`

- **Documento:** `doc_type` (`DNI` | `CUIT` | `CUIL`) y `doc_number` (solo dígitos), con índice único en (`doc_type`, `doc_number`).
- `name` (hasta 120).
- `iva_condition` (`consumidor_final` | `monotributo` | `responsable_inscripto` | `exento`).
- `address` (opcional).
- `created_at`, `updated_at`.

### `invoices`

- **Identidad:**
  - `kind` (`invoice` | `credit_note`);
  - `voucher_type` (código ARCA: 11, 13; a futuro 1, 3, 6, 8);
  - `environment`, `point_of_sale`, `number`;
  - `sale_id` (FK), `related_invoice_id` (FK, la factura que anula una nota de crédito).
- **Receptor (copia fija):**
  - `customer_id` (FK, opcional);
  - `receiver_doc_type` (código ARCA: 80, 86, 96, 99), `receiver_doc_number`;
  - `receiver_name`, `receiver_iva_condition`, `receiver_address`.
- **Contenido (copia fija):**
  - `detail_mode` (`items` | `generic`);
  - `lines` (JSON: `[{qty, description, unit_price, amount}]`);
  - `total`, `net`, `iva`, `iva_rate` (Numeric; en C, `net = total` y `iva = 0`);
  - `voucher_date` (fecha Argentina).
- **Resultado:**
  - `status` (`pending` | `authorized` | `rejected`);
  - `cae`, `cae_due`;
  - `arca_result` (JSON: observaciones y errores);
  - `request` (JSON: el pedido completo enviado a ARCA);
  - `error` (texto para la caja).
- **Auditoría:** `created_by`, `created_at`, `authorized_at`.
- **Índices:**
  - único parcial en (`environment`, `point_of_sale`, `voucher_type`, `number`) donde `status = 'authorized'`;
  - índice en `sale_id`.

### `invoice_payments`

- `invoice_id`, `payment_id`, `amount`.
- Qué pagos cubre cada factura.

**Factura vigente:** una factura `authorized` sin ninguna nota de crédito `authorized` que la referencie. Una venta tiene como máximo una factura vigente.

## Reglas de negocio

### Monto facturable y detalle (`amounts.py`, puro)

- Solo ventas `closed`.
- **Pagos facturables:** los pagos activos de la venta cuyo medio no tiene `invoiced_externally`. **Monto facturable:** la suma de sus `amount` (el vuelto no cuenta: `amount` ya es lo aplicado).
- Si el monto facturable es 0, la venta no se puede facturar: "Todo lo cobrado en esta venta lo factura otro sistema".
- **Detalle:**
  - Si el monto facturable es igual a `sale.total`, el modo es `items`. Van los ítems confirmados: cantidad, descripción (producto y variante si hay varias, con modificadores) y precio unitario efectivo. Los descuentos se reflejan en el precio de cada línea, prorrateando los descuentos de la venta. La suma de las líneas tiene que dar exactamente el total; el redondeo se absorbe en la última línea.
  - Si es menor, el modo es `generic`: una línea "Consumo – Venta #N" por el monto facturable.
- **A/B (Responsable Inscripto):** `net = round(total / (1 + rate/100), 2)` e `iva = total − net`, con `default_iva_rate`. En C: `net = total`, `iva = 0`.

### Tipo de comprobante

| Emisor | Receptor | Factura | Nota de crédito |
|---|---|---|---|
| Monotributo | cualquiera | C (11) | C (13) |
| Responsable Inscripto | responsable inscripto o monotributo (RG 5003) | A (1) | A (3) |
| Responsable Inscripto | consumidor final o exento | B (6) | B (8) |

La nota de crédito sigue siempre el tipo de la factura que anula (11→13, 1→3, 6→8) y copia su neto, IVA y alícuota, aunque después haya cambiado la configuración.

### Receptor

- **Consumidor final sin datos:** documento 99, número 0, condición 5. Solo si `total < cf_id_threshold`; si no, "Para facturas desde $X hay que identificar al cliente".
- **Documentos:** DNI 96, CUIT 80, CUIL 86. El CUIT y el CUIL validan el dígito verificador; el DNI, entre 7 y 8 dígitos.
- **Condición frente al IVA (`CondicionIVAReceptorId`):** consumidor final 5, monotributo 6, responsable inscripto 1, exento 4.
- **Validaciones:** responsable inscripto o monotributo exigen CUIT. En Factura A, el receptor tiene que ser responsable inscripto con CUIT.
- **Guardado:** al emitir con datos, se crea o actualiza el `fiscal_customer` por (tipo, número), con el nombre, la condición y el domicilio.

### Emisión en dos fases (`invoice_service.issue`)

1. **Reservar (transacción 1):**
   - `SELECT … FOR UPDATE` de `fiscal_settings`, que serializa las emisiones.
   - Valida la configuración: emisor, punto de venta y certificado vigente del entorno activo.
   - Valida la venta (`closed`, sin factura vigente) y el receptor.
   - Si hay un `pending` del mismo entorno, punto de venta y tipo:
     - con menos de 120 s: 409 "Hay una factura emitiéndose, probá en unos segundos";
     - si no, lo **resuelve** primero.
   - `number = wsfe.last_authorized(pos, type) + 1`.
   - Inserta la factura `pending` con el pedido completo y sus `invoice_payments`, y confirma.
2. **Pedir el CAE (fuera de la transacción):** `wsfe.request_cae(request)`, con timeout de 30 s.
   - Resultado `A`: `authorized` con `cae`, `cae_due`, `authorized_at` y las observaciones.
   - Resultado `R`: `rejected` con los errores y `error` legible. El número no quedó usado.
   - Excepción de red o timeout: queda `pending`. La respuesta HTTP es 202 con `status = pending` y "No pudimos confirmar con ARCA. Tocá Verificar en unos segundos".
3. Si queda `authorized`, encola la impresión (`print_service.add_job('invoice', cashier_printer, …)`). Sin impresora de caja, el comprobante igual queda emitido, con el aviso "No hay impresora de caja configurada".

### Resolver un `pending` (`invoice_service.resolve`)

- `wsfe.query(type, pos, number)`.
  - Si existe: compara importe total y documento del receptor con el pedido guardado. Si coinciden, `authorized` con el CAE devuelto. Si no coinciden, `rejected` con "ARCA tiene otro comprobante con ese número". Ese caso se registra en el log y aparece en Comprobantes para revisarlo.
  - Si no existe y el pedido tiene menos de 120 s: sigue `pending` ("Todavía no aparece en ARCA: probá Verificar de nuevo en un minuto"), porque ARCA puede seguir procesándolo después de nuestro timeout.
  - Si no existe y pasaron 120 s: `rejected` con "No llegó a ARCA".
  - Solo se verifica en el entorno del comprobante: si el entorno activo es otro, se responde un error en lugar de consultar.
- Se dispara con "Verificar" (`POST /fiscal/invoices/<id>/verify`) o automáticamente en la fase 1 de la siguiente emisión, si el `pending` tiene más de 120 s.

### Nota de crédito (`invoice_service.cancel`)

- **Requisitos:** POS y "Anular". La factura tiene que estar vigente.
- **Mismo flujo de dos fases:**
  - tipo según la tabla;
  - mismos receptor, líneas e importes;
  - `CbtesAsoc` con tipo, punto de venta, número, CUIT emisor y fecha de la factura;
  - `related_invoice_id` apuntando a la factura;
  - sus `invoice_payments` son los de la factura.
- Una vez `authorized`, la factura deja de estar vigente, la venta se puede volver a facturar y se imprime la nota de crédito.

### Bloqueos

- `sale_service.cancel_sale` y `payment_service.cancel_payment` consultan `invoice_service.active_invoice_for_sale` y los pagos cubiertos.
- Si la venta tiene una factura vigente, o un `pending`:
  - anular la venta: 409 "La venta tiene la Factura C 0005-00000123: anulala con una nota de crédito antes";
  - anular un pago cubierto: el mismo mensaje.
- Los pagos no cubiertos se anulan como siempre.
- Con un `pending`, el mensaje es "Hay una factura sin confirmar en esta venta: verificala antes".

## Cliente de ARCA

### WSAA (`arca/wsaa.py`)

- **TRA:** XML `loginTicketRequest` versión 1.0 con:
  - `uniqueId` = epoch;
  - `generationTime` = ahora − 10 min y `expirationTime` = ahora + 10 min, ISO con zona −03:00;
  - `service = wsfe`.
- **Firma:** CMS/PKCS#7 *con contenido* (no detached), SHA-256, con el certificado, en base64. Se usa `cryptography.hazmat.primitives.serialization.pkcs7.PKCS7SignatureBuilder`.
- **Llamada:** `LoginCms(in0=cms)`. Se parsean `token`, `sign` y `expirationTime`, y se guardan en `arca_tokens`.
- **Error "ya posee un TA válido" sin token guardado:** "ARCA ya entregó un acceso a este certificado que Galia no tiene guardado; esperá hasta HH:MM o generá otro certificado". Para que esto no pase, el token se guarda en su propia transacción apenas `LoginCms` responde, antes de usarlo.
- **Endpoints:**
  - homologación: `https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl`;
  - producción: `https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl`.

### WSFEv1 (`arca/wsfe.py`)

- **Endpoints:**
  - homologación: `https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL`;
  - producción: `https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL`.
- **Autenticación:** todas las llamadas llevan `Auth {Token, Sign, Cuit}`.
- **Operaciones:**
  - `dummy()`: `FEDummy`, estado de AppServer, DbServer y AuthServer;
  - `last_authorized(pos, type)`: `FECompUltimoAutorizado`;
  - `request_cae(req)`: `FECAESolicitar` con un `FECAEDetRequest`:
    - `Concepto = 1`, `DocTipo`, `DocNro`, `CbteDesde = CbteHasta = number`, `CbteFch` (aaaammdd);
    - importes: `ImpTotal`, `ImpTotConc = 0`, `ImpNeto`, `ImpOpEx = 0`, `ImpIVA`, `ImpTrib = 0`;
    - `MonId = 'PES'`, `MonCotiz = 1`, `CondicionIVAReceptorId`;
    - `Iva` (solo A/B, `AlicIva` con `Id = 5` para 21% o `4` para 10,5%) y `CbtesAsoc` (notas de crédito);
  - `query(type, pos, number)`: `FECompConsultar`.
- **Errores:** las respuestas con `Errors` se convierten en `ArcaRejected(errors)`, y la red, el timeout o el SOAP Fault en `ArcaUnavailable`. Los timeouts son de 10 s para la conexión y de 30 s para la respuesta.
- **WSDL:** se descarga en el primer uso de cada proceso y se guarda en memoria (caché de `zeep`). La dependencia nueva es `zeep==4.2.1`.

## Impresión

- `PRINT_JOB_KINDS` suma `invoice`, que sirve tanto para factura como para nota de crédito. El documento va a la impresora de caja.
- **Documento de factura** (`invoice_documents.invoice_document`):
  - `title`: "FACTURA C" o "NOTA DE CRÉDITO C";
  - `header`: razón social, `CUIT`, `IIBB`, inicio de actividades, domicilio, condición frente al IVA, "Cód. 011", "P.V. 00005 Nº 00000123", fecha, y el receptor (nombre, documento, condición y domicilio);
  - `lines` con importe;
  - `totals`: en C solo "TOTAL"; en A/B, "Neto", "IVA 21%" y "TOTAL";
  - `footer`: "CAE 7…", "Vto. CAE dd/mm/aaaa" y, en homologación, "SIN VALIDEZ FISCAL – PRUEBA";
  - campo nuevo `qr`: la URL del QR.
- **QR de ARCA:** `https://www.afip.gob.ar/fe/qr/?p=<base64(JSON)>`, con el JSON `{ver:1, fecha:'aaaa-mm-dd', cuit, ptoVta, tipoCmp, nroCmp, importe, moneda:'PES', ctz:1, tipoDocRec, nroDocRec, tipoCodAut:'E', codAut}`.
- **Frontend** (`escpos.js`): si el documento trae `qr`, después del pie se imprime el código QR con la secuencia ESC/POS `GS ( k` (modelo 2, tamaño de módulo 6, corrección M, almacenar e imprimir). `renderText` (simulación) muestra la URL.

## API (prefijo `/api/v1`)

| Método y ruta | Permiso | Qué hace |
|---|---|---|
| `GET /fiscal/sales/<id>/preview` | POS | Monto facturable, modo, líneas, tipo de comprobante, si exige identificación y factura vigente si hay |
| `POST /fiscal/sales/<id>/invoice` `{customer?: {doc_type, doc_number, name, iva_condition, address}}` | POS | Emite. 201 `authorized`, 202 `pending`, 409 o 400 con mensaje |
| `POST /fiscal/invoices/<id>/verify` | POS | Resuelve un `pending` |
| `POST /fiscal/invoices/<id>/cancel` | POS + Anular | Nota de crédito |
| `POST /fiscal/invoices/<id>/reprint` | POS | Encola la impresión de nuevo |
| `GET /fiscal/invoices?from&to&kind&status&page` | POS | Listado paginado |
| `GET /fiscal/invoices/<id>` | POS | Detalle |
| `GET /fiscal/sales/<id>/invoices` | POS | Comprobantes de la venta |
| `GET /fiscal/customers?q=` | POS | Sugerencias, por documento o nombre (máximo 10) |
| `GET /fiscal/settings` | admin | Configuración sin secretos: si tiene clave, CSR y certificado por entorno, vencimiento y estado |
| `PUT /fiscal/settings` | admin | Datos del emisor, punto de venta, entorno, umbral y alícuota |
| `POST /fiscal/settings/<env>/csr` | admin | Genera clave RSA 2048 y CSR (`CN=galia`, `O=<razón social>`, `serialNumber=CUIT <cuit>`) y devuelve el CSR |
| `PUT /fiscal/settings/<env>/certificate` `{certificate}` | admin | Valida el PEM, que coincida con la clave y que no esté vencido. Guarda el vencimiento |
| `POST /fiscal/settings/test` | admin | `dummy` + WSAA + `last_authorized`. Devuelve el último número o un error legible |

La venta (`sale_to_dict`) suma `invoice: {id, label, status} | null` con la factura vigente o el `pending`, para la etiqueta en la caja.

## Interfaz

### Ajustes → Facturación (admin, `/admin/fiscal`)

Pasos en tarjetas, cada una con su estado: completo, falta o con error.

1. **Emisor:** CUIT, razón social, domicilio, IIBB, inicio de actividades y condición.
2. **Punto de venta:** el número, con la ayuda "Dalo de alta en ARCA como 'RECE – Web services'".
3. **Certificado** (pestañas Homologación y Producción):
   - **Generar pedido (CSR):** lo descarga como `galia-<env>.csr`, con instrucciones para subirlo en ARCA (WSASS en homologación, "Administración de certificados digitales" en producción) y asociarlo al servicio "Facturación electrónica".
   - **Pegar certificado:** un textarea, más "Guardar". Muestra el vencimiento.
4. **Entorno:** homologación o producción. Cambiar a producción pide confirmación: "Las facturas van a tener validez fiscal".
5. **Probar conexión:** muestra "Conectado. Último comprobante: C 00005-00000041" o el error.
6. **Avanzado:** umbral de identificación del consumidor final y alícuota de IVA.

Un cartel muestra si el certificado del entorno activo vence en menos de 30 días.

### Caja

- **Pie de la venta cerrada:** botón **Facturar** junto a "Imprimir ticket", cuando no hay factura vigente. También aparece en el cartel de "Venta cerrada" del cobro.
  - Si la configuración no está completa, el botón queda deshabilitado con el motivo en el tooltip: "Falta configurar la facturación".
  - Si la venta tiene factura, se muestra una etiqueta ("Factura C 0005-00000123") con **Reimprimir** y **Anular factura** (requiere "Anular"). Si está `pending`, "Factura sin confirmar" con **Verificar**.
- **Modal Facturar:**
  - resumen del preview: "Se facturan los ítems · $ 18.000", o "Se factura $ 10.000 de $ 18.000 (lo demás lo factura otro sistema)";
  - selector **Consumidor final** / **Con datos**. Con datos: tipo de documento, número (con sugerencias de `fiscal_customers` mientras se escribe), nombre, condición frente al IVA y domicilio;
  - **Emitir factura**.
  - **Resultado:**
    - `authorized`: "Factura C 0005-00000123 · CAE …" y se imprime;
    - `pending`: aviso amarillo con "Verificar";
    - `rejected` o error: el mensaje, sin cerrar el modal, para corregir y reintentar.
- **Homologación:** el modal y la etiqueta muestran "PRUEBA".

### Finanzas → Comprobantes (`/fiscal/invoices`, POS)

- **Tabla:** fecha, tipo y número, receptor, total, estado y venta.
- **Filtros:** rango de fechas, tipo (facturas o notas de crédito) y estado.
- **Acciones por fila:**
  - ver el detalle (con el pedido y la respuesta de ARCA, plegados);
  - reimprimir;
  - verificar (si está `pending`);
  - ir a la venta.
- Arriba se ve el entorno activo.

### Ajustes del POS → Medios de pago

Columna nueva **"Lo factura otro sistema"** (checkbox).

## Errores (mensajes para la caja)

| Situación | Mensaje |
|---|---|
| Configuración incompleta | "Falta configurar la facturación: <qué falta>" |
| Certificado vencido | "El certificado de ARCA venció el dd/mm/aaaa: generá uno nuevo en Ajustes → Facturación" |
| ARCA no responde | "ARCA no responde, probá en unos minutos" |
| Rechazo de ARCA | "ARCA rechazó la factura: <texto de ARCA>" |
| Sin monto facturable | "Todo lo cobrado en esta venta lo factura otro sistema" |
| Consumidor final sobre el umbral | "Para facturas desde $X hay que identificar al cliente" |
| Venta no cerrada | "Solo se factura una venta cerrada" |
| Ya facturada | "La venta ya tiene la Factura C 0005-00000123" |

El detalle técnico (SOAP, códigos, trazas) va al log y a `arca_result`; nunca a la caja.

## Pruebas

- **Unitarias (sin red):**
  - `amounts`: venta completa contra parcial, descuentos prorrateados con redondeo exacto, pagos anulados, todo externo, y A/B neto e IVA;
  - tipo de comprobante y receptor: matriz de condiciones, dígito verificador de CUIT y CUIL, y umbral del consumidor final;
  - armado del `FECAEDetRequest`, para factura C y para nota de crédito con `CbtesAsoc`;
  - WSAA: el TRA y la firma CMS, que se verifica con el certificado de prueba y contiene el TRA;
  - cifrado y descifrado de la clave, y la falla con otro `SECRET_KEY`;
  - CSR y validación del certificado: que coincida con la clave y no esté vencido;
  - URL del QR y documento de impresión;
  - `escpos`: secuencia del QR y texto en simulación.
- **Flujo con ARCA falso** (`FakeArca` inyectado en lugar de `wsfe` y `wsaa`):
  - aprobado: imprime y guarda el cliente;
  - rechazado: el número queda libre;
  - timeout que deja `pending` y se resuelve después, encontrado y no encontrado;
  - `pending` reciente: 409;
  - `pending` viejo que se resuelve antes de emitir;
  - nota de crédito y nueva facturación;
  - bloqueos de anulación de venta y de pago;
  - permisos;
  - token WSAA guardado y reutilizado.
- **PostgreSQL** (con `POS_PG_TEST_URL`): dos emisiones simultáneas sobre ventas distintas; una espera a la otra y los números quedan consecutivos sin duplicados.
- **Homologación real (opcional):** un test marcado que corre solo con `ARCA_HOMO_CUIT`, `ARCA_HOMO_CERT`, `ARCA_HOMO_KEY` y `ARCA_HOMO_POS`. Emite una factura C y su nota de crédito.
- **Frontend (Vitest):** el resumen del modal a partir del preview, la validación del documento en el cliente y el QR ESC/POS.
- **Verificación manual:** preview SQLite con `FakeArca` y la página de impresión en simulación. `FakeArca` se activa con la variable `FISCAL_FAKE_ARCA=1` y **solo si la base es SQLite**: con PostgreSQL (producción) se ignora siempre. Después, homologación real con el certificado del cliente.

## Fuera de alcance

- Facturar automáticamente los pagos electrónicos.
- La consulta al padrón de ARCA.
- Notas de crédito parciales.
- Facturar desde el celular (Camarero).
- Monedas extranjeras, conceptos de servicios y tributos (percepciones).
- Libro IVA y exportaciones para el contador, más allá del listado.
- Migrar el histórico de Fudo.
- Alícuotas de IVA por producto: en A/B se usa una alícuota única configurable.
