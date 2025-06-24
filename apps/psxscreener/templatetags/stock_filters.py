from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
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

@register.filter
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

@register.filter
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

@register.simple_tag
def percentage_of_range(value, low, high):
    """Calculate where a value falls in a range as a percentage"""
    if not value or not low or not high:
        return 50  # Default to middle
    
    try:
        value = float(value)
        low = float(low)
        high = float(high)
        
        if high == low:  # Avoid division by zero
            return 50
            
        percentage = (value - low) / (high - low) * 100
        return min(max(percentage, 0), 100)  # Clamp between 0-100
    except (ValueError, TypeError):
        return 50 