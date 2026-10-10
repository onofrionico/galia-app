from pos_helpers import auth_headers, make_user, pos_app  # noqa: F401


def test_authenticated_request_does_not_print_token(pos_app, capsys):
    client = pos_app.test_client()
    waiter = make_user('mozo@test.com', modules=('Camarero',))
    headers = auth_headers(client, waiter)
    token = headers['Authorization'].split(' ')[1]
    capsys.readouterr()
    response = client.get('/api/v1/pos/changes', headers=headers)
    assert response.status_code == 200
    out = capsys.readouterr().out
    assert token not in out
    assert token[:20] not in out
    assert 'Bearer' not in out
    assert '[AUTH DEBUG]' not in out and '[REQUEST]' not in out
