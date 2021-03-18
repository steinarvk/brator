import decimal

from .numberformat import _format_number

def test_format_number():
    assert _format_number(1234567) == "1 234 567"
    assert _format_number(123456) == "123 456"
    assert _format_number(12345) == "12 345"
    assert _format_number(1234) == "1234"
    assert _format_number(2021) == "2021"
    assert _format_number(123) == "123"
    assert _format_number(12) == "12"
    assert _format_number(1) == "1"
    assert _format_number(-1234) == "-1234"
    assert _format_number(decimal.Decimal("1234.56")) == "1234.56"
    assert _format_number(decimal.Decimal("12345.67")) == "12 345.67"
    assert _format_number(12345.5) == "12 345.5"
