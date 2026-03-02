# AWS S3 Setup Guide

Esta guía explica cómo configurar AWS S3 para el almacenamiento de comprobantes de ausencias en la aplicación Galia.

## 📋 Requisitos Previos

- Cuenta de AWS (puedes crear una en https://aws.amazon.com)
- Acceso a la consola de AWS
- Permisos para crear buckets S3 y usuarios IAM

## 🚀 Configuración Paso a Paso

### 1. Crear un Bucket S3

1. Inicia sesión en la [Consola de AWS](https://console.aws.amazon.com)
2. Navega a **S3** (puedes buscar "S3" en la barra de búsqueda)
3. Haz clic en **"Create bucket"**
4. Configura el bucket:
   - **Bucket name**: `galia-app-attachments` (o el nombre que prefieras, debe ser único globalmente)
   - **AWS Region**: Selecciona la región más cercana (ej: `us-east-1`, `sa-east-1` para São Paulo)
   - **Block Public Access settings**: Mantén todas las opciones marcadas (el bucket debe ser privado)
   - **Bucket Versioning**: Opcional (recomendado para backup)
   - **Default encryption**: Habilita **Server-side encryption with Amazon S3 managed keys (SSE-S3)**
5. Haz clic en **"Create bucket"**

### 2. Crear un Usuario IAM

1. Navega a **IAM** en la consola de AWS
2. En el menú lateral, selecciona **"Users"**
3. Haz clic en **"Add users"**
4. Configura el usuario:
   - **User name**: `galia-app-s3-user`
   - **Access type**: Marca **"Access key - Programmatic access"**
5. Haz clic en **"Next: Permissions"**

### 3. Asignar Permisos

1. Selecciona **"Attach existing policies directly"**
2. Haz clic en **"Create policy"** (se abrirá una nueva pestaña)
3. En la pestaña de política, selecciona la pestaña **JSON** y pega:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::galia-app-attachments",
                "arn:aws:s3:::galia-app-attachments/*"
            ]
        }
    ]
}
```

**Importante**: Reemplaza `galia-app-attachments` con el nombre de tu bucket si usaste otro nombre.

4. Haz clic en **"Next: Tags"** (opcional)
5. Haz clic en **"Next: Review"**
6. Nombra la política: `GaliaAppS3Policy`
7. Haz clic en **"Create policy"**
8. Vuelve a la pestaña de creación de usuario y haz clic en el botón de refrescar
9. Busca y selecciona `GaliaAppS3Policy`
10. Haz clic en **"Next: Tags"** → **"Next: Review"** → **"Create user"**

### 4. Guardar las Credenciales

⚠️ **MUY IMPORTANTE**: Esta es la única vez que podrás ver la Secret Access Key.

1. En la pantalla de éxito, verás:
   - **Access key ID**: `AKIA...`
   - **Secret access key**: `wJalrXUtn...` (haz clic en "Show" para verla)
2. **Descarga el archivo CSV** o copia ambas claves en un lugar seguro

### 5. Configurar Variables de Entorno

1. Abre el archivo `.env` en la raíz del proyecto (crea uno si no existe, basándote en `.env.example`)
2. Agrega las siguientes variables:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=tu-access-key-id-aqui
AWS_SECRET_ACCESS_KEY=tu-secret-access-key-aqui
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=galia-app-attachments
```

3. Reemplaza los valores con tus credenciales reales

### 6. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

Esto instalará `boto3`, la librería de AWS para Python.

### 7. Verificar la Configuración

Puedes verificar que todo funciona correctamente:

```python
# En una consola Python dentro del entorno del backend
from app.utils.s3_utils import s3_service

# Verificar conexión
try:
    s3_service.s3_client.list_buckets()
    print("✅ Conexión exitosa con AWS S3")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 💰 Costos Estimados

Para una cafetería con ~100 empleados:

- **Almacenamiento**: ~$0.023 por GB/mes
  - 200 solicitudes/año × 500KB promedio = 100MB = **~$0.002/mes**
- **Requests**:
  - PUT: $0.005 por 1,000 requests
  - GET: $0.0004 por 1,000 requests
  - 200 uploads + 400 downloads/año = **~$0.002/mes**

**Total estimado: ~$0.05/mes** (prácticamente gratis)

### Free Tier de AWS

AWS ofrece un Free Tier que incluye:
- 5 GB de almacenamiento S3
- 20,000 GET requests
- 2,000 PUT requests
- Por 12 meses (para nuevas cuentas)

## 🔒 Seguridad

### Mejores Prácticas Implementadas

✅ **Encriptación**: Los archivos se encriptan automáticamente con AES-256  
✅ **Bucket privado**: No hay acceso público  
✅ **Permisos mínimos**: El usuario IAM solo tiene acceso al bucket específico  
✅ **Nombres únicos**: Los archivos tienen timestamp para evitar colisiones  
✅ **Validación**: Se validan tipos y tamaños de archivo antes de subir  

### Recomendaciones Adicionales

1. **Rotar credenciales**: Cambia las Access Keys cada 90 días
2. **Habilitar MFA**: Activa autenticación de dos factores en tu cuenta AWS
3. **Monitoreo**: Configura CloudWatch para alertas de uso inusual
4. **Backup**: Habilita versionado del bucket para recuperar archivos eliminados

## 🔄 Migración desde Almacenamiento Local

Si ya tienes archivos guardados localmente en `backend/absence_attachments/`, puedes migrarlos a S3:

```python
# Script de migración (ejecutar desde backend/)
import os
from app.utils.s3_utils import s3_service
from app.models.absence_request import AbsenceRequest
from app.extensions import db

local_folder = 'absence_attachments'

if os.path.exists(local_folder):
    for filename in os.listdir(local_folder):
        file_path = os.path.join(local_folder, filename)
        if os.path.isfile(file_path):
            # Extraer employee_id del nombre del archivo
            employee_id = filename.split('_')[0]
            
            with open(file_path, 'rb') as f:
                result = s3_service.upload_file(f, employee_id, filename)
                print(f"✅ Migrado: {filename} → {result['s3_key']}")
            
            # Actualizar base de datos si es necesario
            # ...
```

## 🌍 Regiones Recomendadas

Para mejor rendimiento, elige la región más cercana a tus usuarios:

- **Argentina/Uruguay**: `sa-east-1` (São Paulo, Brasil)
- **Chile**: `sa-east-1` (São Paulo, Brasil)
- **USA**: `us-east-1` (Virginia del Norte)
- **Europa**: `eu-west-1` (Irlanda)

## 📊 Monitoreo

Puedes monitorear el uso de S3 en:
1. Consola AWS → S3 → Tu bucket → Metrics
2. CloudWatch para métricas detalladas
3. AWS Cost Explorer para costos

## ❓ Troubleshooting

### Error: "Access Denied"
- Verifica que las credenciales en `.env` sean correctas
- Confirma que la política IAM esté correctamente configurada
- Verifica que el nombre del bucket coincida

### Error: "Bucket does not exist"
- Confirma que el bucket existe en la región especificada
- Verifica la variable `AWS_S3_BUCKET_NAME` en `.env`

### Error: "Invalid access key"
- Las credenciales pueden haber expirado o ser incorrectas
- Genera nuevas credenciales en IAM

## 📚 Recursos Adicionales

- [Documentación de AWS S3](https://docs.aws.amazon.com/s3/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS Pricing Calculator](https://calculator.aws/)

## 🆘 Soporte

Si tienes problemas con la configuración de AWS S3, contacta al equipo de desarrollo o consulta la documentación oficial de AWS.
