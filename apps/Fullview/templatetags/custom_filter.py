from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def remove_leading_zeros(value):
    """
    Removes leading zeros from a string or number
    """
    if value is None:
        return "0"
    
    # Convert to string to handle various input types
    string_value = str(value)
    
    # If starts with multiple zeros, remove them leaving one if needed
    if string_value.startswith('00'):
        string_value = string_value[2:]
    
    return string_value

@register.filter
def clean_percentage(value, decimal_places=2):
    """
    Removes leading zeros and formats as float with specified decimal places
    """
    if value is None:
        return "0.00"
    
    # First remove leading zeros
    cleaned_value = remove_leading_zeros(value)
    
    try:
        # Convert to float and format
        float_value = float(cleaned_value)
        
        # For small numbers like 0.0076, convert to 0.76
        if float_value != 0 and abs(float_value) < 0.1:
            # Count leading zeros after the decimal point
            str_value = str(abs(float_value))
            decimal_part = str_value.split('.')[1]
            leading_zeros = 0
            for char in decimal_part:
                if char == '0':
                    leading_zeros += 1
                else:
                    break
            
            # Multiply by 10^(leading_zeros + 2) to convert 0.0076 to 0.76
            if leading_zeros > 0:
                float_value *= (10 ** leading_zeros)
        
        return floatformat(float_value, decimal_places)
    except (ValueError, TypeError):
        return "0.00"

@register.filter
def multiply_int(value, arg):
    """
    Multiplies an integer by another integer
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0 