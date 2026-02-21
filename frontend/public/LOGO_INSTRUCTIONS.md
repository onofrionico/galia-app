# Instrucciones para Agregar el Logo de Galia Café

## Archivos de Logo Necesarios

Para que tu app se vea profesional cuando se agrega al inicio del celular, necesitás crear los siguientes archivos de imagen y colocarlos en la carpeta `frontend/public/`:

### Archivos Requeridos:

1. **apple-touch-icon.png** (180x180 píxeles)
   - Para iPhone/iPad cuando se guarda en el inicio
   - Formato: PNG con fondo sólido (sin transparencia)

2. **android-chrome-192x192.png** (192x192 píxeles)
   - Para Android cuando se guarda en el inicio
   - Formato: PNG

3. **android-chrome-512x512.png** (512x512 píxeles)
   - Para Android (alta resolución)
   - Formato: PNG

4. **favicon-32x32.png** (32x32 píxeles)
   - Favicon para navegadores
   - Formato: PNG

5. **favicon-16x16.png** (16x16 píxeles)
   - Favicon para navegadores (pequeño)
   - Formato: PNG

## Cómo Crear los Logos

### Opción 1: Usar un Generador Online
Podés usar herramientas como:
- https://realfavicongenerator.net/
- https://favicon.io/

Subís tu logo original (preferiblemente 512x512 o mayor) y te genera todos los tamaños automáticamente.

### Opción 2: Crear Manualmente
1. Diseñá tu logo en Figma, Canva, o Photoshop
2. Exportá en los tamaños mencionados arriba
3. Guardá todos los archivos en `frontend/public/`

## Recomendaciones de Diseño

- **Fondo sólido**: Para Apple Touch Icon, usá un fondo de color (no transparente)
- **Color sugerido**: Marrón café (#8B4513) para mantener la temática
- **Diseño simple**: El logo debe verse bien en tamaños pequeños
- **Contraste**: Asegurate que el logo tenga buen contraste con el fondo

## Verificar que Funciona

1. Después de agregar los archivos, reiniciá el servidor de desarrollo
2. En iPhone/iPad: Abrí Safari → Compartir → "Agregar a Inicio"
3. En Android: Abrí Chrome → Menú → "Agregar a pantalla de inicio"

El logo debería aparecer correctamente en el acceso directo.

## Estado Actual

✅ Configuración HTML completada en `index.html`
✅ Web manifest creado en `site.webmanifest`
⏳ Pendiente: Agregar archivos de imagen del logo

Una vez que agregues las imágenes, todo estará listo para funcionar.
