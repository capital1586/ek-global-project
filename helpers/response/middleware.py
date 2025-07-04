from django.utils.deprecation import MiddlewareMixin
from django.utils.module_loading import import_string
from django.http import HttpRequest, HttpResponse
import os
import asyncio
from typing import Dict, Union, Any, Callable
from asgiref.sync import async_to_sync
from django.core.exceptions import ImproperlyConfigured

from helpers.config import settings
from .format import drf_response_formatter, Formatter
from ..logging import log_exception


class FormatResponseMiddleware(MiddlewareMixin):
    """
    Middleware to format response data to a consistent format.

    Uses `RESPONSE_FORMATTER` helpers setting, if set. Otherwise,
    a default formatter is used.

    In settings.py:

    ```python
    HELPERS_SETTINGS = {
        ...,
        RESPONSE_FORMATTER: "path.to.formatter_function"
    }
    ```
    """

    default_formatter = drf_response_formatter
    setting_name = "RESPONSE_FORMATTER"

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        formatter = self.get_formatter()
        try:
            response = formatter(response)
        except Exception:
            pass
        return response

    def get_formatter(self):
        """Return the response formatter."""
        formatter_path = getattr(settings, type(self).setting_name, None)
        if formatter_path is None:
            return type(self).default_formatter

        formatter: Formatter = import_string(formatter_path)
        if asyncio.iscoroutinefunction(formatter):
            return async_to_sync(formatter)
        return formatter


class MaintenanceMiddleware(MiddlewareMixin):
    """
    Middleware to handle application maintenance mode.
    The middleware will return a 503 Service Unavailable response with the maintenance message.

    #### Ensure to place this middleware at the top of `MIDDLEWARE` settings.

    Middleware settings:

    - `MAINTENANCE_MODE.status`: Set as "ON" or "OFF", True or False, to enable or disable maintenance mode.
    - `MAINTENANCE_MODE.message`: The message to display in maintenance mode. Can be a path to a template file or a string.

    There are default maintenance message templates available:

    - `default:minimal`: Minimal and clean. Light-themed
    - `default:minimal_dark`: Dark-themed minimal
    - `default:techno`: Techno-themed
    - `default:jazz`: Playful jazz-themed

    In settings.py:

    ```python

    
    HELPERS_SETTINGS = {
        ...,
        MAINTENANCE_MODE: {
            "status": True,
            "message": "default:techno"
        }
    }
    ```
    """

    templates_dir = os.path.join(os.path.dirname(__file__), "templates\\maintenance")
    defaults_prefix = "default:"
    setting_name = "MAINTENANCE_MODE"

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse] | None = ...
    ) -> None:
        super().__init__(get_response)
        self.settings: Dict[str, Any] = getattr(settings, type(self).setting_name)

    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Process the request."""
        if self.check_maintenance_mode_on():
            content = self.get_response_content()
            headers = self.get_response_headers()
            return HttpResponse(content, status=503, headers=headers)
        return None

    def check_maintenance_mode_on(self) -> bool:
        """Check if the application is in maintenance mode."""
        status = str(self.settings.get("status", "off"))
        return status.lower() in ["on", "true"]

    def get_message(self) -> Union[str, bytes]:
        """Return the maintenance message."""
        msg = self.settings.get("message", "default:minimal")

        if not isinstance(msg, str):
            raise ImproperlyConfigured(f"{self.setting_name}.message must be a string")

        if msg.lower().startswith(self.defaults_prefix.lower()):
            slice_start = len(type(self).defaults_prefix)
            template_name = msg[slice_start:]
            msg = self.get_default_template(template_name)

        return msg or "Service Unavailable"

    def get_default_template(self, name: str) -> Union[bytes, None]:
        """Get the default maintenance template content."""
        template_path = os.path.join(type(self).templates_dir, f"{name.lower()}.html")
        try:
            if os.path.exists(template_path):
                with open(template_path, "rb") as file:
                    return file.read()
        except Exception as exc:
            log_exception(exc)
        return None

    def get_response_content(self) -> Union[str, bytes]:
        """Returns the response content."""
        return self.get_message()

    def get_response_headers(self) -> Dict[str, Any]:
        """Returns the response headers."""
        return {
            "Content-Type": "text/html",
        }
