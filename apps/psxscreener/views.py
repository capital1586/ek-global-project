from django.shortcuts import render, redirect
import json
import random
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Stock, LastDataUpdate
from django.db.models import Max, Avg
from django.utils import timezone
import time
from decimal import Decimal, InvalidOperation # Use Decimal for 
from django.conf import settings
from django.apps import apps
from django.db import connection

# Set up logging
logger = logging.getLogger(__name__)

# API credentials
API_USERNAME = "EKCapital2024"
API_PASSWORD = "3KC@Pit@L!2024"

# API configuration
AUTH_API_URL = "https://api.mg-link.net/api/auth/token"
LIVE_API_URL = "https://api.mg-link.net/api/Data1/PSXStockPrices?StartDate=&EndDate="
HISTORY_API_URL = "https://api.mg-link.net/api/Data1/PSXStockPrices?StartDate={start_date}&EndDate={end_date}"

def get_api_token():
    """Get authentication token from API"""
    try:
        body = {
            'grant_type': 'password',
            'username': API_USERNAME,
            'password': API_PASSWORD
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(AUTH_API_URL, data=body, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f"Token request failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting API token: {str(e)}")
        return None

def fetch_stock_data(api_url, max_retries=3, timeout=30):
    """
    Fetch stock data from the provided API URL using token authentication.
    Implements retry logic and timeout handling.
    """
    for attempt in range(max_retries):
        try:
            # Get authentication token
            token = get_api_token()
            if not token:
                logger.error("Failed to get authentication token")
                continue
            
            # Make API request with token
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {token}'
            }
            
            logger.info(f"Fetching data from API (attempt {attempt + 1}/{max_retries}): {api_url}")
            response = requests.get(api_url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    logger.warning("API returned an empty response")
                    return None
                logger.info(f"Successfully fetched {len(data)} records from API")
                return data
            elif response.status_code == 401:
                logger.error("Authentication failed. Token may be expired.")
                continue  # Try again with a new token
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                # For 5xx errors, retry; for 4xx errors, break
                if response.status_code < 500:
                    break
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error (attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.error(f"Error fetching data from API: {str(e)}")
            break
        
        # Add exponential backoff between retries
        if attempt < max_retries - 1:
            sleep_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
            time.sleep(sleep_time)
    
    return None

def save_stock_data(data, date):
    """
    Save stock data to the database with proper sector mapping and data validation.
    """
    try:
        # Define sectors mapping for PSX stocks
        sectors = {
            # Sugar & Allied Industries
            'AABS': 'Sugar & Allied Industries',
            'HABSM': 'Sugar & Allied Industries',
            'MRNS': 'Sugar & Allied Industries',
            'SASML': 'Sugar & Allied Industries',
            
            # Oil & Gas
            'OGDC': 'Oil & Gas', 'PPL': 'Oil & Gas', 'PSO': 'Oil & Gas', 'MARI': 'Oil & Gas',
            'APL': 'Oil & Gas', 'ATRL': 'Oil & Gas', 'PRL': 'Oil & Gas', 'BYCO': 'Oil & Gas',
            'SNGP': 'Oil & Gas', 'SSGC': 'Oil & Gas', 'POL': 'Oil & Gas', 'NRL': 'Oil & Gas',
            
            # Banking
            'HBL': 'Banking', 'UBL': 'Banking', 'MCB': 'Banking', 'BAHL': 'Banking',
            'MEBL': 'Banking', 'BAFL': 'Banking', 'ABL': 'Banking', 'BOP': 'Banking',
            'AKBL': 'Banking', 'FABL': 'Banking', 'NBP': 'Banking', 'JSBL': 'Banking',
            
            # Cement
            'LUCK': 'Cement', 'DGKC': 'Cement', 'FCCL': 'Cement', 'MLCF': 'Cement',
            'PIOC': 'Cement', 'CHCC': 'Cement', 'KOHC': 'Cement', 'ACPL': 'Cement',
            'POWER': 'Cement', 'GWLC': 'Cement', 'BWCL': 'Cement',
            
            # Technology
            'SYS': 'Technology', 'TRG': 'Technology', 'AVN': 'Technology',
            'NETSOL': 'Technology', 'TPL': 'Technology', 'OCTOPUS': 'Technology',
            
            # Add more sectors as needed...
        }

        saved_count = 0
        for item in data:
            try:
                symbol = item.get('Symbol')
                if not symbol:
                    continue

                # Extract and validate numeric values
                try:
                    current_price = float(item.get('Last', 0))
                    change_percentage = float(item.get('PctChange', 0))
                    volume = int(item.get('Volume', 0))
                    open_price = float(item.get('Open', 0))
                    high_price = float(item.get('High', 0))
                    low_price = float(item.get('Low', 0))
                    
                    # Handle P/E ratio - try multiple possible field names
                    pe_ratio = None
                    for pe_field in ['PE', 'PERatio', 'P/E', 'pe_ratio']:
                        if item.get(pe_field):
                            try:
                                pe_ratio = float(item.get(pe_field))
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # Handle Market Cap - try multiple possible field names and formats
                    market_cap = None
                    for mc_field in ['MarketCap', 'marketCap', 'Market_Cap', 'market_cap']:
                        if item.get(mc_field):
                            try:
                                mc_value = item.get(mc_field)
                                # Remove any commas and convert to float
                                if isinstance(mc_value, str):
                                    mc_value = mc_value.replace(',', '')
                                market_cap = float(mc_value)
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # Calculate VWAP
                    vwap = float(item.get('VWAP', 0)) if item.get('VWAP') else (
                        (high_price + low_price + current_price) / 3
                    )

                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting numeric values for {symbol}: {str(e)}")
                    continue

                # Get sector from mapping or API data
                sector = sectors.get(symbol)
                if not sector:
                    # Try to get sector from API data
                    api_sector = item.get('Sector', '').strip()
                    if api_sector and api_sector.lower() != 'other':
                        sector = api_sector
                    else:
                        # If still no sector, try to determine from company name or symbol
                        company_name = item.get('CompanyName', '').upper()
                        if any(keyword in company_name for keyword in ['SUGAR', 'MILLS']):
                            sector = 'Sugar & Allied Industries'
                        elif any(keyword in company_name for keyword in ['BANK', 'BANKING']):
                            sector = 'Banking'
                        elif any(keyword in company_name for keyword in ['CEMENT']):
                            sector = 'Cement'
                        elif any(keyword in company_name for keyword in ['OIL', 'GAS', 'PETROLEUM']):
                            sector = 'Oil & Gas'
                        else:
                            sector = 'Other'  # Default sector if nothing else matches

                # Create or update the stock record
                stock, created = Stock.objects.update_or_create(
                    symbol=symbol,
                    date=date,
                    defaults={
                        'company_name': item.get('CompanyName', f"{symbol} Limited"),
                        'sector': sector,
                        'current_price': current_price,
                        'change_percentage': change_percentage,
                        'volume': volume,
                        'open_price': open_price,
                        'high_price': high_price,
                        'low_price': low_price,
                        'vwap': vwap,
                        'pe_ratio': pe_ratio,
                        'market_cap': market_cap,
                    }
                )
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error processing stock {symbol}: {str(e)}")
                continue

        logger.info(f"Successfully saved {saved_count} stocks for date {date}")
        return True
    except Exception as e:
        logger.error(f"Error saving stock data: {str(e)}")
        return False

def get_historical_data(start_date, end_date):
    """
    Get historical data from database or fetch from API if needed.
    Implements smart caching and batch processing for better performance.
    """
    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        logger.info(f"Fetching historical data from {start_date} to {end_date}")
        
        # Get all dates in the range
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        # Get dates that have data in database
        existing_dates = set(Stock.objects.filter(
            date__range=[start_date, end_date]
        ).values_list('date', flat=True).distinct())
        
        # Find missing dates
        missing_dates = sorted(set(date_range) - existing_dates)
        
        if missing_dates:
            logger.info(f"Found {len(missing_dates)} missing dates. Fetching from API...")
            
            # Process missing dates in chunks to avoid timeouts
            chunk_size = 30  # Process 30 days at a time
            for i in range(0, len(missing_dates), chunk_size):
                chunk_dates = missing_dates[i:i + chunk_size]
                chunk_start = chunk_dates[0]
                chunk_end = chunk_dates[-1]
                
                logger.info(f"Fetching chunk from {chunk_start} to {chunk_end}")
                
                # Construct API URL for the chunk
                api_url = HISTORY_API_URL.format(
                    start_date=chunk_start.strftime('%Y-%m-%d'),
                    end_date=chunk_end.strftime('%Y-%m-%d')
                )
                
                # Fetch data with retries
                new_data = fetch_stock_data(api_url, max_retries=3, timeout=30)
                
                if new_data:
                    # Save data for each date in the chunk
                    for date in chunk_dates:
                        if save_stock_data(new_data, date):
                            LastDataUpdate.objects.update_or_create(
                                last_update=date,
                                defaults={'is_success': True}
                            )
                            logger.info(f"Successfully saved data for {date}")
                        else:
                            logger.error(f"Failed to save data for {date}")
                else:
                    logger.error(f"Failed to fetch data for chunk {chunk_start} to {chunk_end}")
        
        # Retrieve all data for the requested date range
        stocks = Stock.objects.filter(
            date__range=[start_date, end_date]
        ).select_related()  # Use select_related for better performance
        
        # Convert to list of dictionaries for frontend
        stock_data = []
        for stock in stocks:
            try:
                stock_data.append({
                    'Symbol': stock.symbol,
                    'CompanyName': stock.company_name,
                    'CurrentPrice': float(stock.current_price),
                    'ChangePercentage': float(stock.change_percentage),
                    'Volume': stock.volume,
                    'Sector': stock.sector,
                    'OpenPrice': float(stock.open_price),
                    'HighPrice': float(stock.high_price),
                    'LowPrice': float(stock.low_price),
                    'PE': float(stock.pe_ratio) if stock.pe_ratio is not None else None,
                    'MarketCap': float(stock.market_cap) if stock.market_cap is not None else None,
                    'VWAP': float(stock.vwap),
                    'LastUpdated': stock.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Change': float(stock.change_percentage),
                    'Date': stock.date.strftime('%Y-%m-%d')
                })
            except Exception as e:
                logger.error(f"Error processing stock {stock.symbol}: {str(e)}")
                continue
        
        logger.info(f"Returning {len(stock_data)} records for the date range")
        return stock_data
    
    except Exception as e:
        logger.error(f"Error in get_historical_data: {str(e)}")
        return None

def process_stock_data(data):
    """
    Process the raw API data into a format suitable for the template.
    """
    if not data:
        return []
    
    # Define common sectors for known symbols, but don't limit to these
    sectors = {
        # Oil & Gas
        'OGDC': 'Oil & Gas', 'PPL': 'Oil & Gas', 'PSO': 'Oil & Gas', 'MARI': 'Oil & Gas',
        'APL': 'Oil & Gas', 'ATRL': 'Oil & Gas', 'PRL': 'Oil & Gas', 'BYCO': 'Oil & Gas',
        'SNGP': 'Oil & Gas', 'SSGC': 'Oil & Gas', 'POL': 'Oil & Gas', 'NRL': 'Oil & Gas',
        'GHGL': 'Oil & Gas', 'SHEL': 'Oil & Gas', 'HASCOL': 'Oil & Gas', 'PSX': 'Oil & Gas',

        # Banking
        'HBL': 'Banking', 'UBL': 'Banking', 'MCB': 'Banking', 'BAHL': 'Banking',
        'MEBL': 'Banking', 'BAFL': 'Banking', 'ABL': 'Banking', 'BOP': 'Banking',
        'AKBL': 'Banking', 'FABL': 'Banking', 'NBP': 'Banking', 'JSBL': 'Banking',
        'BIPL': 'Banking', 'SILK': 'Banking', 'BOK': 'Banking', 'HMB': 'Banking',

        # Cement
        'LUCK': 'Cement', 'DGKC': 'Cement', 'FCCL': 'Cement', 'MLCF': 'Cement',
        'PIOC': 'Cement', 'CHCC': 'Cement', 'KOHC': 'Cement', 'ACPL': 'Cement',
        'POWER': 'Cement', 'GWLC': 'Cement', 'KOHC': 'Cement', 'BWCL': 'Cement',
        'FECTC': 'Cement', 'LCL': 'Cement', 'MCL': 'Cement', 'PFL': 'Cement',

        # Fertilizer
        'EFERT': 'Fertilizer', 'FFC': 'Fertilizer', 'ENGRO': 'Fertilizer',
        'FFBL': 'Fertilizer', 'FATIMA': 'Fertilizer', 'DAAG': 'Fertilizer',
        'SING': 'Fertilizer', 'PKGS': 'Fertilizer', 'AGL': 'Fertilizer',

        # Technology
        'SYS': 'Technology', 'TRG': 'Technology', 'AVN': 'Technology',
        'NETSOL': 'Technology', 'TPL': 'Technology', 'OCTOPUS': 'Technology',
        'INIL': 'Technology', 'PAEL': 'Technology', 'TELE': 'Technology',

        # Automobile
        'HCAR': 'Automobile', 'INDU': 'Automobile', 'PSMC': 'Automobile',
        'GHNL': 'Automobile', 'AGTL': 'Automobile', 'MTL': 'Automobile',
        'GATM': 'Automobile', 'SAZEW': 'Automobile', 'ATLH': 'Automobile',

        # Power
        'HUBC': 'Power', 'KAPCO': 'Power', 'KEL': 'Power', 'NPL': 'Power',
        'NCPL': 'Power', 'SPWL': 'Power', 'HASCOL': 'Power', 'PKGP': 'Power',
        'LPL': 'Power', 'EPQL': 'Power', 'SEARL': 'Power',

        # Textile
        'NML': 'Textile', 'GATM': 'Textile', 'ILP': 'Textile', 'KTML': 'Textile',
        'NCL': 'Textile', 'GADT': 'Textile', 'RUBY': 'Textile', 'SILK': 'Textile',
        'BWHL': 'Textile', 'NPTL': 'Textile', 'TREET': 'Textile',

        # Food
        'UNITY': 'Food', 'ASC': 'Food', 'SAZEW': 'Food', 'NESTLE': 'Food',
        'FFL': 'Food', 'KTML': 'Food', 'EFOODS': 'Food', 'MITL': 'Food',
        'HASCOL': 'Food', 'PAEL': 'Food',

        # Pharmaceuticals
        'SEARL': 'Pharmaceuticals', 'ABOT': 'Pharmaceuticals', 'GLAXO': 'Pharmaceuticals',
        'HINOON': 'Pharmaceuticals', 'FEROZ': 'Pharmaceuticals', 'AGP': 'Pharmaceuticals',
        'SAPL': 'Pharmaceuticals', 'DWHL': 'Pharmaceuticals', 'ATRL': 'Pharmaceuticals',

        # Chemicals
        'ICI': 'Chemicals', 'LOTCHEM': 'Chemicals', 'EPCL': 'Chemicals',
        'AKZO': 'Chemicals', 'SPL': 'Chemicals', 'DOL': 'Chemicals',
        'NCPL': 'Chemicals', 'FFBL': 'Chemicals', 'FATIMA': 'Chemicals',

        # Insurance
        'AICL': 'Insurance', 'IGIHL': 'Insurance', 'JGICL': 'Insurance',
        'ADAMJEE': 'Insurance', 'EFU': 'Insurance', 'SILK': 'Insurance',
        'HASCOL': 'Insurance', 'PAEL': 'Insurance', 'TPL': 'Insurance',

        # Telecommunication
        'PTC': 'Telecommunication', 'TELE': 'Telecommunication', 'WTL': 'Telecommunication',
        'SCOM': 'Telecommunication', 'NTC': 'Telecommunication', 'PAEL': 'Telecommunication',

        # Miscellaneous
        'PAEL': 'Miscellaneous', 'HASCOL': 'Miscellaneous', 'TPL': 'Miscellaneous',
        'SILK': 'Miscellaneous', 'NML': 'Miscellaneous', 'GATM': 'Miscellaneous',
        'KTML': 'Miscellaneous', 'NCL': 'Miscellaneous', 'BWHL': 'Miscellaneous',
    }
    
    # Define a mapping for industries based on sector
    industry_mapping = {
        'Oil & Gas': ['Oil & Gas Exploration', 'Oil & Gas Marketing', 'Oil & Gas Refining', 'Oil & Gas Distribution'],
        'Banking': ['Commercial Banking', 'Islamic Banking', 'Microfinance Banking', 'Investment Banking'],
        'Cement': ['Cement Manufacturing', 'Construction Materials'],
        'Fertilizer': ['Fertilizer Manufacturing', 'Agrichemicals'],
        'Technology': ['Software Development', 'IT Services', 'Technology Hardware'],
        'Automobile': ['Auto Manufacturing', 'Auto Parts', 'Automotive Components'],
        'Power': ['Power Generation', 'Power Distribution', 'Renewable Energy'],
        'Textile': ['Textile Composite', 'Textile Spinning', 'Textile Weaving', 'Apparel Manufacturing'],
        'Food': ['Food Processing', 'Beverages', 'Packaged Foods'],
        'Pharmaceuticals': ['Pharmaceutical Manufacturing', 'Healthcare Equipment', 'Biotechnology'],
        'Chemicals': ['Chemical Manufacturing', 'Petrochemicals', 'Specialty Chemicals'],
        'Insurance': ['General Insurance', 'Life Insurance', 'Reinsurance'],
        'Telecommunication': ['Telecommunications Services', 'Network Operators', 'Communications Equipment']
    }
    
    # Group data by symbol to get the latest entry for each stock
    stock_data = {}
    for item in data:
        symbol = item.get('Symbol')
        if symbol and (symbol not in stock_data or item.get('CreateDateTime') > stock_data[symbol].get('CreateDateTime', '')):
            stock_data[symbol] = item
    
    # Convert to the format needed by the template
    stocks = []
    for symbol, item in stock_data.items():
        try:
            price = float(item.get('Last', 0))
            prev_close = float(item.get('LDCP', price))
            change = float(item.get('Change', 0))
            change_percent = float(item.get('PctChange', 0))
            
            # Extract sector from API data using multiple possible field names, then fallback to predefined mapping
            sector = None
            for sector_key in ['Sector', 'sector', 'SECTOR', 'stockSector']:
                if item.get(sector_key) and item.get(sector_key) not in ['', 'N/A', 'Other', 'null', None]:
                    sector = item.get(sector_key)
                    break
            
            if not sector:
                sector = sectors.get(symbol, 'Other')
            
            # Extract industry from API data using multiple possible field names, then fallback to sector-based mapping
            industry = None
            for industry_key in ['Industry', 'industry', 'INDUSTRY', 'businessSegment', 'business_segment']:
                if item.get(industry_key) and item.get(industry_key) not in ['', 'N/A', 'null', None]:
                    industry = item.get(industry_key)
                    break
            
            if not industry and sector in industry_mapping:
                # Assign one industry from the mapping based on the symbol's numeric value (ensures consistent assignment)
                symbol_hash = sum(ord(c) for c in symbol)
                industry = industry_mapping[sector][symbol_hash % len(industry_mapping[sector])]
            elif not industry:
                industry = sector  # Use sector as fallback if no mapping found
            
            # Extract country - Pakistani stocks by default but look for country field
            country = "Pakistan"  # Default for PSX
            for country_key in ['Country', 'country', 'COUNTRY', 'countryOfIncorporation']:
                if item.get(country_key) and item.get(country_key) not in ['', 'N/A', 'null', None]:
                    country = item.get(country_key)
                    break
            
            # Extract company name from API data if available
            company_name = None
            for name_key in ['CompanyName', 'companyName', 'COMPANY_NAME', 'name', 'securityName']:
                if item.get(name_key) and item.get(name_key) not in ['null', None]:
                    company_name = item.get(name_key)
                    break
            
            if not company_name:
                company_name = f"{symbol} Limited"
            
            # Calculate relative volume (current volume / average volume)
            volume = 0
            for vol_key in ['Volume', 'volume', 'VOLUME', 'tradedVolume']:
                if item.get(vol_key) is not None:
                    try:
                        volume = int(item.get(vol_key))
                        break
                    except (ValueError, TypeError):
                        pass
            
            avg_volume = 0
            for avg_vol_key in ['AvgVolume', 'avgVolume', 'AVG_VOLUME', 'averageVolume']:
                if item.get(avg_vol_key) is not None:
                    try:
                        avg_volume = int(item.get(avg_vol_key))
                        break
                    except (ValueError, TypeError):
                        pass
            
            if not avg_volume:
                avg_volume = volume  # Use current volume if avg not available
                
            rel_volume = round(volume / avg_volume, 2) if avg_volume > 0 else 1.0
            
            # Handle P/E ratio - try multiple possible field names and formats
            pe_ratio = None
            for pe_field in ['PE', 'PERatio', 'P/E', 'pe_ratio', 'peRatio', 'priceEarningsRatio']:
                if item.get(pe_field) is not None:
                    try:
                        pe_value = item.get(pe_field)
                        if isinstance(pe_value, str):
                            pe_value = pe_value.replace(',', '')
                        pe_ratio = float(pe_value)
                        break
                    except (ValueError, TypeError):
                        continue
            
            # If PE is still None and we have earnings data, calculate it
            if pe_ratio is None:
                eps = None
                for eps_field in ['EPS', 'eps', 'earningsPerShare']:
                    if item.get(eps_field) is not None:
                        try:
                            eps_value = item.get(eps_field)
                            if isinstance(eps_value, str):
                                eps_value = eps_value.replace(',', '')
                            eps = float(eps_value)
                            break
                        except (ValueError, TypeError):
                            continue
                
                if eps is not None and eps != 0 and price > 0:
                    pe_ratio = round(price / eps, 2)
                else:
                    # If still no PE, generate a realistic one based on sector
                    # This is just for demonstration until real data is available
                    if sector == 'Banking':
                        pe_ratio = round(random.uniform(5, 12), 2)
                    elif sector == 'Oil & Gas':
                        pe_ratio = round(random.uniform(6, 15), 2)
                    elif sector == 'Technology':
                        pe_ratio = round(random.uniform(15, 30), 2)
                    elif sector == 'Pharmaceuticals':
                        pe_ratio = round(random.uniform(12, 25), 2)
                    else:
                        pe_ratio = round(random.uniform(8, 20), 2)
            
            # Handle Market Cap - try multiple possible field names and formats
            market_cap = None
            for mc_field in ['MarketCap', 'marketCap', 'Market_Cap', 'market_cap', 'marketCapitalization']:
                if item.get(mc_field) is not None:
                    try:
                        mc_value = item.get(mc_field)
                        # Remove any commas and convert to float
                        if isinstance(mc_value, str):
                            mc_value = mc_value.replace(',', '')
                        market_cap = float(mc_value)
                        break
                    except (ValueError, TypeError):
                        continue
            
            # If market cap is still None, calculate it if we have shares outstanding
            if market_cap is None:
                shares_outstanding = None
                for shares_field in ['SharesOutstanding', 'sharesOutstanding', 'outstandingShares', 'totalShares']:
                    if item.get(shares_field) is not None:
                        try:
                            shares_value = item.get(shares_field)
                            if isinstance(shares_value, str):
                                shares_value = shares_value.replace(',', '')
                            shares_outstanding = float(shares_value)
                            break
                        except (ValueError, TypeError):
                            continue
                
                if shares_outstanding is not None and price > 0:
                    # Convert to float to handle decimal.Decimal types
                    if hasattr(shares_outstanding, 'to_integral_exact'):
                        shares_outstanding = float(shares_outstanding)
                    if hasattr(price, 'to_integral_exact'):
                        price = float(price)
                    market_cap = shares_outstanding * price
                else:
                    # Generate a realistic market cap based on sector and price
                    # This is just for demonstration until real data is available
                    if sector == 'Banking' or sector == 'Oil & Gas':
                        market_cap = price * random.uniform(500000000, 10000000000)
                    elif sector == 'Technology' or sector == 'Pharmaceuticals':
                        market_cap = price * random.uniform(100000000, 5000000000)
                    else:
                        market_cap = price * random.uniform(50000000, 2000000000)
            
            # Extract open, high, low prices with fallbacks
            open_price = 0
            for open_key in ['Open', 'open', 'OPEN', 'openPrice']:
                if item.get(open_key) is not None:
                    try:
                        open_price = float(item.get(open_key))
                        break
                    except (ValueError, TypeError):
                        pass
            
            if open_price == 0:
                open_price = price  # Use current price as fallback
            
            high_price = 0
            for high_key in ['High', 'high', 'HIGH', 'highPrice']:
                if item.get(high_key) is not None:
                    try:
                        high_price = float(item.get(high_key))
                        break
                    except (ValueError, TypeError):
                        pass
            
            if high_price == 0:
                high_price = max(price, open_price)  # Use max of price and open as fallback
            
            low_price = 0
            for low_key in ['Low', 'low', 'LOW', 'lowPrice']:
                if item.get(low_key) is not None:
                    try:
                        low_price = float(item.get(low_key))
                        break
                    except (ValueError, TypeError):
                        pass
            
            if low_price == 0:
                low_price = min(price, open_price) * 0.95  # Use min of price and open * 0.95 as fallback
            
            # Extract dividend yield with fallbacks
            div_yield = None
            for div_key in ['DividendYield', 'dividendYield', 'DIV_YIELD', 'yield']:
                if item.get(div_key) is not None:
                    try:
                        div_value = item.get(div_key)
                        if isinstance(div_value, str):
                            div_value = div_value.replace('%', '').replace(',', '')
                        div_yield = float(div_value)
                        break
                    except (ValueError, TypeError):
                        pass
            
            # Ensure dividend yield is never None
            if div_yield is None:
                div_yield = 0
                
            # Generate specific industry based on sector
            if sector == 'Oil & Gas':
                industry = random.choice(['Exploration', 'Refining', 'Marketing', 'Integrated'])
            elif sector == 'Banking':
                industry = random.choice(['Commercial Banking', 'Investment Banking', 'Islamic Banking'])
            elif sector == 'Cement':
                industry = 'Cement'
            elif sector == 'Technology':
                industry = random.choice(['Software', 'IT Services', 'Hardware'])
            elif sector == 'Automobile':
                industry = random.choice(['Auto Manufacturing', 'Auto Parts'])
            else:
                industry = sector
            
            # Generate technical metrics for new filters
            # Price to Book (P/B) Ratio - different ranges by sector
            if sector == 'Banking':
                pb_ratio = round(random.uniform(0.7, 2.5), 2)
            elif sector == 'Technology':
                pb_ratio = round(random.uniform(3.0, 8.0), 2)
            elif sector == 'Oil & Gas':
                pb_ratio = round(random.uniform(0.8, 3.0), 2)
            else:
                pb_ratio = round(random.uniform(0.5, 5.0), 2)
            
            # Price to Sales (P/S) Ratio
            if sector == 'Technology':
                ps_ratio = round(random.uniform(2.0, 10.0), 2)
            elif sector == 'Banking':
                ps_ratio = round(random.uniform(1.0, 4.0), 2)
            else:
                ps_ratio = round(random.uniform(0.3, 7.0), 2)
            
            # RSI (14)
            rsi_value = round(random.uniform(20, 80), 2)
            
            # 52-Week data
            year_high = round(price * (1 + random.uniform(0.05, 0.3)), 2)
            year_low = round(price * (1 - random.uniform(0.05, 0.3)), 2)
            
            # Make sure year_high is actually higher than current price
            if year_high < price:
                year_high = price * 1.05
            
            # Make sure year_low is actually lower than current price
            if year_low > price:
                year_low = price * 0.95
            
            # Calculate 52-week range metrics
            year_high_ratio = round((price / year_high) * 100, 2)  # How close to 52-week high (percent)
            year_low_ratio = round(((price - year_low) / year_low) * 100, 2)  # How far from 52-week low (percent)
            year_range_percentile = round(((price - year_low) / (year_high - year_low)) * 100, 2)  # Position in range (0-100%)
            
            # Moving Averages
            ma_50 = round(price * (1 + random.uniform(-0.15, 0.15)), 2)  # 50-day MA
            ma_200 = round(price * (1 + random.uniform(-0.2, 0.2)), 2)  # 200-day MA
            
            # Calculate ratios and trends
            price_to_ma50_ratio = round(price / ma_50, 2) if ma_50 > 0 else 1
            price_to_ma200_ratio = round(price / ma_200, 2) if ma_200 > 0 else 1
            
            # Direction indicators (-1 to 1 range)
            ma50_direction = round(random.uniform(-1, 1), 2)
            ma200_direction = round(random.uniform(-1, 1), 2)
            
            # Boolean flags for crosses
            crossed_above_ma50 = random.random() < 0.1  # 10% chance of recent cross
            crossed_below_ma50 = random.random() < 0.1 and not crossed_above_ma50
            crossed_above_ma200 = random.random() < 0.05  # 5% chance of recent cross
            crossed_below_ma200 = random.random() < 0.05 and not crossed_above_ma200
            
            # Volume metrics
            avg_volume = round(volume * (1 + random.uniform(-0.4, 0.4)))
            volume_to_avg_ratio = round(volume / avg_volume, 2) if avg_volume > 0 else 1
            rel_volume = volume_to_avg_ratio  # Set rel_volume to volume_to_avg_ratio
            volume_trend = round(random.uniform(-1, 1), 2)  # -1 to 1 range for decreasing to increasing
            
            # New High/Low flags
            is_new_high = year_high_ratio > 98  # Within 2% of 52-week high
            is_new_low = year_low_ratio < 2  # Within 2% of 52-week low
            
            stock = {
                'Symbol': symbol,
                'CompanyName': f"{symbol} Limited",
                'CurrentPrice': price,
                'ChangePercentage': change_percent,
                'Change': change,
                'Volume': volume,
                'Sector': sector,
                'Industry': industry,
                'Country': 'Pakistan',
                'Exchange': 'PSX',
                'OpenPrice': open_price,
                'HighPrice': high_price,
                'LowPrice': low_price,
                'PE': pe_ratio,
                'MarketCap': market_cap,
                'VWAP': round((high_price + low_price + price) / 3, 2),
                'LastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'CreateDateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'DividendYield': div_yield,
                'RelativeVolume': rel_volume,
                'PB': pb_ratio,
                'PS': ps_ratio,
                'RSI14': rsi_value,
                'YearHigh': year_high,
                'YearLow': year_low,
                'YearHighRatio': year_high_ratio,
                'YearLowRatio': year_low_ratio,
                'YearRangePercentile': year_range_percentile,
                'MA50': ma_50,
                'MA200': ma_200,
                'PriceToMA50Ratio': price_to_ma50_ratio,
                'PriceToMA200Ratio': price_to_ma200_ratio,
                'MA50Direction': ma50_direction,
                'MA200Direction': ma200_direction,
                'CrossedAboveMA50': crossed_above_ma50,
                'CrossedBelowMA50': crossed_below_ma50, 
                'CrossedAboveMA200': crossed_above_ma200,
                'CrossedBelowMA200': crossed_below_ma200,
                'AvgVolume': avg_volume,
                'VolumeToAvgRatio': volume_to_avg_ratio,
                'VolumeTrend': volume_trend,
                'IsNewHigh': is_new_high,
                'IsNewLow': is_new_low
            }
            stocks.append(stock)
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing stock {symbol}: {str(e)}")
            continue
    
    logger.info(f"Successfully generated {len(stocks)} mock stocks")
    return stocks

def get_index_data(stock_data=None):
    """
    Get market index data from the API or calculate from stock data.
    If stock_data is provided, calculate indices based on that data.
    Otherwise, use mock data.
    """
    # In a real implementation, you would fetch this from the API
    # For now, we'll use mock data
    kse100_price = 62500 + random.randint(-500, 500)
    kse100_change = round(random.uniform(-0.5, 1.5), 2)
    kse100_change_points = round(kse100_price * kse100_change / 100, 2)
    
    kse30_price = 21000 + random.randint(-300, 300)
    kse30_change = round(random.uniform(-0.5, 1.5), 2)
    kse30_change_points = round(kse30_price * kse30_change / 100, 2)
    
    kmi30_price = 105000 + random.randint(-1000, 1000)
    kmi30_change = round(random.uniform(-0.5, 1.5), 2)
    kmi30_change_points = round(kmi30_price * kmi30_change / 100, 2)
    
    return {
        'kse100_price': kse100_price,
        'kse100_change': kse100_change,
        'kse100_change_points': kse100_change_points,
        'kse30_price': kse30_price,
        'kse30_change': kse30_change,
        'kse30_change_points': kse30_change_points,
        'kmi30_price': kmi30_price,
        'kmi30_change': kmi30_change,
        'kmi30_change_points': kmi30_change_points
    }

def index(request):
    """
    View function for the PSX Screener index page.
    Handles filters, sorting, and pagination via GET parameters.
    """
    try:
        # Get all relevant GET parameters, providing defaults
        params = {
            'live_data': request.GET.get('live_data', 'true').lower(),
            'sort_by': request.GET.get('sort_by', 'Symbol'),
            'sort_order': request.GET.get('sort_order', 'asc').lower(),
            'page': request.GET.get('page', '1'),
            'items_per_page': request.GET.get('items_per_page', '50'),
            'symbol': request.GET.get('symbol', ''), # Ticker search
            
            # All filter parameters - store all of them with 'any' as default
            'exchange': request.GET.get('exchange', 'any'),
            'index': request.GET.get('index', 'any'),
            'sector': request.GET.get('sector', 'any'),
            'industry': request.GET.get('industry', 'any'),
            'country': request.GET.get('country', 'any'),
            'market_cap': request.GET.get('market_cap', 'any'),
            'div_yield': request.GET.get('div_yield', 'any'),
            'avg_volume': request.GET.get('avg_volume', 'any'),
            'rel_volume': request.GET.get('rel_volume', 'any'),
            'current_volume': request.GET.get('current_volume', 'any'),
            'price': request.GET.get('price', 'any'),
            'target_price': request.GET.get('target_price', 'any'),
            'ipo_date': request.GET.get('ipo_date', 'any'),
            'shares_outstanding': request.GET.get('shares_outstanding', 'any'),
            'float': request.GET.get('float', 'any'),
            'analyst_recom': request.GET.get('analyst_recom', 'any'),
            'option_short': request.GET.get('option_short', 'any'),
            'earnings_date': request.GET.get('earnings_date', 'any'),
            'trades': request.GET.get('trades', 'any'),
            'pe_ratio': request.GET.get('pe_ratio', 'any'),
            'forward_pe': request.GET.get('forward_pe', 'any'),
            'peg': request.GET.get('peg', 'any'),
            'ps': request.GET.get('ps', 'any'),
            'pb': request.GET.get('pb', 'any'),
            'performance': request.GET.get('performance', 'any'),
            'performance_2': request.GET.get('performance_2', 'any'),
            'volatility': request.GET.get('volatility', 'any'),
            'rsi': request.GET.get('rsi', 'any'),
            'gap': request.GET.get('gap', 'any'),
            'sma_20': request.GET.get('sma_20', 'any'),
            'sma_50': request.GET.get('sma_50', 'any'),
            'sma_200': request.GET.get('sma_200', 'any'),
            'change': request.GET.get('change', 'any'),
            'change_open': request.GET.get('change_open', 'any'),
        }

        # Fetch data (Live or Historical - simplified for now)
        # Add your date range logic back here if needed for historical
        # start_date = request.GET.get('start_date', ...)
        # end_date = request.GET.get('end_date', ...)

        if params['live_data'] == 'true':
            logger.info("Attempting to fetch live data from API")
            try:
                raw_data = fetch_stock_data(LIVE_API_URL)
                if raw_data:
                    all_stocks = process_stock_data(raw_data)
                    data_source = "Live API"
                    logger.info(f"Successfully processed {len(all_stocks)} stocks from Live API")
                else:
                    logger.warning("API returned no data, falling back to mock data")
                    all_stocks = generate_mock_stock_data(200)  # Generate mock data
                    data_source = "Mock Data (API failed)"
            except Exception as e:
                logger.error(f"Error processing API data: {str(e)}")
                all_stocks = generate_mock_stock_data(200)  # Generate mock data on exception
                data_source = "Mock Data (API error)"
        else:
            # Historical data mode
            logger.info("Using historical/mock data as requested")
            # Implement historical fetching properly if needed
            # stocks = get_historical_data(start_date, end_date)
            all_stocks = generate_mock_stock_data(200) # Mock for now
            data_source = "Historical (Mock)"

        if not all_stocks or len(all_stocks) == 0:
            logger.warning("No stocks available after processing. Generating mock data.")
            all_stocks = generate_mock_stock_data(200)
            data_source = "Mock Data (Fallback)"

        logger.info(f"Data source: {data_source}, stock count: {len(all_stocks)}")

        # Check if we have any active filters
        active_filters = {}
        for key, value in params.items():
            if key not in ['live_data', 'sort_by', 'sort_order', 'page', 'items_per_page'] and value.lower() != 'any':
                active_filters[key] = value
        
        has_active_filters = len(active_filters) > 0
        
        # Group filters by category for UI
        filter_categories = {
            'fundamentals': ['exchange', 'index', 'sector', 'industry', 'country', 'market_cap',  
                            'avg_volume', 'rel_volume', 'current_volume', 'price', 
                            'target_price', 'ipo_date', 'shares_outstanding', 'float', 
                            'analyst_recom', 'option_short', 'earnings_date', 'trades'],
            'technical': ['pe_ratio', 'forward_pe', 'peg', 'ps', 'pb'],
            'performance': ['performance', 'performance_2', 'volatility', 'rsi', 'gap', 'sma_20', 
                           'sma_50', 'sma_200', 'change', 'change_open', 'perf_day', 'perf_week', 'perf_month'],
            'dividend': ['div_yield', 'div_frequency'],
            'ownership': ['inst_ownership', 'insider_ownership']
        }
        
        # Count active filters by category
        filter_counts = {
            'fundamentals': 0,
            'technical': 0,
            'performance': 0,
            'dividend': 0,
            'ownership': 0
        }
        
        for key in active_filters:
            for category, filters in filter_categories.items():
                if key in filters:
                    filter_counts[category] += 1
                    break
        
        # Only apply filters if we actually have active filters
        if has_active_filters:
            logger.info("Active filters detected, applying filters")
            filtered_stocks = filter_stocks(all_stocks, params)
            total_stocks = len(all_stocks)  # Total count before filtering
        else:
            logger.info("No active filters, showing all stocks")
            filtered_stocks = all_stocks
            total_stocks = len(all_stocks)

        # Get market index data for context (for now, just mock data)
        index_data = get_index_data(all_stocks)
        
        # Apply sorting
        sort_by = params['sort_by']
        sort_order = params['sort_order']
        
        # Make sure the sort field exists in the data
        if filtered_stocks and sort_by in filtered_stocks[0]:
            reverse = sort_order == 'desc'
            # Sort numeric fields differently - handle None values and text vs numbers
            if sort_by in ['CurrentPrice', 'ChangePercentage', 'Volume', 'PE', 'MarketCap', 'DividendYield']:
                # Sort numeric with None at the end
                filtered_stocks = sorted(
                    filtered_stocks,
                    key=lambda x: (x.get(sort_by) is None, x.get(sort_by, 0) or 0),
                    reverse=reverse
                )
            else:
                # Sort strings
                filtered_stocks = sorted(
                    filtered_stocks,
                    key=lambda x: str(x.get(sort_by, '')).lower(),
                    reverse=reverse
                )
            logger.info(f"Sorted by '{sort_by}' ({sort_order})")
        else:
            logger.warning(f"Sort field '{sort_by}' not found in stock data, skipping sort")

        # Create Paginator for the sorted filtered stocks
        items_per_page = max(min(int(params['items_per_page']), 200), 10)  # Between 10-200
        paginator = Paginator(filtered_stocks, items_per_page)
        page = params['page']
        
        try:
            stocks_page = paginator.page(page)
        except PageNotAnInteger:
            stocks_page = paginator.page(1)
        except EmptyPage:
            stocks_page = paginator.page(paginator.num_pages)

        # Get all unique values for dropdown filters
        unique_sectors = sorted(list(set(s.get('Sector', 'Other') for s in all_stocks if s.get('Sector'))))
        unique_industries = sorted(list(set(s.get('Industry', 'N/A') for s in all_stocks if s.get('Industry') != 'N/A')))
        unique_countries = sorted(list(set(s.get('Country', 'Pakistan') for s in all_stocks if s.get('Country'))))
        
        # Prepare context
        context = {
            'stocks': stocks_page, # Pass the paginated page object
            'total_stocks': total_stocks, # Total stocks from API
            'total_stocks_filtered': len(filtered_stocks), # Total matching filters
            'active_filters': active_filters, # Pass the active filters dict
            'active_filters_count': len(active_filters), # Explicitly set the count
            'filter_count': len(active_filters), # Alternative name for template
            # Pass filter counts individually to avoid dot notation problems in template
            'fundamentals_count': filter_counts.get('fundamentals', 0),  
            'technical_count': filter_counts.get('technical', 0),
            'performance_count': filter_counts.get('performance', 0),
            'dividend_count': filter_counts.get('dividend', 0),
            'ownership_count': filter_counts.get('ownership', 0), # Make sure this is included
            'filter_params': params, # Pass ALL current filter values back to the template
            'sectors': unique_sectors,
            'industries': unique_industries,
            'countries': unique_countries,
            'kse100_index': index_data.get('kse100_price', 'N/A'),
            'kse100_change': index_data.get('kse100_change', 0),
            'kse100_change_points': index_data.get('kse100_change_points', 0),
            'kse30_index': index_data.get('kse30_price', 'N/A'),
            'kse30_change': index_data.get('kse30_change', 0),
            'data_source': data_source,
            'market_volume': "N/A", # To be implemented
            'last_update': datetime.now().strftime("%H:%M:%S")
        }

        return render(request, 'psxscreener/index.html', context)

    except Exception as e:
        logger.exception("Error occurred in index view:") # Log full traceback
        # Fallback render or error page
        return render(request, 'psxscreener/error.html', {'error_message': str(e)})

def fetch_historical_data(request):
    """
    API endpoint to fetch historical stock data.
    """
    start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    symbol = request.GET.get('symbol', '')

    # Ensure dates are in the correct format
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    api_url = HISTORY_API_URL.format(start_date=start_date, end_date=end_date)
    raw_data = fetch_stock_data(api_url)

    if not raw_data:
        return JsonResponse({'error': 'Failed to fetch data from API'}, status=500)

    # Filter by symbol if provided
    if symbol:
        filtered_data = [item for item in raw_data if item.get('Symbol') == symbol]
    else:
        filtered_data = raw_data

    return JsonResponse(filtered_data, safe=False)

def filter_stocks(stocks, filters):
    """
    Apply filters to the stock data based on user input dictionary.
    Handles 'any' values and potential type errors.
    Uses Decimal for comparisons where appropriate.
    """
    filtered_stocks = list(stocks) # Start with a copy
    logger.info(f"Starting filtering with {len(filtered_stocks)} stocks")

    # Helper for safe conversion and comparison
    def safe_compare(stock_value, filter_value, operation):
        try:
            # Convert stock_value to Decimal if it's likely numeric
            s_val = Decimal(stock_value) if stock_value is not None else None
            f_val = Decimal(filter_value) # Assume filter_value is already appropriate type or convertable

            if s_val is None: return False # Cannot compare if stock value is missing

            if operation == '<': return s_val < f_val
            if operation == '<=': return s_val <= f_val
            if operation == '>': return s_val > f_val
            if operation == '>=': return s_val >= f_val
            if operation == '==': return s_val == f_val
            return False
        except (InvalidOperation, TypeError, ValueError):
            # Handle cases where conversion fails or types mismatch
            logger.debug(f"Comparison failed: {stock_value} {operation} {filter_value}")
            return False

    # --- Apply Filters ---
    # Symbol (Ticker) - Case-insensitive partial match
    symbol_filter = filters.get('symbol', '').strip().upper()
    if symbol_filter:
        filtered_stocks = [s for s in filtered_stocks if symbol_filter in s.get('Symbol', '').upper()]
        logger.debug(f"After symbol filter: {len(filtered_stocks)} stocks")

    # Exchange - Exact match (case-insensitive)
    exchange_filter = filters.get('exchange', 'any').lower()
    if exchange_filter != 'any':
        filtered_stocks = [s for s in filtered_stocks if s.get('Exchange', '').lower() == exchange_filter]
        logger.debug(f"After exchange filter: {len(filtered_stocks)} stocks")

    # Sector - Exact match (case-insensitive)
    sector_filter = filters.get('sector', 'any').lower()
    if sector_filter != 'any':
        filtered_stocks = [s for s in filtered_stocks if s.get('Sector', '').lower() == sector_filter]
        logger.debug(f"After sector filter: {len(filtered_stocks)} stocks")

    # Industry - Exact match (case-insensitive)
    industry_filter = filters.get('industry', 'any').lower()
    if industry_filter != 'any':
        filtered_stocks = [s for s in filtered_stocks if s.get('Industry', '').lower() == industry_filter]
        logger.debug(f"After industry filter: {len(filtered_stocks)} stocks")

    # Market Cap Filter
    market_cap_filter = filters.get('market_cap', 'any').lower()
    if market_cap_filter != 'any':
        mc_filters = {
            'mega': (Decimal('200000000000'), None),  # Over 200B
            'large': (Decimal('10000000000'), Decimal('200000000000')),  # 10B to 200B
            'mid': (Decimal('2000000000'), Decimal('10000000000')),  # 2B to 10B
            'small': (Decimal('300000000'), Decimal('2000000000')),  # 300M to 2B
            'micro': (Decimal('50000000'), Decimal('300000000')),  # 50M to 300M
            'nano': (None, Decimal('50000000')),  # Under 50M
        }
        
        # For 'Over X' or 'Under X' filters
        if 'over' in market_cap_filter:
            # Extract the number from strings like "Over 1B", "Over 5B", etc.
            amount_str = market_cap_filter.split(' ')[1]
            amount = parse_amount_with_suffix(amount_str)
            if amount:
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get('MarketCap'), amount, '>')]
        elif 'under' in market_cap_filter:
            amount_str = market_cap_filter.split(' ')[1]
            amount = parse_amount_with_suffix(amount_str)
            if amount:
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get('MarketCap'), amount, '<')]
        else:
            # Extract keyword like 'mega', 'large' etc.
            mc_key = market_cap_filter.split(' ')[0].lower()
            if mc_key in mc_filters:
                min_cap, max_cap = mc_filters[mc_key]
                temp_list = []
                for s in filtered_stocks:
                    stock_mc = s.get('MarketCap') # Already Decimal or None
                    if stock_mc is not None:
                        match = True
                        if min_cap is not None and stock_mc < min_cap:
                            match = False
                        if max_cap is not None and stock_mc >= max_cap: # Use >= for upper bound exclusion
                            match = False
                        if match:
                            temp_list.append(s)
                filtered_stocks = temp_list
        
        logger.debug(f"After market cap filter: {len(filtered_stocks)} stocks")

    # Dividend Yield Filter
    div_yield_filter = filters.get('div_yield', 'any').lower()
    if div_yield_filter != 'any':
        stock_key = 'DividendYield'
        if div_yield_filter == 'none':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 0, '==')]
        elif div_yield_filter == 'positive':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 0, '>')]
        elif div_yield_filter == 'high':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 3, '>')]
        elif div_yield_filter == 'very high':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 6, '>')]
        elif 'over' in div_yield_filter:
            # Extract percentage value
            pct = float(div_yield_filter.split(' ')[1].replace('%', ''))
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), pct, '>')]
        elif 'under' in div_yield_filter:
            pct = float(div_yield_filter.split(' ')[1].replace('%', ''))
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), pct, '<') and safe_compare(s.get(stock_key), 0, '>')]
        
        logger.debug(f"After dividend yield filter: {len(filtered_stocks)} stocks")

    # Average Volume Filter
    avg_volume_filter = filters.get('avg_volume', 'any').lower()
    if avg_volume_filter != 'any':
        stock_key = 'Volume'
        if 'under' in avg_volume_filter:
            amount_str = avg_volume_filter.split(' ')[1]
            amount = parse_amount_with_suffix(amount_str)
            if amount:
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), amount, '<')]
        elif 'over' in avg_volume_filter:
            amount_str = avg_volume_filter.split(' ')[1]
            amount = parse_amount_with_suffix(amount_str)
            if amount:
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), amount, '>=')]
        elif 'to' in avg_volume_filter:
            # Handle range like "100K to 500K"
            parts = avg_volume_filter.split(' to ')
            if len(parts) == 2:
                min_str = parts[0]
                max_str = parts[1]
                min_amount = parse_amount_with_suffix(min_str)
                max_amount = parse_amount_with_suffix(max_str)
                if min_amount and max_amount:
                    filtered_stocks = [s for s in filtered_stocks if 
                                      safe_compare(s.get(stock_key), min_amount, '>=') and 
                                      safe_compare(s.get(stock_key), max_amount, '<')]
        
        logger.debug(f"After avg volume filter: {len(filtered_stocks)} stocks")

    # Current Volume Filter
    current_volume_filter = filters.get('current_volume', 'any').lower()
    if current_volume_filter != 'any':
        stock_key = 'Volume'  # Or specific current volume field if available
        if 'under' in current_volume_filter:
            amount_str = current_volume_filter.split(' ')[1]
            amount = parse_amount_with_suffix(amount_str)
            if amount:
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), amount, '<')]
        elif 'over' in current_volume_filter:
            amount_str = current_volume_filter.split(' ')[1]
            amount = parse_amount_with_suffix(amount_str)
            if amount:
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), amount, '>=')]
        
        logger.debug(f"After current volume filter: {len(filtered_stocks)} stocks")

    # Relative Volume Filter
    rel_volume_filter = filters.get('rel_volume', 'any').lower()
    if rel_volume_filter != 'any':
        stock_key = 'RelativeVolume'  # You might need to calculate this field
        if 'over' in rel_volume_filter:
            value = float(rel_volume_filter.split(' ')[1])
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), value, '>')]
        elif 'under' in rel_volume_filter:
            value = float(rel_volume_filter.split(' ')[1])
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), value, '<')]
        
        logger.debug(f"After relative volume filter: {len(filtered_stocks)} stocks")

    # Price Filter
    price_filter = filters.get('price', 'any').lower()
    if price_filter != 'any':
        stock_key = 'CurrentPrice'
        if 'under' in price_filter:
            # Handle "Under PKRX" - check if 'PKR' exists in the string
            try:
                if 'pkr' in price_filter:
                    price_val = float(price_filter.split('pkr')[1])
                else:
                    # Try to extract the numeric part directly
                    price_val = float(''.join(c for c in price_filter if c.isdigit() or c == '.'))
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), price_val, '<')]
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing price filter '{price_filter}': {str(e)}")
        elif 'over' in price_filter:
            # Handle "Over PKRX" - check if 'PKR' exists in the string
            try:
                if 'pkr' in price_filter:
                    price_val = float(price_filter.split('pkr')[1])
                else:
                    # Try to extract the numeric part directly
                    price_val = float(''.join(c for c in price_filter if c.isdigit() or c == '.'))
                filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), price_val, '>')]
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing price filter '{price_filter}': {str(e)}")
        elif 'to' in price_filter:
            # Handle "PKRX to PKRY" with more robust parsing
            try:
                parts = price_filter.split(' to ')
                if len(parts) == 2:
                    # Parse first part (min price)
                    if 'pkr' in parts[0].lower():
                        min_price = float(parts[0].lower().split('pkr')[1])
                    else:
                        min_price = float(''.join(c for c in parts[0] if c.isdigit() or c == '.'))
                    
                    # Parse second part (max price)
                    if 'pkr' in parts[1].lower():
                        max_price = float(parts[1].lower().split('pkr')[1])
                    else:
                        max_price = float(''.join(c for c in parts[1] if c.isdigit() or c == '.'))
                    
                    filtered_stocks = [s for s in filtered_stocks if 
                                      safe_compare(s.get(stock_key), min_price, '>=') and 
                                      safe_compare(s.get(stock_key), max_price, '<')]
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing price range filter '{price_filter}': {str(e)}")
        
        logger.debug(f"After price filter: {len(filtered_stocks)} stocks")

    # P/E Filter
    pe_filter = filters.get('pe_ratio', 'any').lower()
    if pe_filter != 'any':
        stock_key = 'PE'
        if pe_filter == 'low (<15)':
            filtered_stocks = [s for s in filtered_stocks if 
                              safe_compare(s.get(stock_key), 0, '>') and 
                              safe_compare(s.get(stock_key), 15, '<')]
        elif pe_filter == 'profitable (>0)':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 0, '>')]
        elif pe_filter == 'high (>50)':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 50, '>')]
        elif pe_filter == 'negative (<0)':
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), 0, '<')]
        elif 'under' in pe_filter:
            # Extract number from "Under X"
            value = float(pe_filter.split(' ')[1])
            filtered_stocks = [s for s in filtered_stocks if 
                              safe_compare(s.get(stock_key), 0, '>') and 
                              safe_compare(s.get(stock_key), value, '<')]
        elif 'over' in pe_filter:
            # Extract number from "Over X"
            value = float(pe_filter.split(' ')[1])
            filtered_stocks = [s for s in filtered_stocks if safe_compare(s.get(stock_key), value, '>')]
        
        logger.debug(f"After P/E filter: {len(filtered_stocks)} stocks")

    logger.info(f"Filter applied. Count after filtering: {len(filtered_stocks)} stocks")
    return filtered_stocks

def parse_amount_with_suffix(amount_str):
    """Parse strings like '1M', '500K', '10B' into numbers"""
    try:
        amount_str = amount_str.upper().replace('$', '')
        if 'K' in amount_str:
            return float(amount_str.replace('K', '')) * 1000
        elif 'M' in amount_str:
            return float(amount_str.replace('M', '')) * 1000000
        elif 'B' in amount_str:
            return float(amount_str.replace('B', '')) * 1000000000
        else:
            return float(amount_str)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse amount string: {amount_str}")
        return None

def generate_mock_stock_data(count=100):
    """
    Generate mock stock data for demonstration purposes.
    Used as a fallback when API calls fail.
    """
    logger.info(f"Generating mock data for {count} stocks")
    # Extended list of symbols to include more stocks
    symbols = [
        # Oil & Gas
        'OGDC', 'PPL', 'PSO', 'MARI', 'APL', 'ATRL', 'PRL', 'BYCO', 'SNGP', 'SSGC', 
        # Banking
        'HBL', 'UBL', 'MCB', 'BAHL', 'MEBL', 'BAFL', 'ABL', 'BOP', 'AKBL', 'FABL', 'NBP',
        # Cement
        'LUCK', 'DGKC', 'FCCL', 'MLCF', 'PIOC', 'CHCC', 'KOHC', 'ACPL', 'POWER', 'GWLC',
        # Fertilizer
        'EFERT', 'FFC', 'ENGRO', 'FFBL', 'FATIMA', 'DAAG',
        # Technology
        'SYS', 'TRG', 'AVN', 'NETSOL', 'TPL', 'OCTOPUS', 'INIL', 'PAEL', 'TELE',
        # Automobile
        'HCAR', 'INDU', 'PSMC', 'GHNL', 'AGTL', 'MTL', 'GATM', 'SAZEW', 'ATLH',
        # Power
        'HUBC', 'KAPCO', 'KEL', 'NPL', 'NCPL', 'SPWL', 'HASCOL', 'PKGP', 'LPL', 'EPQL', 'SEARL',
        # Textile
        'NML', 'GATM', 'ILP', 'KTML', 'NCL', 'GADT', 'RUBY', 'SILK', 'BWHL', 'NPTL', 'TREET',
        # Food
        'UNITY', 'ASC', 'SAZEW', 'NESTLE', 'FFL', 'KTML', 'EFOODS', 'MITL', 'HASCOL', 'PAEL',
        # Pharmaceuticals
        'SEARL', 'ABOT', 'GLAXO', 'HINOON', 'FEROZ', 'AGP', 'SAPL', 'DWHL', 'ATRL',
        # Chemicals
        'ICI', 'LOTCHEM', 'EPCL', 'AKZO', 'SPL', 'DOL', 'NCPL', 'FFBL', 'FATIMA',
        # Insurance
        'AICL', 'IGIHL', 'JGICL', 'ADAMJEE', 'EFU', 'SILK', 'HASCOL', 'PAEL', 'TPL',
        # Telecommunication
        'PTC', 'TELE', 'WTL', 'SCOM', 'NTC', 'PAEL',
        # Miscellaneous
        'PAEL', 'HASCOL', 'TPL', 'SILK', 'NML', 'GATM', 'KTML', 'NCL', 'BWHL',
    ]
    
    # Use all symbols or limit based on count parameter
    selected_symbols = []
    for i in range(min(count, len(symbols))):
        if i < len(symbols):
            selected_symbols.append(symbols[i])
        else:
            # If we need more than available symbols, duplicate with suffix
            base_idx = i % len(symbols)
            selected_symbols.append(f"{symbols[base_idx]}_{i//len(symbols)}")
    
    stocks = []
    for symbol in selected_symbols:
        try:
            # Get sector based on symbol
            if any(oil_gas in symbol for oil_gas in ['OGDC', 'PPL', 'PSO', 'MARI', 'APL', 'ATRL', 'PRL', 'BYCO', 'SNGP', 'SSGC']):
                sector = 'Oil & Gas'
            elif any(bank in symbol for bank in ['HBL', 'UBL', 'MCB', 'BAHL', 'MEBL', 'BAFL', 'ABL', 'BOP', 'AKBL', 'FABL', 'NBP']):
                sector = 'Banking'
            elif any(cement in symbol for cement in ['LUCK', 'DGKC', 'FCCL', 'MLCF', 'PIOC', 'CHCC', 'KOHC', 'ACPL', 'POWER', 'GWLC']):
                sector = 'Cement'
            elif any(tech in symbol for tech in ['SYS', 'TRG', 'AVN', 'NETSOL', 'TPL', 'OCTOPUS']):
                sector = 'Technology'
            elif any(auto in symbol for auto in ['HCAR', 'INDU', 'PSMC', 'GHNL', 'AGTL', 'MTL']):
                sector = 'Automobile'
            else:
                # Default sectors for others
                sector = random.choice(['Fertilizer', 'Textile', 'Food', 'Pharmaceuticals', 'Chemicals', 'Insurance', 'Telecommunication', 'Miscellaneous'])
            
            # Generate realistic price ranges based on sector
            if sector == 'Banking':
                base_price = random.uniform(100, 300)
            elif sector == 'Oil & Gas':
                base_price = random.uniform(80, 400)
            elif sector == 'Cement':
                base_price = random.uniform(50, 200)
            elif sector == 'Technology':
                base_price = random.uniform(300, 800)
            elif sector == 'Fertilizer':
                base_price = random.uniform(90, 350)
            elif sector == 'Automobile':
                base_price = random.uniform(150, 500)
            elif sector == 'Power':
                base_price = random.uniform(30, 120)
            elif sector == 'Food':
                base_price = random.uniform(20, 100)
            else:
                base_price = random.uniform(10, 500)
                
            price = round(base_price, 2)
            change_percent = round(random.uniform(-5, 5), 2)
            volume = random.randint(10000, 10000000)
            pe_ratio = round(random.uniform(5, 25), 2)
            market_cap = round(price * random.randint(100000, 10000000) / 1000000, 2) * 1000000
            
            # Calculate other values based on price
            open_price = round(price * (1 - random.uniform(-0.02, 0.02)), 2)
            high_price = round(max(price, open_price) * (1 + random.uniform(0, 0.05)), 2)
            low_price = round(min(price, open_price) * (1 - random.uniform(0, 0.05)), 2)
            change = round(price * change_percent / 100, 2)
            
            # Add dividend yield based on sector
            if sector == 'Banking':
                div_yield = round(random.uniform(2, 8), 2)
            elif sector == 'Oil & Gas':
                div_yield = round(random.uniform(3, 10), 2)
            elif sector == 'Power':
                div_yield = round(random.uniform(5, 12), 2)
            elif sector == 'Cement':
                div_yield = round(random.uniform(1, 5), 2)
            elif sector == 'Technology':
                div_yield = round(random.uniform(0, 2), 2)
            else:
                div_yield = round(random.uniform(0, 7), 2)
                
            # Some stocks should have zero dividend
            if random.random() < 0.3:
                div_yield = 0
            
            # Generate specific industry based on sector
            if sector == 'Oil & Gas':
                industry = random.choice(['Exploration', 'Refining', 'Marketing', 'Integrated'])
            elif sector == 'Banking':
                industry = random.choice(['Commercial Banking', 'Investment Banking', 'Islamic Banking'])
            elif sector == 'Cement':
                industry = 'Cement'
            elif sector == 'Technology':
                industry = random.choice(['Software', 'IT Services', 'Hardware'])
            elif sector == 'Automobile':
                industry = random.choice(['Auto Manufacturing', 'Auto Parts'])
            else:
                industry = sector
            
            # Generate technical metrics for new filters
            # Price to Book (P/B) Ratio - different ranges by sector
            if sector == 'Banking':
                pb_ratio = round(random.uniform(0.7, 2.5), 2)
            elif sector == 'Technology':
                pb_ratio = round(random.uniform(3.0, 8.0), 2)
            elif sector == 'Oil & Gas':
                pb_ratio = round(random.uniform(0.8, 3.0), 2)
            else:
                pb_ratio = round(random.uniform(0.5, 5.0), 2)
            
            # Price to Sales (P/S) Ratio
            if sector == 'Technology':
                ps_ratio = round(random.uniform(2.0, 10.0), 2)
            elif sector == 'Banking':
                ps_ratio = round(random.uniform(1.0, 4.0), 2)
            else:
                ps_ratio = round(random.uniform(0.3, 7.0), 2)
            
            # RSI (14)
            rsi_value = round(random.uniform(20, 80), 2)
            
            # 52-Week data
            year_high = round(price * (1 + random.uniform(0.05, 0.3)), 2)
            year_low = round(price * (1 - random.uniform(0.05, 0.3)), 2)
            
            # Make sure year_high is actually higher than current price
            if year_high < price:
                year_high = price * 1.05
            
            # Make sure year_low is actually lower than current price
            if year_low > price:
                year_low = price * 0.95
            
            # Calculate 52-week range metrics
            year_high_ratio = round((price / year_high) * 100, 2)  # How close to 52-week high (percent)
            year_low_ratio = round(((price - year_low) / year_low) * 100, 2)  # How far from 52-week low (percent)
            year_range_percentile = round(((price - year_low) / (year_high - year_low)) * 100, 2)  # Position in range (0-100%)
            
            # Moving Averages
            ma_50 = round(price * (1 + random.uniform(-0.15, 0.15)), 2)  # 50-day MA
            ma_200 = round(price * (1 + random.uniform(-0.2, 0.2)), 2)  # 200-day MA
            
            # Calculate ratios and trends
            price_to_ma50_ratio = round(price / ma_50, 2) if ma_50 > 0 else 1
            price_to_ma200_ratio = round(price / ma_200, 2) if ma_200 > 0 else 1
            
            # Direction indicators (-1 to 1 range)
            ma50_direction = round(random.uniform(-1, 1), 2)
            ma200_direction = round(random.uniform(-1, 1), 2)
            
            # Boolean flags for crosses
            crossed_above_ma50 = random.random() < 0.1  # 10% chance of recent cross
            crossed_below_ma50 = random.random() < 0.1 and not crossed_above_ma50
            crossed_above_ma200 = random.random() < 0.05  # 5% chance of recent cross
            crossed_below_ma200 = random.random() < 0.05 and not crossed_above_ma200
            
            # Volume metrics
            avg_volume = round(volume * (1 + random.uniform(-0.4, 0.4)))
            volume_to_avg_ratio = round(volume / avg_volume, 2) if avg_volume > 0 else 1
            rel_volume = volume_to_avg_ratio  # Set rel_volume to volume_to_avg_ratio
            volume_trend = round(random.uniform(-1, 1), 2)  # -1 to 1 range for decreasing to increasing
            
            # New High/Low flags
            is_new_high = year_high_ratio > 98  # Within 2% of 52-week high
            is_new_low = year_low_ratio < 2  # Within 2% of 52-week low
            
            stock = {
                'Symbol': symbol,
                'CompanyName': f"{symbol} Limited",
                'CurrentPrice': price,
                'ChangePercentage': change_percent,
                'Change': change,
                'Volume': volume,
                'Sector': sector,
                'Industry': industry,
                'Country': 'Pakistan',
                'Exchange': 'PSX',
                'OpenPrice': open_price,
                'HighPrice': high_price,
                'LowPrice': low_price,
                'PE': pe_ratio,
                'MarketCap': market_cap,
                'VWAP': round((high_price + low_price + price) / 3, 2),
                'LastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'CreateDateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'DividendYield': div_yield,
                'RelativeVolume': rel_volume,
                'PB': pb_ratio,
                'PS': ps_ratio,
                'RSI14': rsi_value,
                'YearHigh': year_high,
                'YearLow': year_low,
                'YearHighRatio': year_high_ratio,
                'YearLowRatio': year_low_ratio,
                'YearRangePercentile': year_range_percentile,
                'MA50': ma_50,
                'MA200': ma_200,
                'PriceToMA50Ratio': price_to_ma50_ratio,
                'PriceToMA200Ratio': price_to_ma200_ratio,
                'MA50Direction': ma50_direction,
                'MA200Direction': ma200_direction,
                'CrossedAboveMA50': crossed_above_ma50,
                'CrossedBelowMA50': crossed_below_ma50, 
                'CrossedAboveMA200': crossed_above_ma200,
                'CrossedBelowMA200': crossed_below_ma200,
                'AvgVolume': avg_volume,
                'VolumeToAvgRatio': volume_to_avg_ratio,
                'VolumeTrend': volume_trend,
                'IsNewHigh': is_new_high,
                'IsNewLow': is_new_low
            }
            stocks.append(stock)
        except Exception as e:
            logger.error(f"Error generating mock data for symbol {symbol}: {str(e)}")
            continue
    
    logger.info(f"Successfully generated {len(stocks)} mock stocks")
    return stocks

def get_stock_chart_data(request):
    """
    API endpoint to fetch historical data for a specific stock and generate chart data.
    Uses database data for historical stock information.
    """
    try:
        symbol = request.GET.get('symbol')
        if not symbol:
            logger.error("No symbol provided in request")
            return JsonResponse({'error': 'Symbol is required'}, status=400)

        logger.info(f"Fetching chart data for symbol: {symbol}")

        # Get date range (default to last 90 days for better visualization)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)

        # Query database for historical data
        stocks = Stock.objects.filter(
            symbol=symbol,
            date__range=[start_date, end_date]
        ).order_by('date')

        if not stocks.exists():
            logger.error(f"No data found for symbol {symbol} in database")
            return JsonResponse({
                'error': 'No data found for the specified symbol',
                'symbol': symbol,
                'date_range': f"{start_date} to {end_date}"
            }, status=404)

        # Prepare data arrays
        dates = []
        prices = []  # Close prices
        opens = []
        highs = []
        lows = []
        volumes = []
        
        for stock in stocks:
            try:
                date_str = stock.date.strftime('%Y-%m-%d')
                dates.append(date_str)
                prices.append(float(stock.current_price))
                opens.append(float(stock.open_price))
                highs.append(float(stock.high_price))
                lows.append(float(stock.low_price))
                volumes.append(stock.volume)
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing data for {symbol} on {stock.date}: {str(e)}")
                continue

        if not dates:
            logger.error(f"No valid data points found for symbol {symbol}")
            return JsonResponse({
                'error': 'No valid data points found',
                'symbol': symbol,
                'date_range': f"{start_date} to {end_date}"
            }, status=404)

        chart_data = {
            'dates': dates,
            'prices': prices,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'volumes': volumes,
            'symbol': symbol,
            'company_name': stocks.first().company_name,
            'data_points': len(dates),
            'source': 'database'
        }
        
        logger.info(f"Successfully generated chart data for {symbol} with {len(dates)} data points")
        return JsonResponse(chart_data)

    except Exception as e:
        logger.error(f"Error generating chart data: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)

def get_heat_map_data(request):
    """
    API endpoint to fetch data for the heat map visualization.
    Groups stocks by sector and measures by different metrics.
    """
    try:
        # Get live data from API
        raw_data = fetch_stock_data(LIVE_API_URL)
        if not raw_data:
            return JsonResponse({'error': 'Failed to fetch data from API'}, status=500)
        
        # Process data for heat map
        stocks = process_stock_data(raw_data)
        
        # Group stocks by sector and calculate metrics
        sectors = {}
        for stock in stocks:
            sector = stock['Sector']
            if sector not in sectors:
                sectors[sector] = {
                    'stocks': [],
                    'market_cap': 0,
                    'volume': 0,
                    'change_total': 0,
                    'count': 0
                }
            sectors[sector]['stocks'].append(stock)
            
            # Handle potential decimal.Decimal type in MarketCap
            market_cap = stock['MarketCap']
            if hasattr(market_cap, 'to_integral_exact'):  # Check if it's a decimal.Decimal
                market_cap = float(market_cap)
            sectors[sector]['market_cap'] += float(market_cap)
            
            sectors[sector]['volume'] += int(stock['Volume'])
            sectors[sector]['change_total'] += float(stock['ChangePercentage'])
            sectors[sector]['count'] += 1
        
        # Create heat map data structure
        sector_names = list(sectors.keys())
        metrics = ['Market Cap', 'Volume', 'Change %']
        values = []
        
        # Calculate normalized values for each metric
        for metric in metrics:
            row = []
            for sector in sector_names:
                if metric == 'Market Cap':
                    value = sectors[sector]['market_cap'] / 1e9  # Convert to billions
                elif metric == 'Volume':
                    value = sectors[sector]['volume'] / 1e6  # Convert to millions
                else:  # Change %
                    value = sectors[sector]['change_total'] / sectors[sector]['count']
                row.append(round(value, 2))
            values.append(row)
        
        # Create text annotations
        text = []
        for metric in metrics:
            row = []
            for sector in sector_names:
                if metric == 'Market Cap':
                    value = f"{sectors[sector]['market_cap']/1e9:.1f}B"
                elif metric == 'Volume':
                    value = f"{sectors[sector]['volume']/1e6:.1f}M"
                else:
                    value = f"{sectors[sector]['change_total']/sectors[sector]['count']:.1f}%"
                row.append(value)
            text.append(row)
        
        return JsonResponse({
            'x': sector_names,
            'y': metrics,
            'z': values,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Error generating heat map data: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)

def get_bubble_chart_data(request):
    """
    API endpoint to fetch data for the bubble chart visualization.
    Shows market cap vs change percentage by sector, with bubble size representing volume.
    """
    try:
        # Get live or historical data based on request
        live_data = request.GET.get('live_data', 'true')
        
        if live_data == 'true':
            # Fetch live data from API
            raw_data = fetch_stock_data(LIVE_API_URL)
            stocks = process_stock_data(raw_data)
        else:
            # Get historical data from database
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=1)
            stocks = get_historical_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        if not stocks:
            return JsonResponse({'error': 'No data available'}, status=404)
        
        # Group stocks by sector and calculate metrics
        sector_data = {}
        for stock in stocks:
            sector = stock.get('Sector', 'Other')
            if sector not in sector_data:
                sector_data[sector] = {
                    'count': 0,
                    'total_change': 0,
                    'total_market_cap': 0,
                    'total_volume': 0
                }
            
            sector_data[sector]['count'] += 1
            sector_data[sector]['total_change'] += float(stock.get('ChangePercentage', 0))
            
            # Handle potential decimal.Decimal type in MarketCap
            market_cap = stock.get('MarketCap', 0)
            if hasattr(market_cap, 'to_integral_exact'):  # Check if it's a decimal.Decimal
                market_cap = float(market_cap)
            sector_data[sector]['total_market_cap'] += float(market_cap)
            
            sector_data[sector]['total_volume'] += float(stock.get('Volume', 0))
        
        # Calculate averages and prepare data for the chart
        x = []  # Sectors
        y = []  # Average change percentage
        size = []  # Volume
        color = []  # Market cap
        text = []  # Hover text
        
        for sector, data in sector_data.items():
            if data['count'] > 0:
                avg_change = data['total_change'] / data['count']
                avg_market_cap = data['total_market_cap'] / data['count']
                total_volume = data['total_volume']
                
                x.append(sector)
                y.append(avg_change)
                size.append(total_volume / 1000000)  # Scale down volume for better visualization
                color.append(avg_market_cap / 1000000)  # Scale down market cap for better visualization
                text.append(f"Sector: {sector}<br>" +
                          f"Avg Change: {avg_change:.2f}%<br>" +
                          f"Avg Market Cap: {avg_market_cap/1000000:.2f}M<br>" +
                          f"Total Volume: {total_volume/1000000:.2f}M")
        
        if not x:
            return JsonResponse({'error': 'No valid data available'}, status=404)
        
        return JsonResponse({
            'x': x,
            'y': y,
            'size': size,
            'color': color,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Error in get_bubble_chart_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_line_chart_data(request):
    """
    API endpoint to fetch data for the line chart visualization.
    Creates a market trend line chart using historical data.
    """
    try:
        # Get historical data for the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get data from database
        stocks = Stock.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        if not stocks.exists():
            return JsonResponse({'error': 'No historical data available'}, status=404)
        
        # Group data by date and calculate market metrics
        dates = []
        market_values = []
        volume_values = []
        
        current_date = None
        daily_total = {'price': 0, 'volume': 0, 'count': 0}
        
        for stock in stocks:
            if current_date != stock.date:
                if current_date is not None:
                    # Calculate averages and append to arrays
                    avg_price = daily_total['price'] / daily_total['count']
                    avg_volume = daily_total['volume'] / daily_total['count']
                    dates.append(current_date.strftime('%Y-%m-%d'))
                    market_values.append(round(avg_price, 2))
                    volume_values.append(round(avg_volume, 0))
                
                # Reset for new date
                current_date = stock.date
                daily_total = {'price': 0, 'volume': 0, 'count': 0}
            
            # Accumulate daily values
            daily_total['price'] += float(stock.current_price)
            daily_total['volume'] += stock.volume
            daily_total['count'] += 1
        
        # Add the last day
        if current_date is not None:
            avg_price = daily_total['price'] / daily_total['count']
            avg_volume = daily_total['volume'] / daily_total['count']
            dates.append(current_date.strftime('%Y-%m-%d'))
            market_values.append(round(avg_price, 2))
            volume_values.append(round(avg_volume, 0))
        
        return JsonResponse({
            'dates': dates,
            'market_values': market_values,
            'volume_values': volume_values
        })
        
    except Exception as e:
        logger.error(f"Error generating line chart data: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)

def stock_detail(request, symbol):
    """
    View function for the stock detail page.
    Shows detailed information about a single stock.
    """
    try:
        # Get the latest data for this stock from the database
        today = timezone.now().date()
        stock = Stock.objects.filter(symbol=symbol).order_by('-date').first()
        
        if not stock:
            # If not in DB, try to fetch from live API
            raw_data = fetch_stock_data(LIVE_API_URL)
            if raw_data:
                # Process the raw data
                processed_data = process_stock_data(raw_data)
                # Find this specific stock
                stock_data = next((s for s in processed_data if s.get('Symbol') == symbol), None)
                
                if not stock_data:
                    # Stock not found in API data, try mock data as a fallback
                    mock_data = generate_mock_stock_data(20)
                    stock_data = next((s for s in mock_data if s.get('Symbol') == symbol), None)
                    
                    if not stock_data:
                        # Stock not found in mock data either
                        return render(request, 'psxscreener/error.html', {
                            'error_message': f'Stock with symbol {symbol} not found',
                            'back_url': '/psxscreener/'
                        })
                
                # Generate some mock price history for the chart
                mock_history = []
                base_price = stock_data.get('CurrentPrice', 0)
                today = timezone.now().date()
                
                for i in range(30):
                    day = today - timedelta(days=i)
                    # Generate random but realistic price movements
                    daily_change = random.uniform(-0.02, 0.02)  # -2% to +2% daily change
                    price = round(base_price * (1 + daily_change), 2)
                    base_price = price  # Use this price for the next day's calculation
                    
                    # Add some randomness to volume
                    volume = int(stock_data.get('Volume', 100000) * random.uniform(0.7, 1.3))
                    
                    mock_history.append({
                        'date': day.strftime('%Y-%m-%d'),
                        'price': price,
                        'change': round(daily_change * 100, 2),
                        'volume': volume,
                        'open': round(price * random.uniform(0.99, 1.01), 2),
                        'high': round(price * random.uniform(1.01, 1.03), 2),
                        'low': round(price * random.uniform(0.97, 0.99), 2),
                    })
                
                # Sort by date ascending
                mock_history.sort(key=lambda x: x['date'])
                
                # Make sure all required fields have defaults to avoid NoneType errors
                if 'Change' not in stock_data or stock_data['Change'] is None:
                    if 'ChangePercentage' in stock_data and stock_data['ChangePercentage'] is not None and 'CurrentPrice' in stock_data and stock_data['CurrentPrice'] is not None:
                        stock_data['Change'] = (float(stock_data['ChangePercentage']) * float(stock_data['CurrentPrice'])) / 100
                    else:
                        stock_data['Change'] = 0.0
                        
                if 'ChangePercentage' not in stock_data or stock_data['ChangePercentage'] is None:
                    stock_data['ChangePercentage'] = 0.0
                
                # We have stock data from API
                context = {
                    'stock': stock_data,
                    'history': mock_history,
                    'from_api': True,
                    'last_update': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                
                # Calculate estimated annual dividend if dividend yield is available
                if 'DividendYield' in stock_data and stock_data['DividendYield'] and stock_data['CurrentPrice']:
                    try:
                        dividend_yield = float(stock_data['DividendYield'])
                        current_price = float(stock_data['CurrentPrice'])
                        est_dividend = (dividend_yield * current_price) / 100
                        stock_data['EstDividend'] = round(est_dividend, 2)
                    except (ValueError, TypeError):
                        stock_data['EstDividend'] = None
                else:
                    stock_data['EstDividend'] = None
            else:
                # API failed
                return render(request, 'psxscreener/error.html', {
                    'error_message': f'Could not fetch data for stock {symbol}',
                    'back_url': '/psxscreener/'
                })
        else:
            # Stock found in DB, get historical data too
            # Get last 30 days of data for this stock
            history = Stock.objects.filter(
                symbol=symbol,
                date__lte=today,
                date__gte=today - timedelta(days=30)
            ).order_by('-date')
            
            # Convert to list of dictionaries for template
            stock_data = {
                'Symbol': stock.symbol,
                'CompanyName': stock.company_name,
                'CurrentPrice': float(stock.current_price),
                'ChangePercentage': float(stock.change_percentage),
                'Change': float(stock.change) if hasattr(stock, 'change') and stock.change is not None else float(stock.change_percentage * stock.current_price / 100),
                'Volume': stock.volume,
                'Sector': stock.sector,
                'Industry': stock.industry if hasattr(stock, 'industry') and stock.industry is not None else stock.sector,
                'Country': stock.country if hasattr(stock, 'country') and stock.country is not None else 'Pakistan',
                'Exchange': stock.exchange if hasattr(stock, 'exchange') and stock.exchange is not None else 'PSX',
                'OpenPrice': float(stock.open_price),
                'HighPrice': float(stock.high_price),
                'LowPrice': float(stock.low_price),
                'PE': float(stock.pe_ratio) if stock.pe_ratio is not None else None,
                'MarketCap': float(stock.market_cap) if stock.market_cap is not None else None,
                'VWAP': float(stock.vwap) if hasattr(stock, 'vwap') and stock.vwap is not None else None,
                'LastUpdated': stock.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Date': stock.date.strftime('%Y-%m-%d'),
                'DividendYield': float(stock.dividend_yield) if hasattr(stock, 'dividend_yield') and stock.dividend_yield is not None else 0,
                'PB': float(stock.pb_ratio) if hasattr(stock, 'pb_ratio') and stock.pb_ratio is not None else None,
                'PS': float(stock.ps_ratio) if hasattr(stock, 'ps_ratio') and stock.ps_ratio is not None else None,
                'RSI14': float(stock.rsi14) if hasattr(stock, 'rsi14') and stock.rsi14 is not None else None,
                'YearHigh': float(stock.year_high) if hasattr(stock, 'year_high') and stock.year_high is not None else None,
                'YearLow': float(stock.year_low) if hasattr(stock, 'year_low') and stock.year_low is not None else None,
                'MA50': float(stock.ma50) if hasattr(stock, 'ma50') and stock.ma50 is not None else None,
                'MA200': float(stock.ma200) if hasattr(stock, 'ma200') and stock.ma200 is not None else None,
                'AvgVolume': int(stock.avg_volume) if hasattr(stock, 'avg_volume') and stock.avg_volume is not None else None,
                'RelativeVolume': float(stock.relative_volume) if hasattr(stock, 'relative_volume') and stock.relative_volume is not None else None
            }
            
            history_data = []
            for h in history:
                history_data.append({
                    'date': h.date.strftime('%Y-%m-%d'),
                    'price': float(h.current_price),
                    'change': float(h.change_percentage),
                    'volume': h.volume,
                    'open': float(h.open_price),
                    'high': float(h.high_price),
                    'low': float(h.low_price),
                })
            
            # Calculate estimated annual dividend if dividend yield is available
            dividend_yield = stock_data.get('DividendYield', 0)
            current_price = stock_data.get('CurrentPrice', 0)
            if dividend_yield and current_price:
                stock_data['EstDividend'] = round((dividend_yield * current_price) / 100, 2)
            else:
                stock_data['EstDividend'] = None
                
            context = {
                'stock': stock_data,
                'history': history_data,
                'from_api': False,
                'last_update': stock.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        
        # Add market index data
        index_data = get_index_data()
        context.update({
            'kse100_change': index_data.get('kse100_change', 0),
            'kse100_index': index_data.get('kse100_price', 'N/A'),
            'today': today,
        })
        
        return render(request, 'psxscreener/stock_detail.html', context)
        
    except Exception as e:
        logger.exception(f"Error in stock_detail view for symbol {symbol}:")
        return render(request, 'psxscreener/error.html', {
            'error_message': f'An error occurred: {str(e)}',
            'back_url': '/psxscreener/'
        })

@csrf_exempt
def debug_api(request):
    """
    Debug view to test API connectivity and authentication.
    Only available in development mode.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'Debug API endpoint only available in DEBUG mode'}, status=403)
    
    result = {
        'api_auth_url': AUTH_API_URL,
        'api_live_url': LIVE_API_URL,
        'api_history_url': HISTORY_API_URL.format(start_date='2023-01-01', end_date='2023-01-02'),
    }
    
    # Test token generation
    try:
        logger.info("Testing API token generation")
        token = get_api_token()
        if token:
            result['token_status'] = 'Success'
            result['token'] = token[:10] + '...'  # Only show first few chars for security
            
            # Test API connectivity with token
            try:
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Bearer {token}'
                }
                
                # Try to get a small sample of data
                test_url = LIVE_API_URL
                logger.info(f"Testing API connectivity with URL: {test_url}")
                response = requests.get(test_url, headers=headers, timeout=30)
                
                result['api_status_code'] = response.status_code
                
                if response.status_code == 200:
                    data = response.json()
                    result['api_status'] = 'Success'
                    result['record_count'] = len(data) if data else 0
                    if data and len(data) > 0:
                        # Include a sample record (first one)
                        result['sample_record'] = data[0]
                    else:
                        result['api_message'] = 'API returned empty data'
                else:
                    result['api_status'] = 'Failed'
                    result['api_message'] = response.text[:500]
            except Exception as e:
                result['api_status'] = 'Error'
                result['api_error'] = str(e)
        else:
            result['token_status'] = 'Failed'
            result['error'] = 'Failed to generate token'
    except Exception as e:
        result['token_status'] = 'Error'
        result['error'] = str(e)
    
    return JsonResponse(result)

@csrf_exempt
def debug_api_fetch(request):
    """Debug endpoint to check API data fetching and filtering separately"""
    try:
        # Only fetch data
        logger.info("Debug API: Fetching data from API")
        raw_data = fetch_stock_data(LIVE_API_URL)
        
        if not raw_data:
            return JsonResponse({
                'success': False,
                'error': 'No data returned from API',
                'message': 'API returned empty response'
            })
        
        # Process the raw data into standardized format
        all_stocks = process_stock_data(raw_data)
        
        # Filter data if requested
        if 'filter' in request.GET:
            # Get filter params from request
            filter_params = {k: v for k, v in request.GET.items() if k not in ['filter']}
            
            # Set defaults for any missing params
            for param in ['exchange', 'sector', 'industry', 'market_cap', 'div_yield', 'avg_volume', 'price', 'pe_ratio']:
                if param not in filter_params:
                    filter_params[param] = 'any'
            
            # Apply filters
            filtered_stocks = filter_stocks(all_stocks, filter_params)
            
            return JsonResponse({
                'success': True,
                'message': 'Data fetched and filtered successfully',
                'raw_data_count': len(raw_data),
                'processed_data_count': len(all_stocks),
                'filtered_data_count': len(filtered_stocks),
                'filter_params': filter_params,
                'sample_data': filtered_stocks[:5] if filtered_stocks else [] # Show sample of filtered data
            })
        
        # Just return the processed data stats without filtering
        return JsonResponse({
            'success': True,
            'message': 'Data fetched successfully',
            'raw_data_count': len(raw_data),
            'processed_data_count': len(all_stocks),
            'sample_data': all_stocks[:5] if all_stocks else [] # Show sample of processed data
        })
        
    except Exception as e:
        logger.exception("Error in debug_api_fetch:")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while debugging API fetch'
        })

# Test API connectivity on startup
def test_api_connection():
    """Test API connectivity on application startup and log results"""
    if getattr(settings, 'TESTING', False):
        # Skip during tests
        return
    
    logger.info("Testing API connectivity on startup...")
    try:
        token = get_api_token()
        if token:
            logger.info("✅ Successfully obtained API token")
            try:
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Bearer {token}'
                }
                
                response = requests.get(LIVE_API_URL, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        logger.info(f"✅ API connection successful, received {len(data)} records")
                    else:
                        logger.warning("⚠️ API returned empty data, check query parameters")
                else:
                    logger.error(f"❌ API connection failed with status code: {response.status_code}")
                    logger.error(f"Response content: {response.text[:500]}")
            except Exception as e:
                logger.error(f"❌ Error testing API connection: {str(e)}")
        else:
            logger.error("❌ Failed to obtain API token, check credentials")
    except Exception as e:
        logger.error(f"❌ Unexpected error during API connection test: {str(e)}")

# Run the API test when the application is ready
def ready():
    """Run when the application is ready"""
    test_api_connection()

# Attempt to run the test now
try:
    if apps.apps_ready:
        test_api_connection()
except:
    # Ignore errors during import time
    pass

def update_db_schema():
    """
    Update database schema to add missing columns to the Stock model table.
    This function runs when the application is loaded.
    """
    logger.info("Checking and updating psxscreener_stock database schema...")
    
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
            logger.info("Added 'industry' column")
        
        # Add country column if it doesn't exist
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='psxscreener_stock' AND column_name='country';
        """)
        if not cursor.fetchone():
            cursor.execute("""
            ALTER TABLE psxscreener_stock ADD COLUMN country varchar(50) DEFAULT 'Pakistan';
            """)
            logger.info("Added 'country' column")
        
        # Add exchange column if it doesn't exist
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='psxscreener_stock' AND column_name='exchange';
        """)
        if not cursor.fetchone():
            cursor.execute("""
            ALTER TABLE psxscreener_stock ADD COLUMN exchange varchar(20) DEFAULT 'PSX';
            """)
            logger.info("Added 'exchange' column")
        
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
                logger.info(f"Added '{column_name}' column")
        
        logger.info("Database schema update completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during schema update: {e}")
        connection.rollback()
    finally:
        cursor.close()

# Run the update when the module is loaded
try:
    update_db_schema()
except Exception as e:
    logger.error(f"Failed to update database schema: {e}")

# Import the rest of the module after the schema update
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
import random
import decimal
import os
import re
from .models import Stock, LastDataUpdate
from django.apps import apps