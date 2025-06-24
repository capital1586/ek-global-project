from django.urls import path
from . import views

app_name = 'academy'

urlpatterns = [
    path('', views.index, name='index'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('video/<int:video_id>/', views.video_detail, name='video_detail'),
]
