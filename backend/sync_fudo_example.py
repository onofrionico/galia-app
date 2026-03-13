#!/usr/bin/env python3
"""
Script de ejemplo para sincronizar datos desde Fudo API

Este script muestra cómo usar el cliente de Fudo para sincronizar
ventas y gastos desde Fudo a Galia.

Uso:
    python sync_fudo_example.py --sync sales --start-date 2024-01-01 --end-date 2024-01-31
    python sync_fudo_example.py --sync expenses --start-date 2024-01-01 --end-date 2024-01-31
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

from app.utils.fudo_client import FudoClient

load_dotenv()


def sync_sales(start_date=None, end_date=None):
    """Sincronizar ventas desde Fudo"""
    print("🔄 Iniciando sincronización de ventas desde Fudo...")
    
    try:
        client = FudoClient()
        
        if start_date and end_date:
            print(f"📅 Rango de fechas: {start_date} a {end_date}")
            sales = client.get_all_sales(start_date=start_date, end_date=end_date)
        else:
            print("📅 Obteniendo todas las ventas...")
            sales = client.get_all_sales()
        
        print(f"✅ Se obtuvieron {len(sales)} ventas desde Fudo")
        
        if sales:
            print("\n📊 Ejemplo de venta:")
            print(f"  ID: {sales[0].get('id')}")
            print(f"  Total: {sales[0].get('attributes', {}).get('total', 0) / 100}")
            print(f"  Estado: {sales[0].get('attributes', {}).get('status')}")
            print(f"  Fecha: {sales[0].get('attributes', {}).get('closedAt')}")
        
        return sales
        
    except Exception as e:
        print(f"❌ Error sincronizando ventas: {str(e)}")
        return []


def sync_expenses(start_date=None, end_date=None):
    """Sincronizar gastos desde Fudo"""
    print("🔄 Iniciando sincronización de gastos desde Fudo...")
    
    try:
        client = FudoClient()
        
        if start_date and end_date:
            print(f"📅 Rango de fechas: {start_date} a {end_date}")
            expenses = client.get_all_expenses(start_date=start_date, end_date=end_date)
        else:
            print("📅 Obteniendo todos los gastos...")
            expenses = client.get_all_expenses()
        
        print(f"✅ Se obtuvieron {len(expenses)} gastos desde Fudo")
        
        if expenses:
            print("\n📊 Ejemplo de gasto:")
            print(f"  ID: {expenses[0].get('id')}")
            print(f"  Monto: {expenses[0].get('attributes', {}).get('amount', 0) / 100}")
            print(f"  Proveedor: {expenses[0].get('attributes', {}).get('providerName')}")
            print(f"  Fecha: {expenses[0].get('attributes', {}).get('date')}")
        
        return expenses
        
    except Exception as e:
        print(f"❌ Error sincronizando gastos: {str(e)}")
        return []


def get_categories():
    """Obtener categorías de gastos desde Fudo"""
    print("🔄 Obteniendo categorías desde Fudo...")
    
    try:
        client = FudoClient()
        response = client.get_expense_categories()
        categories = response.get('data', [])
        
        print(f"✅ Se obtuvieron {len(categories)} categorías")
        print("\n📋 Categorías de Fudo:")
        for cat in categories:
            print(f"  ID: {cat.get('id')} - {cat.get('attributes', {}).get('name')}")
        
        return categories
        
    except Exception as e:
        print(f"❌ Error obteniendo categorías: {str(e)}")
        return []


def test_connection():
    """Probar conexión con Fudo API"""
    print("🔄 Probando conexión con Fudo API...")
    
    try:
        client = FudoClient()
        token = client._get_valid_token()
        
        print("✅ Conexión exitosa!")
        print(f"  Token expira: {client.token_expiration}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Fudo: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Sincronizar datos desde Fudo API')
    parser.add_argument('--sync', choices=['sales', 'expenses', 'categories', 'test'],
                        help='Tipo de sincronización a realizar')
    parser.add_argument('--start-date', help='Fecha de inicio (YYYY-MM-DD para expenses, YYYY-MM-DDTHH:MM:SSZ para sales)')
    parser.add_argument('--end-date', help='Fecha de fin (YYYY-MM-DD para expenses, YYYY-MM-DDTHH:MM:SSZ para sales)')
    
    args = parser.parse_args()
    
    if not args.sync:
        parser.print_help()
        return
    
    print("=" * 60)
    print("🚀 Script de sincronización con Fudo API")
    print("=" * 60)
    print()
    
    if args.sync == 'test':
        test_connection()
    elif args.sync == 'sales':
        sync_sales(args.start_date, args.end_date)
    elif args.sync == 'expenses':
        sync_expenses(args.start_date, args.end_date)
    elif args.sync == 'categories':
        get_categories()
    
    print()
    print("=" * 60)
    print("✨ Proceso completado")
    print("=" * 60)


if __name__ == '__main__':
    main()
