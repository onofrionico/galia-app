import io

import pytest
from PIL import Image

from app.services.menu_image_service import process_image, InvalidImageError, MAX_UPLOAD_BYTES


def _image_bytes(fmt='PNG', size=(1600, 1200), mode='RGB'):
    buffer = io.BytesIO()
    Image.new(mode, size, color=(200, 100, 50) if mode == 'RGB' else (200, 100, 50, 128)).save(buffer, format=fmt)
    return buffer.getvalue()


def test_converts_to_webp_and_limits_size():
    body, key = process_image(_image_bytes('JPEG'))
    result = Image.open(io.BytesIO(body))
    assert result.format == 'WEBP'
    assert max(result.size) == 800
    assert key.startswith('images/') and key.endswith('.webp')


def test_key_is_content_hash():
    data = _image_bytes('PNG')
    assert process_image(data)[1] == process_image(data)[1]


def test_keeps_transparency():
    body, _ = process_image(_image_bytes('PNG', mode='RGBA'))
    assert Image.open(io.BytesIO(body)).mode == 'RGBA'


def test_rejects_non_images():
    with pytest.raises(InvalidImageError):
        process_image(b'not an image')


def test_rejects_unsupported_format():
    with pytest.raises(InvalidImageError):
        process_image(_image_bytes('GIF', mode='RGB'))


def test_rejects_large_files():
    with pytest.raises(InvalidImageError):
        process_image(b'0' * (MAX_UPLOAD_BYTES + 1))
