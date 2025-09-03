import yfinance as yf
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class YFinanceClient:
    """Client using yfinance library for reliable Yahoo Finance data"""
    
    def __init__(self):
        pass
    
    def get_real_time_quote(self, ticker: str) -> Dict[str, Any]:
        """Get real-time stock quote using yfinance"""
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            if not info or 'regularMarketPrice' not in info:
                logger.warning(f"No quote data for {ticker}")
                return {}
            
            # Calculate change percentage manually to avoid YFinance errors
            current_price = info.get('regularMarketPrice', 0)
            previous_close = info.get('regularMarketPreviousClose', 0)
            change = info.get('regularMarketChange', 0)
            
            # Calculate change percentage safely
            if previous_close and previous_close > 0:
                calculated_change_pct = ((current_price - previous_close) / previous_close) * 100
                # Sanity check: if change is > 50% or < -50%, use 0 (likely data error)
                if abs(calculated_change_pct) > 50:
                    logger.warning(f"Suspicious change % for {ticker}: {calculated_change_pct:.2f}% - setting to 0")
                    calculated_change_pct = 0
            else:
                calculated_change_pct = 0
            
            return {
                'ticker': ticker.upper(),
                'price': current_price,
                'change': change,
                'change_percent': calculated_change_pct,
                'volume': info.get('regularMarketVolume', 0),
                'open': info.get('regularMarketOpen', 0),
                'high': info.get('regularMarketDayHigh', 0),
                'low': info.get('regularMarketDayLow', 0),
                'previous_close': previous_close,
                'company_name': info.get('longName') or info.get('shortName', ''),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {ticker}: {e}")
            return {}
    
    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """Get company overview using yfinance"""
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            if not info:
                return {}
            
            return {
                'symbol': ticker.upper(),
                'name': info.get('longName') or info.get('shortName', ''),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error getting company overview for {ticker}: {e}")
            return {}
    
    def get_intraday_data(self, ticker: str, interval: str = '15m') -> Dict[str, Any]:
        """Get intraday stock data using yfinance"""
        try:
            stock = yf.Ticker(ticker.upper())
            
            # Get 1 day of intraday data
            data = stock.history(period='1d', interval=interval)
            
            if data.empty:
                logger.warning(f"No intraday data for {ticker}")
                return {}
            
            # Get the latest data point
            latest = data.iloc[-1]
            
            return {
                'ticker': ticker.upper(),
                'interval': interval,
                'timestamp': latest.name.isoformat(),
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'close': latest['Close'],
                'volume': latest['Volume'],
                'data_points': len(data),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting intraday data for {ticker}: {e}")
            return {}
    
    def get_daily_data(self, ticker: str, period: str = '1mo') -> Dict[str, Any]:
        """Get daily stock data using yfinance"""
        try:
            stock = yf.Ticker(ticker.upper())
            
            # Get historical data
            data = stock.history(period=period)
            
            if data.empty:
                logger.warning(f"No daily data for {ticker}")
                return {}
            
            # Get the latest data point
            latest = data.iloc[-1]
            
            return {
                'ticker': ticker.upper(),
                'period': period,
                'timestamp': latest.name.isoformat(),
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'close': latest['Close'],
                'volume': latest['Volume'],
                'data_points': len(data),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting daily data for {ticker}: {e}")
            return {}
    
    def test_connection(self, ticker: str = "AAPL") -> bool:
        """Test if yfinance is working"""
        try:
            data = self.get_real_time_quote(ticker)
            return bool(data and data.get('price', 0) > 0)
        except Exception as e:
            logger.error(f"YFinance connection test failed: {e}")
            return False