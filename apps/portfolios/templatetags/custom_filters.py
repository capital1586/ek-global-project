import json
from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter(name="multiply_int")
def multiply_int(value, arg):
    """Multiplies the value by the arg."""
    return int(value) * int(arg)


@register.filter(name="json_dumps")
def json_dumps(value):
    """Returns the JSON dumps of the value."""
    return json.dumps(value)


@register.filter(name="format_market_cap")
def format_market_cap(value):
    """Format market cap values in B/M format"""
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
        if value >= 1000000000:
            return f"{value / 1000000000:.2f}B"
        elif value >= 1000000:
            return f"{value / 1000000:.2f}M"
        else:
            return f"{value:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


@register.filter(name="format_large_number")
def format_large_number(value):
    """Format large numbers with K/M/B suffixes"""
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
        if value >= 1000000000:
            return f"{value / 1000000000:.2f}B"
        elif value >= 1000000:
            return f"{value / 1000000:.2f}M"
        elif value >= 1000:
            return f"{value / 1000:.1f}K"
        else:
            return f"{value:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


@register.filter(name="calculate_dividend")
def calculate_dividend(price, yield_value):
    """Calculate estimated annual dividend from price and yield percentage"""
    if price is None or yield_value is None:
        return "N/A"
    
    try:
        price = float(price)
        yield_value = float(yield_value)
        return f"{(price * yield_value / 100):.2f}"
    except (ValueError, TypeError):
        return "N/A"


@register.filter(name="percentage_of_range")
def percentage_of_range(value, range_tuple):
    """Calculate where a value falls in a range as a percentage"""
    if not value or not range_tuple or len(range_tuple) != 2:
        return 50  # Default to middle
    
    try:
        value = float(value)
        low = float(range_tuple[0])
        high = float(range_tuple[1])
        
        if high == low:  # Avoid division by zero
            return 50
            
        percentage = (value - low) / (high - low) * 100
        return min(max(percentage, 0), 100)  # Clamp between 0-100
    except (ValueError, TypeError, IndexError):
        return 50
