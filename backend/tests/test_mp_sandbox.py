"""Crea y cancela una orden real en el entorno de prueba de MercadoPago. Solo con MP_TEST_TOKEN y MP_TEST_TERMINAL."""
import os
import uuid
from decimal import Decimal

import pytest

from app.services.mercadopago.client import MpClient, order_state

pytestmark = pytest.mark.skipif(not (os.getenv('MP_TEST_TOKEN') and os.getenv('MP_TEST_TERMINAL')),
                                reason='Sin credenciales de prueba de MercadoPago')


def test_real_order_create_and_cancel():
    client = MpClient(os.environ['MP_TEST_TOKEN'])
    assert client.me()['id']
    terminals = [t['id'] for t in client.list_terminals()]
    assert os.environ['MP_TEST_TERMINAL'] in terminals
    key = str(uuid.uuid4())
    order = client.create_order(os.environ['MP_TEST_TERMINAL'], Decimal('15'), f'galia-test-{key[:8]}', key)
    assert order_state(client.get_order(order['id']))['status'] in ('created', 'processing')
    client.cancel_order(order['id'])
    assert order_state(client.get_order(order['id']))['status'] == 'canceled'
