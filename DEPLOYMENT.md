# Guía de Deployment en Render.com

## Requisitos Previos

1. Cuenta en [Render.com](https://render.com) (gratis)
2. Repositorio en GitHub con el código pusheado
3. Variables de entorno configuradas

## Pasos para Deployar

### 1. Crear cuenta en Render

Ve a https://render.com y crea una cuenta (puedes usar tu cuenta de GitHub).

### 2. Conectar tu repositorio

1. En el dashboard de Render, haz clic en **"New +"**
2. Selecciona **"Blueprint"**
3. Conecta tu repositorio de GitHub: `onofrionico/galia-app`
4. Render detectará automáticamente el archivo `render.yaml`

### 3. Configurar Variables de Entorno

Render creará automáticamente los servicios definidos en `render.yaml`. Necesitas configurar estas variables:

#### Para el Backend (`galia-backend`):
- `SECRET_KEY`: Se genera automáticamente
- `DATABASE_URL`: Se conecta automáticamente desde la base de datos
- `FLASK_ENV`: Ya está configurado como `production`
- `CORS_ORIGINS`: **DEBES CONFIGURAR MANUALMENTE**
  - Formato: `https://galia-frontend.onrender.com` (reemplaza con tu URL del frontend)

#### Para el Frontend (`galia-frontend`):
- `VITE_API_URL`: **DEBES CONFIGURAR MANUALMENTE**
  - Formato: `https://galia-backend.onrender.com` (reemplaza con tu URL del backend)

### 4. Orden de Deployment

Render deployará en este orden:
1. **Base de datos PostgreSQL** (`galia-db`)
2. **Backend Flask** (`galia-backend`)
3. **Frontend React** (`galia-frontend`)

### 5. Verificar el Deployment

Una vez completado:
- Backend estará en: `https://galia-backend.onrender.com`
- Frontend estará en: `https://galia-frontend.onrender.com`

Prueba accediendo al frontend y verificando que se conecte correctamente al backend.

## Configuración Manual (Alternativa)

Si prefieres no usar el archivo `render.yaml`, puedes crear los servicios manualmente:

### Base de Datos PostgreSQL

1. New + → PostgreSQL
2. Name: `galia-db`
3. Database: `galia_db`
4. User: `galia_user`
5. Region: Oregon (o el más cercano)
6. Plan: Free

### Backend (Web Service)

1. New + → Web Service
2. Conectar repositorio
3. Configuración:
   - **Name**: `galia-backend`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Root Directory**: (dejar vacío)
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn --chdir backend --bind 0.0.0.0:$PORT run:app`
   - **Plan**: Free

4. Variables de entorno:
   ```
   PYTHON_VERSION=3.11.0
   DATABASE_URL=[copiar desde la base de datos]
   SECRET_KEY=[generar uno seguro]
   FLASK_ENV=production
   CORS_ORIGINS=https://galia-frontend.onrender.com
   ```

### Frontend (Static Site)

1. New + → Static Site
2. Conectar repositorio
3. Configuración:
   - **Name**: `galia-frontend`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Root Directory**: (dejar vacío)
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

4. Variables de entorno:
   ```
   VITE_API_URL=https://galia-backend.onrender.com
   ```

5. En **Redirects/Rewrites**, agregar:
   - Source: `/*`
   - Destination: `/index.html`
   - Action: Rewrite

## Crear Usuario Administrador

Una vez deployado el backend, necesitas crear un usuario admin:

1. Ve al dashboard de Render
2. Selecciona el servicio `galia-backend`
3. Ve a la pestaña **Shell**
4. Ejecuta:
   ```bash
   cd backend
   python create_admin.py
   ```

O puedes usar el endpoint de la API si lo tienes configurado.

## Limitaciones del Tier Gratuito

- ⚠️ Los servicios **"duermen"** después de 15 minutos de inactividad
- ⚠️ Tardan ~30 segundos en "despertar" en la primera petición
- ⚠️ 750 horas de compute por mes
- ⚠️ La base de datos se elimina después de 90 días de inactividad

## Troubleshooting

### Error: "Application failed to start"
- Verifica los logs en el dashboard de Render
- Asegúrate de que todas las variables de entorno estén configuradas
- Verifica que `build.sh` tenga permisos de ejecución

### Error: CORS
- Verifica que `CORS_ORIGINS` en el backend incluya la URL exacta del frontend
- No incluyas trailing slash: ✅ `https://galia-frontend.onrender.com` ❌ `https://galia-frontend.onrender.com/`

### Error: Database connection
- Verifica que `DATABASE_URL` esté correctamente configurada
- Render usa formato `postgres://` pero SQLAlchemy necesita `postgresql://` (ya está manejado en el código)

### Frontend no se conecta al backend
- Verifica que `VITE_API_URL` esté configurada correctamente
- Recuerda que las variables de Vite deben estar presentes en **build time**, no runtime
- Si cambias `VITE_API_URL`, debes hacer un **Manual Deploy** del frontend

## Actualizar la Aplicación

Render hace **auto-deploy** cuando pusheas a la rama `main`:

```bash
git add .
git commit -m "Update application"
git push origin main
```

Render detectará el push y redesplegará automáticamente.

## Monitoreo

- **Logs**: Disponibles en tiempo real en el dashboard de cada servicio
- **Metrics**: CPU, memoria y ancho de banda en la pestaña Metrics
- **Health checks**: Render hace ping automático a tu aplicación

## Costos

El tier gratuito incluye:
- ✅ 750 horas/mes de web services
- ✅ 1 base de datos PostgreSQL (90 días de retención)
- ✅ Static sites ilimitados
- ✅ SSL automático
- ✅ Deploy automático desde Git

Para producción con más tráfico, considera el plan Starter ($7/mes por servicio).
