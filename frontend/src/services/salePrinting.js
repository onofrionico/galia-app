/**
 * Sale Printing Service
 * Handles printing of comanda (kitchen order) and control (payment receipt)
 */

// Debug mode - set to true for testing without printer
const DEBUG_MODE = localStorage.getItem('POS_DEBUG_PRINT') === 'true'

const salePrinting = {
  /**
   * Print comanda (kitchen order) with items
   * Called when items are confirmed to go to the kitchen
   */
  async printComanda(sale, items, newItemsOnly = false) {
    try {
      console.log(`[COMANDA] Enviando orden a impresora...`, {
        mesa: sale.mesa_id,
        items: items.length,
        newItemsOnly,
        timestamp: new Date().toLocaleTimeString(),
      })

      const window_print = window.open('', 'PRINT', 'width=600,height=400')

      const itemsText = (items || [])
        .map(
          (item) =>
            `${item.quantity}x ${item.product_name}${
              item.variant_name ? ` (${item.variant_name})` : ''
            }`
        )
        .join('\n')

      const htmlContent = `
        <html>
          <head>
            <title>COMANDA - Mesa ${sale.mesa_id || 'N/A'}</title>
            <style>
              body {
                font-family: monospace;
                font-size: 14px;
                margin: 0;
                padding: 10px;
              }
              .header {
                text-align: center;
                border-bottom: 2px solid #000;
                margin-bottom: 10px;
                padding-bottom: 5px;
              }
              .items {
                margin: 20px 0;
                line-height: 1.8;
              }
              .footer {
                border-top: 2px solid #000;
                margin-top: 10px;
                padding-top: 5px;
                text-align: center;
                font-size: 12px;
              }
              .time {
                font-size: 12px;
                color: #666;
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h2 style="margin: 0;">COMANDA</h2>
              <p style="margin: 5px 0;">Mesa ${sale.mesa_id || 'N/A'}</p>
              ${sale.numero_personas ? `<p style="margin: 5px 0;">${sale.numero_personas} Persona(s)</p>` : ''}
              ${newItemsOnly ? '<p style="margin: 5px 0; font-weight: bold;">NUEVOS ITEMS</p>' : ''}
            </div>
            <div class="items">
              ${itemsText}
            </div>
            <div class="footer">
              <p class="time">${new Date().toLocaleString()}</p>
              ${sale.comentarios ? `<p style="margin: 5px 0;">Nota: ${sale.comentarios}</p>` : ''}
            </div>
          </body>
        </html>
      `

      if (DEBUG_MODE) {
        console.log('[COMANDA DEBUG] Contenido a imprimir:')
        console.log(htmlContent)
        console.log('[COMANDA DEBUG] En producción, esto se enviaría a la impresora')
      }

      window_print.document.write(htmlContent)
      window_print.document.close()
      window_print.print()

      console.log(`[COMANDA ✓] Comanda enviada a impresora - Mesa ${sale.mesa_id}`)
      return true
    } catch (error) {
      console.error('[COMANDA ERROR]', error)
      return false
    }
  },

  /**
   * Print control (payment receipt) for the sale
   * Called when payment is registered/completed
   */
  async printControl(sale, items, totalWithDiscount, paid) {
    try {
      console.log(`[CONTROL] Enviando recibo a impresora...`, {
        mesa: sale.mesa_id,
        total: totalWithDiscount,
        pagado: paid,
        timestamp: new Date().toLocaleTimeString(),
      })

      const window_print = window.open('', 'PRINT', 'width=600,height=400')

      const itemsText = (items || [])
        .map(
          (item) =>
            `${item.quantity.toString().padEnd(2)} x ${item.product_name.substring(0, 25).padEnd(25)} $${item.unit_price.toFixed(2)} = $${(
              item.unit_price * item.quantity
            ).toFixed(2)}`
        )
        .join('\n')

      const discountLine = sale.descuento_monto
        ? `DESCUENTO (${sale.descuento_tipo === 'porcentaje' ? `${sale.descuento_valor}%` : 'fijo'})  -$${sale.descuento_monto.toFixed(2)}`
        : ''

      const remaining = Math.max(0, totalWithDiscount - paid)

      const htmlContent = `
        <html>
          <head>
            <title>CONTROL - Mesa ${sale.mesa_id || 'N/A'}</title>
            <style>
              body {
                font-family: monospace;
                font-size: 12px;
                margin: 0;
                padding: 10px;
              }
              .header {
                text-align: center;
                border-bottom: 2px solid #000;
                margin-bottom: 10px;
                padding-bottom: 5px;
              }
              .items {
                margin: 10px 0;
                line-height: 1.6;
              }
              .totals {
                border-top: 2px solid #000;
                border-bottom: 2px solid #000;
                margin: 10px 0;
                padding: 8px 0;
              }
              .total-row {
                display: flex;
                justify-content: space-between;
                margin: 3px 0;
              }
              .total-final {
                font-weight: bold;
                font-size: 16px;
              }
              .footer {
                margin-top: 10px;
                text-align: center;
                font-size: 11px;
              }
              .payment-info {
                margin: 10px 0;
                padding: 8px;
                border: 1px solid #666;
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h3 style="margin: 0;">CONTROL</h3>
              <p style="margin: 3px 0;">Mesa ${sale.mesa_id || 'N/A'}</p>
              ${sale.numero_personas ? `<p style="margin: 3px 0;">${sale.numero_personas} Persona(s)</p>` : ''}
            </div>
            <div class="items">
              ${itemsText}
            </div>
            <div class="totals">
              <div class="total-row">
                <span>SUBTOTAL:</span>
                <span>$${sale.total.toFixed(2)}</span>
              </div>
              ${
                discountLine
                  ? `
                <div class="total-row">
                  <span>${discountLine}</span>
                </div>
              `
                  : ''
              }
              <div class="total-row total-final">
                <span>TOTAL:</span>
                <span>$${totalWithDiscount.toFixed(2)}</span>
              </div>
              ${
                paid > 0
                  ? `
                <div class="total-row">
                  <span>PAGADO:</span>
                  <span>$${paid.toFixed(2)}</span>
                </div>
              `
                  : ''
              }
              ${
                remaining > 0
                  ? `
                <div class="total-row" style="color: red;">
                  <span>PENDIENTE:</span>
                  <span>$${remaining.toFixed(2)}</span>
                </div>
              `
                  : ''
              }
            </div>
            ${
              paid > 0 || remaining === 0
                ? `
              <div class="payment-info">
                <p style="margin: 2px 0;">Estado: ${remaining <= 0 ? 'PAGADO' : 'PARCIALMENTE PAGADO'}</p>
              </div>
            `
                : ''
            }
            <div class="footer">
              <p style="margin: 3px 0;">${new Date().toLocaleString()}</p>
              ${sale.comentarios ? `<p style="margin: 3px 0;">Nota: ${sale.comentarios}</p>` : ''}
            </div>
          </body>
        </html>
      `

      if (DEBUG_MODE) {
        console.log('[CONTROL DEBUG] Contenido a imprimir:')
        console.log(htmlContent)
      }

      window_print.document.write(htmlContent)
      window_print.document.close()
      window_print.print()

      console.log(`[CONTROL ✓] Recibo enviado a impresora - Mesa ${sale.mesa_id}`)
      return true
    } catch (error) {
      console.error('[CONTROL ERROR]', error)
      return false
    }
  },

  /**
   * Print simple ticket (minimal receipt)
   * Can be used as an alternative or supplement
   */
  async printTicket(saleNumber, total, itemCount, timestamp) {
    try {
      console.log(`[TICKET] Enviando ticket a impresora...`, {
        venta: saleNumber,
        total,
        items: itemCount,
        timestamp: new Date().toLocaleTimeString(),
      })

      const window_print = window.open('', 'PRINT', 'width=400,height=300')

      const htmlContent = `
        <html>
          <head>
            <title>TICKET #${saleNumber}</title>
            <style>
              body {
                font-family: monospace;
                font-size: 14px;
                margin: 0;
                padding: 5px;
                width: 300px;
              }
              .header {
                text-align: center;
                border-bottom: 1px solid #000;
                padding-bottom: 5px;
              }
              .content {
                margin: 10px 0;
              }
              .footer {
                border-top: 1px solid #000;
                text-align: center;
                padding-top: 5px;
                font-size: 12px;
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h3 style="margin: 0;">VENTA #${saleNumber}</h3>
            </div>
            <div class="content">
              <p>Items: ${itemCount}</p>
              <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">Total: $${total.toFixed(2)}</p>
            </div>
            <div class="footer">
              <p>${new Date().toLocaleString()}</p>
            </div>
          </body>
        </html>
      `

      if (DEBUG_MODE) {
        console.log('[TICKET DEBUG] Contenido a imprimir:')
        console.log(htmlContent)
      }

      window_print.document.write(htmlContent)
      window_print.document.close()
      window_print.print()

      console.log(`[TICKET ✓] Ticket enviado a impresora - Venta #${saleNumber}`)
      return true
    } catch (error) {
      console.error('[TICKET ERROR]', error)
      return false
    }
  },
}

export default salePrinting
