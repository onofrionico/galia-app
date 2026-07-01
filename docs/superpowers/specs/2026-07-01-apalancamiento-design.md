# Diseño: Apalancamiento Operativo en el Dashboard de Reportes

**Fecha:** 2026-07-01  
**Estado:** Aprobado

## Resumen

Agregar al reporte mensual una sección de **Grado de Apalancamiento Operativo (GAO)** con un simulador interactivo de precio vs. volumen, para que el usuario pueda decidir si conviene defender el precio o generar más volumen.

---

## Arquitectura y flujo de datos

El backend agrega un objeto `apalancamiento` al response existente de `GET /api/v1/reports/dashboard`. El simulador corre completamente en el frontend usando los datos ya disponibles — no requiere llamadas adicionales a la API.

```
Backend: backend/app/routes/reports.py
  └── get_dashboard() → agrega apalancamiento{}

Frontend: frontend/src/pages/Reports.jsx
  └── <ApalancamientoCard dashboard={dashboard} />
        ├── Card superior: GAO + interpretación + recomendación
        └── Simulador: 2 sliders → proyección de resultado
```

---

## Backend

### Función `calculate_gao()`

Nueva función en `reports.py`, llamada desde `get_dashboard()` con los valores ya calculados.

**Fórmula:**
```
Margen de Contribución Total = Ventas - Gastos Directos
GAO = Margen de Contribución Total / Resultado Operativo
```

Donde Resultado Operativo = `resultado_neto` (ya calculado en el endpoint).

**Umbrales de interpretación:**
| GAO | Interpretación | Recomendación |
|-----|---------------|---------------|
| < 1.5 | `"bajo"` | `"precio"` |
| 1.5 – 3.0 | `"medio"` | `"equilibrado"` |
| > 3.0 | `"alto"` | `"volumen"` |

**Casos borde:**
- `resultado_neto <= 0` → `gao: null`, `estado: "en_perdida"`
- `margen_contribucion_total <= 0` → `gao: null`, `estado: "margen_negativo"`

**Response shape agregado al dashboard:**
```json
{
  "apalancamiento": {
    "gao": 2.4,
    "margen_contribucion_total": 150000,
    "resultado_operativo": 62500,
    "interpretacion": "medio",
    "recomendacion": "equilibrado",
    "estado": "ok"
  }
}
```

---

## Frontend

### Componente `ApalancamientoCard`

Nuevo componente en `Reports.jsx`, renderizado debajo de la sección "Punto de Equilibrio".

#### Parte superior — GAO display

- Número grande: `GAO: 2.4x`
- Color por interpretación: verde (`bajo`), amarillo (`medio`), rojo/naranja (`alto`)
- Badge de recomendación: `"Defender precio"` / `"Generar volumen"` / `"Equilibrado"`
- Frase explicativa dinámica: *"Cada 1% de aumento en ventas mejora tu ganancia un 2.4%"*
- Si `estado !== "ok"`: mostrar mensaje contextual en lugar del GAO

#### Parte inferior — Simulador interactivo

Dos sliders, rango −30% a +30%, paso 1%:
- **Δ Volumen**: variación en cantidad de ventas
- **Δ Precio**: variación en ticket promedio

**Lógica de proyección (cliente):**
```js
const nuevasVentas = ventas * (1 + deltaVolumen/100) * (1 + deltaPrecio/100)
const nuevosCostosVar = costosVariables * (1 + deltaVolumen/100)
const nuevoResultado = nuevasVentas - nuevosCostosVar - costosFijos
const variacion = nuevoResultado - resultadoActual
```

Fuentes de datos desde `dashboard`:
- `ventas` → `dashboard.ventas.total`
- `costosVariables` → `dashboard.punto_equilibrio.costos_variables`
- `costosFijos` → `dashboard.punto_equilibrio.costos_fijos`
- `resultadoActual` → `dashboard.rentabilidad.resultado_neto`

**Display de resultado:**
| Campo | Valor |
|-------|-------|
| Ventas proyectadas | formatCurrency(nuevasVentas) |
| Resultado proyectado | formatCurrency(nuevoResultado) |
| Variación vs. actual | +/- $ y % (verde si positivo, rojo si negativo) |

El resultado se actualiza en tiempo real al mover cualquier slider. Si la combinación precio↓ + volumen↑ da resultado positivo → verde; si no compensa → rojo.

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `backend/app/routes/reports.py` | Agregar `calculate_gao()` y llamarla en `get_dashboard()` |
| `frontend/src/pages/Reports.jsx` | Agregar componente `ApalancamientoCard` y renderizarlo |

No se requieren cambios en modelos, migraciones, ni servicios del frontend.
