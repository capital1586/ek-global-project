from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def abs_value(value):
    """Return the absolute value of a number."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def min_value(value, arg):
    """Return the minimum of value and arg."""
    try:
        return min(float(value), float(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value 