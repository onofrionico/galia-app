"""API de recetas: permisos, costos, ciclos y vínculo con el producto."""
from datetime import date
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Product, ProductCategory, ProductVariant, Recipe, Supply, SupplyPrice
from pos_helpers import auth_headers, make_user, pos_app  # noqa: F401


@pytest.fixture
def client(pos_app):
    return pos_app.test_client()


@pytest.fixture
def world(pos_app):
    cat = ProductCategory(name='Pastelería')
    harina = Supply(name='Harina', unit='kg', stock_quantity=0, min_stock=0)
    db.session.add_all([cat, harina])
    db.session.flush()
    product = Product(name='Torta', category_id=cat.id)
    db.session.add(product)
    db.session.flush()
    variant = ProductVariant(product_id=product.id, name='Porción', price=Decimal('1000'),
                             stock_quantity=0, min_stock=0)
    viewer = make_user('viewer@x.com', modules=['Recipes'])
    cost_viewer = make_user('cost@x.com', modules=['Recipes', 'RecipeCosts'])
    editor = make_user('editor@x.com', modules=['Recipes', 'RecipesAdmin'])
    nobody = make_user('nobody@x.com')
    db.session.add(variant)
    db.session.add(SupplyPrice(supply_id=harina.id, price=Decimal('1000'), recorded_at=date(2026, 1, 1),
                               created_by=viewer.id))
    db.session.commit()
    return dict(product=product, variant=variant, harina=harina, viewer=viewer, cost_viewer=cost_viewer,
                editor=editor, nobody=nobody)


def _headers(client, user):
    return auth_headers(client, user)


def _payload(world, name='Masa', **extra):
    body = {'name': name, 'yield_quantity': 10, 'yield_unit': 'porción',
            'ingredients': [{'supply_id': world['harina'].id, 'quantity': 2, 'unit': 'kg'}],
            'steps': [{'title': 'Mezclar'}]}
    body.update(extra)
    return body


def _create(client, world, **kwargs):
    response = client.post('/api/v1/recipes', json=_payload(world, **kwargs),
                           headers=_headers(client, world['editor']))
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def _link(client, world, recipe_id, stock_active=False, variant_units=None, product_id=-1):
    return client.put(f'/api/v1/recipes/{recipe_id}/product', headers=_headers(client, world['editor']), json={
        'product_id': world['product'].id if product_id == -1 else product_id,
        'stock_active': stock_active, 'variant_units': variant_units or {}})


def _keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys(value)


def test_employee_without_recipes_module_gets_403(client, world):
    response = client.get('/api/v1/recipes', headers=_headers(client, world['nobody']))
    assert response.status_code == 403


def test_viewer_sees_recipe_without_any_cost_keys(client, world):
    recipe = _create(client, world)
    assert _link(client, world, recipe['id']).status_code == 200
    headers = _headers(client, world['viewer'])
    listing = client.get('/api/v1/recipes', headers=headers).get_json()
    detail = client.get(f"/api/v1/recipes/{recipe['id']}", headers=headers).get_json()
    product = client.get(f"/api/v1/products/{world['product'].id}", headers=headers).get_json()
    assert listing and detail['ingredients'] and product['recipe']['id'] == recipe['id']
    for body in (listing, detail, product, recipe):
        assert not [key for key in _keys(body) if 'cost' in key.lower()]


def test_cost_viewer_gets_cost(client, world):
    recipe = _create(client, world)
    assert _link(client, world, recipe['id']).status_code == 200
    headers = _headers(client, world['cost_viewer'])
    listing = client.get('/api/v1/recipes', headers=headers).get_json()
    detail = client.get(f"/api/v1/recipes/{recipe['id']}", headers=headers).get_json()
    assert listing[0]['unit_cost'] == 200.0 and listing[0]['cost_complete'] is True
    assert detail['cost']['batch_cost'] == 2000.0
    product = client.get(f"/api/v1/products/{world['product'].id}", headers=headers).get_json()
    assert product['recipe_cost']['unit_cost'] == 200.0


def test_viewer_cannot_edit(client, world):
    recipe = _create(client, world)
    headers = _headers(client, world['viewer'])
    assert client.put(f"/api/v1/recipes/{recipe['id']}", json=_payload(world), headers=headers).status_code == 403
    assert client.post('/api/v1/recipes', json=_payload(world, name='Otra'), headers=headers).status_code == 403
    assert client.delete(f"/api/v1/recipes/{recipe['id']}", headers=headers).status_code == 403
    assert client.put(f"/api/v1/recipes/{recipe['id']}/product", headers=headers,
                      json={'product_id': None, 'stock_active': False, 'variant_units': {}}).status_code == 403


def test_indirect_cycle_rejected(client, world):
    headers = _headers(client, world['editor'])
    a = _create(client, world, name='A')
    b = _create(client, world, name='B', ingredients=[{'sub_recipe_id': a['id'], 'quantity': 1, 'unit': 'porción'}])
    c = _create(client, world, name='C', ingredients=[{'sub_recipe_id': b['id'], 'quantity': 1, 'unit': 'porción'}])
    response = client.put(f"/api/v1/recipes/{a['id']}", headers=headers, json=_payload(
        world, name='A', ingredients=[{'sub_recipe_id': c['id'], 'quantity': 1, 'unit': 'porción'}]))
    assert response.status_code == 400
    assert 'ciclo' in response.get_json()['error'].lower()


def test_cycle_rejected_even_with_null_quantity_or_missing_yield(client, world):
    headers = _headers(client, world['editor'])
    a = _create(client, world, name='A')
    b = _create(client, world, name='B', yield_quantity=None, yield_unit=None,
                ingredients=[{'sub_recipe_id': a['id'], 'quantity': None, 'unit': None}])
    response = client.put(f"/api/v1/recipes/{a['id']}", headers=headers, json=_payload(
        world, name='A', ingredients=[{'sub_recipe_id': b['id'], 'quantity': None, 'unit': None}]))
    assert response.status_code == 400
    self_ref = client.put(f"/api/v1/recipes/{a['id']}", headers=headers, json=_payload(
        world, name='A', ingredients=[{'sub_recipe_id': a['id'], 'quantity': 1, 'unit': 'porción'}]))
    assert self_ref.status_code == 400


def test_validation_errors(client, world):
    headers = _headers(client, world['editor'])
    _create(client, world, name='Única')
    harina = world['harina'].id
    bad = [
        _payload(world, name='Única'),
        _payload(world, name='Q', ingredients=[{'supply_id': harina, 'quantity': 0, 'unit': 'kg'}]),
        _payload(world, name='S', ingredients=[{'supply_id': 9999, 'quantity': 1, 'unit': 'kg'}]),
        _payload(world, name='B', ingredients=[{'sub_recipe_id': 9999, 'quantity': 1, 'unit': 'kg'}]),
        _payload(world, name='X', ingredients=[{'supply_id': harina, 'sub_recipe_id': 1, 'quantity': 1, 'unit': 'kg'}]),
        _payload(world, name=''),
    ]
    for body in bad:
        assert client.post('/api/v1/recipes', json=body, headers=headers).status_code == 400, body


def test_inactive_recipe_cannot_be_sub_recipe(client, world):
    headers = _headers(client, world['editor'])
    base = _create(client, world, name='Base')
    assert client.delete(f"/api/v1/recipes/{base['id']}", headers=headers).status_code == 200
    response = client.post('/api/v1/recipes', headers=headers, json=_payload(
        world, name='Padre', ingredients=[{'sub_recipe_id': base['id'], 'quantity': 1, 'unit': 'porción'}]))
    assert response.status_code == 400


def test_delete_base_in_use_conflicts(client, world):
    headers = _headers(client, world['editor'])
    base = _create(client, world, name='Base')
    _create(client, world, name='Padre',
            ingredients=[{'sub_recipe_id': base['id'], 'quantity': 1, 'unit': 'porción'}])
    assert client.delete(f"/api/v1/recipes/{base['id']}", headers=headers).status_code == 409


def test_link_and_activate_sets_has_recipe_and_units(client, world):
    recipe = _create(client, world)
    response = _link(client, world, recipe['id'], stock_active=True,
                     variant_units={str(world['variant'].id): 0.125})
    assert response.status_code == 200, response.get_json()
    db.session.expire_all()
    assert db.session.get(Product, world['product'].id).has_recipe is True
    assert db.session.get(ProductVariant, world['variant'].id).recipe_units == Decimal('0.125')
    assert db.session.get(Recipe, recipe['id']).product_id == world['product'].id
    # Desvincular apaga el stock del producto.
    assert _link(client, world, recipe['id'], product_id=None).status_code == 200
    db.session.expire_all()
    assert db.session.get(Product, world['product'].id).has_recipe is False


def test_activate_without_yield_rejected(client, world):
    recipe = _create(client, world, yield_quantity=None, yield_unit=None)
    assert _link(client, world, recipe['id'], stock_active=True).status_code == 400


def test_activate_with_track_stock_rejected(client, world):
    world['product'].track_stock = True
    db.session.commit()
    recipe = _create(client, world)
    assert _link(client, world, recipe['id'], stock_active=True).status_code == 400


def test_link_inactive_recipe_rejected(client, world):
    recipe = _create(client, world)
    client.delete(f"/api/v1/recipes/{recipe['id']}", headers=_headers(client, world['editor']))
    assert _link(client, world, recipe['id']).status_code == 400


def test_link_product_with_other_recipe_conflicts(client, world):
    first = _create(client, world, name='Primera')
    second = _create(client, world, name='Segunda')
    assert _link(client, world, first['id']).status_code == 200
    assert _link(client, world, second['id']).status_code == 409


def test_removing_yield_with_active_stock_conflicts(client, world):
    recipe = _create(client, world)
    assert _link(client, world, recipe['id'], stock_active=True).status_code == 200
    response = client.put(f"/api/v1/recipes/{recipe['id']}", headers=_headers(client, world['editor']),
                          json=_payload(world, yield_quantity=None, yield_unit=None))
    assert response.status_code == 409


def test_delete_recipe_with_active_stock_conflicts(client, world):
    recipe = _create(client, world)
    assert _link(client, world, recipe['id'], stock_active=True).status_code == 200
    assert client.delete(f"/api/v1/recipes/{recipe['id']}",
                         headers=_headers(client, world['editor'])).status_code == 409


def test_list_filters_bases(client, world):
    headers = _headers(client, world['editor'])
    base = _create(client, world, name='Base')
    linked = _create(client, world, name='Con producto')
    assert _link(client, world, linked['id']).status_code == 200
    bases = client.get('/api/v1/recipes?bases=1', headers=headers).get_json()
    assert [r['name'] for r in bases] == ['Base'] and bases[0]['is_base'] is True
    found = client.get('/api/v1/recipes?q=con', headers=headers).get_json()
    assert [r['name'] for r in found] == ['Con producto']
    detail = client.get(f"/api/v1/recipes/{base['id']}", headers=headers).get_json()
    assert detail['used_in'] == []
