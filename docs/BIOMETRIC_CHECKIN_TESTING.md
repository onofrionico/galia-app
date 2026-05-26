# Guía de Testing - Sistema de Ficha Biométrica

## Configuración Inicial

### 1. Backend Setup

```bash
# Navegar al directorio backend
cd backend

# Instalar dependencias nuevas
pip install -r requirements.txt

# Aplicar migrations
flask db upgrade

# Seed de ubicaciones para testing (opcional)
python seed_biometric_locations.py

# Iniciar servidor
python run.py
# Backend corre en http://localhost:5000
```

### 2. Frontend Setup

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias nuevas (incluyendo jsQR y face-api)
npm install

# Iniciar dev server
npm run dev
# Frontend corre en http://localhost:5173
```

## Pruebas de Funcionalidad

### Test 1: Generación de QR

**Objetivo**: Verificar que se puede generar un código QR válido

**Pasos**:
1. Login como empleado (usar credenciales de seed)
2. Navegar a "Fichar Biométrico" en el sidebar
3. En la página, hacer clic en "Generar QR" (si existe el botón)
4. O acceder directamente a: `http://localhost:5173/biometric-check-in`

**Verificar**:
- ✓ Se muestra un código QR
- ✓ El QR es diferente cada vez que se genera
- ✓ El QR contiene datos válidos (token y employee_id)

**Backend Check**:
```bash
# Ver en la consola del backend que se creó BiometricSession:
# Buscar línea como: "[INFO] Created BiometricSession with token: ..."
```

---

### Test 2: Escaneo de QR

**Objetivo**: Verificar que el scanner detecta correctamente los códigos QR

**Pasos**:
1. En la página de BiometricCheckIn, debería verse un video feed
2. Apuntar con la cámara a un código QR (puedes usar tu móvil con otro código)
3. El sistema debe detectar automáticamente el QR

**Verificar**:
- ✓ Video se carga y muestra el feed de la cámara
- ✓ Al escanear un QR, la aplicación detecta el código
- ✓ Se pasa automáticamente al siguiente paso (captura biométrica)

**Fallback Test**:
1. Si la cámara no está disponible, hacer clic en "No puedo usar la cámara"
2. Ingresar manualmente un token QR válido
3. Hacer clic en "Continuar"

---

### Test 3: Solicitud de Permisos

**Objetivo**: Verificar que se piden correctamente los permisos de GPS y cámara

**Pasos**:
1. Después de escanear QR, se debe mostrar una pantalla de permisos
2. Hacer clic en "Permitir Acceso"

**Verificar**:
- ✓ Navegador solicita permiso de cámara
- ✓ Navegador solicita permiso de geolocalización
- ✓ Ambos permisos son aceptados
- ✓ Se pasa al paso de captura

**Rechazo de Permisos**:
1. Si rechazas los permisos, debería mostrar un error
2. Verificar que puedes intentar de nuevo

---

### Test 4: Detección de Rostro

**Objetivo**: Verificar que se detectan rostros correctamente con face-api

**Pasos**:
1. Después de aceptar permisos, se muestra la cámara
2. El modelo de face-api se cargará (puede tardar 5-10 segundos)
3. Mirar a la cámara directamente
4. Se debe mostrar "✓ Un rostro detectado" en verde

**Verificar**:
- ✓ Se carga el modelo de face-api
- ✓ Se detecta tu rostro en tiempo real
- ✓ Borde del cuadro cambia a verde cuando se detecta un rostro
- ✓ Botón "Capturar Foto" se habilita (deja de estar gris)
- ✓ Si aparecen dos rostros, se muestra advertencia

**Edge Cases**:
1. **Sin rostro**: Apartar la cara - debería mostrar "No se detecta rostro"
2. **Múltiples rostros**: Poner otra persona - debería mostrar "⚠ 2 rostros detectados"
3. **Mala iluminación**: Oscuridad - sistema debe seguir intentando detectar

---

### Test 5: Captura de Foto

**Objetivo**: Verificar que se captura correctamente la foto del usuario

**Pasos**:
1. Con un rostro detectado, hacer clic en "Capturar Foto"
2. La foto se debe capturar desde el video stream

**Verificar**:
- ✓ Se captura una imagen clara
- ✓ La imagen se muestra en la siguiente pantalla
- ✓ Se calcula un score de confianza (ej: 0.92)
- ✓ Si el score está arriba de 0.85, muestra "✓ Identidad Verificada"

**Recaptura**:
1. Si la foto no es buena, hacer clic en "Intentar Nuevamente"
2. Volver a capturar una foto

---

### Test 6: Ubicación GPS

**Objetivo**: Verificar que se captura correctamente la ubicación GPS

**Pasos**:
1. Durante toda la captura, el sistema debe estar recolectando datos GPS
2. Verificar que se muestran las coordenadas

**Verificar**:
- ✓ Se muestra latitud
- ✓ Se muestra longitud
- ✓ Se muestra precisión (accuracy) en metros
- ✓ Valores parecen razonables para tu ubicación

**Testing sin GPS Real**:
Si estás desarrollando sin GPS real:
1. Usa las herramientas de developer (DevTools) del navegador
2. Emula ubicación en Chrome DevTools:
   - F12 → Ctrl+Shift+P → "Emulate geolocation"
   - Selecciona una ubicación predefinida o ingresa coordenadas

---

### Test 7: Selección Entrada/Salida

**Objetivo**: Verificar que se puede seleccionar correctamente el tipo de registro

**Pasos**:
1. Con foto capturada y verificada, se muestran dos botones: "Entrada" y "Salida"
2. Hacer clic en "Entrada"

**Verificar**:
- ✓ Botón se destaca (se ve seleccionado)
- ✓ Se muestra resumen de datos (tipo, ubicación, confianza)
- ✓ Botón "Confirmar Registro" se habilita

**Test de Salida**:
1. Si ya hay una entrada activa, hacer clic en "Salida"
2. Debería aceptar la salida

---

### Test 8: Registro Completo (Check-in)

**Objetivo**: Verificar que el check-in se guarda correctamente en la base de datos

**Pasos**:
1. Habiendo seleccionado Entrada/Salida, hacer clic en "Confirmar Registro"
2. Sistema muestra "Registrando entrada..."
3. Esperar a que se complete

**Verificar Backend**:
```bash
# Conectarse a la base de datos PostgreSQL:
psql -U your_user -d your_db -c "SELECT * FROM work_blocks ORDER BY created_at DESC LIMIT 1;"

# Debería mostrar un registro nuevo con:
# - latitude, longitude, accuracy (números)
# - photo_url (URL en S3 o NULL si S3 no está configurado)
# - biometric_verified = true
# - entry_type = 'qr_biometric'
# - start_time = hora de entrada
# - end_time = hora de entrada (todavía igual para una entrada activa)
```

**Verificar Frontend**:
- ✓ Mensaje "✓ Entrada registrada a las HH:MM"
- ✓ Se muestra botón "Escanear Otro QR"
- ✓ Se puede volver a escanear otro QR

---

### Test 9: Verificación de Datos en Base de Datos

**Objetivo**: Verificar que todos los datos se guardaron correctamente

**Query para Verificar**:
```sql
-- Ver el último check-in
SELECT 
  id, 
  employee_id, 
  start_time, 
  end_time, 
  latitude, 
  longitude, 
  accuracy, 
  photo_url, 
  biometric_verified, 
  biometric_confidence,
  entry_type,
  created_at
FROM work_blocks 
WHERE entry_type = 'qr_biometric'
ORDER BY created_at DESC 
LIMIT 5;
```

**Verificar**:
- ✓ latitude y longitude tienen valores numéricos válidos
- ✓ accuracy es un número razonable (< 100m es bueno)
- ✓ biometric_verified = true
- ✓ entry_type = 'qr_biometric'
- ✓ photo_url es NULL o contiene URL válida

---

## Pruebas de Geofencing (Opcional)

### Setup
```bash
# Seed de ubicaciones:
cd backend
python seed_biometric_locations.py
```

### Test de Geofencing Activo
1. Modificar biometric.py para usar geofencing:
```python
# En biometric.py, línea ~180, uncomment:
if biometric_session.qr_location_id:
    location = LocationBoundary.query.filter_by(...)
```

2. Generar QR con location_id vinculado
3. Intentar check-in desde fuera del radio
4. Debería rechazar con error de ubicación

---

## Pruebas en Móvil

### Testing en Android/iOS

**Android Chrome**:
1. Abrir Chrome en Android
2. Navegar a `localhost:5173` (en la LAN local)
3. Probar completo el flujo

**iOS Safari**:
1. Abrir Safari en iOS
2. Navegar a la dirección IP del servidor en la LAN
3. Probar completo el flujo

### Requisitos Móvil
- ✓ HTTPS para acceso a cámara (use túnel ngrok si está en local)
- ✓ GPS debe estar activado en el dispositivo
- ✓ Permisos de cámara concedidos

---

## Troubleshooting

### "Error cargando modelos de detección"
**Causa**: Face-api no puede descargar los modelos desde CDN
**Solución**:
- Verificar conexión a internet
- Los modelos se descargan de: `https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/`
- Esperar 10-20 segundos en la primera carga

### "No se puede acceder a la cámara"
**Causa**: Permiso denegado o cámara en uso
**Solución**:
- Verificar que diste permiso de cámara en el navegador
- Cerrar otras aplicaciones usando la cámara
- Reiniciar el navegador

### "Ubicación no disponible"
**Causa**: GPS no está habilitado o sin señal
**Solución**:
- Activar GPS en el dispositivo
- Esperar a que se localice (puede tardar 10-30 segundos)
- Usar emulación en DevTools si estás en desktop

### "No se detecta rostro"
**Causa**: Mala iluminación o distancia a la cámara
**Solución**:
- Mejorar la iluminación
- Acercarse más a la cámara
- Asegurar que el rostro está completamente visible

### "QR inválido o no existe"
**Causa**: Token QR expirado (> 5 minutos)
**Solución**:
- Generar un nuevo QR
- Los QRs expiran después de 5 minutos

---

## Validación de Producción

### Checklist Final
- [ ] Backend API respondiendo correctamente
- [ ] Frontend cargando sin errores
- [ ] QR generation funcionando
- [ ] Face detection detectando rostros
- [ ] GPS capturando ubicación
- [ ] Check-in guardándose en DB
- [ ] Fotos subiendo a S3 (si configurado)
- [ ] Geofencing funcionando (si habilitado)
- [ ] Mobile responsive
- [ ] Error handling adecuado

### Performance Checks
- Frontend carga en < 3 segundos
- Face-api models cargan en < 15 segundos (primera vez)
- QR scan ocurre < 1 segundo
- Check-in submission < 2 segundos

---

## Datos de Test

### Usuario de Test
```
Email: test@example.com
Contraseña: Test123!
Role: employee
```

### Ubicación de Test
```
Nombre: Café Centro Principal
Latitud: -34.6037
Longitud: -58.3816
Radio: 50 metros
```

---

## Próximos Pasos

### Después de Testing Exitoso:
1. ✅ Mergear a `main` branch
2. ✅ Deployar a staging
3. ✅ Testing en staging environment
4. ✅ Deployar a producción
5. ✅ Monitorear en vivo

### Mejoras Futuras:
- [ ] Integración con AWS Rekognition para face matching
- [ ] Batch processing de fotos para mejor performance
- [ ] Analytics dashboard de check-ins
- [ ] Notificaciones en tiempo real
- [ ] Histórico y reportes de asistencia
