from app.utils.slug import slugify


def test_slugify_removes_accents_and_symbols():
    assert slugify('Cafés Fríos & Frappé') == 'cafes-frios-frappe'


def test_slugify_collapses_separators():
    assert slugify('  Tortas   --  Postres ') == 'tortas-postres'


def test_slugify_empty_falls_back():
    assert slugify('¡¡!!') == 'item'
