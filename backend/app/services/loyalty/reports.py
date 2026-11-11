"""Reportes de fidelización (5.1–5.4 del diseño)."""
from datetime import datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import Sale
from app.models.loyalty import Customer, LoyaltyMovement, LoyaltySettings, Reward
from app.models.pos import PosSale
from app.utils.timezone_utils import convert_argentina_to_utc


def _visits_query():
    return db.session.query(PosSale.customer_id, func.count(PosSale.id), func.max(PosSale.business_date)).filter(
        PosSale.status == 'closed', PosSale.is_practice.is_(False), PosSale.customer_id.isnot(None))


def _window(today):
    return today - timedelta(days=LoyaltySettings.get().active_days - 1), today


def active_customers(today):
    since, until = _window(today)
    rows = (_visits_query().filter(PosSale.business_date >= since, PosSale.business_date <= until)
            .group_by(PosSale.customer_id).all())
    customers = {c.id: c for c in Customer.query.filter(Customer.id.in_([r[0] for r in rows])).all()}
    result = [{'id': cid, 'full_name': customers[cid].full_name, 'last_visit': last.isoformat(), 'visits': count}
              for cid, count, last in rows]
    return sorted(result, key=lambda r: (r['last_visit'], r['id']), reverse=True)


def inactive_customers(today):
    since, until = _window(today)
    active_ids = {r[0] for r in _visits_query().filter(PosSale.business_date >= since,
                                                       PosSale.business_date <= until)
                  .group_by(PosSale.customer_id).all()}
    last_visits = {r[0]: r[2] for r in _visits_query().filter(PosSale.business_date <= until)
                   .group_by(PosSale.customer_id).all()}
    result = []
    for customer in Customer.query.order_by(Customer.id).all():
        if customer.id in active_ids:
            continue
        last = last_visits.get(customer.id)
        result.append({'id': customer.id, 'full_name': customer.full_name,
                       'last_visit': last.isoformat() if last else None, 'never_visited': last is None})
    return sorted(result, key=lambda r: (r['last_visit'] is not None, r['last_visit'] or '', r['id']))


def _utc_range(desde, hasta):
    start = convert_argentina_to_utc(datetime.combine(desde, datetime.min.time())).replace(tzinfo=None)
    end = convert_argentina_to_utc(datetime.combine(hasta + timedelta(days=1), datetime.min.time())).replace(
        tzinfo=None)
    return start, end


def redemptions(desde, hasta):
    start, end = _utc_range(desde, hasta)
    reversed_ids = db.session.query(LoyaltyMovement.reversal_of_id).filter(
        LoyaltyMovement.reversal_of_id.isnot(None))
    rows = (db.session.query(Reward.name, func.count(LoyaltyMovement.id), func.sum(LoyaltyMovement.reward_cost),
                             func.sum(LoyaltyMovement.pesos_value))
            .join(Reward, Reward.id == LoyaltyMovement.reward_id)
            .filter(LoyaltyMovement.kind == 'redeem', LoyaltyMovement.created_at >= start,
                    LoyaltyMovement.created_at < end, ~LoyaltyMovement.id.in_(reversed_ids))
            .group_by(Reward.name).order_by(Reward.name).all())
    by_reward = [{'reward': name, 'count': count, 'cafecitos': int(cost or 0), 'pesos': float(pesos or 0)}
                 for name, count, cost, pesos in rows]
    return {'total': sum(r['count'] for r in by_reward), 'cafecitos': sum(r['cafecitos'] for r in by_reward),
            'pesos': round(sum(r['pesos'] for r in by_reward), 2), 'by_reward': by_reward}


def _group(total, count):
    total = float(total or 0)
    return {'total': round(total, 2), 'count': count, 'avg_ticket': round(total / count, 2) if count else 0.0}


def registered_vs_unregistered(desde, hasta):
    """Sobre la tabla `sales` (Galia + Fudo). Registrada = proyección de una venta POS con cliente."""
    in_period = [Sale.estado == 'Cerrada', Sale.fecha >= desde, Sale.fecha <= hasta]
    all_total, all_count = db.session.query(func.coalesce(func.sum(Sale.total), 0), func.count(Sale.id)).filter(
        *in_period).one()
    registered_ids = db.session.query(PosSale.sale_id).filter(PosSale.customer_id.isnot(None),
                                                              PosSale.sale_id.isnot(None))
    reg_total, reg_count = db.session.query(func.coalesce(func.sum(Sale.total), 0), func.count(Sale.id)).filter(
        *in_period, Sale.id.in_(registered_ids)).one()
    return {'registered': _group(reg_total, reg_count),
            'unregistered': _group(float(all_total or 0) - float(reg_total or 0), all_count - reg_count)}
