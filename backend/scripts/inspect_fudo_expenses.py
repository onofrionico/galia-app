#!/usr/bin/env python3
"""Muestra los NOMBRES de atributos y relaciones de /expenses (sin valores) para validar el parseo.

Uso: cd backend && venv/Scripts/python.exe scripts/inspect_fudo_expenses.py
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from dotenv import load_dotenv

load_dotenv()

from app.utils.fudo_client import FudoClient


def main():
    client = FudoClient()
    response = client.get_expenses(page_size=50, page_number=1)
    expense_attrs, expense_rels = set(), set()
    statuses = set()
    for expense in response.get('data', []):
        expense_attrs.update(expense.get('attributes', {}).keys())
        expense_rels.update(expense.get('relationships', {}).keys())
        statuses.add(expense.get('attributes', {}).get('status'))
    included = defaultdict(set)
    for item in response.get('included', []):
        included[item.get('type')].update(item.get('attributes', {}).keys())

    print('Expense attributes:', sorted(expense_attrs))
    print('Expense relationships:', sorted(expense_rels))
    print('Expense status values:', sorted(str(s) for s in statuses))
    for kind, keys in sorted(included.items()):
        print(f'included[{kind}] attributes:', sorted(keys))


if __name__ == '__main__':
    main()
