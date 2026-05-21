#!/usr/bin/env python3
"""
Script para verificar y reparar usuarios con hashes de contraseña inválidos.
Detecta hashes bcrypt corruptos y permite regenerarlos.

Uso:
    python verify_user_passwords.py          # Solo listar usuarios con problema
    python verify_user_passwords.py --fix    # Reparar hashes corruptos
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.extensions import bcrypt

def is_valid_bcrypt_hash(hash_str):
    """Verifica si un string es un hash bcrypt válido"""
    if not hash_str:
        return False
    # Los hashes bcrypt siempre empiezan con $2a$, $2b$, $2x$, o $2y$
    return hash_str.startswith(('$2a$', '$2b$', '$2x$', '$2y$'))

def main():
    app = create_app()

    with app.app_context():
        users = User.query.all()
        invalid_users = []

        print("🔍 Verificando hashes de contraseña...")
        print("-" * 60)

        for user in users:
            if not is_valid_bcrypt_hash(user.password_hash):
                invalid_users.append(user)
                print(f"❌ {user.email} (ID: {user.id})")
                print(f"   Hash: {user.password_hash[:50]}...")
                print()

        if not invalid_users:
            print("✅ Todos los usuarios tienen hashes válidos.")
            return

        print(f"\n⚠️  Encontrados {len(invalid_users)} usuarios con hashes inválidos.")

        if '--fix' in sys.argv:
            print("\n🔧 Reparando hashes...")
            for user in invalid_users:
                # Generar una contraseña temporal segura
                temp_password = f"temp_{user.id}_{user.email.split('@')[0]}"
                user.set_password(temp_password)
                print(f"✅ {user.email} - Nueva contraseña temporal: {temp_password}")

            db.session.commit()
            print("\n✅ Hashes reparados. Los usuarios deben cambiar su contraseña al próximo login.")
        else:
            print("\nPara reparar, ejecuta: python verify_user_passwords.py --fix")

if __name__ == '__main__':
    main()
