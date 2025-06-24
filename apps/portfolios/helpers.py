from concurrent.futures import ThreadPoolExecutor
import datetime
import decimal
import functools
import typing
import asyncio
from asgiref.sync import sync_to_async
from django.db import models

from .models import Investment, Portfolio
from apps.stocks.models import KSE100Rate, Stock
from helpers.utils.colors import random_colors
from helpers.utils.models import get_objects_within_datetime_range
from helpers.utils.datetime import (
    activate_timezone,
    split,
    timedelta_code_to_datetime_range,
)
from helpers.caching import ttl_cache
from helpers.utils.misc import merge_dicts


def get_portfolio_stocks(portfolio: Portfolio):
    """Returns the stocks invested in a portfolio"""
    stock_ids = portfolio.investments.select_related("stock").values_list(
        "stock_id", flat=True
    )
    return Stock.objects.filter(id__in=stock_ids)


def get_portfolio_allocation_data(portfolio: Portfolio) -> typing.Dict[str, float]:
    """
    Returns a mapping of the ticker symbols of stocks invested in,
    to the respective cost amounts invested in them, in a portfolio
    """
    allocation_data = {}

    for investment in portfolio.investments.select_related("stock").all():
        allocation_data[investment.symbol] = allocation_data.get(
            investment.symbol, 0.00
        ) + float(abs(investment.cost))
    return allocation_data


def get_portfolio_allocation_piechart_data(portfolio: Portfolio) -> str:
    """Returns the portfolio's stock allocation data in a format suitable for Chart.js pie chart."""
    allocation_data = get_portfolio_allocation_data(portfolio)
    colors = [next(random_colors()) for _ in range(len(allocation_data))]
    return {"data": allocation_data, "colors": colors}


# The investments based function for fetching allocation
# data is slightly efficient than the portfolio based function
def get_investments_allocation_data(
    investments: models.QuerySet[Investment],
) -> typing.Dict[str, float]:
    """
    Returns a mapping of the ticker symbols of stocks invested in,
    to the respective cost amounts invested in them, from the investments given.
    """
    allocation_data = {}

    for investment in investments:
        allocation_data[investment.symbol] = allocation_data.get(
            investment.symbol, 0.00
        ) + float(abs(investment.cost))
    return allocation_data


def get_investments_allocation_piechart_data(
    investments: models.QuerySet[Investment],
) -> str:
    """Returns the investments' stock allocation data in a format suitable for Chart.js pie chart."""
    allocation_data = get_investments_allocation_data(investments)
    colors = [next(random_colors()) for _ in range(len(allocation_data))]
    return {"data": allocation_data, "colors": colors}


def get_close_price_range_for_period(
    rate_model_or_qs: typing.Union[models.Model, models.QuerySet],
    /,
    period_start: typing.Union[datetime.date, datetime.datetime],
    period_end: typing.Union[datetime.date, datetime.datetime],
    dt_field: str,
):
    """
    Returns the minimum and maximum close prices within a specified date/datetime period

    :param rate_model_or_qs: rate model or queryset to filter on.
    :param period_start: start date/datetime of the period.
    :param period_end: end date/datetime of the period.
    :param dt_field: The date/datetime field to filter on.
    :return: The minimum and maximum close prices within the specified period.
    """
    rates = get_objects_within_datetime_range(
        rate_model_or_qs, period_start, period_end, dt_field
    )
    aggregate = rates.aggregate(
        min_close=models.Min("close"), max_close=models.Max("close")
    )
    min_close = aggregate.get("min_close")
    max_close = aggregate.get("max_close")
    return min_close, max_close


DATETIME_FILTERS = ("5D", "1W", "1M", "3M", "6M", "1Y", "YTD", "5Y")


@ttl_cache
def datetime_filter_to_date_range(
    _filter: str, timezone: str = None
) -> typing.Tuple[typing.Optional[datetime.date], datetime.date]:
    """
    Parses the datetime filter into a start and end date range.

    :param _filter: The datetime filter to parse.
    :param timezone: The preferred timezone to use.
    :return: A tuple containing the start and end date.
    :raises ValueError: If the filter is invalid.
    """
    if _filter not in DATETIME_FILTERS:
        raise ValueError(f"Invalid datetime filter: {_filter}")

    start, end = timedelta_code_to_datetime_range(_filter, timezone=timezone)
    return start.date(), end.date()


@ttl_cache(ttl=60 * 5)
def get_kse_performance_data(
    dt_filter: str, timezone: typing.Optional[str] = None
) -> typing.Dict[str, float]:
    """
    Returns the KSE100 performance data for the time period
    specified by the datetime filter.

    :param dt_filter: The datetime filter to use.
    :param timezone: The preferred timezone to use.
    """
    with activate_timezone(timezone):
        start_date, end_date = datetime_filter_to_date_range(dt_filter)
        if not start_date:
            # If the start date is None, use the date of the first KSE100Rate
            earliest_rate = KSE100Rate.objects.only("date").order_by("date").first()
            if earliest_rate:
                start_date = earliest_rate.date

        delta = None

        def get_kse_performance_data_for_period(period_start, period_end):
            nonlocal kse_performance_data, delta
            if delta is None:
                delta = period_end - period_start

            pre_period_start = period_start - delta

            pre_period_start_price = KSE100Rate.get_close_on_date(pre_period_start)
            period_start_price = KSE100Rate.get_close_on_date(period_start)
            period_end_price = KSE100Rate.get_close_on_date(period_end)

            percentage_change_at_period_start = 0.00
            percentage_change_at_period_end = 0.00
            if pre_period_start_price and period_start_price:
                percentage_change_at_period_start = (
                    (period_start_price - pre_period_start_price)
                    / pre_period_start_price
                ) * 100

            if period_start_price and period_end_price:
                percentage_change_at_period_end = (
                    (period_end_price - period_start_price) / period_start_price
                ) * 100

            return {
                period_start.isoformat(): percentage_change_at_period_start,
                period_end.isoformat(): percentage_change_at_period_end,
            }

        async def main():
            async_func = sync_to_async(get_kse_performance_data_for_period)
            tasks = []
            for periods in split(start_date, end_date, parts=5):
                task = asyncio.create_task(async_func(*periods))
                tasks.append(task)

            return await asyncio.gather(*tasks)

        results = asyncio.run(main())
        # Merge the results such that the most recent result updates the existing one
        kse_performance_data = functools.reduce(merge_dicts, results)
        return kse_performance_data


def get_portfolio_percentage_return_on_dates(
    portfolio: Portfolio, *dates: datetime.date
):
    if not dates:
        raise ValueError()

    with ThreadPoolExecutor(max_workers=2) as executor:
        result = executor.map(portfolio.get_percentage_return_on_investments, dates)
    return list(result)


@ttl_cache
def get_investment_percentage_return_on_dates(
    investment: Investment, *dates: datetime.date
):
    if not dates:
        raise ValueError()

    with ThreadPoolExecutor(max_workers=2) as executor:
        result = executor.map(
            lambda date: investment.get_percentage_return_on_date(date)
            or decimal.Decimal(0),
            dates,
        )
    return list(result)


def get_portfolio_performance_data(
    portfolio: Portfolio,
    dt_filter: str,
    timezone: str = None,
    stocks: typing.Optional[typing.List[str]] = None,
) -> typing.Dict[str, typing.Dict[str, float]]:
    portfolio_investments = (
        portfolio.investments.only(
            "transaction_type",
            "stock",
            "rate",
            "quantity",
            "brokerage_fee",
            *Investment.ADDITIONAL_FEES,
        )
        .select_related("stock")
        # .prefetch_related("stock__rates")
    )

    with activate_timezone(timezone):
        start_date, end_date = datetime_filter_to_date_range(dt_filter)
        if not start_date:
            # If the start date is None, use the date the portfolio was created
            start_date = portfolio.created_at.date()

        def get_portfolio_percentage_return_values_for_period(period_start, period_end):
            nonlocal percentage_return_values
            percentage_returns = get_portfolio_percentage_return_on_dates(
                portfolio, period_start, period_end
            )
            return {
                period_start.isoformat(): float(percentage_returns[0]),
                period_end.isoformat(): float(percentage_returns[1]),
            }

        def get_investment_percentage_return_values_for_period(
            period_start, period_end
        ):
            nonlocal percentage_return_values
            nonlocal stocks
            period_start_iso_fmt = period_start.isoformat()
            period_end_iso_fmt = period_end.isoformat()
            result = {}

            for stock in stocks:
                investment: Investment = portfolio_investments.filter(
                    stock__ticker=stock
                ).first()
                if not investment:
                    continue
                percentage_returns = get_investment_percentage_return_on_dates(
                    investment, period_start, period_end
                )
                result[stock] = {
                    period_start_iso_fmt: float(percentage_returns[0]),
                    period_end_iso_fmt: float(percentage_returns[1]),
                }
            return result

        if stocks:
            func = get_investment_percentage_return_values_for_period
        else:
            func = get_portfolio_percentage_return_values_for_period

        async def main():
            async_func = sync_to_async(func)
            tasks = []
            for period in split(start_date, end_date, parts=5):
                task = asyncio.create_task(async_func(*period))
                tasks.append(task)

            return await asyncio.gather(*tasks)

        results = asyncio.run(main())
        # Merge the results such that the most recent result updates the existing one
        percentage_return_values = functools.reduce(merge_dicts, results)
        if stocks:
            return percentage_return_values
        return {"all": percentage_return_values}


def get_portfolio_performance_graph_data(
    portfolio: Portfolio,
    dt_filter: str = "5D",
    timezone: str = None,
    stocks: typing.Optional[typing.List[str]] = None,
) -> typing.Dict[str, float]:
    """
    Returns an aggregates the portfolio investments and
    KSE100 performance data to be plotted on a line graph

    :param portfolio: The portfolio to get performance data for.
    :param dt_filter: The datetime filter to use.
    :param timezone: The preferred timezone to use.
    :param stocks: Limit performance data aggregation to include
        only investments in these stocks(stocks with the ticker symbol).
    """
    try:
        kse_performance_data = get_kse_performance_data(dt_filter, timezone)
    except ValueError:
        kse_performance_data = {}
    try:
        portfolio_performance_data = get_portfolio_performance_data(
            portfolio=portfolio, dt_filter=dt_filter, timezone=timezone, stocks=stocks
        )
    except ValueError:
        portfolio_performance_data = {}

    colors = {}
    colors["KSE100"] = next(random_colors())
    for key in portfolio_performance_data:
        colors[key] = next(random_colors())

    return {
        "KSE100": kse_performance_data,
        "portfolio": portfolio_performance_data,
        "colors": colors,
    }


def get_stocks_invested_from_portfolio(portfolio: Portfolio) -> typing.List[str]:
    stock_tickers = (
        portfolio.investments.only("stock")
        .select_related("stock")
        .values_list("stock__ticker", flat=True)
    )
    return list(set(stock_tickers))


def get_stocks_invested_from_investments(
    investments: models.QuerySet[Investment],
) -> typing.List[str]:
    """Returns the tickers of all stocks invested in from the given investment set"""
    stock_tickers = investments.values_list("stock__ticker", flat=True)
    return list(set(stock_tickers))
