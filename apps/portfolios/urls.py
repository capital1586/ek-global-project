from django.urls import path

from . import views


app_name = "portfolios"

urlpatterns = [
    path("", views.portfolio_list_view, name="portfolio_list"),
    path(
        "transaction-upload-template/download",
        views.transactions_upload_template_download_view,
        name="transactions_upload_template_download",
    ),
    path("new", views.portfolio_create_view, name="portfolio_create"),
    # path("image-test", views.image_test_view, name="image_test"),
    
    # API endpoints
    path("api/transactions/", views.portfolio_transactions_api_view, name="portfolio_transactions_api"),
    path("api/notifications/send-email/", views.email_notification_view, name="email_notification"),
    path("api/news/", views.portfolio_news_api_view, name="portfolio_news_api"),
    
    path("<uuid:portfolio_id>", views.portfolio_detail_view, name="portfolio_detail"),
    path(
        "<uuid:portfolio_id>/performance-data",
        views.portfolio_performance_data_view,
        name="portfolio_performance_data",
    ),
    path(
        "<uuid:portfolio_id>/update",
        views.portfolio_update_view,
        name="portfolio_update",
    ),
    path(
        "<uuid:portfolio_id>/delete",
        views.portfolio_delete_view,
        name="portfolio_delete",
    ),
    path(
        "<uuid:portfolio_id>/dividends-update",
        views.portfolio_dividends_update_view,
        name="portfolio_dividends_update",
    ),
    path(
        "<uuid:portfolio_id>/investments/new",
        views.investment_add_view,
        name="investment_add",
    ),
    path(
        "<uuid:portfolio_id>/investments/<uuid:investment_id>/delete",
        views.investment_delete_view,
        name="investment_delete",
    ),
    path(
        "transactions/compare",
        views.transaction_compare_view,
        name="transaction_compare",
    ),
]
