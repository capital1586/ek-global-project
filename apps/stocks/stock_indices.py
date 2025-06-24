from pathlib import Path
import typing
import csv
from django.db import models

from .models import Stock, StockIndices
from apps.live_rates.rate_providers import convert_keys_to_snake_case
from helpers.models.functions import PostgreSQLArrayAppend
from helpers.utils.time import timeit


@timeit
def index_stocks(indices_file: typing.Union[str, Path]):
    """
    Update existing stock indices using data contained in a CSV file.

    :param indices_file: Path to the CSV file containing the indices data.
    """
    with open(indices_file, "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            data = convert_keys_to_snake_case(row)
            stock_ticker = data.get("symbol", None)
            index_id = data.get("index_id", None)
            if not stock_ticker or index_id is None:
                continue

            stock_index = StockIndices(int(index_id))
            stock = Stock.objects.filter(ticker__iexact=stock_ticker.strip()).first()
            if stock:
                if stock_index not in stock.indices:
                    stock.indices = PostgreSQLArrayAppend(
                        models.F("indices"), models.Value(stock_index)
                    )
                    stock.save(update_fields=["indices"])
    return
