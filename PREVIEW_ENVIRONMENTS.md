# Preview Environments - Configuración

## ✅ Configuración Completada

Se han habilitado los Preview Environments en Render para el proyecto Galia App.

## 📋 Cambios Realizados

### 1. Servicios Configurados
- **Backend (`galia-backend`)**: Preview Environments habilitados
- **Frontend (`galia-frontend`)**: Preview Environments habilitados
- **Expiración**: 7 días después de cerrar el PR

### 2. Base de Datos de Test
- **Nombre**: `galia-db-test`
- **Plan**: Free (sin costo adicional)
- **Uso**: Compartida entre todos los Preview Environments

### 3. Configuración en render.yaml
```yaml
previewsEnabled: true
previewsExpireAfterDays: 7
```

## 🚀 Cómo Funciona

### Creación Automática
1. Creas un Pull Request en GitHub
2. Render detecta el PR automáticamente
3. Se despliega un Preview Environment con:
   - URL única para el backend preview
   - URL única para el frontend preview
   - Conexión a la base de datos de test compartida

### Limpieza Automática
- Los previews se eliminan automáticamente 7 días después de cerrar/mergear el PR
- Esto ahorra recursos y mantiene el entorno limpio

## ⚙️ Configuración Manual Necesaria

### Paso 1: Conectar la DB de Test a los Previews

Actualmente, los previews del backend usarán la misma DB de producción (`galia-db`). Para usar la DB de test, necesitas:

**Opción A - Configurar en el Dashboard de Render:**
1. Ve a tu servicio `galia-backend` en Render
2. En la sección "Preview Environments"
3. Configura la variable de entorno `DATABASE_URL` para que apunte a `galia-db-test`

**Opción B - Usar variables de entorno condicionales:**
Render automáticamente establece `IS_PULL_REQUEST=true` en previews. Puedes modificar tu código para detectar esto:

```python
# En backend/app/config.py
import os

if os.getenv('IS_PULL_REQUEST') == 'true':
    # Usar DB de test
    DATABASE_URL = os.getenv('TEST_DATABASE_URL')
else:
    # Usar DB de producción
    DATABASE_URL = os.getenv('DATABASE_URL')
```

### Paso 2: Configurar VITE_API_URL en Frontend Previews

El frontend preview necesita apuntar al backend preview. Render proporciona variables automáticas:

```bash
# En el dashboard de Render, para galia-frontend previews:
VITE_API_URL=https://galia-backend-pr-{PR_NUMBER}.onrender.com
```

O usa la variable automática `RENDER_SERVICE_NAME` para construir la URL dinámicamente.

## 💰 Costos

- **Preview Environments**: Sin costo adicional (incluido en plan Starter)
- **Base de datos de test**: Free plan (sin costo)
- **Total adicional**: $0/mes

## 🔄 Próximos Pasos

1. **Hacer commit y push** de los cambios en `render.yaml`
2. **Crear la base de datos de test** en Render (se creará automáticamente al hacer push)
3. **Configurar variables de entorno** para los previews en el dashboard
4. **Crear un PR de prueba** para verificar que todo funciona

## 📝 Notas Importantes

- La DB de test es compartida entre todos los previews
- Considera limpiar/resetear la DB de test periódicamente
- Los previews tienen URLs únicas: `https://[service-name]-pr-[number].onrender.com`
- Puedes deshabilitar previews temporalmente cambiando `previewsEnabled: false`

## 🔗 Referencias

- [Render Preview Environments Docs](https://render.com/docs/preview-environments)
- [Blueprint Spec](https://render.com/docs/blueprint-spec)
