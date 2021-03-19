from django import template

register = template.Library()

def _format_integer(n):
    rv = []
    groupsz = 3
    digits = list(str(n))

    if len(digits) <= 4:
        return "".join(digits)

    while len(digits) > groupsz:
        rv.append("".join(digits[-groupsz:]))
        digits = digits[:-groupsz]

    if digits:
        rv.append("".join(digits))

    return " ".join(reversed(rv))

def _format_nonnegative(n):
    assert n >= 0

    whole = int(n)

    if whole == n:
        return _format_integer(whole)

    frac = str(round(n, 2)).partition(".")[-1]

    return _format_integer(whole) + "." + str(frac)

def _format_number(n):
    if n == 0:
        return "0"
    if n < 0:
        return "-" + _format_nonnegative(-n)
    return _format_nonnegative(n)

@register.simple_tag
def format_number(n):
    return _format_number(n)

@register.simple_tag
def format_percent(n):
    assert 0 <= n <= 100

    if int(n) == n:
        return str(int(n)) + "%"

    return str(round(n, 1)) + "%"

@register.simple_tag
def format_probability(p):
    assert 0 <= p <= 1
    return str(round(p, 4))

@register.simple_tag
def format_probability_as_percent(p):
    assert 0 <= p <= 1
    return str(round(p * 100, 1)) + "%"
