from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/historical-data/", views.fetch_historical_data, name="fetch_historical_data"),
    path("api/chart-data/", views.get_stock_chart_data, name="stock_chart_data"),
    path("api/heat-map-data/", views.get_heat_map_data, name="heat_map_data"),
    path("api/bubble-chart-data/", views.get_bubble_chart_data, name="bubble_chart_data"),
    path("api/line-chart-data/", views.get_line_chart_data, name="line_chart_data"),
    path("api/debug/", views.debug_api, name="debug_api"),
    path("api/debug-fetch/", views.debug_api_fetch, name="debug_api_fetch"),
    path("stock/<str:symbol>/", views.stock_detail, name="stock_detail"),
    #path("stock-chart/<str:symbol>/", views.stock_chart, name="stock_chart"),
    #path("api/data/", views.api_data, name="api_data"),
]

app_name = "psxscreener"
