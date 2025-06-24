from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def remove_page_param(query_string):
    """
    Remove page parameter from query string
    """
    if not query_string:
        return ''
    
    # Remove page parameter using regex
    cleaned = re.sub(r'page=\d+&?', '', query_string)
    
    # Remove trailing & if present
    if cleaned.endswith('&'):
        cleaned = cleaned[:-1]
        
    return cleaned

@register.filter
def remove_sort_params(query_string):
    """
    Remove sort and order parameters from query string
    """
    if not query_string:
        return ''
    
    # Remove sort and order parameters using regex
    cleaned = re.sub(r'sort=\w+&?', '', query_string)
    cleaned = re.sub(r'order=\w+&?', '', cleaned)
    
    # Remove trailing & if present
    if cleaned.endswith('&'):
        cleaned = cleaned[:-1]
        
    return cleaned

@register.simple_tag
def sorting_url(request, sort_field, current_sort, current_order):
    """Generate a URL for sorting with the correct order parameter."""
    # Start with base parameters
    params = []
    
    # Determine the order
    if sort_field == current_sort:
        # Toggle the current order
        new_order = 'asc' if current_order == 'desc' else 'desc'
    else:
        # Default orders for different fields
        if sort_field in ['symbol', 'company_name']:
            new_order = 'asc'
        else:
            new_order = 'desc'
    
    # Add sort and order parameters
    params.append(f'sort={sort_field}')
    params.append(f'order={new_order}')
    
    # Add all other parameters except sort, order, and page
    for key, value in request.GET.items():
        if key not in ['sort', 'order', 'page']:
            params.append(f'{key}={value}')
    
    # Construct the URL
    return '?' + '&'.join(params)

@register.simple_tag
def pagination_url(request, page_number):
    """Generate a URL for pagination with the correct page parameter."""
    # Start with base parameters
    params = []
    
    # Add page parameter
    params.append(f'page={page_number}')
    
    # Add all other parameters except page
    for key, value in request.GET.items():
        if key != 'page':
            params.append(f'{key}={value}')
    
    # Construct the URL
    return '?' + '&'.join(params)
