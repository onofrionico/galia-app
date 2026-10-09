from app.utils.slug import slugify


def test_slugify_removes_accents_and_symbols():
    assert slugify('Cafés Fríos & Frappé') == 'cafes-frios-frappe'


def test_slugify_collapses_separators():
    assert slugify('  Tortas   --  Postres ') == 'tortas-postres'


def test_slugify_empty_falls_back():
    assert slugify('¡¡!!') == 'item'


def test_unique_slug_is_bounded_for_long_text(menu_app):
    from app.models.menu import MenuCategory
    from app.utils.slug import unique_slug
    assert len(unique_slug(MenuCategory, 'a' * 300)) <= 110
