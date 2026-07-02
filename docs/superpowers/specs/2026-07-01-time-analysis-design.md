# Diseño: Análisis por Día de Semana y Hora

**Fecha:** 2026-07-01  
**Estado:** Aprobado

## Resumen

Agregar una nueva pestaña "Día / Hora" en el dashboard de Reportes que muestre ventas y costo laboral desagregados por día de semana y por franja horaria, incluyendo un cruce costo/ventas por día con umbrales configurables en la propia vista.

---

## Arquitectura y flujo de datos

```
Backend: backend/app/routes/reports.py
  └── GET /api/v1/reports/time-analysis?start_date=&end_date=
        ├── get_sales_by_weekday(start, end)
        ├── get_sales_by_hour(start, end)
        ├── get_labor_by_weekday(start, end)
        ├── get_labor_by_hour(start, end)
        └── cross: ratio costo/ventas por día de semana

Frontend: frontend/src/pages/Reports.jsx
  └── Nueva pestaña "Día / Hora"
        ├── Reutiliza filtros de período (mes/período/rango) del dashboard
        ├── Llama a /reports/time-analysis al cambiar de pestaña o filtro
        ├── Sección: ventas por día de semana
        ├── Sección: ventas por hora
        ├── Sección: costo laboral por día de semana
        ├── Sección: costo laboral por hora
        └── Sección: cruce costo/ventas (con umbrales configurables)

Frontend nuevo service:
  └── frontend/src/services/reportsService.js → agregar getTimeAnalysis(params)
```

---

## Backend

### Endpoint

`GET /api/v1/reports/time-analysis`

**Params:** `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)  
**Auth:** token_required + admin_required (igual que el resto de reports)

### Función `get_sales_by_weekday(start_date, end_date)`

- Source: `Sale.cerrada` (DateTime), `Sale.total`, `Sale.estado == 'Cerrada'`
- Filtra por `cast(Sale.cerrada, Date)` entre `start_date` y `end_date`
- Agrupa por `extract(dow from Sale.cerrada)` (0=domingo … 6=sábado)
- Para cada bucket: `sum_ventas`, `count_ventas`
- `promedio` = `sum_ventas / cantidad_de_dias_ese_dow_en_el_rango`
  - "cantidad de días ese dow en el rango" = cantidad de veces que ese día de semana aparece entre start_date y end_date (calculado en Python iterando el rango de fechas)

Retorna lista de 7 elementos (un objeto por día de semana, incluyendo días con 0 ventas):
```json
[
  {"dow": 0, "nombre": "Domingo", "sum_ventas": 150000, "count_ventas": 45, "promedio_ventas": 50000, "dias_en_rango": 3},
  ...
]
```

### Función `get_sales_by_hour(start_date, end_date)`

- Source: `Sale.cerrada` (DateTime), `Sale.total`
- Agrupa por `extract(hour from Sale.cerrada)` (0–23)
- Para cada bucket: `sum_ventas`, `count_ventas`, `promedio_ventas = sum_ventas / count_ventas`
- Solo incluye horas con al menos una venta

Retorna lista de hasta 24 elementos:
```json
[
  {"hora": 12, "sum_ventas": 80000, "count_ventas": 25, "promedio_ventas": 3200},
  ...
]
```

### Función `get_labor_by_weekday(start_date, end_date)`

**Tasa horaria:**
```python
tasa_horaria = total_sueldos_periodo / total_horas_periodo
# total_sueldos_periodo: mismo cálculo que get_payroll_metrics()
# total_horas_periodo: sum(shift.hours) para shifts en el período
```

Si `total_horas_periodo == 0` → retorna lista vacía con `tasa_horaria: null`.

**Por día de semana:**
- Consulta `Shift` donde `shift_date` entre `start_date` y `end_date`
- Para cada turno: `costo_turno = shift.hours * tasa_horaria`
- Agrupa por `shift_date.weekday()` (0=lunes … 6=domingo, en Python)
- Para cada DOW: `sum_horas`, `sum_costo`, `count_dias_con_turnos`
- `promedio_costo = sum_costo / cantidad_de_dias_ese_dow_en_el_rango`
- `promedio_horas = sum_horas / cantidad_de_dias_ese_dow_en_el_rango`

**Nota de conversión DOW:** SQLAlchemy `extract(dow)` usa 0=domingo (PostgreSQL). Python `date.weekday()` usa 0=lunes. El endpoint normaliza a 0=lunes…6=domingo en el response para consistencia.

Retorna lista de 7 elementos:
```json
[
  {"dow": 0, "nombre": "Lunes", "sum_horas": 24.0, "sum_costo": 48000, "promedio_horas": 8.0, "promedio_costo": 16000, "dias_en_rango": 3},
  ...
]
```

### Función `get_labor_by_hour(start_date, end_date)`

Para cada turno en el período, distribuir horas y costo entre las franjas horarias cubiertas:

```python
def distribute_shift_hours(start_time, end_time, tasa_horaria):
    """
    Retorna dict {hora: horas_trabajadas} para un turno.
    Maneja fracciones correctamente.
    Ejemplo: 16:00-17:45 → {16: 1.0, 17: 0.75}
    """
    slots = {}
    current = start_time  # time object
    end = end_time        # time object (si end < start, turno cruza medianoche)
    
    while current < end:
        hora = current.hour
        minutos_hasta_fin_de_hora = 60 - current.minute
        minutos_hasta_fin_turno = (end.hour * 60 + end.minute) - (current.hour * 60 + current.minute)
        
        fraccion = min(minutos_hasta_fin_de_hora, minutos_hasta_fin_turno) / 60.0
        slots[hora] = slots.get(hora, 0) + fraccion
        
        # Avanzar al inicio de la próxima hora
        current = time(hora + 1, 0) if hora < 23 else time(0, 0)  # manejo de medianoche
    
    return slots
```

Retorna lista de hasta 24 elementos con horas trabajadas y costo por franja:
```json
[
  {"hora": 9, "sum_horas": 32.5, "sum_costo": 65000, "promedio_horas": 10.83, "promedio_costo": 21667},
  ...
]
```
`promedio` = `sum / cantidad_de_dias_en_rango`.

### Cruce costo/ventas por día de semana

Calculado en el endpoint combinando los resultados de `get_sales_by_weekday` y `get_labor_by_weekday`:

```python
for dow in range(7):
    ventas = sales_by_dow[dow]['sum_ventas']
    costo = labor_by_dow[dow]['sum_costo']
    ratio = costo / ventas if ventas > 0 else None
    cross[dow] = {'dow': dow, 'nombre': ..., 'sum_ventas': ventas, 'sum_costo': costo, 'ratio': ratio}
```

Los umbrales no se calculan en el backend — se evalúan en el frontend con los valores configurados por el usuario.

### Response shape completo

```json
{
  "period": {"start_date": "2026-07-01", "end_date": "2026-07-31"},
  "tasa_horaria": 2000.0,
  "by_weekday": {
    "ventas": [...],
    "labor": [...],
    "cross": [...]
  },
  "by_hour": {
    "ventas": [...],
    "labor": [...]
  }
}
```

---

## Frontend

### Nueva pestaña

En `Reports.jsx`, agregar `"time"` al sistema de tabs existente (`activeTab` state). El tab selector muestra:
- `dashboard` → "Dashboard" (existente)
- `time` → "Día / Hora" (nuevo)

Al activar la pestaña "Día / Hora", se llama a `reportsService.getTimeAnalysis({ start_date, end_date })` con las mismas fechas del filtro activo.

### Secciones de la pestaña

**1. Ventas por día de semana**
Tabla con columnas: Día | Total vendido | Días en rango | Promedio por día

**2. Ventas por hora**
Tabla con columnas: Hora | Total vendido | # Ventas | Ticket promedio

**3. Costo laboral por día de semana**
Tabla con columnas: Día | Horas totales | Costo total | Promedio por día

**4. Costo laboral por hora**
Tabla con columnas: Hora | Horas trabajadas | Costo total | Promedio por día

**5. Cruce costo/ventas por día (con umbrales configurables)**
- Dos inputs numéricos: "Umbral favorable (%)" (default 35) y "Umbral desfavorable (%)" (default 50), manejados con `useState`
- Tabla con columnas: Día | Ventas | Costo laboral | Ratio (%) | Estado
- Estado: verde si ratio < umbral_favorable, amarillo si entre umbrales, rojo si > umbral_desfavorable, gris si sin datos

### Nuevo service method

En `frontend/src/services/reportsService.js`:
```js
getTimeAnalysis: async (params = {}) => {
  const response = await api.get('/reports/time-analysis', { params })
  return response.data
}
```

---

## Archivos a modificar/crear

| Archivo | Acción |
|---------|--------|
| `backend/app/routes/reports.py` | Agregar endpoint + 4 funciones helper |
| `backend/tests/test_time_analysis.py` | Crear — tests unitarios de helpers |
| `frontend/src/pages/Reports.jsx` | Agregar tab "Día/Hora" + componentes de tabla |
| `frontend/src/services/reportsService.js` | Agregar `getTimeAnalysis()` |
