"""Cálculo puro del pronóstico de producción (sin app ni base)."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.services.production_forecast import (DayPart, SoldLine, comparable_days, day_part_for, expand_components,
                                              forecast, weekday_averages)

DESAYUNO, ALMUERZO, MERIENDA = 1, 2, 3
PARTS = [DayPart(DESAYUNO, 'Desayuno', time(8), time(12)), DayPart(ALMUERZO, 'Almuerzo', time(12), time(16)),
         DayPart(MERIENDA, 'Merienda', time(16), time(20))]
MEDIALUNA = ('v', 7)


def _line(day, local_hour, quantity, key=MEDIALUNA, variant_id=7, minute=0):
    """Línea vendida el `day` a la `local_hour` de Argentina (UTC-3)."""
    moment = datetime(day.year, day.month, day.day, local_hour, minute) + timedelta(hours=3)
    return SoldLine(fecha=day, moment_utc=moment, key=key, quantity=Decimal(quantity), variant_id=variant_id)


def test_day_part_boundaries():
    assert day_part_for(time(8), PARTS) == DESAYUNO
    assert day_part_for(time(11, 59), PARTS) == DESAYUNO
    assert day_part_for(time(12), PARTS) == ALMUERZO
    assert day_part_for(time(19, 59), PARTS) == MERIENDA
    assert day_part_for(time(20), PARTS) is None
    assert day_part_for(time(7, 30), PARTS) is None


def test_comparable_days_normal_skips_holidays_and_closed_days():
    target = date(2026, 11, 14)
    sale_days = {date(2026, 11, 7), date(2026, 10, 31), date(2026, 10, 24), date(2026, 10, 17), date(2026, 10, 10),
                 date(2026, 10, 3)}
    holidays = {date(2026, 10, 10)}
    assert comparable_days(target, sale_days, holidays, 4, 12) == [
        date(2026, 11, 7), date(2026, 10, 31), date(2026, 10, 24), date(2026, 10, 17)]
    assert comparable_days(target, sale_days - {date(2026, 10, 24)}, holidays, 4, 12) == [
        date(2026, 11, 7), date(2026, 10, 31), date(2026, 10, 17), date(2026, 10, 3)]


def test_comparable_days_holiday_uses_holidays_and_sundays():
    target = date(2026, 11, 23)
    holidays = {target, date(2026, 10, 12), date(2025, 11, 22)}
    sundays = {date(2026, 11, 22), date(2026, 11, 15), date(2026, 11, 8), date(2026, 11, 1), date(2026, 10, 25)}
    sale_days = sundays | {date(2026, 10, 12), date(2025, 11, 22)}
    assert set(comparable_days(target, sale_days, holidays, 4, 12)) == {
        date(2026, 10, 12), date(2026, 11, 22), date(2026, 11, 15), date(2026, 11, 8), date(2026, 11, 1)}


def test_sunday_holiday_not_counted_as_sunday():
    sale_days = {date(2026, 11, 22), date(2026, 11, 15), date(2026, 11, 8)}
    assert comparable_days(date(2026, 11, 29), sale_days, {date(2026, 11, 15)}, 2, 12) == [
        date(2026, 11, 22), date(2026, 11, 8)]


def test_utc_moment_is_converted_to_local():
    day = date(2026, 11, 7)
    line = SoldLine(fecha=day, moment_utc=datetime(2026, 11, 7, 13, 30), key=MEDIALUNA, quantity=Decimal(1),
                    variant_id=7)
    assert forecast([line], [day], PARTS)[MEDIALUNA]['por_turno'][DESAYUNO] == 1.0


def test_forecast_averages_and_counts_missing_as_zero():
    day1, day2 = date(2026, 11, 7), date(2026, 10, 31)
    result = forecast([_line(day1, 9, 10)], [day1, day2], PARTS)[MEDIALUNA]
    assert result['total'] == 5.0
    assert result['por_turno'][DESAYUNO] == 5.0
    assert result['por_turno'][MERIENDA] == 0.0


def test_forecast_out_of_shift():
    day = date(2026, 11, 7)
    result = forecast([_line(day, 21, 2), _line(day, 9, 1)], [day], PARTS)[MEDIALUNA]
    assert result['fuera_de_turno'] == 2.0 and result['total'] == 3.0


def test_forecast_ignores_days_not_comparable_and_empty_days():
    day = date(2026, 11, 7)
    assert forecast([_line(day, 9, 4)], [date(2026, 10, 31)], PARTS) == {}
    assert forecast([_line(day, 9, 4)], [], PARTS) == {}


def test_components_keep_day_part_of_combo_sale():
    day = date(2026, 11, 7)
    combo = _line(day, 17, 3, key=('v', 50), variant_id=50)
    lines = expand_components([combo], {50: [(7, Decimal(2))]})
    result = forecast(lines, [day], PARTS)
    assert result[MEDIALUNA]['total'] == 6.0
    assert result[MEDIALUNA]['por_turno'][MERIENDA] == 6.0
    assert result[MEDIALUNA]['desde_combos'] == 6.0
    assert result[('v', 50)]['total'] == 3.0 and result[('v', 50)]['desde_combos'] == 0.0


def test_components_one_level_only():
    day = date(2026, 11, 7)
    combo = _line(day, 9, 1, key=('v', 50), variant_id=50)
    lines = expand_components([combo], {50: [(7, Decimal(1))], 7: [(8, Decimal(1))]})
    assert sorted(line.key for line in lines) == [('v', 7), ('v', 50)]


def test_weekday_averages():
    mon1, mon2, holiday = date(2026, 11, 2), date(2026, 11, 9), date(2026, 11, 3)
    lines = [_line(mon1, 9, 4), _line(mon2, 9, 6), _line(holiday, 9, 10)]
    sale_days = {mon1, mon2, holiday}
    result = weekday_averages(lines, sale_days, {holiday}, date(2026, 11, 14), 4, 12)[MEDIALUNA]
    assert result[0] == 5.0
    assert result['feriado'] == 10.0
    assert result[3] == 0.0
