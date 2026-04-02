# Especificación: Email Invoice to Payments (Versión Simplificada)

**Fecha**: 26 de Marzo, 2026  
**Versión**: 1.0 - Simplified  
**Estado**: Draft

---

## 1. Resumen Ejecutivo

Sistema simplificado de procesamiento automático de facturas desde email usando etiquetas de Gmail. El sistema procesa emails con la etiqueta "Facturas pendientes", extrae datos de los PDFs adjuntos, crea gastos automáticamente, y cambia la etiqueta según el resultado del procesamiento.

### Objetivo Principal
Automatizar la carga de facturas desde email con un flujo simple basado en etiquetas de Gmail, sin necesidad de revisión manual compleja.

### Alcance
- Procesamiento automático de emails con etiqueta específica
- Extracción de datos de PDFs de facturas argentinas (AFIP)
- Creación automática de gastos en el sistema
- Gestión de etiquetas según resultado del procesamiento
- Trigger manual para iniciar el procesamiento

---

## 2. User Stories

### Historia Principal
**Como** administrador del sistema  
**Quiero** que las facturas que llegan por email se procesen automáticamente  
**Para** no tener que cargar manualmente cada factura en el sistema

### Criterios de Aceptación
- ✅ Los emails con etiqueta "Facturas pendientes" se procesan automáticamente
- ✅ Los PDFs adjuntos se extraen y se parsean los datos
- ✅ Se crea un gasto automáticamente con los datos extraídos
- ✅ Los emails procesados exitosamente cambian a etiqueta "Factura procesada"
- ✅ Los emails con error mantienen la etiqueta "Facturas pendientes"
- ✅ Existe un trigger manual para iniciar el procesamiento

---

## 3. Flujo del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO SIMPLIFICADO                        │
└─────────────────────────────────────────────────────────────┘

1. Email llega a Gmail
   └─> Usuario aplica etiqueta "Facturas pendientes" manualmente
       o mediante filtro automático

2. Admin hace clic en "Procesar Facturas" (trigger manual)
   └─> Sistema busca emails con etiqueta "Facturas pendientes"

3. Para cada email encontrado:
   
   ┌─> Extrae PDF adjunto
   │
   ├─> Extrae datos del PDF (CUIT, monto, fecha, etc.)
   │
   ├─> Verifica si es duplicado (por número de comprobante + CUIT)
   │
   └─> Resultado:
       │
       ├─> ✅ ÉXITO:
       │   - Crea gasto en estado "Pendiente"
       │   - Cambia etiqueta a "Factura procesada"
       │   - Guarda PDF en almacenamiento
       │
       └─> ❌ ERROR:
           - Mantiene etiqueta "Facturas pendientes"
           - Registra error en log
           - No crea gasto

4. Admin revisa gastos creados en la sección normal de Gastos
```

---

## 4. Etiquetas de Gmail

### Etiquetas Requeridas

| Etiqueta | Propósito | Quién la aplica |
|----------|-----------|-----------------|
| **Facturas pendientes** | Marca emails listos para procesar | Usuario o filtro automático |
| **Factura procesada** | Marca emails procesados exitosamente | Sistema automático |

### Configuración de Filtros en Gmail (Opcional)

El usuario puede configurar filtros automáticos en Gmail:

```
De: proveedor@ejemplo.com
Tiene adjunto: ✓
Aplicar etiqueta: "Facturas pendientes"
```

---

## 5. Modelo de Datos

### 5.1 Tabla: `email_invoices`

Registro de emails procesados.

```sql
CREATE TABLE email_invoices (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255) NOT NULL UNIQUE,  -- Gmail message ID
    subject VARCHAR(500),
    sender VARCHAR(255),
    received_date TIMESTAMP,
    processing_status VARCHAR(50),  -- 'success', 'error', 'duplicate'
    processed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Estados de procesamiento:**
- `success`: Procesado exitosamente, gasto creado
- `error`: Error en procesamiento, no se creó gasto
- `duplicate`: Factura duplicada detectada

### 5.2 Tabla: `invoice_attachments`

PDFs almacenados.

```sql
CREATE TABLE invoice_attachments (
    id SERIAL PRIMARY KEY,
    email_invoice_id INTEGER REFERENCES email_invoices(id),
    filename VARCHAR(255),
    file_path TEXT,
    file_size INTEGER,
    file_hash VARCHAR(64),  -- MD5 para detectar duplicados
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 Extensión de Tabla: `expenses`

Campos adicionales para identificar gastos automáticos.

```sql
ALTER TABLE expenses ADD COLUMN source VARCHAR(20) DEFAULT 'manual';
ALTER TABLE expenses ADD COLUMN invoice_attachment_id INTEGER REFERENCES invoice_attachments(id);
```

**Valores de `source`:**
- `manual`: Gasto creado manualmente
- `email_auto`: Gasto creado automáticamente desde email

---

## 6. Datos Extraídos de PDFs

### Campos a Extraer (Facturas AFIP Argentina)

| Campo | Descripción | Regex Pattern | Obligatorio |
|-------|-------------|---------------|-------------|
| **CUIT** | CUIT del proveedor | `\d{2}-\d{8}-\d{1}` | ✅ |
| **Proveedor** | Razón social | Texto antes de CUIT | ❌ |
| **Tipo Comprobante** | Factura A/B/C | `FACTURA [ABC]` | ✅ |
| **Número Comprobante** | Número de factura | `\d{4}-\d{8}` | ✅ |
| **Fecha Emisión** | Fecha de la factura | `\d{2}/\d{2}/\d{4}` | ✅ |
| **Importe Total** | Monto total | `\$?\s*[\d,.]+` | ✅ |
| **CAE** | Código de autorización | `\d{14}` | ❌ |

### Confidence Score

El sistema calcula un score de confianza (0-100%) basado en:
- Campos obligatorios encontrados: 60%
- Campos opcionales encontrados: 20%
- Formato válido de campos: 20%

**Criterio de procesamiento:**
- Score ≥ 50%: Se crea el gasto
- Score < 50%: Se marca como error

---

## 7. Detección de Duplicados

### Nivel 1: Archivo Duplicado
- Se calcula hash MD5 del PDF
- Si existe un archivo con el mismo hash: **SKIP** (no procesar)

### Nivel 2: Factura Duplicada
- Se busca en `expenses` por:
  - `numero_comprobante` = extraído del PDF
  - `numero_fiscal` (CUIT) = extraído del PDF
  - `cancelado` = false
- Si existe: **DUPLICATE** (no crear gasto, marcar como duplicado)

---

## 8. API Endpoints

### 8.1 Configuración de Email

```http
POST /api/v1/email-invoices/config
```

**Request Body:**
```json
{
  "email_address": "tu-email@gmail.com",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "username": "tu-email@gmail.com",
  "password": "app-password",
  "use_ssl": true
}
```

**Response:**
```json
{
  "id": 1,
  "email_address": "tu-email@gmail.com",
  "is_active": true,
  "created_at": "2026-03-26T17:00:00Z"
}
```

### 8.2 Trigger Manual de Procesamiento

```http
POST /api/v1/email-invoices/process
```

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "task_id": "abc123-def456",
  "status": "processing",
  "message": "Procesamiento iniciado"
}
```

### 8.3 Estado del Procesamiento

```http
GET /api/v1/email-invoices/status/{task_id}
```

**Response:**
```json
{
  "task_id": "abc123-def456",
  "status": "completed",
  "emails_found": 5,
  "emails_processed": 4,
  "emails_error": 1,
  "expenses_created": 4,
  "results": [
    {
      "email_id": "msg123",
      "subject": "Factura 001-00001234",
      "status": "success",
      "expense_id": 456
    },
    {
      "email_id": "msg124",
      "subject": "Factura 001-00001235",
      "status": "error",
      "error": "Confidence score too low (35%)"
    }
  ]
}
```

### 8.4 Historial de Procesamiento

```http
GET /api/v1/email-invoices/history
```

**Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "email_id": "msg123",
      "subject": "Factura 001-00001234",
      "sender": "proveedor@ejemplo.com",
      "processing_status": "success",
      "processed_at": "2026-03-26T17:05:00Z",
      "expense_id": 456
    }
  ]
}
```

---

## 9. Componentes Técnicos

### 9.1 Backend Services

```
backend/app/services/
├── email_service.py           # Conexión IMAP, gestión de etiquetas
├── pdf_extraction_service.py  # Extracción de datos de PDFs
└── invoice_processor.py       # Lógica de procesamiento principal
```

### 9.2 Celery Tasks

```python
# backend/app/tasks/invoice_tasks.py

@shared_task
def process_pending_invoices():
    """
    Procesa emails con etiqueta 'Facturas pendientes'
    """
    # 1. Conectar a Gmail
    # 2. Buscar emails con etiqueta "Facturas pendientes"
    # 3. Para cada email:
    #    - Extraer PDF
    #    - Parsear datos
    #    - Crear gasto
    #    - Cambiar etiqueta según resultado
    # 4. Retornar resumen
```

### 9.3 Frontend (Opcional - Mínimo)

Solo se necesita:
- Botón "Procesar Facturas" en alguna sección admin
- Mensaje de confirmación con resultados

---

## 10. Flujo de Procesamiento Detallado

```
┌─────────────────────────────────────────────────────────────┐
│              PROCESO DE PROCESAMIENTO                        │
└─────────────────────────────────────────────────────────────┘

1. TRIGGER
   └─> Admin hace clic en "Procesar Facturas"
       └─> POST /api/v1/email-invoices/process
           └─> Celery task: process_pending_invoices()

2. CONEXIÓN A GMAIL
   └─> Conectar vía IMAP con credenciales guardadas
       └─> Buscar emails con etiqueta "Facturas pendientes"

3. PARA CADA EMAIL:

   A. EXTRACCIÓN
      ├─> Obtener adjuntos PDF
      ├─> Calcular hash MD5
      └─> Verificar si hash existe en BD
          ├─> SÍ: SKIP (archivo duplicado)
          └─> NO: Continuar

   B. PARSING
      ├─> Extraer texto del PDF (pdfplumber)
      ├─> Aplicar regex patterns
      ├─> Calcular confidence score
      └─> Validar score ≥ 50%
          ├─> SÍ: Continuar
          └─> NO: ERROR (confidence bajo)

   C. VALIDACIÓN DE DUPLICADOS
      └─> Buscar en expenses:
          numero_comprobante + numero_fiscal
          ├─> EXISTE: DUPLICATE
          └─> NO EXISTE: Continuar

   D. CREACIÓN DE GASTO
      ├─> Guardar PDF en storage
      ├─> Crear registro en invoice_attachments
      ├─> Crear registro en expenses:
          │   - fecha = fecha_emision
          │   - proveedor = extraído
          │   - numero_fiscal = CUIT
          │   - tipo_comprobante = tipo
          │   - numero_comprobante = número
          │   - importe = importe_total
          │   - estado_pago = "Pendiente"
          │   - source = "email_auto"
          │   - invoice_attachment_id = ID del PDF
      └─> Crear registro en email_invoices

   E. GESTIÓN DE ETIQUETAS
      ├─> ÉXITO:
      │   ├─> Remover etiqueta "Facturas pendientes"
      │   └─> Agregar etiqueta "Factura procesada"
      │
      └─> ERROR/DUPLICATE:
          └─> Mantener etiqueta "Facturas pendientes"

4. RESUMEN
   └─> Retornar:
       - Total emails encontrados
       - Emails procesados exitosamente
       - Emails con error
       - Gastos creados
       - Detalles de cada email
```

---

## 11. Configuración Inicial

### 11.1 Variables de Entorno

```bash
# .env
EMAIL_ENCRYPTION_KEY=<generar-con-fernet>
INVOICE_STORAGE_PATH=invoice_attachments
```

### 11.2 Generar Clave de Encriptación

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 11.3 Configurar Gmail

1. Habilitar IMAP en Gmail
2. Crear App Password:
   - https://myaccount.google.com/apppasswords
   - Seleccionar "Correo" → "Otro"
   - Copiar contraseña de 16 caracteres

3. Crear etiquetas en Gmail:
   - "Facturas pendientes"
   - "Factura procesada"

### 11.4 Configurar en la Aplicación

```bash
POST /api/v1/email-invoices/config
{
  "email_address": "tu-email@gmail.com",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "username": "tu-email@gmail.com",
  "password": "xxxx xxxx xxxx xxxx",
  "use_ssl": true
}
```

---

## 12. Uso del Sistema

### Flujo de Trabajo Diario

1. **Recepción de Facturas**
   - Las facturas llegan por email
   - Usuario o filtro automático aplica etiqueta "Facturas pendientes"

2. **Procesamiento**
   - Admin entra a la aplicación
   - Va a sección "Gastos" o "Email Invoices"
   - Hace clic en botón "Procesar Facturas Pendientes"
   - Sistema muestra progreso y resultados

3. **Revisión de Gastos Creados**
   - Admin va a sección "Gastos"
   - Filtra por `source = 'email_auto'` (opcional)
   - Revisa gastos creados
   - Edita si es necesario
   - Marca como pagado cuando corresponda

4. **Manejo de Errores**
   - Emails que no se procesaron mantienen etiqueta "Facturas pendientes"
   - Admin puede revisar el log de errores
   - Puede corregir manualmente o volver a intentar

---

## 13. Casos de Uso

### Caso 1: Procesamiento Exitoso

```
Email: "Factura A 0001-00001234"
Adjunto: factura.pdf
Etiqueta actual: "Facturas pendientes"

PROCESAMIENTO:
1. Extrae PDF ✓
2. Parsea datos ✓
   - CUIT: 20-12345678-9
   - Monto: $15,000
   - Fecha: 25/03/2026
   - Número: 0001-00001234
3. Confidence: 85% ✓
4. No es duplicado ✓
5. Crea gasto ID: 789 ✓

RESULTADO:
- Gasto creado: ID 789
- Etiqueta cambiada a: "Factura procesada"
- Estado: success
```

### Caso 2: Error por Confidence Bajo

```
Email: "Factura escaneada"
Adjunto: factura_escaneada.pdf (imagen)
Etiqueta actual: "Facturas pendientes"

PROCESAMIENTO:
1. Extrae PDF ✓
2. Parsea datos ⚠️
   - CUIT: No encontrado
   - Monto: No encontrado
   - Fecha: 25/03/2026
3. Confidence: 25% ✗

RESULTADO:
- Gasto NO creado
- Etiqueta: "Facturas pendientes" (sin cambios)
- Estado: error
- Error: "Confidence score too low (25%)"
```

### Caso 3: Factura Duplicada

```
Email: "Factura A 0001-00001234"
Adjunto: factura.pdf
Etiqueta actual: "Facturas pendientes"

PROCESAMIENTO:
1. Extrae PDF ✓
2. Parsea datos ✓
3. Confidence: 85% ✓
4. Verifica duplicados:
   - Número: 0001-00001234
   - CUIT: 20-12345678-9
   - Ya existe en BD ✗

RESULTADO:
- Gasto NO creado
- Etiqueta: "Facturas pendientes" (sin cambios)
- Estado: duplicate
- Mensaje: "Invoice already exists"
```

---

## 14. Ventajas de esta Solución Simplificada

### ✅ Simplicidad
- No requiere UI compleja de revisión
- Flujo basado en etiquetas familiar para usuarios de Gmail
- Trigger manual simple

### ✅ Flexibilidad
- Usuario controla qué emails procesar (con etiquetas)
- Puede revisar antes de etiquetar
- Puede re-procesar emails con error

### ✅ Transparencia
- Etiquetas visibles en Gmail
- Fácil identificar qué se procesó y qué no
- Log de errores accesible

### ✅ Bajo Mantenimiento
- Menos código que mantener
- Menos componentes
- Menos puntos de falla

---

## 15. Limitaciones y Consideraciones

### Limitaciones

1. **Requiere intervención manual**
   - Usuario debe aplicar etiqueta o configurar filtro
   - Debe hacer clic en "Procesar" (no es 100% automático)

2. **Sin revisión previa**
   - Gastos se crean directamente
   - Requiere confianza en la extracción de datos

3. **Manejo de errores básico**
   - Emails con error quedan en "Facturas pendientes"
   - Usuario debe revisar manualmente

### Consideraciones

1. **Calidad de PDFs**
   - PDFs deben tener texto seleccionable
   - PDFs escaneados (solo imagen) tendrán baja confidence

2. **Formato de Facturas**
   - Optimizado para facturas AFIP argentinas
   - Otros formatos pueden no funcionar

3. **Duplicados**
   - Solo detecta duplicados exactos (mismo número + CUIT)
   - Facturas rectificativas pueden ser marcadas como duplicadas

---

## 16. Plan de Implementación

### Fase 1: Core (MVP)
- ✅ Modelo de datos
- ✅ Servicio de email (IMAP + etiquetas)
- ✅ Servicio de extracción de PDFs
- ✅ Procesador de facturas
- ✅ Endpoint de trigger
- ✅ Detección de duplicados

### Fase 2: UI Básica
- ⏳ Botón "Procesar Facturas"
- ⏳ Modal con resultados
- ⏳ Historial de procesamiento

### Fase 3: Mejoras (Futuro)
- ⏳ Procesamiento automático programado
- ⏳ OCR para PDFs escaneados
- ⏳ Notificaciones de errores
- ⏳ Dashboard de métricas

---

## 17. Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| **Tasa de éxito** | > 80% de emails procesados exitosamente |
| **Confidence promedio** | > 70% |
| **Tiempo de procesamiento** | < 5 segundos por email |
| **Duplicados detectados** | 100% de duplicados evitados |
| **Errores** | < 20% de emails con error |

---

## 18. Documentación de Usuario

### Guía Rápida

**Paso 1: Configurar Gmail**
1. Crear etiquetas: "Facturas pendientes" y "Factura procesada"
2. Configurar filtro automático (opcional)

**Paso 2: Configurar en la App**
1. Ir a configuración
2. Ingresar credenciales de Gmail
3. Guardar

**Paso 3: Usar el Sistema**
1. Aplicar etiqueta "Facturas pendientes" a emails con facturas
2. Hacer clic en "Procesar Facturas"
3. Revisar resultados
4. Verificar gastos creados en sección Gastos

---

**Fin de la Especificación**

---

**Próximos Pasos:**
1. Revisar y aprobar especificación
2. Implementar modelos de datos
3. Implementar servicios backend
4. Crear endpoints API
5. Testing
6. Deployment
