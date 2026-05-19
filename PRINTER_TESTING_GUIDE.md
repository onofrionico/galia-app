# Guía de Prueba de Impresora - POS

## ¿Cómo funciona actualmente?

El sistema POS envía comandos de impresión de tres tipos:

1. **COMANDA** - Orden que va a la cocina cuando se agrega un item
2. **CONTROL** - Recibo de pago cuando se cierra la venta
3. **TICKET** - Ticket simple (alternativa)

## Prueba Local sin Impresora

### Opción 1: Ver en Console (Recomendado para desarrollo)

1. **Abre el navegador en http://localhost:5173**
2. **Abre DevTools** - Presiona `F12` o `Ctrl+Shift+I`
3. **Ve a la pestaña "Console"**
4. **Crea una nueva venta y agrega un item**
5. **En la consola verás:**

```
[COMANDA] Enviando orden a impresora...
{mesa: 1, items: 1, newItemsOnly: true, timestamp: "14:32:15"}

[COMANDA DEBUG] Contenido a imprimir:
<html>
  <head>
    <title>COMANDA - Mesa 1</title>
    ...
  </head>
  <body>
    <div class="header">
      <h2>COMANDA</h2>
      <p>Mesa 1</p>
      ...
    </div>
    ...
  </body>
</html>

[COMANDA ✓] Comanda enviada a impresora - Mesa 1
```

### Opción 2: Habilitar Modo Debug Completo

En la consola del navegador, ejecuta:

```javascript
localStorage.setItem('POS_DEBUG_PRINT', 'true')
```

Luego recarga la página. Ahora verás más detalles en console cuando se intente imprimir.

### Opción 3: Usar "Imprimir a PDF"

1. Cuando se abre el diálogo de impresión del navegador
2. **En lugar de usar impresora física:**
   - Selecciona "Guardar como PDF"
   - Guarda el archivo
   - Abre el PDF para ver exactamente qué se imprimiría

**Ventaja**: Ves el resultado final exactamente como lo vería la impresora

## Flujo de Prueba Paso a Paso

### Test: Imprimir Comanda

```
1. Abre POS en http://localhost:5173
2. Abre DevTools (F12) → Console
3. Click en Mesa libre
4. Llenar "Número de personas" → Click "Crear Venta"
5. Click "Agregar Item"
6. Selecciona un producto
7. Confirma cantidad → Click "Agregar"

RESULTADO EN CONSOLE:
✓ [COMANDA] Enviando orden a impresora...
✓ Aparece el HTML que se imprimiría
✓ [COMANDA ✓] Comanda enviada a impresora
```

### Test: Imprimir Control (Recibo)

```
1. Desde la orden anterior
2. Click "Cobrar"
3. Selecciona "Método de Pago"
4. Ingresan monto
5. Click "Registrar Pago"
6. Si se cierra la venta...

RESULTADO EN CONSOLE:
✓ [CONTROL] Enviando recibo a impresora...
✓ Aparece el HTML del recibo
✓ [CONTROL ✓] Recibo enviado a impresora
```

## Mensajes en Console

Busca estos patrones en la consola:

| Mensaje | Significado | Color |
|---------|------------|-------|
| `[COMANDA] Enviando...` | Comanda siendo enviada | 🔵 Info |
| `[COMANDA ✓]` | Comanda enviada exitosamente | ✅ Éxito |
| `[COMANDA ERROR]` | Error al enviar comanda | ❌ Error |
| `[CONTROL]` | Recibo siendo enviado | 🔵 Info |
| `[CONTROL ✓]` | Recibo enviado exitosamente | ✅ Éxito |
| `[TICKET]` | Ticket siendo enviado | 🔵 Info |

## Integración en Producción

Para usar impresoras reales, necesitarás:

### Opción A: Impresora USB/Ethernet Directa

```javascript
// Backend API que reciba comandos de impresión
POST /api/v1/print/comanda
{
  mesa_id: 1,
  items: [...],
  newItemsOnly: true
}
```

El backend puede usar librerías como:
- Python: `escpos`, `usb.core`
- Node.js: `printer`, `node-thermal-printer`
- PHP: `escpos-php`

### Opción B: Servidor de Impresión Local

```
Cliente (POS) 
    ↓ HTTP
Servidor Local (puerto 5000)
    ↓ USB/Ethernet
Impresora Térmica
```

### Opción C: API en la Nube

```
Cliente (POS)
    ↓ HTTPS
API Cloud (e.g., CloudPrinter)
    ↓
Impresora en la nube
```

## Ambiente Actual

- **Tecnología**: `window.print()` (navegador)
- **Diálogo**: Abre print dialog del navegador
- **Interacción**: Usuario hace click en "Imprimir"
- **Confirmación**: Vista en Console + ACK

## Próximos Pasos

1. ✅ Test en desarrollo con console
2. ✅ Exportar a PDF para ver formato
3. 📋 Integrar con impresora real cuando esté disponible
4. 📋 Implementar servicio backend de impresión
5. 📋 Agregar reintentos automáticos en caso de fallo

## Deshabilitar Modo Debug

Si habilitaste modo debug:

```javascript
localStorage.removeItem('POS_DEBUG_PRINT')
```

O en la consola sin debug:
```javascript
localStorage.setItem('POS_DEBUG_PRINT', 'false')
```

---

**Nota**: Actualmente el sistema está optimizado para pruebas. En producción, se integraría directamente con drivers de impresora o un servicio backend especializado.
