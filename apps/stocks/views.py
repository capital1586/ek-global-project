from typing import Dict, Any
import json
from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .helpers import (
    handle_rates_file,
    handle_kse_rates_file,
    RateUploadError,
    EXPECTED_KSE_COLUMNS,
    EXPECTED_RATE_COLUMNS,
)
from helpers.logging import log_exception
from helpers.exceptions import capture
from .models import Stock


class UploadsView(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ["get", "post"]
    template_name = "stocks/uploads.html"

    def post(self, request, *args, **kwargs):
        rates_file = request.FILES.get("rates_file", None)
        kse_rates_file = request.FILES.get("kse_rates_file", None)
        try:
            if rates_file:
                handle_rates_file(rates_file)
                messages.success(request, "Rates upload successful.")

            if kse_rates_file:
                handle_kse_rates_file(kse_rates_file)
                messages.success(request, "KSE upload successful.")
        except RateUploadError as exc:
            log_exception(exc)
            messages.error(request, str(exc))

        except Exception as exc:
            log_exception(exc)
            if rates_file:
                extra_msg = f"Expected columns include; {', '.join(EXPECTED_RATE_COLUMNS.keys())}"
            else:
                extra_msg = f"Expected columns include; {', '.join(EXPECTED_KSE_COLUMNS.keys())}"

            messages.error(
                request,
                "Upload failed! Ensure the CSV file is in the correct format and contains the correct data. "
                + extra_msg,
            )

        return redirect("stocks:uploads")


@capture.enable
class StockLatestPriceView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]

    @capture.capture(content="Oops! An error occurred")
    def post(self, request, *args: Any, **kwargs: Any) -> JsonResponse:
        data: Dict = json.loads(request.body)
        ticker = data["stock"]
        stock = get_object_or_404(Stock, ticker=ticker)
        latest_price = stock.price
        if latest_price is None:
            return JsonResponse(
                data={
                    "status": "error",
                    "detail": "No price found",
                },
                status=417,
            )

        return JsonResponse(
            data={
                "status": "success",
                "detail": "Price fetched successfully",
                "data": {
                    "latest_price": latest_price,
                },
            },
            status=200,
        )


uploads_view = UploadsView.as_view()
stock_latest_price_view = StockLatestPriceView.as_view()
