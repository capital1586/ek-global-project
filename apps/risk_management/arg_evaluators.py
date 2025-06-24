"""
A collection of argument evaluators for TA-LIB functions
"""

import typing
import datetime
from django.db import models
from django.utils import timezone

from apps.stocks.models import Stock, Rate, StockIndices
from apps.stocks.helpers import get_stocks_by_indices
from .criteria.functions import FunctionSpec, ensure_ndarray


def filter_rate_qs_by_timeperiod(
    rates: models.QuerySet[Rate], timeperiod: typing.Optional[float]
) -> models.QuerySet[Rate]:
    """Returns a filtered Rate queryset based on the provided timeperiod."""
    delta = datetime.timedelta(days=float(timeperiod))
    start_date = timezone.now().date() - delta
    return rates.filter(added_at__date__gte=start_date).distinct("added_at")


@ensure_ndarray(array_dtype=float)
def OPEN_VALUES(stock: Stock, /, spec: FunctionSpec) -> typing.List[float]:
    """Returns a list containing `open` values of a stock rate"""
    rates = stock.rates
    timeperiod = spec.kwargs.get("timeperiod", None)

    if timeperiod is not None:
        rates = filter_rate_qs_by_timeperiod(rates, timeperiod)
    return rates.only("open").values_list("open", flat=True)


@ensure_ndarray(array_dtype=float)
def HIGH_VALUES(stock: Stock, /, spec: FunctionSpec) -> typing.List[float]:
    """Returns a list containing `high` values of a stock rate"""
    rates = stock.rates
    timeperiod = spec.kwargs.get("timeperiod", None)

    if timeperiod is not None:
        rates = filter_rate_qs_by_timeperiod(rates, timeperiod)
    return rates.only("high").values_list("high", flat=True)


@ensure_ndarray(array_dtype=float)
def LOW_VALUES(stock: Stock, /, spec: FunctionSpec) -> typing.List[float]:
    """Returns a list containing `low` values of a stock rate"""
    rates = stock.rates
    timeperiod = spec.kwargs.get("timeperiod", None)

    if timeperiod is not None:
        rates = filter_rate_qs_by_timeperiod(rates, timeperiod)
    return rates.only("low").values_list("low", flat=True)


@ensure_ndarray(array_dtype=float)
def CLOSE_VALUES(stock: Stock, /, spec: FunctionSpec) -> typing.List[float]:
    """Returns a list containing `close` values of a stock rate"""
    rates = stock.rates
    timeperiod = spec.kwargs.get("timeperiod", None)

    if timeperiod is not None:
        rates = filter_rate_qs_by_timeperiod(rates, timeperiod)
    return rates.only("close").values_list("close", flat=True)


@ensure_ndarray(array_dtype=float)
def VOLUME_VALUES(stock: Stock, /, spec: FunctionSpec) -> typing.List[float]:
    """Returns a list containing `volume` values of a stock rate"""
    rates = stock.rates
    timeperiod = spec.kwargs.get("timeperiod", None)

    if timeperiod is not None:
        rates = filter_rate_qs_by_timeperiod(rates, timeperiod)
    return rates.only("volume").values_list("volume", flat=True)


@ensure_ndarray(array_dtype=float)
def KSE100_CLOSE_VALUES(stock: Stock, /, spec: FunctionSpec) -> typing.List[float]:
    """Returns a list containing latest `close` values of KSE100 stocks"""
    kse100_stocks = get_stocks_by_indices(StockIndices.KSE100)

    latest_close_values = []
    for kse100_stock in kse100_stocks:
        try:
            latest_rate = kse100_stock.rates.only("close", "added_at").latest("added_at")
        except Rate.DoesNotExist:
            latest_close_values.append(0.0)
        else:
            latest_close_values.append(latest_rate.close)
    return latest_close_values


###########
# ALIASES #
###########

Open = OPEN_VALUES
High = HIGH_VALUES
Low = LOW_VALUES
Close = CLOSE_VALUES
Volume = VOLUME_VALUES
KSE100Close = KSE100_CLOSE_VALUES

Real = Close
Real0 = KSE100Close
Real1 = Close
