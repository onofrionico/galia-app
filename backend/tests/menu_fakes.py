class FakeStorage:
    """Reemplazo en memoria de MenuStorage."""

    def __init__(self):
        self.objects = {}

    def put(self, rel_key, body, content_type, cache_control):
        self.objects[rel_key] = {'body': body, 'content_type': content_type, 'cache_control': cache_control}

    def delete(self, rel_key):
        self.objects.pop(rel_key, None)

    def list(self, rel_prefix):
        return sorted(k for k in self.objects if k.startswith(rel_prefix))


class FakeFudoClient:
    def __init__(self, products=None, categories=None):
        self.products = products or []
        self.categories = categories or []

    def get_all_products(self):
        return self.products

    def get_all_product_categories(self):
        return self.categories


def fudo_product(fudo_id, name, price, active=True, category_id='1'):
    return {
        'id': str(fudo_id),
        'type': 'Product',
        'attributes': {'name': name, 'price': price, 'active': active},
        'relationships': {'productCategory': {'data': {'id': category_id, 'type': 'ProductCategory'}}},
    }


def fudo_category(category_id, name):
    return {'id': str(category_id), 'type': 'ProductCategory', 'attributes': {'name': name}}


def make_category(name='Cafés', fudo_category_id=None, **kwargs):
    """Por defecto crea una categoría 'heredada' (sin vínculo a Fudo); pasar fudo_category_id único para una de Fudo."""
    from app.extensions import db
    from app.models.menu import MenuCategory
    from app.utils.slug import unique_slug
    category = MenuCategory(name=name, slug=unique_slug(MenuCategory, name), fudo_category_id=fudo_category_id, **kwargs)
    db.session.add(category)
    db.session.commit()
    return category
