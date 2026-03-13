#!/usr/bin/env python3
"""
Script de prueba para ver la estructura real de los gastos de Fudo
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.utils.fudo_client import FudoClient

def test_expenses():
    """Test fetching expenses from Fudo API"""
    try:
        client = FudoClient()
        
        # Get expenses from March 1, 2026
        response = client.get_expenses(page_size=5, page_number=1)
        
        print("=" * 80)
        print("PRIMEROS 5 GASTOS DE FUDO:")
        print("=" * 80)
        
        for i, expense in enumerate(response.get('data', [])[:5], 1):
            print(f"\n{'=' * 80}")
            print(f"GASTO #{i}")
            print(f"{'=' * 80}")
            print(f"ID: {expense.get('id')}")
            print(f"Type: {expense.get('type')}")
            print(f"\nAttributes:")
            print(json.dumps(expense.get('attributes', {}), indent=2, ensure_ascii=False))
            print(f"\nRelationships:")
            print(json.dumps(expense.get('relationships', {}), indent=2, ensure_ascii=False))
            
            # Check amount specifically
            amount = expense.get('attributes', {}).get('amount')
            print(f"\n>>> AMOUNT VALUE: {amount} (type: {type(amount).__name__})")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_expenses()
