# Integración con FUdo API

Este documento describe la integración de Galia con la API de FUdo para sincronizar ventas, gastos y movimientos de caja.

## Configuración

### 1. Obtener Credenciales de FUdo

Para usar la API de FUdo, necesitas obtener las credenciales de acceso:

1. Contacta a soporte@fu.do indicando:
   - Nombre de la cuenta en FUdo
   - Usuario de la cuenta al que quieres dar acceso API

2. Te proporcionarán:
   - `apiKey` (Client ID)
   - `apiSecret` (Client Secret)

### 2. Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```bash
# FUdo API Integration
FUDO_API_BASE_URL=https://api.fu.do/v1alpha1
FUDO_CLIENT_ID=tu_client_id_aqui
FUDO_CLIENT_SECRET=tu_client_secret_aqui
FUDO_WEBHOOK_SECRET=tu_webhook_secret_aqui
FUDO_SYNC_ENABLED=True
```

### 3. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 4. Ejecutar Migraciones

```bash
cd backend
flask db upgrade
```

## Características

### Sincronización de Datos

La integración permite sincronizar:

1. **Ventas (Sales)**
   - Estado de pedidos
   - Información de clientes
   - Totales y medios de pago
   - Mesas y salas
   - Camareros/repartidores

2. **Gastos (Expenses)**
   - Montos y fechas
   - Proveedores
   - Categorías
   - Estados de pago
   - Números de comprobante

3. **Movimientos de Caja (Cash Movements)**
   - Pagos
   - Métodos de pago
   - Cajas registradoras
   - Fechas y montos

### Modelos de Base de Datos

#### FudoSyncLog
Registra el historial de sincronizaciones:
- Tipo de sincronización (sales, expenses, payments)
- Estado (in_progress, completed, failed)
- Registros procesados, creados, actualizados y fallidos
- Mensajes de error
- Timestamps

#### FudoOrder
Relaciona pedidos de FUdo con ventas locales:
- ID del pedido en FUdo
- Referencia a la venta local
- Datos completos del pedido
- Estado y tipo de evento
- Timestamps de sincronización

#### FudoExpense
Relaciona gastos de FUdo con gastos locales:
- ID del gasto en FUdo
- Referencia al gasto local
- Datos completos del gasto
- Timestamps de sincronización

#### FudoCashMovement
Almacena movimientos de caja de FUdo:
- ID del movimiento en FUdo
- Tipo de movimiento
- Monto y método de pago
- Caja registradora
- Fecha del movimiento
- Datos completos del movimiento

## API Endpoints

### Sincronización Manual

#### Sincronizar Todo
```http
POST /api/fudo/sync/all
Authorization: Bearer <token>
Content-Type: application/json

{
  "days_back": 7
}
```

#### Sincronizar Solo Ventas
```http
POST /api/fudo/sync/sales
Authorization: Bearer <token>
Content-Type: application/json

{
  "days_back": 7
}
```

#### Sincronizar Solo Gastos
```http
POST /api/fudo/sync/expenses
Authorization: Bearer <token>
Content-Type: application/json

{
  "days_back": 7
}
```

#### Sincronizar Solo Pagos
```http
POST /api/fudo/sync/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "days_back": 7
}
```

### Consultas

#### Ver Logs de Sincronización
```http
GET /api/fudo/sync/logs?limit=50
Authorization: Bearer <token>
```

#### Probar Conexión
```http
GET /api/fudo/test/connection
Authorization: Bearer <token>
```

#### Ver Estado de Configuración
```http
GET /api/fudo/config/status
Authorization: Bearer <token>
```

### Webhooks

#### Webhook de Pedidos
```http
POST /api/fudo/webhook/order
X-Fudo-Signature: <signature>
Content-Type: application/json

{
  "event": "ORDER-CONFIRMED",
  "order": { ... }
}
```

Eventos soportados:
- `ORDER-CONFIRMED`: Pedido confirmado
- `ORDER-CLOSED`: Pedido cerrado
- `ORDER-REJECTED`: Pedido rechazado
- `ORDER-READY-TO-DELIVER`: Pedido listo para entregar
- `ORDER-DELIVERY-SENT`: Pedido enviado

## Configuración de Webhooks en FUdo

1. Accede a FUdo: Administración > Aplicaciones Externas (beta)
2. Crea una nueva aplicación externa
3. Configura los eventos que deseas recibir
4. Agrega la URL de tu webhook: `https://tu-dominio.com/api/fudo/webhook/order`
5. Guarda el `Client ID` y `Client Secret` en tus variables de entorno

## Uso Programático

### Cliente de API

```python
from app.services.fudo_api_client import FudoAPIClient

client = FudoAPIClient()

# Obtener ventas
sales = client.get_sales(page_size=500, page_number=1)

# Obtener gastos
expenses = client.get_expenses(page_size=500, page_number=1)

# Crear gasto
expense_data = {
    "data": {
        "type": "Expense",
        "attributes": {
            "amount": 100.50,
            "date": "2026-02-17"
        }
    }
}
result = client.create_expense(expense_data)
```

### Servicio de Sincronización

```python
from app.services.fudo_sync_service import FudoSyncService

sync_service = FudoSyncService()

# Sincronizar todo
results = sync_service.sync_all(days_back=7)

# Sincronizar solo ventas
result = sync_service.sync_sales(days_back=7)

# Ver logs
logs = sync_service.get_sync_logs(limit=50)
```

## Mapeo de Datos

### Estados de Venta
- `IN-COURSE` → `En curso`
- `CLOSED` → `Cerrada`
- `CANCELED` → `Cancelada`

### Tipos de Venta
- `EAT-IN` → `Local`
- `DELIVERY` → `Delivery`
- `TAKE-AWAY` → `Para llevar`

### Estados de Pago de Gastos
- Con `paymentDate` → `Pagado`
- Sin `paymentDate` → `Pendiente`

## Seguridad

### Autenticación
- La API usa tokens JWT que expiran cada 24 horas
- Los tokens se renuevan automáticamente cuando es necesario
- Las credenciales se almacenan de forma segura en variables de entorno

### Webhooks
- Los webhooks pueden validarse usando HMAC-SHA256
- Configura `FUDO_WEBHOOK_SECRET` para habilitar la validación
- Las firmas se verifican en el header `X-Fudo-Signature`

## Monitoreo

### Logs de Sincronización
Todos los procesos de sincronización se registran en la tabla `fudo_sync_logs`:
- Estado del proceso
- Cantidad de registros procesados
- Registros creados, actualizados y fallidos
- Mensajes de error detallados
- Timestamps de inicio y finalización

### Logs de Aplicación
Los errores se registran en los logs de Flask:
```python
current_app.logger.error(f"Error syncing sales: {str(e)}")
```

## Troubleshooting

### Error: "FUdo API credentials not configured"
- Verifica que `FUDO_CLIENT_ID` y `FUDO_CLIENT_SECRET` estén configurados en `.env`
- Reinicia la aplicación después de modificar las variables de entorno

### Error: "FUdo sync is not enabled"
- Asegúrate de que `FUDO_SYNC_ENABLED=True` en `.env`

### Error: "Failed to authenticate with FUdo API"
- Verifica que las credenciales sean correctas
- Contacta a soporte@fu.do si las credenciales no funcionan

### Error: "Invalid signature" en webhook
- Verifica que `FUDO_WEBHOOK_SECRET` coincida con el configurado en FUdo
- Asegúrate de que el header `X-Fudo-Signature` se esté enviando correctamente

## Limitaciones

- Paginación máxima: 500 registros por página
- Token de autenticación: válido por 24 horas
- Sincronización manual: requiere autenticación de usuario
- Webhooks: solo para pedidos inyectados vía API

## Referencias

- [Documentación API FUdo](https://dev.fu.do/api/)
- [API de Integraciones](https://dev.fu.do/integrations-api/)
- [Centro de Ayuda FUdo](https://soporte.fu.do/es/articles/11732034-api-de-integraciones-de-pedidos)
