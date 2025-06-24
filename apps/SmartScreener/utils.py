from django.db.models import Q
from decimal import Decimal
import logging

# Set up logging
logger = logging.getLogger(__name__)

def filter_stock(stock_dict, filters):
    """Filter a single stock based on given criteria"""
    if not filters:
        return True
        
    # For debugging
    logger.debug(f"Filtering stock: {stock_dict.get('Symbol')} with filters: {filters}")

    # Symbol/ticker filter (case insensitive)
    if 'symbol' in filters and filters['symbol']:
        symbol_query = filters['symbol'].upper().strip()
        stock_symbol = stock_dict.get('Symbol', '')
        if not stock_symbol or symbol_query not in stock_symbol.upper():
            return False

    # Basic filters - case insensitive string comparison
    if 'sector' in filters and filters['sector'] and filters['sector'].lower() not in ['any', 'none']:
        stock_sector = stock_dict.get('sector', '') or stock_dict.get('Sector', '')
        if not stock_sector or filters['sector'].lower() != stock_sector.lower():
            return False
            
    if 'industry' in filters and filters['industry'] and filters['industry'].lower() not in ['any', 'none']:
        stock_industry = stock_dict.get('industry', '') or stock_dict.get('Industry', '')
        if not stock_industry or filters['industry'].lower() != stock_industry.lower():
            return False

    # Numeric range filters
    ranges = {
        'price': ('price_min', 'price_max', ['price', 'Last']),
        'volume': ('volume_min', 'volume_max', ['volume', 'Volume']),
        'market_cap': ('market_cap_min', 'market_cap_max', ['marketCap', 'MarketCap']),
        'pe': ('pe_min', 'pe_max', ['pe', 'PE']),
        'change': ('change_min', 'change_max', ['changePercent', 'PctChange', 'Change'])
    }

    for _, (min_key, max_key, value_keys) in ranges.items():
        # Try each possible key in the stock dictionary
        value = None
        for key in value_keys:
            if key in stock_dict and stock_dict[key] is not None:
                try:
                    value = float(stock_dict[key])
                    break
                except (ValueError, TypeError):
                    continue
                
        if value is None:
            # Skip this filter if we can't find a value
            continue
            
        # Apply min filter if it exists
        if min_key in filters and filters[min_key]:
            try:
                min_val = float(filters[min_key])
                if value < min_val:
                    return False
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing min value for {min_key}: {e}")
                continue
        
        # Apply max filter if it exists
        if max_key in filters and filters[max_key]:
            try:
                max_val = float(filters[max_key])
                if value > max_val:
                    return False
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing max value for {max_key}: {e}")
                continue

    # Signal filters
    if 'signal' in filters and filters['signal'] and filters['signal'] != 'none':
        signal = filters['signal']
        
        # Get relevant values with fallbacks
        change_percent = None
        for key in ['changePercent', 'PctChange', 'Change', 'change']:
            if key in stock_dict and stock_dict[key] is not None:
                try:
                    change_percent = float(stock_dict[key])
                    break
                except (ValueError, TypeError):
                    pass
                    
        volume = None
        for key in ['volume', 'Volume']:
            if key in stock_dict and stock_dict[key] is not None:
                try:
                    volume = float(stock_dict[key])
                    break
                except (ValueError, TypeError):
                    pass
                    
        rsi = None
        for key in ['rsi', 'RSI']:
            if key in stock_dict and stock_dict[key] is not None:
                try:
                    rsi = float(stock_dict[key])
                    break
                except (ValueError, TypeError):
                    pass
            
        # Apply signal filters
        if signal == 'top_gainers' and (change_percent is None or change_percent <= 0):
            return False
        elif signal == 'top_losers' and (change_percent is None or change_percent >= 0):
            return False
        elif signal == 'most_active' and (volume is None or volume < 500000):  # Adjust threshold as needed
            return False
        elif signal == 'overbought' and (rsi is None or rsi < 70):
            return False
        elif signal == 'oversold' and (rsi is None or rsi > 30):
            return False
        elif signal == 'new_high' and stock_dict.get('High52') is not None:
            current_price = None
            for key in ['Last', 'price']:
                if key in stock_dict:
                    try:
                        current_price = float(stock_dict[key])
                        break
                    except (ValueError, TypeError):
                        pass
            if current_price is None or current_price < float(stock_dict['High52']) * 0.95:
                return False
        elif signal == 'new_low' and stock_dict.get('Low52') is not None:
            current_price = None
            for key in ['Last', 'price']:
                if key in stock_dict:
                    try:
                        current_price = float(stock_dict[key])
                        break
                    except (ValueError, TypeError):
                        pass
            if current_price is None or current_price > float(stock_dict['Low52']) * 1.05:
                return False

    return True

def build_filter_query(filters):
    """Build Django ORM query from filters"""
    query = Q()
    
    if filters.get('sector') and filters['sector'].lower() not in ['any', 'none']:
        query &= Q(sector__iexact=filters['sector'])
        
    if filters.get('industry') and filters['industry'].lower() not in ['any', 'none']:
        query &= Q(industry__iexact=filters['industry'])
        
    # Symbol/ticker filter
    if filters.get('symbol'):
        query &= Q(symbol__icontains=filters['symbol'])
        
    # Price range
    if filters.get('price_min'):
        try:
            query &= Q(price__gte=Decimal(filters['price_min']))
        except (ValueError, TypeError, InvalidOperation):
            pass
            
    if filters.get('price_max'):
        try:
            query &= Q(price__lte=Decimal(filters['price_max']))
        except (ValueError, TypeError, InvalidOperation):
            pass
        
    # Volume range
    if filters.get('volume_min'):
        try:
            query &= Q(volume__gte=int(float(filters['volume_min'])))
        except (ValueError, TypeError):
            pass
            
    if filters.get('volume_max'):
        try:
            query &= Q(volume__lte=int(float(filters['volume_max'])))
        except (ValueError, TypeError):
            pass
        
    # Change percent range
    if filters.get('change_min'):
        try:
            query &= Q(change_percent__gte=Decimal(filters['change_min']))
        except (ValueError, TypeError, InvalidOperation):
            pass
            
    if filters.get('change_max'):
        try:
            query &= Q(change_percent__lte=Decimal(filters['change_max']))
        except (ValueError, TypeError, InvalidOperation):
            pass
        
    # PE ratio range
    if filters.get('pe_min'):
        try:
            query &= Q(pe_ratio__gte=Decimal(filters['pe_min']))
        except (ValueError, TypeError, InvalidOperation):
            pass
            
    if filters.get('pe_max'):
        try:
            query &= Q(pe_ratio__lte=Decimal(filters['pe_max']))
        except (ValueError, TypeError, InvalidOperation):
            pass
        
    # Market cap range
    if filters.get('market_cap_min'):
        try:
            query &= Q(market_cap__gte=Decimal(filters['market_cap_min']))
        except (ValueError, TypeError, InvalidOperation):
            pass
            
    if filters.get('market_cap_max'):
        try:
            query &= Q(market_cap__lte=Decimal(filters['market_cap_max']))
        except (ValueError, TypeError, InvalidOperation):
            pass
        
    return query 