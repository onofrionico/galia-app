"""Migrate from legacy categoria field to normalized category_id system

Revision ID: migrate_to_normalized_categories
Revises: fab7ffda9936
Create Date: 2026-03-04

This migration:
1. Populates expense_categories table from existing categoria values
2. Maps all expenses to their corresponding category_id
3. Removes the legacy categoria and subcategoria columns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'migrate_to_normalized_categories'
down_revision = 'fab7ffda9936'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Step 1: Get all unique categoria values from expenses
    result = conn.execute(text("""
        SELECT DISTINCT categoria 
        FROM expenses 
        WHERE categoria IS NOT NULL 
        AND categoria != '' 
        AND cancelado = false
        ORDER BY categoria
    """))
    
    categorias = [row[0] for row in result]
    
    # Step 2: Define category mappings with expense_type classification
    # Keywords to identify direct expenses (gastos directos)
    direct_keywords = ['mercaderia', 'mercadería', 'insumo', 'materia prima', 'producto', 'stock']
    
    category_mappings = {}
    
    for categoria in categorias:
        # Determine if it's a direct or indirect expense
        cat_lower = categoria.lower()
        expense_type = 'directo' if any(kw in cat_lower for kw in direct_keywords) else 'indirecto'
        
        # Check if category already exists
        existing = conn.execute(text("""
            SELECT id FROM expense_categories WHERE name = :name
        """), {'name': categoria}).fetchone()
        
        if existing:
            category_mappings[categoria] = existing[0]
        else:
            # Insert new category
            result = conn.execute(text("""
                INSERT INTO expense_categories (name, expense_type, is_active, created_at)
                VALUES (:name, :expense_type, true, CURRENT_TIMESTAMP)
                RETURNING id
            """), {'name': categoria, 'expense_type': expense_type})
            
            category_mappings[categoria] = result.fetchone()[0]
    
    # Step 3: Update all expenses with their category_id
    for categoria, category_id in category_mappings.items():
        conn.execute(text("""
            UPDATE expenses 
            SET category_id = :category_id 
            WHERE categoria = :categoria 
            AND category_id IS NULL
        """), {'category_id': category_id, 'categoria': categoria})
    
    # Step 4: Create a default "Sin categoría" category for uncategorized expenses
    result = conn.execute(text("""
        SELECT id FROM expense_categories WHERE name = 'Sin categoría'
    """)).fetchone()
    
    if result:
        default_category_id = result[0]
    else:
        result = conn.execute(text("""
            INSERT INTO expense_categories (name, expense_type, is_active, created_at)
            VALUES ('Sin categoría', 'indirecto', true, CURRENT_TIMESTAMP)
            RETURNING id
        """))
        default_category_id = result.fetchone()[0]
    
    # Assign default category to expenses without categoria
    conn.execute(text("""
        UPDATE expenses 
        SET category_id = :category_id 
        WHERE (categoria IS NULL OR categoria = '') 
        AND category_id IS NULL
        AND cancelado = false
    """), {'category_id': default_category_id})
    
    # Step 5: Drop the legacy columns
    # First drop the index on categoria
    try:
        op.drop_index('idx_expenses_categoria', table_name='expenses')
    except Exception:
        pass  # Index might not exist
    
    # Drop the columns
    op.drop_column('expenses', 'subcategoria')
    op.drop_column('expenses', 'categoria')
    
    # Step 6: Make category_id NOT NULL now that all expenses have a category
    op.alter_column('expenses', 'category_id',
                    existing_type=sa.Integer(),
                    nullable=False)


def downgrade():
    # Add back the legacy columns
    op.add_column('expenses', sa.Column('categoria', sa.String(100), nullable=True))
    op.add_column('expenses', sa.Column('subcategoria', sa.String(100), nullable=True))
    
    # Recreate the index
    op.create_index('idx_expenses_categoria', 'expenses', ['categoria'])
    
    # Make category_id nullable again
    op.alter_column('expenses', 'category_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    # Populate categoria from category_id
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE expenses e
        SET categoria = ec.name
        FROM expense_categories ec
        WHERE e.category_id = ec.id
    """))
