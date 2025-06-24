from django.urls import path

from . import views

app_name = "copilot"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("tradingview/", views.tradingview, name="tradingview"),
    path("api/process-query/", views.process_query, name="process_query"),
    path("api/stock-data/", views.get_stock_data, name="stock_data"),
]

