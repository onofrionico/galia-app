from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import current_app
from app.extensions import db
from app.models import Sale, Expense, FudoSyncLog, FudoOrder, FudoExpense, FudoCashMovement
from app.services.fudo_api_client import FudoAPIClient

class FudoSyncService:
    def __init__(self):
        self.client = FudoAPIClient()
    
    def sync_all(self, days_back: int = 7) -> Dict[str, Any]:
        results = {
            'sales': None,
            'expenses': None,
            'payments': None
        }
        
        try:
            results['sales'] = self.sync_sales(days_back=days_back)
        except Exception as e:
            current_app.logger.error(f"Error syncing sales: {str(e)}")
            results['sales'] = {'error': str(e)}
        
        try:
            results['expenses'] = self.sync_expenses(days_back=days_back)
        except Exception as e:
            current_app.logger.error(f"Error syncing expenses: {str(e)}")
            results['expenses'] = {'error': str(e)}
        
        try:
            results['payments'] = self.sync_payments(days_back=days_back)
        except Exception as e:
            current_app.logger.error(f"Error syncing payments: {str(e)}")
            results['payments'] = {'error': str(e)}
        
        return results
    
    def sync_sales(self, days_back: int = 7) -> Dict[str, Any]:
        sync_log = FudoSyncLog(
            sync_type='sales',
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            from_date = datetime.now() - timedelta(days=days_back)
            to_date = datetime.now()
            
            filters = {
                'createdAt': f"and(gte.{from_date.strftime('%Y-%m-%dT%H:%M:%SZ')},lte.{to_date.strftime('%Y-%m-%dT%H:%M:%SZ')})"
            }
            
            all_sales = []
            page = 1
            page_size = 500
            
            while True:
                response = self.client.get_sales(
                    page_size=page_size,
                    page_number=page,
                    filters=filters
                )
                
                sales_data = response.get('data', [])
                if not sales_data:
                    break
                
                all_sales.extend(sales_data)
                
                if len(sales_data) < page_size:
                    break
                
                page += 1
            
            created = 0
            updated = 0
            failed = 0
            
            for sale_data in all_sales:
                try:
                    self._process_sale(sale_data)
                    
                    existing_fudo_order = FudoOrder.query.filter_by(
                        fudo_order_id=sale_data['id']
                    ).first()
                    
                    if existing_fudo_order:
                        updated += 1
                    else:
                        created += 1
                        
                except Exception as e:
                    current_app.logger.error(f"Error processing sale {sale_data.get('id')}: {str(e)}")
                    failed += 1
            
            sync_log.status = 'completed'
            sync_log.records_processed = len(all_sales)
            sync_log.records_created = created
            sync_log.records_updated = updated
            sync_log.records_failed = failed
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'status': 'success',
                'processed': len(all_sales),
                'created': created,
                'updated': updated,
                'failed': failed
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _process_sale(self, sale_data: Dict[str, Any]) -> Sale:
        fudo_sale_id = sale_data['id']
        attributes = sale_data.get('attributes', {})
        
        fudo_order = FudoOrder.query.filter_by(fudo_order_id=fudo_sale_id).first()
        
        if fudo_order and fudo_order.sale_id:
            sale = Sale.query.get(fudo_order.sale_id)
            if sale:
                self._update_sale_from_fudo(sale, attributes)
                fudo_order.order_data = sale_data
                fudo_order.status = attributes.get('status', 'UNKNOWN')
                fudo_order.updated_at = datetime.utcnow()
                db.session.commit()
                return sale
        
        sale = self._create_sale_from_fudo(attributes)
        db.session.add(sale)
        db.session.flush()
        
        if not fudo_order:
            fudo_order = FudoOrder(
                fudo_order_id=fudo_sale_id,
                sale_id=sale.id,
                order_data=sale_data,
                status=attributes.get('status', 'UNKNOWN'),
                synced_at=datetime.utcnow()
            )
            db.session.add(fudo_order)
        else:
            fudo_order.sale_id = sale.id
            fudo_order.order_data = sale_data
            fudo_order.status = attributes.get('status', 'UNKNOWN')
            fudo_order.updated_at = datetime.utcnow()
        
        db.session.commit()
        return sale
    
    def _create_sale_from_fudo(self, attributes: Dict[str, Any]) -> Sale:
        created_at_str = attributes.get('createdAt')
        closed_at_str = attributes.get('closedAt')
        
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) if created_at_str else datetime.utcnow()
        closed_at = datetime.fromisoformat(closed_at_str.replace('Z', '+00:00')) if closed_at_str else None
        
        sale = Sale(
            fecha=created_at.date(),
            creacion=created_at,
            cerrada=closed_at,
            caja=attributes.get('cashRegister'),
            estado=self._map_fudo_status(attributes.get('status')),
            cliente=attributes.get('customerName'),
            mesa=attributes.get('tableName'),
            sala=attributes.get('roomName'),
            personas=attributes.get('people'),
            camarero=attributes.get('waiterName') or attributes.get('deliverymanName'),
            total=attributes.get('total', 0),
            fiscal=attributes.get('hasFiscalInvoice', False),
            tipo_venta=self._map_sale_type(attributes.get('saleType')),
            comentario=attributes.get('comment'),
            origen='FUdo',
            id_origen=attributes.get('id')
        )
        
        return sale
    
    def _update_sale_from_fudo(self, sale: Sale, attributes: Dict[str, Any]):
        closed_at_str = attributes.get('closedAt')
        if closed_at_str:
            sale.cerrada = datetime.fromisoformat(closed_at_str.replace('Z', '+00:00'))
        
        sale.estado = self._map_fudo_status(attributes.get('status'))
        sale.total = attributes.get('total', sale.total)
        sale.fiscal = attributes.get('hasFiscalInvoice', sale.fiscal)
        
        if attributes.get('comment'):
            sale.comentario = attributes.get('comment')
    
    def _map_fudo_status(self, fudo_status: str) -> str:
        status_map = {
            'IN-COURSE': 'En curso',
            'CLOSED': 'Cerrada',
            'CANCELED': 'Cancelada'
        }
        return status_map.get(fudo_status, 'En curso')
    
    def _map_sale_type(self, fudo_sale_type: str) -> str:
        type_map = {
            'EAT-IN': 'Local',
            'DELIVERY': 'Delivery',
            'TAKE-AWAY': 'Para llevar'
        }
        return type_map.get(fudo_sale_type, 'Local')
    
    def sync_expenses(self, days_back: int = 7) -> Dict[str, Any]:
        sync_log = FudoSyncLog(
            sync_type='expenses',
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            from_date = datetime.now() - timedelta(days=days_back)
            to_date = datetime.now()
            
            filters = {
                'date': f"and(gte.{from_date.strftime('%Y-%m-%d')},lte.{to_date.strftime('%Y-%m-%d')})"
            }
            
            all_expenses = []
            page = 1
            page_size = 500
            
            while True:
                response = self.client.get_expenses(
                    page_size=page_size,
                    page_number=page,
                    filters=filters
                )
                
                expenses_data = response.get('data', [])
                if not expenses_data:
                    break
                
                all_expenses.extend(expenses_data)
                
                if len(expenses_data) < page_size:
                    break
                
                page += 1
            
            created = 0
            updated = 0
            failed = 0
            
            for expense_data in all_expenses:
                try:
                    self._process_expense(expense_data)
                    
                    existing_fudo_expense = FudoExpense.query.filter_by(
                        fudo_expense_id=expense_data['id']
                    ).first()
                    
                    if existing_fudo_expense:
                        updated += 1
                    else:
                        created += 1
                        
                except Exception as e:
                    current_app.logger.error(f"Error processing expense {expense_data.get('id')}: {str(e)}")
                    failed += 1
            
            sync_log.status = 'completed'
            sync_log.records_processed = len(all_expenses)
            sync_log.records_created = created
            sync_log.records_updated = updated
            sync_log.records_failed = failed
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'status': 'success',
                'processed': len(all_expenses),
                'created': created,
                'updated': updated,
                'failed': failed
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _process_expense(self, expense_data: Dict[str, Any]) -> Expense:
        fudo_expense_id = expense_data['id']
        attributes = expense_data.get('attributes', {})
        
        fudo_expense = FudoExpense.query.filter_by(fudo_expense_id=fudo_expense_id).first()
        
        if fudo_expense and fudo_expense.expense_id:
            expense = Expense.query.get(fudo_expense.expense_id)
            if expense:
                self._update_expense_from_fudo(expense, attributes)
                fudo_expense.expense_data = expense_data
                fudo_expense.updated_at = datetime.utcnow()
                db.session.commit()
                return expense
        
        expense = self._create_expense_from_fudo(attributes)
        db.session.add(expense)
        db.session.flush()
        
        if not fudo_expense:
            fudo_expense = FudoExpense(
                fudo_expense_id=fudo_expense_id,
                expense_id=expense.id,
                expense_data=expense_data,
                synced_at=datetime.utcnow()
            )
            db.session.add(fudo_expense)
        else:
            fudo_expense.expense_id = expense.id
            fudo_expense.expense_data = expense_data
            fudo_expense.updated_at = datetime.utcnow()
        
        db.session.commit()
        return expense
    
    def _create_expense_from_fudo(self, attributes: Dict[str, Any]) -> Expense:
        date_str = attributes.get('date')
        due_date_str = attributes.get('dueDate')
        payment_date_str = attributes.get('paymentDate')
        
        fecha = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        fecha_vencimiento = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        
        estado_pago = 'Pagado' if payment_date_str else 'Pendiente'
        
        expense = Expense(
            fecha=fecha,
            fecha_vencimiento=fecha_vencimiento,
            proveedor=attributes.get('providerName'),
            comentario=attributes.get('description'),
            estado_pago=estado_pago,
            importe=attributes.get('amount', 0),
            de_caja=attributes.get('useInCashCount', False),
            numero_comprobante=attributes.get('receiptNumber')
        )
        
        return expense
    
    def _update_expense_from_fudo(self, expense: Expense, attributes: Dict[str, Any]):
        payment_date_str = attributes.get('paymentDate')
        if payment_date_str:
            expense.estado_pago = 'Pagado'
        
        expense.importe = attributes.get('amount', expense.importe)
        
        if attributes.get('description'):
            expense.comentario = attributes.get('description')
    
    def sync_payments(self, days_back: int = 7) -> Dict[str, Any]:
        sync_log = FudoSyncLog(
            sync_type='payments',
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            from_date = datetime.now() - timedelta(days=days_back)
            to_date = datetime.now()
            
            filters = {
                'createdAt': f"and(gte.{from_date.strftime('%Y-%m-%dT%H:%M:%SZ')},lte.{to_date.strftime('%Y-%m-%dT%H:%M:%SZ')})"
            }
            
            all_payments = []
            page = 1
            page_size = 500
            
            while True:
                response = self.client.get_payments(
                    page_size=page_size,
                    page_number=page,
                    filters=filters
                )
                
                payments_data = response.get('data', [])
                if not payments_data:
                    break
                
                all_payments.extend(payments_data)
                
                if len(payments_data) < page_size:
                    break
                
                page += 1
            
            created = 0
            
            for payment_data in all_payments:
                try:
                    self._process_payment(payment_data)
                    created += 1
                except Exception as e:
                    current_app.logger.error(f"Error processing payment {payment_data.get('id')}: {str(e)}")
            
            sync_log.status = 'completed'
            sync_log.records_processed = len(all_payments)
            sync_log.records_created = created
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'status': 'success',
                'processed': len(all_payments),
                'created': created
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _process_payment(self, payment_data: Dict[str, Any]) -> FudoCashMovement:
        fudo_payment_id = payment_data['id']
        attributes = payment_data.get('attributes', {})
        
        existing_movement = FudoCashMovement.query.filter_by(
            fudo_movement_id=fudo_payment_id
        ).first()
        
        if existing_movement:
            existing_movement.movement_data = payment_data
            existing_movement.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_movement
        
        created_at_str = attributes.get('createdAt')
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) if created_at_str else datetime.utcnow()
        
        movement = FudoCashMovement(
            fudo_movement_id=fudo_payment_id,
            movement_type='payment',
            amount=attributes.get('amount', 0),
            cash_register=attributes.get('cashRegister'),
            payment_method=attributes.get('paymentMethodName'),
            description=f"Pago - {attributes.get('paymentMethodName')}",
            movement_date=created_at,
            movement_data=payment_data,
            synced_at=datetime.utcnow()
        )
        
        db.session.add(movement)
        db.session.commit()
        
        return movement
    
    def get_sync_logs(self, limit: int = 50) -> List[FudoSyncLog]:
        return FudoSyncLog.query.order_by(FudoSyncLog.started_at.desc()).limit(limit).all()
