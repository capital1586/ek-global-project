from django.urls import path

from . import views

app_name = "dashboard"


urlpatterns = [
    path("", views.index_view, name="index"),
    # API endpoints
    path("api/market-overview/", views.market_overview_view, name="market_overview"),
    path("api/top-stocks/", views.top_stocks_view, name="top_stocks"),
    path("api/latest-news/", views.latest_news_view, name="latest_news"),
    path("api/portfolio/", views.portfolio_data_view, name="portfolio_data"),
    path("api/industry-performance/", views.industry_performance_view, name="industry_performance"),
    path("api/psx-notices/", views.psx_notices_view, name="psx_notices"),
    path("api/financial-results/", views.financial_results_view, name="financial_results"),
    path("api/treemap-data/", views.treemap_data_view, name="treemap_data"),
]
