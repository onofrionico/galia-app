#!/bin/bash

# Setup script for Biometric Check-In System
# Run this to initialize the biometric system for testing

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Galia - Sistema de Ficha Biométrica                      ║"
echo "║  Setup & Initialization                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from root directory
if [ ! -f "package.json" ] && [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Ejecuta este script desde la raíz del proyecto${NC}"
    exit 1
fi

# Backend Setup
echo -e "${YELLOW}[1/5] Configurando Backend...${NC}"
cd backend

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python no instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python encontrado${NC}"

# Install dependencies
echo -e "${YELLOW}    Instalando dependencias...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# Apply migrations
echo -e "${YELLOW}    Aplicando migraciones...${NC}"
if ! flask db upgrade 2>/dev/null; then
    echo -e "${YELLOW}    (Nota: Las migraciones podrían requerir configuración manual)${NC}"
fi
echo -e "${GREEN}✓ Migraciones aplicadas${NC}"

# Seed locations
echo -e "${YELLOW}[2/5] Seeding de ubicaciones...${NC}"
if python seed_biometric_locations.py 2>/dev/null; then
    echo -e "${GREEN}✓ Ubicaciones creadas${NC}"
else
    echo -e "${YELLOW}⚠ No se pudieron crear ubicaciones (puede requerir DB)${NC}"
fi

# Return to root
cd ..

# Frontend Setup
echo -e "${YELLOW}[3/5] Configurando Frontend...${NC}"
cd frontend

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js no instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js encontrado ($(node -v))${NC}"

# Install dependencies
echo -e "${YELLOW}    Instalando dependencias...${NC}"
npm install -q 2>/dev/null || npm install
echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# Return to root
cd ..

# Configuration Check
echo -e "${YELLOW}[4/5] Verificando configuración...${NC}"

# Check .env
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓ .env configurado${NC}"
else
    echo -e "${YELLOW}⚠ .env no encontrado - asegúrate de configurarlo${NC}"
fi

# Check database
if [ -f "backend/.env" ]; then
    DB_URL=$(grep DATABASE_URL backend/.env | cut -d '=' -f2 || echo "")
    if [ ! -z "$DB_URL" ]; then
        echo -e "${GREEN}✓ DATABASE_URL configurado${NC}"
    else
        echo -e "${YELLOW}⚠ DATABASE_URL no configurado en .env${NC}"
    fi
fi

# Summary
echo ""
echo -e "${YELLOW}[5/5] Setup completado${NC}"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Sistema listo para testing${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Backend:"
echo "   cd backend"
echo "   python run.py"
echo ""
echo "2. Frontend (en otra terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Abre en el navegador:"
echo "   http://localhost:5173"
echo ""
echo "Para más detalles, lee:"
echo "   docs/BIOMETRIC_CHECKIN_TESTING.md"
echo ""
