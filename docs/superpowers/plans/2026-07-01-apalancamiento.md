# Apalancamiento Operativo (GAO) + Simulador Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar al dashboard de reportes el Grado de Apalancamiento Operativo (GAO) con un simulador interactivo de precio vs. volumen para ayudar a decidir entre defender el precio o generar más volumen.

**Architecture:** El backend expone el GAO como nuevo campo en el response de `GET /api/v1/reports/dashboard`. El frontend agrega un componente `ApalancamientoCard` en `Reports.jsx` que muestra el GAO y un simulador con dos sliders (Δvolumen, Δprecio) cuya lógica corre enteramente en el cliente.

**Tech Stack:** Python/Flask (backend), React + Tailwind CSS (frontend), sin nuevas dependencias.

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|----------------|
| `backend/app/routes/reports.py` | Modificar | Agregar `calculate_gao()` y llamarla en `get_dashboard()` |
| `backend/tests/test_gao.py` | Crear | Tests unitarios de `calculate_gao()` |
| `frontend/src/pages/Reports.jsx` | Modificar | Agregar componente `ApalancamientoCard` con GAO display y simulador |

---

## Task 1: Función `calculate_gao()` en el backend

**Files:**
- Modify: `backend/app/routes/reports.py`
- Test: `backend/tests/test_gao.py`

- [ ] **Step 1: Crear el archivo de tests**

Crear `backend/tests/test_gao.py` con el siguiente contenido:

```python
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.routes.reports import calculate_gao


def test_gao_normal_case():
    """GAO = margen_contribucion_total / resultado_operativo"""
    result = calculate_gao(
        ventas=100000,
        costos_variables=40000,   # gastos directos
        costos_fijos=30000,       # gastos indirectos + sueldos
        resultado_neto=30000      # 100k - 40k - 30k
    )
    assert result['estado'] == 'ok'
    assert result['gao'] == pytest.approx(2.0, rel=1e-3)
    assert result['margen_contribucion_total'] == 60000
    assert result['resultado_operativo'] == 30000
    assert result['interpretacion'] == 'medio'
    assert result['recomendacion'] == 'equilibrado'


def test_gao_alto():
    """GAO > 3 → alto → recomendacion volumen"""
    result = calculate_gao(
        ventas=100000,
        costos_variables=20000,
        costos_fijos=55000,
        resultado_neto=25000
    )
    assert result['estado'] == 'ok'
    # margen_contribucion_total = 80000, gao = 80000/25000 = 3.2
    assert result['gao'] == pytest.approx(3.2, rel=1e-3)
    assert result['interpretacion'] == 'alto'
    assert result['recomendacion'] == 'volumen'


def test_gao_bajo():
    """GAO < 1.5 → bajo → recomendacion precio"""
    result = calculate_gao(
        ventas=100000,
        costos_variables=10000,
        costos_fijos=20000,
        resultado_neto=70000
    )
    assert result['estado'] == 'ok'
    # margen_contribucion_total = 90000, gao = 90000/70000 ≈ 1.286
    assert result['gao'] == pytest.approx(90000 / 70000, rel=1e-3)
    assert result['interpretacion'] == 'bajo'
    assert result['recomendacion'] == 'precio'


def test_gao_en_perdida():
    """resultado_neto <= 0 → estado en_perdida, gao null"""
    result = calculate_gao(
        ventas=100000,
        costos_variables=60000,
        costos_fijos=50000,
        resultado_neto=-10000
    )
    assert result['estado'] == 'en_perdida'
    assert result['gao'] is None
    assert result['recomendacion'] is None


def test_gao_margen_negativo():
    """costos_variables >= ventas → estado margen_negativo"""
    result = calculate_gao(
        ventas=50000,
        costos_variables=60000,
        costos_fijos=10000,
        resultado_neto=-20000
    )
    assert result['estado'] == 'margen_negativo'
    assert result['gao'] is None


def test_gao_sin_ventas():
    """ventas = 0 → estado sin_datos"""
    result = calculate_gao(
        ventas=0,
        costos_variables=0,
        costos_fijos=10000,
        resultado_neto=-10000
    )
    assert result['estado'] == 'sin_datos'
    assert result['gao'] is None
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```bash
cd backend
python -m pytest tests/test_gao.py -v
```

Resultado esperado: `ImportError` o `AttributeError` — `calculate_gao` no existe todavía.

- [ ] **Step 3: Implementar `calculate_gao()` en `reports.py`**

Agregar esta función en `backend/app/routes/reports.py`, después de `calculate_break_even_point()` (alrededor de la línea 343):

```python
def calculate_gao(ventas, costos_variables, costos_fijos, resultado_neto):
    """
    Calcula el Grado de Apalancamiento Operativo (GAO).

    GAO = Margen de Contribución Total / Resultado Operativo
    Margen de Contribución Total = Ventas - Costos Variables
    """
    if ventas <= 0:
        return {
            'gao': None,
            'margen_contribucion_total': 0,
            'resultado_operativo': resultado_neto,
            'interpretacion': None,
            'recomendacion': None,
            'estado': 'sin_datos'
        }

    margen_contribucion_total = ventas - costos_variables

    if margen_contribucion_total <= 0:
        return {
            'gao': None,
            'margen_contribucion_total': round(margen_contribucion_total, 2),
            'resultado_operativo': round(resultado_neto, 2),
            'interpretacion': None,
            'recomendacion': None,
            'estado': 'margen_negativo'
        }

    if resultado_neto <= 0:
        return {
            'gao': None,
            'margen_contribucion_total': round(margen_contribucion_total, 2),
            'resultado_operativo': round(resultado_neto, 2),
            'interpretacion': None,
            'recomendacion': None,
            'estado': 'en_perdida'
        }

    gao = margen_contribucion_total / resultado_neto

    if gao < 1.5:
        interpretacion = 'bajo'
        recomendacion = 'precio'
    elif gao <= 3.0:
        interpretacion = 'medio'
        recomendacion = 'equilibrado'
    else:
        interpretacion = 'alto'
        recomendacion = 'volumen'

    return {
        'gao': round(gao, 2),
        'margen_contribucion_total': round(margen_contribucion_total, 2),
        'resultado_operativo': round(resultado_neto, 2),
        'interpretacion': interpretacion,
        'recomendacion': recomendacion,
        'estado': 'ok'
    }
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

```bash
cd backend
python -m pytest tests/test_gao.py -v
```

Resultado esperado: todos los tests en `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/reports.py backend/tests/test_gao.py
git commit -m "feat: add calculate_gao() to reports"
```

---

## Task 2: Integrar `calculate_gao()` en el endpoint `/dashboard`

**Files:**
- Modify: `backend/app/routes/reports.py` — función `get_dashboard()` (línea ~125)

- [ ] **Step 1: Agregar la llamada a `calculate_gao()` dentro de `get_dashboard()`**

En `get_dashboard()`, después de la línea donde se calcula `punto_equilibrio` (alrededor de línea 154), agregar:

```python
    # Calcular GAO (Grado de Apalancamiento Operativo)
    apalancamiento = calculate_gao(
        ventas=total_ingresos,
        costos_variables=expenses_data['directos'],
        costos_fijos=expenses_data['indirectos'] + payroll_data['total'],
        resultado_neto=resultado_neto
    )
```

- [ ] **Step 2: Agregar `apalancamiento` al return del endpoint**

En el `return jsonify({...})` de `get_dashboard()`, agregar al final del dict (antes del cierre `}`), después del campo `'goals'`:

```python
        'apalancamiento': apalancamiento,
```

El bloque return completo queda así (mostrado parcialmente para ubicación):

```python
    return jsonify({
        'period': { ... },
        'ventas': { ... },
        'gastos': { ... },
        'sueldos': { ... },
        'rentabilidad': { ... },
        'punto_equilibrio': calculate_break_even_point(...),
        'goals': goals,
        'apalancamiento': apalancamiento,
    }), 200
```

- [ ] **Step 3: Verificar el endpoint manualmente**

Con el servidor corriendo (`cd backend && flask run`), ejecutar:

```bash
curl -s -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/v1/reports/dashboard?period=mensual" \
  | python -m json.tool | grep -A 10 '"apalancamiento"'
```

Resultado esperado: objeto `apalancamiento` con campos `gao`, `interpretacion`, `recomendacion`, `estado`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/reports.py
git commit -m "feat: expose apalancamiento in dashboard endpoint"
```

---

## Task 3: Componente `ApalancamientoCard` en el frontend

**Files:**
- Modify: `frontend/src/pages/Reports.jsx`

- [ ] **Step 1: Agregar el componente `ApalancamientoCard`**

En `frontend/src/pages/Reports.jsx`, agregar este componente **antes** del componente `GoalsModal` (alrededor de la línea 805):

```jsx
const ApalancamientoCard = ({ dashboard }) => {
  const [deltaVolumen, setDeltaVolumen] = useState(0)
  const [deltaPrecio, setDeltaPrecio] = useState(0)

  const apal = dashboard?.apalancamiento
  const ventas = dashboard?.ventas?.total || 0
  const costosVariables = dashboard?.punto_equilibrio?.costos_variables || 0
  const costosFijos = dashboard?.punto_equilibrio?.costos_fijos || 0
  const resultadoActual = dashboard?.rentabilidad?.resultado_neto || 0

  const nuevasVentas = ventas * (1 + deltaVolumen / 100) * (1 + deltaPrecio / 100)
  const nuevosCostosVar = costosVariables * (1 + deltaVolumen / 100)
  const nuevoResultado = nuevasVentas - nuevosCostosVar - costosFijos
  const variacionAbsoluta = nuevoResultado - resultadoActual
  const variacionPct = resultadoActual !== 0
    ? ((variacionAbsoluta / Math.abs(resultadoActual)) * 100)
    : 0

  const formatCurrency = (value) =>
    new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)

  const gaoColor = {
    bajo: 'text-green-600',
    medio: 'text-amber-600',
    alto: 'text-orange-600'
  }

  const gaoBackground = {
    bajo: 'bg-green-50 border-green-200',
    medio: 'bg-amber-50 border-amber-200',
    alto: 'bg-orange-50 border-orange-200'
  }

  const recomendacionLabel = {
    precio: 'Defender el precio',
    volumen: 'Generar más volumen',
    equilibrado: 'Estrategia equilibrada'
  }

  const recomendacionBadge = {
    precio: 'bg-green-100 text-green-800',
    volumen: 'bg-blue-100 text-blue-800',
    equilibrado: 'bg-amber-100 text-amber-800'
  }

  const renderGaoStatus = () => {
    if (!apal || apal.estado === 'sin_datos') {
      return (
        <div className="text-center py-4 text-gray-500">
          <p className="text-sm">Sin datos suficientes para calcular el GAO</p>
        </div>
      )
    }
    if (apal.estado === 'en_perdida') {
      return (
        <div className="text-center py-4">
          <p className="text-sm text-red-600 font-medium">Operando con pérdida — el GAO no aplica</p>
          <p className="text-xs text-gray-500 mt-1">Primero alcanzá el punto de equilibrio</p>
        </div>
      )
    }
    if (apal.estado === 'margen_negativo') {
      return (
        <div className="text-center py-4">
          <p className="text-sm text-red-600 font-medium">Margen de contribución negativo</p>
          <p className="text-xs text-gray-500 mt-1">Los costos variables superan las ventas</p>
        </div>
      )
    }
    return (
      <div className={`rounded-lg border p-4 ${gaoBackground[apal.interpretacion]}`}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs text-gray-500 mb-1">Grado de Apalancamiento Operativo</p>
            <p className={`text-4xl font-bold ${gaoColor[apal.interpretacion]}`}>
              {apal.gao}x
            </p>
          </div>
          <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${recomendacionBadge[apal.recomendacion]}`}>
            {recomendacionLabel[apal.recomendacion]}
          </span>
        </div>
        <p className="text-sm text-gray-600">
          Cada <strong>1%</strong> de aumento en ventas mejora tu ganancia un{' '}
          <strong className={gaoColor[apal.interpretacion]}>{apal.gao}%</strong>
        </p>
      </div>
    )
  }

  const simulatorDisabled = !apal || apal.estado !== 'ok' || ventas === 0

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <TrendingUp size={20} className="text-indigo-600" />
        Apalancamiento Operativo
      </h3>

      {renderGaoStatus()}

      {/* Simulador */}
      <div className={`mt-6 ${simulatorDisabled ? 'opacity-40 pointer-events-none' : ''}`}>
        <h4 className="text-sm font-semibold text-gray-700 mb-4">Simulador: ¿Qué pasa si...?</h4>

        <div className="space-y-5">
          {/* Slider Volumen */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm text-gray-600">Cambio en volumen de ventas</label>
              <span className={`text-sm font-bold ${deltaVolumen >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {deltaVolumen >= 0 ? '+' : ''}{deltaVolumen}%
              </span>
            </div>
            <input
              type="range"
              min="-30"
              max="30"
              step="1"
              value={deltaVolumen}
              onChange={(e) => setDeltaVolumen(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>-30%</span>
              <span>0%</span>
              <span>+30%</span>
            </div>
          </div>

          {/* Slider Precio */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm text-gray-600">Cambio en precio (ticket promedio)</label>
              <span className={`text-sm font-bold ${deltaPrecio >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {deltaPrecio >= 0 ? '+' : ''}{deltaPrecio}%
              </span>
            </div>
            <input
              type="range"
              min="-30"
              max="30"
              step="1"
              value={deltaPrecio}
              onChange={(e) => setDeltaPrecio(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>-30%</span>
              <span>0%</span>
              <span>+30%</span>
            </div>
          </div>
        </div>

        {/* Resultado proyectado */}
        <div className={`mt-5 p-4 rounded-lg border ${
          variacionAbsoluta >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
        }`}>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500 mb-1">Ventas proyectadas</p>
              <p className="text-base font-bold text-gray-900">{formatCurrency(nuevasVentas)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Resultado proyectado</p>
              <p className={`text-base font-bold ${nuevoResultado >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
                {formatCurrency(nuevoResultado)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Variación vs. actual</p>
              <p className={`text-base font-bold ${variacionAbsoluta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {variacionAbsoluta >= 0 ? '+' : ''}{formatCurrency(variacionAbsoluta)}
                <span className="block text-xs font-normal">
                  ({variacionAbsoluta >= 0 ? '+' : ''}{variacionPct.toFixed(1)}%)
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Reset */}
        {(deltaVolumen !== 0 || deltaPrecio !== 0) && (
          <button
            onClick={() => { setDeltaVolumen(0); setDeltaPrecio(0) }}
            className="mt-3 text-xs text-gray-400 hover:text-gray-600 underline"
          >
            Resetear sliders
          </button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Agregar `useState` al import si no está (verificar línea 1)**

`useState` ya está importado en la línea 1 del archivo:
```jsx
import { useState, useEffect } from 'react'
```
No requiere cambios.

- [ ] **Step 3: Renderizar `ApalancamientoCard` en el JSX**

En el return del componente `Reports`, buscar el cierre del bloque `{/* Punto de Equilibrio */}` (alrededor de la línea 772). Agregar `<ApalancamientoCard>` **después** de ese bloque, antes del cierre `</>`:

```jsx
          {/* Punto de Equilibrio */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            {/* ... código existente ... */}
          </div>

          {/* Apalancamiento Operativo */}
          <ApalancamientoCard dashboard={dashboard} />
```

- [ ] **Step 4: Verificar en el navegador**

Iniciar el servidor de desarrollo:
```bash
cd frontend && npm run dev
```

Navegar a la sección de Reportes. Verificar:
1. Se muestra la card "Apalancamiento Operativo" debajo del Punto de Equilibrio
2. El GAO se muestra con el color correcto (verde/amarillo/naranja)
3. Los sliders responden y el resultado proyectado cambia en tiempo real
4. El resultado se pone verde cuando la combinación es positiva, rojo cuando es negativa
5. El botón "Resetear sliders" aparece cuando los sliders no están en 0

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Reports.jsx
git commit -m "feat: add ApalancamientoCard with GAO display and price/volume simulator"
```
