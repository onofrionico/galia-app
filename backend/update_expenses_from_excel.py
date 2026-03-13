#!/usr/bin/env python3
"""
Script para actualizar gastos desde archivo Excel de Fudo
Uso: python update_expenses_from_excel.py <ruta_al_archivo.xlsx>
"""
import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.expense import Expense

def update_expenses_from_excel(excel_path):
    """Update expenses from Excel file"""
    
    if not os.path.exists(excel_path):
        print(f"Error: File not found: {excel_path}")
        return
    
    print(f"Reading Excel file: {excel_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        
        print(f"\nColumns in Excel: {list(df.columns)}")
        print(f"Total rows: {len(df)}")
        
        # Show first few rows to understand structure
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        app = create_app()
        with app.app_context():
            updated = 0
            created = 0
            errors = 0
            
            for idx, row in df.iterrows():
                try:
                    # Extract data from Excel
                    # Adjust column names based on actual Excel structure
                    expense_id = str(row.get('ID', ''))  # Fudo expense ID
                    fecha_str = row.get('Fecha', '')
                    monto = row.get('Monto', 0) or row.get('Total', 0) or row.get('Importe', 0)
                    proveedor = row.get('Proveedor', '') or row.get('Provider', '')
                    descripcion = row.get('Descripción', '') or row.get('Description', '') or row.get('Concepto', '')
                    
                    # Parse date
                    if isinstance(fecha_str, str):
                        try:
                            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                        except:
                            try:
                                fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                            except:
                                fecha = datetime.now().date()
                    elif hasattr(fecha_str, 'date'):
                        fecha = fecha_str.date()
                    else:
                        fecha = datetime.now().date()
                    
                    # Parse amount
                    if isinstance(monto, str):
                        monto = float(monto.replace('$', '').replace(',', '').replace('.', '').strip()) / 100
                    else:
                        monto = float(monto) if monto else 0.0
                    
                    # Find existing expense by external_id or create new
                    if expense_id:
                        expense = Expense.query.filter_by(external_id=expense_id).first()
                    else:
                        expense = None
                    
                    if expense:
                        # Update existing expense
                        expense.fecha = fecha
                        expense.importe = monto
                        if proveedor:
                            expense.proveedor = proveedor
                        if descripcion:
                            expense.comentario = descripcion
                        updated += 1
                    else:
                        # Create new expense
                        expense = Expense(
                            external_id=expense_id if expense_id else None,
                            fecha=fecha,
                            importe=monto,
                            proveedor=proveedor,
                            comentario=descripcion,
                            creado_por='Excel Import'
                        )
                        db.session.add(expense)
                        created += 1
                    
                    if (idx + 1) % 50 == 0:
                        print(f"Processed {idx + 1} rows...")
                        db.session.commit()
                        
                except Exception as e:
                    print(f"Error processing row {idx + 1}: {str(e)}")
                    errors += 1
                    continue
            
            # Final commit
            db.session.commit()
            
            print(f"\n{'='*60}")
            print(f"Import completed:")
            print(f"  - Updated: {updated}")
            print(f"  - Created: {created}")
            print(f"  - Errors: {errors}")
            print(f"{'='*60}")
            
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python update_expenses_from_excel.py <path_to_excel_file>")
        print("\nExample:")
        print("  python update_expenses_from_excel.py ../gastos-237595-20260310-1-qs0jhj.xlsx")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    update_expenses_from_excel(excel_path)
