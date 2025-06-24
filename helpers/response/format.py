import functools
from django.http import HttpResponse
from typing import Callable, Optional, Dict, Any, Coroutine
import json
from asgiref.sync import sync_to_async
import asyncio

from . import HTTPResponse
from ..views import CBV, FBV


Formatter = Callable[[HTTPResponse], HTTPResponse | Coroutine[Any, Any, HTTPResponse]]


def _transfer_response_props(original: HTTPResponse, new: HTTPResponse) -> HTTPResponse:
    """
    Updates the new response with attributes from the original response
    that are not already present.
    """
    for key, value in original.__dict__.items():
        if key not in new.__dict__:
            new.__dict__[key] = value
    return new


def enforce_format(formatter: Formatter):
    """
    Enforces a format for the response of a view function using the formatter provided.

    :param formatter: A function that restructures the response' data to a desired format.
    The function should expect the response as an argument and return the formatted response.
    In an asynchronous context, the formatter provided should be a coroutine function.
    """

    def decorator(view_func: FBV) -> FBV:
        if asyncio.iscoroutinefunction(view_func):

            @functools.wraps(view_func)
            async def wrapper(*args, **kwargs) -> HTTPResponse:
                response = await view_func(*args, **kwargs)
                formatted_response = await formatter(response)
                async_transfer_props = sync_to_async(_transfer_response_props)
                return await async_transfer_props(response, formatted_response)
        else:

            @functools.wraps(view_func)
            def wrapper(*args, **kwargs) -> HTTPResponse:
                response = view_func(*args, **kwargs)
                formatted_response = formatter(response)
                return _transfer_response_props(response, formatted_response)

        return wrapper

    return decorator


DEFAULT_ERROR_MSG = "An error occurred while processing your request!"

DEFAULT_OK_MSG = "Request processed successfully!"

DEFAULT_NOT_FOUND_MSG = "Resource not found!"


def is_formatted(data: Dict[str, Any]) -> bool:
    """Checks if the response data has already been formatted."""
    standard_keys = {"status", "message", "errors", "data", "detail"}

    # If at least one standard key is not present, it is not formatted
    if len(standard_keys & data.keys()) < 1:
        return False

    # If 'status' is present, it must be either 'success' or 'error'
    if "status" in data and data["status"] not in {"success", "error"}:
        return False

    # If 'message' is present, it must be a non-empty string
    if "message" in data and data["message"] and not isinstance(data["message"], str):
        return False

    # If 'errors' is present, it must be a non-empty dictionary or a list
    if (
        "errors" in data
        and data["errors"]
        and not isinstance(data["errors"], (dict, list))
    ):
        return False

    # If 'data' is present, it must be a dictionary, list or str
    if (
        "data" in data
        and data["data"]
        and not isinstance(data["data"], (dict, list, str))
    ):
        return False

    # If 'detail' is present, it must be a dictionary, list or str
    if (
        "detail" in data
        and data["detail"]
        and not isinstance(data["detail"], (dict, list, str))
    ):
        return False

    return True


def generic_response_data_formatter(
    response_data: Any, response_ok: bool
) -> Dict[str, Any]:
    """
    Generic response data formatter

    Formatted response data structure:
    ```JSON
    {
        "status": "success" | "error",
        "message": "Request processed successfully" | ...,
        "errors": ..., # If response has errors
        "data": ..., # If response is successful and has data
        "detail": ..., # Dependent on the response
    }
    ```
    """
    if not isinstance(response_data, dict):
        formatted = {
            "status": "success" if response_ok else "error",
            "message": DEFAULT_OK_MSG if response_ok else DEFAULT_ERROR_MSG,
        }
        if not response_data:
            return formatted
        if response_ok:
            formatted["data"] = response_data
        else:
            if isinstance(response_data, (list, dict)):
                formatted["errors"] = response_data
            else:
                formatted["detail"] = response_data
        return formatted

    message = response_data.get("message", None)
    detail = response_data.get("detail", None)
    errors = response_data.get("errors", None)
    data = response_data.get("data", None)
    status = "success" if response_ok else "error"

    if message is None:
        # If the detail is provided, use it as the message
        # Else, use the default success or error message
        if detail and isinstance(detail, str):
            message = detail
        elif response_ok:
            message = DEFAULT_OK_MSG
        else:
            message = DEFAULT_ERROR_MSG

    formatted = {
        "status": status,
        "message": message,
    }

    if detail and detail != message:
        # If the detail is different from the message, include it in the response
        formatted["detail"] = detail

    if response_ok:
        # If the response is successful, include the data
        if data is not None:
            # If the data is provided, use it
            formatted["data"] = data
        else:
            # If the data is not provided, use the response data.
            # If the data has not already been formatted
            if not is_formatted(response_data):
                formatted["data"] = response_data
    else:
        # If the response is an error, include the errors
        if errors is not None:
            # If the errors are provided, use them
            formatted["errors"] = errors
        else:
            # If the errors are not provided, use the response data.
            # If the data has not already been formatted
            if not is_formatted(response_data):
                formatted["errors"] = response_data
    return formatted


def json_httpresponse_formatter(response: HTTPResponse) -> HTTPResponse:
    """
    Formats JSON serializable response data into a standard format.

    Only works for HTTP responses with JSON serializable data.

    Uses generic formmater to format the response' data.
    """
    status_code = response.status_code
    if status_code == 204:
        # No content response
        return response

    data = json.loads(response.content) if response.content else ""
    response_ok = status_code >= 200 and status_code < 300
    formatted_data = generic_response_data_formatter(data, response_ok)

    # Ensure that the status message is not misleading
    if status_code == 404 and formatted_data["message"] == DEFAULT_ERROR_MSG:
        formatted_data["message"] = DEFAULT_NOT_FOUND_MSG

    content = json.dumps(formatted_data)
    return HttpResponse(content, status=status_code, content_type="application/json")


def drf_response_formatter(response: HTTPResponse) -> HTTPResponse:
    """
    Formats a Django Rest Framework response data into a standard format.

    Works for HTTP responses with JSON serializable data also.

    Formated response data structure:
    ```JSON
    {
        "status": "success" | "error",
        "message": "Request processed successfully" | ...,
        "errors": {
            "field_name": [
                "Error message 1",
                "Error message 2"
            ]
        }, # If response has errors
        "data": { ... }, # If response is successful and has data
        "detail": ..., # Dependent on the response
    }
    ```
    """
    try:
        # Try to render the response
        response = response.render()
    except AttributeError:
        pass
    return json_httpresponse_formatter(response)


def format_response(cbv: CBV = None, formatter: Optional[Formatter] = None) -> CBV:
    """
    Formats the response of a class-based view to a standard format.

    Ensure that the view returns a JSON serializable response.

    :param cbv: The CBV to be decorated.
    :param formatter: Preferred formatter for the view.
    If not provided, `drf_response_formatter` will be used as it is globally compatible.

    Example Usage:
    ```python
    from rest_framework import views

    @format_response
    class DRFFooView(views.APIView):
        ...
    ```

    Or;
    ```python
    from django.views import generic
    def foo_formatter(response: Response) -> Response:
        ...

    @format_response(formatter=foo_formatter)
    class FooView(generic.View):
        ...
    ```
    """
    formatter = formatter or drf_response_formatter
    if cbv is None:
        # Return this same decorator but with the formatter already set
        decorator = functools.partial(format_response, formatter=formatter)
        return decorator

    cbv.dispatch = enforce_format(formatter)(cbv.dispatch)
    return cbv
