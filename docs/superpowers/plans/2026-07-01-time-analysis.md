# Time Analysis (Día/Hora) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un endpoint `/api/v1/reports/time-analysis` y una nueva pestaña "Día / Hora" en Reports.jsx que muestre ventas y costo laboral desagregados por día de semana y hora, con cruce ratio costo/ventas configurable.

**Architecture:** El backend agrega 5 funciones helper y un nuevo endpoint en `reports.py`. El frontend agrega `getTimeAnalysis` al service y un componente `TimeAnalysisTab` con 5 tablas dentro de una nueva pestaña en `Reports.jsx`. La tasa horaria se calcula como `total_sueldos / total_horas_shifts` para distribuir el costo laboral entre días y franjas.

**Tech Stack:** Python/Flask + SQLAlchemy (backend), React + Tailwind CSS (frontend). Sin nuevas dependencias.

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|----------------|
| `backend/app/routes/reports.py` | Modificar | Agregar `distribute_shift_hours()`, `get_sales_by_weekday()`, `get_sales_by_hour()`, `get_labor_by_weekday()`, `get_labor_by_hour()` y el endpoint `time_analysis()` |
| `backend/tests/test_time_analysis.py` | Crear | Tests unitarios de `distribute_shift_hours` y tests de integración del endpoint |
| `frontend/src/services/reportsService.js` | Modificar | Agregar `getTimeAnalysis(params)` |
| `frontend/src/pages/Reports.jsx` | Modificar | Agregar navegación de tabs, estado `timeData`, y componente `TimeAnalysisTab` |

---

## Task 1: `distribute_shift_hours()` — función pura con TDD

**Files:**
- Modify: `backend/app/routes/reports.py`
- Test: `backend/tests/test_time_analysis.py`

- [ ] **Step 1: Crear el archivo de tests**

Crear `backend/tests/test_time_analysis.py`:

```python
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import time
from app.routes.reports import distribute_shift_hours


def test_distribute_full_hour():
    """Turno de una hora exacta: 10:00-11:00 → {10: 1.0}"""
    result = distribute_shift_hours(time(10, 0), time(11, 0))
    assert result == {10: pytest.approx(1.0)}


def test_distribute_fractional_end():
    """16:00-17:45 → {16: 1.0, 17: 0.75}"""
    result = distribute_shift_hours(time(16, 0), time(17, 45))
    assert result[16] == pytest.approx(1.0)
    assert result[17] == pytest.approx(0.75)


def test_distribute_fractional_start():
    """16:30-18:00 → {16: 0.5, 17: 1.0}"""
    result = distribute_shift_hours(time(16, 30), time(18, 0))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(1.0)


def test_distribute_fractional_both():
    """16:30-17:45 → {16: 0.5, 17: 0.75}"""
    result = distribute_shift_hours(time(16, 30), time(17, 45))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(0.75)


def test_distribute_multi_hour():
    """9:00-12:00 → {9: 1.0, 10: 1.0, 11: 1.0}"""
    result = distribute_shift_hours(time(9, 0), time(12, 0))
    assert result == {9: pytest.approx(1.0), 10: pytest.approx(1.0), 11: pytest.approx(1.0)}


def test_distribute_total_hours_preserved():
    """La suma de las fracciones debe igualar la duración del turno"""
    result = distribute_shift_hours(time(8, 30), time(16, 45))
    total = sum(result.values())
    assert total == pytest.approx(8.25)


def test_distribute_midnight_crossing():
    """Turno que cruza medianoche: 23:00-01:00 → {23: 1.0, 0: 1.0}"""
    result = distribute_shift_hours(time(23, 0), time(1, 0))
    assert result[23] == pytest.approx(1.0)
    assert result[0] == pytest.approx(1.0)
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
cd backend && python -m pytest tests/test_time_analysis.py -v
```

Resultado esperado: `ImportError` — `distribute_shift_hours` no existe aún.

- [ ] **Step 3: Implementar `distribute_shift_hours()` en `reports.py`**

Agregar esta función al final de `backend/app/routes/reports.py`, antes del último `# ==================`:

```python
# ==================== TIME ANALYSIS ====================

def distribute_shift_hours(start_time, end_time):
    """
    Distribuye las horas de un turno entre franjas horarias.
    Retorna dict {hora: fraccion_horas}.
    Ejemplo: start=16:00, end=17:45 → {16: 1.0, 17: 0.75}
    Maneja turnos que cruzan medianoche.
    """
    start_min = start_time.hour * 60 + start_time.minute
    end_min = end_time.hour * 60 + end_time.minute

    if end_min <= start_min:
        end_min += 24 * 60

    slots = {}
    current_min = start_min

    while current_min < end_min:
        hora = (current_min // 60) % 24
        minutos_hasta_fin_hora = 60 - (current_min % 60)
        minutos_restantes = end_min - current_min
        fraccion_min = min(minutos_hasta_fin_hora, minutos_restantes)
        slots[hora] = slots.get(hora, 0) + fraccion_min / 60.0
        current_min += fraccion_min

    return slots
```

- [ ] **Step 4: Verificar que todos los tests pasan**

```bash
cd backend && python -m pytest tests/test_time_analysis.py -v
```

Resultado esperado: 7 tests en PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/reports.py backend/tests/test_time_analysis.py
git commit -m "feat: add distribute_shift_hours() with tests"
```

---

## Task 2: Funciones de ventas — `get_sales_by_weekday` y `get_sales_by_hour`

**Files:**
- Modify: `backend/app/routes/reports.py`
- Modify: `backend/tests/test_time_analysis.py`

Estas funciones requieren DB. Los tests usan el mismo patrón que `backend/tests/test_sales_date_filter.py`.

- [ ] **Step 1: Agregar imports necesarios al tope de `test_time_analysis.py`**

Reemplazar el bloque de imports en `backend/tests/test_time_analysis.py` con:

```python
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import time, date, datetime
from app.routes.reports import distribute_shift_hours, get_sales_by_weekday, get_sales_by_hour
from app import create_app
from app.extensions import db
from app.models.sale import Sale
from app.models.user import User


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield app


# ---- Tests de distribute_shift_hours (sin DB) ----
# (los tests anteriores van acá igual que en el Task 1)

def test_distribute_full_hour():
    result = distribute_shift_hours(time(10, 0), time(11, 0))
    assert result == {10: pytest.approx(1.0)}

def test_distribute_fractional_end():
    result = distribute_shift_hours(time(16, 0), time(17, 45))
    assert result[16] == pytest.approx(1.0)
    assert result[17] == pytest.approx(0.75)

def test_distribute_fractional_start():
    result = distribute_shift_hours(time(16, 30), time(18, 0))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(1.0)

def test_distribute_fractional_both():
    result = distribute_shift_hours(time(16, 30), time(17, 45))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(0.75)

def test_distribute_multi_hour():
    result = distribute_shift_hours(time(9, 0), time(12, 0))
    assert result == {9: pytest.approx(1.0), 10: pytest.approx(1.0), 11: pytest.approx(1.0)}

def test_distribute_total_hours_preserved():
    result = distribute_shift_hours(time(8, 30), time(16, 45))
    assert sum(result.values()) == pytest.approx(8.25)

def test_distribute_midnight_crossing():
    result = distribute_shift_hours(time(23, 0), time(1, 0))
    assert result[23] == pytest.approx(1.0)
    assert result[0] == pytest.approx(1.0)


# ---- Tests de ventas por día de semana y hora ----

def test_sales_by_weekday_sums_correctly(app_ctx):
    """Dos ventas en lunes → sum_ventas correcto, promedio = sum / 1 día lunes en rango"""
    # 2026-07-06 es lunes
    sale1 = Sale(
        fecha=date(2026, 7, 6),
        creacion=datetime(2026, 7, 6, 12, 0, 0),
        cerrada=datetime(2026, 7, 6, 13, 0, 0),
        total=10000,
        estado='Cerrada'
    )
    sale2 = Sale(
        fecha=date(2026, 7, 6),
        creacion=datetime(2026, 7, 6, 20, 0, 0),
        cerrada=datetime(2026, 7, 6, 21, 0, 0),
        total=5000,
        estado='Cerrada'
    )
    db.session.add_all([sale1, sale2])
    db.session.commit()

    result = get_sales_by_weekday(date(2026, 7, 6), date(2026, 7, 6))
    lunes = next(r for r in result if r['dow'] == 0)  # 0=Lunes
    assert lunes['sum_ventas'] == pytest.approx(15000)
    assert lunes['count_ventas'] == 2
    assert lunes['promedio_ventas'] == pytest.approx(15000)  # 1 lunes en rango
    assert lunes['dias_en_rango'] == 1


def test_sales_by_weekday_returns_all_7_days(app_ctx):
    """Siempre retorna los 7 días aunque no haya ventas"""
    result = get_sales_by_weekday(date(2026, 7, 6), date(2026, 7, 6))
    assert len(result) == 7


def test_sales_by_hour_groups_correctly(app_ctx):
    """Dos ventas en hora 12 → sum correcto"""
    sale1 = Sale(
        fecha=date(2026, 7, 7),
        creacion=datetime(2026, 7, 7, 12, 0, 0),
        cerrada=datetime(2026, 7, 7, 12, 30, 0),
        total=3000,
        estado='Cerrada'
    )
    sale2 = Sale(
        fecha=date(2026, 7, 7),
        creacion=datetime(2026, 7, 7, 12, 45, 0),
        cerrada=datetime(2026, 7, 7, 12, 50, 0),
        total=2000,
        estado='Cerrada'
    )
    db.session.add_all([sale1, sale2])
    db.session.commit()

    result = get_sales_by_hour(date(2026, 7, 7), date(2026, 7, 7))
    hora_12 = next((r for r in result if r['hora'] == 12), None)
    assert hora_12 is not None
    assert hora_12['sum_ventas'] == pytest.approx(5000)
    assert hora_12['count_ventas'] == 2
    assert hora_12['promedio_ventas'] == pytest.approx(2500)
```

- [ ] **Step 2: Verificar que los nuevos tests fallan**

```bash
cd backend && python -m pytest tests/test_time_analysis.py::test_sales_by_weekday_sums_correctly -v
```

Resultado esperado: `ImportError` — `get_sales_by_weekday` no existe.

- [ ] **Step 3: Implementar `get_sales_by_weekday` y `get_sales_by_hour` en `reports.py`**

Agregar estas dos funciones después de `distribute_shift_hours()`:

```python
def _days_in_range_by_dow(start_date, end_date):
    """Cuenta cuántas veces aparece cada día de semana (0=lunes) en el rango."""
    counts = {i: 0 for i in range(7)}
    current = start_date
    while current <= end_date:
        counts[current.weekday()] += 1
        current += timedelta(days=1)
    return counts


DOW_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def get_sales_by_weekday(start_date, end_date):
    """Ventas agrupadas por día de semana (0=lunes … 6=domingo)."""
    from sqlalchemy import cast
    from sqlalchemy.types import Date as SQLDate

    days_in_range = _days_in_range_by_dow(start_date, end_date)

    # extract(dow) en PostgreSQL: 0=domingo, 1=lunes, …, 6=sábado
    rows = db.session.query(
        func.extract('dow', Sale.cerrada).label('dow_pg'),
        func.sum(Sale.total).label('sum_ventas'),
        func.count(Sale.id).label('count_ventas')
    ).filter(
        cast(Sale.cerrada, SQLDate) >= start_date,
        cast(Sale.cerrada, SQLDate) <= end_date,
        Sale.estado == 'Cerrada',
        Sale.cerrada.isnot(None)
    ).group_by('dow_pg').all()

    # Convertir DOW de PostgreSQL (0=dom) a Python (0=lun)
    by_dow = {i: {'sum_ventas': 0.0, 'count_ventas': 0} for i in range(7)}
    for row in rows:
        py_dow = (int(row.dow_pg) - 1) % 7  # 0(dom)->6, 1(lun)->0, ..., 6(sab)->5
        by_dow[py_dow]['sum_ventas'] = float(row.sum_ventas or 0)
        by_dow[py_dow]['count_ventas'] = row.count_ventas or 0

    output = []
    for dow in range(7):
        dias = days_in_range[dow]
        sum_v = by_dow[dow]['sum_ventas']
        output.append({
            'dow': dow,
            'nombre': DOW_NAMES[dow],
            'sum_ventas': round(sum_v, 2),
            'count_ventas': by_dow[dow]['count_ventas'],
            'promedio_ventas': round(sum_v / dias, 2) if dias > 0 else 0,
            'dias_en_rango': dias
        })
    return output


def get_sales_by_hour(start_date, end_date):
    """Ventas agrupadas por hora del día (0–23)."""
    from sqlalchemy import cast
    from sqlalchemy.types import Date as SQLDate

    rows = db.session.query(
        func.extract('hour', Sale.cerrada).label('hora'),
        func.sum(Sale.total).label('sum_ventas'),
        func.count(Sale.id).label('count_ventas')
    ).filter(
        cast(Sale.cerrada, SQLDate) >= start_date,
        cast(Sale.cerrada, SQLDate) <= end_date,
        Sale.estado == 'Cerrada',
        Sale.cerrada.isnot(None)
    ).group_by('hora').order_by('hora').all()

    output = []
    for row in rows:
        sum_v = float(row.sum_ventas or 0)
        count_v = row.count_ventas or 0
        output.append({
            'hora': int(row.hora),
            'sum_ventas': round(sum_v, 2),
            'count_ventas': count_v,
            'promedio_ventas': round(sum_v / count_v, 2) if count_v > 0 else 0
        })
    return output
```

- [ ] **Step 4: Correr los tests**

```bash
cd backend && python -m pytest tests/test_time_analysis.py -v
```

Resultado esperado: todos en PASSED (7 de distribute + 3 de ventas = 10 total).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/reports.py backend/tests/test_time_analysis.py
git commit -m "feat: add get_sales_by_weekday and get_sales_by_hour"
```

---

## Task 3: Funciones de labor + endpoint `time-analysis`

**Files:**
- Modify: `backend/app/routes/reports.py`
- Modify: `backend/tests/test_time_analysis.py`

- [ ] **Step 1: Agregar tests de labor y del endpoint a `test_time_analysis.py`**

Agregar al final de `backend/tests/test_time_analysis.py`:

```python
from app.routes.reports import get_labor_by_weekday, get_labor_by_hour
from app.models.shift import Shift
from app.models.payroll import Payroll
from app.models.employee import Employee


def _make_employee(name='Test'):
    from app.models.employee import Employee
    emp = Employee(
        first_name=name,
        last_name='Test',
        email=f'{name.lower()}@test.com',
        role='employee'
    )
    db.session.add(emp)
    db.session.flush()
    return emp


def test_get_labor_by_weekday_distributes_cost(app_ctx):
    """Turno de 8h un lunes con tasa 1000/h → sum_costo=8000 para lunes"""
    emp = _make_employee('L1')
    # 2026-07-06 es lunes
    shift = Shift(
        employee_id=emp.id,
        schedule_id=1,
        shift_date=date(2026, 7, 6),
        start_time=time(9, 0),
        end_time=time(17, 0),
        hours=8.0
    )
    db.session.add(shift)
    db.session.commit()

    result = get_labor_by_weekday(date(2026, 7, 6), date(2026, 7, 6), tasa_horaria=1000)
    lunes = next(r for r in result if r['dow'] == 0)
    assert lunes['sum_horas'] == pytest.approx(8.0)
    assert lunes['sum_costo'] == pytest.approx(8000.0)
    assert lunes['promedio_horas'] == pytest.approx(8.0)   # 1 lunes en rango
    assert lunes['promedio_costo'] == pytest.approx(8000.0)


def test_get_labor_by_weekday_returns_7_days(app_ctx):
    result = get_labor_by_weekday(date(2026, 7, 6), date(2026, 7, 6), tasa_horaria=1000)
    assert len(result) == 7


def test_get_labor_by_hour_distributes_fractional(app_ctx):
    """Turno 16:00-17:45 con tasa 1000/h → slot 16h=1000, slot 17h=750"""
    emp = _make_employee('H1')
    shift = Shift(
        employee_id=emp.id,
        schedule_id=1,
        shift_date=date(2026, 7, 7),
        start_time=time(16, 0),
        end_time=time(17, 45),
        hours=1.75
    )
    db.session.add(shift)
    db.session.commit()

    result = get_labor_by_hour(date(2026, 7, 7), date(2026, 7, 7), tasa_horaria=1000)
    slot_16 = next((r for r in result if r['hora'] == 16), None)
    slot_17 = next((r for r in result if r['hora'] == 17), None)
    assert slot_16 is not None
    assert slot_16['sum_costo'] == pytest.approx(1000.0)
    assert slot_17 is not None
    assert slot_17['sum_costo'] == pytest.approx(750.0)
```

- [ ] **Step 2: Verificar que los nuevos tests fallan**

```bash
cd backend && python -m pytest tests/test_time_analysis.py::test_get_labor_by_weekday_distributes_cost -v
```

Resultado esperado: `ImportError`.

- [ ] **Step 3: Implementar `get_labor_by_weekday` y `get_labor_by_hour` en `reports.py`**

Agregar después de `get_sales_by_hour()`. También agregar `from app.models.shift import Shift` en los imports del archivo (buscar el bloque de imports al tope, agregar junto a los otros modelos):

```python
from app.models.shift import Shift
```

Luego las funciones:

```python
def get_labor_by_weekday(start_date, end_date, tasa_horaria):
    """Costo laboral por día de semana (0=lunes … 6=domingo)."""
    days_in_range = _days_in_range_by_dow(start_date, end_date)

    shifts = Shift.query.filter(
        Shift.shift_date >= start_date,
        Shift.shift_date <= end_date
    ).all()

    by_dow = {i: {'sum_horas': 0.0, 'sum_costo': 0.0} for i in range(7)}
    for shift in shifts:
        dow = shift.shift_date.weekday()  # 0=lunes
        horas = float(shift.hours)
        by_dow[dow]['sum_horas'] += horas
        by_dow[dow]['sum_costo'] += horas * tasa_horaria

    output = []
    for dow in range(7):
        dias = days_in_range[dow]
        output.append({
            'dow': dow,
            'nombre': DOW_NAMES[dow],
            'sum_horas': round(by_dow[dow]['sum_horas'], 2),
            'sum_costo': round(by_dow[dow]['sum_costo'], 2),
            'promedio_horas': round(by_dow[dow]['sum_horas'] / dias, 2) if dias > 0 else 0,
            'promedio_costo': round(by_dow[dow]['sum_costo'] / dias, 2) if dias > 0 else 0,
            'dias_en_rango': dias
        })
    return output


def get_labor_by_hour(start_date, end_date, tasa_horaria):
    """Costo laboral por franja horaria, distribuyendo fracciones por turno."""
    total_dias = (end_date - start_date).days + 1

    shifts = Shift.query.filter(
        Shift.shift_date >= start_date,
        Shift.shift_date <= end_date
    ).all()

    by_hour = {}
    for shift in shifts:
        slots = distribute_shift_hours(shift.start_time, shift.end_time)
        for hora, fraccion in slots.items():
            if hora not in by_hour:
                by_hour[hora] = {'sum_horas': 0.0, 'sum_costo': 0.0}
            by_hour[hora]['sum_horas'] += fraccion
            by_hour[hora]['sum_costo'] += fraccion * tasa_horaria

    output = []
    for hora in sorted(by_hour.keys()):
        output.append({
            'hora': hora,
            'sum_horas': round(by_hour[hora]['sum_horas'], 2),
            'sum_costo': round(by_hour[hora]['sum_costo'], 2),
            'promedio_horas': round(by_hour[hora]['sum_horas'] / total_dias, 2),
            'promedio_costo': round(by_hour[hora]['sum_costo'] / total_dias, 2)
        })
    return output
```

- [ ] **Step 4: Agregar el endpoint `time_analysis` en `reports.py`**

Agregar al final del archivo (antes de las rutas de expense-categories o al final del bloque TIME ANALYSIS):

```python
@bp.route('/time-analysis', methods=['GET'])
@token_required
@admin_required
def time_analysis(current_user):
    """Análisis de ventas y costo laboral por día de semana y hora."""
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))

    if not start_date:
        start_date, end_date = get_period_dates('mensual')
    if not end_date:
        end_date = date.today()

    payroll_data = get_payroll_metrics(start_date, end_date)
    total_horas = payroll_data['horas']
    total_sueldos = payroll_data['total']
    tasa_horaria = total_sueldos / total_horas if total_horas > 0 else 0

    sales_wd = get_sales_by_weekday(start_date, end_date)
    sales_hr = get_sales_by_hour(start_date, end_date)
    labor_wd = get_labor_by_weekday(start_date, end_date, tasa_horaria)
    labor_hr = get_labor_by_hour(start_date, end_date, tasa_horaria)

    cross = []
    for i in range(7):
        ventas = sales_wd[i]['sum_ventas']
        costo = labor_wd[i]['sum_costo']
        cross.append({
            'dow': i,
            'nombre': DOW_NAMES[i],
            'sum_ventas': ventas,
            'sum_costo': costo,
            'ratio': round(costo / ventas * 100, 1) if ventas > 0 else None
        })

    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'tasa_horaria': round(tasa_horaria, 2),
        'by_weekday': {
            'ventas': sales_wd,
            'labor': labor_wd,
            'cross': cross
        },
        'by_hour': {
            'ventas': sales_hr,
            'labor': labor_hr
        }
    }), 200
```

- [ ] **Step 5: Verificar que todos los tests pasan**

```bash
cd backend && python -m pytest tests/test_time_analysis.py -v
```

Resultado esperado: 13 tests en PASSED.

- [ ] **Step 6: Verificar que la importación del módulo funciona**

```bash
cd backend && python -c "from app.routes.reports import time_analysis, get_labor_by_weekday, get_labor_by_hour; print('OK')"
```

Resultado esperado: `OK`

- [ ] **Step 7: Commit**

```bash
git add backend/app/routes/reports.py backend/tests/test_time_analysis.py
git commit -m "feat: add time-analysis endpoint with labor and sales helpers"
```

---

## Task 4: Frontend — service + tab + tablas

**Files:**
- Modify: `frontend/src/services/reportsService.js`
- Modify: `frontend/src/pages/Reports.jsx`

- [ ] **Step 1: Agregar `getTimeAnalysis` al service**

En `frontend/src/services/reportsService.js`, agregar antes del cierre del objeto `reportsService`:

```js
  getTimeAnalysis: async (params = {}) => {
    const response = await api.get('/reports/time-analysis', { params })
    return response.data
  },
```

- [ ] **Step 2: Agregar estado y carga de datos en `Reports.jsx`**

En el componente `Reports`, agregar después de `const [activeTab, setActiveTab] = useState('dashboard')` (línea ~24):

```jsx
const [timeData, setTimeData] = useState(null)
const [timeLoading, setTimeLoading] = useState(false)
const [timeError, setTimeError] = useState(null)
```

Agregar la función `loadTimeAnalysis` después de `loadDashboard`:

```jsx
const loadTimeAnalysis = async () => {
  try {
    setTimeLoading(true)
    setTimeError(null)
    let startStr, endStr
    if (filterMode === 'range' && startDate && endDate) {
      startStr = startDate
      endStr = endDate
    } else if (filterMode === 'month') {
      const start = new Date(selectedMonth.year, selectedMonth.month - 1, 1)
      const end = new Date(selectedMonth.year, selectedMonth.month, 0)
      startStr = start.toISOString().split('T')[0]
      endStr = end.toISOString().split('T')[0]
    } else {
      const [s, e] = (() => {
        const now = new Date()
        const start = new Date(now.getFullYear(), now.getMonth(), 1)
        const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
        return [start.toISOString().split('T')[0], end.toISOString().split('T')[0]]
      })()
      startStr = s
      endStr = e
    }
    const data = await reportsService.getTimeAnalysis({ start_date: startStr, end_date: endStr })
    setTimeData(data)
  } catch (err) {
    console.error('Error loading time analysis:', err)
    setTimeError('Error al cargar el análisis por día/hora')
  } finally {
    setTimeLoading(false)
  }
}
```

Modificar el `useEffect` existente (líneas ~26-33) para incluir la carga de tiempo cuando la pestaña activa sea `'time'`:

```jsx
useEffect(() => {
  if (activeTab === 'dashboard') {
    if (filterMode === 'period') loadDashboard()
    else if (filterMode === 'month') loadDashboard()
  } else if (activeTab === 'time') {
    loadTimeAnalysis()
  }
}, [period, filterMode, selectedMonth, activeTab])
```

- [ ] **Step 3: Agregar navegación de tabs en el JSX**

En el return del componente `Reports`, buscar el div `{/* Header */}` (línea ~225). Dentro de ese div, después del bloque de botones (después del botón "Metas"), agregar la navegación de tabs:

```jsx
{/* Tab navigation */}
<div className="flex items-center bg-gray-100 rounded-lg p-1 self-start">
  <button
    onClick={() => setActiveTab('dashboard')}
    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
      activeTab === 'dashboard'
        ? 'bg-white text-gray-900 shadow-sm'
        : 'text-gray-600 hover:text-gray-900'
    }`}
  >
    Dashboard
  </button>
  <button
    onClick={() => setActiveTab('time')}
    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
      activeTab === 'time'
        ? 'bg-white text-gray-900 shadow-sm'
        : 'text-gray-600 hover:text-gray-900'
    }`}
  >
    Día / Hora
  </button>
</div>
```

- [ ] **Step 4: Condicionar el contenido existente a `activeTab === 'dashboard'`**

El bloque `{dashboard && (<> ... </>)}` (alrededor de línea 386) debe envolverse en:

```jsx
{activeTab === 'dashboard' && dashboard && (
  <>
    {/* ... todo el contenido existente del dashboard ... */}
  </>
)}
```

- [ ] **Step 5: Agregar el componente `TimeAnalysisTab`**

Agregar este componente en `Reports.jsx` **antes** de `ApalancamientoCard` (que está antes de `GoalsModal`):

```jsx
const TimeAnalysisTab = ({ data, loading, error }) => {
  const [umbralFavorable, setUmbralFavorable] = useState(35)
  const [umbralDesfavorable, setUmbralDesfavorable] = useState(50)

  const formatCurrency = (value) =>
    new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0)

  const formatHour = (h) => `${String(h).padStart(2, '0')}:00`

  const ratioColor = (ratio) => {
    if (ratio === null || ratio === undefined) return 'text-gray-400'
    if (ratio < umbralFavorable) return 'text-green-600 font-bold'
    if (ratio <= umbralDesfavorable) return 'text-amber-600 font-bold'
    return 'text-red-600 font-bold'
  }

  const ratioBg = (ratio) => {
    if (ratio === null || ratio === undefined) return ''
    if (ratio < umbralFavorable) return 'bg-green-50'
    if (ratio <= umbralDesfavorable) return 'bg-amber-50'
    return 'bg-red-50'
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-[300px]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
    </div>
  )

  if (error) return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
  )

  if (!data) return null

  const TableSection = ({ title, icon, children }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Tasa horaria */}
      {data.tasa_horaria > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-800">
          Tasa horaria del período: <strong>{formatCurrency(data.tasa_horaria)}/h</strong>
        </div>
      )}

      {/* Ventas por día de semana */}
      <TableSection title="Ventas por día de semana" icon={<ShoppingCart size={20} className="text-green-600" />}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-500 font-medium">Día</th>
                <th className="text-right py-2 text-gray-500 font-medium">Total vendido</th>
                <th className="text-right py-2 text-gray-500 font-medium">Días en rango</th>
                <th className="text-right py-2 text-gray-500 font-medium">Promedio / día</th>
              </tr>
            </thead>
            <tbody>
              {data.by_weekday.ventas.map((row) => (
                <tr key={row.dow} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 font-medium text-gray-900">{row.nombre}</td>
                  <td className="py-2 text-right text-green-600">{formatCurrency(row.sum_ventas)}</td>
                  <td className="py-2 text-right text-gray-500">{row.dias_en_rango}</td>
                  <td className="py-2 text-right text-gray-700">{formatCurrency(row.promedio_ventas)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </TableSection>

      {/* Ventas por hora */}
      <TableSection title="Ventas por hora del día" icon={<Clock size={20} className="text-blue-600" />}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-500 font-medium">Hora</th>
                <th className="text-right py-2 text-gray-500 font-medium">Total vendido</th>
                <th className="text-right py-2 text-gray-500 font-medium"># Ventas</th>
                <th className="text-right py-2 text-gray-500 font-medium">Ticket promedio</th>
              </tr>
            </thead>
            <tbody>
              {data.by_hour.ventas.length === 0 ? (
                <tr><td colSpan={4} className="py-4 text-center text-gray-400">Sin datos</td></tr>
              ) : data.by_hour.ventas.map((row) => (
                <tr key={row.hora} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 font-medium text-gray-900">{formatHour(row.hora)}</td>
                  <td className="py-2 text-right text-green-600">{formatCurrency(row.sum_ventas)}</td>
                  <td className="py-2 text-right text-gray-500">{row.count_ventas}</td>
                  <td className="py-2 text-right text-gray-700">{formatCurrency(row.promedio_ventas)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </TableSection>

      {/* Costo laboral por día de semana */}
      <TableSection title="Costo laboral por día de semana" icon={<Users size={20} className="text-purple-600" />}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-500 font-medium">Día</th>
                <th className="text-right py-2 text-gray-500 font-medium">Horas totales</th>
                <th className="text-right py-2 text-gray-500 font-medium">Costo total</th>
                <th className="text-right py-2 text-gray-500 font-medium">Promedio / día</th>
              </tr>
            </thead>
            <tbody>
              {data.by_weekday.labor.map((row) => (
                <tr key={row.dow} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 font-medium text-gray-900">{row.nombre}</td>
                  <td className="py-2 text-right text-gray-500">{row.sum_horas}h</td>
                  <td className="py-2 text-right text-purple-600">{formatCurrency(row.sum_costo)}</td>
                  <td className="py-2 text-right text-gray-700">{formatCurrency(row.promedio_costo)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </TableSection>

      {/* Costo laboral por hora */}
      <TableSection title="Costo laboral por hora del día" icon={<Clock size={20} className="text-purple-600" />}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-500 font-medium">Hora</th>
                <th className="text-right py-2 text-gray-500 font-medium">Horas trabajadas</th>
                <th className="text-right py-2 text-gray-500 font-medium">Costo total</th>
                <th className="text-right py-2 text-gray-500 font-medium">Promedio / día</th>
              </tr>
            </thead>
            <tbody>
              {data.by_hour.labor.length === 0 ? (
                <tr><td colSpan={4} className="py-4 text-center text-gray-400">Sin datos de turnos</td></tr>
              ) : data.by_hour.labor.map((row) => (
                <tr key={row.hora} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 font-medium text-gray-900">{formatHour(row.hora)}</td>
                  <td className="py-2 text-right text-gray-500">{row.sum_horas}h</td>
                  <td className="py-2 text-right text-purple-600">{formatCurrency(row.sum_costo)}</td>
                  <td className="py-2 text-right text-gray-700">{formatCurrency(row.promedio_costo)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </TableSection>

      {/* Cruce costo/ventas por día */}
      <TableSection title="Cruce costo laboral / ventas por día" icon={<Scale size={20} className="text-indigo-600" />}>
        {/* Configuración de umbrales */}
        <div className="flex flex-wrap items-center gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-600 font-medium">Umbrales:</span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-green-700">Favorable si ratio &lt;</span>
            <input
              type="number"
              min="1"
              max="100"
              value={umbralFavorable}
              onChange={(e) => setUmbralFavorable(Number(e.target.value))}
              className="w-16 border border-gray-300 rounded px-2 py-1 text-sm text-center"
            />
            <span className="text-xs text-gray-500">%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-red-700">Desfavorable si ratio &gt;</span>
            <input
              type="number"
              min="1"
              max="100"
              value={umbralDesfavorable}
              onChange={(e) => setUmbralDesfavorable(Number(e.target.value))}
              className="w-16 border border-gray-300 rounded px-2 py-1 text-sm text-center"
            />
            <span className="text-xs text-gray-500">%</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-500 font-medium">Día</th>
                <th className="text-right py-2 text-gray-500 font-medium">Ventas</th>
                <th className="text-right py-2 text-gray-500 font-medium">Costo laboral</th>
                <th className="text-right py-2 text-gray-500 font-medium">Ratio</th>
                <th className="text-center py-2 text-gray-500 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {data.by_weekday.cross.map((row) => (
                <tr key={row.dow} className={`border-b border-gray-50 ${ratioBg(row.ratio)}`}>
                  <td className="py-2 font-medium text-gray-900">{row.nombre}</td>
                  <td className="py-2 text-right text-green-600">{formatCurrency(row.sum_ventas)}</td>
                  <td className="py-2 text-right text-purple-600">{formatCurrency(row.sum_costo)}</td>
                  <td className={`py-2 text-right ${ratioColor(row.ratio)}`}>
                    {row.ratio !== null ? `${row.ratio}%` : '—'}
                  </td>
                  <td className="py-2 text-center">
                    {row.ratio === null ? (
                      <span className="text-gray-400 text-xs">Sin datos</span>
                    ) : row.ratio < umbralFavorable ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-800">Favorable</span>
                    ) : row.ratio <= umbralDesfavorable ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-800">Neutro</span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-800">Desfavorable</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </TableSection>
    </div>
  )
}
```

- [ ] **Step 6: Renderizar `TimeAnalysisTab` en el JSX de `Reports`**

En el return del componente `Reports`, después del bloque del dashboard (`{activeTab === 'dashboard' && ...}`), agregar:

```jsx
{activeTab === 'time' && (
  <TimeAnalysisTab data={timeData} loading={timeLoading} error={timeError} />
)}
```

- [ ] **Step 7: Verificar que el build compila sin errores**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Resultado esperado: sin errores (solo los warnings de chunk size preexistentes).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/services/reportsService.js frontend/src/pages/Reports.jsx
git commit -m "feat: add Día/Hora tab with time-analysis tables"
```
