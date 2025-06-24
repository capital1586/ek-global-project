from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

class StockData(BaseModel):
    """Pydantic model for stock data returned from API"""
    Symbol: str
    CompanyName: Optional[str] = None
    Sector: Optional[str] = None
    Industry: Optional[str] = None
    Country: Optional[str] = "Pakistan"  # Default to Pakistan for PSX stocks
    Exchange: Optional[str] = "PSX"  # Default exchange
    CurrentPrice: Optional[Decimal] = None
    ChangePercentage: Optional[Decimal] = None
    Change: Optional[Decimal] = None
    Volume: Optional[int] = None
    OpenPrice: Optional[Decimal] = None
    HighPrice: Optional[Decimal] = None
    LowPrice: Optional[Decimal] = None
    VWAP: Optional[Decimal] = None
    PE: Optional[Decimal] = None
    MarketCap: Optional[Decimal] = None
    DividendYield: Optional[Decimal] = None
    RelativeVolume: Optional[Decimal] = None
    Date: Optional[date] = None
    LastUpdated: Optional[datetime] = None
    
    class Config:
        # Allow extra fields to future-proof
        extra = "allow"

    @validator('*', pre=True)
    def convert_numeric_strings(cls, v):
        """Convert string numbers to appropriate types"""
        if isinstance(v, str):
            # Try to convert to Decimal if it looks numeric
            try:
                if v.replace('.', '', 1).isdigit() or (v.startswith('-') and v[1:].replace('.', '', 1).isdigit()):
                    return Decimal(v)
            except (InvalidOperation, ValueError):
                pass
        return v

    @validator('*', pre=True)
    def handle_null_values(cls, v):
        """Convert 'null', 'None', '-' to None"""
        if v in ['null', 'None', 'N/A', '-', '']:
            return None
        return v

    @root_validator(pre=True)
    def normalize_field_names(cls, values):
        """Convert various API field name formats to our standardized format"""
        field_mapping = {
            # Handle case variations
            'symbol': 'Symbol',
            'SYMBOL': 'Symbol',
            'company_name': 'CompanyName',
            'companyname': 'CompanyName',
            'company': 'CompanyName',
            'sector': 'Sector',
            'industry': 'Industry',
            'country': 'Country',
            'exchange': 'Exchange',
            'currentprice': 'CurrentPrice',
            'current_price': 'CurrentPrice',
            'price': 'CurrentPrice',
            'last': 'CurrentPrice',
            'change': 'Change',
            'change_percentage': 'ChangePercentage',
            'changepct': 'ChangePercentage',
            'pctchange': 'ChangePercentage',
            'volume': 'Volume',
            'vol': 'Volume',
            'open': 'OpenPrice',
            'openprice': 'OpenPrice',
            'open_price': 'OpenPrice',
            'high': 'HighPrice',
            'highprice': 'HighPrice',
            'high_price': 'HighPrice',
            'low': 'LowPrice',
            'lowprice': 'LowPrice',
            'low_price': 'LowPrice',
            'vwap': 'VWAP',
            'pe': 'PE',
            'pe_ratio': 'PE',
            'peratio': 'PE',
            'p/e': 'PE',
            'marketcap': 'MarketCap',
            'market_cap': 'MarketCap',
            'market_capitalization': 'MarketCap',
            'date': 'Date',
            'dividend': 'DividendYield',
            'dividend_yield': 'DividendYield',
            'dividendyield': 'DividendYield',
            'yield': 'DividendYield',
            'relative_volume': 'RelativeVolume',
            'relativevolume': 'RelativeVolume',
            'rel_volume': 'RelativeVolume',
            'last_updated': 'LastUpdated',
            'lastupdated': 'LastUpdated',
            'createdatetime': 'LastUpdated',
            'create_date_time': 'LastUpdated',
        }
        
        # Create a new dict with normalized keys
        normalized = {}
        for key, value in values.items():
            # Convert key to lowercase for case-insensitive matching
            lower_key = key.lower()
            # Use the mapping or the original key
            normalized_key = field_mapping.get(lower_key, key)
            normalized[normalized_key] = value
        
        return normalized

class FilterCriteria(BaseModel):
    """Pydantic model for filter parameters"""
    symbol: Optional[str] = None
    exchange: Optional[str] = Field(None, description="Exchange code (PSX, NYSE, NASDAQ, etc.)")
    sector: Optional[str] = Field(None, description="Sector name")
    industry: Optional[str] = Field(None, description="Industry name")
    country: Optional[str] = Field(None, description="Country (Pakistan, USA, etc.)")
    market_cap: Optional[str] = Field(None, description="Market cap filter (Mega, Large, Mid, Small, Micro, Nano, Over XB, Under XB)")
    div_yield: Optional[str] = Field(None, description="Dividend yield filter (None, Positive, High, Very High, Over X%, Under X%)")
    avg_volume: Optional[str] = Field(None, description="Average volume filter (Under X, Over X, X to Y)")
    rel_volume: Optional[str] = Field(None, description="Relative volume filter (Over X, Under X)")
    current_volume: Optional[str] = Field(None, description="Current volume filter (Over X, Under X)")
    price: Optional[str] = Field(None, description="Price filter (Under $X, Over $X, $X to $Y)")
    target_price: Optional[str] = Field(None, description="Target price filter (Above Price, Below Price, X% Above/Below Price)")
    ipo_date: Optional[str] = Field(None, description="IPO date filter (Today, In the last week/month/year, etc.)")
    shares_outstanding: Optional[str] = Field(None, description="Shares outstanding filter (Over X, Under X)")
    float: Optional[str] = Field(None, description="Float filter (Over X, Under X)")
    analyst_recom: Optional[str] = Field(None, description="Analyst recommendation filter (Strong Buy, Buy, Hold, Sell, etc.)")
    option_short: Optional[str] = Field(None, description="Options/Short filter (Optionable, Shortable, etc.)")
    earnings_date: Optional[str] = Field(None, description="Earnings date filter (Today, Tomorrow, This Week, etc.)")
    trades: Optional[str] = Field(None, description="Trades filter (Elite only, etc.)")
    pe_ratio: Optional[str] = Field(None, description="P/E ratio filter (Low (<15), Profitable (>0), High (>50), Negative (<0), Over X, Under X)")
    forward_pe: Optional[str] = Field(None, description="Forward P/E filter (Low, High, etc.)")
    peg: Optional[str] = Field(None, description="PEG ratio filter (Low (<1), High (>2), etc.)")
    ps: Optional[str] = Field(None, description="Price to Sales filter (Low (<1), High (>10), etc.)")
    pb: Optional[str] = Field(None, description="Price to Book filter (Low (<1), High (>5), etc.)")
    performance: Optional[str] = Field(None, description="Performance filter (Week, Month, Quarter, etc.)")
    volatility: Optional[str] = Field(None, description="Volatility filter (Week, Month, etc.)")
    rsi: Optional[str] = Field(None, description="RSI filter (Overbought, Oversold, etc.)")
    gap: Optional[str] = Field(None, description="Gap filter (Up, Down, Up X%, Down X%, etc.)")
    sma_20: Optional[str] = Field(None, description="20-Day SMA filter (Price above/below SMA20, etc.)")
    sma_50: Optional[str] = Field(None, description="50-Day SMA filter (Price above/below SMA50, etc.)")
    sma_200: Optional[str] = Field(None, description="200-Day SMA filter (Price above/below SMA200, etc.)")
    change: Optional[str] = Field(None, description="Change % filter (Up, Down, Up X%, Down X%)")
    change_open: Optional[str] = Field(None, description="Change from Open % filter (Up, Down, Up X%, Down X%)")
    
    # Add the new technical filters
    pb_ratio: Optional[str] = Field(None, description="Price to Book ratio filter (Under X, Over X)")
    ps_ratio: Optional[str] = Field(None, description="Price to Sales ratio filter (Under X, Over X)")
    year_range: Optional[str] = Field(None, description="52-Week Range filter (Near High, Near Low, New High, New Low)")
    ma_50: Optional[str] = Field(None, description="50-day Moving Average filter (Price Above/Below MA, MA Rising/Falling)")
    ma_200: Optional[str] = Field(None, description="200-day Moving Average filter (Price Above/Below MA, MA Rising/Falling)")
    volume_trend: Optional[str] = Field(None, description="Volume Trend filter (Increasing, Decreasing, Above/Below Average)")
    
    # Additional criteria can be added as needed
    
    @validator('*')
    def convert_any_to_none(cls, v):
        """Convert 'any' to None for easier processing"""
        if v == 'any':
            return None
        return v 