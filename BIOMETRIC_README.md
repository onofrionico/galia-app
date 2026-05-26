# 📸 Sistema de Ficha Biométrica con QR

Sistema completo de registro de entrada/salida de empleados utilizando códigos QR, detección facial en tiempo real y geolocalización GPS.

## 🎯 Características

- **Escaneo de QR**: Códigos QR dinámicos con tokens de 5 minutos
- **Detección Facial**: Detección de rostros en tiempo real usando face-api.js
- **Geolocalización**: Captura de GPS con precisión y validación
- **Geofencing** (Opcional): Límite de ubicaciones para check-in
- **Responsive**: Funciona en desktop, tablet y móvil
- **Almacenamiento**: Fotos en S3, registros en PostgreSQL

## 🚀 Inicio Rápido

### Opción 1: Setup Automático (Recomendado)

```bash
# Desde la raíz del proyecto
bash setup_biometric.sh

# Luego en dos terminales:
# Terminal 1:
cd backend && python run.py

# Terminal 2:
cd frontend && npm run dev
```

### Opción 2: Setup Manual

**Backend:**
```bash
cd backend
pip install -r requirements.txt
flask db upgrade
python seed_biometric_locations.py
python run.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentación

- **[Testing Guide](docs/BIOMETRIC_CHECKIN_TESTING.md)** - Guía completa de testing
- **API Reference** - Ver `backend/app/routes/biometric.py`
- **Components** - Ver `frontend/src/components/biometric/`

## 🔄 Flujo de Usuario

```
1. Escanear QR
   ↓
2. Permitir acceso a cámara y GPS
   ↓
3. Capturar foto (face-api detecta rostro)
   ↓
4. Ubicación GPS se captura automáticamente
   ↓
5. Seleccionar Entrada o Salida
   ↓
6. Confirmar registro
   ↓
7. ✅ Check-in completado
```

## 🛠 Stack Tecnológico

### Backend
- **Flask** - Framework web
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos
- **qrcode** - Generación de códigos QR
- **boto3** - Almacenamiento en AWS S3

### Frontend
- **React 18** - Framework UI
- **jsQR** - Escaneo de códigos QR
- **@vladmandic/face-api** - Detección facial en tiempo real
- **Geolocation API** - GPS del navegador
- **Tailwind CSS** - Estilos

## 📋 Requisitos

### Hardware
- Cámara web (entrada/salida de video)
- Acceso a GPS (móvil o emulado)
- Micrófono (opcional, para navegadores futuros)

### Software
- Node.js >= 18
- Python >= 3.8
- PostgreSQL >= 12
- Navegador moderno (Chrome, Firefox, Safari, Edge)

## 🔐 Seguridad

- **Tokens QR**: Generados aleatoriamente, expiran en 5 minutos
- **Sesiones**: Un token = un registro
- **Fotos**: Almacenadas en S3 con encriptación
- **GPS**: Validación de precisión y geofencing opcional
- **Biometría**: Confianza de detección de rostro registrada

## 🌐 Endpoints API

### Públicos (Sin autenticación)
```
GET  /api/v1/biometric/qr/<token>
     - Validar QR y obtener información del empleado

POST /api/v1/biometric/check-in
     - Registrar entrada/salida con datos biométricos
```

### Autenticados
```
POST /api/v1/biometric/qr-generate
     - Generar nuevo código QR (empleado logueado)

POST /api/v1/biometric/verify-face
     - Verificar rostro (opcional, para ML avanzado)
```

## 💾 Base de Datos

### work_blocks (Extendido)
```sql
id                      INT
time_tracking_id        INT (FK)
start_time             TIME
end_time               TIME
latitude               FLOAT      -- GPS latitud
longitude              FLOAT      -- GPS longitud
accuracy               FLOAT      -- Precisión GPS en metros
photo_url              VARCHAR    -- URL en S3
biometric_confidence   FLOAT      -- Score de detección (0-1)
biometric_verified     BOOLEAN    -- ¿Se verificó rostro?
entry_type             VARCHAR    -- 'qr_biometric', 'manual', 'legacy'
raw_metadata           JSON       -- Metadata adicional
```

### biometric_sessions
```sql
id                INT
employee_id       INT (FK)
session_token     VARCHAR UNIQUE
qr_location_id    VARCHAR
qr_generated_at   DATETIME
qr_scanned_at     DATETIME
status            VARCHAR (active, used, expired)
expires_at        DATETIME
work_block_id     INT (FK)
```

### location_boundaries (Opcional)
```sql
id                INT
name              VARCHAR
latitude          FLOAT
longitude         FLOAT
radius_meters     FLOAT
is_active         BOOLEAN
```

## 🧪 Testing

Ejecuta la guía completa en [BIOMETRIC_CHECKIN_TESTING.md](docs/BIOMETRIC_CHECKIN_TESTING.md)

Resumen rápido:
```bash
# Test 1: QR Generation
- Generar QR
- Verificar que es válido

# Test 2: QR Scanning
- Escanear QR
- Verificar detección automática

# Test 3: Face Detection
- Mostrar rostro a cámara
- Verificar detección en tiempo real

# Test 4: GPS Capture
- Verificar coordenadas capturadas
- Validar precisión

# Test 5: Full Check-in
- Completar flujo entero
- Verificar datos en BD
```

## ⚙️ Configuración

### Variables de Entorno Requeridas (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/galia

# AWS S3 (para fotos)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET_NAME=your_bucket
AWS_REGION=us-east-1

# Security
SECRET_KEY=your_secret_key_here
```

### Configuración de Geofencing (Opcional)

En `backend/app/routes/biometric.py`, línea ~180:

```python
# Uncomment para habilitar validación de geofencing
if biometric_session.qr_location_id:
    location = LocationBoundary.query.filter_by(...)
    if not location.is_within_boundary(latitude, longitude):
        return jsonify({'error': 'Fuera del área permitida'}), 403
```

Luego seed las ubicaciones:
```bash
cd backend
python seed_biometric_locations.py
```

## 📊 Arquitectura

```
┌─────────────────────────────────────────────────┐
│           EMPLOYEE MOBILE/DESKTOP               │
├─────────────────────────────────────────────────┤
│                 React Frontend                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  QR Scanner  │  │ Face Capture │            │
│  │   (jsQR)     │  │  (face-api)  │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────────────────────────┐          │
│  │  GPS Capture (Geolocation API)   │          │
│  └──────────────────────────────────┘          │
└─────────────────────────────────────────────────┘
            ↓ REST API
┌─────────────────────────────────────────────────┐
│              Flask Backend                      │
│  ┌──────────────────────────────────┐          │
│  │   POST /biometric/check-in       │          │
│  │   - Validate QR token            │          │
│  │   - Check geofencing             │          │
│  │   - Upload photo to S3           │          │
│  │   - Create work_block record     │          │
│  └──────────────────────────────────┘          │
└─────────────────────────────────────────────────┘
        ↓ ORM ↓ Storage
┌─────────────────────────────────────────────────┐
│           Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ PostgreSQL   │  │   AWS S3     │            │
│  │ work_blocks  │  │    Photos    │            │
│  │ biometric_   │  └──────────────┘            │
│  │  sessions    │                              │
│  └──────────────┘                              │
└─────────────────────────────────────────────────┘
```

## 🚨 Troubleshooting

| Problema | Solución |
|----------|----------|
| Face-api no carga | Verificar conexión CDN, esperar 10-20s |
| Cámara no accede | Dar permiso en navegador, reiniciar |
| GPS no funciona | Activar GPS, usar emulación en DevTools |
| QR inválido | Generar nuevo (expira en 5 min) |
| Fotos no suben | Verificar AWS S3 configurado |

## 🎓 Mejoras Futuras

- [ ] Facial Recognition con AWS Rekognition
- [ ] Dashboard de asistencia en tiempo real
- [ ] Reportes y analytics
- [ ] Notificaciones push
- [ ] Integración con calendario
- [ ] Múltiples sucursales
- [ ] Reportes de tardanzas

## 📞 Support

Para problemas o preguntas, revisar:
- `docs/BIOMETRIC_CHECKIN_TESTING.md`
- `backend/app/routes/biometric.py` (API)
- `frontend/src/components/biometric/` (Frontend)

## 📄 Licencia

Parte del proyecto Galia - Café Management System
