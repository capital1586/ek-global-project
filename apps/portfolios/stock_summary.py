import math
import typing
import decimal
import functools
import attrs
from concurrent.futures import ThreadPoolExecutor
from django.db import models

from .helpers import datetime_filter_to_date_range, get_stocks_invested_from_investments
from .models import TransactionType, Portfolio, Investment
from apps.stocks.models import Rate
from helpers.utils.decimals import to_n_decimal_places
from helpers.utils.datetime import activate_timezone


convert_to_2dp_decimal = functools.partial(to_n_decimal_places, n=2)


@attrs.define(auto_attribs=True, kw_only=True)
class StockSummary:
    """Model to represent a stock's summary in a portfolio"""

    symbol: str
    net_quantity: int = 0
    average_rate: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )
    net_average_cost: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )
    market_rate: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )
    market_value: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )
    net_return_on_investments: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )
    percentage_return_on_investments: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )
    percentage_allocation: typing.Optional[decimal.Decimal] = attrs.field(
        default=None, converter=convert_to_2dp_decimal
    )


def get_stock_summary_from_investments(
    stock: str, investments: models.QuerySet[Investment]
) -> StockSummary:
    investments_for_stock = investments.filter(stock__ticker=stock)
    # If no investments exists, return a stock summary with the default attributes
    if not investments_for_stock.exists():
        return StockSummary(symbol=stock)

    annotated_qs = investments_for_stock.annotate(
        signed_quantity=models.Case(
            models.When(
                transaction_type=TransactionType.SELL, then=-models.F("quantity")
            ),
            default=models.F("quantity"),
            output_field=models.IntegerField(),
        )
    )
    aggregation = annotated_qs.aggregate(
        net_quantity=models.Sum("signed_quantity"),
        average_rate=models.Avg("rate"),
    )

    net_quantity: int = aggregation["net_quantity"]
    average_rate = aggregation["average_rate"]
    net_average_cost = float(net_quantity * average_rate)
    latest_rate_record = (
        Rate.objects.only("stock", "added_at", "close")
        .filter(stock__ticker=stock)
        .order_by("-added_at")
        .first()
    )

    market_rate = None
    market_value = None
    net_return_on_investments = None
    percentage_return_on_investments = None
    if latest_rate_record:
        # Get the current/latest (market) rate
        market_rate = latest_rate_record.close

    if market_rate and net_average_cost:
        market_value = abs(net_quantity) * market_rate
        net_return_on_investments = market_value - net_average_cost
        percentage_return_on_investments = (
            net_return_on_investments / abs(net_average_cost)
        ) * 100

    return StockSummary(
        **{
            "symbol": stock,
            "net_quantity": net_quantity,
            "average_rate": average_rate,
            "net_average_cost": net_average_cost,
            "market_rate": market_rate,
            "market_value": market_value,
            "net_return_on_investments": net_return_on_investments,
            "percentage_return_on_investments": percentage_return_on_investments,
        }
    )


def _update_stock_summary_with_percentage_allocation(
    stock_summary: StockSummary,
    total_quantity_of_stocks_invested_in: int,
):
    if not total_quantity_of_stocks_invested_in:
        stock_summary.percentage_allocation = None
        return stock_summary

    percentage_allocation = (
        stock_summary.net_quantity / abs(total_quantity_of_stocks_invested_in) * 100
    )
    stock_summary.percentage_allocation = percentage_allocation
    return stock_summary


def generate_portfolio_stocks_summary(
    portfolio: Portfolio, dt_filter: str = "5D", timezone: str = None
) -> typing.List[StockSummary]:
    with activate_timezone(timezone):
        start_date, _ = datetime_filter_to_date_range(dt_filter)
        portfolio_investments = portfolio.investments.filter(
            transaction_date__gte=start_date
        ).select_related("stock")

    # If no investments exists, return a summary for the total only
    if not portfolio_investments.exists():
        return [StockSummary(symbol="TOTAL")]

    stocks_invested_in = get_stocks_invested_from_investments(portfolio_investments)
    with ThreadPoolExecutor(max_workers=2) as executor:
        stocks_summaries = list(
            executor.map(
                lambda stock: get_stock_summary_from_investments(
                    stock, portfolio_investments
                ),
                stocks_invested_in,
            )
        )

    net_total_quantity_of_stocks_invested_in = math.fsum(
        summary.net_quantity for summary in stocks_summaries
    )
    net_total_average_cost = math.fsum(
        summary.net_quantity for summary in stocks_summaries
    )
    total_market_value = math.fsum(
        summary.market_value for summary in stocks_summaries if summary.market_value
    )
    net_total_return_on_investments = math.fsum(
        summary.net_return_on_investments
        for summary in stocks_summaries
        if summary.net_return_on_investments
    )
    net_percentage_return_on_investments = math.fsum(
        summary.percentage_return_on_investments
        for summary in stocks_summaries
        if summary.percentage_return_on_investments
    )

    for summary in stocks_summaries:
        summary = _update_stock_summary_with_percentage_allocation(
            summary, net_total_quantity_of_stocks_invested_in
        )

    if net_total_quantity_of_stocks_invested_in:
        net_total_percentage_allocation = math.fsum(
            summary.percentage_allocation
            for summary in stocks_summaries
            if summary.percentage_allocation
        )
    else:
        net_total_percentage_allocation = None

    total_summary = StockSummary(
        **{
            "symbol": "TOTAL",
            "net_quantity": net_total_quantity_of_stocks_invested_in,
            "average_rate": None,
            "net_average_cost": net_total_average_cost,
            "market_rate": None,
            "market_value": total_market_value,
            "net_return_on_investments": net_total_return_on_investments,
            "percentage_return_on_investments": net_percentage_return_on_investments,
            "percentage_allocation": net_total_percentage_allocation,
        }
    )
    stocks_summaries.append(total_summary)
    return stocks_summaries
