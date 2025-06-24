from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Stock
import datetime
import json
import logging
import pandas as pd
import orjson
import requests
import numpy as np

from .helpers import (
    get_token, 
    get_data, 
    calculate_market_cap, 
    filter_stocks
)
from .schemas import (
    Stock as StockSchema,
    MarketData,
    PaginationMeta,
    StockResponse,
    ErrorResponse
)

# Set up basic logging
logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    """Main view for the stock screener page"""
    # Get current market data for display
    try:
        # Try to get live market index data
        token = get_token()
        market_data = {}
        
        if token:
            # Get KSE-100 Index data
            url = "https://api.mg-link.net/api/Data1/GetPSXIndicesLive"
            indices_data = get_data(url, token)
            
            if indices_data and isinstance(indices_data, list):
                # Find KSE-100 in the list
                for index in indices_data:
                    if index.get('Symbol') == 'KSE100' or index.get('IndexName', '').lower() == 'kse-100':
                        market_data['kse100_index'] = index.get('LastTrade', 42156.28)
                        market_data['kse100_change'] = index.get('Change', 0.43)
                        market_data['kse100_change_percent'] = index.get('ChangePercentage', 0.43)
                        break
            
            # Get market volume
            url = "https://api.mg-link.net/api/Data1/GetPSXLivePrices"
            stocks_data = get_data(url, token)
            if stocks_data and isinstance(stocks_data, list):
                total_volume = sum(float(stock.get('Volume', 0)) for stock in stocks_data)
                market_data['market_volume'] = total_volume
            
            # Get sectors data
            sectors = {}
            if stocks_data and isinstance(stocks_data, list):
                for stock in stocks_data:
                    sector = stock.get('Sector')
                    if sector:
                        if sector not in sectors:
                            sectors[sector] = {
                                'count': 0,
                                'market_cap': 0
                            }
                        sectors[sector]['count'] += 1
                        sectors[sector]['market_cap'] += float(stock.get('MarketCap', 0))
                
                market_data['sectors'] = [
                    {
                        'name': sector,
                        'count': data['count'],
                        'market_cap': data['market_cap']
                    } for sector, data in sectors.items()
                ]
            
            # Get total stocks count
            market_data['total_stocks'] = len(stocks_data) if stocks_data and isinstance(stocks_data, list) else 0
        
        # If API data not available, use default values
        if not market_data.get('kse100_index'):
            market_data['kse100_index'] = 42156.28
            market_data['kse100_change'] = 0.43
            market_data['kse100_change_percent'] = 0.43
            market_data['market_volume'] = 285200000
            market_data['total_stocks'] = 559
        
        # Count active filters - consider all possible filter parameters
        # Exclude pagination and sorting parameters
        excluded_params = ['page', 'per_page', 'sort_by', 'sort_dir', 'orderBy', 'orderDirection']
        active_filters_count = sum(1 for key, value in request.GET.items() 
                                  if key not in excluded_params and value and value.lower() != 'any')
                                  
        # Format the timestamp for last updated
        market_data['last_update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Pass market data and filters to template
        context = {
            'market_data': market_data,
            'active_filters_count': active_filters_count,
            'kse100_index': market_data.get('kse100_index'),
            'kse100_change': market_data.get('kse100_change_percent'),
            'market_volume': market_data.get('market_volume'),
            'total_stocks': market_data.get('total_stocks'),
            'sort_by': request.GET.get('sort_by', 'Symbol'),
            'sort_dir': request.GET.get('sort_dir', 'asc')
        }
        
        return render(request, 'SmartScreener/Screener.html', context)
        
    except Exception as e:
        logger.error(f"Error in index view: {str(e)}")
        # Provide fallback data in case of error
        context = {
            'kse100_index': 42156.28,
            'kse100_change': 0.43,
            'market_volume': 285200000,
            'total_stocks': 559,
            'active_filters_count': 0
        }
        return render(request, 'SmartScreener/Screener.html', context)

def get_stock_prices(request):
    """API endpoint to get stock prices"""
    try:
        # Try to get real API data first
        token = get_token()
        if token:
            # Correct API endpoint URL for PSX Stock Prices
            url = "https://api.mg-link.net/api/Data1/GetPSXLivePrices"
            api_data = get_data(url, token)
            
            if api_data:
                # Ensure api_data is a list
                if not isinstance(api_data, list):
                    api_data = [api_data]
                
                # Add MarketCap field if not present
                for stock in api_data:
                    if 'MarketCap' not in stock:
                        stock['MarketCap'] = calculate_market_cap(stock)
                    if 'PE' not in stock:
                        stock['PE'] = None
                
                # Get query parameters for filtering
                page = int(request.GET.get('page', 1))
                per_page = int(request.GET.get('per_page', 20))
                
                # Create comprehensive filters dictionary
                filters = {
                    # Fundamentals tab filters
                    'exchange': request.GET.get('exchange'),
                    'index': request.GET.get('index'),
                    'sector': request.GET.get('sector'),
                    'industry': request.GET.get('industry'),
                    'country': request.GET.get('country'),
                    'market_cap': request.GET.get('market_cap'),
                    'div_yield': request.GET.get('div_yield'),
                    'avg_volume': request.GET.get('avg_volume'),
                    'rel_volume': request.GET.get('rel_volume'),
                    'current_volume': request.GET.get('current_volume'),
                    'price': request.GET.get('price'),
                    'target_price': request.GET.get('target_price'),
                    'ipo_date': request.GET.get('ipo_date'),
                    'shares_outstanding': request.GET.get('shares_outstanding'),
                    'float': request.GET.get('float'),
                    'analyst_recom': request.GET.get('analyst_recom'),
                    'option_short': request.GET.get('option_short'),
                    'earnings_date': request.GET.get('earnings_date'),
                    'trades': request.GET.get('trades'),
                    
                    # Technical tab filters
                    'pe_ratio': request.GET.get('pe_ratio'),
                    'forward_pe': request.GET.get('forward_pe'),
                    'peg': request.GET.get('peg'),
                    'ps': request.GET.get('ps'),
                    'pb': request.GET.get('pb'),
                    
                    # Performance tab filters
                    'performance': request.GET.get('performance'),
                    'performance_2': request.GET.get('performance_2'),
                    'volatility': request.GET.get('volatility'),
                    'rsi': request.GET.get('rsi'),
                    'gap': request.GET.get('gap'),
                    'sma_20': request.GET.get('sma_20'),
                    'sma_50': request.GET.get('sma_50'),
                    'sma_200': request.GET.get('sma_200'),
                    'change': request.GET.get('change'),
                    'change_open': request.GET.get('change_open'),
                    
                    # Legacy filters (for backward compatibility)
                    'price_min': request.GET.get('price_min'),
                    'price_max': request.GET.get('price_max'),
                    'volume_min': request.GET.get('volume_min'),
                    'volume_max': request.GET.get('volume_max'),
                    'change_min': request.GET.get('change_min'),
                    'change_max': request.GET.get('change_max'),
                    'pe_min': request.GET.get('pe_min'),
                    'pe_max': request.GET.get('pe_max'),
                    'symbol': request.GET.get('symbol'),
                    'signal': request.GET.get('signal')
                }
                
                # Remove None values and empty strings
                filters = {k: v for k, v in filters.items() if v is not None and v != '' and (isinstance(v, str) and v.lower() != 'any' or not isinstance(v, str))}
                
                # Apply all filters using enhanced filter_stocks function
                filtered_data = filter_stocks(api_data, filters)
                
                # Apply sorting
                sort_by = request.GET.get('sort_by', 'Symbol')
                sort_dir = request.GET.get('sort_dir', 'asc')
                
                # Create DataFrame for efficient sorting
                df = pd.DataFrame(filtered_data)
                
                if not df.empty:
                    # Find the correct column to sort by
                    valid_sort_key = sort_by
                    if sort_by not in df.columns:
                        for col in df.columns:
                            if col.lower() == sort_by.lower():
                                valid_sort_key = col
                                break
                        else:
                            valid_sort_key = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
                    
                    # Determine sort direction
                    ascending = sort_dir.lower() != 'desc'
                    
                    # For numeric columns, ensure proper typing
                    if valid_sort_key in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
                        df[valid_sort_key] = pd.to_numeric(df[valid_sort_key], errors='coerce')
                    
                    # Apply sorting
                    df = df.sort_values(by=valid_sort_key, ascending=ascending, na_position='last')
                    
                    # Convert back to list
                    filtered_data = df.replace({np.nan: None}).to_dict('records')
                
                # Paginate results
                total_count = len(filtered_data)
                
                # Ensure page is valid
                total_pages = max(1, (total_count + per_page - 1) // per_page)
                if page > total_pages and total_pages > 0:
                    page = 1
                
                # Calculate slice indices
                start = (page - 1) * per_page
                end = min(start + per_page, total_count)
                
                # Create paginated data
                paginated_data = filtered_data[start:end] if start < total_count else []
                
                return JsonResponse({
                    'status': 'success',
                    'data': paginated_data,
                    'meta': {
                        'total': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }
                })

        # Fall back to database data if API fails
        from django.conf import settings
        from django.db.models import Q
        
        # Query database
        stocks = Stock.objects.all()
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        sort_by = request.GET.get('sort_by', 'symbol')
        sort_dir = request.GET.get('sort_dir', 'asc')
        
        # Apply basic filters with ORM
        if request.GET.get('symbol'):
            stocks = stocks.filter(symbol__icontains=request.GET.get('symbol'))
        
        if request.GET.get('sector') and request.GET.get('sector').lower() != 'any':
            stocks = stocks.filter(sector__iexact=request.GET.get('sector'))
        
        if request.GET.get('industry') and request.GET.get('industry').lower() != 'any':
            stocks = stocks.filter(industry__iexact=request.GET.get('industry'))
        
        # Convert queryset to list of dictionaries for advanced filtering
        stock_list = []
        for stock in stocks:
            stock_dict = {
                'Symbol': stock.symbol,
                'CompanyName': stock.company_name,
                'Sector': stock.sector,
                'Industry': stock.industry,
                'Last': float(stock.last_price) if stock.last_price else None,
                'LDCP': float(stock.previous_close) if stock.previous_close else None,
                'Change': float(stock.price_change) if stock.price_change else None,
                'PctChange': float(stock.percent_change) if stock.percent_change else None,
                'Open': float(stock.open_price) if stock.open_price else None,
                'High': float(stock.high_price) if stock.high_price else None,
                'Low': float(stock.low_price) if stock.low_price else None,
                'Volume': int(stock.volume) if stock.volume else None,
                'MarketCap': float(stock.market_cap) if stock.market_cap else None,
                'PE': float(stock.pe) if stock.pe else None
            }
            stock_list.append(stock_dict)
        
        # Collect all filter parameters
        filters = {
            # Fundamentals tab filters
            'exchange': request.GET.get('exchange'),
            'index': request.GET.get('index'),
            'sector': request.GET.get('sector'),
            'industry': request.GET.get('industry'),
            'country': request.GET.get('country'),
            'market_cap': request.GET.get('market_cap'),
            'div_yield': request.GET.get('div_yield'),
            'avg_volume': request.GET.get('avg_volume'),
            'rel_volume': request.GET.get('rel_volume'),
            'current_volume': request.GET.get('current_volume'),
            'price': request.GET.get('price'),
            'target_price': request.GET.get('target_price'),
            'ipo_date': request.GET.get('ipo_date'),
            'shares_outstanding': request.GET.get('shares_outstanding'),
            'float': request.GET.get('float'),
            'analyst_recom': request.GET.get('analyst_recom'),
            'option_short': request.GET.get('option_short'),
            'earnings_date': request.GET.get('earnings_date'),
            'trades': request.GET.get('trades'),
            
            # Technical tab filters
            'pe_ratio': request.GET.get('pe_ratio'),
            'forward_pe': request.GET.get('forward_pe'),
            'peg': request.GET.get('peg'),
            'ps': request.GET.get('ps'),
            'pb': request.GET.get('pb'),
            
            # Performance tab filters
            'performance': request.GET.get('performance'),
            'performance_2': request.GET.get('performance_2'),
            'volatility': request.GET.get('volatility'),
            'rsi': request.GET.get('rsi'),
            'gap': request.GET.get('gap'),
            'sma_20': request.GET.get('sma_20'),
            'sma_50': request.GET.get('sma_50'),
            'sma_200': request.GET.get('sma_200'),
            'change': request.GET.get('change'),
            'change_open': request.GET.get('change_open'),
            
            # Legacy filters
            'price_min': request.GET.get('price_min'),
            'price_max': request.GET.get('price_max'),
            'volume_min': request.GET.get('volume_min'),
            'volume_max': request.GET.get('volume_max'),
            'change_min': request.GET.get('change_min'),
            'change_max': request.GET.get('change_max'),
            'pe_min': request.GET.get('pe_min'),
            'pe_max': request.GET.get('pe_max'),
            'symbol': request.GET.get('symbol'),
            'signal': request.GET.get('signal')
        }
        
        # Remove None values and empty strings
        filters = {k: v for k, v in filters.items() if v is not None and v != '' and (not isinstance(v, str) or v.lower() != 'any')}
        
        # Apply all filters using enhanced filter_stocks function
        filtered_data = filter_stocks(stock_list, filters)
        
        # Sort using pandas
        df = pd.DataFrame(filtered_data)
        if not df.empty:
            # Find the correct column name to sort by
            valid_sort_key = sort_by
            if sort_by not in df.columns:
                for col in df.columns:
                    if col.lower() == sort_by.lower():
                        valid_sort_key = col
                        break
                else:
                    valid_sort_key = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
            
            # Determine sort direction
            ascending = sort_dir.lower() != 'desc'
            
            # For numeric columns, ensure proper typing
            if valid_sort_key in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
                df[valid_sort_key] = pd.to_numeric(df[valid_sort_key], errors='coerce')
            
            # Apply sorting
            df = df.sort_values(by=valid_sort_key, ascending=ascending, na_position='last')
            
            # Convert back to list
            filtered_data = df.replace({np.nan: None}).to_dict('records')
        
        # Paginate the results
        total_count = len(filtered_data)
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        
        # Ensure page is valid
        if page > total_pages and total_pages > 0:
            page = 1
        
        # Calculate slice indices
        start = (page - 1) * per_page
        end = min(start + per_page, total_count)
        
        # Slice the data
        paginated_data = filtered_data[start:end] if start < total_count else []
        
        return JsonResponse({
            'status': 'success',
            'data': paginated_data,
            'meta': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_stock_prices: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve stock data',
            'error': str(e)
        }, status=500)

def get_indices_live(request):
    """API endpoint to get live indices data"""
    token = get_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    url = "https://api.mg-link.net/api/Data1/GetPSXIndicesLive"
    data = get_data(url, token)
    
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to retrieve indices data"}, status=500)

def get_psx_announcements(request):
    """API endpoint to get PSX announcements"""
    token = get_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    url = "https://api.mg-link.net/api/Data1/GetPSXAnnouncements"
    data = get_data(url, token)
    
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to retrieve announcements"}, status=500)

def get_news(request):
    """API endpoint to get news"""
    token = get_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    url = "https://api.mg-link.net/api/Data1/GetMGNews_New"
    data = get_data(url, token)
    
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to retrieve news"}, status=500)

def get_commodities(request):
    """API endpoint to get commodities data"""
    token = get_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    symbols = request.GET.get('symbols', 'Q1T')
    date = request.GET.get('date', '')
    
    url = f"https://api.mg-link.net/api/Data1/Commodities?symbols={symbols}"
    if date:
        url += f"&date={date}"
    
    data = get_data(url, token)
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to retrieve commodities data"}, status=500)

def get_currencies_live(request):
    """API endpoint to get live currencies data"""
    token = get_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    symbols = request.GET.get('symbols', 'USDPKR,GBPUSD,EURUSD')
    
    url = f"https://api.mg-link.net/api/Data/GetCurrenciesLive?Symbols={symbols}"
    data = get_data(url, token)
    
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to retrieve currencies data"}, status=500)

def get_economic_data(request):
    """API endpoint to get economic data"""
    token = get_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    data_id = request.GET.get('data_id', '1')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    url = f"https://api.mg-link.net/api/Data1/EconomicData?DataID={data_id}"
    if start_date and end_date:
        url += f"&StartDate={start_date}&EndDate={end_date}"
    
    data = get_data(url, token)
    
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to retrieve economic data"}, status=500)

@csrf_exempt
def screener(request):
    """API endpoint for the stock screener"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        # Get basic pagination and sorting parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))
        order_by = request.GET.get('orderBy', 'Symbol')
        order_direction = request.GET.get('orderDirection', 'asc')
        
        # Create a comprehensive filter dictionary that handles all possible filter parameters
        filters = {
            # Fundamentals tab filters
            'exchange': request.GET.get('exchange'),
            'index': request.GET.get('index'),
            'sector': request.GET.get('sector'),
            'industry': request.GET.get('industry'),
            'country': request.GET.get('country'),
            'market_cap': request.GET.get('market_cap'),
            'div_yield': request.GET.get('div_yield'),
            'avg_volume': request.GET.get('avg_volume'),
            'rel_volume': request.GET.get('rel_volume'),
            'current_volume': request.GET.get('current_volume'),
            'price': request.GET.get('price'),
            'target_price': request.GET.get('target_price'),
            'ipo_date': request.GET.get('ipo_date'),
            'shares_outstanding': request.GET.get('shares_outstanding'),
            'float': request.GET.get('float'),
            'analyst_recom': request.GET.get('analyst_recom'),
            'option_short': request.GET.get('option_short'),
            'earnings_date': request.GET.get('earnings_date'),
            'trades': request.GET.get('trades'),
            
            # Technical tab filters
            'pe_ratio': request.GET.get('pe_ratio'),
            'forward_pe': request.GET.get('forward_pe'),
            'peg': request.GET.get('peg'),
            'ps': request.GET.get('ps'),
            'pb': request.GET.get('pb'),
            
            # Performance tab filters
            'performance': request.GET.get('performance'),
            'performance_2': request.GET.get('performance_2'),
            'volatility': request.GET.get('volatility'),
            'rsi': request.GET.get('rsi'),
            'gap': request.GET.get('gap'),
            'sma_20': request.GET.get('sma_20'),
            'sma_50': request.GET.get('sma_50'),
            'sma_200': request.GET.get('sma_200'),
            'change': request.GET.get('change'),
            'change_open': request.GET.get('change_open'),
            
            # Legacy/compatibility filters
            'marketCap': request.GET.get('marketCap'),
            'pe': request.GET.get('pe'),
            'dividendYield': request.GET.get('dividendYield'),
            'volume': request.GET.get('volume'),
            'targetPrice': request.GET.get('targetPrice'),
            'signal': request.GET.get('signal')
        }
        
        # Remove None values and empty strings
        filters = {k: v for k, v in filters.items() if v is not None and v != '' and (isinstance(v, str) and v.lower() != 'any' or not isinstance(v, str))}
        
        # Try to get live API data
        token = get_token()
        if token:
            url = "https://api.mg-link.net/api/Data1/GetPSXLivePrices"
            api_data = get_data(url, token)
            
            if api_data:
                # Normalize data and add missing fields
                for stock in api_data:
                    if 'MarketCap' not in stock:
                        stock['MarketCap'] = calculate_market_cap(stock)
                
                # Apply all filters using our enhanced filter_stocks function
                filtered_stocks = filter_stocks(api_data, filters)
                
                # Create a DataFrame for advanced sorting
                df = pd.DataFrame(filtered_stocks)
                
                if not df.empty:
                    # Handle column name matching for sorting
                    valid_order_by = order_by
                    if order_by not in df.columns:
                        for col in df.columns:
                            if col.lower() == order_by.lower():
                                valid_order_by = col
                                break
                        else:
                            valid_order_by = 'Symbol'
                    
                    # Determine sort direction
                    ascending = order_direction.lower() != 'desc'
                    
                    # Handle numeric columns properly
                    if valid_order_by in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
                        df[valid_order_by] = pd.to_numeric(df[valid_order_by], errors='coerce')
                    
                    # Apply sorting
                    df = df.sort_values(by=valid_order_by, ascending=ascending, na_position='last')
                    
                    # Convert back to list
                    filtered_stocks = df.replace({np.nan: None}).to_dict('records')
                
                # Paginate results
                total_count = len(filtered_stocks)
                total_pages = max(1, (total_count + per_page - 1) // per_page)
                
                # Ensure page is valid
                if page > total_pages and total_pages > 0:
                    page = 1
                
                # Calculate slice indices
                start = (page - 1) * per_page
                end = min(start + per_page, total_count)
                
                # Slice the data
                paginated_stocks = filtered_stocks[start:end] if start < total_count else []
                
                return JsonResponse({
                    'data': paginated_stocks,
                    'pagination': {
                        'total': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages
                    }
                })
        
        # Fall back to database data if API fails
        from django.conf import settings
        from django.db.models import Q
        
        stocks = Stock.objects.all()
            
        # Apply basic filters with ORM
        if 'sector' in filters and filters['sector'] != 'Any':
            stocks = stocks.filter(sector__iexact=filters['sector'])
        
        if 'industry' in filters and filters['industry'] != 'Any':
            stocks = stocks.filter(industry__iexact=filters['industry'])
            
        # Convert queryset to list of dictionaries
        stock_list = []
        for stock in stocks:
            stock_dict = {
                'Symbol': stock.symbol,
                'CompanyName': stock.company_name,
                'Sector': stock.sector,
                'Industry': stock.industry,
                'Last': float(stock.last_price) if stock.last_price else None,
                'LDCP': float(stock.previous_close) if stock.previous_close else None,
                'Change': float(stock.price_change) if stock.price_change else None,
                'PctChange': float(stock.percent_change) if stock.percent_change else None,
                'Open': float(stock.open_price) if stock.open_price else None,
                'High': float(stock.high_price) if stock.high_price else None,
                'Low': float(stock.low_price) if stock.low_price else None,
                'Volume': int(stock.volume) if stock.volume else None,
                'MarketCap': float(stock.market_cap) if stock.market_cap else None,
                'PE': float(stock.pe) if stock.pe else None,
            }
            stock_list.append(stock_dict)
        
        # Apply all filters using pandas helper
        filtered_stocks = filter_stocks(stock_list, filters)
        
        # Apply sorting with pandas
        df = pd.DataFrame(filtered_stocks)
        if not df.empty:
            # Handle column name matching for sorting
            valid_order_by = order_by
            if order_by not in df.columns:
                for col in df.columns:
                    if col.lower() == order_by.lower():
                        valid_order_by = col
                        break
                else:
                    valid_order_by = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
            
            # Determine sort direction
            ascending = order_direction.lower() != 'desc'
            
            # Handle numeric columns properly
            if valid_order_by in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
                df[valid_order_by] = pd.to_numeric(df[valid_order_by], errors='coerce')
            
            # Apply sorting
            df = df.sort_values(by=valid_order_by, ascending=ascending, na_position='last')
            
            # Convert back to list
            filtered_stocks = df.replace({np.nan: None}).to_dict('records')
        
        # Pagination
        total_records = len(filtered_stocks)
        total_pages = max(1, (total_records + per_page - 1) // per_page)
        
        # Ensure page is valid
        if page > total_pages and total_pages > 0:
            page = 1
        
        # Calculate slice indices
        start = (page - 1) * per_page
        end = min(start + per_page, total_records)
        
        # Slice the data
        paginated_stocks = filtered_stocks[start:end] if start < total_records else []
        
        return JsonResponse({
            'data': paginated_stocks,
            'pagination': {
                'total': total_records,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error in screener: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_stock_daily_history(request):
    """API endpoint to get daily stock history"""
    token = get_token()
    if not token:
        logger.error("Failed to authenticate with the API")
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    # Get query parameters
    symbol = request.GET.get('symbol', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    if not symbol:
        return JsonResponse({"error": "Symbol parameter is required"}, status=400)
    
    # Build the URL based on parameters
    base_url = f"https://api.mg-link.net/api/Data1/PSXStockDailyHistory?Symbol={symbol}"
    if start_date and end_date:
        url = f"{base_url}&StartDate={start_date}&EndDate={end_date}"
    else:
        # Default to last 30 days if no dates provided
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        url = f"{base_url}&StartDate={start_date}&EndDate={end_date}"
    
    # Make the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                # Use orjson for better performance
                data = orjson.loads(response.content)
                return JsonResponse(data, safe=False)
            except Exception as e:
                logger.error(f"Error decoding JSON response: {str(e)}")
                return JsonResponse({"error": "Failed to parse API response"}, status=500)
        else:
            logger.error(f"API returned status code {response.status_code}")
            return JsonResponse({"error": f"API returned status code {response.status_code}"}, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve stock history for {symbol}: {str(e)}")
        return JsonResponse({"error": "Failed to connect to API"}, status=500)

def get_technical_indicators(request):
    """API endpoint to get technical indicators for a stock"""
    token = get_token()
    if not token:
        logger.error("Failed to authenticate with the API")
        return JsonResponse({"error": "Failed to authenticate with the API"}, status=401)
    
    # Get query parameters
    symbol = request.GET.get('symbol', '')
    period = request.GET.get('period', '14')  # Default to 14-day period
    
    if not symbol:
        return JsonResponse({"error": "Symbol parameter is required"}, status=400)
    
    # Build the URL based on parameters
    url = f"https://api.mg-link.net/api/Data1/TechnicalIndicators?Symbol={symbol}&Period={period}"
    
    # Make the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                # Use orjson for better performance
                data = orjson.loads(response.content)
                return JsonResponse(data, safe=False)
            except Exception as e:
                logger.error(f"Error decoding JSON response: {str(e)}")
                return JsonResponse({"error": "Failed to parse API response"}, status=500)
        else:
            logger.error(f"API returned status code {response.status_code}")
            return JsonResponse({"error": f"API returned status code {response.status_code}"}, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve technical indicators for {symbol}: {str(e)}")
        return JsonResponse({"error": "Failed to connect to API"}, status=500)

def get_stocks(request):
    """API endpoint to get and filter stock data for the screener"""
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        sort_by = request.GET.get('sort_by', 'Symbol')
        sort_dir = request.GET.get('sort_dir', 'asc')
        
        # Log all request parameters for debugging
        all_params = dict(request.GET.items())
        logger.debug(f"Received parameters: {all_params}")
        
        # Get token and fetch real data first
        token = get_token()
        if token:
            # Correct API endpoint URL for PSX Stock Prices
            url = "https://api.mg-link.net/api/Data1/GetPSXLivePrices"
            api_data = get_data(url, token)
            
            if api_data:
                # Ensure api_data is a list
                if not isinstance(api_data, list):
                    api_data = [api_data]
                
                # Add MarketCap field if not present and normalize field names
                for stock in api_data:
                    if 'MarketCap' not in stock:
                        stock['MarketCap'] = calculate_market_cap(stock)
                    if 'PE' not in stock and 'pe' in stock:
                        stock['PE'] = stock['pe']
                    # Handle percent change field inconsistencies
                    if 'PctChange' not in stock and 'changePercent' in stock:
                        stock['PctChange'] = stock['changePercent']
                    elif 'PctChange' not in stock and 'Change' in stock:
                        # If PctChange is missing but we have Change, try to calculate it
                        if 'LDCP' in stock and stock['LDCP'] and float(stock['LDCP']) != 0:
                            stock['PctChange'] = (float(stock['Change']) / float(stock['LDCP'])) * 100
                
                # Create comprehensive filters dictionary from all query parameters
                # This now supports all filter types defined in the frontend
                filters = {}
                
                # Loop through all request parameters and add them to the filters dictionary
                # Skip pagination, sorting and other non-filter parameters
                excluded_params = ['page', 'per_page', 'sort_by', 'sort_dir', 'csrfmiddlewaretoken']
                for key, value in request.GET.items():
                    if key not in excluded_params and value and value.lower() != 'any':
                        filters[key] = value
                        logger.debug(f"Added filter: {key}={value}")
                
                # Explicitly check for important filter parameters
                # Fundamentals tab filters
                if request.GET.get('exchange') and request.GET.get('exchange').lower() != 'any':
                    filters['exchange'] = request.GET.get('exchange')
                
                if request.GET.get('sector') and request.GET.get('sector').lower() != 'any':
                    filters['sector'] = request.GET.get('sector')
                
                if request.GET.get('industry') and request.GET.get('industry').lower() != 'any':
                    filters['industry'] = request.GET.get('industry')
                
                if request.GET.get('market_cap') and request.GET.get('market_cap').lower() != 'any':
                    filters['market_cap'] = request.GET.get('market_cap')
                
                # Technical tab filters
                if request.GET.get('pe_ratio') and request.GET.get('pe_ratio').lower() != 'any':
                    filters['pe_ratio'] = request.GET.get('pe_ratio')
                
                # Performance tab filters
                if request.GET.get('rsi') and request.GET.get('rsi').lower() != 'any':
                    filters['rsi'] = request.GET.get('rsi')
                
                if request.GET.get('performance') and request.GET.get('performance').lower() != 'any':
                    filters['performance'] = request.GET.get('performance')
                
                # Symbol search (supports both symbol and tickers parameter names)
                if request.GET.get('symbol'):
                    filters['symbol'] = request.GET.get('symbol')
                elif request.GET.get('tickers'):
                    filters['symbol'] = request.GET.get('tickers')
                
                # Signal filter
                if request.GET.get('signal') and request.GET.get('signal') != 'none':
                    filters['signal'] = request.GET.get('signal')
                
                # Log filters being applied
                logger.debug(f"Applying filters: {filters}")
                
                # Apply filters using the improved pandas-based filter_stocks function
                filtered_data = filter_stocks(api_data, filters)
                
                # Create DataFrame for efficient sorting
                df = pd.DataFrame(filtered_data)
                
                if not df.empty:
                    # Make sure sort field exists in the data - if not, use a fallback
                    valid_sort_key = sort_by
                    if sort_by not in df.columns:
                        for col in df.columns:
                            if col.lower() == sort_by.lower():
                                valid_sort_key = col
                                break
                        else:
                            valid_sort_key = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
                    
                    # Determine sort order
                    ascending = sort_dir.lower() != 'desc'
                    
                    # Apply sorting with pandas - handle numeric fields appropriately
                    if valid_sort_key in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
                        # Convert to numeric for correct sorting
                        df[valid_sort_key] = pd.to_numeric(df[valid_sort_key], errors='coerce')
                    
                    # Sort the dataframe
                    df = df.sort_values(by=valid_sort_key, ascending=ascending, na_position='last')
                    
                    # Convert back to list of dictionaries
                    filtered_data = df.replace({np.nan: None}).to_dict('records')
                
                # Log how many records we found after filtering
                logger.debug(f"Filter returned {len(filtered_data)} stocks")
                
                # Paginate results
                total_count = len(filtered_data)
                
                # Make sure page is valid
                total_pages = max(1, (total_count + per_page - 1) // per_page)
                if page > total_pages:
                    page = 1
                
                # Calculate slice indices
                start = (page - 1) * per_page
                end = min(start + per_page, total_count)  # Ensure we don't go past the end
                
                # Slice the data
                paginated_data = filtered_data[start:end] if start < total_count else []
                
                # Return paginated results with metadata
                return JsonResponse({
                    'status': 'success',
                    'data': paginated_data,
                    'meta': {
                        'total': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }
                })
        
        # Fall back to database data if API fails
        from django.db.models import Q
        stocks = Stock.objects.all()
        
        # Apply basic filters that can be handled by ORM
        if request.GET.get('symbol'):
            stocks = stocks.filter(symbol__icontains=request.GET.get('symbol'))
        
        if request.GET.get('sector') and request.GET.get('sector').lower() != 'any':
            stocks = stocks.filter(sector__iexact=request.GET.get('sector'))
        
        if request.GET.get('industry') and request.GET.get('industry').lower() != 'any':
            stocks = stocks.filter(industry__iexact=request.GET.get('industry'))
        
        # For more complex filters, we'll convert to dictionaries and use pandas
        stock_list = []
        for stock in stocks:
            stock_dict = {
                'Symbol': stock.symbol,
                'CompanyName': stock.company_name,
                'Sector': stock.sector,
                'Industry': stock.industry,
                'Last': float(stock.last_price) if stock.last_price else None,
                'LDCP': float(stock.previous_close) if stock.previous_close else None,
                'Change': float(stock.price_change) if stock.price_change else None,
                'PctChange': float(stock.percent_change) if stock.percent_change else None,
                'Open': float(stock.open_price) if stock.open_price else None,
                'High': float(stock.high_price) if stock.high_price else None,
                'Low': float(stock.low_price) if stock.low_price else None,
                'Volume': int(stock.volume) if stock.volume else None,
                'MarketCap': float(stock.market_cap) if stock.market_cap else None,
                'PE': float(stock.pe) if stock.pe else None
            }
            stock_list.append(stock_dict)
        
        # Collect all filter parameters
        filters = {
            # Fundamentals tab filters
            'exchange': request.GET.get('exchange'),
            'index': request.GET.get('index'),
            'sector': request.GET.get('sector'),
            'industry': request.GET.get('industry'),
            'country': request.GET.get('country'),
            'market_cap': request.GET.get('market_cap'),
            'div_yield': request.GET.get('div_yield'),
            'avg_volume': request.GET.get('avg_volume'),
            'rel_volume': request.GET.get('rel_volume'),
            'current_volume': request.GET.get('current_volume'),
            'price': request.GET.get('price'),
            'target_price': request.GET.get('target_price'),
            'ipo_date': request.GET.get('ipo_date'),
            'shares_outstanding': request.GET.get('shares_outstanding'),
            'float': request.GET.get('float'),
            'analyst_recom': request.GET.get('analyst_recom'),
            'option_short': request.GET.get('option_short'),
            'earnings_date': request.GET.get('earnings_date'),
            'trades': request.GET.get('trades'),
            
            # Technical tab filters
            'pe_ratio': request.GET.get('pe_ratio'),
            'forward_pe': request.GET.get('forward_pe'),
            'peg': request.GET.get('peg'),
            'ps': request.GET.get('ps'),
            'pb': request.GET.get('pb'),
            
            # Performance tab filters
            'performance': request.GET.get('performance'),
            'performance_2': request.GET.get('performance_2'),
            'volatility': request.GET.get('volatility'),
            'rsi': request.GET.get('rsi'),
            'gap': request.GET.get('gap'),
            'sma_20': request.GET.get('sma_20'),
            'sma_50': request.GET.get('sma_50'),
            'sma_200': request.GET.get('sma_200'),
            'change': request.GET.get('change'),
            'change_open': request.GET.get('change_open'),
            
            # Legacy filters
            'price_min': request.GET.get('price_min'),
            'price_max': request.GET.get('price_max'),
            'volume_min': request.GET.get('volume_min'),
            'volume_max': request.GET.get('volume_max'),
            'change_min': request.GET.get('change_min'),
            'change_max': request.GET.get('change_max'),
            'pe_min': request.GET.get('pe_min'),
            'pe_max': request.GET.get('pe_max'),
            'market_cap_min': request.GET.get('market_cap_min'),
            'market_cap_max': request.GET.get('market_cap_max'),
            'symbol': request.GET.get('symbol'),
            'signal': request.GET.get('signal')
        }
        
        # Remove None values and empty strings
        filters = {k: v for k, v in filters.items() if v is not None and v != '' and (not isinstance(v, str) or v.lower() != 'any')}
        
        # Apply all filters using the helper function with pandas
        filtered_data = filter_stocks(stock_list, filters)
            
        # Sort using pandas
        df = pd.DataFrame(filtered_data)
        if not df.empty:
            # Convert sort_by to Django ORM field name
            sort_field = sort_by.lower().replace('pctchange', 'percent_change')
            
            # Find closest matching column name
            valid_sort_key = sort_by
            if sort_by not in df.columns:
                for col in df.columns:
                    if col.lower() == sort_by.lower():
                        valid_sort_key = col
                        break
                else:
                    valid_sort_key = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
            
            # Determine sort order
            ascending = sort_dir.lower() != 'desc'
            
            # For numeric columns, ensure proper sorting
            if valid_sort_key in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
                df[valid_sort_key] = pd.to_numeric(df[valid_sort_key], errors='coerce')
            
            # Sort the dataframe
            df = df.sort_values(by=valid_sort_key, ascending=ascending, na_position='last')
            
            # Convert back to list
            filtered_data = df.replace({np.nan: None}).to_dict('records')
        
        # Paginate the results
        total_count = len(filtered_data)
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        
        # Ensure page is valid
        if page > total_pages and total_pages > 0:
            page = 1
            
        # Calculate slice indices
        start = (page - 1) * per_page
        end = min(start + per_page, total_count)
        
        # Slice the data
        paginated_data = filtered_data[start:end] if start < total_count else []
        
        return JsonResponse({
            'status': 'success',
            'data': paginated_data,
            'meta': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_stocks: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve stock data',
            'error': str(e)
        }, status=500)

