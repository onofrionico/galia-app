# Impresión de comandas y tickets con QZ Tray

La impresión la hace una PC del local con QZ Tray y la página **Impresión** de Galia abierta (`/pos/impresion`). El backend encola los trabajos y esa página los imprime en las térmicas de red (IP, puerto 9100) y USB (instaladas en Windows).

## 1. Instalar QZ Tray

Descargar e instalar QZ Tray desde https://qz.io/download/ en la PC de impresión (la de caja). Queda corriendo en la bandeja del sistema y arranca con Windows.

## 2. Certificado para imprimir sin confirmación

Sin certificado, QZ Tray pregunta "¿Permitir?" en cada impresión. Para evitarlo, generar un par de claves (una sola vez, en cualquier PC con OpenSSL, por ejemplo Git Bash):

```bash
openssl req -x509 -newkey rsa:2048 -keyout galia-qz-key.pem -out galia-qz-cert.pem -days 3650 -nodes -subj "/CN=Galia POS"
```

- En Render (servicio `galia-backend` → Environment), cargar:
  - `QZ_CERTIFICATE` con el contenido completo de `galia-qz-cert.pem`.
  - `QZ_PRIVATE_KEY` con el contenido completo de `galia-qz-key.pem`.
- En la PC de impresión, copiar `galia-qz-cert.pem` como `override.crt` en la carpeta de instalación de QZ Tray (por ejemplo `C:\Program Files\QZ Tray\override.crt`) y reiniciar QZ Tray.
- Guardar la clave privada en un lugar seguro y no compartirla.

## 3. Estaciones, impresoras y categorías

En Galia, como admin:

1. **Ajustes del POS → Estaciones:** crear "Cocina", "Barra" (o las que correspondan).
2. **Ajustes del POS → Impresoras:** dar de alta cada térmica:
   - **Red:** IP fija de la impresora y puerto 9100.
   - **USB:** el nombre exacto con el que figura en Windows (Configuración → Impresoras).
   - **Papel:** 58 u 80 mm.
   - **Punto de impresión:** "Caja" (el nombre que va a elegir la PC de impresión).
   - **Estación:** la que imprime esa impresora, o marcar "Impresora de caja" para precuentas y tickets.
3. **Productos → Categorías:** en cada categoría, elegir la estación. "Sin comanda" no imprime (por ejemplo, lo que se entrega directo en caja).

## 4. Dejar la página de impresión abierta

1. En la PC de impresión, entrar a Galia con un usuario con permiso POS y abrir `/pos/impresion`.
2. Elegir el punto de impresión ("Caja").
3. Fijar la pestaña en Chrome (clic derecho → Fijar) y configurarla como página de inicio, para que se abra sola al prender la PC.
4. Desactivar la suspensión de la PC durante el horario del local.

## 5. Probar

En la página de impresión, usar **Imprimir prueba** en cada impresora: tiene que salir un ticket con acentos y ñ legibles. Después, confirmar una tanda de prueba en el POS y verificar que cada estación reciba solo lo suyo.

Para probar sin impresoras, marcar **Modo simulación**: la página muestra en pantalla lo que se habría impreso y marca los trabajos como impresos. No queda guardado: al recargar la página vuelve a imprimir de verdad.

## Si algo no imprime

- El indicador **Impresión** de la caja se pone rojo y muestra qué falló.
- "QZ Tray no está abierto": abrir QZ Tray. La página se reconecta sola (o tocar **Reintentar**).
- Si una impresora está apagada, las demás siguen imprimiendo; sus trabajos se reintentan solos al volver.
- La página puede quedar en una pestaña de fondo mientras se usa la caja en otra: sigue imprimiendo.
- Impresora de red: verificar que la PC llegue a esa IP (por ejemplo, `ping 192.168.0.50`).
- Los trabajos quedan en cola: cuando se resuelve, se imprimen solos. Si ya se resolvió a mano, usar **Marcar como impresa**.
