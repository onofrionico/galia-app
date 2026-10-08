from app.utils.fudo_client import FudoClient


def _client_with_pages(monkeypatch, pages_by_endpoint):
    client = FudoClient(api_key='key', api_secret='secret')
    calls = []

    def fake_request(endpoint, params=None):
        calls.append((endpoint, params))
        pages = pages_by_endpoint[endpoint]
        index = params['page[number]'] - 1
        return {'data': pages[index] if index < len(pages) else []}

    monkeypatch.setattr(client, '_make_request', fake_request)
    return client, calls


def test_get_all_products_paginates_until_short_page(monkeypatch):
    full_page = [{'id': str(i)} for i in range(500)]
    client, calls = _client_with_pages(monkeypatch, {'/products': [full_page, [{'id': '500'}]]})

    products = client.get_all_products()

    assert len(products) == 501
    assert [c[1]['page[number]'] for c in calls] == [1, 2]
    assert calls[0] == ('/products', {'page[size]': 500, 'page[number]': 1})


def test_get_all_product_categories(monkeypatch):
    client, calls = _client_with_pages(monkeypatch, {'/product-categories': [[{'id': '1'}, {'id': '2'}]]})

    assert [c['id'] for c in client.get_all_product_categories()] == ['1', '2']
    assert calls[0][0] == '/product-categories'
