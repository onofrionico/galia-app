# Sistema ML de Predicción de Demanda - Documentación Completa

## 📋 Índice
1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Características Implementadas](#características-implementadas)
4. [Uso del Sistema](#uso-del-sistema)
5. [Mantenimiento Automático](#mantenimiento-automático)
6. [API Endpoints](#api-endpoints)
7. [Métricas y Monitoreo](#métricas-y-monitoreo)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visión General

El sistema ML de predicción de demanda utiliza **Random Forest Regressor** para predecir:
- Cantidad de ventas por hora
- Monto de ventas esperado
- Cantidad de personal recomendado

### Características Clave
- ✅ Predicciones basadas en datos históricos
- ✅ Detección automática de feriados y eventos especiales
- ✅ Tracking de precisión del modelo
- ✅ Alertas cuando las predicciones difieren del personal programado
- ✅ Reentrenamiento periódico automático
- ✅ Dashboard visual de métricas

---

## 🏗️ Arquitectura

### Modelos de Base de Datos

#### 1. `ml_model_versions`
Tracking de versiones del modelo ML.
```python
- version: Versión del modelo (ej: "1.0.0")
- trained_at: Fecha/hora de entrenamiento
- training_records: Cantidad de registros usados
- train_score: Score de entrenamiento (R²)
- test_score: Score de prueba (R²)
- features_used: Features utilizados (JSON)
- hyperparameters: Hiperparámetros (JSON)
- is_active: Si es el modelo activo
```

#### 2. `ml_prediction_accuracy`
Comparación de predicciones vs valores reales.
```python
- date, hour: Fecha y hora de la predicción
- predicted_sales_count: Ventas predichas
- actual_sales_count: Ventas reales
- sales_count_error: Error porcentual
- model_version: Versión del modelo usado
```

#### 3. `holidays`
Feriados y eventos especiales.
```python
- date: Fecha del feriado
- name: Nombre del feriado
- type: Tipo (national, local, special_event)
- impact_multiplier: Multiplicador de impacto en ventas
```

#### 4. `prediction_alerts`
Alertas cuando predicciones difieren de lo programado.
```python
- schedule_id: ID de la grilla
- date, hour: Fecha y hora
- recommended_staff: Personal recomendado por ML
- scheduled_staff: Personal programado
- difference: Diferencia absoluta
- difference_percentage: Diferencia porcentual
- severity: Severidad (low, medium, high, critical)
- status: Estado (pending, acknowledged, resolved)
```

### Features del Modelo ML

El modelo utiliza las siguientes features:
1. **Temporales:**
   - `hour`: Hora del día (0-23)
   - `day_of_week`: Día de la semana (0-6)
   - `hour_sin`, `hour_cos`: Codificación cíclica de hora
   - `day_sin`, `day_cos`: Codificación cíclica de día

2. **Categóricas:**
   - `is_weekend`: Si es fin de semana
   - `is_morning`: Horario mañana (6-12h)
   - `is_afternoon`: Horario tarde (12-18h)
   - `is_evening`: Horario noche (18-24h)

3. **Eventos:**
   - `is_holiday`: Si es feriado
   - `holiday_impact`: Multiplicador de impacto del feriado

---

## 🚀 Características Implementadas

### 1. ✅ Re-entrenamiento Periódico

**Automático:**
- **Semanal:** Verifica si el modelo necesita reentrenamiento
- **Mensual:** Reentrenamiento completo con todos los datos

**Manual:**
```bash
# Verificar si necesita reentrenamiento
cd backend
source venv/bin/activate
python app/tasks/ml_tasks.py weekly_retrain_check

# Reentrenar manualmente
python train_and_predict.py
```

**Criterio de Reentrenamiento:**
El sistema recomienda reentrenar si:
- MAPE reciente > MAPE histórico + 20%
- Degradación significativa en precisión

### 2. ✅ Ajuste según Precisión Real vs Predicha

**Tracking Automático:**
```bash
# Actualizar precisión para ayer
python app/tasks/ml_tasks.py daily_accuracy
```

**Métricas Calculadas:**
- **MAE (Mean Absolute Error):** Error absoluto medio
- **MAPE (Mean Absolute Percentage Error):** Error porcentual medio
- **Accuracy Within ±2:** % de predicciones dentro de ±2 ventas

**API Endpoint:**
```http
GET /api/v1/ml/dashboard/accuracy?days=30
```

### 3. ✅ Features: Clima, Eventos Especiales, Festivos

**Feriados de Argentina 2026:**
- 17 feriados nacionales pre-cargados
- Multiplicador de impacto configurable

**Agregar Evento Especial:**
```http
POST /api/v1/ml/dashboard/holidays
{
  "date": "2026-12-24",
  "name": "Nochebuena",
  "impact_multiplier": 1.5,
  "notes": "Mayor demanda esperada"
}
```

**Listar Feriados:**
```http
GET /api/v1/ml/dashboard/holidays?year=2026
```

**Clima (Preparado para integración futura):**
El modelo está preparado para incluir features de clima:
- Temperatura
- Condición climática
- Precipitación

### 4. ✅ Dashboard de Precisión del Modelo

**Ubicación:** `/ml-dashboard` (solo admin)

**Visualizaciones:**
- 📊 Métricas generales (MAE, MAPE, Accuracy)
- ⏰ Precisión por hora del día
- 📅 Precisión por día de la semana
- 🎯 Información del modelo activo
- ⚠️ Recomendación de reentrenamiento
- 🚨 Alertas activas

**Períodos Configurables:**
- Últimos 7 días
- Últimos 30 días
- Últimos 90 días

### 5. ✅ Alertas cuando Predicción Difiere de lo Programado

**Generación Automática:**
```http
POST /api/v1/ml/dashboard/alerts/check-schedule/{schedule_id}
```

**Severidades:**
- **Critical:** Diferencia ≥ 50%
- **High:** Diferencia ≥ 30%
- **Medium:** Diferencia ≥ 15%
- **Low:** Diferencia < 15%

**Ver Alertas:**
```http
GET /api/v1/ml/dashboard/alerts?severity=critical
```

**Reconocer Alerta:**
```http
POST /api/v1/ml/dashboard/alerts/{alert_id}/acknowledge
```

---

## 📖 Uso del Sistema

### Flujo Completo

#### 1. Generación de Datos Históricos (Primera vez)
```bash
cd backend
source venv/bin/activate
python generate_sample_data.py
```

#### 2. Inicializar Feriados
```bash
python initialize_holidays.py
```

#### 3. Entrenar Modelo y Generar Predicciones
```bash
python train_and_predict.py
```

#### 4. Crear Grilla Horaria
1. Ir a "Horarios" → "Crear Nueva Grilla"
2. Seleccionar fechas
3. Click en "Ver Recomendaciones IA"
4. Ver predicciones por día:
   - Ventas estimadas
   - Personal recomendado
   - Hora pico

#### 5. Verificar Alertas
1. Crear grilla con turnos
2. Sistema genera alertas automáticamente
3. Ver alertas en Dashboard ML
4. Ajustar personal según recomendaciones

#### 6. Monitorear Precisión
1. Ir a "Dashboard ML"
2. Ver métricas de precisión
3. Verificar recomendación de reentrenamiento
4. Analizar precisión por hora/día

---

## ⚙️ Mantenimiento Automático

### Configuración de Cron Jobs

```bash
cd backend
./setup_cron.sh
```

### Tareas Programadas

#### 1. Actualización Diaria de Precisión
**Frecuencia:** Todos los días a la 1:00 AM
```cron
0 1 * * * cd /path/to/backend && venv/bin/python app/tasks/ml_tasks.py daily_accuracy
```

#### 2. Verificación Semanal de Reentrenamiento
**Frecuencia:** Todos los lunes a las 2:00 AM
```cron
0 2 * * 1 cd /path/to/backend && venv/bin/python app/tasks/ml_tasks.py weekly_retrain_check
```

#### 3. Generación Semanal de Predicciones
**Frecuencia:** Todos los domingos a las 3:00 AM
```cron
0 3 * * 0 cd /path/to/backend && venv/bin/python app/tasks/ml_tasks.py weekly_predictions
```

#### 4. Verificación Diaria de Alertas
**Frecuencia:** Todos los días a las 9:00 AM
```cron
0 9 * * * cd /path/to/backend && venv/bin/python app/tasks/ml_tasks.py daily_alerts
```

#### 5. Reentrenamiento Mensual Completo
**Frecuencia:** Primer día del mes a las 4:00 AM
```cron
0 4 1 * * cd /path/to/backend && venv/bin/python app/tasks/ml_tasks.py monthly_retrain
```

---

## 🔌 API Endpoints

### Predicciones

#### Entrenar Modelo
```http
POST /api/v1/ml/train
Authorization: Bearer {token}
Content-Type: application/json

{
  "min_weeks": 8
}
```

#### Generar Predicciones
```http
POST /api/v1/ml/predict
Authorization: Bearer {token}
Content-Type: application/json

{
  "start_date": "2026-02-05",
  "end_date": "2026-02-19"
}
```

#### Obtener Recomendaciones
```http
GET /api/v1/ml/recommendations/summary?start_date=2026-02-05&end_date=2026-02-19
Authorization: Bearer {token}
```

### Dashboard

#### Estadísticas Generales
```http
GET /api/v1/ml/dashboard/stats
Authorization: Bearer {token}
```

#### Métricas de Precisión
```http
GET /api/v1/ml/dashboard/accuracy?days=30
Authorization: Bearer {token}
```

#### Precisión por Hora
```http
GET /api/v1/ml/dashboard/accuracy/by-hour
Authorization: Bearer {token}
```

#### Precisión por Día
```http
GET /api/v1/ml/dashboard/accuracy/by-day
Authorization: Bearer {token}
```

#### Verificar Reentrenamiento
```http
GET /api/v1/ml/dashboard/retrain-check
Authorization: Bearer {token}
```

### Alertas

#### Listar Alertas
```http
GET /api/v1/ml/dashboard/alerts?severity=critical
Authorization: Bearer {token}
```

#### Resumen de Alertas
```http
GET /api/v1/ml/dashboard/alerts/summary
Authorization: Bearer {token}
```

#### Verificar Grilla
```http
POST /api/v1/ml/dashboard/alerts/check-schedule/{schedule_id}
Authorization: Bearer {token}
```

### Feriados

#### Listar Feriados
```http
GET /api/v1/ml/dashboard/holidays?year=2026
Authorization: Bearer {token}
```

#### Agregar Evento
```http
POST /api/v1/ml/dashboard/holidays
Authorization: Bearer {token}
Content-Type: application/json

{
  "date": "2026-12-24",
  "name": "Nochebuena",
  "impact_multiplier": 1.5,
  "notes": "Mayor demanda"
}
```

---

## 📊 Métricas y Monitoreo

### Métricas Clave

#### MAE (Mean Absolute Error)
- **Qué es:** Error absoluto medio en cantidad de ventas
- **Interpretación:** Promedio de cuántas ventas se desvía la predicción
- **Objetivo:** < 3 ventas

#### MAPE (Mean Absolute Percentage Error)
- **Qué es:** Error porcentual medio absoluto
- **Interpretación:** Porcentaje promedio de error
- **Objetivo:** < 15%

#### Accuracy Within ±2
- **Qué es:** % de predicciones dentro de ±2 ventas del valor real
- **Interpretación:** Qué tan preciso es el modelo
- **Objetivo:** > 70%

### Interpretación de Colores

- 🟢 **Verde:** MAPE < 10% (Excelente)
- 🟡 **Amarillo:** MAPE 10-20% (Bueno)
- 🔴 **Rojo:** MAPE > 20% (Necesita mejora)

---

## 🔧 Troubleshooting

### Problema: Modelo no entrena

**Síntoma:** Error "Insufficient data for training"

**Solución:**
```bash
# Verificar cantidad de datos
python -c "from app import create_app; from app.models.staffing_metrics import StaffingMetrics; app = create_app(); app.app_context().push(); print(StaffingMetrics.query.count())"

# Generar más datos si es necesario
python generate_sample_data.py
```

### Problema: Predicciones no aparecen en UI

**Síntoma:** "No hay predicciones disponibles"

**Solución:**
```bash
# Verificar predicciones en DB
python -c "from app import create_app; from app.models.staffing_metrics import StaffingPrediction; app = create_app(); app.app_context().push(); print(StaffingPrediction.query.count())"

# Generar predicciones
python train_and_predict.py
```

### Problema: Alertas no se generan

**Síntoma:** No hay alertas en el dashboard

**Solución:**
```bash
# Verificar manualmente para una grilla
curl -X POST http://localhost:5000/api/v1/ml/dashboard/alerts/check-schedule/1 \
  -H "Authorization: Bearer {token}"
```

### Problema: MAPE muy alto

**Síntoma:** MAPE > 30%

**Solución:**
1. Verificar calidad de datos históricos
2. Agregar más datos de entrenamiento
3. Reentrenar modelo:
```bash
python train_and_predict.py
```

### Problema: Feriados no se detectan

**Síntoma:** is_holiday siempre es 0

**Solución:**
```bash
# Inicializar feriados
python initialize_holidays.py

# Verificar feriados
python -c "from app import create_app; from app.models.ml_tracking import Holiday; app = create_app(); app.app_context().push(); print(Holiday.query.count())"
```

---

## 📝 Notas Importantes

1. **Datos Mínimos:** El modelo requiere al menos 50 registros (≈4 semanas) para entrenar
2. **Reentrenamiento:** Se recomienda reentrenar mensualmente o cuando MAPE > 20%
3. **Feriados:** Actualizar feriados anualmente para el próximo año
4. **Alertas:** Revisar alertas críticas diariamente
5. **Backup:** Respaldar modelos entrenados en `backend/app/ml/models/`

---

## 🎓 Mejoras Futuras Sugeridas

1. **Integración con API de Clima**
   - OpenWeatherMap o similar
   - Agregar features: temperatura, precipitación, condición

2. **Eventos Locales**
   - Integración con calendario de eventos de la ciudad
   - Conciertos, partidos, festivales

3. **Análisis de Tendencias**
   - Detección de tendencias estacionales
   - Predicción de crecimiento/decrecimiento

4. **A/B Testing**
   - Comparar diferentes algoritmos
   - Optimización de hiperparámetros

5. **Notificaciones Push**
   - Alertas en tiempo real
   - Notificaciones móviles

---

## 📞 Soporte

Para problemas o consultas:
1. Revisar logs: `backend/server.log`
2. Verificar estado del modelo: Dashboard ML
3. Consultar esta documentación

---

**Última actualización:** Febrero 2026
**Versión del sistema:** 1.0.0
