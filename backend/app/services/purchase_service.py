from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.supplier import Supplier
from app.models.audit_log import AuditLog
from app.services.base_service import BaseService


class PurchaseService(BaseService):
    """Service for managing purchases with automatic price tracking"""
    
    model = Purchase
    
    def create_purchase(self, data, user_id=None):
        """
        Create a new purchase with items and automatic price tracking
        
        Args:
            data: Dictionary with purchase data including items
            user_id: ID of user creating the purchase
            
        Returns:
            Created Purchase object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            supplier_id = data.get('supplier_id')
            if not supplier_id:
                raise ValueError('Supplier ID is required')
            
            supplier = Supplier.query.get(supplier_id)
            if not supplier or supplier.is_deleted:
                raise ValueError('Supplier not found or deleted')
            
            items_data = data.get('items', [])
            if not items_data:
                raise ValueError('At least one purchase item is required')
            
            purchase = Purchase(
                supplier_id=supplier_id,
                related_expense_id=data.get('related_expense_id'),
                purchase_date=data.get('purchase_date'),
                currency=data.get('currency', 'ARS'),
                exchange_rate=data.get('exchange_rate'),
                invoice_number=data.get('invoice_number'),
                cae_number=data.get('cae_number'),
                payment_status=data.get('payment_status', 'pending'),
                notes=data.get('notes'),
                created_by_user_id=user_id,
                modified_by_user_id=user_id
            )
            
            db.session.add(purchase)
            db.session.flush()
            
            total_amount = Decimal('0.00')
            price_updates = []
            
            for item_data in items_data:
                product_id = item_data.get('product_id')
                if not product_id:
                    raise ValueError('Product ID is required for all items')
                
                product = Product.query.get(product_id)
                if not product or product.is_deleted:
                    raise ValueError(f'Product {product_id} not found or deleted')
                
                if product.supplier_id != supplier_id:
                    raise ValueError(f'Product {product.name} does not belong to supplier {supplier.name}')
                
                quantity = Decimal(str(item_data.get('quantity', 0)))
                unit_price = Decimal(str(item_data.get('unit_price', 0)))
                
                if quantity <= 0:
                    raise ValueError('Quantity must be greater than 0')
                if unit_price <= 0:
                    raise ValueError('Unit price must be greater than 0')
                
                item_total = quantity * unit_price
                total_amount += item_total
                
                catalog_price = product.current_price
                
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product_id,
                    product_name_snapshot=product.name,
                    sku_snapshot=product.sku,
                    quantity=quantity,
                    unit_price=unit_price,
                    catalog_price_at_time=catalog_price,
                    total_price=item_total,
                    notes=item_data.get('notes')
                )
                
                db.session.add(purchase_item)
                
                if abs(unit_price - catalog_price) > Decimal('0.01'):
                    price_updates.append({
                        'product': product,
                        'old_price': catalog_price,
                        'new_price': unit_price,
                        'purchase_item': purchase_item
                    })
            
            purchase.total_amount = total_amount
            
            for update in price_updates:
                self._create_price_history_entry(
                    product=update['product'],
                    new_price=update['new_price'],
                    old_price=update['old_price'],
                    source='purchase_entry',
                    purchase_id=purchase.id,
                    user_id=user_id
                )
            
            db.session.commit()
            
            self._log_audit(
                entity_type='Purchase',
                entity_id=purchase.id,
                action='create',
                user_id=user_id
            )
            
            return purchase
            
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f'Database integrity error: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise
    
    def update_purchase(self, purchase_id, data, user_id=None):
        """
        Update an existing purchase with optimistic locking
        
        Args:
            purchase_id: ID of purchase to update
            data: Dictionary with updated purchase data
            user_id: ID of user updating the purchase
            
        Returns:
            Updated Purchase object
            
        Raises:
            ValueError: If validation fails or version conflict
        """
        try:
            purchase = Purchase.query.get(purchase_id)
            if not purchase or purchase.is_deleted:
                raise ValueError('Purchase not found or deleted')
            
            current_version = data.get('version')
            if current_version and purchase.version != current_version:
                raise ValueError('Purchase has been modified by another user. Please refresh and try again.')
            
            if 'supplier_id' in data and data['supplier_id'] != purchase.supplier_id:
                raise ValueError('Cannot change supplier for existing purchase')
            
            if 'purchase_date' in data:
                purchase.purchase_date = data['purchase_date']
            if 'currency' in data:
                purchase.currency = data['currency']
            if 'exchange_rate' in data:
                purchase.exchange_rate = data['exchange_rate']
            if 'invoice_number' in data:
                purchase.invoice_number = data['invoice_number']
            if 'cae_number' in data:
                purchase.cae_number = data['cae_number']
            if 'payment_status' in data:
                purchase.payment_status = data['payment_status']
            if 'notes' in data:
                purchase.notes = data['notes']
            
            if 'items' in data:
                existing_item_ids = {item.id for item in purchase.items.all()}
                new_item_ids = {item.get('id') for item in data['items'] if item.get('id')}
                items_to_delete = existing_item_ids - new_item_ids
                
                for item_id in items_to_delete:
                    item = PurchaseItem.query.get(item_id)
                    if item:
                        db.session.delete(item)
                
                total_amount = Decimal('0.00')
                
                for item_data in data['items']:
                    item_id = item_data.get('id')
                    
                    if item_id:
                        item = PurchaseItem.query.get(item_id)
                        if item and item.purchase_id == purchase_id:
                            item.quantity = Decimal(str(item_data.get('quantity', item.quantity)))
                            item.unit_price = Decimal(str(item_data.get('unit_price', item.unit_price)))
                            item.total_price = item.quantity * item.unit_price
                            item.notes = item_data.get('notes', item.notes)
                            total_amount += item.total_price
                    else:
                        product_id = item_data.get('product_id')
                        product = Product.query.get(product_id)
                        if not product:
                            raise ValueError(f'Product {product_id} not found')
                        
                        quantity = Decimal(str(item_data.get('quantity', 0)))
                        unit_price = Decimal(str(item_data.get('unit_price', 0)))
                        item_total = quantity * unit_price
                        
                        new_item = PurchaseItem(
                            purchase_id=purchase_id,
                            product_id=product_id,
                            product_name_snapshot=product.name,
                            sku_snapshot=product.sku,
                            quantity=quantity,
                            unit_price=unit_price,
                            catalog_price_at_time=product.current_price,
                            total_price=item_total,
                            notes=item_data.get('notes')
                        )
                        db.session.add(new_item)
                        total_amount += item_total
                
                purchase.total_amount = total_amount
            
            purchase.version += 1
            purchase.modified_by_user_id = user_id
            purchase.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            self._log_audit(
                entity_type='Purchase',
                entity_id=purchase.id,
                action='update',
                user_id=user_id
            )
            
            return purchase
            
        except Exception as e:
            db.session.rollback()
            raise
    
    def delete_purchase(self, purchase_id, user_id=None):
        """
        Soft delete a purchase (only allowed within 7 days)
        
        Args:
            purchase_id: ID of purchase to delete
            user_id: ID of user deleting the purchase
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If purchase cannot be deleted
        """
        purchase = Purchase.query.get(purchase_id)
        if not purchase:
            raise ValueError('Purchase not found')
        
        if purchase.is_deleted:
            raise ValueError('Purchase is already deleted')
        
        if not purchase.can_delete():
            raise ValueError('Purchase can only be deleted within 7 days of creation')
        
        purchase.is_deleted = True
        purchase.deleted_at = datetime.utcnow()
        purchase.modified_by_user_id = user_id
        
        db.session.commit()
        
        self._log_audit(
            entity_type='Purchase',
            entity_id=purchase.id,
            action='delete',
            user_id=user_id
        )
        
        return True
    
    def get_purchase_with_items(self, purchase_id):
        """Get purchase with all items and related data"""
        purchase = Purchase.query.get(purchase_id)
        if not purchase or purchase.is_deleted:
            raise ValueError('Purchase not found')
        
        return purchase
    
    def search_purchases(self, filters=None, page=1, per_page=20):
        """
        Search purchases with filters and pagination
        
        Args:
            filters: Dictionary with filter criteria
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with purchases and pagination info
        """
        query = Purchase.query.filter_by(is_deleted=False)
        
        if filters:
            if 'supplier_id' in filters:
                query = query.filter_by(supplier_id=filters['supplier_id'])
            
            if 'payment_status' in filters:
                query = query.filter_by(payment_status=filters['payment_status'])
            
            if 'currency' in filters:
                query = query.filter_by(currency=filters['currency'])
            
            if 'date_from' in filters:
                query = query.filter(Purchase.purchase_date >= filters['date_from'])
            
            if 'date_to' in filters:
                query = query.filter(Purchase.purchase_date <= filters['date_to'])
            
            if 'invoice_number' in filters:
                query = query.filter(Purchase.invoice_number.ilike(f"%{filters['invoice_number']}%"))
        
        query = query.order_by(Purchase.purchase_date.desc(), Purchase.id.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'purchases': paginated.items,
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages
        }
    
    def get_purchase_from_expense(self, expense_id):
        """Get purchase linked to an expense"""
        purchase = Purchase.query.filter_by(
            related_expense_id=expense_id,
            is_deleted=False
        ).first()
        
        return purchase
    
    def update_product_prices_from_purchase(self, purchase_id, price_updates, user_id=None):
        """
        Update product catalog prices based on purchase prices
        
        Args:
            purchase_id: ID of the purchase
            price_updates: List of dicts with product_id and new_price
            user_id: ID of user making the update
            
        Returns:
            Number of products updated
        """
        purchase = Purchase.query.get(purchase_id)
        if not purchase or purchase.is_deleted:
            raise ValueError('Purchase not found')
        
        updated_count = 0
        
        for update in price_updates:
            product_id = update.get('product_id')
            new_price = Decimal(str(update.get('new_price', 0)))
            
            product = Product.query.get(product_id)
            if not product or product.is_deleted:
                continue
            
            old_price = product.current_price
            
            if abs(new_price - old_price) > Decimal('0.01'):
                product.current_price = new_price
                product.modified_by_user_id = user_id
                product.updated_at = datetime.utcnow()
                
                self._create_price_history_entry(
                    product=product,
                    new_price=new_price,
                    old_price=old_price,
                    source='purchase_correction',
                    purchase_id=purchase_id,
                    user_id=user_id
                )
                
                updated_count += 1
        
        db.session.commit()
        
        return updated_count
    
    def _create_price_history_entry(self, product, new_price, old_price, source, purchase_id=None, user_id=None):
        """Create a price history entry"""
        change_percentage = None
        if old_price and old_price > 0:
            change_percentage = ((new_price - old_price) / old_price) * 100
        
        price_history = PriceHistory(
            product_id=product.id,
            price=new_price,
            effective_date=datetime.utcnow().date(),
            change_percentage=change_percentage,
            source=source,
            related_purchase_id=purchase_id,
            created_by_user_id=user_id
        )
        
        db.session.add(price_history)
        
        return price_history
    
    def _log_audit(self, entity_type, entity_id, action, user_id=None):
        """Helper method to log audit entries"""
        if user_id:
            AuditLog.log_change(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id
            )
            db.session.commit()
