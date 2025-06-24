# smartscreener/urls.py

from django.urls import path
from . import views

app_name = "SmartScreener" # Use this namespace in templates: {% url 'SmartScreener:index' %}

urlpatterns = [
    # Main page
    path('', views.index, name='index'),

    # --- API Endpoints ---
    # Primary endpoint for the screener table data
    path('api/stocks/', views.get_stocks, name='get_stocks_api'), # Renamed for clarity

    # Endpoint for stock history (used by charts)
    path('api/stock-history/', views.get_stock_daily_history, name='get_stock_history_api'),

    # Other potential API endpoints (keep or remove as needed)
    path('api/indices-live/', views.get_indices_live, name='get_indices_live_api'),
    # path('api/announcements/', views.get_psx_announcements, name='get_announcements_api'),
    # path('api/news/', views.get_news, name='get_news_api'),
    # path('api/commodities/', views.get_commodities, name='get_commodities_api'),
    # path('api/currencies-live/', views.get_currencies_live, name='get_currencies_live_api'),
    # path('api/economic-data/', views.get_economic_data, name='get_economic_data_api'),
    # path('api/technical-indicators/', views.get_technical_indicators, name='get_technical_indicators_api'),
]