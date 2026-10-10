import hashlib
import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_SIDE = 800
MAX_PIXELS = 40_000_000
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}


class InvalidImageError(ValueError):
    pass


def process_image(data, max_side=MAX_SIDE, key_prefix='images/'):
    """Valida la imagen, la redimensiona a `max_side` px de lado máximo y la convierte a WebP.

    Devuelve (bytes_webp, clave_relativa) donde la clave es `<key_prefix><hash>.webp`.
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImageError('La imagen supera los 10 MB')
    try:
        image = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise InvalidImageError('El archivo no es una imagen válida')
    image_format = image.format
    if image_format not in ALLOWED_FORMATS:
        raise InvalidImageError('Formato no soportado: usá JPG, PNG o WebP')
    width, height = image.size
    if width * height > MAX_PIXELS:
        raise InvalidImageError('La imagen es demasiado grande (máximo 40 megapíxeles)')
    try:
        image.load()
    except (Image.DecompressionBombError, OSError):
        raise InvalidImageError('El archivo no es una imagen válida')

    image = ImageOps.exif_transpose(image)
    if image.mode not in ('RGB', 'RGBA'):
        has_alpha = 'A' in image.getbands() or 'transparency' in image.info
        image = image.convert('RGBA' if has_alpha else 'RGB')
    image.thumbnail((max_side, max_side))

    output = io.BytesIO()
    image.save(output, format='WEBP', quality=82, method=6)
    body = output.getvalue()
    return body, f'{key_prefix}{hashlib.sha256(body).hexdigest()[:16]}.webp'
