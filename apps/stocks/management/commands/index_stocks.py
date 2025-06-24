from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.stocks import stock_indices


class Command(BaseCommand):
    help = "Add/Update stock indices from a CSV file containing the stock indices data."

    def add_arguments(self, parser):
        parser.add_argument(
            "indices_file",
            nargs="?",
            type=lambda p: Path(p).resolve(),
            default=settings.STOCKS_INDICES_FILE,
            help="Path to the CSV file containing the indices data.",
        )

    def handle(self, *args, **options):
        indices_file = options["indices_file"]
        self.stdout.write(f"Indexing stocks using indices defined in: {indices_file}")

        try:
            stock_indices.index_stocks(indices_file)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error indexing stocks: {exc}"))
            return
        else:
            self.stdout.write(self.style.SUCCESS("Stocks indexed successfully."))
        return
