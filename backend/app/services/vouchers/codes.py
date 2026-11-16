"""Códigos de voucher: 10 caracteres sin letras confusas, mostrados como GAL-XXXXX-XXXXX."""
import re
import secrets

ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # sin 0, O, 1, I, L
CODE_LENGTH = 10
PREFIX = 'GAL'


def generate_code():
    return ''.join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(raw):
    """Mayúsculas y solo alfanuméricos; quita el prefijo GAL si viene tipeado completo."""
    cleaned = re.sub(r'[^A-Z0-9]', '', (raw or '').upper())
    if len(cleaned) == CODE_LENGTH + len(PREFIX) and cleaned.startswith(PREFIX):
        cleaned = cleaned[len(PREFIX):]
    return cleaned


def format_code(code):
    return f'{PREFIX}-{code[:5]}-{code[5:]}'
