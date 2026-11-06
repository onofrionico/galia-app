"""Autenticación de clientes de la carta: Google valida la identidad y emitimos un token propio de cliente.

El token lleva `typ='customer'` y no tiene `user_id`, así que nunca sirve en la app de gestión.
"""
from datetime import datetime, timedelta
from functools import wraps

import jwt
import requests
from flask import current_app, jsonify, request

from app.extensions import db
from app.models.loyalty import Customer
from app.services.loyalty.errors import LoyaltyError

TOKENINFO_URL = 'https://oauth2.googleapis.com/tokeninfo'
TOKEN_DAYS = 90


def verify_google_credential(credential):
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not client_id:
        raise LoyaltyError('El ingreso con Google no está configurado', 503)
    if not credential or not isinstance(credential, str):
        raise LoyaltyError('Falta la credencial de Google', 401)
    try:
        resp = requests.get(TOKENINFO_URL, params={'id_token': credential}, timeout=5)
    except requests.RequestException:
        raise LoyaltyError('No pudimos validar con Google, probá de nuevo', 503)
    if resp.status_code != 200:
        raise LoyaltyError('Credencial de Google inválida', 401)
    data = resp.json()
    if data.get('aud') != client_id or str(data.get('email_verified')).lower() != 'true' or not data.get('sub'):
        raise LoyaltyError('Credencial de Google inválida', 401)
    return {'sub': data['sub'], 'email': data.get('email'), 'given_name': data.get('given_name'),
            'family_name': data.get('family_name')}


def issue_customer_token(customer):
    payload = {'customer_id': customer.id, 'typ': 'customer',
               'exp': datetime.utcnow() + timedelta(days=TOKEN_DAYS)}
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def customer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        token = header.split(' ', 1)[1] if header.startswith('Bearer ') else None
        if not token:
            return jsonify({'error': 'Iniciá sesión'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Sesión vencida, volvé a entrar'}), 401
        if data.get('typ') != 'customer' or not data.get('customer_id'):
            return jsonify({'error': 'Sesión inválida'}), 401
        customer = db.session.get(Customer, data['customer_id'])
        if customer is None:
            return jsonify({'error': 'Sesión inválida'}), 401
        return f(customer, *args, **kwargs)
    return decorated
