from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _to_decimal(value):
    if value in (None, ''):
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(',', '').strip())
    except (InvalidOperation, AttributeError, ValueError):
        return Decimal('0')


@register.filter(name='vnd')
def vnd(value):
    amount = int(_to_decimal(value).quantize(Decimal('1')))
    return f'{amount:,}'.replace(',', '.')
