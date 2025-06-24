import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Analyzes API test data for discrepancies with display values'

    def add_arguments(self, parser):
        parser.add_argument('--input-dir', type=str, default='api_test_data', help='Directory containing test data')
        parser.add_argument('--symbol', type=str, default='DGKC', help='Symbol to analyze')

    def handle(self, *args, **options):
        input_dir = options['input_dir']
        symbol = options['symbol']
        
        if not os.path.exists(input_dir):
            self.stdout.write(self.style.ERROR(f'Input directory {input_dir} does not exist'))
            return
            
        self.stdout.write(self.style.NOTICE(f'Analyzing data for {symbol} from {input_dir}...'))
        
        # Load stock data
        stock_data_file = os.path.join(input_dir, f'{symbol}_stock_data.json')
        latest_data_file = os.path.join(input_dir, f'{symbol}_latest.json')
        
        if not os.path.exists(stock_data_file):
            self.stdout.write(self.style.ERROR(f'Stock data file {stock_data_file} does not exist'))
            return
            
        stock_data = self.load_json_file(stock_data_file)
        latest_data = self.load_json_file(latest_data_file) if os.path.exists(latest_data_file) else None
        
        # Analyze data
        self.analyze_stock_data(stock_data, latest_data, symbol)
        
        # Load and analyze announcements
        announcements_file = os.path.join(input_dir, f'{symbol}_announcements.json')
        if os.path.exists(announcements_file):
            announcements = self.load_json_file(announcements_file)
            self.analyze_announcements(announcements, symbol)
        
        # Load and analyze news
        news_file = os.path.join(input_dir, 'news.json')
        if os.path.exists(news_file):
            news = self.load_json_file(news_file)
            self.analyze_news(news)
        
        # Load and analyze indices
        indices_file = os.path.join(input_dir, 'indices.json')
        if os.path.exists(indices_file):
            indices = self.load_json_file(indices_file)
            self.analyze_indices(indices)
        
        # Generate summary report
        self.generate_summary_report(input_dir, symbol)

    def load_json_file(self, filepath):
        """Load data from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading {filepath}: {str(e)}'))
            return None

    def analyze_stock_data(self, stock_data, latest_data, symbol):
        """Analyze stock data for the given symbol"""
        self.stdout.write(self.style.NOTICE('Analyzing stock data...'))
        
        if not stock_data:
            self.stdout.write(self.style.WARNING('No stock data available'))
            return
            
        # Check if stock data is a list and not empty
        if not isinstance(stock_data, list) or len(stock_data) == 0:
            self.stdout.write(self.style.WARNING('Stock data is empty or not a list'))
            return
            
        # Print number of records
        self.stdout.write(f'  Found {len(stock_data)} records for {symbol}')
        
        # Check latest data
        if latest_data:
            self.stdout.write('  Latest stock data:')
            for key, value in latest_data.items():
                self.stdout.write(f'    {key}: {value}')
                
            # Check for critical fields
            critical_fields = ['Symbol', 'Last', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume']
            missing_fields = [field for field in critical_fields if field not in latest_data]
            
            if missing_fields:
                self.stdout.write(self.style.ERROR(f'  Missing critical fields: {", ".join(missing_fields)}'))
            
            # Calculate performance metrics to match what's shown in the 360View
            if len(stock_data) >= 2:
                self.calculate_performance_metrics(stock_data, symbol)
        else:
            self.stdout.write(self.style.WARNING('  No latest data available'))

    def calculate_performance_metrics(self, stock_data, symbol):
        """Calculate performance metrics from stock data"""
        self.stdout.write(self.style.NOTICE('Calculating performance metrics...'))
        
        # Sort data by date to ensure proper calculations
        try:
            sorted_data = sorted(stock_data, key=lambda x: x.get('Date', ''))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error sorting data: {str(e)}'))
            return

        latest = sorted_data[-1]
        
        # Daily performance (already in latest data)
        daily_change = latest.get('PctChange', 0)
        
        # Try to calculate other performance metrics based on available data
        try:
            # Weekly (last 5 trading days)
            weekly_start_price = sorted_data[-6].get('Last', 0) if len(sorted_data) >= 6 else sorted_data[0].get('Last', 0)
            weekly_end_price = latest.get('Last', 0)
            weekly_change = ((weekly_end_price - weekly_start_price) / weekly_start_price * 100) if weekly_start_price else 0
            
            # Monthly (last 20 trading days)
            monthly_start_price = sorted_data[-21].get('Last', 0) if len(sorted_data) >= 21 else sorted_data[0].get('Last', 0)
            monthly_change = ((weekly_end_price - monthly_start_price) / monthly_start_price * 100) if monthly_start_price else 0
            
            # Create a performance object similar to what's used in the view
            performance = {
                'Daily': daily_change,
                'Weekly': weekly_change,
                'Monthly': monthly_change,
                # Other metrics would require longer data history
                'Quarterly': 'N/A (need 3 months data)',
                'SixMonth': 'N/A (need 6 months data)',
                'Yearly': 'N/A (need 1 year data)',
                'YTD': 'N/A (need data from beginning of year)'
            }
            
            self.stdout.write('  Performance metrics:')
            for period, change in performance.items():
                self.stdout.write(f'    {period}: {change}')
                
            # Save the performance metrics
            output_file = os.path.join('api_test_data', f'{symbol}_performance.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(performance, f, indent=4, ensure_ascii=False)
                
            self.stdout.write(self.style.SUCCESS(f'  Performance metrics saved to {output_file}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error calculating performance metrics: {str(e)}'))

    def analyze_announcements(self, announcements, symbol):
        """Analyze company announcements"""
        self.stdout.write(self.style.NOTICE('Analyzing company announcements...'))
        
        if not announcements:
            self.stdout.write(self.style.WARNING('No announcements available'))
            return
            
        # Check if announcements is a list and not empty
        if not isinstance(announcements, list):
            self.stdout.write(self.style.WARNING('Announcements data is not a list'))
            return
            
        self.stdout.write(f'  Found {len(announcements)} announcements for {symbol}')
        
        # Check for recent announcements (last 10)
        recent = announcements[:10] if len(announcements) >= 10 else announcements
        
        self.stdout.write('  Recent announcements:')
        for i, announcement in enumerate(recent, 1):
            date = announcement.get('Date', 'N/A')
            title = announcement.get('Title', 'N/A')
            self.stdout.write(f'    {i}. {date}: {title}')

    def analyze_news(self, news):
        """Analyze news data"""
        self.stdout.write(self.style.NOTICE('Analyzing news data...'))
        
        if not news:
            self.stdout.write(self.style.WARNING('No news available'))
            return
            
        # Check if news is a list and not empty
        if not isinstance(news, list):
            self.stdout.write(self.style.WARNING('News data is not a list'))
            return
            
        self.stdout.write(f'  Found {len(news)} news items')
        
        # Check for recent news (last 5)
        recent = news[:5] if len(news) >= 5 else news
        
        self.stdout.write('  Recent news:')
        for i, item in enumerate(recent, 1):
            date = item.get('NewsDate', 'N/A')
            headline = item.get('Headline', 'N/A')
            self.stdout.write(f'    {i}. {date}: {headline}')

    def analyze_indices(self, indices):
        """Analyze market indices data"""
        self.stdout.write(self.style.NOTICE('Analyzing market indices...'))
        
        if not indices:
            self.stdout.write(self.style.WARNING('No indices data available'))
            return
            
        if not isinstance(indices, list):
            self.stdout.write(self.style.WARNING('Indices data is not a list'))
            return
            
        self.stdout.write(f'  Found {len(indices)} indices')
        
        # Print main indices
        main_indices = ['KSE100', 'KSE30', 'KMI30', 'PSX']
        found_indices = []
        
        for idx in indices:
            index_name = idx.get('Symbol', '')
            if index_name in main_indices:
                found_indices.append(index_name)
                self.stdout.write(f'  {index_name}:')
                self.stdout.write(f'    Last: {idx.get("Last", "N/A")}')
                self.stdout.write(f'    Change: {idx.get("Change", "N/A")} ({idx.get("PctChange", "N/A")}%)')
        
        # Check which main indices are missing
        missing = [idx for idx in main_indices if idx not in found_indices]
        if missing:
            self.stdout.write(self.style.WARNING(f'  Missing important indices: {", ".join(missing)}'))

    def generate_summary_report(self, input_dir, symbol):
        """Generate a summary report of all data analysis"""
        self.stdout.write(self.style.NOTICE('Generating summary report...'))
        
        report = {
            'symbol': symbol,
            'analysis_date': self.get_current_datetime(),
            'data_completeness': {},
            'data_accuracy': {},
            'recommendations': []
        }
        
        # Check stock data completeness
        stock_data_file = os.path.join(input_dir, f'{symbol}_stock_data.json')
        latest_data_file = os.path.join(input_dir, f'{symbol}_latest.json')
        
        stock_data = self.load_json_file(stock_data_file)
        latest_data = self.load_json_file(latest_data_file) if os.path.exists(latest_data_file) else None
        
        report['data_completeness']['stock_data'] = {
            'available': stock_data is not None and len(stock_data) > 0,
            'count': len(stock_data) if stock_data else 0
        }
        
        report['data_completeness']['latest_data'] = {
            'available': latest_data is not None,
            'fields_present': list(latest_data.keys()) if latest_data else []
        }
        
        # Check other data completeness
        report['data_completeness']['announcements'] = {
            'available': os.path.exists(os.path.join(input_dir, f'{symbol}_announcements.json')),
            'count': len(self.load_json_file(os.path.join(input_dir, f'{symbol}_announcements.json'))) if os.path.exists(os.path.join(input_dir, f'{symbol}_announcements.json')) else 0
        }
        
        report['data_completeness']['news'] = {
            'available': os.path.exists(os.path.join(input_dir, 'news.json')),
            'count': len(self.load_json_file(os.path.join(input_dir, 'news.json'))) if os.path.exists(os.path.join(input_dir, 'news.json')) else 0
        }
        
        report['data_completeness']['indices'] = {
            'available': os.path.exists(os.path.join(input_dir, 'indices.json')),
            'count': len(self.load_json_file(os.path.join(input_dir, 'indices.json'))) if os.path.exists(os.path.join(input_dir, 'indices.json')) else 0
        }
        
        # Add recommendations based on findings
        if not report['data_completeness']['stock_data']['available']:
            report['recommendations'].append('Stock data is missing or empty. Check API connection and credentials.')
        
        if not report['data_completeness']['latest_data']['available']:
            report['recommendations'].append('Latest stock data is missing. Check if the API is returning the most recent values.')
        
        critical_fields = ['Symbol', 'Last', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume']
        if report['data_completeness']['latest_data']['available']:
            missing_fields = [field for field in critical_fields if field not in report['data_completeness']['latest_data']['fields_present']]
            if missing_fields:
                report['recommendations'].append(f'Critical fields are missing from the latest data: {", ".join(missing_fields)}')
        
        # Add general recommendations for data issues
        if report['data_completeness']['stock_data']['count'] < 30:
            report['recommendations'].append('Limited historical stock data available. Performance metrics may not be accurate.')
        
        # Save the report
        report_file = os.path.join(input_dir, f'{symbol}_data_analysis_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
            
        self.stdout.write(self.style.SUCCESS(f'Summary report saved to {report_file}'))
        
        # Print the recommendations
        if report['recommendations']:
            self.stdout.write(self.style.WARNING('Recommendations for improving data quality:'))
            for i, rec in enumerate(report['recommendations'], 1):
                self.stdout.write(f'  {i}. {rec}')
        else:
            self.stdout.write(self.style.SUCCESS('All data appears to be complete and accurate.'))

    def get_current_datetime(self):
        """Get current datetime as string"""
        from datetime import datetime
        return datetime.now().isoformat() 