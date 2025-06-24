from django.urls import path
from . import views
app_name = 'stockscreener'
urlpatterns = [
    path('', views.stock_screener, name='screener'),
]