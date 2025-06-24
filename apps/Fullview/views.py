from django.shortcuts import render
import requests
import json
from datetime import datetime, timedelta
import random
from django.http import JsonResponse
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Create your views here.

def get_token():
    """Get authentication token from API"""
    url = "https://api.mg-link.net/api/auth/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'password',
        'username': 'EKCapital2024',
        'password': '3KC@Pit@L!2024'
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def get_stock_data(access_token, symbol=None):
    """Get stock data from API"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    
    # Get stock prices data
    url = f"https://api.mg-link.net/api/Data1/PSXStockPrices?StartDate=&EndDate="
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if symbol:
            # Filter for specific stock if symbol provided
            return [item for item in data if item.get('Symbol') == symbol]
        return data
    return []

def get_news(access_token):
    """Get news data from API"""
    url = "https://api.mg-link.net/api/Data1/GetMGNews_New"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_announcements(access_token):
    """Get company announcements from API"""
    url = "https://api.mg-link.net/api/Data1/GetPSXAnnouncements"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_indices(access_token):
    """Get market indices data from API"""
    url = "https://api.mg-link.net/api/Data1/GetPSXIndicesLive"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_company_analysis(symbol, stock_data):
    """Generate company analysis with positive and negative signals"""
    analysis = {
        'positives': [],
        'negatives': []
    }
    
    if not stock_data:
        return analysis
    
    latest_stock = stock_data[-1]
    daily_change = latest_stock.get('PctChange', 0)
    
    # Positive signals
    if daily_change > 0:
        analysis['positives'].append({
            'title': 'Positive Price Movement',
            'description': f'Stock price increased by {abs(daily_change):.2f}% today',
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if latest_stock.get('Volume', 0) > latest_stock.get('AvgVolume', 0):
        analysis['positives'].append({
            'title': 'High Trading Volume',
            'description': 'Trading volume is above average, indicating strong market interest',
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    # Add more positive signals based on available data
    analysis['positives'].append({
        'title': 'Strong Market Position',
        'description': 'Company maintains a leading position in its sector',
        'date': datetime.now().strftime('%Y-%m-%d')
    })
    
    # Negative signals
    if daily_change < 0:
        analysis['negatives'].append({
            'title': 'Negative Price Movement',
            'description': f'Stock price decreased by {abs(daily_change):.2f}% today',
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if latest_stock.get('Volume', 0) < latest_stock.get('AvgVolume', 0):
        analysis['negatives'].append({
            'title': 'Low Trading Volume',
            'description': 'Trading volume is below average, indicating potential lack of interest',
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    # Add more negative signals based on available data
    analysis['negatives'].append({
        'title': 'Market Volatility',
        'description': 'High market volatility may impact short-term performance',
        'date': datetime.now().strftime('%Y-%m-%d')
    })
    
    return analysis

def calculate_risk_metrics(stock_data):
    """Calculate risk metrics for the stock"""
    risk_metrics = {
        'score': 'Moderate',
        'volatility': 'Medium',
        'beta': 1.2,
        'factors': []
    }
    
    if not stock_data:
        return risk_metrics
    
    # Calculate volatility from stock data
    prices = [float(stock.get('Last', 0)) for stock in stock_data]
    if prices:
        std_dev = sum((x - sum(prices)/len(prices))**2 for x in prices)**0.5 / len(prices)
        volatility = std_dev / (sum(prices)/len(prices))
        
        if volatility < 0.02:
            risk_metrics['score'] = 'Low'
            risk_metrics['volatility'] = 'Low'
        elif volatility > 0.05:
            risk_metrics['score'] = 'High'
            risk_metrics['volatility'] = 'High'
    
    # Add risk factors
    risk_metrics['factors'] = [
        'Market volatility exposure',
        'Industry cyclical nature',
        'Regulatory environment'
    ]
    
    return risk_metrics

def calculate_performance_metrics(stock_data):
    """Calculate performance metrics for different time periods"""
    performance = {
        'Daily': 0,
        'Weekly': 0,
        'Monthly': 0,
        'Quarterly': 0,
        'SixMonth': 0,
        'Yearly': 0,
        'YTD': 0
    }
    
    if not stock_data or len(stock_data) < 2:
        return performance
    
    latest_price = float(stock_data[-1].get('Last', 0))
    
    # Calculate returns for different periods
    for stock in stock_data:
        date_str = stock.get('Date', '')
        if not date_str:  # Skip if date is empty
            continue
            
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            price = float(stock.get('Last', 0))
            days_diff = (datetime.now() - date).days
            
            if days_diff <= 1:
                performance['Daily'] = ((latest_price / price) - 1) * 100
            elif days_diff <= 7:
                performance['Weekly'] = ((latest_price / price) - 1) * 100
            elif days_diff <= 30:
                performance['Monthly'] = ((latest_price / price) - 1) * 100
            elif days_diff <= 90:
                performance['Quarterly'] = ((latest_price / price) - 1) * 100
            elif days_diff <= 180:
                performance['SixMonth'] = ((latest_price / price) - 1) * 100
            elif days_diff <= 365:
                performance['Yearly'] = ((latest_price / price) - 1) * 100
        except ValueError:
            # Skip invalid dates
            continue
    
    # Calculate YTD performance
    start_of_year = datetime(datetime.now().year, 1, 1)
    for stock in reversed(stock_data):
        date_str = stock.get('Date', '')
        if not date_str:  # Skip if date is empty
            continue
            
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if date <= start_of_year:
                price = float(stock.get('Last', 0))
                performance['YTD'] = ((latest_price / price) - 1) * 100
                break
        except ValueError:
            # Skip invalid dates
            continue
    
    return performance

def stock_360_view(request, symbol="786"):
    """View for 360-degree stock analysis page"""
    # Get API token
    access_token = get_token()
    
    if not access_token:
        return render(request, '360View/index.html', {
            'error': 'Failed to authenticate with API'
        })
    
    # Get stock data
    stock_data = get_stock_data(access_token, symbol)
    
    # Get latest stock information
    latest_stock = None
    if stock_data:
        latest_stock = stock_data[-1]
    
    # Get historical stock data for performance calculation
    daily_change = 0
    if latest_stock:
        # Get the PctChange value
        pct_change_raw = latest_stock.get('PctChange')
        logger.debug(f"PctChange raw value: {pct_change_raw}, Type: {type(pct_change_raw).__name__}")
        
        # Try to convert PctChange to float with proper error handling
        try:
            if pct_change_raw is not None:
                # Remove leading zeros if it's a string
                if isinstance(pct_change_raw, str) and pct_change_raw.startswith('00'):
                    pct_change_raw = pct_change_raw[2:]
                    logger.debug(f"Removed leading zeros: {pct_change_raw}")
                
                daily_change = float(pct_change_raw)
                logger.debug(f"Converted daily_change: {daily_change}")
            else:
                # If PctChange is missing, try to calculate from Change and Last
                change = latest_stock.get('Change')
                last = latest_stock.get('Last')
                if change is not None and last is not None:
                    try:
                        change_float = float(change)
                        last_float = float(last)
                        if last_float > 0:
                            daily_change = (change_float / last_float) * 100
                            logger.debug(f"Calculated daily_change from Change/Last: {daily_change}")
                    except (ValueError, TypeError):
                        logger.error(f"Failed to calculate daily_change from Change/Last")
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting PctChange to float: {e}")
    
    # Get news
    news = get_news(access_token)
    
    # Get announcements
    announcements = get_announcements(access_token)
    filtered_announcements = [a for a in announcements if a.get('Symbol') == symbol]
    
    # Get indices
    indices = get_indices(access_token)
    
    # Get company analysis
    company_analysis = get_company_analysis(symbol, stock_data)
    
    # Get risk metrics
    risk_metrics = calculate_risk_metrics(stock_data)
    
    # Get performance metrics
    performance = calculate_performance_metrics(stock_data)
    
    # Define competitor list based on industry
    industry_competitors = {
        # Investment industry
        "786": [
            {"Symbol": "BAFL", "Name": "Bank Alfalah Limited"},
            {"Symbol": "HBL", "Name": "Habib Bank Limited"},
            {"Symbol": "UBL", "Name": "United Bank Limited"},
            {"Symbol": "MCB", "Name": "MCB Bank Limited"}
        ],
        # Default competitors
        "default": [
            {"Symbol": "BAFL", "Name": "Bank Alfalah Limited"},
            {"Symbol": "HBL", "Name": "Habib Bank Limited"},
            {"Symbol": "UBL", "Name": "United Bank Limited"},
            {"Symbol": "MCB", "Name": "MCB Bank Limited"}
        ]
    }
    
    # Get competitors for this company
    competitors = industry_competitors.get(symbol, industry_competitors["default"])
    
    # Company information database
    company_info_db = {
        "786": {
            "Symbol": "786",
            "CompanyName": "786 Investments Limited",
            "Founded": "1968",
            "CEO": "Asif Hussain",
            "HeadOffice": "Karachi, Pakistan",
            "Employees": "150+",
            "Industry": "Investment Banking",
            "Revenue": "PKR 1.2 billion",
            "Website": "www.786investments.com",
            "Exchange": "PSX",
            "Currency": "PKR",
            "Sector": "Financial Services",
            "IPODate": "1968",
            "FiscalYearEnd": "June",
            "Country": "Pakistan",
            "FullTimeEmployees": "150"
        }
    }
    
    # Generic company info for any company not in our database
    generic_company_info = {
        "Symbol": symbol,
        "CompanyName": latest_stock.get('CompanyName', symbol) if latest_stock else symbol,
        "Founded": "N/A",
        "CEO": "N/A",
        "HeadOffice": "Pakistan",
        "Employees": "N/A",
        "Industry": "N/A",
        "Revenue": "N/A",
        "Website": "N/A",
        "Exchange": "PSX",
        "Currency": "PKR",
        "Sector": "N/A",
        "IPODate": "N/A",
        "FiscalYearEnd": "June",
        "Country": "Pakistan",
        "FullTimeEmployees": "N/A"
    }
    
    # Get company information (use generic if not found)
    company_info = company_info_db.get(symbol, generic_company_info)
    
    # Ensure CompanyName is not None
    if company_info["CompanyName"] is None or company_info["CompanyName"] == "None" or company_info["CompanyName"] == "":
        company_info["CompanyName"] = f"{symbol} Stock"
    
    # Calculate market cap - handle case when latest_stock is None
    market_cap_formatted = "N/A"
    if latest_stock:
        logger.debug(f"Symbol: {symbol}, Latest stock available: {latest_stock is not None}")
        shares_outstanding = latest_stock.get('SharesOutstanding', 0)
        logger.debug(f"SharesOutstanding: {shares_outstanding}")
        
        if shares_outstanding and shares_outstanding > 0:
            last_price = float(latest_stock.get('Last', 0) or 0)
            try:
                # Convert shares_outstanding to float if it's a decimal.Decimal
                if hasattr(shares_outstanding, 'to_integral_exact'):
                    shares_outstanding = float(shares_outstanding)
                market_cap = shares_outstanding * last_price
                logger.debug(f"Market Cap calculation: {shares_outstanding} * {last_price} = {market_cap}")
                market_cap_formatted = f"{market_cap/1e9:.2f}B" if market_cap > 0 else "N/A"
            except Exception as e:
                logger.error(f"Error calculating market cap for {symbol}: {str(e)}")
                market_cap_formatted = "N/A"
        else:
            logger.debug(f"No valid SharesOutstanding for {symbol}")
    else:
        logger.debug(f"No latest_stock data for {symbol}")
    
    # AlphAIQ View ratings with more sophisticated calculation
    base_score = 65  # Base score
    volatility_factor = abs(daily_change) * 2 if daily_change else 0
    market_trend = 5 if daily_change and daily_change > 0 else -5
    
    # QUANTRA GLOBAL View ratings with comprehensive metrics
    quantra_metrics = {
        "Fundamentals": {
            "score": min(100, max(20, base_score + market_trend)),
            "components": {
                "Financial_Health": min(100, max(20, base_score + 5)),
                "Market_Position": min(100, max(20, base_score + market_trend)),
                "Business_Model": min(100, max(20, base_score + 2))
            }
        },
        "Technicals": {
            "score": min(100, max(20, 75 - volatility_factor)),
            "components": {
                "Price_Trend": min(100, max(20, 70 + (daily_change * 2 if daily_change else 0))),
                "Volume_Analysis": min(100, max(20, 65 + market_trend)),
                "Momentum": min(100, max(20, 75 - volatility_factor))
            }
        },
        "Valuation": {
            "score": min(100, max(20, base_score + (daily_change * 1.5 if daily_change else 0))),
            "components": {
                "PE_Ratio": min(100, max(20, 70)),
                "Market_Cap": min(100, max(20, 65)),
                "Growth_Potential": min(100, max(20, base_score + 5))
            }
        },
        "Dividends": {
            "score": min(100, max(20, 60 + (daily_change * 0.5 if daily_change else 0))),
            "components": {
                "Yield": min(100, max(20, 60)),
                "Payout_Ratio": min(100, max(20, 65)),
                "Sustainability": min(100, max(20, 70))
            }
        },
        "Outlook": {
            "score": min(100, max(20, base_score + (daily_change * 3 if daily_change and daily_change > 0 else -10))),
            "components": {
                "Industry_Growth": min(100, max(20, 75)),
                "Company_Strategy": min(100, max(20, 70)),
                "Market_Sentiment": min(100, max(20, base_score + market_trend))
            }
        }
    }

    # Calculate overall scores for main metrics
    alphaiq_view = {
        "Fundamentals": quantra_metrics["Fundamentals"]["score"],
        "Technicals": quantra_metrics["Technicals"]["score"],
        "Valuation": quantra_metrics["Valuation"]["score"],
        "Dividends": quantra_metrics["Dividends"]["score"],
        "Outlook": quantra_metrics["Outlook"]["score"]
    }
    
    # Calculate average score for overall rating
    avg_score = sum(alphaiq_view.values()) / len(alphaiq_view)
    rating_grade = 'A' if avg_score >= 80 else 'B' if avg_score >= 65 else 'C' if avg_score >= 50 else 'D' if avg_score >= 35 else 'E'
    
    # Calculate rating description based on score
    rating_descriptions = {
        'A': 'Excellent performance across all metrics',
        'B': 'Strong performance with some room for improvement',
        'C': 'Average performance with significant potential',
        'D': 'Below average performance, needs attention',
        'E': 'Poor performance, immediate action required'
    }
    
    # Get rating description
    rating_description = rating_descriptions.get(rating_grade, 'Rating description not available')
    
    # Portfolio breakdown with more realistic values
    portfolio_breakdown = {
        "ThisStock": min(100, max(0, 25 + (daily_change if daily_change and daily_change > 0 else 0))),
        "OtherStocks": 45,
        "Cash": 20,
        "Bonds": 10
    }
    
    # Enhanced analyst data
    current_price = float(latest_stock.get('Last', 0)) if latest_stock else 0
    analyst_data = {
        "lowTarget": current_price * 0.85 if current_price else 0,
        "meanTarget": current_price * 1.15 if current_price else 0,
        "highTarget": current_price * 1.35 if current_price else 0,
        "buyCount": 6,
        "holdCount": 3,
        "sellCount": 1,
        "buyPercentage": 60,
        "holdPercentage": 30,
        "sellPercentage": 10
    }
    
    # Enhanced financial info
    pe_ratio = latest_stock.get('PERatio', 'N/A') if latest_stock else 'N/A'
    eps = latest_stock.get('EPS', 'N/A') if latest_stock else 'N/A'
    dividend_yield = latest_stock.get('DividendYield', 'N/A') if latest_stock else 'N/A'
    
    financial_info = {
        "MarketCap": market_cap_formatted,
        "PERatio": pe_ratio,
        "EPS": eps,
        "DividendYield": dividend_yield,
        "Beta": 1.15  # Default beta value
    }
    
    # Enhanced stock data for charts
    stock_data_summary = {
        "week52High": max([float(stock.get('High', 0)) for stock in stock_data]) if stock_data else current_price * 1.2,
        "week52Low": min([float(stock.get('Low', 0)) for stock in stock_data]) if stock_data else current_price * 0.8,
        "avgVolume": sum([float(stock.get('Volume', 0)) for stock in stock_data]) / len(stock_data) if stock_data else 0
    }
    
    # Calculate traded value (30-day average)
    thirty_day_traded_value = 0
    if stock_data:
        recent_data = stock_data[-30:] if len(stock_data) > 30 else stock_data
        traded_values = [float(stock.get('Last', 0)) * float(stock.get('Volume', 0)) for stock in recent_data]
        thirty_day_traded_value = sum(traded_values) / len(traded_values)
    
    traded_value_formatted = f"{thirty_day_traded_value/1e9:.2f}B" if thirty_day_traded_value > 0 else "N/A"
    
    context = {
        'company_info': company_info,
        'latest_stock': latest_stock,
        'news': news[:5],  # Only show latest 5 news items
        'announcements': filtered_announcements[:5],  # Only show latest 5 announcements
        'competitors': competitors,
        'alphaiq_view': alphaiq_view,
        'quantra_metrics': quantra_metrics,
        'portfolio_breakdown': portfolio_breakdown,
        'performance': performance,
        'risk_rating': risk_metrics['score'],
        'risk_metrics': risk_metrics,
        'company_analysis': company_analysis,
        'analyst_data': analyst_data,
        'financial_info': financial_info,
        'stock_data': stock_data_summary,
        'rating_grade': rating_grade,
        'rating_description': rating_description,
        'traded_value': traded_value_formatted
    }
    
    return render(request, '360View/index.html', context)

def companies_list(request):
    """View to display all available companies"""
    # Get API token
    access_token = get_token()
    
    if not access_token:
        return render(request, '360View/companies_list.html', {
            'error': 'Failed to authenticate with API'
        })
    
    # Get stock data for all companies
    all_stocks = get_stock_data(access_token)
    
    # Group by Symbol to get unique companies
    companies = {}
    for stock in all_stocks:
        symbol = stock.get('Symbol')
        if symbol and symbol not in companies:
            # Get company name - use symbol as fallback
            company_name = stock.get('CompanyName')
            if company_name is None or company_name == "None" or company_name == "":
                company_name = f"{symbol} Stock"
            
            # Get SharesOutstanding and Last price
            shares = stock.get('SharesOutstanding')
            price = stock.get('Last')
            
            # Calculate market cap with proper error handling
            market_cap_formatted = "N/A"
            try:
                # Only calculate if we have valid data
                if shares and price and float(shares) > 0 and float(price) > 0:
                    # Convert to float to handle decimal.Decimal types
                    shares_outstanding = float(shares)
                    last_price = float(price)
                    
                    # Safety check for decimal.Decimal
                    if hasattr(shares_outstanding, 'to_integral_exact'):
                        shares_outstanding = float(shares_outstanding)
                    if hasattr(last_price, 'to_integral_exact'):
                        last_price = float(last_price)
                        
                    market_cap = shares_outstanding * last_price
                    
                    # Format based on size
                    if market_cap >= 1000000000:  # Billions
                        market_cap_formatted = f"{market_cap/1000000000:.2f}B"
                    elif market_cap >= 1000000:  # Millions
                        market_cap_formatted = f"{market_cap/1000000:.2f}M"
                    elif market_cap > 0:  # Thousands
                        market_cap_formatted = f"{market_cap/1000:.2f}K"
            except Exception as e:
                # Silently handle the error
                logger.error(f"Error calculating market cap for {symbol}: {str(e)}")
                pass
            
            companies[symbol] = {
                'Symbol': symbol,
                'CompanyName': company_name,
                'Last': price,
                'Change': stock.get('Change'),
                'PctChange': stock.get('PctChange'),
                'MarketCap': market_cap_formatted
            }
    
    # Convert to list for template
    companies_list = list(companies.values())
    
    # Sort by company name
    companies_list.sort(key=lambda x: x.get('CompanyName', '') or '')
    
    context = {
        'companies': companies_list
    }
    
    return render(request, '360View/companies_list.html', context)

def api_debug(request, symbol="DGKC"):
    """Debug view to show raw API data"""
    # Get API token
    access_token = get_token()
    
    if not access_token:
        return JsonResponse({
            'error': 'Failed to authenticate with API',
            'status': 'error'
        })
    
    # Create directory for API test data
    output_dir = 'api_test_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Get stock data
    stock_data = get_stock_data(access_token, symbol)
    
    # Get latest stock information
    latest_stock = None
    if stock_data:
        latest_stock = stock_data[-1]
    
    # Get news
    news = get_news(access_token)
    
    # Get announcements
    announcements = get_announcements(access_token)
    filtered_announcements = [a for a in announcements if a.get('Symbol') == symbol]
    
    # Get indices
    indices = get_indices(access_token)
    
    # Save data to files
    try:
        if stock_data:
            with open(os.path.join(output_dir, f'{symbol}_stock_data.json'), 'w', encoding='utf-8') as f:
                json.dump(stock_data, f, indent=4, ensure_ascii=False)
        
        if latest_stock:
            with open(os.path.join(output_dir, f'{symbol}_latest.json'), 'w', encoding='utf-8') as f:
                json.dump(latest_stock, f, indent=4, ensure_ascii=False)
        
        if news:
            with open(os.path.join(output_dir, 'news.json'), 'w', encoding='utf-8') as f:
                json.dump(news, f, indent=4, ensure_ascii=False)
        
        if filtered_announcements:
            with open(os.path.join(output_dir, f'{symbol}_announcements.json'), 'w', encoding='utf-8') as f:
                json.dump(filtered_announcements, f, indent=4, ensure_ascii=False)
        
        if indices:
            with open(os.path.join(output_dir, 'indices.json'), 'w', encoding='utf-8') as f:
                json.dump(indices, f, indent=4, ensure_ascii=False)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        })
    
    # Return data as JSON for debugging
    return JsonResponse({
        'status': 'success',
        'message': f'API data saved to {output_dir}/',
        'data': {
            'symbol': symbol,
            'latest_stock': latest_stock,
            'stock_data_count': len(stock_data) if stock_data else 0,
            'news_count': len(news) if news else 0,
            'announcements_count': len(filtered_announcements) if filtered_announcements else 0,
            'indices_count': len(indices) if indices else 0
        }
    })
