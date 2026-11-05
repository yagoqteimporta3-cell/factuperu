from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def money(value):
    """Formatea un número como 1,234.56"""
    try:
        v = Decimal(str(value or 0))
    except Exception:
        return '0.00'
    return f'{v:,.2f}'


@register.filter
def soles(value):
    """S/ 1,234.56"""
    return f'S/ {money(value)}'
