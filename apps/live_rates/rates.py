import typing
import datetime
from django.utils import timezone
from django.conf import settings

from helpers.logging import log_exception
from .rate_providers import cleaned_rates_data, mg_link_provider
from .data_cleaners import MGLinkStockRateDataCleaner
from apps.stocks.models import Stock, Rate, MarketType


def save_mg_link_psx_rates_data(mg_link_rates_data: typing.List[typing.Dict]):
    # Load first to ensure the data is valid and the
    # and the values are casted to their proper types
    stocks_rates = []

    for data in cleaned_rates_data(mg_link_rates_data):
        try:
            stock_ticker = data.get("symbol", None)
            if stock_ticker is None or not stock_ticker.strip():
                continue

            stock_ticker = stock_ticker.strip()
            stock_created = False
            stock = Stock.objects.filter(ticker__iexact=stock_ticker).first()
            if not stock:
                stock_title = data.get("company_name", None)
                if stock_title:
                    stock_title = stock_title.strip()

                stock = Stock.objects.create(
                    ticker=stock_ticker.upper(),
                    title=stock_title,
                )
                stock_created = True

            data_cleaner = MGLinkStockRateDataCleaner(data)
            data_cleaner.clean()
            stock_rate = data_cleaner.new_instance(
                stock=stock,
                market=MarketType.FUTURE,
            )
            # If the rate already exists for the stock and the added_at date
            # Ignore the rate and continue to the next one
            if (
                not stock_created
                and Rate.objects.filter(
                    stock_id=stock.id, added_at=stock_rate.added_at
                ).exists()
            ):
                continue
        except Exception as exc:
            log_exception(exc)
            continue
        else:
            stocks_rates.append(stock_rate)

    return Rate.objects.bulk_create(
        stocks_rates, batch_size=5000, ignore_conflicts=False
    )


def get_time_in_pst(hour: int, minute: int = 0, second: int = 0) -> datetime.time:
    return datetime.time(hour, minute, second, tzinfo=settings.PAKISTAN_TIMEZONE)


PSX_MARKET_HOURS = {
    0: [(get_time_in_pst(9, 30), get_time_in_pst(15, 30))],
    1: [(get_time_in_pst(9, 30), get_time_in_pst(15, 30))],
    2: [(get_time_in_pst(9, 30), get_time_in_pst(15, 30))],
    3: [(get_time_in_pst(9, 30), get_time_in_pst(15, 30))],
    4: [
        (get_time_in_pst(9, 15), get_time_in_pst(12)),
        (get_time_in_pst(14, 30), get_time_in_pst(16, 30)),
    ],
}
"""The PSX market hours in PST for each market day of the week"""


def update_stock_rates(
    start_date: typing.Optional[datetime.date] = None,
    end_date: typing.Optional[datetime.date] = None,
):
    """
    Update stock rates data in DB with rates from MGLink.

    :param start_date: Start date to fetch rates from.
    :param end_date: End date to fetch rates from.
    """

    def adjust_date_range_for_latest_rates(
        start_date: typing.Optional[datetime.date],
        end_date: typing.Optional[datetime.date],
    ) -> typing.Tuple[typing.Optional[datetime.date], typing.Optional[datetime.date]]:
        """
        Based on client request,

        Only when fetching the latest rates - start_date and end_date are None;
        This function adjusts the date range to the current date if the current
        time is outside the PSX market hours.

        However, if the current time is within the PSX market hours, the date range
        is returned as is (None, None).
        """
        if any([start_date, end_date]):
            return start_date, end_date

        # Both start_date and end_date are None from here on
        weekday_now = timezone.now().weekday()
        if weekday_now not in PSX_MARKET_HOURS:
            return start_date, end_date

        market_hours = PSX_MARKET_HOURS[weekday_now]
        time_now_pst = timezone.now().astimezone(settings.PAKISTAN_TIMEZONE).time()
        for market_hour in market_hours:
            market_open_pst, market_close_pst = market_hour

            # Based on the client request, we should only fetch the latest rates
            # if the current time is within the PSX market hours
            if not (market_open_pst <= time_now_pst <= market_close_pst):
                start_date = timezone.now().date()
                end_date = start_date
                return start_date, end_date

        return start_date, end_date

    start_date, end_date = adjust_date_range_for_latest_rates(start_date, end_date)
    rates_data = mg_link_provider.fetch_psx_rates(start_date, end_date)
    save_mg_link_psx_rates_data(rates_data)
    # Just return this for now to be able to track date used for fetching rates
    # in admin logs
    return start_date, end_date
