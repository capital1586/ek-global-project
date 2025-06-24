from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from typing_extensions import Annotated

class Stock(BaseModel):
    """Stock data model"""
    Symbol: str
    CompanyName: Optional[str] = None
    Sector: Optional[str] = None
    Industry: Optional[str] = None
    Last: Optional[float] = None
    LDCP: Optional[float] = None  # Last day closing price
    Change: Optional[float] = None
    PctChange: Optional[float] = None
    Open: Optional[float] = None
    High: Optional[float] = None
    Low: Optional[float] = None
    Volume: Optional[int] = None
    MarketCap: Optional[float] = None
    PE: Optional[float] = None
    
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class IndexData(BaseModel):
    """Index data model"""
    Symbol: str
    IndexName: Optional[str] = None
    LastTrade: Optional[float] = None
    Change: Optional[float] = None
    ChangePercentage: Optional[float] = None
    Volume: Optional[int] = None
    UpdateTime: Optional[str] = None

class MarketData(BaseModel):
    """Market data model"""
    kse100_index: Optional[float] = None
    kse100_change: Optional[float] = None
    kse100_change_percent: Optional[float] = None
    market_volume: Optional[float] = None
    total_stocks: Optional[int] = None
    last_update: Optional[str] = None
    sectors: Optional[list[dict[str, Any]]] = None

class PaginationMeta(BaseModel):
    """Pagination metadata model"""
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_previous: bool

class StockResponse(BaseModel):
    """Stock response model"""
    status: str
    data: list[Stock]
    meta: PaginationMeta

class FilterParams(BaseModel):
    """Filter parameters model"""
    # Fundamentals tab filters
    exchange: Optional[str] = None  
    index: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    market_cap: Optional[str] = None
    div_yield: Optional[str] = None
    avg_volume: Optional[str] = None
    rel_volume: Optional[str] = None
    current_volume: Optional[str] = None
    price: Optional[str] = None
    target_price: Optional[str] = None
    ipo_date: Optional[str] = None
    shares_outstanding: Optional[str] = None
    float: Optional[str] = None
    analyst_recom: Optional[str] = None
    option_short: Optional[str] = None
    earnings_date: Optional[str] = None
    trades: Optional[str] = None
    
    # Technical tab filters
    pe_ratio: Optional[str] = None
    forward_pe: Optional[str] = None
    peg: Optional[str] = None
    ps: Optional[str] = None
    pb: Optional[str] = None
    
    # Performance tab filters
    performance: Optional[str] = None
    performance_2: Optional[str] = None
    volatility: Optional[str] = None
    rsi: Optional[str] = None
    gap: Optional[str] = None
    sma_20: Optional[str] = None
    sma_50: Optional[str] = None
    sma_200: Optional[str] = None
    change: Optional[str] = None
    change_open: Optional[str] = None
    
    # Original/legacy filters
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None
    change_min: Optional[float] = None
    change_max: Optional[float] = None
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    symbol: Optional[str] = None
    signal: Optional[str] = None
    
    # Pagination and sorting
    page: Optional[int] = 1
    per_page: Optional[int] = 20
    sort_by: Optional[str] = "Symbol"
    sort_dir: Optional[str] = "asc"

class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    message: str
    error: Optional[str] = None

class TechnicalIndicator(BaseModel):
    """Technical indicator model"""
    symbol: str
    indicators: dict[str, Any]
    timestamp: str

class StockHistory(BaseModel):
    """Stock history data model"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str 