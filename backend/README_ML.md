# 🧠 Sistema ML - Guía Rápida

## Inicio Rápido

### 1. Primera Configuración

```bash
# 1. Crear tablas ML
cd backend
source venv/bin/activate
python create_ml_tables.py

# 2. Inicializar feriados
python initialize_holidays.py

# 3. Generar datos de muestra (si es necesario)
python generate_sample_data.py

# 4. Entrenar modelo y generar predicciones
python train_and_predict.py
```

### 2. Uso Diario

**Ver Recomendaciones al Crear Grilla:**
1. Ir a "Horarios" → "Crear Nueva Grilla"
2. Seleccionar fechas
3. Click en "Ver Recomendaciones IA" 🧠
4. Revisar predicciones por día

**Monitorear Precisión:**
1. Ir a "Dashboard ML" (menú lateral)
2. Revisar métricas de precisión
3. Verificar alertas activas
4. Comprobar recomendación de reentrenamiento

### 3. Mantenimiento

**Tareas Manuales:**

```bash
# Actualizar precisión para ayer
python app/tasks/ml_tasks.py daily_accuracy

# Verificar si necesita reentrenamiento
python app/tasks/ml_tasks.py weekly_retrain_check

# Generar predicciones para próximas 2 semanas
python app/tasks/ml_tasks.py weekly_predictions

# Verificar alertas críticas
python app/tasks/ml_tasks.py daily_alerts

# Reentrenamiento completo
python app/tasks/ml_tasks.py monthly_retrain
```

**Automatización con Cron:**

```bash
# Ver comandos cron sugeridos
./setup_cron.sh

# Instalar cron jobs (opcional)
# Seguir instrucciones del script
```

## Estructura de Archivos

```
backend/
├── app/
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── staffing_predictor.py      # Modelo ML principal
│   │   └── models/                     # Modelos entrenados
│   │       ├── sales_model.pkl
│   │       ├── scaler.pkl
│   │       └── metadata.pkl
│   ├── models/
│   │   ├── ml_tracking.py              # Modelos de tracking
│   │   └── staffing_metrics.py         # Métricas y predicciones
│   ├── services/
│   │   ├── ml_accuracy_service.py      # Tracking de precisión
│   │   ├── holiday_service.py          # Gestión de feriados
│   │   └── alert_service.py            # Sistema de alertas
│   ├── routes/
│   │   ├── ml_predictions.py           # Endpoints de predicción
│   │   └── ml_dashboard.py             # Endpoints de dashboard
│   └── tasks/
│       └── ml_tasks.py                 # Tareas de mantenimiento
├── generate_sample_data.py             # Generar datos de prueba
├── train_and_predict.py                # Entrenar y predecir
├── initialize_holidays.py              # Inicializar feriados
├── create_ml_tables.py                 # Crear tablas
└── setup_cron.sh                       # Configurar cron jobs
```

## API Endpoints Principales

### Predicciones
- `POST /api/v1/ml/train` - Entrenar modelo
- `POST /api/v1/ml/predict` - Generar predicciones
- `GET /api/v1/ml/recommendations/summary` - Resumen de recomendaciones

### Dashboard
- `GET /api/v1/ml/dashboard/stats` - Estadísticas generales
- `GET /api/v1/ml/dashboard/accuracy` - Métricas de precisión
- `GET /api/v1/ml/dashboard/alerts` - Alertas activas

### Feriados
- `GET /api/v1/ml/dashboard/holidays` - Listar feriados
- `POST /api/v1/ml/dashboard/holidays` - Agregar evento especial

## Métricas Clave

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| **MAE** | Error absoluto medio | < 3 ventas |
| **MAPE** | Error porcentual medio | < 15% |
| **Accuracy ±2** | Precisión dentro de ±2 ventas | > 70% |

## Troubleshooting Rápido

**Problema:** No hay predicciones
```bash
python train_and_predict.py
```

**Problema:** MAPE muy alto (>30%)
```bash
# Reentrenar con más datos
python train_and_predict.py
```

**Problema:** Feriados no detectados
```bash
python initialize_holidays.py
```

**Problema:** Backend no inicia
```bash
# Ver logs
tail -f server.log

# Verificar puerto
lsof -ti:5000
```

## Documentación Completa

Ver `ML_SYSTEM_DOCUMENTATION.md` para documentación detallada.

## Soporte

- 📖 Documentación: `ML_SYSTEM_DOCUMENTATION.md`
- 🐛 Logs: `backend/server.log`
- 📊 Dashboard: http://localhost:5173/ml-dashboard
