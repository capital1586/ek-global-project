# news/views.py

import requests
import logging
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote

# Django Imports
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q # For complex lookups
from django.utils import timezone
# from django.views.decorators.cache import cache_page # View-level caching less ideal with filtering

# Local Imports
from .models import News # Assuming your model is in the same app

logger = logging.getLogger(__name__)

# --- Constants for Cache ---
ACCESS_TOKEN_CACHE_KEY = 'mg_link_access_token'
NEWS_DATA_CACHE_KEY = 'mg_link_news_data'
MARKET_DATA_CACHE_KEY = 'market_data_v2'
ALL_CATEGORIES_CACHE_KEY = 'all_news_categories_v2'
DISTINCT_SOURCES_CACHE_KEY = 'distinct_news_sources_v2'

# --- Cache Timeouts (in seconds) ---
TOKEN_EXPIRY_SECONDS = 3500 # Assume token expires in 3600 secs, refresh slightly earlier
NEWS_CACHE_TIMEOUT = 15 * 60 # Cache news API data for 15 minutes
MARKET_DATA_CACHE_TIMEOUT = 5 * 60 # Cache market data for 5 minutes
ALL_CATEGORIES_TIMEOUT = 60 * 60 # Cache category list for 1 hour
SOURCES_CACHE_TIMEOUT = 2 * 60 * 60 # Cache sources for 2 hours

# --- API Credentials (Move to settings or environment variables!) ---
MG_API_USERNAME = "EKCapital2024"
MG_API_PASSWORD = "3KC@Pit@L!2024"
# Placeholder for Market Data API - REPLACE THESE
MARKET_DATA_API_KEY = getattr(settings, "MARKET_DATA_API_KEY", "YOUR_MARKET_API_KEY")
MARKET_DATA_API_URL = getattr(settings, "MARKET_DATA_API_URL", "YOUR_MARKET_API_ENDPOINT")


# ===========================
# === API HELPER FUNCTIONS ===
# ===========================

def get_access_token():
    """Fetches the MG-Link access token from the API or cache."""
    token = cache.get(ACCESS_TOKEN_CACHE_KEY)
    if token:
        logger.debug("MG-Link Access token found in cache.")
        return token

    logger.info("Fetching new MG-Link access token from API.")
    url = "https://api.mg-link.net/api/auth/token"
    data = {
        "grant_type": "password",
        "username": MG_API_USERNAME,
        "password": MG_API_PASSWORD
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get('access_token')
        # Use 'expires_in' for dynamic timeout, provide a default
        expires_in = token_data.get('expires_in', TOKEN_EXPIRY_SECONDS)
        # Ensure cache timeout is reasonable, at least 60 seconds
        cache_timeout = max(60, expires_in - 120) if expires_in else TOKEN_EXPIRY_SECONDS - 120

        if access_token:
            cache.set(ACCESS_TOKEN_CACHE_KEY, access_token, timeout=cache_timeout)
            logger.info(f"New MG-Link access token obtained and cached for {cache_timeout} seconds.")
            return access_token
        else:
            logger.error("Access token not found in MG-Link API response.")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error getting MG-Link access token: {str(e)}")
        return None
    except ValueError as e: # JSON decode error
        logger.error(f"Error decoding JSON response from MG-Link token API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during MG-Link token fetch: {str(e)}")
        return None


def fetch_news_from_api():
    """Fetches raw news data from the MG-Link API or cache."""
    cached_news = cache.get(NEWS_DATA_CACHE_KEY)
    if cached_news:
        logger.debug(f"Raw news data found in cache ({len(cached_news)} items).")
        return cached_news

    logger.info("Fetching fresh news data from MG-Link API.")
    access_token = get_access_token()
    if not access_token:
        logger.error("Cannot fetch news, MG-Link access token is missing.")
        return [] # Return empty list on failure

    url = "https://api.mg-link.net/api/Data1/GetMGNews_New"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # Increased timeout for potentially large response
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        news_data = response.json() # Assume this returns a list of dicts

        # Basic validation of response structure
        if isinstance(news_data, list):
             # Filter out items potentially missing core data *before* caching
             valid_news_data = [item for item in news_data if item.get('NewsID') and item.get('Headline')]
             if len(valid_news_data) < len(news_data):
                 logger.warning(f"Filtered out {len(news_data) - len(valid_news_data)} items missing NewsID or Headline during API fetch.")

             cache.set(NEWS_DATA_CACHE_KEY, valid_news_data, timeout=NEWS_CACHE_TIMEOUT)
             logger.info(f"Fetched {len(valid_news_data)} valid news items from MG-Link API and cached.")
             return valid_news_data
        else:
             logger.error(f"Unexpected data format received from MG-Link news API. Expected list, got {type(news_data)}. Response: {str(response.text)[:200]}")
             return []

    except requests.exceptions.Timeout:
        logger.error("Timeout occurred while fetching MG-Link news.")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching MG-Link news: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 401: # Unauthorized
            cache.delete(ACCESS_TOKEN_CACHE_KEY) # Clear potentially expired token
            logger.warning("Received 401 from MG-Link, clearing cached access token.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching MG-Link news: {str(e)}")
        return []
    except ValueError as e: # JSON decode error
        logger.error(f"Error decoding JSON response from MG-Link news API: {str(e)}. Response text: {str(response.text)[:200]}")
        return []
    except Exception as e:
        # Log the full traceback for unexpected errors
        logger.exception(f"Unexpected error fetching MG-Link news: {str(e)}")
        return []


def fetch_market_data():
    """
    Placeholder function to fetch market data.
    REPLACE THIS with your actual market data API implementation.
    """
    cached_data = cache.get(MARKET_DATA_CACHE_KEY)
    # Check for None to differentiate cache miss from cached empty list
    if cached_data is not None:
        logger.debug("Market data found in cache.")
        return cached_data

    logger.info("Fetching 'market data' (Placeholder).")
    # --- START Placeholder ---
    market_data = [
        {"symbol": "S&P 500", "price": "5105.60", "change": "+20.10", "change_percent": "+0.39%"},
        {"symbol": "NASDAQ", "price": "16188.30", "change": "-62.50", "change_percent": "-0.38%"},
        {"symbol": "DJIA", "price": "38590.90", "change": "+110.90", "change_percent": "+0.29%"},
        # Add more relevant indices/commodities if needed
        {"symbol": "FTSE 100", "price": "7685.10", "change": "+15.50", "change_percent": "+0.20%"},
        {"symbol": "Gold (USD)", "price": "2055.80", "change": "+8.10", "change_percent": "+0.40%"},
        {"symbol": "Oil (WTI)", "price": "78.50", "change": "-0.45", "change_percent": "-0.57%"},
        {"symbol": "EUR/USD", "price": "1.0835", "change": "-0.0025", "change_percent": "-0.23%"},
    ]
    # Simulate potential API failure
    import random
    if random.random() < 0.05: # Simulate a 5% chance of failure
        logger.warning("Simulated failure fetching market data.")
        market_data = [] # Represents API failure
    # --- END Placeholder ---

    if market_data:
        cache.set(MARKET_DATA_CACHE_KEY, market_data, timeout=MARKET_DATA_CACHE_TIMEOUT)
        logger.info("Fetched and cached market data (Placeholder).")
    else:
        # Cache an empty list on failure to prevent repeated API calls for a short period
        cache.set(MARKET_DATA_CACHE_KEY, [], timeout=60) # Cache failure state for 1 minute
        logger.warning("Failed to fetch market data (Placeholder), caching empty list.")

    return market_data


# ============================
# === DATABASE & SYNC HELPERS ===
# ============================

def get_source_domain(url):
    """Helper function to extract domain name from URL for display."""
    if not url or not isinstance(url, str):
        return None # Return None for invalid input
    try:
        # Ensure scheme is present
        if not url.startswith(('http://', 'https://')):
             url = 'http://' + url

        parsed_uri = urlparse(url)
        domain = parsed_uri.netloc
        # Remove 'www.' prefix if it exists
        if domain.lower().startswith('www.'):
            domain = domain[4:]
        # Return None if domain is empty after parsing
        return domain if domain else None
    except Exception as e:
        logger.warning(f"Could not parse domain from URL '{url}': {e}")
        return None # Return None on parsing error


def sync_news_db(news_data_api):
    """Updates the database with news items from the API data."""
    logger.info(f"Starting DB sync for {len(news_data_api)} items from API.")
    updated_count = 0
    created_count = 0
    error_count = 0
    skipped_count = 0
    processed_ids = set()

    for item in news_data_api:
        news_id_raw = item.get('NewsID') # Get ID first for logging
        try:
            headline = item.get('Headline')

            # Basic validation
            if not news_id_raw or not headline or str(headline).strip() == '':
                logger.warning(f"Skipping news item due to missing/empty ID or Headline: ID={news_id_raw}, Headline='{headline}'")
                skipped_count += 1
                continue

            # Ensure news_id is stored consistently (e.g., as string if not always int)
            news_id = str(news_id_raw)
            processed_ids.add(news_id)

            # Date Parsing
            news_date_obj = None
            news_date_str = item.get('NewsDate')
            if news_date_str:
                try:
                    # Handle potential timezone info ('Z') and microseconds
                    if '.' in news_date_str: news_date_str = news_date_str.split('.')[0]
                    if 'Z' in news_date_str: news_date_str = news_date_str.replace('Z', '')
                    news_date_obj = datetime.strptime(news_date_str, "%Y-%m-%dT%H:%M:%S")
                    # Optional: Make timezone aware using Django settings
                    # if settings.USE_TZ:
                    #     news_date_obj = timezone.make_aware(news_date_obj, timezone.get_current_timezone())
                except (ValueError, TypeError) as dt_error:
                    logger.warning(f"Could not parse date '{news_date_str}' for NewsID {news_id}: {dt_error}")

            # Extract source domain
            link = item.get('NewsLink')
            source_domain_val = get_source_domain(link) if link else None

            # Prepare defaults safely
            defaults = {
                'headline': str(headline).strip(),
                'news_content': item.get('News', ''),
                'news_link': link if isinstance(link, str) else None,
                'image_url': item.get('ImageUrl') if isinstance(item.get('ImageUrl'), str) else None,
                'news_date': news_date_obj,
                'tags': item.get('Tags', ''),
                'description': item.get('Description', ''),
                'categories': item.get('Categories', ''),
                'author_name': item.get('AuthorName'),
                'source_domain': source_domain_val, # Store the extracted domain
            }

            # Use update_or_create with the consistent news_id type
            obj, created = News.objects.update_or_create(
                news_id=news_id,
                defaults=defaults
            )

            if created: created_count += 1
            else: updated_count += 1

        except KeyError as e:
            logger.error(f"Missing expected key {e} in news item processing: ID={news_id_raw}")
            error_count += 1
        except Exception as e:
            logger.exception(f"Error processing news item ID={news_id_raw}: {e}")
            error_count += 1

    logger.info(f"News DB Sync finished: {created_count} created, {updated_count} updated, {skipped_count} skipped, {error_count} errors.")

    # Optional: Invalidate caches that depend on News data after sync
    cache.delete(ALL_CATEGORIES_CACHE_KEY)
    cache.delete(DISTINCT_SOURCES_CACHE_KEY)
    logger.debug("Invalidated category and source caches after DB sync.")

    # Optional: Cleanup old articles (implement carefully)
    # ...


# ================================
# === FILTER OPTIONS HELPERS ===
# ================================

def get_all_categories():
    """
    Fetches a list of unique, cleaned category names from the News items.
    Handles comma-separated categories and caches the result.
    Sorts based on a preferred order, then alphabetically.
    """
    cached_categories = cache.get(ALL_CATEGORIES_CACHE_KEY)
    if cached_categories is not None: # Check for cache hit (could be empty list)
        logger.debug("All categories list found in cache.")
        return cached_categories

    logger.info("Generating list of all unique categories from DB.")
    all_categories_set = set()
    try:
        category_strings = News.objects.filter(
            categories__isnull=False
        ).exclude(
            categories__exact=''
        ).values_list('categories', flat=True).distinct()

        for cat_string in category_strings:
            categories = [
                c.strip().title()
                for c in cat_string.split(',') if c.strip()
            ]
            all_categories_set.update(categories)

        # Convert set to list for sorting
        sorted_categories = sorted(list(all_categories_set))

        # Define a preferred order (customize as needed)
        preferred_order = [
            'Breaking News', 'Market Updates', 'Economy', 'Politics', 'Finance',
            'Technology', 'Corporate Events', 'Commodities', 'Foreign Exchange',
            'Cryptocurrencies', 'Health & Lifestyle', 'GCC News', 'Global News' # Add specific regions if used
        ]
        # Sort primarily by preferred order, then alphabetically
        ordered_categories = sorted(
            sorted_categories,
            key=lambda x: (preferred_order.index(x) if x in preferred_order else float('inf'), x)
        )

        cache.set(ALL_CATEGORIES_CACHE_KEY, ordered_categories, timeout=ALL_CATEGORIES_TIMEOUT)
        logger.info(f"Generated and cached {len(ordered_categories)} unique categories.")
        return ordered_categories

    except Exception as e:
        logger.exception(f"Error fetching all categories: {e}")
        return [] # Return empty list on error


def get_distinct_sources():
    """Fetches a list of unique, non-empty source domains."""
    cached_sources = cache.get(DISTINCT_SOURCES_CACHE_KEY)
    if cached_sources is not None:
        logger.debug("Distinct sources list found in cache.")
        return cached_sources

    logger.info("Generating list of distinct source domains from DB.")
    try:
        # Assumes source_domain field exists and is populated
        sources = News.objects.filter(
            source_domain__isnull=False
        ).exclude(
            source_domain__exact=''
        ).values_list('source_domain', flat=True).distinct().order_by('source_domain')

        source_list = list(sources)
        cache.set(DISTINCT_SOURCES_CACHE_KEY, source_list, timeout=SOURCES_CACHE_TIMEOUT)
        logger.info(f"Generated and cached {len(source_list)} distinct sources.")
        return source_list
    except Exception as e:
        logger.exception(f"Error fetching distinct sources: {e}")
        # Fallback if the source_domain field doesn't exist yet
        if 'source_domain' in str(e):
             logger.warning("source_domain field not found, attempting fallback source extraction (less efficient).")
             # This is less efficient - run only if needed
             all_links = News.objects.filter(news_link__isnull=False).exclude(news_link__exact='').values_list('news_link', flat=True)
             domains = set()
             for link in all_links:
                 domain = get_source_domain(link)
                 if domain:
                     domains.add(domain)
             return sorted(list(domains))
        return []


# ================================
# === CONTENT HELPER FUNCTIONS ===
# ================================

def get_trending_news(limit=5):
    """Fetches the latest news published within the last 24 hours."""
    try:
        cutoff_time = timezone.now() - timedelta(hours=24)
        trending = News.objects.filter(
            news_date__isnull=False,
            news_date__gte=cutoff_time
        ).order_by('-news_date')[:limit]

        # Add display helpers (ensure model methods or properties handle this)
        # If News model has get_absolute_url, etc., they will be available.
        # We might not need explicit loops here if model methods are sufficient.

        return trending
    except Exception as e:
        logger.exception(f"Error fetching trending news: {e}")
        return News.objects.none() # Return empty QuerySet on error


def add_display_helpers(news_queryset):
     """Adds source_domain and category_list to items in a queryset."""
     # This might be inefficient for large querysets if run repeatedly.
     # Consider adding properties to the model instead if performance is critical.
     for item in news_queryset:
        # Use getattr to avoid errors if field doesn't exist (though it should)
        item.source_domain = getattr(item, 'source_domain', None) or get_source_domain(getattr(item, 'news_link', None))
        item.category_list = item.get_categories_list() if hasattr(item, 'get_categories_list') else []
     return news_queryset


# ======================
# === DJANGO VIEWS ===
# ======================

def news_list(request):
    """Displays the main news page with category filtering and sidebar."""

    # --- Step 1: Sync DB (Run cautiously in production views) ---
    # It's generally better to run sync via a scheduled task (Celery, cron)
    # to avoid impacting user request times. Triggering it here for simplicity.
    try:
        news_data_api = fetch_news_from_api()
        if news_data_api:
            sync_news_db(news_data_api)
        else:
            logger.warning("No data received from API, skipping DB sync for this request.")
    except Exception as sync_err:
        logger.exception(f"Error during background sync trigger: {sync_err}")

    # --- Step 2: Get Filters & Filter Options ---
    selected_category_raw = request.GET.get('category')
    selected_category = selected_category_raw.strip().title() if selected_category_raw else None
    selected_source = request.GET.get('source')
    search_query = request.GET.get('q', '').strip() # Ensure it's a string and strip whitespace
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Fetch options for the filter sidebar UI
    all_categories = get_all_categories()
    all_sources = get_distinct_sources()

    # --- Step 3: Build Filtered News Queryset ---
    try:
        news_queryset = News.objects.filter(news_date__isnull=False) # Base queryset

        # Apply filters
        if selected_category:
            news_queryset = news_queryset.filter(categories__icontains=selected_category)
        if selected_source:
            # Assumes source_domain field exists and is populated
            news_queryset = news_queryset.filter(source_domain__iexact=selected_source)
        if search_query:
            news_queryset = news_queryset.filter(
                Q(headline__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(news_content__icontains=search_query) | # Optional: Search content
                Q(tags__icontains=search_query) # Optional: Search tags
            )
        # Apply date filters safely
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                news_queryset = news_queryset.filter(news_date__date__gte=start_date)
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                # Add one day to end_date to make it inclusive if needed, or use lte
                news_queryset = news_queryset.filter(news_date__date__lte=end_date)
        except ValueError:
            logger.warning(f"Invalid date format received: start='{start_date_str}', end='{end_date_str}'. Ignoring date filter.")

        # Final ordering and distinct results (if needed due to Q objects)
        news_items_all = news_queryset.distinct().order_by('-news_date')

    except Exception as e:
        logger.exception(f"Error building filtered news query: {e}")
        news_items_all = News.objects.none() # Return empty queryset on error

    # --- Step 4: Pagination ---
    paginator = Paginator(news_items_all, 9) # Items per page
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception(f"Error during pagination: {e}")
        page_obj = paginator.get_page(1) # Default to page 1 on error

    # Add display helpers (consider moving to model properties/methods if feasible)
    # page_obj = add_display_helpers(page_obj) # Can be slow, use model methods instead

    # --- Step 5: Get Breaking/Featured & Trending News ---
    try:
        breaking_news_items = News.objects.filter(news_date__isnull=False).order_by('-news_date')[:4]
        # breaking_news_items = add_display_helpers(breaking_news_items) # Add helpers
        latest_news_item = breaking_news_items[0] if breaking_news_items else None
        other_breaking_news = breaking_news_items[1:] if len(breaking_news_items) > 1 else []
    except Exception as e:
        logger.exception(f"Error fetching breaking news items: {e}")
        latest_news_item, other_breaking_news = None, []

    trending_news = get_trending_news(limit=5) # Fetch trending news

    # --- Step 6: Fetch Market Data ---
    market_data = fetch_market_data()

    # --- Step 7: Prepare Context ---
    current_filters_params = request.GET.copy()
    current_filters_params.pop('page', None) # Remove page for base pagination URL
    filters_query_string = current_filters_params.urlencode()

    context = {
        'market_data': market_data,
        'latest_news_item': latest_news_item,
        'other_breaking_news': other_breaking_news,
        'news': page_obj, # Main filtered & paginated list
        'trending_news': trending_news,

        # Filter options for sidebar UI
        'all_categories': all_categories,
        'all_sources': all_sources,

        # Currently applied filters (for UI state)
        'selected_category': selected_category,
        'selected_source': selected_source,
        'search_query': search_query,
        'start_date': start_date_str,
        'end_date': end_date_str,

        # For pagination links
        'filters_query_string': filters_query_string,
    }

    return render(request, 'news/news_list_page.html', context)


def news_detail(request, news_id):
    """Displays the full detail of a single news article."""
    # Use str(news_id) if your news_id in the model is CharField
    news_item = get_object_or_404(News, news_id=str(news_id))

    # --- Add display helpers (using model methods if available) ---
    # These might already be handled by model properties/methods now
    # news_item = add_display_helpers([news_item])[0] # Less ideal

    # --- Find Related News ---
    related_news = News.objects.none() # Default to empty
    try:
        item_categories = news_item.get_categories_list()
        if item_categories:
            category_query = Q()
            for cat in item_categories:
                category_query |= Q(categories__icontains=cat)

            related_news = News.objects.filter(
                category_query,
                news_date__isnull=False
            ).exclude(
                pk=news_item.pk # Exclude self
            ).distinct().order_by('-news_date')[:4] # Limit related items

            # related_news = add_display_helpers(related_news) # Add helpers

    except Exception as e:
        logger.exception(f"Error finding related news for ID {news_id}: {e}")

    # --- Fetch Trending News (for sidebar) ---
    trending_news = get_trending_news(limit=5)

    # --- Fetch Market Data (optional) ---
    market_data = fetch_market_data()

    context = {
        'news_item': news_item,
        'related_news': related_news,
        'trending_news': trending_news,
        'market_data': market_data,
    }
    return render(request, 'news/news_detail.html', context)