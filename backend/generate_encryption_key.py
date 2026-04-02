#!/usr/bin/env python3
"""
Generate encryption key for email password encryption
Run this script and add the output to your .env file as EMAIL_ENCRYPTION_KEY
"""
from cryptography.fernet import Fernet

if __name__ == '__main__':
    key = Fernet.generate_key()
    print("Generated encryption key:")
    print(key.decode())
    print("\nAdd this to your .env file:")
    print(f"EMAIL_ENCRYPTION_KEY={key.decode()}")
