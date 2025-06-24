from django.shortcuts import render
import yfinance as yf
import pandas as pd
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import concurrent.futures
import time
from functools import lru_cache
from django.views.decorators.cache import cache_page

# Cache stock data for 15 minutes to reduce API calls
@lru_cache(maxsize=128)
def get_ticker_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def get_stock_data(filters):
    # Define tickers (expanded list for more options)
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'PYPL', 'ADBE', 'INTC',
        'NFLX', 'CSCO', 'CMCSA', 'PEP', 'COST', 'TMUS', 'AVGO', 'TXN', 'QCOM', 'HON',
        'AMGN', 'SBUX', 'MDLZ', 'GILD', 'ADP', 'VRTX', 'REGN', 'ILMN', 'ISRG', 'DXCM',
        'SPGI', 'MU', 'ATVI', 'KLAC', 'PANW', 'FTNT', 'CDNS', 'MCHP', 'MRVL', 'MNST',
        'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP', 'V', 'MA',
        'DIS', 'NFLX', 'CMCSA', 'T', 'VZ', 'CHTR', 'TMUS', 'DISH', 'ATUS', 'LUMN',
        'JNJ', 'PFE', 'MRK', 'ABBV', 'BMY', 'LLY', 'AMGN', 'GILD', 'BIIB', 'REGN'
    ]
    
    stocks = []
    start_time = time.time()
    
    # Use ThreadPoolExecutor to fetch data in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks and map tickers to their future results
        future_to_ticker = {executor.submit(get_ticker_info, ticker): ticker for ticker in tickers}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            info = future.result()
            
            if not info:
                continue
                
            # Apply filters
            if filters.get('exchange') and info.get('exchange') != filters['exchange']:
                continue
                
            # Price Range Filter
            price = info.get('regularMarketPrice', 0)
            if filters.get('price_min') and price < float(filters['price_min']):
                continue
            if filters.get('price_max') and price > float(filters['price_max']):
                continue
                
            # Volume Range Filter
            volume = info.get('regularMarketVolume', 0)
            if filters.get('volume_min') and volume < int(filters['volume_min']):
                continue
            if filters.get('volume_max') and volume > int(filters['volume_max']):
                continue
                
            if filters.get('sector') and info.get('sector') != filters['sector']:
                continue
                
            # Market Cap Filter
            market_cap = info.get('marketCap', 0)
            if filters.get('market_cap'):
                if filters['market_cap'] == 'mega' and market_cap < 200e9:
                    continue
                elif filters['market_cap'] == 'large' and (market_cap < 10e9 or market_cap > 200e9):
                    continue
                elif filters['market_cap'] == 'mid' and (market_cap < 2e9 or market_cap > 10e9):
                    continue
                elif filters['market_cap'] == 'small' and (market_cap < 300e6 or market_cap > 2e9):
                    continue
                elif filters['market_cap'] == 'micro' and market_cap > 300e6:
                    continue
            
            # P/E Ratio Filter
            pe_ratio = info.get('trailingPE', 0)
            if filters.get('pe_ratio'):
                if filters['pe_ratio'] == 'low' and pe_ratio > 15:
                    continue
                elif filters['pe_ratio'] == 'profitable' and pe_ratio <= 0:
                    continue
                elif filters['pe_ratio'] == 'high' and pe_ratio < 50:
                    continue
                elif filters['pe_ratio'] == 'negative' and pe_ratio >= 0:
                    continue
                
            # Dividend Yield Filter
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            if filters.get('dividend'):
                if filters['dividend'] == 'any' and dividend_yield <= 0:
                    continue
                elif filters['dividend'] == 'high' and dividend_yield < 4:
                    continue
                elif filters['dividend'] == 'very_high' and dividend_yield < 7:
                    continue
                elif filters['dividend'] == 'none' and dividend_yield > 0:
                    continue
            
            # 52-Week High/Low Filter
            if filters.get('52_week'):
                fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
                fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
                
                if fifty_two_week_high > 0 and fifty_two_week_low > 0:
                    current_range_percent = (price - fifty_two_week_low) / (fifty_two_week_high - fifty_two_week_low) * 100
                    
                    if filters['52_week'] == 'high' and current_range_percent < 80:
                        continue
                    elif filters['52_week'] == 'low' and current_range_percent > 20:
                        continue
                    elif filters['52_week'] == 'middle' and (current_range_percent < 20 or current_range_percent > 80):
                        continue
            
            # Calculate additional metrics
            change_percent = info.get('regularMarketChangePercent', 0)
            eps = info.get('trailingEps', 0)
            
            stocks.append({
                'symbol': ticker,
                'company_name': info.get('shortName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'exchange': info.get('exchange', 'N/A'),
                'market_cap': market_cap / 1e9,  # Convert to billions
                'price': price,
                'change_pct': change_percent,
                'volume': volume,
                'avg_volume': info.get('averageVolume', 0),
                'pe_ratio': pe_ratio,
                'eps': eps,
                'dividend_yield': dividend_yield,
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'target_price': info.get('targetMeanPrice', 0),
            })
    
    end_time = time.time()
    print(f"Data fetching completed in {end_time - start_time:.2f} seconds")
    
    return stocks

# Cache the page for 5 minutes to improve performance
@cache_page(60 * 5)
def stock_screener(request):
    filters = {
        'exchange': request.GET.get('exchange'),
        'market_cap': request.GET.get('market_cap'),
        'price_min': request.GET.get('price_min'),
        'price_max': request.GET.get('price_max'),
        'volume_min': request.GET.get('volume_min'),
        'volume_max': request.GET.get('volume_max'),
        'sector': request.GET.get('sector'),
        'pe_ratio': request.GET.get('pe_ratio'),
        'dividend': request.GET.get('dividend'),
        '52_week': request.GET.get('52_week'),
    }
    
    # Get sort parameter from request
    sort_by = request.GET.get('sort', 'market_cap')
    sort_order = request.GET.get('order', 'desc')
    
    stocks = get_stock_data(filters)
    
    # Apply sorting
    reverse_sort = sort_order == 'desc'
    if sort_by in ['symbol', 'company_name', 'sector', 'industry']:
        stocks.sort(key=lambda x: str(x.get(sort_by, '')).lower(), reverse=reverse_sort)
    else:
        stocks.sort(key=lambda x: float(x.get(sort_by, 0) or 0), reverse=reverse_sort)
    
    # Pagination
    page = request.GET.get('page', 1)
    items_per_page = int(request.GET.get('items_per_page', 20))  # Allow user to choose items per page
    paginator = Paginator(stocks, items_per_page)
    
    try:
        paginated_stocks = paginator.page(page)
    except PageNotAnInteger:
        paginated_stocks = paginator.page(1)
    except EmptyPage:
        paginated_stocks = paginator.page(paginator.num_pages)
    
    # Calculate sort order toggle for template
    sort_order_toggle = 'asc' if sort_order == 'desc' else 'desc'
    
    context = {
        'stocks': paginated_stocks,
        'paginator': paginator,
        'current_date': pd.Timestamp.now(),
        'filters': filters,
        'total_results': len(stocks),
        'sort_by': sort_by,
        'sort_order': sort_order,
        'sort_order_toggle': sort_order_toggle,
        'items_per_page': items_per_page,
    }
    return render(request, 'stockscreener/index.html', context)