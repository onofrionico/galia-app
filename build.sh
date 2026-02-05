#!/usr/bin/env bash
set -o errexit

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gunicorn

echo "Running database migrations..."
cd backend
flask db upgrade
cd ..

echo "Build completed successfully!"
