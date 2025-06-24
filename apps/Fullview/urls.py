from django.urls import path
from .views import stock_360_view, companies_list, api_debug

app_name = 'Fullview'

urlpatterns = [
    path('', companies_list, name='companies_list'),
    path('stock/<str:symbol>/', stock_360_view, name='stock_360_view'),
    path('api-debug/<str:symbol>/', api_debug, name='api_debug'),
    path('api-debug/', api_debug, name='api_debug_default'),
]
