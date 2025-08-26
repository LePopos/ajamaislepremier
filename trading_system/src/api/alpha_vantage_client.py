import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Client for Alpha Vantage API to get stock price data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 12  # 12 seconds between requests (5 per minute limit)
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: sleeping {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_real_time_quote(self, ticker: str) -> Dict[str, Any]:
        """Get real-time stock quote"""
        self._rate_limit()
        
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': ticker.upper(),
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
                return {}
            
            if 'Note' in data:
                logger.warning(f"API limit reached: {data['Note']}")
                return {}
            
            quote_data = data.get('Global Quote', {})
            
            if not quote_data:
                logger.warning(f"No quote data for {ticker}")
                return {}
            
            return {
                'ticker': ticker.upper(),
                'price': float(quote_data.get('05. price', 0)),
                'change': float(quote_data.get('09. change', 0)),
                'change_percent': quote_data.get('10. change percent', '0%').replace('%', ''),
                'volume': int(quote_data.get('06. volume', 0)),
                'open': float(quote_data.get('02. open', 0)),
                'high': float(quote_data.get('03. high', 0)),
                'low': float(quote_data.get('04. low', 0)),
                'previous_close': float(quote_data.get('08. previous close', 0)),
                'latest_trading_day': quote_data.get('07. latest trading day', ''),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {ticker}: {e}")
            return {}
    
    def get_intraday_data(self, ticker: str, interval: str = '15min') -> Dict[str, Any]:
        """Get intraday stock data (1min, 5min, 15min, 30min, 60min)"""
        self._rate_limit()
        
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': ticker.upper(),
                'interval': interval,
                'apikey': self.api_key,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
                return {}
            
            if 'Note' in data:
                logger.warning(f"API limit reached: {data['Note']}")
                return {}
            
            time_series_key = f'Time Series ({interval})'
            time_series = data.get(time_series_key, {})
            
            if not time_series:
                logger.warning(f"No intraday data for {ticker}")
                return {}
            
            # Get latest data point
            latest_time = max(time_series.keys())
            latest_data = time_series[latest_time]
            
            return {
                'ticker': ticker.upper(),
                'interval': interval,
                'timestamp': latest_time,
                'open': float(latest_data.get('1. open', 0)),
                'high': float(latest_data.get('2. high', 0)),
                'low': float(latest_data.get('3. low', 0)),
                'close': float(latest_data.get('4. close', 0)),
                'volume': int(latest_data.get('5. volume', 0)),
                'data_points': len(time_series),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting intraday data for {ticker}: {e}")
            return {}
    
    def get_daily_data(self, ticker: str, outputsize: str = 'compact') -> Dict[str, Any]:
        """Get daily stock data (outputsize: 'compact' = 100 days, 'full' = 20+ years)"""
        self._rate_limit()
        
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': ticker.upper(),
                'apikey': self.api_key,
                'outputsize': outputsize
            }
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
                return {}
            
            if 'Note' in data:
                logger.warning(f"API limit reached: {data['Note']}")
                return {}
            
            time_series = data.get('Time Series (Daily)', {})
            
            if not time_series:
                logger.warning(f"No daily data for {ticker}")
                return {}
            
            # Get latest data point
            latest_date = max(time_series.keys())
            latest_data = time_series[latest_date]
            
            return {
                'ticker': ticker.upper(),
                'date': latest_date,
                'open': float(latest_data.get('1. open', 0)),
                'high': float(latest_data.get('2. high', 0)),
                'low': float(latest_data.get('3. low', 0)),
                'close': float(latest_data.get('4. close', 0)),
                'volume': int(latest_data.get('5. volume', 0)),
                'data_points': len(time_series),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting daily data for {ticker}: {e}")
            return {}
    
    def get_technical_indicators(self, ticker: str, indicator: str = 'RSI', 
                               time_period: int = 14, interval: str = 'daily') -> Dict[str, Any]:
        """Get technical indicators (RSI, MACD, SMA, EMA, etc.)"""
        self._rate_limit()
        
        try:
            params = {
                'function': indicator.upper(),
                'symbol': ticker.upper(),
                'interval': interval,
                'time_period': time_period,
                'series_type': 'close',
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
                return {}
            
            if 'Note' in data:
                logger.warning(f"API limit reached: {data['Note']}")
                return {}
            
            # The key varies by indicator
            indicator_key = f'Technical Analysis: {indicator.upper()}'
            indicator_data = data.get(indicator_key, {})
            
            if not indicator_data:
                logger.warning(f"No {indicator} data for {ticker}")
                return {}
            
            # Get latest data point
            latest_date = max(indicator_data.keys())
            latest_value = indicator_data[latest_date]
            
            return {
                'ticker': ticker.upper(),
                'indicator': indicator.upper(),
                'date': latest_date,
                'value': float(list(latest_value.values())[0]) if latest_value else 0,
                'time_period': time_period,
                'interval': interval,
                'data_points': len(indicator_data),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting {indicator} for {ticker}: {e}")
            return {}
    
    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """Get company fundamental data"""
        self._rate_limit()
        
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker.upper(),
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
                return {}
            
            if not data or data.get('Symbol') is None:
                logger.warning(f"No company overview for {ticker}")
                return {}
            
            return {
                'ticker': ticker.upper(),
                'name': data.get('Name', ''),
                'sector': data.get('Sector', ''),
                'industry': data.get('Industry', ''),
                'market_cap': data.get('MarketCapitalization', ''),
                'pe_ratio': data.get('PERatio', ''),
                'peg_ratio': data.get('PEGRatio', ''),
                'dividend_yield': data.get('DividendYield', ''),
                'eps': data.get('EPS', ''),
                'beta': data.get('Beta', ''),
                '52_week_high': data.get('52WeekHigh', ''),
                '52_week_low': data.get('52WeekLow', ''),
                'analyst_target_price': data.get('AnalystTargetPrice', ''),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting company overview for {ticker}: {e}")
            return {}
    
    def get_comprehensive_data(self, ticker: str) -> Dict[str, Any]:
        """Get comprehensive stock data in one call"""
        quote = self.get_real_time_quote(ticker)
        overview = self.get_company_overview(ticker)
        rsi = self.get_technical_indicators(ticker, 'RSI')
        
        return {
            'ticker': ticker.upper(),
            'quote': quote,
            'overview': overview,
            'technical': {'rsi': rsi},
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_multiple_quotes_async(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple stocks with proper rate limiting"""
        results = {}
        
        # Process in batches to respect rate limits
        for i, ticker in enumerate(tickers):
            if i > 0:  # Rate limit between requests
                await asyncio.sleep(self.min_request_interval)
            
            quote = self.get_real_time_quote(ticker)
            results[ticker] = quote
            
            logger.info(f"Fetched quote for {ticker} ({i+1}/{len(tickers)})")
        
        return results
    
    def __del__(self):
        """Close session on cleanup"""
        if hasattr(self, 'session'):
            self.session.close()