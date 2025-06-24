# management/commands/backfill_historical.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from psxscreener.models import Stock, LastDataUpdate
from psxscreener.views import fetch_stock_data, save_stock_data, HISTORY_API_URL
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backfill historical stock data for a specific date range'

    def add_arguments(self, parser):
        parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
        parser.add_argument('--end-date', type=str, help='End date in YYYY-MM-DD format')
        parser.add_argument('--batch-size', type=int, default=30, help='Number of days to fetch in each batch')

    def handle(self, *args, **options):
        try:
            # Parse dates
            start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            batch_size = options['batch_size']

            # Calculate number of batches
            total_days = (end_date - start_date).days + 1
            num_batches = (total_days + batch_size - 1) // batch_size

            self.stdout.write(f"Starting backfill from {start_date} to {end_date} in {num_batches} batches")

            current_start = start_date
            while current_start <= end_date:
                current_end = min(current_start + timedelta(days=batch_size-1), end_date)
                
                self.stdout.write(f"Fetching data for {current_start} to {current_end}")
                
                # Fetch data from API
                api_url = HISTORY_API_URL.format(
                    start_date=current_start.strftime('%Y-%m-%d'),
                    end_date=current_end.strftime('%Y-%m-%d')
                )
                data = fetch_stock_data(api_url)
                
                if data:
                    # Save data for each date in the batch
                    current_date = current_start
                    while current_date <= current_end:
                        if save_stock_data(data, current_date):
                            LastDataUpdate.objects.update_or_create(
                                last_update=current_date,
                                defaults={'is_success': True}
                            )
                            self.stdout.write(self.style.SUCCESS(f"Saved data for {current_date}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"Failed to save data for {current_date}"))
                        current_date += timedelta(days=1)
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to fetch data for {current_start} to {current_end}"))
                
                current_start += timedelta(days=batch_size)

            self.stdout.write(self.style.SUCCESS("Backfill completed successfully"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during backfill: {str(e)}"))
            logger.error(f"Error during backfill: {str(e)}")