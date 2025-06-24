import os
import json
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Tests API connections and stores data in JSON files for analysis'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, default='DGKC', help='Symbol to test')
        parser.add_argument('--output-dir', type=str, default='api_test_data', help='Directory to store test data')

    def handle(self, *args, **options):
        symbol = options['symbol']
        output_dir = options['output_dir']
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get authentication token
        self.stdout.write(self.style.NOTICE('Getting authentication token...'))
        token = self.get_token()
        
        if not token:
            self.stdout.write(self.style.ERROR('Failed to authenticate with API'))
            return
            
        self.stdout.write(self.style.SUCCESS('Successfully authenticated'))
        
        # Test APIs and save results
        self.test_stock_data(token, symbol, output_dir)
        self.test_news(token, output_dir)
        self.test_announcements(token, symbol, output_dir)
        self.test_indices(token, output_dir)
        
        self.stdout.write(self.style.SUCCESS(f'API tests completed. Results saved to {output_dir}/'))

    def get_token(self):
        """Get authentication token from API"""
        url = "https://api.mg-link.net/api/auth/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'password',
            'username': 'EKCapital2024',
            'password': '3KC@Pit@L!2024'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Authentication error: {str(e)}'))
            self.save_error('auth_error.json', str(e))
            return None

    def test_stock_data(self, token, symbol, output_dir):
        """Test stock data API and save results"""
        self.stdout.write(self.style.NOTICE(f'Testing stock data API for {symbol}...'))
        
        today = datetime.now().strftime('%Y-%m-%d')
        past_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Get stock prices data
        url = f"https://api.mg-link.net/api/Data1/PSXStockPrices?StartDate={past_date}&EndDate={today}"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Save all stock data
            self.save_to_file(os.path.join(output_dir, 'all_stocks.json'), data)
            
            # Filter for specific stock
            symbol_data = [item for item in data if item.get('Symbol') == symbol]
            self.save_to_file(os.path.join(output_dir, f'{symbol}_stock_data.json'), symbol_data)
            
            self.stdout.write(self.style.SUCCESS(f'Stock data saved for {symbol}'))
            
            # Save the latest data for the symbol
            if symbol_data:
                self.save_to_file(os.path.join(output_dir, f'{symbol}_latest.json'), symbol_data[-1])
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Stock data API error: {str(e)}'))
            self.save_error(os.path.join(output_dir, 'stock_data_error.json'), str(e))

    def test_news(self, token, output_dir):
        """Test news API and save results"""
        self.stdout.write(self.style.NOTICE('Testing news API...'))
        
        url = "https://api.mg-link.net/api/Data1/GetMGNews_New"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.save_to_file(os.path.join(output_dir, 'news.json'), data)
            self.stdout.write(self.style.SUCCESS('News data saved'))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'News API error: {str(e)}'))
            self.save_error(os.path.join(output_dir, 'news_error.json'), str(e))

    def test_announcements(self, token, symbol, output_dir):
        """Test announcements API and save results"""
        self.stdout.write(self.style.NOTICE('Testing announcements API...'))
        
        url = "https://api.mg-link.net/api/Data1/GetPSXAnnouncements"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Save all announcements
            self.save_to_file(os.path.join(output_dir, 'all_announcements.json'), data)
            
            # Filter announcements for the specific symbol
            filtered_announcements = [a for a in data if a.get('Symbol') == symbol]
            self.save_to_file(os.path.join(output_dir, f'{symbol}_announcements.json'), filtered_announcements)
            
            self.stdout.write(self.style.SUCCESS('Announcements data saved'))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Announcements API error: {str(e)}'))
            self.save_error(os.path.join(output_dir, 'announcements_error.json'), str(e))

    def test_indices(self, token, output_dir):
        """Test indices API and save results"""
        self.stdout.write(self.style.NOTICE('Testing indices API...'))
        
        url = "https://api.mg-link.net/api/Data1/GetPSXIndicesLive"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.save_to_file(os.path.join(output_dir, 'indices.json'), data)
            self.stdout.write(self.style.SUCCESS('Indices data saved'))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Indices API error: {str(e)}'))
            self.save_error(os.path.join(output_dir, 'indices_error.json'), str(e))

    def save_to_file(self, filepath, data):
        """Save data to a JSON file with proper formatting"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error saving to {filepath}: {str(e)}'))
            
    def save_error(self, filepath, error_message):
        """Save error information to a file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'error': error_message,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=4)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error saving error info to {filepath}: {str(e)}')) 