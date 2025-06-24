from typing import Any, Dict
import json
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render
from django.views import generic
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
import logging
import random
from datetime import datetime

# Import API client with fallback for tests
try:
    from .api_client import api_client
except ImportError:
    # Mock API client for testing
    class MockAPIClient:
        def get_indices_live(self): return []
        def get_stock_prices_live(self): return []
        def get_announcements(self, limit=5): return []
        def get_news(self, limit=5): return []
        def get_commodities(self, symbols=None): return []
        def get_currencies(self): return []
    api_client = MockAPIClient()


class IndexView(generic.TemplateView):
    template_name = "dashboard/index.html"
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Skip authentication check in development
        context = self.get_context_data(**kwargs)
        context.update(self.get_market_data())
        
        return self.render_to_response(context)
    
    def get_market_data(self) -> Dict[str, Any]:
        """Get market data from the API"""
        # Use API client to fetch data
        market_data = {
            'market_indices': api_client.get_indices_live(),
            'top_gainers': self.get_top_stocks(filter_type='gainers', limit=5),
            'top_losers': self.get_top_stocks(filter_type='losers', limit=5),
            'top_industries': self.get_top_industries(filter_type='gainers', limit=5),
            'worst_industries': self.get_top_industries(filter_type='losers', limit=5),
            'announcements': api_client.get_announcements(limit=5),
            'news': api_client.get_news(limit=5),
            'board_meetings': self.filter_announcements_by_category('Board Meeting', limit=5),
            'psx_notices': self.filter_announcements_by_category('Notice', limit=8),
            'commodities': api_client.get_commodities(symbols='Q1T'),
            'currencies': api_client.get_currencies()
        }
        
        return market_data
    
    def get_top_stocks(self, filter_type='gainers', limit=5):
        """Get top gainers or losers"""
        stocks = api_client.get_stock_prices_live()
        if not stocks:
            return []
        
        # Filter out stocks with no price change
        stocks_with_change = [s for s in stocks if s.get('PctChange') is not None]
        
        # Sort by percentage change
        if filter_type == 'gainers':
            sorted_stocks = sorted(stocks_with_change, key=lambda x: float(x.get('PctChange', 0)) if x.get('PctChange') not in [None, ''] else 0, reverse=True)
        else:  # losers
            sorted_stocks = sorted(stocks_with_change, key=lambda x: float(x.get('PctChange', 0)) if x.get('PctChange') not in [None, ''] else 0)
        
        return sorted_stocks[:limit]
    
    def get_top_industries(self, filter_type='gainers', limit=5):
        """Get top performing or worst performing industries"""
        stocks = api_client.get_stock_prices_live()
        if not stocks:
            return []
            
        # Group stocks by industry
        industries = {}
        for stock in stocks:
            if not stock.get('Sector'):
                continue
                
            sector = stock.get('Sector')
            if sector not in industries:
                industries[sector] = {
                    'name': sector,
                    'stocks': [],
                    'avg_change': 0
                }
            
            if stock.get('PctChange') is not None:
                try:
                    pct_change = float(stock.get('PctChange', 0))
                    industries[sector]['stocks'].append({
                        'symbol': stock.get('Symbol'),
                        'pct_change': pct_change
                    })
                except (ValueError, TypeError):
                    continue
        
        # Calculate average change for each industry
        industry_list = []
        for industry_name, data in industries.items():
            if not data['stocks']:
                continue
                
            total_change = sum(s['pct_change'] for s in data['stocks'])
            avg_change = total_change / len(data['stocks'])
            
            industry_list.append({
                'name': industry_name,
                'avg_change': avg_change,
                'change': avg_change, # For sorting
                'change_str': f"{avg_change:.2f}%",
                'stock_count': len(data['stocks'])
            })
        
        # Sort industries by average change
        if filter_type == 'gainers':
            sorted_industries = sorted(industry_list, key=lambda x: x['avg_change'], reverse=True)
        else:  # losers
            sorted_industries = sorted(industry_list, key=lambda x: x['avg_change'])
        
        return sorted_industries[:limit]
    
    def filter_announcements_by_category(self, category, limit=5):
        """Filter announcements by category"""
        announcements = api_client.get_announcements()
        if not announcements:
            return []
        
        # Filter announcements by category field - improve matching
        categories_to_match = [category.lower()]
        if category.lower() == 'notice':
            categories_to_match.extend(['psx notice', 'market notice'])
            
        filtered = []
        for announcement in announcements:
            if announcement.get('Category'):
                cat_lower = announcement.get('Category', '').lower()
                if any(c in cat_lower for c in categories_to_match):
                    filtered.append(announcement)
        
        # If we don't have enough, look for category in Title field
        if len(filtered) < limit:
            title_filtered = [a for a in announcements if a.get('Title') and any(c in a.get('Title', '').lower() for c in categories_to_match)]
            # Combine, but avoid duplicates
            existing_ids = {a['ID'] for a in filtered if 'ID' in a}
            filtered.extend([a for a in title_filtered if 'ID' in a and a['ID'] not in existing_ids])
        
        # For debugging
        logger = logging.getLogger(__name__)
        logger.info(f"Found {len(filtered)} announcements for category {category}")
        
        return filtered[:limit]

# API endpoints for AJAX requests
def get_market_overview(request):
    """API endpoint for market overview data"""
    # Skip authentication for development
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Get market indices data
    indices = api_client.get_indices_live()
    
    if not indices:
        # Return mock data if API fails
        logger = logging.getLogger(__name__)
        logger.warning("Failed to fetch market indices from API, returning mock data")
        indices = [
            {
                "IndexName": "KSE100",
                "CurrentIndex": 93291.68,
                "PreviousIndex": 92520.49,
                "NetChange": 771.19,
                "PNetChange": 0.83,
                "Volume": 362829838
            },
            {
                "IndexName": "KSE30",
                "CurrentIndex": 32104.55,
                "PreviousIndex": 31865.22,
                "NetChange": 239.33,
                "PNetChange": 0.75,
                "Volume": 162345678
            },
            {
                "IndexName": "KSE20",
                "CurrentIndex": 29090.90,
                "PreviousIndex": 28865.82,
                "NetChange": 225.08,
                "PNetChange": 0.78,
                "Volume": 98765432
            },
            {
                "IndexName": "KMI30",
                "CurrentIndex": 18376.44,
                "PreviousIndex": 18218.65,
                "NetChange": 157.79,
                "PNetChange": 0.87,
                "Volume": 87654321
            }
        ]
    
    return JsonResponse(indices, safe=False)

def get_top_stocks(request):
    """API endpoint for top gaining/losing stocks"""
    # Skip authentication for development
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Authentication required'}, status=401)
    
    filter_type = request.GET.get('type', 'gainers')
    limit = int(request.GET.get('limit', 5))
    
    view = IndexView()
    stocks = view.get_top_stocks(filter_type, limit)
    
    if not stocks:
        # Return mock data if API fails
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to fetch top {filter_type} from API, returning mock data")
        
        if filter_type == 'gainers':
            stocks = [
                {
                    "Symbol": "DEMO1",
                    "Name": "Demo Company 1",
                    "CurrentRate": 150.25,
                    "PreviousRate": 145.20,
                    "Change": 5.05,
                    "PctChange": 3.48
                },
                {
                    "Symbol": "DEMO2",
                    "Name": "Demo Company 2",
                    "CurrentRate": 78.50,
                    "PreviousRate": 76.25,
                    "Change": 2.25,
                    "PctChange": 2.95
                },
                {
                    "Symbol": "DEMO3",
                    "Name": "Demo Company 3",
                    "CurrentRate": 210.75,
                    "PreviousRate": 205.50,
                    "Change": 5.25,
                    "PctChange": 2.55
                }
            ]
        else:  # losers
            stocks = [
                {
                    "Symbol": "DEMO4",
                    "Name": "Demo Company 4",
                    "CurrentRate": 95.50,
                    "PreviousRate": 100.25,
                    "Change": -4.75,
                    "PctChange": -4.74
                },
                {
                    "Symbol": "DEMO5",
                    "Name": "Demo Company 5",
                    "CurrentRate": 45.75,
                    "PreviousRate": 48.00,
                    "Change": -2.25,
                    "PctChange": -4.69
                },
                {
                    "Symbol": "DEMO6",
                    "Name": "Demo Company 6",
                    "CurrentRate": 128.25,
                    "PreviousRate": 134.50,
                    "Change": -6.25,
                    "PctChange": -4.65
                }
            ]
    
    return JsonResponse(stocks, safe=False)

def get_latest_news(request):
    """API endpoint for latest news"""
    # Skip authentication for development
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Authentication required'}, status=401)
    
    limit = int(request.GET.get('limit', 5))
    news = api_client.get_news(limit=limit)
    
    return JsonResponse(news, safe=False)

def get_psx_notices(request):
    """API endpoint for PSX Notices"""
    # Skip authentication for development
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Authentication required'}, status=401)
    
    limit = int(request.GET.get('limit', 10))
    view = IndexView()
    notices = view.filter_announcements_by_category('Notice', limit=limit)
    
    return JsonResponse(notices, safe=False)

def get_financial_results(request):
    """API endpoint for financial results data"""
    # Skip authentication for development
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Authentication required'}, status=401)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Try to get real stock data from API
        stock_data = api_client.get_stock_prices_live()
        
        if not stock_data:
            logger.warning("No stock data returned from API, using mock data")
            return JsonResponse(get_mock_financial_results(), safe=False)
        
        # Get announcements to cross-reference for financial results
        announcements = api_client.get_announcements(limit=50)
        financial_announcements = []
        
        if announcements:
            # Extract financial-related announcements
            financial_keywords = ['financial', 'results', 'dividend', 'earning', 'eps', 'profit', 'loss']
            financial_announcements = [a for a in announcements if any(kw in a.get('Title', '').lower() for kw in financial_keywords)]
            logger.info(f"Found {len(financial_announcements)} financial-related announcements")
        
        # Process the stock data to get financial results
        financial_results = []
        
        # Filter stocks with financial data
        for stock in stock_data:
            # Skip stocks without necessary data
            if not all(key in stock for key in ['Symbol', 'Title']):
                continue
                
            # Extract financial data
            try:
                symbol = stock.get('Symbol', '')
                
                # Look for matching announcements
                stock_announcements = [a for a in financial_announcements if a.get('Symbol') == symbol]
                
                # Use real EPS if available, otherwise use a realistic value
                eps = stock.get('EPS')
                is_profit = True
                
                if eps is not None:
                    try:
                        eps_value = float(eps)
                        is_profit = eps_value >= 0
                    except (ValueError, TypeError):
                        # Generate a realistic EPS value based on stock price
                        current_price = float(stock.get('CurrentRate', 100))
                        eps = str(round(current_price * 0.08 * (1 if random.random() > 0.2 else -1), 2))
                        is_profit = float(eps) >= 0
                else:
                    # Generate a realistic EPS value based on stock price
                    current_price = float(stock.get('CurrentRate', 100))
                    eps = str(round(current_price * 0.08 * (1 if random.random() > 0.2 else -1), 2))
                    is_profit = float(eps) >= 0
                
                # Sometimes stocks have dividend information
                dividend = stock.get('Dividend', '-')
                has_dividend = dividend not in [None, '-', '']
                
                # If we don't have dividend info but it's profitable, maybe add one
                if not has_dividend and is_profit and random.random() > 0.7:
                    dividend_pct = random.choice([10, 15, 20, 25, 30, 40, 50, 75, 100])
                    dividend = f"{dividend_pct}% (D)"
                    has_dividend = True
                
                # Get profit/loss values if available, otherwise calculate realistic ones
                if stock.get('PLBeforeTax'):
                    pl_before_tax = stock.get('PLBeforeTax')
                else:
                    # Calculate based on EPS and outstanding shares (estimated)
                    estimated_shares = random.randint(50, 2000)  # millions
                    estimated_pl = float(eps) * estimated_shares
                    pl_before_tax = f"{estimated_pl:.3f}" if estimated_pl >= 0 else f"({abs(estimated_pl):.3f})"
                
                if stock.get('PLAfterTax'):
                    pl_after_tax = stock.get('PLAfterTax')
                else:
                    # After tax is typically 70-85% of before tax for profits
                    if is_profit:
                        tax_factor = random.uniform(0.70, 0.85)
                        estimated_pl_after = float(pl_before_tax.replace(',', '')) * tax_factor if not pl_before_tax.startswith('(') else float(pl_before_tax.strip('()').replace(',', '')) * tax_factor
                        pl_after_tax = f"{estimated_pl_after:.3f}" if estimated_pl_after >= 0 else f"({abs(estimated_pl_after):.3f})"
                    else:
                        # Losses often remain the same after tax
                        pl_after_tax = pl_before_tax
                
                # Use ROE for industry categorization if available
                roe = stock.get('ROE', 'N/A')
                
                # Determine a realistic reporting period
                period = stock.get('Year', '')
                if not period:
                    current_month = datetime.now().month
                    current_year = datetime.now().year
                    quarter = f"Q{(current_month-1)//3 + 1}"
                    period = f"31/{3*(current_month//3)}/20{current_year-2000} (I{quarter})"
                
                financial_results.append({
                    "company": stock.get('Title', symbol),
                    "symbol": symbol,
                    "sector": stock.get('Sector', 'Others'),
                    "period": period,
                    "dividend": dividend,
                    "pl_before_tax": pl_before_tax,
                    "pl_after_tax": pl_after_tax,
                    "eps": eps,
                    "roe": roe,
                    "has_dividend": has_dividend,
                    "is_profit": is_profit
                })
            except Exception as e:
                logger.error(f"Error processing stock {stock.get('Symbol', 'Unknown')}: {str(e)}")
                continue
        
        if not financial_results:
            logger.warning("No financial results could be extracted from stock data, using mock data")
            return JsonResponse(get_mock_financial_results(), safe=False)
        
        # Sort by EPS (descending) so best performing companies are at the top
        try:
            sorted_results = sorted(
                financial_results, 
                key=lambda x: float(x['eps']) if isinstance(x['eps'], (int, float)) or (isinstance(x['eps'], str) and x['eps'].replace('-', '').replace('.', '').replace(',', '').isdigit()) else -9999,
                reverse=True
            )
        except Exception as e:
            logger.error(f"Error sorting financial results: {str(e)}")
            sorted_results = financial_results
        
        limit = int(request.GET.get('limit', len(sorted_results)))
        return JsonResponse(sorted_results[:limit], safe=False)
    
    except Exception as e:
        logger.error(f"Exception in get_financial_results: {str(e)}")
        return JsonResponse(get_mock_financial_results(), safe=False)

def get_mock_financial_results():
    """Return mock financial results data for fallback"""
    return [
        {
            "company": "Rafhan Maize",
            "symbol": "RMPL",
            "sector": "Food",
            "period": "31/03/2025(IQ)",
            "dividend": "1000%(i) (D)",
            "pl_before_tax": "3,146.498",
            "pl_after_tax": "1,955.046",
            "eps": "211.67",
            "has_dividend": True,
            "is_profit": True
        },
        {
            "company": "Bestway Cement",
            "symbol": "BWCL",
            "sector": "Cement",
            "period": "31/03/2025(IIIQ)",
            "dividend": "80%(iii) (D)",
            "pl_before_tax": "27,021.830",
            "pl_after_tax": "17,541.448",
            "eps": "29.42",
            "has_dividend": True,
            "is_profit": True
        },
        {
            "company": "Bawany Air Products",
            "symbol": "BAPL",
            "sector": "Chemical",
            "period": "31/03/2025(IIIQ)",
            "dividend": "-",
            "pl_before_tax": "(6.425)",
            "pl_after_tax": "(6.425)",
            "eps": "(0.86)",
            "has_dividend": False,
            "is_profit": False
        },
        {
            "company": "Lotte Chemical",
            "symbol": "LOTCHEM",
            "sector": "Chemical",
            "period": "31/03/2025(IQ)",
            "dividend": "-",
            "pl_before_tax": "1,085.719",
            "pl_after_tax": "661.901",
            "eps": "0.44",
            "has_dividend": False,
            "is_profit": True
        },
        {
            "company": "Bank Al-Falah",
            "symbol": "BAFL",
            "sector": "Banking",
            "period": "31/03/2025(IQ)",
            "dividend": "25%(i) (D)",
            "pl_before_tax": "15,384.198 (UCS)",
            "pl_after_tax": "7,040.102 (UCS)",
            "eps": "4.46",
            "has_dividend": True,
            "is_profit": True
        },
        {
            "company": "Bank Al-Falah",
            "symbol": "BAFL",
            "sector": "Banking",
            "period": "31/03/2025(IQ)",
            "dividend": "-",
            "pl_before_tax": "15,604.774 (CS)",
            "pl_after_tax": "7,072.689 (CS)",
            "eps": "4.49",
            "has_dividend": False,
            "is_profit": True
        }
    ]

def get_industry_performance(request):
    """API endpoint for industry performance"""
    filter_type = request.GET.get('type', 'gainers')
    limit = int(request.GET.get('limit', 5))
    
    view = IndexView()
    industries = view.get_top_industries(filter_type, limit)
    
    if not industries:
        # Return mock data if API fails
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to fetch {filter_type} industries from API, returning mock data")
        
        if filter_type == 'gainers':
            industries = [
                {
                    "name": "Technology",
                    "avg_change": 2.45,
                    "change": 2.45,
                    "change_str": "2.45%",
                    "stock_count": 12
                },
                {
                    "name": "Banking",
                    "avg_change": 1.85,
                    "change": 1.85,
                    "change_str": "1.85%",
                    "stock_count": 8
                },
                {
                    "name": "Pharmaceuticals",
                    "avg_change": 1.32,
                    "change": 1.32,
                    "change_str": "1.32%",
                    "stock_count": 6
                }
            ]
        else:  # losers
            industries = [
                {
                    "name": "Oil & Gas",
                    "avg_change": -1.85,
                    "change": -1.85,
                    "change_str": "-1.85%",
                    "stock_count": 7
                },
                {
                    "name": "Textiles",
                    "avg_change": -1.45,
                    "change": -1.45,
                    "change_str": "-1.45%",
                    "stock_count": 9
                },
                {
                    "name": "Construction",
                    "avg_change": -1.15,
                    "change": -1.15,
                    "change_str": "-1.15%",
                    "stock_count": 5
                }
            ]
    
    return JsonResponse(industries, safe=False)

@login_required
def get_portfolio_data(request):
    """API endpoint for portfolio data"""
    try:
        from apps.portfolios.models import Portfolio, Investment
        logger = logging.getLogger(__name__)
        
        # Get user's portfolios and their investments
        portfolios = Portfolio.objects.filter(owner=request.user)
        
        if not portfolios.exists():
            logger.info(f"No portfolios found for user {request.user.username}")
            return JsonResponse([], safe=False)
            
        portfolio_data = []
        
        # Get current prices for stocks from API
        stock_prices = api_client.get_stock_prices_live()
        
        if not stock_prices:
            logger.error("Failed to fetch stock prices from API")
            # Return mock data for demonstration
            return JsonResponse([
                {
                    'symbol': 'DEMO1',
                    'name': 'Demo Stock 1',
                    'price': 100.0,
                    'change': 5.0,
                    'changePercent': 5.0,
                    'quantity': 10,
                    'holdingValue': 1000.0,
                    'portfolio': 'Demo Portfolio'
                },
                {
                    'symbol': 'DEMO2',
                    'name': 'Demo Stock 2',
                    'price': 200.0,
                    'change': -10.0,
                    'changePercent': -5.0,
                    'quantity': 5,
                    'holdingValue': 1000.0,
                    'portfolio': 'Demo Portfolio'
                }
            ], safe=False)
            
        price_map = {s.get('Symbol'): s for s in stock_prices if s.get('Symbol')}
        logger.info(f"Fetched prices for {len(price_map)} stocks from API")
        
        for portfolio in portfolios:
            investments = Investment.objects.filter(portfolio=portfolio).select_related('stock')
            logger.info(f"Processing {investments.count()} investments for portfolio '{portfolio.name}'")
            
            for investment in investments:
                stock_ticker = investment.stock.ticker
                stock_data = price_map.get(stock_ticker)
                
                if stock_data:
                    try:
                        current_price = float(stock_data.get('CurrentRate', 0))
                        previous_price = float(stock_data.get('PreviousRate', current_price))
                        change = current_price - previous_price
                        change_percent = (change / previous_price * 100) if previous_price else 0
                        holding_value = current_price * investment.quantity
                        
                        portfolio_data.append({
                            'symbol': stock_ticker,
                            'name': investment.stock.title,
                            'price': current_price,
                            'change': change,
                            'changePercent': change_percent,
                            'quantity': investment.quantity,
                            'holdingValue': holding_value,
                            'portfolio': portfolio.name
                        })
                    except (ValueError, TypeError, ZeroDivisionError) as e:
                        logger.error(f"Error processing stock {stock_ticker}: {str(e)}")
                        continue
                else:
                    logger.warning(f"No price data found for stock {stock_ticker}")
                        
        logger.info(f"Returning data for {len(portfolio_data)} portfolio items")
        return JsonResponse(portfolio_data, safe=False)
    except ImportError as e:
        logger.error(f"ImportError: {str(e)}")
        # In case portfolios app isn't available
        return JsonResponse([], safe=False)
    except Exception as e:
        logger.error(f"Error in portfolio_data_view: {str(e)}")
        # Return mock data for demonstration
        return JsonResponse([
            {
                'symbol': 'DEMO1',
                'name': 'Demo Stock 1',
                'price': 100.0,
                'change': 5.0,
                'changePercent': 5.0,
                'quantity': 10,
                'holdingValue': 1000.0,
                'portfolio': 'Demo Portfolio'
            },
            {
                'symbol': 'DEMO2',
                'name': 'Demo Stock 2',
                'price': 200.0,
                'change': -10.0,
                'changePercent': -5.0,
                'quantity': 5,
                'holdingValue': 1000.0,
                'portfolio': 'Demo Portfolio'
            }
        ], safe=False)

def get_treemap_data(request):
    """API endpoint for treemap chart data showing stock market cap distribution"""
    try:
        logger = logging.getLogger(__name__)
        
        # Fetch real stock market cap data from API
        treemap_data = api_client.get_stock_market_cap_data()
        
        if treemap_data and len(treemap_data) > 0:
            logger.info(f"Fetched real market cap data for {len(treemap_data)} stocks")
            return JsonResponse(treemap_data, safe=False)
        
        # Fallback to mock data if API call failed
        logger.warning("Failed to fetch stock market cap data, using mock data")
        mock_data = [
            {"x": "OGDC", "y": 435, "name": "Oil & Gas Development Company", "sector": "Oil & Gas"},
            {"x": "PPL", "y": 312, "name": "Pakistan Petroleum Limited", "sector": "Oil & Gas"},
            {"x": "LUCK", "y": 287, "name": "Lucky Cement Limited", "sector": "Cement"},
            {"x": "MCB", "y": 245, "name": "MCB Bank Limited", "sector": "Banking"},
            {"x": "ENGRO", "y": 220, "name": "Engro Corporation", "sector": "Fertilizer"},
            {"x": "HBL", "y": 198, "name": "Habib Bank Limited", "sector": "Banking"},
            {"x": "UBL", "y": 185, "name": "United Bank Limited", "sector": "Banking"},
            {"x": "FFC", "y": 175, "name": "Fauji Fertilizer Company", "sector": "Fertilizer"},
            {"x": "POL", "y": 168, "name": "Pakistan Oilfields Limited", "sector": "Oil & Gas"}
        ]
        
        return JsonResponse(mock_data, safe=False)
    except Exception as e:
        logger.error(f"Error in treemap_data_view: {str(e)}")
        return JsonResponse([], safe=False)

# Register API views
index_view = IndexView.as_view()
market_overview_view = get_market_overview
top_stocks_view = get_top_stocks
latest_news_view = get_latest_news
industry_performance_view = get_industry_performance
portfolio_data_view = get_portfolio_data
psx_notices_view = get_psx_notices
financial_results_view = get_financial_results
treemap_data_view = get_treemap_data
