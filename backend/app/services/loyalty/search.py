"""Búsqueda de clientes para la caja: por QR exacto o por palabras de nombre, mail o teléfono."""
from app.models.loyalty import Customer, normalize_search


def find_customers(q, limit=20):
    q = (q or '').strip()
    if not q:
        return []
    exact = Customer.query.filter_by(qr_token=q).first()
    if exact is not None:
        return [exact]
    words = normalize_search(q).split()
    if len(''.join(words)) < 2:
        return []
    query = Customer.query
    for word in words:
        query = query.filter(Customer.search_text.like(f'%{word}%'))
    return query.order_by(Customer.last_name, Customer.first_name, Customer.id).limit(limit).all()


def mask_email(email):
    if not email or '@' not in email:
        return None
    local, domain = email.split('@', 1)
    return f'{local[:2]}…@{domain}'


def mask_phone(phone):
    if not phone:
        return None
    digits = phone.strip()
    if len(digits) <= 6:
        return digits
    return f'{digits[:2]}…{digits[-4:]}'
