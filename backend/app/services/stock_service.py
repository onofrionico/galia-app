from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from app.extensions import db
from app.models.product_variant import ProductVariant
from app.models.product_recipe_item import ProductRecipeItem
from app.models.supply import Supply
from app.utils.validation import parse_decimal

MAX_SALE_QUANTITY = Decimal('1000000')
STOCK_STEP = Decimal('0.001')


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

    Las filas se bloquean con SELECT ... FOR UPDATE (ver move_stock).
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

    variants, supplies = stock_requirements(dict(variant_needed))
    move_stock(variants, supplies, sign=-1)


def stock_requirements(variant_quantities, extra_supplies=None):
    """Calcula qué stock hay que mover para estas cantidades vendidas.

    variant_quantities: {product_variant_id: Decimal}; extra_supplies: {supply_id: Decimal}
    (por ejemplo, insumos de modificadores). Devuelve (variantes, insumos) como {id: Decimal}:
    - producto con receta: insumos de la receta × cantidad;
    - producto sin receta con track_stock: la propia variante;
    - producto sin receta sin track_stock: nada.
    Levanta ValueError si una variante no existe.
    """
    variants = defaultdict(Decimal)
    supplies = defaultdict(Decimal)
    for variant_id, quantity in variant_quantities.items():
        variant = db.session.get(ProductVariant, variant_id)
        if not variant:
            raise ValueError(f'ProductVariant {variant_id} no encontrado')
        product = variant.product
        if product.has_recipe:
            for recipe_item in ProductRecipeItem.query.filter_by(product_id=product.id).all():
                supplies[recipe_item.supply_id] += Decimal(recipe_item.quantity) * quantity
        elif product.track_stock:
            variants[variant_id] += quantity
    for supply_id, quantity in (extra_supplies or {}).items():
        supplies[supply_id] += quantity
    # Las columnas de stock son Numeric(10,3): cuantizar mantiene simétricos descuento y devolución.
    return ({k: v.quantize(STOCK_STEP, rounding=ROUND_HALF_UP) for k, v in variants.items()},
            {k: v.quantize(STOCK_STEP, rounding=ROUND_HALF_UP) for k, v in supplies.items()})


def move_stock(variants, supplies, sign, allow_negative=False):
    """Aplica un movimiento de stock: sign=-1 descuenta, sign=1 devuelve.

    Bloquea las filas con SELECT ... FOR UPDATE en orden de id (evita deadlocks) y recarga
    sus valores. Con sign=-1 y allow_negative=False valida que alcance y, si falta, no
    modifica nada. El llamador hace commit o rollback.
    """
    if sign not in (-1, 1):
        raise ValueError('sign debe ser -1 o 1')
    if any(q < 0 for q in (*variants.values(), *supplies.values())):
        raise ValueError('Las cantidades de stock no pueden ser negativas')
    locked_variants = (
        ProductVariant.query.filter(ProductVariant.id.in_(list(variants)))
        .order_by(ProductVariant.id).with_for_update().populate_existing().all()
        if variants else []
    )
    locked_supplies = (
        Supply.query.filter(Supply.id.in_(list(supplies)))
        .order_by(Supply.id).with_for_update().populate_existing().all()
        if supplies else []
    )
    if len(locked_variants) != len(variants) or len(locked_supplies) != len(supplies):
        raise ValueError('Producto o insumo no encontrado')
    if sign < 0 and not allow_negative:
        for variant in locked_variants:
            if Decimal(variant.stock_quantity) < variants[variant.id]:
                raise ValueError(f'Stock insuficiente para {variant.product.name} - {variant.name}')
        for supply in locked_supplies:
            if Decimal(supply.stock_quantity) < supplies[supply.id]:
                raise ValueError(f'Stock insuficiente de {supply.name}')
    for variant in locked_variants:
        variant.stock_quantity = Decimal(variant.stock_quantity) + sign * variants[variant.id]
    for supply in locked_supplies:
        supply.stock_quantity = Decimal(supply.stock_quantity) + sign * supplies[supply.id]
    db.session.flush()
