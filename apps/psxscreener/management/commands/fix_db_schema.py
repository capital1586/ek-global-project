from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Adds missing columns to psxscreener_stock table'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database schema update...'))
        
        cursor = connection.cursor()
        
        # Check if columns exist before adding them
        try:
            # Add industry column if it doesn't exist
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='psxscreener_stock' AND column_name='industry';
            """)
            if not cursor.fetchone():
                cursor.execute("""
                ALTER TABLE psxscreener_stock ADD COLUMN industry varchar(100) NULL;
                """)
                self.stdout.write(self.style.SUCCESS("Added 'industry' column"))
            
            # Add country column if it doesn't exist
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='psxscreener_stock' AND column_name='country';
            """)
            if not cursor.fetchone():
                cursor.execute("""
                ALTER TABLE psxscreener_stock ADD COLUMN country varchar(50) DEFAULT 'Pakistan';
                """)
                self.stdout.write(self.style.SUCCESS("Added 'country' column"))
            
            # Add exchange column if it doesn't exist
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='psxscreener_stock' AND column_name='exchange';
            """)
            if not cursor.fetchone():
                cursor.execute("""
                ALTER TABLE psxscreener_stock ADD COLUMN exchange varchar(20) DEFAULT 'PSX';
                """)
                self.stdout.write(self.style.SUCCESS("Added 'exchange' column"))
            
            # Add additional columns
            columns_to_add = [
                ('dividend_yield', 'decimal(6,2)'),
                ('pb_ratio', 'decimal(10,2)'),
                ('ps_ratio', 'decimal(10,2)'),
                ('year_high', 'decimal(10,2)'),
                ('year_low', 'decimal(10,2)'),
                ('ma50', 'decimal(10,2)'),
                ('ma200', 'decimal(10,2)'),
                ('rsi14', 'decimal(6,2)'),
                ('avg_volume', 'bigint'),
                ('relative_volume', 'decimal(6,2)'),
                ('change', 'decimal(10,2)')
            ]
            
            for column_name, column_type in columns_to_add:
                cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='psxscreener_stock' AND column_name='{column_name}';
                """)
                if not cursor.fetchone():
                    cursor.execute(f"""
                    ALTER TABLE psxscreener_stock ADD COLUMN {column_name} {column_type} NULL;
                    """)
                    self.stdout.write(self.style.SUCCESS(f"Added '{column_name}' column"))
            
            self.stdout.write(self.style.SUCCESS('Database schema update completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during schema update: {e}"))
            connection.rollback()
            raise
        finally:
            cursor.close() 