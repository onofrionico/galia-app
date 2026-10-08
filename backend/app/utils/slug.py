import re
import unicodedata


def slugify(text):
    normalized = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    return slug or 'item'


def unique_slug(model, text, exclude_id=None):
    """Devuelve un slug único para `model` (debe tener columnas `slug` e `id`)."""
    base = slugify(text)[:110].rstrip('-') or 'item'
    slug = base
    suffix = 2
    while True:
        query = model.query.filter_by(slug=slug)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f'{base}-{suffix}'
        suffix += 1
