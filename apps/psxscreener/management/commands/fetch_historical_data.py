from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from psxscreener.models import Stock, LastDataUpdate
from psxscreener.views import fetch_stock_data, save_stock_data, HISTORY_API_URL
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches and stores daily historical stock data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of historical data to fetch'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force fetch even if data exists for the date'
        )

    def handle(self, *args, **options):
        try:
            days = options['days']
            force = options['force']
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)

            self.stdout.write(f'Fetching historical data from {start_date} to {end_date}')

            # Format dates for API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Get the latest date in our database
            latest_date = Stock.objects.aggregate(Max('date'))['date__max']

            # Check if we need to fetch new data
            if force or not latest_date or latest_date < end_date:
                # Fetch new data from API
                api_url = HISTORY_API_URL.format(start_date=start_date_str, end_date=end_date_str)
                new_data = fetch_stock_data(api_url)

                if new_data:
                    # Save the data for each date in the range
                    current_date = start_date
                    while current_date <= end_date:
                        if save_stock_data(new_data, current_date):
                            LastDataUpdate.objects.update_or_create(
                                last_update=current_date,
                                defaults={'is_success': True}
                            )
                            self.stdout.write(self.style.SUCCESS(f'Successfully saved data for {current_date}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'Failed to save data for {current_date}'))
                        current_date += timedelta(days=1)
                else:
                    self.stdout.write(self.style.ERROR('Failed to fetch new data from API'))
            else:
                self.stdout.write(self.style.SUCCESS('Database is already up to date'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            logger.error(f'Error in fetch_historical_data: {str(e)}') 