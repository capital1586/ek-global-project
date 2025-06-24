# news/templatetags/news_template_tags.py
from django import template
from django.http import QueryDict
from urllib.parse import quote_plus # Use quote_plus for query params

register = template.Library()

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Allows modifying query parameters in a URL within a template.
    Usage: {% url 'my_view' %}{% query_transform request key1='val1' key2=None %}
    - Sets key1 to 'val1'.
    - Removes key2 if it exists.
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            query[k] = v
        else:
            query.pop(k, None) # Remove key if value is None
    return '?'+query.urlencode() if query else ''


@register.simple_tag(takes_context=True)
def get_active_filters(context):
    """
    Generates a list of dictionaries representing active filters
    for display, including the URL to remove that filter.
    """
    request = context['request']
    active_filters = []
    filter_map = {
        'q': 'Keyword',
        'category': 'Category',
        'source': 'Source',
        'start_date': 'From Date',
        'end_date': 'To Date',
        'region': 'Region',       # Add new filters
        'sector': 'Sector',
        'industry': 'Industry',
        # Add more mappings as needed
    }

    query_params = request.GET.copy()

    for key, label in filter_map.items():
        value = query_params.get(key)
        if value: # If the filter is active (has a value)
            # Create QueryDict copy to modify for removal URL
            remove_query = query_params.copy()
            remove_query.pop(key, None) # Remove this specific filter key
             # Remove page number as well when changing filters
            remove_query.pop('page', None)

            active_filters.append({
                'key': key,
                'label': label,
                'value': value,
                # Generate the query string for the removal link
                'remove_url': '?'+remove_query.urlencode() if remove_query else '?'
            })

    return active_filters