import pytest

from app import create_app

# Endpoints sin autenticación a propósito.
PUBLIC_ENDPOINTS = {
    'static',
    'health',
    'auth.login',
    'csv_import.status',
    'config.get_branding_config',
    'csv_import.download_template',
}


@pytest.fixture(scope='module')
def view_functions():
    return create_app('testing').view_functions


def test_every_endpoint_declares_access_control(view_functions):
    missing = sorted(
        endpoint for endpoint, view in view_functions.items()
        if endpoint not in PUBLIC_ENDPOINTS and not getattr(view, '_access_control', None)
    )
    assert missing == []


def test_public_whitelist_only_lists_existing_endpoints(view_functions):
    assert PUBLIC_ENDPOINTS - set(view_functions) == set()


@pytest.mark.parametrize('blueprint, expected', [
    ('menu', 'module:Menu'),
    ('reports', 'module:Reports'),
    ('fudo_sync', 'admin'),
])
def test_blueprint_admin_endpoints_use_expected_control(view_functions, blueprint, expected):
    controls = {
        getattr(view, '_access_control', None)
        for endpoint, view in view_functions.items()
        if endpoint.startswith(f'{blueprint}.')
    }
    assert expected in controls
    assert 'admin' not in controls or expected == 'admin'
