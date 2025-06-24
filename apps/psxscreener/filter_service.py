import pandas as pd
import numpy as np
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta, date
import json

from .schemas import StockData, FilterCriteria

logger = logging.getLogger(__name__)

class StockFilterService:
    def __init__(self):
        self._cache = {}
        self._cache_timestamp = None
        self.cache_ttl = timedelta(minutes=15)  # Cache expiration time
    
    def _cache_key(self, date_str: Optional[str] = None) -> str:
        """Generate a cache key for the stock data"""
        if date_str:
            return f"stock_data_{date_str}"
        return "stock_data_latest"
    
    def is_cache_valid(self, key: str) -> bool:
        """Check if cache is still valid"""
        if key not in self._cache or not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < self.cache_ttl
    
    def validate_stock_data(self, raw_data: List[Dict[str, Any]]) -> List[StockData]:
        """
        Validate and normalize stock data using pydantic models
        """
        validated_data = []
        errors = []
        
        for idx, item in enumerate(raw_data):
            try:
                # Process through pydantic model to validate and normalize
                stock = StockData(**item)
                validated_data.append(stock)
            except Exception as e:
                # Log validation errors but continue processing
                errors.append(f"Error validating stock #{idx}: {str(e)}")
                logger.warning(f"Validation error for stock data: {str(e)}")
        
        if errors:
            logger.warning(f"Encountered {len(errors)} validation errors out of {len(raw_data)} stocks")
        
        logger.info(f"Validated {len(validated_data)} stocks successfully")
        return validated_data
    
    def to_dataframe(self, validated_data: List[StockData]) -> pd.DataFrame:
        """
        Convert list of pydantic models to pandas DataFrame
        """
        # Convert pydantic models to dictionaries
        dict_data = [stock.dict() for stock in validated_data]
        
        # Create DataFrame
        df = pd.DataFrame(dict_data)
        
        # Process numeric columns to handle None values properly
        numeric_columns = ['CurrentPrice', 'ChangePercentage', 'Volume', 'OpenPrice', 
                          'HighPrice', 'LowPrice', 'VWAP', 'PE', 'MarketCap', 'DividendYield']
        
        for col in numeric_columns:
            if col in df.columns:
                # Convert None to NaN for proper pandas numeric handling
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure date column is properly formatted if present
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        
        return df
    
    def build_filter_conditions(self, filter_criteria: FilterCriteria) -> Dict[str, Any]:
        """
        Build filter conditions based on user filter criteria
        Returns a dictionary of conditions that can be applied to the DataFrame
        """
        conditions = {}
        
        # Symbol filter (case-insensitive partial match)
        if filter_criteria.symbol:
            conditions['symbol'] = {
                'column': 'Symbol',
                'type': 'contains',
                'value': filter_criteria.symbol.upper()
            }
        
        # Country filter (exact match case-insensitive)
        if filter_criteria.country and filter_criteria.country.lower() != 'any':
            conditions['country'] = {
                'column': 'Country',
                'type': 'exact',
                'value': filter_criteria.country
            }
        
        # Exchange filter
        if filter_criteria.exchange and filter_criteria.exchange.lower() != 'any':
            conditions['exchange'] = {
                'column': 'Exchange',
                'type': 'exact',
                'value': filter_criteria.exchange
            }
        
        # Sector filter
        if filter_criteria.sector and filter_criteria.sector.lower() != 'any':
            conditions['sector'] = {
                'column': 'Sector',
                'type': 'exact',
                'value': filter_criteria.sector
            }
        
        # Industry filter
        if filter_criteria.industry and filter_criteria.industry.lower() != 'any':
            conditions['industry'] = {
                'column': 'Industry',
                'type': 'exact',
                'value': filter_criteria.industry
            }
        
        # Market Cap filter
        if filter_criteria.market_cap and filter_criteria.market_cap.lower() != 'any':
            cap_filter = filter_criteria.market_cap
            if cap_filter.startswith('Mega'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'gte', 
                    'value': 200_000_000_000
                }
            elif cap_filter.startswith('Large'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'gte', 
                    'value': 10_000_000_000
                }
            elif cap_filter.startswith('Mid'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'gte', 
                    'value': 2_000_000_000
                }
            elif cap_filter.startswith('Small'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'gte', 
                    'value': 300_000_000
                }
            elif cap_filter.startswith('Micro'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'gte', 
                    'value': 50_000_000
                }
            elif cap_filter.startswith('Nano'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'lt', 
                    'value': 50_000_000
                }
            elif cap_filter.startswith('-Mega'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'lt', 
                    'value': 200_000_000_000
                }
            elif cap_filter.startswith('-Large'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'lt', 
                    'value': 10_000_000_000
                }
            elif cap_filter.startswith('-Mid'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'lt', 
                    'value': 2_000_000_000
                }
            elif cap_filter.startswith('-Small'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'lt', 
                    'value': 300_000_000
                }
            elif cap_filter.startswith('-Micro'):
                conditions['market_cap'] = {
                    'column': 'MarketCap', 
                    'type': 'lt', 
                    'value': 50_000_000
                }
            elif cap_filter.startswith('Over'):
                # Extract numeric value from string like "Over 10B"
                value_str = cap_filter.replace('Over ', '').replace('B', '000000000').replace('M', '000000')
                try:
                    value = float(value_str)
                    conditions['market_cap'] = {
                        'column': 'MarketCap', 
                        'type': 'gte', 
                        'value': value
                    }
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse market cap filter value: {cap_filter}")
            elif cap_filter.startswith('Under'):
                # Extract numeric value from string like "Under 5B"
                value_str = cap_filter.replace('Under ', '').replace('B', '000000000').replace('M', '000000')
                try:
                    value = float(value_str)
                    conditions['market_cap'] = {
                        'column': 'MarketCap', 
                        'type': 'lt', 
                        'value': value
                    }
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse market cap filter value: {cap_filter}")
        
        # P/E filter
        if filter_criteria.pe_ratio and filter_criteria.pe_ratio.lower() != 'any':
            pe_filter = filter_criteria.pe_ratio
            
            if pe_filter == 'Low (<15)':
                conditions['pe'] = {
                    'column': 'PE',
                    'type': 'between',
                    'value': (0, 15)
                }
            elif pe_filter == 'Profitable (>0)':
                conditions['pe'] = {
                    'column': 'PE',
                    'type': 'gt',
                    'value': 0
                }
            elif pe_filter == 'High (>50)':
                conditions['pe'] = {
                    'column': 'PE',
                    'type': 'gt',
                    'value': 50
                }
            elif pe_filter == 'Negative (<0)':
                conditions['pe'] = {
                    'column': 'PE',
                    'type': 'lt',
                    'value': 0
                }
            elif pe_filter.startswith('Under'):
                try:
                    # Extract the numeric part, e.g. "Under 10" -> 10
                    value = float(pe_filter.replace('Under ', ''))
                    conditions['pe'] = {
                        'column': 'PE',
                        'type': 'lt',
                        'value': value
                    }
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse P/E filter value: {pe_filter}")
            elif pe_filter.startswith('Over'):
                try:
                    # Extract the numeric part, e.g. "Over 20" -> 20
                    value = float(pe_filter.replace('Over ', ''))
                    conditions['pe'] = {
                        'column': 'PE',
                        'type': 'gt',
                        'value': value
                    }
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse P/E filter value: {pe_filter}")
        
        # Dividend Yield filter
        div_yield_filter = filter_criteria.div_yield
        if div_yield_filter and div_yield_filter.lower() != 'any':
            stock_key = 'DividendYield'
            if div_yield_filter == 'none':
                conditions[stock_key] = {
                    'column': stock_key,
                    'type': 'eq',
                    'value': 0
                }
            elif div_yield_filter == 'positive':
                conditions[stock_key] = {
                    'column': stock_key,
                    'type': 'gt',
                    'value': 0
                }
            elif div_yield_filter == 'high':
                conditions[stock_key] = {
                    'column': stock_key,
                    'type': 'gt',
                    'value': 3
                }
            elif div_yield_filter == 'very high':
                conditions[stock_key] = {
                    'column': stock_key,
                    'type': 'gt',
                    'value': 6
                }
            elif 'over' in div_yield_filter:
                # Extract percentage value
                pct = float(div_yield_filter.split(' ')[1].replace('%', ''))
                conditions[stock_key] = {
                    'column': stock_key,
                    'type': 'gt',
                    'value': pct
                }
            elif 'under' in div_yield_filter:
                pct = float(div_yield_filter.split(' ')[1].replace('%', ''))
                conditions[stock_key] = {
                    'column': stock_key,
                    'type': 'lt',
                    'value': pct
                }
        
        # Add other filters as needed...
        # For each filter, check if it's set (not None or "any") then add appropriate condition
        
        # These are examples of more filters you can add:
        
        # Index filter
        if filter_criteria.index and filter_criteria.index.lower() != 'any':
            conditions['index'] = {
                'column': 'Index',  # Assumes you have an Index column
                'type': 'exact',
                'value': filter_criteria.index
            }
        
        # Price filter
        if filter_criteria.price and filter_criteria.price.lower() != 'any':
            price_filter = filter_criteria.price
            
            try:
                if price_filter.startswith('Under'):
                    # Extract numeric value safely
                    if 'PKR' in price_filter:
                        value = float(price_filter.replace('Under PKR', ''))
                    else:
                        value = float(''.join(c for c in price_filter.replace('Under ', '') if c.isdigit() or c == '.'))
                    
                    conditions['price'] = {
                        'column': 'CurrentPrice',
                        'type': 'lt',
                        'value': value
                    }
                elif price_filter.startswith('Over'):
                    # Extract numeric value safely
                    if 'PKR' in price_filter:
                        value = float(price_filter.replace('Over PKR', ''))
                    else:
                        value = float(''.join(c for c in price_filter.replace('Over ', '') if c.isdigit() or c == '.'))
                    
                    conditions['price'] = {
                        'column': 'CurrentPrice',
                        'type': 'gt',
                        'value': value
                    }
                elif ' to ' in price_filter:
                    # Parse range like "PKR50 to PKR100"
                    range_parts = price_filter.split(' to ')
                    
                    # Parse min value
                    min_part = range_parts[0]
                    if 'PKR' in min_part:
                        min_val = float(min_part.replace('PKR', ''))
                    else:
                        min_val = float(''.join(c for c in min_part if c.isdigit() or c == '.'))
                    
                    # Parse max value
                    max_part = range_parts[1]
                    if 'PKR' in max_part:
                        max_val = float(max_part.replace('PKR', ''))
                    else:
                        max_val = float(''.join(c for c in max_part if c.isdigit() or c == '.'))
                    
                    conditions['price'] = {
                        'column': 'CurrentPrice',
                        'type': 'between',
                        'value': (min_val, max_val)
                    }
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"Could not parse price filter value: {price_filter}. Error: {str(e)}")
        
        # P/B Ratio filter
        if filter_criteria.pb_ratio and filter_criteria.pb_ratio.lower() != 'any':
            pb_filter = filter_criteria.pb_ratio
            
            try:
                if pb_filter.startswith('Under'):
                    # Extract numeric value
                    value = float(pb_filter.replace('Under ', '').split(' ')[0])
                    conditions['pb_ratio'] = {
                        'column': 'PB',  # Assume PB column exists
                        'type': 'lt',
                        'value': value
                    }
                elif pb_filter.startswith('Over'):
                    # Extract numeric value
                    value = float(pb_filter.replace('Over ', '').split(' ')[0])
                    conditions['pb_ratio'] = {
                        'column': 'PB',
                        'type': 'gt',
                        'value': value
                    }
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"Could not parse P/B filter value: {pb_filter}. Error: {str(e)}")
        
        # P/S Ratio filter
        if filter_criteria.ps_ratio and filter_criteria.ps_ratio.lower() != 'any':
            ps_filter = filter_criteria.ps_ratio
            
            try:
                if ps_filter.startswith('Under'):
                    # Extract numeric value
                    value = float(ps_filter.replace('Under ', '').split(' ')[0])
                    conditions['ps_ratio'] = {
                        'column': 'PS',  # Assume PS column exists
                        'type': 'lt',
                        'value': value
                    }
                elif ps_filter.startswith('Over'):
                    # Extract numeric value
                    value = float(ps_filter.replace('Over ', '').split(' ')[0])
                    conditions['ps_ratio'] = {
                        'column': 'PS',
                        'type': 'gt',
                        'value': value
                    }
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"Could not parse P/S filter value: {ps_filter}. Error: {str(e)}")
        
        # 52-Week Range filter
        if filter_criteria.year_range and filter_criteria.year_range.lower() != 'any':
            year_filter = filter_criteria.year_range
            
            # Determine condition based on selection
            if year_filter == 'Near High':
                conditions['year_range'] = {
                    'column': 'YearHighRatio',  # Percentage of 52-week high (e.g., CurrentPrice / YearHigh * 100)
                    'type': 'gte',
                    'value': 90  # 90% or higher of 52-week high
                }
            elif year_filter == 'Near Low':
                conditions['year_range'] = {
                    'column': 'YearLowRatio',  # Percentage above 52-week low (e.g., (CurrentPrice - YearLow) / YearLow * 100)
                    'type': 'lte',
                    'value': 10  # Within 10% of 52-week low
                }
            elif year_filter == 'New High':
                conditions['year_range'] = {
                    'column': 'IsNewHigh',  # Boolean flag for new high
                    'type': 'eq',
                    'value': True
                }
            elif year_filter == 'New Low':
                conditions['year_range'] = {
                    'column': 'IsNewLow',  # Boolean flag for new low
                    'type': 'eq',
                    'value': True
                }
            elif year_filter == 'Upper Half':
                conditions['year_range'] = {
                    'column': 'YearRangePercentile',  # Position in 52-week range (0-100%)
                    'type': 'gte',
                    'value': 50  # Upper half of range
                }
            elif year_filter == 'Lower Half':
                conditions['year_range'] = {
                    'column': 'YearRangePercentile',  # Position in 52-week range (0-100%)
                    'type': 'lt',
                    'value': 50  # Lower half of range
                }
        
        # RSI filter
        if filter_criteria.rsi and filter_criteria.rsi.lower() != 'any':
            rsi_filter = filter_criteria.rsi
            
            if rsi_filter == 'Overbought (>70)':
                conditions['rsi'] = {
                    'column': 'RSI14',  # 14-day RSI
                    'type': 'gt',
                    'value': 70
                }
            elif rsi_filter == 'Oversold (<30)':
                conditions['rsi'] = {
                    'column': 'RSI14',
                    'type': 'lt',
                    'value': 30
                }
            elif rsi_filter == 'Over 80':
                conditions['rsi'] = {
                    'column': 'RSI14',
                    'type': 'gt',
                    'value': 80
                }
            elif rsi_filter == 'Under 20':
                conditions['rsi'] = {
                    'column': 'RSI14',
                    'type': 'lt',
                    'value': 20
                }
            elif rsi_filter == 'Between 40-60':
                conditions['rsi'] = {
                    'column': 'RSI14',
                    'type': 'between',
                    'value': (40, 60)
                }
            elif rsi_filter == 'Between 50-70':
                conditions['rsi'] = {
                    'column': 'RSI14',
                    'type': 'between',
                    'value': (50, 70)
                }
            elif rsi_filter == 'Between 30-50':
                conditions['rsi'] = {
                    'column': 'RSI14',
                    'type': 'between',
                    'value': (30, 50)
                }
        
        # Moving Average (50-day) filter
        if filter_criteria.ma_50 and filter_criteria.ma_50.lower() != 'any':
            ma_filter = filter_criteria.ma_50
            
            if ma_filter == 'Price Above MA':
                conditions['ma_50'] = {
                    'column': 'PriceToMA50Ratio',  # Price / 50-day MA ratio
                    'type': 'gt',
                    'value': 1
                }
            elif ma_filter == 'Price Below MA':
                conditions['ma_50'] = {
                    'column': 'PriceToMA50Ratio',
                    'type': 'lt',
                    'value': 1
                }
            elif ma_filter == 'Price 10% Above MA':
                conditions['ma_50'] = {
                    'column': 'PriceToMA50Ratio',
                    'type': 'gt',
                    'value': 1.1
                }
            elif ma_filter == 'Price 10% Below MA':
                conditions['ma_50'] = {
                    'column': 'PriceToMA50Ratio',
                    'type': 'lt',
                    'value': 0.9
                }
            elif ma_filter == 'MA Rising':
                conditions['ma_50'] = {
                    'column': 'MA50Direction',  # Direction indicator (e.g., 1 for rising, -1 for falling)
                    'type': 'gt',
                    'value': 0
                }
            elif ma_filter == 'MA Falling':
                conditions['ma_50'] = {
                    'column': 'MA50Direction',
                    'type': 'lt',
                    'value': 0
                }
            elif ma_filter == 'Crossed Above':
                conditions['ma_50'] = {
                    'column': 'CrossedAboveMA50',  # Boolean flag for recent cross above
                    'type': 'eq',
                    'value': True
                }
            elif ma_filter == 'Crossed Below':
                conditions['ma_50'] = {
                    'column': 'CrossedBelowMA50',  # Boolean flag for recent cross below
                    'type': 'eq',
                    'value': True
                }
        
        # Moving Average (200-day) filter
        if filter_criteria.ma_200 and filter_criteria.ma_200.lower() != 'any':
            ma_filter = filter_criteria.ma_200
            
            if ma_filter == 'Price Above MA':
                conditions['ma_200'] = {
                    'column': 'PriceToMA200Ratio',  # Price / 200-day MA ratio
                    'type': 'gt',
                    'value': 1
                }
            elif ma_filter == 'Price Below MA':
                conditions['ma_200'] = {
                    'column': 'PriceToMA200Ratio',
                    'type': 'lt',
                    'value': 1
                }
            elif ma_filter == 'Price 10% Above MA':
                conditions['ma_200'] = {
                    'column': 'PriceToMA200Ratio',
                    'type': 'gt',
                    'value': 1.1
                }
            elif ma_filter == 'Price 10% Below MA':
                conditions['ma_200'] = {
                    'column': 'PriceToMA200Ratio',
                    'type': 'lt',
                    'value': 0.9
                }
            elif ma_filter == 'MA Rising':
                conditions['ma_200'] = {
                    'column': 'MA200Direction',  # Direction indicator (e.g., 1 for rising, -1 for falling)
                    'type': 'gt',
                    'value': 0
                }
            elif ma_filter == 'MA Falling':
                conditions['ma_200'] = {
                    'column': 'MA200Direction',
                    'type': 'lt',
                    'value': 0
                }
            elif ma_filter == 'Crossed Above':
                conditions['ma_200'] = {
                    'column': 'CrossedAboveMA200',  # Boolean flag for recent cross above
                    'type': 'eq',
                    'value': True
                }
            elif ma_filter == 'Crossed Below':
                conditions['ma_200'] = {
                    'column': 'CrossedBelowMA200',  # Boolean flag for recent cross below
                    'type': 'eq',
                    'value': True
                }
        
        # Volume Trend filter
        if filter_criteria.volume_trend and filter_criteria.volume_trend.lower() != 'any':
            vol_filter = filter_criteria.volume_trend
            
            if vol_filter == 'Increasing':
                conditions['volume_trend'] = {
                    'column': 'VolumeTrend',  # Volume trend indicator (positive for increasing)
                    'type': 'gt',
                    'value': 0
                }
            elif vol_filter == 'Decreasing':
                conditions['volume_trend'] = {
                    'column': 'VolumeTrend',
                    'type': 'lt',
                    'value': 0
                }
            elif vol_filter == 'Above Average':
                conditions['volume_trend'] = {
                    'column': 'VolumeToAvgRatio',  # Current volume / avg volume ratio
                    'type': 'gt',
                    'value': 1
                }
            elif vol_filter == 'Below Average':
                conditions['volume_trend'] = {
                    'column': 'VolumeToAvgRatio',
                    'type': 'lt',
                    'value': 1
                }
            elif vol_filter == 'Unusual High':
                conditions['volume_trend'] = {
                    'column': 'VolumeToAvgRatio',
                    'type': 'gt',
                    'value': 3  # Volume 3x average
                }
            elif vol_filter == 'Unusual Low':
                conditions['volume_trend'] = {
                    'column': 'VolumeToAvgRatio',
                    'type': 'lt',
                    'value': 0.33  # Volume 1/3 of average
                }
        
        return conditions
    
    def apply_filters(self, df: pd.DataFrame, conditions: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply the filter conditions to a pandas DataFrame
        Returns filtered DataFrame
        """
        if not conditions:
            return df
        
        mask = pd.Series(True, index=df.index)
        
        for condition_id, condition in conditions.items():
            column = condition['column']
            filter_type = condition['type']
            value = condition['value']
            
            # Skip if column doesn't exist in DataFrame
            if column not in df.columns:
                self.logger.warning(f"Column '{column}' not found in DataFrame")
                continue
            
            # Apply appropriate filter based on type
            try:
                if filter_type == 'exact':
                    # Case-insensitive exact match
                    if df[column].dtype == 'object':  # string column
                        sub_mask = df[column].str.lower() == str(value).lower()
                    else:
                        sub_mask = df[column] == value
                    
                elif filter_type == 'contains':
                    # Case-insensitive contains match
                    sub_mask = df[column].str.contains(value, case=False, na=False)
                    
                elif filter_type == 'gt':
                    # Greater than
                    sub_mask = df[column] > value
                    
                elif filter_type == 'gte':
                    # Greater than or equal
                    sub_mask = df[column] >= value
                    
                elif filter_type == 'lt':
                    # Less than
                    sub_mask = df[column] < value
                    
                elif filter_type == 'lte':
                    # Less than or equal
                    sub_mask = df[column] <= value
                    
                elif filter_type == 'eq':
                    # Equal to
                    sub_mask = df[column] == value
                    
                elif filter_type == 'neq':
                    # Not equal to
                    sub_mask = df[column] != value
                    
                elif filter_type == 'between':
                    # Between range (inclusive)
                    min_val, max_val = value
                    sub_mask = (df[column] >= min_val) & (df[column] <= max_val)
                    
                elif filter_type == 'in':
                    # Value in list
                    sub_mask = df[column].isin(value)
                    
                else:
                    self.logger.warning(f"Unknown filter type: {filter_type}")
                    continue
                
                # Replace NaN values in mask with False
                sub_mask = sub_mask.fillna(False)
                
                # Combine with overall mask
                mask = mask & sub_mask
                
                # Log the effect of this filter
                remaining = mask.sum()
                total = len(df)
                pct = (remaining / total) * 100 if total > 0 else 0
                self.logger.info(f"Filter '{condition_id}' ({column} {filter_type} {value}) kept {remaining}/{total} rows ({pct:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"Error applying filter '{condition_id}': {str(e)}")
        
        # Return filtered DataFrame
        filtered_df = df[mask]
        self.logger.info(f"Applied {len(conditions)} filters, kept {len(filtered_df)}/{len(df)} rows ({len(filtered_df)/len(df)*100 if len(df)>0 else 0:.1f}%)")
        return filtered_df
    
    def to_dict_list(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame back to list of dictionaries for output"""
        # Convert NaN values to None for better JSON serialization
        return json.loads(df.where(pd.notna(df), None).to_json(orient='records', date_format='iso'))
    
    def filter_stocks(self, stock_data: List[Dict[str, Any]], filter_criteria: Union[Dict[str, Any], FilterCriteria]) -> List[Dict[str, Any]]:
        """
        Main filter method that orchestrates the entire filtering process:
        1. Validate input data with pydantic models
        2. Convert to pandas DataFrame
        3. Build filter conditions
        4. Apply filters
        5. Return results
        """
        # Convert filter_criteria to proper model if it's a dict
        if isinstance(filter_criteria, dict):
            filter_criteria = FilterCriteria(**filter_criteria)
        
        # Check if we have any active filter criteria
        has_filters = False
        for field, value in filter_criteria.dict(exclude_unset=True).items():
            if value is not None and value != '':
                has_filters = True
                break
        
        if not has_filters:
            logger.info("No active filters provided, returning all stock data")
            return stock_data
        
        # Step 1: Validate and normalize stock data
        validated_data = self.validate_stock_data(stock_data)
        
        # Step 2: Convert to pandas DataFrame
        df = self.to_dataframe(validated_data)
        
        # Log dataframe info for debugging
        logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        logger.debug(f"DataFrame shape: {df.shape}")
        
        # Step 3: Build filter conditions
        conditions = self.build_filter_conditions(filter_criteria)
        
        if not conditions:
            logger.info("No filter conditions generated, returning all stock data")
            return self.to_dict_list(df)
        
        # Step 4: Apply filters
        filtered_df = self.apply_filters(df, conditions)
        
        # Step 5: Convert back to dict list for output
        result = self.to_dict_list(filtered_df)
        
        return result 