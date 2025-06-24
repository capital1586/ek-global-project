from django.apps import AppConfig


class AcademyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.Academy'
    verbose_name = 'Academy'
    
    def ready(self):
        # Import signals here to avoid circular imports
        pass
