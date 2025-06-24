from django.apps import AppConfig


class RiskManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.risk_management"

    def ready(self) -> None:
        import apps.risk_management.function_evaluators  # noqa
        # import rich
        # from apps.risk_management.criteria.functions import FUNCTIONS_REGISTRY
        # rich.print(FUNCTIONS_REGISTRY)
        # print(len(FUNCTIONS_REGISTRY))
