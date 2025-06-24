import typing
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import date, timedelta

from apps.live_rates.rate_providers import mg_link_provider
from apps.live_rates.rates import save_mg_link_psx_rates_data
from apps.live_rates.scheduled_tasks import schedule_stock_rates_update


class Command(BaseCommand):
    help = (
        "Update or schedule updates of stock rates data in DB with rates from MGLink."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--start_date",
            type=str,
            help="Start date in YYYY-MM-DD format. If not provided, defaults to 30 days ago.",
        )
        parser.add_argument(
            "--end_date",
            type=str,
            help="End date in YYYY-MM-DD format. If not provided, defaults to today.",
        )
        parser.add_argument(
            "--latest",
            action="store_true",
            help="Update rates for the latest available date only.",
        )
        parser.add_argument(
            "--schedule",
            action="store_true",
            help="""
            Schedule a task to update stock rates data based on the provided interval.

            Deletes the existing schedule if it already exists.

            Defaults to repeating indefinitely every 5 minutes.
            """,
        )
        parser.add_argument(
            "--repeats",
            type=int,
            default=-1,
            help="Number of times to repeat the task. -1 to repeat indefinitely.",
        )
        parser.add_argument(
            "--cron",
            type=str,
            default="*/5 * * * *",
            help="Cron expression defining the interval at which the task should run.",
        )

    def handle(self, *args, **options):
        start_date_str: str = options["start_date"]
        end_date_str: str = options["end_date"]
        latest: bool = options["latest"]
        schedule: bool = options["schedule"]
        repeats: int = options["repeats"]
        cron: str = options["cron"]

        if latest and (start_date_str or end_date_str):
            self.stdout.write(
                self.style.ERROR("Cannot use --latest with --start_date or --end_date.")
            )
            return

        if latest:
            start_date = end_date = None
        else:
            start_date = (
                parse_date(start_date_str)
                if start_date_str
                else (timezone.now() - timedelta(days=30)).date()
            )
            end_date = (
                parse_date(end_date_str) if end_date_str else timezone.now().date()
            )

            if start_date > end_date:
                self.stdout.write(
                    self.style.ERROR("Start date cannot be after end date.")
                )
                return

        if not schedule:
            self.update_now(start_date, end_date)
        else:
            self.schedule_update(
                start_date=start_date, end_date=end_date, repeats=repeats, cron=cron
            )

    def update_now(
        self, start_date: typing.Optional[date], end_date: typing.Optional[date]
    ):
        latest = start_date == end_date
        try:
            if latest:
                self.stdout.write("Fetching rates for latest available rates...")
            else:
                self.stdout.write(f"Fetching rates from {start_date} to {end_date}...")
            rates_data = mg_link_provider.fetch_psx_rates(start_date, end_date)
            
            self.stdout.write(
                self.style.SUCCESS(f"{len(rates_data)} rates fetched from MGLink.")
            )
            self.stdout.write("Saving rates to DB...")

            save_mg_link_psx_rates_data(rates_data)
            if latest:
                self.stdout.write(
                    self.style.SUCCESS("Successfully updated latest rates data.")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated stock rates data from {start_date} to {end_date}."
                    )
                )
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"Error updating stock rates data: {exc}")
            )

    def schedule_update(self, *args, **kwargs):
        try:
            self.stdout.write(
                f"Scheduling rates update to run every {kwargs.get('cron')}..."
            )
            schedule_stock_rates_update(*args, **kwargs)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Stock rates update scheduled to run every {kwargs.get('cron')}."
                )
            )

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"Error scheduling stock rates update: {exc}")
            )
