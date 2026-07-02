import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import time
from app.routes.reports import distribute_shift_hours


def test_distribute_full_hour():
    """Turno de una hora exacta: 10:00-11:00 → {10: 1.0}"""
    result = distribute_shift_hours(time(10, 0), time(11, 0))
    assert result == {10: pytest.approx(1.0)}


def test_distribute_fractional_end():
    """16:00-17:45 → {16: 1.0, 17: 0.75}"""
    result = distribute_shift_hours(time(16, 0), time(17, 45))
    assert result[16] == pytest.approx(1.0)
    assert result[17] == pytest.approx(0.75)


def test_distribute_fractional_start():
    """16:30-18:00 → {16: 0.5, 17: 1.0}"""
    result = distribute_shift_hours(time(16, 30), time(18, 0))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(1.0)


def test_distribute_fractional_both():
    """16:30-17:45 → {16: 0.5, 17: 0.75}"""
    result = distribute_shift_hours(time(16, 30), time(17, 45))
    assert result[16] == pytest.approx(0.5)
    assert result[17] == pytest.approx(0.75)


def test_distribute_multi_hour():
    """9:00-12:00 → {9: 1.0, 10: 1.0, 11: 1.0}"""
    result = distribute_shift_hours(time(9, 0), time(12, 0))
    assert result == {9: pytest.approx(1.0), 10: pytest.approx(1.0), 11: pytest.approx(1.0)}


def test_distribute_total_hours_preserved():
    """La suma de fracciones debe igualar la duración del turno"""
    result = distribute_shift_hours(time(8, 30), time(16, 45))
    total = sum(result.values())
    assert total == pytest.approx(8.25)


def test_distribute_midnight_crossing():
    """Turno que cruza medianoche: 23:00-01:00 → {23: 1.0, 0: 1.0}"""
    result = distribute_shift_hours(time(23, 0), time(1, 0))
    assert result[23] == pytest.approx(1.0)
    assert result[0] == pytest.approx(1.0)
