import io

from PIL import Image

from app.services.menu_image_service import process_image


def _png(size=(3000, 1500)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color=(10, 20, 30)).save(buffer, format='PNG')
    return buffer.getvalue()


def test_defaults_unchanged():
    body, key = process_image(_png())
    assert max(Image.open(io.BytesIO(body)).size) == 800
    assert key.startswith('images/')


def test_custom_max_side_and_prefix():
    body, key = process_image(_png(), max_side=1920, key_prefix='branding/banner-')
    assert max(Image.open(io.BytesIO(body)).size) == 1920
    assert key.startswith('branding/banner-') and key.endswith('.webp')
