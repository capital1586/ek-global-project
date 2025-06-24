from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('news_list_page/', views.news_list, name='news_list_page'),
    path('news_detail/<int:news_id>/', views.news_detail, name='news_detail'),
]
