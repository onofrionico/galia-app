#!/usr/bin/env python3
"""
Script para cargar datos de prueba en la base de datos.
Este script es un wrapper que ejecuta seed_test_data.py

Uso:
    python load_test_data.py

Nota: Asegúrate de haber ejecutado las migraciones base primero con:
    flask db upgrade
"""

import sys
import os

# Simplemente ejecutar el script de seed
if __name__ == '__main__':
    import seed_test_data
    seed_test_data.seed_data()
