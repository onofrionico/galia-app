#!/usr/bin/env bash
set -o errexit

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gunicorn

echo "Running database migrations..."
cd backend
flask db upgrade
python create_notifications_tables.py
python add_extraordinary_fields.py

echo "Loading initial recipe book (only while there are no recipes yet)..."
python scripts/import_recetario.py --apply --if-empty || echo "AVISO: la carga inicial del recetario no se aplico (ver el informe arriba)"
cd ..

echo "Build completed successfully!"
