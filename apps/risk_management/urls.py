from django.urls import path

from . import views

app_name = "risk_management"


urlpatterns = [
    path("", views.risk_management_view, name="risk_management"),
    path(
        "risk-profile/create",
        views.risk_profile_create_view,
        name="risk_profile_create",
    ),
    path(
        "risk-profile/<uuid:profile_id>/update",
        views.risk_profile_update_view,
        name="risk_profile_update",
    ),
    path(
        "risk-profile/<uuid:profile_id>/delete",
        views.risk_profile_delete_view,
        name="risk_profile_delete",
    ),
    path(
        "risk-profile/<uuid:profile_id>/generate",
        views.stocks_risk_profile_generation_view,
        name="stocks_risk_profile_generation",
    ),
]
