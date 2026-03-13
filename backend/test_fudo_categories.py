#!/usr/bin/env python3
"""
Script de prueba para ver la estructura real de las categorías de Fudo
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

def test_categories():
    """Test fetching categories from Fudo API"""
    try:
        client = FudoClient()
        response = client.get_expense_categories()
        
        print("=" * 80)
        print("RESPUESTA COMPLETA DE LA API DE FUDO:")
        print("=" * 80)
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("\n" + "=" * 80)
        print("CATEGORÍAS INDIVIDUALES:")
        print("=" * 80)
        
        for category in response.get('data', []):
            print(f"\nID: {category.get('id')}")
            print(f"Type: {category.get('type')}")
            print(f"Attributes: {json.dumps(category.get('attributes', {}), indent=2, ensure_ascii=False)}")
            print(f"Relationships: {json.dumps(category.get('relationships', {}), indent=2, ensure_ascii=False)}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_categories()
