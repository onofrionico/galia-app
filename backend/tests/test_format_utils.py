import pytest
from app.utils.format_utils import format_money_ar, parse_money_ar


class TestFormatMoneyAr:
    def test_format_basic_amount(self):
        assert format_money_ar(1234.56) == "1.234,56"
    
    def test_format_large_amount(self):
        assert format_money_ar(1234567.89) == "1.234.567,89"
    
    def test_format_small_amount(self):
        assert format_money_ar(100) == "100,00"
    
    def test_format_zero(self):
        assert format_money_ar(0) == "0,00"
    
    def test_format_negative(self):
        assert format_money_ar(-1234.56) == "-1.234,56"
    
    def test_format_none(self):
        assert format_money_ar(None) == "0,00"
    
    def test_format_string_number(self):
        assert format_money_ar("1234.56") == "1.234,56"
    
    def test_format_decimal_rounding(self):
        assert format_money_ar(1234.999) == "1.235,00"
    
    def test_format_very_large_number(self):
        assert format_money_ar(1000000000.50) == "1.000.000.000,50"


class TestParseMoneyAr:
    def test_parse_basic_amount(self):
        assert parse_money_ar("1.234,56") == 1234.56
    
    def test_parse_large_amount(self):
        assert parse_money_ar("1.234.567,89") == 1234567.89
    
    def test_parse_small_amount(self):
        assert parse_money_ar("100,00") == 100.0
    
    def test_parse_zero(self):
        assert parse_money_ar("0,00") == 0.0
    
    def test_parse_negative(self):
        assert parse_money_ar("-1.234,56") == -1234.56
    
    def test_parse_empty_string(self):
        assert parse_money_ar("") == 0.0
    
    def test_parse_none(self):
        assert parse_money_ar(None) == 0.0
    
    def test_parse_number(self):
        assert parse_money_ar(1234.56) == 1234.56
    
    def test_parse_int(self):
        assert parse_money_ar(1234) == 1234.0
    
    def test_parse_invalid_string(self):
        assert parse_money_ar("invalid") == 0.0


class TestRoundTrip:
    def test_format_and_parse(self):
        original = 1234567.89
        formatted = format_money_ar(original)
        parsed = parse_money_ar(formatted)
        assert abs(parsed - original) < 0.01
    
    def test_format_and_parse_negative(self):
        original = -1234.56
        formatted = format_money_ar(original)
        parsed = parse_money_ar(formatted)
        assert abs(parsed - original) < 0.01
