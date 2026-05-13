from app.extensions import db
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.supply import Supply


def deduct_stock_for_sale(sale_items):
    """
    Descuenta stock para una venta.
    sale_items: lista de {'product_variant_id': int, 'quantity': int}

    Lógica:
    - Si producto.has_recipe = False: descuenta de ProductVariant.stock_quantity
    - Si producto.has_recipe = True: descuenta de Supply según receta

    Levanta excepción si hay stock insuficiente o variante no existe.
    """
    for item in sale_items:
        variant = ProductVariant.query.get(item['product_variant_id'])
        if not variant:
            raise ValueError(f"ProductVariant {item['product_variant_id']} no encontrado")

        product = variant.product
        quantity = item['quantity']

        if not product.has_recipe:
            if float(variant.stock_quantity) < quantity:
                raise ValueError(f"Stock insuficiente para {product.name} - {variant.name}")
            variant.stock_quantity = float(variant.stock_quantity) - quantity
        else:
            recipe_items = ProductRecipeItem.query.filter_by(product_id=product.id).all()
            for recipe_item in recipe_items:
                supply = recipe_item.supply
                needed = float(recipe_item.quantity) * quantity
                if float(supply.stock_quantity) < needed:
                    raise ValueError(f"Stock insuficiente de {supply.name}")
                supply.stock_quantity = float(supply.stock_quantity) - needed

    db.session.flush()
