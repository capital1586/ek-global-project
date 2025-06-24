from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("sign-in/", views.user_signin_view, name="signin"),
    path("sign-out/", views.user_signout_view, name="signout"),
    path("sign-up/", views.user_signup_view, name="signup"),
]
