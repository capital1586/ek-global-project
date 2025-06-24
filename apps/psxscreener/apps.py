from django.apps import AppConfig


class PsxscreenerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.psxscreener'
    
    def ready(self):
        # Import here to avoid circular imports
        from . import views
        views.test_api_connection()