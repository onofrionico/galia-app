from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from decimal import Decimal
from app.extensions import db
from app.models.purchase import Purchase
from app.models.supplier import Supplier
from app.models.purchase_item import PurchaseItem
from app.models.product import Product

class DashboardService:
    """Service for dashboard analytics and aggregations"""
    
    @staticmethod
    def get_suppliers_dashboard(start_date=None, end_date=None, currency='ARS'):
        """
        Get supplier purchase analytics for dashboard
        
        Args:
            start_date: Start date for filtering (default: first day of current month)
            end_date: End date for filtering (default: today)
            currency: Currency for amounts (default: ARS)
            
        Returns:
            dict: Dashboard data with metrics, top suppliers, and distribution
        """
        # Default to current month if no dates provided
        if not start_date:
            today = datetime.now()
            start_date = datetime(today.year, today.month, 1).date()
        if not end_date:
            end_date = datetime.now().date()
        
        # Get purchases in date range
        purchases_query = Purchase.query.filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency
            )
        )
        
        # Calculate key metrics
        total_purchases = purchases_query.count()
        total_spent = db.session.query(
            func.sum(Purchase.total_amount)
        ).filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency
            )
        ).scalar() or Decimal('0')
        
        avg_order_value = (total_spent / total_purchases) if total_purchases > 0 else Decimal('0')
        
        # Get unique suppliers count
        unique_suppliers = db.session.query(
            func.count(func.distinct(Purchase.supplier_id))
        ).filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False
            )
        ).scalar() or 0
        
        # Get top suppliers by spending
        top_suppliers = db.session.query(
            Supplier.id,
            Supplier.name,
            Supplier.tax_id,
            func.count(Purchase.id).label('purchase_count'),
            func.sum(Purchase.total_amount).label('total_spent'),
            func.avg(Purchase.total_amount).label('avg_order_value')
        ).join(
            Purchase, Purchase.supplier_id == Supplier.id
        ).filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency
            )
        ).group_by(
            Supplier.id, Supplier.name, Supplier.tax_id
        ).order_by(
            func.sum(Purchase.total_amount).desc()
        ).limit(10).all()
        
        # Format top suppliers
        top_suppliers_data = []
        for supplier in top_suppliers:
            percentage = (float(supplier.total_spent) / float(total_spent) * 100) if total_spent > 0 else 0
            top_suppliers_data.append({
                'id': supplier.id,
                'name': supplier.name,
                'tax_id': supplier.tax_id,
                'purchase_count': supplier.purchase_count,
                'total_spent': float(supplier.total_spent),
                'avg_order_value': float(supplier.avg_order_value),
                'percentage': round(percentage, 2)
            })
        
        # Get spending distribution by category (top product categories)
        category_distribution = db.session.query(
            Product.category,
            func.sum(PurchaseItem.total_price).label('total_spent')
        ).join(
            PurchaseItem, PurchaseItem.product_id == Product.id
        ).join(
            Purchase, Purchase.id == PurchaseItem.purchase_id
        ).filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency,
                Product.category.isnot(None)
            )
        ).group_by(
            Product.category
        ).order_by(
            func.sum(PurchaseItem.total_price).desc()
        ).limit(8).all()
        
        category_data = []
        for cat in category_distribution:
            category_data.append({
                'category': cat.category,
                'total_spent': float(cat.total_spent)
            })
        
        # Get spending trend (daily aggregation)
        spending_trend = db.session.query(
            Purchase.purchase_date,
            func.sum(Purchase.total_amount).label('daily_total')
        ).filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency
            )
        ).group_by(
            Purchase.purchase_date
        ).order_by(
            Purchase.purchase_date
        ).all()
        
        trend_data = []
        for day in spending_trend:
            trend_data.append({
                'date': day.purchase_date.isoformat(),
                'total': float(day.daily_total)
            })
        
        # Get payment status distribution
        payment_status_dist = db.session.query(
            Purchase.payment_status,
            func.count(Purchase.id).label('count'),
            func.sum(Purchase.total_amount).label('total')
        ).filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency
            )
        ).group_by(
            Purchase.payment_status
        ).all()
        
        payment_status_data = []
        for status in payment_status_dist:
            payment_status_data.append({
                'status': status.payment_status,
                'count': status.count,
                'total': float(status.total)
            })
        
        # Calculate comparison with previous period
        period_days = (end_date - start_date).days + 1
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date - timedelta(days=1)
        
        prev_total_spent = db.session.query(
            func.sum(Purchase.total_amount)
        ).filter(
            and_(
                Purchase.purchase_date >= prev_start_date,
                Purchase.purchase_date <= prev_end_date,
                Purchase.is_deleted == False,
                Purchase.currency == currency
            )
        ).scalar() or Decimal('0')
        
        spending_change = 0
        if prev_total_spent > 0:
            spending_change = ((float(total_spent) - float(prev_total_spent)) / float(prev_total_spent)) * 100
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'metrics': {
                'total_spent': float(total_spent),
                'total_purchases': total_purchases,
                'avg_order_value': float(avg_order_value),
                'unique_suppliers': unique_suppliers,
                'spending_change': round(spending_change, 2),
                'currency': currency
            },
            'top_suppliers': top_suppliers_data,
            'category_distribution': category_data,
            'spending_trend': trend_data,
            'payment_status': payment_status_data
        }
    
    @staticmethod
    def get_supplier_comparison(supplier_ids, start_date=None, end_date=None, currency='ARS'):
        """
        Compare multiple suppliers side by side
        
        Args:
            supplier_ids: List of supplier IDs to compare
            start_date: Start date for filtering
            end_date: End date for filtering
            currency: Currency for amounts
            
        Returns:
            dict: Comparison data for selected suppliers
        """
        if not start_date:
            today = datetime.now()
            start_date = datetime(today.year, today.month, 1).date()
        if not end_date:
            end_date = datetime.now().date()
        
        comparison_data = []
        
        for supplier_id in supplier_ids:
            supplier = Supplier.query.get(supplier_id)
            if not supplier:
                continue
            
            # Get purchases for this supplier
            purchases = Purchase.query.filter(
                and_(
                    Purchase.supplier_id == supplier_id,
                    Purchase.purchase_date >= start_date,
                    Purchase.purchase_date <= end_date,
                    Purchase.is_deleted == False,
                    Purchase.currency == currency
                )
            ).all()
            
            total_spent = sum(p.total_amount for p in purchases)
            purchase_count = len(purchases)
            avg_order = (total_spent / purchase_count) if purchase_count > 0 else Decimal('0')
            
            comparison_data.append({
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'total_spent': float(total_spent),
                'purchase_count': purchase_count,
                'avg_order_value': float(avg_order)
            })
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'comparison': comparison_data
        }
    
    @staticmethod
    def get_purchase_frequency_analysis(supplier_id=None, days=90):
        """
        Analyze purchase frequency patterns for suppliers
        
        Args:
            supplier_id: Optional supplier ID to filter by
            days: Number of days to analyze (default: 90)
        
        Returns:
            dict with frequency metrics, timeline, and gap detection
        """
        from datetime import timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Build base query
        query = Purchase.query.filter(
            and_(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.is_deleted == False
            )
        )
        
        if supplier_id:
            query = query.filter(Purchase.supplier_id == supplier_id)
        
        purchases = query.order_by(Purchase.purchase_date.asc()).all()
        
        if not purchases:
            return {
                'period_days': days,
                'total_purchases': 0,
                'suppliers': []
            }
        
        # Group purchases by supplier
        supplier_purchases = {}
        for purchase in purchases:
            sid = purchase.supplier_id
            if sid not in supplier_purchases:
                supplier_purchases[sid] = []
            supplier_purchases[sid].append(purchase)
        
        # Analyze each supplier
        supplier_analysis = []
        
        for sid, supplier_purch in supplier_purchases.items():
            supplier = Supplier.query.get(sid)
            if not supplier:
                continue
            
            # Sort by date
            supplier_purch.sort(key=lambda p: p.purchase_date)
            
            # Calculate frequency metrics
            purchase_count = len(supplier_purch)
            
            # Calculate days between purchases
            days_between = []
            for i in range(1, len(supplier_purch)):
                delta = (supplier_purch[i].purchase_date - supplier_purch[i-1].purchase_date).days
                days_between.append(delta)
            
            avg_days_between = sum(days_between) / len(days_between) if days_between else 0
            
            # Calculate purchases per week/month
            purchases_per_week = (purchase_count / days) * 7 if days > 0 else 0
            purchases_per_month = (purchase_count / days) * 30 if days > 0 else 0
            
            # Detect gaps (periods longer than 1.5x average)
            gaps = []
            if avg_days_between > 0:
                threshold = avg_days_between * 1.5
                for i in range(1, len(supplier_purch)):
                    delta = (supplier_purch[i].purchase_date - supplier_purch[i-1].purchase_date).days
                    if delta > threshold:
                        gaps.append({
                            'start_date': supplier_purch[i-1].purchase_date.isoformat(),
                            'end_date': supplier_purch[i].purchase_date.isoformat(),
                            'days': delta,
                            'expected_days': round(avg_days_between, 1)
                        })
            
            # Check for current gap
            days_since_last = (end_date - supplier_purch[-1].purchase_date).days
            current_gap = None
            if avg_days_between > 0 and days_since_last > avg_days_between * 1.5:
                current_gap = {
                    'last_purchase_date': supplier_purch[-1].purchase_date.isoformat(),
                    'days_since': days_since_last,
                    'expected_days': round(avg_days_between, 1),
                    'overdue_by': round(days_since_last - avg_days_between, 1)
                }
            
            # Build timeline
            timeline = []
            for p in supplier_purch:
                # Count items safely
                try:
                    items_count = len(p.items) if hasattr(p, 'items') else 0
                except:
                    items_count = 0
                
                timeline.append({
                    'date': p.purchase_date.isoformat(),
                    'purchase_id': p.id,
                    'total_amount': float(p.total_amount),
                    'currency': p.currency,
                    'items_count': items_count
                })
            
            # Calculate regularity score (0-100, higher is more regular)
            regularity_score = 0
            if len(days_between) > 1:
                # Calculate coefficient of variation (lower is more regular)
                mean = avg_days_between
                variance = sum((d - mean) ** 2 for d in days_between) / len(days_between)
                std_dev = variance ** 0.5
                cv = (std_dev / mean) if mean > 0 else 0
                # Convert to score (0 = very irregular, 100 = perfectly regular)
                regularity_score = max(0, min(100, 100 - (cv * 50)))
            
            supplier_analysis.append({
                'supplier_id': sid,
                'supplier_name': supplier.name,
                'metrics': {
                    'total_purchases': purchase_count,
                    'avg_days_between': round(avg_days_between, 1),
                    'purchases_per_week': round(purchases_per_week, 2),
                    'purchases_per_month': round(purchases_per_month, 2),
                    'regularity_score': round(regularity_score, 1),
                    'min_days_between': min(days_between) if days_between else 0,
                    'max_days_between': max(days_between) if days_between else 0
                },
                'timeline': timeline,
                'gaps': gaps,
                'current_gap': current_gap,
                'first_purchase_date': supplier_purch[0].purchase_date.isoformat(),
                'last_purchase_date': supplier_purch[-1].purchase_date.isoformat()
            })
        
        # Sort by total purchases descending
        supplier_analysis.sort(key=lambda x: x['metrics']['total_purchases'], reverse=True)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'total_purchases': len(purchases),
            'total_suppliers': len(supplier_analysis),
            'suppliers': supplier_analysis
        }
