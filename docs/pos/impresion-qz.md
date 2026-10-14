# Impresión de comandas y tickets con QZ Tray

La impresión la hace una PC del local con QZ Tray y la página **Impresión** de Galia abierta (`/pos/impresion`). El backend encola los trabajos y esa página los imprime en las térmicas de red (IP, puerto 9100) y USB (instaladas en Windows).

## 1. Preparar la PC de impresión (una vez por PC)

1. Descargar e instalar QZ Tray desde https://qz.io/download/. Queda corriendo en la bandeja del sistema y arranca con Windows.
2. En Galia, abrir **Impresión** (`/pos/impresion`) y tocar **Preparar esta PC**. Se descarga `preparar-impresion-galia.bat`: abrirlo y aceptar el permiso de Windows. Si Chrome avisa que el archivo puede ser peligroso, elegir **Conservar**.
3. El archivo instala el certificado de Galia en QZ Tray y lo reinicia. La página se conecta sola en unos segundos y ya no pregunta "¿Permitir?" al imprimir.

El certificado es el mismo para todas las PCs: para sumar otra PC (o reemplazar la de caja) se repiten estos tres pasos.

### Cómo funciona la firma

QZ Tray solo imprime sin preguntar si el pedido viene firmado con una clave en la que confía. Galia genera ese par de claves sola la primera vez que se abre la página de impresión y lo guarda en la base de datos. El backend firma cada pedido, y el archivo de "Preparar esta PC" le instala a QZ Tray el certificado correspondiente (`override.crt` en su carpeta).

Opcional: para manejar el par fuera de la base, definir en el backend (Render → `galia-backend` → Environment) `QZ_CERTIFICATE` y `QZ_PRIVATE_KEY` con los PEM completos (se aceptan saltos de línea reales o `\n`). Si están definidas, tienen prioridad sobre el par guardado. Si se cambian, hay que volver a hacer **Preparar esta PC** en cada PC.

## 2. Estaciones, impresoras y categorías

En Galia, como admin:

1. **Ajustes del POS → Estaciones:** crear "Cocina", "Barra" (o las que correspondan).
2. **Ajustes del POS → Impresoras:** dar de alta cada térmica:
   - **Red:** IP fija de la impresora y puerto 9100.
   - **USB:** el nombre exacto con el que figura en Windows (Configuración → Impresoras).
   - **Papel:** 58 u 80 mm.
   - **Punto de impresión:** "Caja" (el nombre que va a elegir la PC de impresión).
   - **Estación:** la que imprime esa impresora, o marcar "Impresora de caja" para precuentas y tickets.
3. **Productos → Categorías:** en cada categoría, elegir la estación. "Sin comanda" no imprime (por ejemplo, lo que se entrega directo en caja).

## 3. Dejar la página de impresión abierta

1. En la PC de impresión, entrar a Galia con un usuario con permiso POS y abrir `/pos/impresion`.
2. Elegir el punto de impresión ("Caja").
3. Fijar la pestaña en Chrome (clic derecho → Fijar) y configurarla como página de inicio, para que se abra sola al prender la PC.
4. Desactivar la suspensión de la PC durante el horario del local.

## 4. Probar

En la página de impresión, usar **Imprimir prueba** en cada impresora: tiene que salir un ticket con acentos y ñ legibles. Después, confirmar una tanda de prueba en el POS y verificar que cada estación reciba solo lo suyo.

Para probar sin impresoras, marcar **Modo simulación**: la página muestra en pantalla lo que se habría impreso y marca los trabajos como impresos. No queda guardado: al recargar la página vuelve a imprimir de verdad.

## Si algo no imprime

- El indicador **Impresión** de la caja se pone rojo y muestra qué falló.
- "QZ Tray no está abierto": abrir QZ Tray. La página se reconecta sola (o tocar **Reintentar**).
- QZ Tray pregunta "¿Permitir?" en cada impresión: falta el certificado en esa PC. Tocar **Preparar esta PC** y ejecutar el archivo.
- Si una impresora está apagada, las demás siguen imprimiendo; sus trabajos se reintentan solos al volver.
- La página puede quedar en una pestaña de fondo mientras se usa la caja en otra: sigue imprimiendo.
- Impresora de red: verificar que la PC llegue a esa IP (por ejemplo, `ping 192.168.0.50`).
- Los trabajos quedan en cola: cuando se resuelve, se imprimen solos. Si ya se resolvió a mano, usar **Marcar como impresa**.
