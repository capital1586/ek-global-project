from django.db import connection
from django.core.management.base import BaseCommand

def run_migrations():
    """Add missing columns to psxscreener_stock table"""
    print("Running manual migrations for psxscreener_stock table...")
    
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
            print("Added 'industry' column")
        
        # Add country column if it doesn't exist
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='psxscreener_stock' AND column_name='country';
        """)
        if not cursor.fetchone():
            cursor.execute("""
            ALTER TABLE psxscreener_stock ADD COLUMN country varchar(50) DEFAULT 'Pakistan';
            """)
            print("Added 'country' column")
        
        # Add exchange column if it doesn't exist
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='psxscreener_stock' AND column_name='exchange';
        """)
        if not cursor.fetchone():
            cursor.execute("""
            ALTER TABLE psxscreener_stock ADD COLUMN exchange varchar(20) DEFAULT 'PSX';
            """)
            print("Added 'exchange' column")
        
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
                print(f"Added '{column_name}' column")
        
        print("Manual migrations completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

class Command(BaseCommand):
    help = 'Runs manual migrations to add missing columns to psxscreener_stock table'
    
    def handle(self, *args, **options):
        run_migrations()
        self.stdout.write(self.style.SUCCESS('Successfully ran manual migrations'))

if __name__ == "__main__":
    # This allows running the script directly
    run_migrations() 