from django.shortcuts import render
from django.http import JsonResponse
import yfinance as yf
import json
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def index_view(request):
    """Render the copilot feature template."""
    return render(request, "copilot_feature.html")

def process_query(request):
    """Process user queries about stocks and return relevant information."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip().lower()
            print("User Question: ",query)
            # Log the incoming query
            logger.info(f"Received query: {query}")
            
            # Process the query and generate a response
            response_data = analyze_query(query)
            
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'type': 'text'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def get_stock_data(request):
    """Get stock data for a specific symbol."""
    if request.method == 'GET':
        try:
            symbol = request.GET.get('symbol', '')
            period = request.GET.get('period', '1mo')  # Default to 1 month
            interval = request.GET.get('interval', '1d')  # Default to daily data
            
            if not symbol:
                return JsonResponse({'status': 'error', 'message': 'Symbol is required'}, status=400)
            
            # Get stock data using yfinance
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period, interval=interval)
            
            # Format the data for TradingView
            data = []
            for index, row in hist.iterrows():
                data.append({
                    'time': int(index.timestamp()) * 1000,  # Convert to milliseconds
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                })
            
            # Get additional info
            info = stock.info
            company_name = info.get('shortName', symbol)
            
            return JsonResponse({
                'status': 'success',
                'symbol': symbol,
                'company_name': company_name,
                'data': data,
                'currency': info.get('currency', 'USD')
            })
        except Exception as e:
            logger.error(f"Error getting stock data: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def analyze_query(query):
    """Analyze the user query and return appropriate response."""
    # Check for direct stock symbol mentions (e.g., "AAPL", "MSFT")
    words = query.split()
    potential_symbols = [word.upper() for word in words if word.isalpha() and 2 <= len(word) <= 5]
    
    # Check if query contains a stock symbol or keywords about stocks
    stock_keywords = ['stock', 'price', 'quote', 'share', 'ticker', 'company']
    is_stock_query = any(keyword in query.lower() for keyword in stock_keywords) or potential_symbols
    
    # Check if query is about a specific stock
    if is_stock_query:
        # If we have potential symbols, try to get data for them
        if potential_symbols:
            try:
                symbol = potential_symbols[0]
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Check if we have valid data
                if 'regularMarketPrice' in info:
                    price = info['regularMarketPrice']
                    prev_close = info.get('previousClose', 0)
                    change = price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0
                    
                    # Extract day range if available
                    day_low = info.get('dayLow', price * 0.98)
                    day_high = info.get('dayHigh', price * 1.02)
                    
                    # Check if query is specifically asking for a chart
                    if 'chart' in query.lower() or 'graph' in query.lower() or 'period' in query.lower():
                        return {
                            'status': 'success',
                            'type': 'chart',
                            'symbol': symbol,
                            'message': f'Here\'s the chart for {symbol}'
                        }
                    
                    # Return stock info with chart symbol for displaying both
                    return {
                        'status': 'success',
                        'type': 'stock_info',
                        'symbol': symbol,
                        'company_name': info.get('shortName', symbol),
                        'price': price,
                        'currency': info.get('currency', 'USD'),
                        'change': change,
                        'change_percent': change_percent,
                        'market_cap': info.get('marketCap', 'N/A'),
                        'volume': info.get('volume', 'N/A'),
                        'day_low': day_low,
                        'day_high': day_high,
                        'chart_symbol': symbol
                    }
            except Exception as e:
                logger.warning(f"Failed to get stock info for {potential_symbols[0]}: {str(e)}")
                return {
                    'status': 'error',
                    'type': 'text',
                    'message': f"Sorry, I couldn't find information for {potential_symbols[0]}. Please try another stock symbol."
                }
    
    # Check if query is about a chart
    if 'chart' in query.lower() or 'graph' in query.lower() or 'period' in query.lower():
        # Extract potential stock symbols
        potential_symbols = [word.upper() for word in words if word.isalpha() and 2 <= len(word) <= 5]
        
        if potential_symbols:
            try:
                symbol = potential_symbols[0]
                # Verify the symbol exists
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Check if we have valid data
                if 'regularMarketPrice' not in info:
                    return {
                        'status': 'error',
                        'type': 'text',
                        'message': f"Sorry, I couldn't find information for {symbol}. Please try another stock symbol."
                    }
                
                # Determine time period if specified
                period = '1mo'  # Default to 1 month
                period_text = "1 month"
                
                if 'day' in query.lower() or '1d' in query.lower() or 'today' in query.lower():
                    period = '1d'
                    period_text = "1 day"
                elif 'week' in query.lower() or '1w' in query.lower() or '7 day' in query.lower():
                    period = '1wk'
                    period_text = "1 week"
                elif 'month' in query.lower() or '1m' in query.lower() or '30 day' in query.lower():
                    period = '1mo'
                    period_text = "1 month"
                elif 'year' in query.lower() or '1y' in query.lower() or '12 month' in query.lower() or 'annual' in query.lower():
                    period = '1y'
                    period_text = "1 year"
                elif '5y' in query.lower() or 'five year' in query.lower() or '5 year' in query.lower():
                    period = '5y'
                    period_text = "5 years"
                
                company_name = info.get('shortName', symbol)
                
                return {
                    'status': 'success',
                    'type': 'chart',
                    'symbol': symbol,
                    'period': period,
                    'message': f"Here's the {period_text} chart for {company_name} ({symbol})"
                }
            except Exception as e:
                logger.warning(f"Failed to get chart for {potential_symbols[0]}: {str(e)}")
                return {
                    'status': 'error',
                    'type': 'text',
                    'message': f"Sorry, I couldn't generate a chart for {potential_symbols[0]}. Please try another stock symbol."
                }
    
    # Check if query is about market trends or analysis
    if ('market' in query.lower() and ('trend' in query.lower() or 'analysis' in query.lower() or 'recent' in query.lower())) or 'explain' in query.lower():
        try:
            # Get data for major indices
            indices = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^FTSE': 'FTSE 100'
            }
            
            market_data = []
            for symbol, name in indices.items():
                index = yf.Ticker(symbol)
                info = index.info
                if 'regularMarketPrice' in info:
                    price = info['regularMarketPrice']
                    prev_close = info.get('previousClose', 0)
                    change = price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0
                    
                    market_data.append({
                        'name': name,
                        'symbol': symbol,
                        'price': price,
                        'change': change,
                        'change_percent': change_percent
                    })
            
            # Determine overall market sentiment
            positive_indices = sum(1 for item in market_data if item['change'] > 0)
            total_indices = len(market_data)
            
            if positive_indices > total_indices / 2:
                sentiment = "The market is generally positive today"
            elif positive_indices < total_indices / 2:
                sentiment = "The market is showing weakness today"
            else:
                sentiment = "The market is showing mixed signals today"
                
            return {
                'status': 'success',
                'type': 'market_overview',
                'data': market_data,
                'message': f'Here is the market overview. {sentiment}.'
            }
        except Exception as e:
            logger.warning(f"Failed to get market overview: {str(e)}")
            return {
                'status': 'error',
                'type': 'text',
                'message': "Sorry, I couldn't retrieve the market overview at this time."
            }
    
    # Default response if we can't categorize the query
    return {
        'status': 'success',
        'type': 'text',
        'message': 'I can help you with stock information, market overviews, and charts. Try asking about a specific stock, the market overview, or requesting a chart.'
    }

def tradingview(request):
    try:
        # Default symbol is MSFT if no symbol is provided
        symbol = request.GET.get('symbol', 'MSFT')
        
        # Remove PSX: prefix for Yahoo Finance if present
        if symbol.startswith('PSX:'):
            yf_symbol = symbol.replace('PSX:', '') + '.KA'
        else:
            yf_symbol = symbol
        
        import yfinance as yf
        stock = yf.Ticker(yf_symbol)
        
        # Get company info
        info = stock.info
        company_info = {
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'description': info.get('longBusinessSummary', ''),
            'website': info.get('website', ''),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
            'employees': info.get('fullTimeEmployees', 0),
        }
        
        # Get financial data
        financial_data = {
            'current_price': info.get('currentPrice', 0),
            'previous_close': info.get('previousClose', 0),
            'open': info.get('open', 0),
            'day_high': info.get('dayHigh', 0),
            'day_low': info.get('dayLow', 0),
            'volume': info.get('volume', 0),
            'avg_volume': info.get('averageVolume', 0),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
        }
        
        # Calculate price change and percentage
        if financial_data['previous_close'] and financial_data['current_price']:
            price_change = financial_data['current_price'] - financial_data['previous_close']
            price_change_percent = (price_change / financial_data['previous_close']) * 100
        else:
            price_change = 0
            price_change_percent = 0
            
        # Get news
        news = stock.news[:5]  # Get latest 5 news items
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        company_info = {}
        financial_data = {}
        price_change = 0
        price_change_percent = 0
        news = []

    context = {
        'page_title': 'Trading View',
        'app_name': 'EK Global',
        'app_alias': 'EK Global',
        'company_info': company_info,
        'financial_data': financial_data,
        'price_change': price_change,
        'price_change_percent': price_change_percent,
        'news': news,
        'current_symbol': symbol,
    }
    return render(request, 'copilot/tradingview.html', context)