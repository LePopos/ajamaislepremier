import requests
import json
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import time
import re

logger = logging.getLogger(__name__)

class YahooFinanceClient:
    """Client for Yahoo Finance API to get stock price data - free and reliable"""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.quote_url = "https://query1.finance.yahoo.com/v7/finance/quote"
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Very light rate limiting (10 requests/sec)
        
        # Headers to mimic browser requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        self.session.headers.update(self.headers)
    
    def _rate_limit(self):
        """Light rate limiting to be respectful"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_real_time_quote(self, ticker: str) -> Dict[str, Any]:
        """Get real-time stock quote from Yahoo Finance"""
        self._rate_limit()
        
        try:
            params = {
                'symbols': ticker.upper(),
                'fields': 'regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketVolume,regularMarketOpen,regularMarketDayHigh,regularMarketDayLow,regularMarketPreviousClose,longName,shortName'
            }
            
            response = self.session.get(self.quote_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'quoteResponse' not in data or 'result' not in data['quoteResponse']:
                logger.warning(f"Invalid response structure for {ticker}")
                return {}
            
            quotes = data['quoteResponse']['result']
            if not quotes:
                logger.warning(f"No quote data for {ticker}")
                return {}
            
            quote = quotes[0]
            
            # Extract the data with safe gets
            return {
                'ticker': ticker.upper(),
                'price': quote.get('regularMarketPrice', 0),
                'change': quote.get('regularMarketChange', 0),
                'change_percent': quote.get('regularMarketChangePercent', 0),
                'volume': quote.get('regularMarketVolume', 0),
                'open': quote.get('regularMarketOpen', 0),
                'high': quote.get('regularMarketDayHigh', 0),
                'low': quote.get('regularMarketDayLow', 0),
                'previous_close': quote.get('regularMarketPreviousClose', 0),
                'company_name': quote.get('longName') or quote.get('shortName', ''),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {ticker}: {e}")
            return {}
    
    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """Get company overview - simplified for Yahoo Finance"""
        try:
            # Get basic info from quote call
            quote_data = self.get_real_time_quote(ticker)
            
            if not quote_data:
                return {}
            
            return {
                'symbol': ticker.upper(),
                'name': quote_data.get('company_name', ''),
                'sector': 'Unknown',  # Yahoo Finance free API doesn't provide this easily
                'industry': 'Unknown',
                'market_cap': 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"Error getting company overview for {ticker}: {e}")
            return {}
    
    def get_intraday_data(self, ticker: str, interval: str = '15m') -> Dict[str, Any]:
        """Get intraday stock data"""
        self._rate_limit()
        
        try:
            # Yahoo Finance intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            params = {
                'interval': interval,
                'range': '1d',  # Get today's data
                'includePrePost': 'false'
            }
            
            url = f"{self.base_url}/{ticker.upper()}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or 'result' not in data['chart']:
                logger.warning(f"Invalid chart data for {ticker}")
                return {}
            
            results = data['chart']['result']
            if not results:
                logger.warning(f"No intraday data for {ticker}")
                return {}
            
            chart_data = results[0]
            
            # Get the latest data point
            timestamps = chart_data.get('timestamp', [])
            indicators = chart_data.get('indicators', {})
            quotes = indicators.get('quote', [{}])[0]
            
            if not timestamps or not quotes:
                logger.warning(f"No valid intraday data for {ticker}")
                return {}
            
            # Get latest values (last in arrays)
            latest_idx = -1
            
            return {
                'ticker': ticker.upper(),
                'interval': interval,
                'timestamp': datetime.fromtimestamp(timestamps[latest_idx]).isoformat(),
                'open': quotes.get('open', [0])[latest_idx] or 0,
                'high': quotes.get('high', [0])[latest_idx] or 0,
                'low': quotes.get('low', [0])[latest_idx] or 0,
                'close': quotes.get('close', [0])[latest_idx] or 0,
                'volume': quotes.get('volume', [0])[latest_idx] or 0,
                'data_points': len(timestamps),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting intraday data for {ticker}: {e}")
            return {}
    
    def get_daily_data(self, ticker: str, period: str = '1mo') -> Dict[str, Any]:
        """Get daily stock data"""
        self._rate_limit()
        
        try:
            params = {
                'interval': '1d',
                'range': period  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            }
            
            url = f"{self.base_url}/{ticker.upper()}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or 'result' not in data['chart']:
                logger.warning(f"Invalid daily data for {ticker}")
                return {}
            
            results = data['chart']['result']
            if not results:
                logger.warning(f"No daily data for {ticker}")
                return {}
            
            chart_data = results[0]
            
            timestamps = chart_data.get('timestamp', [])
            indicators = chart_data.get('indicators', {})
            quotes = indicators.get('quote', [{}])[0]
            
            if not timestamps or not quotes:
                return {}
            
            # Get latest values
            latest_idx = -1
            
            return {
                'ticker': ticker.upper(),
                'period': period,
                'timestamp': datetime.fromtimestamp(timestamps[latest_idx]).isoformat(),
                'open': quotes.get('open', [0])[latest_idx] or 0,
                'high': quotes.get('high', [0])[latest_idx] or 0,
                'low': quotes.get('low', [0])[latest_idx] or 0,
                'close': quotes.get('close', [0])[latest_idx] or 0,
                'volume': quotes.get('volume', [0])[latest_idx] or 0,
                'data_points': len(timestamps),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting daily data for {ticker}: {e}")
            return {}
    
    def test_connection(self, ticker: str = "AAPL") -> bool:
        """Test if Yahoo Finance API is working"""
        try:
            data = self.get_real_time_quote(ticker)
            return bool(data and data.get('price', 0) > 0)
        except Exception as e:
            logger.error(f"Yahoo Finance connection test failed: {e}")
            return False