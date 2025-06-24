import requests
import orjson
import pandas as pd
import numpy as np
import datetime
from django.conf import settings

def get_token():
    """Get authentication token from the API"""
    url = "https://api.mg-link.net/api/auth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # Get credentials from environment variables or use defaults for development
  
    
    data = {
        "grant_type": "password",
        "username": settings.MG_LINK_CLIENT_USERNAME,
        "password": settings.MG_LINK_CLIENT_PASSWORD  
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            try:
                result = response.json()
                token = result.get("access_token")
                if not token:
                    return None
                    
                return token
            except Exception:
                return None
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None

def get_data(url, token):
    """Get data from the API using the token"""
    if not token:
        return None
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                # Using orjson for better performance
                data = orjson.loads(response.content)
                return data
            except Exception:
                return None
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None

def calculate_market_cap(stock):
    """Calculate market cap from stock data if not available"""
    try:
        if isinstance(stock, dict):
            price = float(stock.get('Last', 0))
            # Assuming 100 million shares outstanding as a placeholder
            shares_outstanding = 100000000
            return price * shares_outstanding
        else:
            # For database model
            return float(stock.price) * 100000000
    except:
        return 0

def filter_stocks(stocks, filters):
    """Apply filters to stock data using pandas for efficient filtering"""
    if not stocks:
        return []
    
    # Convert list of dictionaries to pandas DataFrame
    df = pd.DataFrame(stocks)
    
    # Make sure essential columns exist
    for column in ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']:
        if column not in df.columns:
            df[column] = None
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['Last', 'LDCP', 'Change', 'PctChange', 'Open', 'High', 'Low', 'Volume', 'PE', 'MarketCap']
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors='coerce')

    # Special signal filters that override other filters
    if 'signal' in filters and filters['signal'] != 'none':
        try:
            if filters['signal'] == 'top_gainers':
                # Sort by percent change, descending
                df = df.sort_values(by='PctChange', ascending=False).head(20)
                return df.to_dict('records')
                
            elif filters['signal'] == 'top_losers':
                # Sort by percent change, ascending (most negative first)
                df = df.sort_values(by='PctChange', ascending=True).head(20)
                return df.to_dict('records')
                
            elif filters['signal'] == 'most_active':
                # Sort by volume, descending
                df = df.sort_values(by='Volume', ascending=False).head(20)
                return df.to_dict('records')
                
            elif filters['signal'] == 'new_high':
                # Filter for stocks making new 52-week high
                if 'High52Week' in df.columns:
                    df = df[df['Last'] >= 0.95 * df['High52Week']]
                
            elif filters['signal'] == 'new_low':
                # Filter for stocks making new 52-week low
                if 'Low52Week' in df.columns:
                    df = df[df['Last'] <= 1.05 * df['Low52Week']]
                
            elif filters['signal'] == 'overbought' and 'RSI' in df.columns:
                # Filter stocks with RSI > 70
                df = df[df['RSI'] > 70].copy()
                
            elif filters['signal'] == 'oversold' and 'RSI' in df.columns:
                # Filter stocks with RSI < 30
                df = df[df['RSI'] < 30].copy()
                
        except Exception as e:
            print(f"Error in signal filtering: {str(e)}")
    
    # Apply exchange filter
    if 'exchange' in filters and filters['exchange'] and filters['exchange'].lower() not in ['any', 'none']:
        exchange = filters['exchange']
        # If Exchange column exists
        if 'Exchange' in df.columns:
            df = df[df['Exchange'].str.lower() == exchange.lower()]
    
    # Apply index filter
    if 'index' in filters and filters['index'] and filters['index'].lower() not in ['any', 'none']:
        index_filter = filters['index']
        # If Index column exists
        if 'Index' in df.columns:
            df = df[df['Index'].str.lower() == index_filter.lower()]
    
    # Apply sector filter
    if 'sector' in filters and filters['sector'] and filters['sector'].lower() not in ['any', 'none']:
        sector = filters['sector']
        # Case-insensitive sector filter if Sector column exists
        if 'Sector' in df.columns:
            df = df[df['Sector'].str.lower() == sector.lower()]
    
    # Apply industry filter
    if 'industry' in filters and filters['industry'] and filters['industry'].lower() not in ['any', 'none']:
        industry = filters['industry']
        # Case-insensitive industry filter if Industry column exists
        if 'Industry' in df.columns:
            df = df[df['Industry'].str.lower() == industry.lower()]
    
    # Apply country filter
    if 'country' in filters and filters['country'] and filters['country'].lower() not in ['any', 'none']:
        country = filters['country']
        # Case-insensitive country filter if Country column exists
        if 'Country' in df.columns:
            df = df[df['Country'].str.lower() == country.lower()]
    
    # Apply market capitalization filters
    if 'market_cap' in filters and filters['market_cap'] and filters['market_cap'].lower() not in ['any', 'none']:
        market_cap = filters['market_cap']
        
        if market_cap == 'Mega':
            # Mega (>$200B)
            df = df[df['MarketCap'] > 200_000_000_000]
        elif market_cap == 'Large':
            # Large ($10B-$200B)
            df = df[(df['MarketCap'] >= 10_000_000_000) & (df['MarketCap'] <= 200_000_000_000)]
        elif market_cap == 'Mid':
            # Mid ($2B-$10B)
            df = df[(df['MarketCap'] >= 2_000_000_000) & (df['MarketCap'] <= 10_000_000_000)]
        elif market_cap == 'Small':
            # Small ($300M-$2B)
            df = df[(df['MarketCap'] >= 300_000_000) & (df['MarketCap'] <= 2_000_000_000)]
        elif market_cap == 'Micro':
            # Micro (<$300M)
            df = df[df['MarketCap'] < 300_000_000]
    
    # Apply dividend yield filters
    if 'div_yield' in filters and filters['div_yield'] and filters['div_yield'].lower() not in ['any', 'none']:
        div_yield = filters['div_yield']
        
        if 'DividendYield' in df.columns:
            div_yield_col = 'DividendYield'
        else:
            # Try alternative column names
            div_yield_col = next((col for col in df.columns if 'dividend' in col.lower() and 'yield' in col.lower()), None)
        
        if div_yield_col:
            df[div_yield_col] = pd.to_numeric(df[div_yield_col], errors='coerce')
            
            if div_yield == 'Positive':
                # Positive (>0%)
                df = df[df[div_yield_col] > 0]
            elif div_yield == 'High':
                # High (>3%)
                df = df[df[div_yield_col] > 3]
            elif div_yield == 'Very High':
                # Very High (>6%)
                df = df[df[div_yield_col] > 6]
            elif div_yield == 'None':
                # None (0%)
                df = df[df[div_yield_col] == 0]
    
    # Apply volume filters
    if 'avg_volume' in filters and filters['avg_volume'] and filters['avg_volume'].lower() not in ['any', 'none']:
        avg_volume = filters['avg_volume']
        
        # Check for appropriate column
        if 'AverageVolume' in df.columns:
            vol_col = 'AverageVolume'
        elif 'AvgVolume' in df.columns:
            vol_col = 'AvgVolume'
        else:
            vol_col = 'Volume'  # Fallback to current volume
            
        df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce')
        
        if avg_volume == 'Under 100K':
            df = df[df[vol_col] < 100_000]
        elif avg_volume == 'Over 100K':
            df = df[df[vol_col] > 100_000]
        elif avg_volume == 'Over 500K':
            df = df[df[vol_col] > 500_000]
        elif avg_volume == 'Over 1M':
            df = df[df[vol_col] > 1_000_000]
    
    # Apply relative volume filters
    if 'rel_volume' in filters and filters['rel_volume'] and filters['rel_volume'].lower() not in ['any', 'none']:
        rel_volume = filters['rel_volume']
        
        # Check for appropriate column
        if 'RelativeVolume' in df.columns:
            rel_vol_col = 'RelativeVolume'
        elif 'RelVolume' in df.columns:
            rel_vol_col = 'RelVolume'
        elif 'Volume' in df.columns and 'AvgVolume' in df.columns:
            # Calculate relative volume if we have both current and average volume
            df['RelVolume'] = df['Volume'] / df['AvgVolume']
            rel_vol_col = 'RelVolume'
        else:
            rel_vol_col = None
            
        if rel_vol_col:
            df[rel_vol_col] = pd.to_numeric(df[rel_vol_col], errors='coerce')
            
            if rel_volume == 'Over 0.5':
                df = df[df[rel_vol_col] > 0.5]
            elif rel_volume == 'Over 1':
                df = df[df[rel_vol_col] > 1]
            elif rel_volume == 'Over 2':
                df = df[df[rel_vol_col] > 2]
            elif rel_volume == 'Over 3':
                df = df[df[rel_vol_col] > 3]
    
    # Apply current volume filters
    if 'current_volume' in filters and filters['current_volume'] and filters['current_volume'].lower() not in ['any', 'none']:
        current_volume = filters['current_volume']
        
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        
        if current_volume == 'Under 100K':
            df = df[df['Volume'] < 100_000]
        elif current_volume == 'Over 100K':
            df = df[df['Volume'] > 100_000]
        elif current_volume == 'Over 500K':
            df = df[df['Volume'] > 500_000]
        elif current_volume == 'Over 1M':
            df = df[df['Volume'] > 1_000_000]
    
    # Apply price filters
    if 'price' in filters and filters['price'] and filters['price'].lower() not in ['any', 'none']:
        price_filter = filters['price']
        
        df['Last'] = pd.to_numeric(df['Last'], errors='coerce')
        
        if price_filter == 'Under 1':
            df = df[df['Last'] < 1]
        elif price_filter == 'Under 5':
            df = df[df['Last'] < 5]
        elif price_filter == 'Under 10':
            df = df[df['Last'] < 10]
        elif price_filter == 'Under 20':
            df = df[df['Last'] < 20]
        elif price_filter == 'Over 50':
            df = df[df['Last'] > 50]
        elif price_filter == 'Over 100':
            df = df[df['Last'] > 100]
    
    # Apply target price filters
    if 'target_price' in filters and filters['target_price'] and filters['target_price'].lower() not in ['any', 'none']:
        target_price = filters['target_price']
        
        # Check for target price column
        if 'TargetPrice' in df.columns:
            df['TargetPrice'] = pd.to_numeric(df['TargetPrice'], errors='coerce')
            df['PriceToTarget'] = (df['TargetPrice'] / df['Last'] - 1) * 100
            
            if target_price == 'Positive':
                df = df[df['PriceToTarget'] > 0]
            elif target_price == 'Over 5%':
                df = df[df['PriceToTarget'] > 5]
            elif target_price == 'Over 10%':
                df = df[df['PriceToTarget'] > 10]
            elif target_price == 'Over 20%':
                df = df[df['PriceToTarget'] > 20]
    
    # Apply IPO date filters
    if 'ipo_date' in filters and filters['ipo_date'] and filters['ipo_date'].lower() not in ['any', 'none']:
        ipo_date_filter = filters['ipo_date']
        
        if 'IPODate' in df.columns:
            today = datetime.datetime.now().date()
            
            # Convert to datetime
            df['IPODate'] = pd.to_datetime(df['IPODate'], errors='coerce')
            
            if ipo_date_filter == 'This Year':
                year_start = datetime.datetime(today.year, 1, 1).date()
                df = df[df['IPODate'] >= year_start]
            elif ipo_date_filter == 'Last 2 Years':
                two_years_ago = today.replace(year=today.year - 2)
                df = df[df['IPODate'] >= two_years_ago]
            elif ipo_date_filter == 'Last 5 Years':
                five_years_ago = today.replace(year=today.year - 5)
                df = df[df['IPODate'] >= five_years_ago]
            elif ipo_date_filter == 'Over 10 Years':
                ten_years_ago = today.replace(year=today.year - 10)
                df = df[df['IPODate'] <= ten_years_ago]
    
    # Apply shares outstanding filters
    if 'shares_outstanding' in filters and filters['shares_outstanding'] and filters['shares_outstanding'].lower() not in ['any', 'none']:
        shares_filter = filters['shares_outstanding']
        
        if 'SharesOutstanding' in df.columns:
            df['SharesOutstanding'] = pd.to_numeric(df['SharesOutstanding'], errors='coerce')
            
            if shares_filter == 'Under 10M':
                df = df[df['SharesOutstanding'] < 10_000_000]
            elif shares_filter == 'Over 50M':
                df = df[df['SharesOutstanding'] > 50_000_000]
            elif shares_filter == 'Over 100M':
                df = df[df['SharesOutstanding'] > 100_000_000]
            elif shares_filter == 'Over 500M':
                df = df[df['SharesOutstanding'] > 500_000_000]
    
    # Apply float filters
    if 'float' in filters and filters['float'] and filters['float'].lower() not in ['any', 'none']:
        float_filter = filters['float']
        
        if 'Float' in df.columns:
            df['Float'] = pd.to_numeric(df['Float'], errors='coerce')
            
            if float_filter == 'Under 10M':
                df = df[df['Float'] < 10_000_000]
            elif float_filter == 'Over 50M':
                df = df[df['Float'] > 50_000_000]
            elif float_filter == 'Over 100M':
                df = df[df['Float'] > 100_000_000]
            elif float_filter == 'Over 500M':
                df = df[df['Float'] > 500_000_000]
    
    # Apply analyst recommendation filters
    if 'analyst_recom' in filters and filters['analyst_recom'] and filters['analyst_recom'].lower() not in ['any', 'none']:
        recom = filters['analyst_recom']
        
        recom_columns = [col for col in df.columns if 'recommendation' in col.lower() or 'recom' in col.lower()]
        if recom_columns:
            recom_col = recom_columns[0]
            df = df[df[recom_col].str.lower() == recom.lower()]
    
    # Apply PE ratio filters from the Technical tab
    if 'pe_ratio' in filters and filters['pe_ratio'] and filters['pe_ratio'].lower() not in ['any', 'none']:
        pe_filter = filters['pe_ratio']
        
        df['PE'] = pd.to_numeric(df['PE'], errors='coerce')
        
        if pe_filter == 'Low':
            df = df[df['PE'] < 15]
        elif pe_filter == 'High':
            df = df[df['PE'] > 50]
        elif pe_filter == 'Negative':
            df = df[df['PE'] < 0]
    
    # Apply Forward P/E filters
    if 'forward_pe' in filters and filters['forward_pe'] and filters['forward_pe'].lower() not in ['any', 'none']:
        forward_pe = filters['forward_pe']
        
        if 'ForwardPE' in df.columns:
            df['ForwardPE'] = pd.to_numeric(df['ForwardPE'], errors='coerce')
            
            if forward_pe == 'Low':
                df = df[df['ForwardPE'] < 15]
            elif forward_pe == 'High':
                df = df[df['ForwardPE'] > 50]
    
    # Apply PEG ratio filters
    if 'peg' in filters and filters['peg'] and filters['peg'].lower() not in ['any', 'none']:
        peg_filter = filters['peg']
        
        if 'PEG' in df.columns:
            df['PEG'] = pd.to_numeric(df['PEG'], errors='coerce')
            
            if peg_filter == 'Low':
                df = df[df['PEG'] < 1]
            elif peg_filter == 'High':
                df = df[df['PEG'] > 2]
    
    # Apply P/S ratio filters
    if 'ps' in filters and filters['ps'] and filters['ps'].lower() not in ['any', 'none']:
        ps_filter = filters['ps']
        
        if 'PS' in df.columns:
            df['PS'] = pd.to_numeric(df['PS'], errors='coerce')
            
            if ps_filter == 'Low':
                df = df[df['PS'] < 1]
            elif ps_filter == 'High':
                df = df[df['PS'] > 10]
    
    # Apply P/B ratio filters
    if 'pb' in filters and filters['pb'] and filters['pb'].lower() not in ['any', 'none']:
        pb_filter = filters['pb']
        
        if 'PB' in df.columns:
            df['PB'] = pd.to_numeric(df['PB'], errors='coerce')
            
            if pb_filter == 'Low':
                df = df[df['PB'] < 1]
            elif pb_filter == 'High':
                df = df[df['PB'] > 5]
    
    # Apply RSI filters
    if 'rsi' in filters and filters['rsi'] and filters['rsi'].lower() not in ['any', 'none']:
        rsi_filter = filters['rsi']
        
        # Check for RSI column
        if 'RSI' in df.columns:
            df['RSI'] = pd.to_numeric(df['RSI'], errors='coerce')
            
            if rsi_filter == 'Oversold':
                df = df[df['RSI'] < 30]
            elif rsi_filter == 'Overbought':
                df = df[df['RSI'] > 70]
            elif rsi_filter == 'Not Overbought':
                df = df[df['RSI'] < 70]
            elif rsi_filter == 'Not Oversold':
                df = df[df['RSI'] > 30]
    
    # Apply SMA filters
    if 'sma_20' in filters and filters['sma_20'] and filters['sma_20'].lower() not in ['any', 'none']:
        sma_20_filter = filters['sma_20']
        
        # Check for necessary columns
        required_cols = ['SMA20', 'Last', 'SMA50']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if not missing_cols:
            # Convert to numeric to ensure proper comparison
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if sma_20_filter == 'Price Above SMA20':
                df = df[df['Last'] > df['SMA20']]
            elif sma_20_filter == 'Price Below SMA20':
                df = df[df['Last'] < df['SMA20']]
            elif sma_20_filter == 'Price Crossed SMA20':
                # This would ideally need historical data, we'd approximate
                df = df[abs(df['Last'] - df['SMA20']) / df['SMA20'] < 0.02]
            elif sma_20_filter == 'SMA20 Crossed SMA50':
                # This would ideally need historical data, we'd approximate
                df = df[abs(df['SMA20'] - df['SMA50']) / df['SMA50'] < 0.02]
            elif sma_20_filter == 'SMA20 Above SMA50':
                df = df[df['SMA20'] > df['SMA50']]
            elif sma_20_filter == 'SMA20 Below SMA50':
                df = df[df['SMA20'] < df['SMA50']]
    
    # Similar implementation for SMA50 filter
    if 'sma_50' in filters and filters['sma_50'] and filters['sma_50'].lower() not in ['any', 'none']:
        sma_50_filter = filters['sma_50']
        
        # Check for necessary columns
        required_cols = ['SMA50', 'Last', 'SMA200']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if not missing_cols:
            # Convert to numeric to ensure proper comparison
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if sma_50_filter == 'Price Above SMA50':
                df = df[df['Last'] > df['SMA50']]
            elif sma_50_filter == 'Price Below SMA50':
                df = df[df['Last'] < df['SMA50']]
            elif sma_50_filter == 'Price Crossed SMA50':
                # This would ideally need historical data, we'd approximate
                df = df[abs(df['Last'] - df['SMA50']) / df['SMA50'] < 0.02]
            elif sma_50_filter == 'SMA50 Crossed SMA200':
                # This would ideally need historical data, we'd approximate
                df = df[abs(df['SMA50'] - df['SMA200']) / df['SMA200'] < 0.02]
            elif sma_50_filter == 'SMA50 Above SMA200':
                df = df[df['SMA50'] > df['SMA200']]
            elif sma_50_filter == 'SMA50 Below SMA200':
                df = df[df['SMA50'] < df['SMA200']]
    
    # Similar implementation for SMA200 filter
    if 'sma_200' in filters and filters['sma_200'] and filters['sma_200'].lower() not in ['any', 'none']:
        sma_200_filter = filters['sma_200']
        
        # Check for necessary columns
        required_cols = ['SMA200', 'Last', 'SMA20']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if not missing_cols:
            # Convert to numeric to ensure proper comparison
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if sma_200_filter == 'Price Above SMA200':
                df = df[df['Last'] > df['SMA200']]
            elif sma_200_filter == 'Price Below SMA200':
                df = df[df['Last'] < df['SMA200']]
            elif sma_200_filter == 'Price Crossed SMA200':
                # This would ideally need historical data, we'd approximate
                df = df[abs(df['Last'] - df['SMA200']) / df['SMA200'] < 0.02]
            elif sma_200_filter == 'SMA200 Above SMA20':
                df = df[df['SMA200'] > df['SMA20']]
            elif sma_200_filter == 'SMA200 Below SMA20':
                df = df[df['SMA200'] < df['SMA20']]
    
    # Apply Gap filters
    if 'gap' in filters and filters['gap'] and filters['gap'].lower() not in ['any', 'none']:
        gap_filter = filters['gap']
        
        # Check for necessary columns
        if 'Open' in df.columns and 'LDCP' in df.columns:
            # Calculate gap percentage
            df['Gap'] = ((df['Open'] - df['LDCP']) / df['LDCP']) * 100
            
            if gap_filter == 'Up':
                df = df[df['Gap'] > 0]
            elif gap_filter == 'Up 0-2%':
                df = df[(df['Gap'] > 0) & (df['Gap'] <= 2)]
            elif gap_filter == 'Up 2-5%':
                df = df[(df['Gap'] > 2) & (df['Gap'] <= 5)]
            elif gap_filter == 'Up 5-10%':
                df = df[(df['Gap'] > 5) & (df['Gap'] <= 10)]
            elif gap_filter == 'Up 10-20%':
                df = df[(df['Gap'] > 10) & (df['Gap'] <= 20)]
            elif gap_filter == 'Down':
                df = df[df['Gap'] < 0]
            elif gap_filter == 'Down 0-2%':
                df = df[(df['Gap'] < 0) & (df['Gap'] >= -2)]
            elif gap_filter == 'Down 2-5%':
                df = df[(df['Gap'] < -2) & (df['Gap'] >= -5)]
            elif gap_filter == 'Down 5-10%':
                df = df[(df['Gap'] < -5) & (df['Gap'] >= -10)]
            elif gap_filter == 'Down 10-20%':
                df = df[(df['Gap'] < -10) & (df['Gap'] >= -20)]
    
    # Apply change filters
    if 'change' in filters and filters['change'] and filters['change'].lower() not in ['any', 'none']:
        change_filter = filters['change']
        
        # Use percent change column if available
        if 'PctChange' in df.columns:
            df['PctChange'] = pd.to_numeric(df['PctChange'], errors='coerce')
            
            if change_filter == 'Up':
                df = df[df['PctChange'] > 0]
            elif change_filter == 'Up 1%':
                df = df[df['PctChange'] > 1]
            elif change_filter == 'Up 2%':
                df = df[df['PctChange'] > 2]
            elif change_filter == 'Up 5%':
                df = df[df['PctChange'] > 5]
            elif change_filter == 'Up 10%':
                df = df[df['PctChange'] > 10]
            elif change_filter == 'Up 15%':
                df = df[df['PctChange'] > 15]
            elif change_filter == 'Up 20%':
                df = df[df['PctChange'] > 20]
            elif change_filter == 'Down':
                df = df[df['PctChange'] < 0]
            elif change_filter == 'Down 1%':
                df = df[df['PctChange'] < -1]
            elif change_filter == 'Down 2%':
                df = df[df['PctChange'] < -2]
            elif change_filter == 'Down 5%':
                df = df[df['PctChange'] < -5]
            elif change_filter == 'Down 10%':
                df = df[df['PctChange'] < -10]
            elif change_filter == 'Down 15%':
                df = df[df['PctChange'] < -15]
    
    # Apply change from open filters
    if 'change_open' in filters and filters['change_open'] and filters['change_open'].lower() not in ['any', 'none']:
        change_open_filter = filters['change_open']
        
        # Check for necessary columns
        if 'Last' in df.columns and 'Open' in df.columns:
            # Calculate change from open
            df['ChangeFromOpen'] = ((df['Last'] - df['Open']) / df['Open']) * 100
            
            if change_open_filter == 'Up':
                df = df[df['ChangeFromOpen'] > 0]
            elif change_open_filter == 'Up 1%':
                df = df[df['ChangeFromOpen'] > 1]
            elif change_open_filter == 'Up 2%':
                df = df[df['ChangeFromOpen'] > 2]
            elif change_open_filter == 'Up 5%':
                df = df[df['ChangeFromOpen'] > 5]
            elif change_open_filter == 'Down':
                df = df[df['ChangeFromOpen'] < 0]
            elif change_open_filter == 'Down 1%':
                df = df[df['ChangeFromOpen'] < -1]
            elif change_open_filter == 'Down 2%':
                df = df[df['ChangeFromOpen'] < -2]
            elif change_open_filter == 'Down 5%':
                df = df[df['ChangeFromOpen'] < -5]
    
    # Apply symbol filter if it exists and hasn't been applied yet
    if 'symbol' in filters and filters['symbol'] and 'symbol' not in locals():
        symbol = filters['symbol'].upper()
        df = df[df['Symbol'].str.contains(symbol, case=False, na=False)]
    
    # Apply performance filters
    if 'performance' in filters and filters['performance'] and filters['performance'].lower() not in ['any', 'none']:
        performance_filter = filters['performance']
        
        # Map filter values to column names and expected values
        performance_map = {
            'Week Up': ('PerformanceWeek', 0, None),
            'Week Down': ('PerformanceWeek', None, 0),
            'Month Up': ('PerformanceMonth', 0, None),
            'Month Down': ('PerformanceMonth', None, 0),
            'Quarter Up': ('PerformanceQuarter', 0, None),
            'Quarter Down': ('PerformanceQuarter', None, 0),
            'Year Up': ('PerformanceYear', 0, None),
            'Year Down': ('PerformanceYear', None, 0)
        }
        
        if performance_filter in performance_map:
            column, min_val, max_val = performance_map[performance_filter]
            
            # Check if column exists, fall back to PctChange if not
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors='coerce')
                
                if min_val is not None:
                    df = df[df[column] > min_val]
                if max_val is not None:
                    df = df[df[column] < max_val]
            elif column == 'PerformanceWeek' and 'PctChange' in df.columns:
                # If we don't have week performance, use daily change as a fallback
                df['PctChange'] = pd.to_numeric(df['PctChange'], errors='coerce')
                
                if min_val is not None:
                    df = df[df['PctChange'] > min_val]
                if max_val is not None:
                    df = df[df['PctChange'] < max_val]
    
    # Apply volatility filters
    if 'volatility' in filters and filters['volatility'] and filters['volatility'].lower() not in ['any', 'none']:
        volatility_filter = filters['volatility']
        
        volatility_col = next((col for col in df.columns if 'volatility' in col.lower()), None)
        
        if volatility_col:
            df[volatility_col] = pd.to_numeric(df[volatility_col], errors='coerce')
            
            if volatility_filter == 'Low':
                df = df[df[volatility_col] < 1.5]  # Arbitrary threshold
            elif volatility_filter == 'High':
                df = df[df[volatility_col] > 2.5]  # Arbitrary threshold
            elif volatility_filter == 'Week':
                # If we have weekly volatility column
                week_vol_col = next((col for col in df.columns if 'week' in col.lower() and 'volatility' in col.lower()), None)
                if week_vol_col:
                    df = df.sort_values(by=week_vol_col, ascending=False).head(100)
            elif volatility_filter == 'Month':
                # If we have monthly volatility column
                month_vol_col = next((col for col in df.columns if 'month' in col.lower() and 'volatility' in col.lower()), None)
                if month_vol_col:
                    df = df.sort_values(by=month_vol_col, ascending=False).head(100)
    
    # Apply dividend filters for the Dividend tab
    if 'dividend_yield' in filters and filters['dividend_yield'] and filters['dividend_yield'].lower() not in ['any', 'none']:
        div_yield_filter = filters['dividend_yield']
        
        # Find appropriate dividend yield column
        div_yield_col = next((col for col in df.columns if 'dividend' in col.lower() and 'yield' in col.lower()), None)
        
        if div_yield_col:
            df[div_yield_col] = pd.to_numeric(df[div_yield_col], errors='coerce')
            
            if div_yield_filter == 'No Dividend':
                df = df[df[div_yield_col] == 0]
            elif div_yield_filter == 'Very High':
                df = df[df[div_yield_col] > 6]
            elif div_yield_filter == 'High':
                df = df[df[div_yield_col] > 4]
            elif div_yield_filter == 'Average':
                df = df[(df[div_yield_col] > 2) & (df[div_yield_col] <= 4)]
            elif div_yield_filter == 'Low':
                df = df[(df[div_yield_col] > 0) & (df[div_yield_col] <= 2)]
    
    # Apply dividend growth filters
    if 'dividend_growth' in filters and filters['dividend_growth'] and filters['dividend_growth'].lower() not in ['any', 'none']:
        div_growth_filter = filters['dividend_growth']
        
        # Find appropriate dividend growth column
        div_growth_col = next((col for col in df.columns if 'dividend' in col.lower() and 'growth' in col.lower()), None)
        
        if div_growth_col:
            df[div_growth_col] = pd.to_numeric(df[div_growth_col], errors='coerce')
            
            if div_growth_filter == 'Positive Only':
                df = df[df[div_growth_col] > 0]
            elif div_growth_filter == 'Very High':
                df = df[df[div_growth_col] > 15]
            elif div_growth_filter == 'High':
                df = df[df[div_growth_col] > 10]
            elif div_growth_filter == 'Average':
                df = df[(df[div_growth_col] > 5) & (df[div_growth_col] <= 10)]
            elif div_growth_filter == 'Low':
                df = df[(df[div_growth_col] > 0) & (df[div_growth_col] <= 5)]
            elif div_growth_filter == 'Negative Only':
                df = df[df[div_growth_col] < 0]
    
    # Apply ownership filters
    if 'ownership' in filters and filters['ownership'] and filters['ownership'].lower() not in ['any', 'none']:
        ownership_filter = filters['ownership']
        
        # Try to find appropriate ownership columns
        institutional_col = next((col for col in df.columns if 'institutional' in col.lower() and 'ownership' in col.lower()), None)
        insider_col = next((col for col in df.columns if 'insider' in col.lower() and 'ownership' in col.lower()), None)
        
        if ownership_filter == 'High Institutional' and institutional_col:
            df[institutional_col] = pd.to_numeric(df[institutional_col], errors='coerce')
            df = df[df[institutional_col] > 70]
        elif ownership_filter == 'Low Institutional' and institutional_col:
            df[institutional_col] = pd.to_numeric(df[institutional_col], errors='coerce')
            df = df[df[institutional_col] < 30]
        elif ownership_filter == 'High Insider' and insider_col:
            df[insider_col] = pd.to_numeric(df[insider_col], errors='coerce')
            df = df[df[insider_col] > 10]
        elif ownership_filter == 'Very High Insider' and insider_col:
            df[insider_col] = pd.to_numeric(df[insider_col], errors='coerce')
            df = df[df[insider_col] > 30]
        elif ownership_filter == 'Low Insider' and insider_col:
            df[insider_col] = pd.to_numeric(df[insider_col], errors='coerce')
            df = df[df[insider_col] < 5]
    
    # Apply symbol search (more specific than existing implementation)
    if 'symbol' in filters and filters['symbol']:
        symbol_filter = filters['symbol'].upper()
        # Split by commas or spaces to allow multiple symbols
        symbols = [s.strip() for s in symbol_filter.replace(',', ' ').split()]
        
        if symbols:
            # Filter for any symbol that matches (case insensitive)
            symbol_mask = df['Symbol'].str.upper().isin([s.upper() for s in symbols])
            
            # Also match partial symbols in case they didn't type the full ticker
            for symbol in symbols:
                symbol_mask = symbol_mask | df['Symbol'].str.upper().str.contains(symbol.upper())
            
            df = df[symbol_mask]
    
    # Convert the filtered DataFrame back to a list of dictionaries
    return df.replace({np.nan: None}).to_dict('records') 