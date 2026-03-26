from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.configurable_list import ConfigurableList
from app.models.exchange_rate import ExchangeRate
from app.services.base_service import BaseService


class ConfigurableListService(BaseService):
    """Service for managing configurable lists"""
    
    model = ConfigurableList
    
    def get_by_type(self, list_type, active_only=True):
        """
        Get all items for a specific list type
        
        Args:
            list_type: Type of list to retrieve
            active_only: If True, only return active items
            
        Returns:
            List of ConfigurableList objects
        """
        query = ConfigurableList.query.filter_by(list_type=list_type)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(
            ConfigurableList.display_order,
            ConfigurableList.value
        ).all()
    
    def get_active_values(self, list_type):
        """Get list of active values for a specific type"""
        return ConfigurableList.get_active_values(list_type)
    
    def create_item(self, data, user_id=None):
        """
        Create a new configurable list item
        
        Args:
            data: Dictionary with item data
            user_id: ID of user creating the item
            
        Returns:
            Created ConfigurableList object
            
        Raises:
            ValueError: If validation fails or duplicate exists
        """
        try:
            existing = ConfigurableList.query.filter_by(
                list_type=data.get('list_type'),
                value=data.get('value')
            ).first()
            
            if existing:
                if existing.is_active:
                    raise ValueError(f'Value "{data.get("value")}" already exists for {data.get("list_type")}')
                else:
                    existing.is_active = True
                    existing.display_order = data.get('display_order', existing.display_order)
                    db.session.commit()
                    
                    self._log_audit(
                        entity_type='ConfigurableList',
                        entity_id=existing.id,
                        action='reactivate',
                        user_id=user_id
                    )
                    
                    return existing
            
            item = ConfigurableList(
                list_type=data.get('list_type'),
                value=data.get('value'),
                display_order=data.get('display_order', 0),
                is_active=data.get('is_active', True),
                created_by_user_id=user_id
            )
            
            db.session.add(item)
            db.session.commit()
            
            self._log_audit(
                entity_type='ConfigurableList',
                entity_id=item.id,
                action='create',
                user_id=user_id
            )
            
            return item
            
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f'Database integrity error: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise
    
    def update_item(self, item_id, data, user_id=None):
        """
        Update a configurable list item
        
        Args:
            item_id: ID of item to update
            data: Dictionary with updated data
            user_id: ID of user updating the item
            
        Returns:
            Updated ConfigurableList object
            
        Raises:
            ValueError: If item not found or validation fails
        """
        item = ConfigurableList.query.get(item_id)
        if not item:
            raise ValueError('Configurable list item not found')
        
        if 'value' in data and data['value'] != item.value:
            existing = ConfigurableList.query.filter_by(
                list_type=item.list_type,
                value=data['value']
            ).filter(ConfigurableList.id != item_id).first()
            
            if existing:
                raise ValueError(f'Value "{data["value"]}" already exists for {item.list_type}')
            
            item.value = data['value']
        
        if 'display_order' in data:
            item.display_order = data['display_order']
        
        if 'is_active' in data:
            item.is_active = data['is_active']
        
        db.session.commit()
        
        self._log_audit(
            entity_type='ConfigurableList',
            entity_id=item.id,
            action='update',
            user_id=user_id
        )
        
        return item
    
    def deactivate_item(self, item_id, user_id=None):
        """
        Deactivate a configurable list item (soft delete)
        
        Args:
            item_id: ID of item to deactivate
            user_id: ID of user deactivating the item
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If item not found or in use
        """
        item = ConfigurableList.query.get(item_id)
        if not item:
            raise ValueError('Configurable list item not found')
        
        if not item.is_active:
            raise ValueError('Item is already inactive')
        
        if self._is_value_in_use(item.list_type, item.value):
            raise ValueError(f'Cannot deactivate "{item.value}" because it is currently in use')
        
        item.is_active = False
        db.session.commit()
        
        self._log_audit(
            entity_type='ConfigurableList',
            entity_id=item.id,
            action='deactivate',
            user_id=user_id
        )
        
        return True
    
    def _is_value_in_use(self, list_type, value):
        """Check if a configurable list value is currently in use"""
        if list_type == 'product_category':
            from app.models.product import Product
            return Product.query.filter_by(category=value, is_deleted=False).count() > 0
        
        if list_type == 'unit_of_measure':
            from app.models.product import Product
            return Product.query.filter_by(unit_of_measure=value, is_deleted=False).count() > 0
        
        if list_type == 'payment_term':
            from app.models.supplier import Supplier
            return Supplier.query.filter_by(payment_terms=value, is_deleted=False).count() > 0
        
        return False
    
    def reorder_items(self, list_type, item_orders, user_id=None):
        """
        Reorder items in a list
        
        Args:
            list_type: Type of list to reorder
            item_orders: List of dicts with id and display_order
            user_id: ID of user reordering items
            
        Returns:
            Number of items updated
        """
        updated_count = 0
        
        for order_data in item_orders:
            item = ConfigurableList.query.get(order_data.get('id'))
            if item and item.list_type == list_type:
                item.display_order = order_data.get('display_order', 0)
                updated_count += 1
        
        db.session.commit()
        
        return updated_count


class ExchangeRateService(BaseService):
    """Service for managing exchange rates"""
    
    model = ExchangeRate
    
    def create_rate(self, data, user_id=None):
        """
        Create a new exchange rate
        
        Args:
            data: Dictionary with rate data
            user_id: ID of user creating the rate
            
        Returns:
            Created ExchangeRate object
            
        Raises:
            ValueError: If validation fails or duplicate exists
        """
        try:
            existing = ExchangeRate.query.filter_by(
                from_currency=data.get('from_currency'),
                to_currency=data.get('to_currency'),
                effective_date=data.get('effective_date')
            ).first()
            
            if existing:
                raise ValueError(
                    f'Exchange rate for {data.get("from_currency")}/{data.get("to_currency")} '
                    f'on {data.get("effective_date")} already exists'
                )
            
            rate = ExchangeRate(
                from_currency=data.get('from_currency'),
                to_currency=data.get('to_currency'),
                rate=data.get('rate'),
                effective_date=data.get('effective_date'),
                source=data.get('source', 'manual'),
                created_by_user_id=user_id
            )
            
            db.session.add(rate)
            db.session.commit()
            
            self._log_audit(
                entity_type='ExchangeRate',
                entity_id=rate.id,
                action='create',
                user_id=user_id
            )
            
            return rate
            
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f'Database integrity error: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise
    
    def update_rate(self, rate_id, data, user_id=None):
        """
        Update an exchange rate
        
        Args:
            rate_id: ID of rate to update
            data: Dictionary with updated data
            user_id: ID of user updating the rate
            
        Returns:
            Updated ExchangeRate object
            
        Raises:
            ValueError: If rate not found or validation fails
        """
        rate = ExchangeRate.query.get(rate_id)
        if not rate:
            raise ValueError('Exchange rate not found')
        
        if 'rate' in data:
            rate.rate = data['rate']
        
        if 'source' in data:
            rate.source = data['source']
        
        db.session.commit()
        
        self._log_audit(
            entity_type='ExchangeRate',
            entity_id=rate.id,
            action='update',
            user_id=user_id
        )
        
        return rate
    
    def delete_rate(self, rate_id, user_id=None):
        """
        Delete an exchange rate
        
        Args:
            rate_id: ID of rate to delete
            user_id: ID of user deleting the rate
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If rate not found
        """
        rate = ExchangeRate.query.get(rate_id)
        if not rate:
            raise ValueError('Exchange rate not found')
        
        self._log_audit(
            entity_type='ExchangeRate',
            entity_id=rate.id,
            action='delete',
            user_id=user_id
        )
        
        db.session.delete(rate)
        db.session.commit()
        
        return True
    
    def get_rates_by_currency(self, from_currency=None, to_currency=None, date_from=None, date_to=None):
        """
        Get exchange rates with filters
        
        Args:
            from_currency: Filter by source currency
            to_currency: Filter by target currency
            date_from: Filter from this date
            date_to: Filter to this date
            
        Returns:
            List of ExchangeRate objects
        """
        query = ExchangeRate.query
        
        if from_currency:
            query = query.filter_by(from_currency=from_currency)
        
        if to_currency:
            query = query.filter_by(to_currency=to_currency)
        
        if date_from:
            query = query.filter(ExchangeRate.effective_date >= date_from)
        
        if date_to:
            query = query.filter(ExchangeRate.effective_date <= date_to)
        
        return query.order_by(ExchangeRate.effective_date.desc()).all()
    
    def get_rate_for_date(self, from_currency, to_currency, target_date=None):
        """
        Get exchange rate for a specific date (or most recent)
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            target_date: Date to get rate for (defaults to today)
            
        Returns:
            ExchangeRate object or None
        """
        if target_date is None:
            target_date = date.today()
        
        return ExchangeRate.query.filter(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.effective_date <= target_date
        ).order_by(ExchangeRate.effective_date.desc()).first()
    
    def get_latest_rates(self):
        """Get the most recent exchange rate for each currency pair"""
        from sqlalchemy import func
        
        subquery = db.session.query(
            ExchangeRate.from_currency,
            ExchangeRate.to_currency,
            func.max(ExchangeRate.effective_date).label('max_date')
        ).group_by(
            ExchangeRate.from_currency,
            ExchangeRate.to_currency
        ).subquery()
        
        rates = db.session.query(ExchangeRate).join(
            subquery,
            db.and_(
                ExchangeRate.from_currency == subquery.c.from_currency,
                ExchangeRate.to_currency == subquery.c.to_currency,
                ExchangeRate.effective_date == subquery.c.max_date
            )
        ).all()
        
        return rates
