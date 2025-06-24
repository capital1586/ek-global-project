from django.urls import path
from . import views

app_name = 'Alerts'

urlpatterns = [
    path('', views.alert_list_view, name='alert_list'),
    path('new/', views.alert_create_view, name='alert_create'),
    path('<int:pk>/update/', views.alert_update_view, name='alert_update'),
    path('<int:pk>/delete/', views.alert_delete_view, name='alert_delete'),
    
    # API endpoints
    path('api/alerts/', views.alert_api_view, name='alert_api'),
    path('api/notify/', views.alert_notification_view, name='alert_notify'),
    path('portfolio-alert/', views.create_portfolio_alert, name='portfolio_alert_create'),
]
