from collections import defaultdict
from decimal import Decimal

from app.extensions import db
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.supply import Supply
from app.utils.validation import parse_decimal

MAX_SALE_QUANTITY = Decimal('1000000')


def deduct_stock_for_sale(sale_items):
    """
    Descuenta stock para una venta.
    sale_items: lista de {'product_variant_id': int, 'quantity': número > 0}

    Lógica:
    - Producto con receta (has_recipe=True): descuenta los insumos (Supply) según la
      receta. Siempre se descuentan, sin importar track_stock.
    - Producto sin receta y track_stock=True: descuenta de ProductVariant.stock_quantity.
    - Producto sin receta y track_stock=False: no se controla stock, no se descuenta nada.

    Primero se valida y se agrega todo (cantidades por variante e insumo) y recién
    después se aplica, de modo que si algún ítem falla no se modifica nada. Levanta
    ValueError si la cantidad es inválida, la variante no existe o el stock no alcanza.

    El llamador es responsable de hacer commit o rollback (acá sólo se hace flush).

    NOTA: no hay bloqueo de filas. Antes de usar esta función con ventas concurrentes,
    el subproyecto POS debe agregar `with_for_update()` en las lecturas o reemplazar el
    descuento por un UPDATE atómico condicional (stock_quantity >= cantidad).
    """
    variant_needed = defaultdict(Decimal)
    for item in sale_items:
        if not isinstance(item, dict):
            raise ValueError('Ítem de venta inválido')
        quantity = parse_decimal(item.get('quantity'), 'La cantidad', maximum=MAX_SALE_QUANTITY)
        if quantity <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        variant_id = item.get('product_variant_id')
        if isinstance(variant_id, bool) or not isinstance(variant_id, int):
            raise ValueError(f'ProductVariant {variant_id} no encontrado')
        variant_needed[variant_id] += quantity

    variant_deductions = []  # (variant, cantidad)
    supply_needed = defaultdict(Decimal)
    for variant_id, quantity in variant_needed.items():
        variant = db.session.get(ProductVariant, variant_id)
        if not variant:
            raise ValueError(f'ProductVariant {variant_id} no encontrado')
        product = variant.product
        if product.has_recipe:
            recipe_items = ProductRecipeItem.query.filter_by(product_id=product.id).all()
            for recipe_item in recipe_items:
                supply_needed[recipe_item.supply_id] += Decimal(recipe_item.quantity) * quantity
        elif product.track_stock:
            if Decimal(variant.stock_quantity) < quantity:
                raise ValueError(f'Stock insuficiente para {product.name} - {variant.name}')
            variant_deductions.append((variant, quantity))

    supply_deductions = []
    for supply_id, needed in supply_needed.items():
        supply = db.session.get(Supply, supply_id)
        if Decimal(supply.stock_quantity) < needed:
            raise ValueError(f'Stock insuficiente de {supply.name}')
        supply_deductions.append((supply, needed))

    for variant, quantity in variant_deductions:
        variant.stock_quantity = Decimal(variant.stock_quantity) - quantity
    for supply, needed in supply_deductions:
        supply.stock_quantity = Decimal(supply.stock_quantity) - needed

    db.session.flush()
