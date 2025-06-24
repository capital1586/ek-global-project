from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path("", include("apps.dashboard.urls", namespace="dashboard")),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("stocks/", include("apps.stocks.urls", namespace="stocks")),
    path("portfolios/", include("apps.portfolios.urls", namespace="portfolios")),
   # path("risk-management/",include("apps.risk_management.urls", namespace="risk_management")),
    path("stockscreener/", include("apps.stockscreener.urls", namespace="stockscreener")),
    path("copilot/", include("apps.copilot.urls", namespace="copilot")),
   # path("psxscreener/", include("apps.psxscreener.urls", namespace="psxscreener")),
    path("news/", include("apps.News.urls", namespace="news")),
    path("smartscreener/", include("apps.psxscreener.urls", namespace="smartscreener")),
    path("academy/", include("apps.Academy.urls", namespace="academy")),
    path("fullview/", include("apps.Fullview.urls", namespace="fullview")),
    path("alerts/", include("apps.Alerts.urls", namespace="alerts")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = f"{settings.APPLICATION_NAME} Admin"
admin.site.site_title = f"{settings.APPLICATION_ALIAS} Admin"
