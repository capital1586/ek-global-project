from django.urls import path

from . import views


app_name = "stocks"


urlpatterns = [
    path("uploads/", views.uploads_view, name="uploads"),
    path("latest-price/", views.stock_latest_price_view, name="stock_latest_price"),
]
