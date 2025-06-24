import typing
import decimal
from dateutil.parser import parse
from django.conf import settings

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from helpers.data_utils import cleaners as cl
from .models import Investment


def toDecimal(val):
    if not val:
        return decimal.Decimal(0)
    return decimal.Decimal(val).quantize(
        decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
    )


def toDate(val, timezone: typing.Optional[str] = None):
    if not val:
        return None
    tz = zoneinfo.ZoneInfo(timezone) if timezone else zoneinfo.ZoneInfo("UTC")
    return parse(val).astimezone(tz).date()


def toTime(val, timezone: typing.Optional[str] = None):
    if not val:
        return None

    tz = zoneinfo.ZoneInfo(timezone) if timezone else zoneinfo.ZoneInfo("UTC")
    return parse(val).astimezone(tz).time()


_DataCleaner = typing.TypeVar("_DataCleaner", bound=cl.ModelDataCleaner)


def _parse_to_decimal(*fields: str):
    def decorator(data_cleaner_cls: typing.Type[_DataCleaner]):
        for field in fields:
            if field in data_cleaner_cls.exclude:
                continue

            field_parsers = data_cleaner_cls.parsers.get(field, [])
            data_cleaner_cls.parsers[field] = [*field_parsers, toDecimal]
        return data_cleaner_cls

    return decorator


@_parse_to_decimal(*Investment.ADDITIONAL_FEES, "rate")
class InvestmentDataCleaner(cl.ModelDataCleaner[Investment]):
    model = Investment
    exclude = [
        "portfolio",
        "transaction_type",
        "stock",
        "quantity",
        "brokerage_fee",
        "added_at",
        "updated_at",
    ]
    key_mappings = {
        "transaction_date": "TRDATE",
        "settlement_date": "STDATE",
        "transaction_time": "TIME",
        "location": "LOC",
        "client_category": "CLIENT_CAT",
        "cdc_id": "CDCID",
        "commission": "COMM",
        # Additional mappings for Excel and PDF formats
        "symbol": "SYMBOL",
        "symbol_title": "SYMBOL_TITLE",
        "rate": "RATE",
        "quantity": "BUY",
        "divestments": "SELL",
        "client": "UIN",
        "client_title": "CLIENT_TITLE",
    }
    parsers = {
        "transaction_date": [
            lambda val: toDate(val, timezone=str(settings.PAKISTAN_TIMEZONE)),
        ],
        "settlement_date": [
            lambda val: toDate(val, timezone=str(settings.PAKISTAN_TIMEZONE)),
        ],
        "transaction_time": [
            lambda val: toTime(val, timezone=str(settings.PAKISTAN_TIMEZONE)),
        ],
    }

    def to_key(self, field_name: str) -> str:
        key = super().to_key(field_name)
        if field_name not in type(self).key_mappings:
            key = key.upper().replace("_", " ")
        return key
