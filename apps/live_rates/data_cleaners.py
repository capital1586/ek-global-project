from helpers.data_utils import cleaners as cl
from dateutil.parser import parse as parse_date

from apps.stocks.models import Rate
from apps.stocks.helpers import get_trend


def null_to_zero(value):
    return value if value is not None else 0.00


class MGLinkStockRateDataCleaner(cl.ModelDataCleaner[Rate]):
    model = Rate
    exclude = ["id", "stock", "market", "trend", "updated_at"]
    key_mappings = {
        "added_at": "create_date_time",
        "close": "last",
    }
    parsers = {
        "open": [null_to_zero, float],
        "high": [null_to_zero, float],
        "low": [null_to_zero, float],
        "close": [null_to_zero, float],
        "volume": [null_to_zero, float],
        "previous_close": [null_to_zero, float],
        "added_at": [lambda v: parse_date(v).astimezone() if isinstance(v, str) else v],
    }

    def new_instance(self, **extra_fields):
        rate = super().new_instance(**extra_fields)

        if not extra_fields.get("trend", None):
            rate.trend = get_trend(rate.previous_close, rate.close)
        return rate
