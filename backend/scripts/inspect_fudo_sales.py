#!/usr/bin/env python3
"""Valida contra Fudo el parseo de ventas e ítems, sin mostrar datos de clientes.

Muestra los NOMBRES de atributos y relaciones de /sales y de `included`, y para hasta 20 ventas
compara `total` contra la suma de ítems calculada como precio x cantidad y como solo precio,
para confirmar si `price` es unitario.

Uso: cd backend && venv/Scripts/python.exe scripts/inspect_fudo_sales.py
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from dotenv import load_dotenv

load_dotenv()

from app.services.sale_fudo_parsing import index_included, request_params  # noqa: E402
from app.utils.fudo_client import FudoClient  # noqa: E402


def main():
    client = FudoClient()
    response = client.get_sales(page_size=20, page_number=1, filters={'saleState': 'in.(CLOSED)'},
                                extra_params={**request_params(), 'sort': '-id'})
    sales = response.get('data', [])
    sale_attrs, sale_rels = set(), set()
    for sale in sales:
        sale_attrs.update((sale.get('attributes') or {}).keys())
        sale_rels.update((sale.get('relationships') or {}).keys())
    included = defaultdict(set)
    for item in response.get('included', []) or []:
        included[item.get('type')].update((item.get('attributes') or {}).keys())

    print('Sale attributes:', sorted(sale_attrs))
    print('Sale relationships:', sorted(sale_rels))
    print('saleType values:', sorted({str((s.get('attributes') or {}).get('saleType')) for s in sales}))
    for kind, keys in sorted(included.items()):
        print(f'included[{kind}] attributes:', sorted(keys))

    index = index_included(response.get('included'))
    print('\nventa: total | sum(price*quantity) | sum(price)  (ítems no cancelados)')
    for sale in sales:
        refs = ((sale.get('relationships') or {}).get('items') or {}).get('data') or []
        items = [index.get((r.get('type'), str(r.get('id')))) for r in refs]
        attrs = [(i.get('attributes') or {}) for i in items if i]
        attrs = [a for a in attrs if not a.get('canceled')]
        by_unit = sum(float(a.get('price') or 0) * float(a.get('quantity') or 0) for a in attrs)
        by_line = sum(float(a.get('price') or 0) for a in attrs)
        total = (sale.get('attributes') or {}).get('total')
        print(f"{sale.get('id')}: {total} | {by_unit:.2f} | {by_line:.2f}")


if __name__ == '__main__':
    main()
