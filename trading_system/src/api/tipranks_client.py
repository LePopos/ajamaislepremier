import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TipRanksClient:
    """Client for TipRanks API to get analyst recommendations and Smart Scores"""
    
    def __init__(self, proxy_url: Optional[str] = None):
        self.base_url = "https://www.tipranks.com/api/stocks"
        self.session = requests.Session()
        self.proxy_url = proxy_url
        
        # Headers to mimic browser requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tipranks.com/',
            'Origin': 'https://www.tipranks.com'
        }
        self.session.headers.update(self.headers)
    
    def get_price_targets(self, ticker: str) -> Dict[str, Any]:
        """Get analyst price targets for a stock"""
        try:
            url = f"{self.base_url}/getPriceTargets/"
            params = {'name': ticker.upper()}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'priceTargets' not in data:
                logger.warning(f"No price target data for {ticker}")
                return {}
            
            price_data = data['priceTargets'][0] if data['priceTargets'] else {}
            
            return {
                'ticker': ticker.upper(),
                'mean_target': price_data.get('priceTargetAverage'),
                'median_target': price_data.get('priceTargetMedian'),
                'high_target': price_data.get('priceTargetHigh'),
                'low_target': price_data.get('priceTargetLow'),
                'num_analysts': price_data.get('numOfAnalysts', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting price targets for {ticker}: {e}")
            return {}
    
    def get_news_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Get news sentiment data for a stock"""
        try:
            url = f"{self.base_url}/getNewsSentimentData/"
            params = {'name': ticker.upper()}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No sentiment data for {ticker}")
                return {}
            
            return {
                'ticker': ticker.upper(),
                'bullish_percent': data.get('bullishPercent', 0),
                'bearish_percent': data.get('bearishPercent', 0),
                'news_score': data.get('score', 0),
                'articles_count': data.get('buzz', {}).get('articlesInLastWeek', 0),
                'buzz_avg': data.get('buzz', {}).get('weeklyAverage', 0),
                'sector_avg': data.get('sectorAverageBullishPercent', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment for {ticker}: {e}")
            return {}
    
    def get_smart_score(self, ticker: str) -> Dict[str, Any]:
        """Get TipRanks Smart Score for a stock (1-10 scale)"""
        try:
            # Smart Score is typically embedded in the main stock data
            url = f"{self.base_url}/getData/"
            params = {'name': ticker.upper()}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No data for {ticker}")
                return {}
            
            # Extract Smart Score from the response
            smart_score = data.get('portfolioHoldingData', {}).get('smartScore')
            if smart_score is None:
                smart_score = data.get('smartScore')
            
            return {
                'ticker': ticker.upper(),
                'smart_score': smart_score,
                'score_meaning': self._interpret_smart_score(smart_score),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Smart Score for {ticker}: {e}")
            return {}
    
    def get_trending_stocks(self) -> List[Dict[str, Any]]:
        """Get currently trending stocks"""
        try:
            url = f"{self.base_url}/getTrendingStocks/"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'stocks' not in data:
                logger.warning("No trending stocks data")
                return []
            
            trending = []
            for stock in data['stocks'][:20]:  # Limit to top 20
                trending.append({
                    'ticker': stock.get('ticker', '').upper(),
                    'company_name': stock.get('companyFullName', ''),
                    'smart_score': stock.get('smartScore'),
                    'price_target': stock.get('priceTargetAverage'),
                    'consensus': stock.get('consensusRecommendation'),
                    'timestamp': datetime.now().isoformat()
                })
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting trending stocks: {e}")
            return []
    
    def get_comprehensive_data(self, ticker: str) -> Dict[str, Any]:
        """Get all available data for a ticker in one call"""
        price_targets = self.get_price_targets(ticker)
        sentiment = self.get_news_sentiment(ticker)
        smart_score = self.get_smart_score(ticker)
        
        return {
            'ticker': ticker.upper(),
            'price_targets': price_targets,
            'sentiment': sentiment,
            'smart_score': smart_score,
            'timestamp': datetime.now().isoformat()
        }
    
    def _interpret_smart_score(self, score: Optional[int]) -> str:
        """Interpret Smart Score meaning"""
        if score is None:
            return "No Score"
        elif score >= 8:
            return "Strong Buy"
        elif score >= 6:
            return "Buy"
        elif score >= 4:
            return "Hold"
        elif score >= 2:
            return "Sell"
        else:
            return "Strong Sell"
    
    async def get_multiple_stocks_async(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple stocks asynchronously"""
        results = {}
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = []
            for ticker in tickers:
                task = self._fetch_stock_data_async(session, ticker)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ticker, response in zip(tickers, responses):
                if isinstance(response, Exception):
                    logger.error(f"Error fetching {ticker}: {response}")
                    results[ticker] = {}
                else:
                    results[ticker] = response
        
        return results
    
    async def _fetch_stock_data_async(self, session: aiohttp.ClientSession, ticker: str) -> Dict[str, Any]:
        """Fetch stock data asynchronously"""
        try:
            url = f"{self.base_url}/getData/"
            params = {'name': ticker.upper()}
            
            async with session.get(url, params=params, timeout=10) as response:
                data = await response.json()
                
                smart_score = data.get('portfolioHoldingData', {}).get('smartScore')
                if smart_score is None:
                    smart_score = data.get('smartScore')
                
                return {
                    'ticker': ticker.upper(),
                    'smart_score': smart_score,
                    'score_meaning': self._interpret_smart_score(smart_score),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Async error for {ticker}: {e}")
            return {}
    
    def __del__(self):
        """Close session on cleanup"""
        if hasattr(self, 'session'):
            self.session.close()