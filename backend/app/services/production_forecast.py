"""Pronóstico de producción por turno. Puro: recibe líneas vendidas ya leídas de la base.

Ver docs/superpowers/specs/2026-11-09-reports-franjas-design.md.
"""
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from app.utils.timezone_utils import convert_utc_to_argentina

MAX_WEEKS_BACK = 52
SUNDAY = 6


@dataclass(frozen=True)
class DayPart:
    id: int
    name: str
    start: time
    end: time


@dataclass(frozen=True)
class SoldLine:
    """Unidades vendidas de una fila del reporte (`key`) en una venta."""
    fecha: date
    moment_utc: datetime
    key: tuple
    quantity: Decimal
    variant_id: int | None
    from_combo: bool = False


def day_part_for(local, parts):
    """Id del turno con inicio <= hora < fin, o None si cae fuera de todos."""
    for part in parts:
        if part.start <= local < part.end:
            return part.id
    return None


def _holiday_window_start(target, holiday_months):
    return target - relativedelta(months=holiday_months)


def _last_open(target, sale_days, holidays, count):
    """Los últimos `count` días target-7k abiertos y no feriados."""
    found = []
    for k in range(1, MAX_WEEKS_BACK + 1):
        day = target - timedelta(days=7 * k)
        if day in sale_days and day not in holidays:
            found.append(day)
            if len(found) == count:
                break
    return found


def comparable_days(target, sale_days, holidays, weeks, holiday_months):
    """Días con los que se compara `target`, del más reciente al más viejo."""
    if target not in holidays:
        return _last_open(target, sale_days, holidays, weeks)
    since = _holiday_window_start(target, holiday_months)
    past_holidays = [h for h in holidays if since <= h < target and h in sale_days]
    # Ancla en el domingo siguiente al último domingo anterior a target: target-7k recorre los domingos previos.
    days_since_sunday = (target.weekday() - SUNDAY) % 7 or 7
    anchor = target - timedelta(days=days_since_sunday) + timedelta(days=7)
    sundays = _last_open(anchor, sale_days, holidays, weeks)
    return sorted(set(past_holidays) | set(sundays), reverse=True)


def expand_components(lines, components):
    """Agrega, por cada línea de un combo, una línea por componente. Un solo nivel."""
    expanded = list(lines)
    for line in lines:
        for component_id, quantity in components.get(line.variant_id, ()) if line.variant_id else ():
            expanded.append(replace(line, key=('v', component_id), quantity=line.quantity * quantity,
                                    variant_id=component_id, from_combo=True))
    return expanded


def _local_time(moment_utc):
    return convert_utc_to_argentina(moment_utc).time()


def _avg(value, days):
    return round(float(value) / days, 1)


def forecast(lines, days, parts):
    """Promedio por día comparable de cada fila: total, por turno, fuera de turno y desde combos."""
    if not days:
        return {}
    wanted = set(days)
    sums = defaultdict(lambda: {'total': Decimal(0), 'por_turno': defaultdict(Decimal), 'fuera_de_turno': Decimal(0),
                                'desde_combos': Decimal(0)})
    for line in lines:
        if line.fecha not in wanted:
            continue
        row = sums[line.key]
        row['total'] += line.quantity
        part_id = day_part_for(_local_time(line.moment_utc), parts)
        if part_id is None:
            row['fuera_de_turno'] += line.quantity
        else:
            row['por_turno'][part_id] += line.quantity
        if line.from_combo:
            row['desde_combos'] += line.quantity
    count = len(wanted)
    result = {}
    for key, row in sums.items():
        if row['total'] <= 0:
            continue
        result[key] = {
            'total': _avg(row['total'], count),
            'por_turno': {part.id: _avg(row['por_turno'][part.id], count) for part in parts},
            'fuera_de_turno': _avg(row['fuera_de_turno'], count),
            'desde_combos': _avg(row['desde_combos'], count),
        }
    return result


def weekday_averages(lines, sale_days, holidays, until, weeks, holiday_months):
    """Por fila: promedio de unidades de cada día de la semana (0=lunes) y de los feriados."""
    since = until - timedelta(days=7 * weeks)
    by_weekday = defaultdict(set)
    for day in sale_days:
        if since <= day < until and day not in holidays:
            by_weekday[day.weekday()].add(day)
    holiday_since = _holiday_window_start(until, holiday_months)
    holiday_days = {h for h in holidays if holiday_since <= h < until and h in sale_days}

    sums = defaultdict(lambda: defaultdict(Decimal))
    for line in lines:
        if line.fecha in holiday_days:
            sums[line.key]['feriado'] += line.quantity
        elif line.fecha in by_weekday[line.fecha.weekday()]:
            sums[line.key][line.fecha.weekday()] += line.quantity

    result = {}
    for key, row in sums.items():
        averages = {wd: _avg(row[wd], len(by_weekday[wd])) if by_weekday[wd] else 0.0 for wd in range(7)}
        averages['feriado'] = _avg(row['feriado'], len(holiday_days)) if holiday_days else None
        result[key] = averages
    return result
