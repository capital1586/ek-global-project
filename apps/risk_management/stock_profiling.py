import datetime
import decimal
import functools
import typing
import uuid
from concurrent.futures import ThreadPoolExecutor

from apps.accounts.models import UserAccount
from apps.portfolios.models import Portfolio
from apps.risk_management.models import RiskProfile
from apps.stocks.models import Stock, StockIndices
from apps.stocks.helpers import get_stocks_by_indices
from helpers.utils.time import timeit
from helpers.utils.datetime import timedelta_code_to_datetime_range, activate_timezone
from .criteria.criteria import Criteria, evaluate_criteria, CriterionStatus


def get_stock_price_on_date(
    stock: Stock,
    date: datetime.date,
    *,
    tolerance: int = 5,
    positive_tolerance: bool = False,
) -> decimal.Decimal:
    """
    Get the price of a stock on a given date. If the price is not available for the given date,
    the function will go back a number of days specified by the tolerance parameter to find the
    closest available price.

    :param stock: A Stock object to get the price for
    :param date: The date to get the price for
    :param tolerance: The number of days to go back if the price is not available for the given date
    :param positive_tolerance: If True, the function will go forward in time instead of backwards
    :return: The price of the stock on the given date
    """
    if tolerance < 1:
        raise ValueError("Tolerance must be greater than 0")
    
    price = stock.get_price_on_date(date)
    if price:
        return price

    for i in range(1, tolerance + 1):
        if positive_tolerance:
            previous_date = date + datetime.timedelta(days=i)
        else:
            previous_date = date - datetime.timedelta(days=i)
        
        price = stock.get_price_on_date(previous_date)
        if not price:
            continue
        return price

    return decimal.Decimal(0.0)


def calculate_stock_percentage_return(
    stock: Stock, start_date: datetime.date, end_date: datetime.date
) -> decimal.Decimal:
    """
    Calculate the percentage return of a stock over a period of time.

    :param stock: A Stock object to calculate the return for
    :param start_date: The start date of the period
    :param end_date: The end date of the period
    :return: The percentage return of the stock
    """
    start_price = get_stock_price_on_date(stock, start_date, tolerance=10)
    end_price = get_stock_price_on_date(stock, end_date, tolerance=10)
    if not start_price or not end_price:
        return decimal.Decimal(0.0)

    return (((end_price - start_price) / start_price) * 100).quantize(
        decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
    )


def calculate_percentage_ranking(
    evaluation_result: typing.Dict[str, CriterionStatus],
) -> int:
    """Calculate the percentage ranking of the stock based on the evaluation result."""
    score = sum((status.value for status in evaluation_result.values()))
    expected_score = sum((CriterionStatus.PASSED.value for _ in evaluation_result))
    return round((score / expected_score) * 100)


PERCENTAGE_RETURN_INDICATORS_TIMEDELTA_CODES = (
    "1D",
    "3D",
    "1W",
    "1M",
    "YTD",
)


@timeit
def generate_stock_profile(
    stock: Stock, criteria: Criteria, risk_profile: RiskProfile
) -> dict:
    """
    Generates the risk profile for a single stock.

    :param stock: A Stock object to evaluate
    :param criteria: The criteria to evaluate the stock against
    :return: A dictionary containing the stock's profile and evaluation
    """
    stock_profile = {
        # First add the basic information about the stock
        "symbol": stock.ticker,
        "close": stock.price
    }

    with activate_timezone(risk_profile.owner.timezone):
        # Calculate the percentage return for the stock over user defined time periods
        if risk_profile.period_return_start and risk_profile.period_return_end:
            percentage_return = calculate_stock_percentage_return(
                stock, risk_profile.period_return_start, risk_profile.period_return_end
            )
            # period = f"{risk_profile.period_return_start.strftime("%d.%m.%Y")} - {risk_profile.period_return_end.strftime("%d.%m.%Y")}"
            stock_profile["period return (%)"] = float(percentage_return)

        # Calculate the percentage return for the stock over different (default) time periods
        # Update the stock profile with the percentage return for each time period
        for timedelta_code in PERCENTAGE_RETURN_INDICATORS_TIMEDELTA_CODES:
            start, end = timedelta_code_to_datetime_range(timedelta_code)
            percentage_return = calculate_stock_percentage_return(
                stock, start.date(), end.date()
            )
            stock_profile[f"{timedelta_code} return (%)"] = float(percentage_return)

        evaluation_result = evaluate_criteria(stock, criteria=criteria)
        stock_profile.update(evaluation_result)
        percentage_ranking = calculate_percentage_ranking(evaluation_result)
        # This is the percentage ranking of the stock based on the evaluation result
        # It should be the last key in the dictionary
        stock_profile["EK score (%)"] = percentage_ranking
    return stock_profile


@timeit
def load_risk_profile(
    risk_profile: RiskProfile,
    stockset: str,
    criteria: Criteria,
) -> list:
    """
    Load the risk profile for the given stockset and criteria.

    :param risk_profile: The risk profile to load the profile for
    :param stockset: The stockset to evaluate the profile against
    :param criteria: The criteria to evaluate the stocks against
    :return: A list of results of each stock's evaluation
    """
    stocks = resolve_stockset(stockset, risk_profile)
    if not stocks:
        return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        profiles = list(
            executor.map(
                lambda stock: generate_stock_profile(stock, criteria, risk_profile),
                stocks,
            )
        )

    return profiles


def portfolio_stockset(risk_profile: RiskProfile, portofolio_id: uuid.UUID):
    """
    Return the stocks in the portfolio with the given ID, if the portfolio exists
    for the risk profile's owner.

    The stocks are fetched from the portfolio's investments.

    :param risk_profile: The risk profile to fetch the portfolio from
    :param portofolio_id: The ID of the portfolio to fetch the stocks from
    """
    try:
        stock_ids = (
            risk_profile.owner.portfolios.prefetch_related(
                "investments", "investments__stock"
            )
            .get(id=portofolio_id)
            .investments.values_list("stock", flat=True)
        )
    except Portfolio.DoesNotExist:
        return []
    else:
        return (
            Stock.objects.filter(id__in=stock_ids).distinct()
        )


DEFAULT_STOCKSETS: typing.Dict[str, typing.Callable[[], typing.Iterable[Stock]]] = {
    index.name.upper(): functools.partial(
        lambda *_, index: get_stocks_by_indices(index), index=index
    )
    for index in StockIndices
}


def resolve_stockset(stockset: str, risk_profile: RiskProfile):
    """
    Resolve the given stockset to a list of stocks.

    If the stockset is a UUID, it is assumed to be a portfolio ID
    and the stocks in the portfolio are returned.

    :param stockset: The stockset to resolve
    :param risk_profile: The risk profile to resolve the stockset for
    :return: A collection of stocks in the stockset
    """
    resolver = DEFAULT_STOCKSETS.get(stockset.upper(), None)
    if not resolver:
        try:
            return portfolio_stockset(risk_profile, uuid.UUID(stockset))
        except ValueError:
            return []

    return resolver(risk_profile)


def get_available_stocksets_for_user(user: UserAccount):
    """
    Return the available stocksets for the user.
    """
    stocksets = [
        {"name": stockset.replace("_", " "), "value": stockset.lower()}
        for stockset in DEFAULT_STOCKSETS
    ]

    portfolio_values = user.portfolios.values("id", "name")
    for portfolio in portfolio_values:
        stockset = {}
        stockset["value"] = portfolio["id"]
        stockset["name"] = f"Portfolio: {portfolio['name']}"
        stocksets.append(stockset)
    return stocksets
