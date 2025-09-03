import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

from ..models.stock_models import (
    Stock, PriceData, Recommendation, get_session_factory
)
from ..api.tipranks_client import TipRanksClient  
from ..api.yfinance_client import YFinanceClient
from ..config.config import config

logger = logging.getLogger(__name__)

class DataCollector:
    """Collect and store stock data from various sources"""
    
    def __init__(self, tipranks_client: TipRanksClient, yfinance_client: YFinanceClient):
        self.tipranks = tipranks_client
        self.yfinance = yfinance_client
        self.session_factory = get_session_factory(config.database_url)
    
    def collect_all_data(self, tickers: List[str]) -> Dict[str, bool]:
        """Collect comprehensive data for all tickers"""
        results = {}
        
        with self.session_factory() as db:
            for ticker in tickers:
                try:
                    logger.info(f"Collecting data for {ticker}")
                    
                    # Collect price data
                    price_success = self._collect_price_data(db, ticker)
                    
                    # Collect TipRanks data
                    tipranks_success = self._collect_tipranks_data(db, ticker)
                    
                    results[ticker] = price_success and tipranks_success
                    
                    if results[ticker]:
                        logger.info(f"Successfully collected data for {ticker}")
                    else:
                        logger.warning(f"Partial data collection failure for {ticker}")
                
                except Exception as e:
                    logger.error(f"Error collecting data for {ticker}: {e}")
                    results[ticker] = False
                    continue
            
            db.commit()
        
        return results
    
    def _collect_price_data(self, db: Session, ticker: str) -> bool:
        """Collect and store current price data"""
        try:
            # Get or create stock record
            stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
            if not stock:
                # Get company overview to populate stock info
                overview = self.yfinance.get_company_overview(ticker)
                
                stock = Stock(
                    ticker=ticker.upper(),
                    company_name=overview.get('name', '') if overview else '',
                    sector=overview.get('sector', '') if overview else '',
                    industry=overview.get('industry', '') if overview else '',
                    market_cap=overview.get('market_cap', '') if overview else ''
                )
                db.add(stock)
                db.flush()  # Get the ID without committing
            
            # Get current quote
            quote_data = self.yfinance.get_real_time_quote(ticker)
            if not quote_data or 'price' not in quote_data:
                logger.warning(f"No price data available for {ticker}")
                return False
            
            # Check if we already have recent data (within last 15 minutes)
            fifteen_min_ago = datetime.utcnow() - timedelta(minutes=15)
            recent_data = db.query(PriceData).filter(
                PriceData.stock_id == stock.id,
                PriceData.timestamp > fifteen_min_ago
            ).first()
            
            if recent_data:
                # Update existing record
                recent_data.price = quote_data['price']
                recent_data.open_price = quote_data.get('open', recent_data.open_price)
                recent_data.high_price = quote_data.get('high', recent_data.high_price)
                recent_data.low_price = quote_data.get('low', recent_data.low_price)
                recent_data.volume = quote_data.get('volume', recent_data.volume)
                recent_data.change = quote_data.get('change', recent_data.change)
                recent_data.change_percent = self._parse_change_percent(quote_data.get('change_percent', '0'))
                recent_data.timestamp = datetime.utcnow()
            else:
                # Create new record
                price_data = PriceData(
                    stock_id=stock.id,
                    price=quote_data['price'],
                    open_price=quote_data.get('open'),
                    high_price=quote_data.get('high'),
                    low_price=quote_data.get('low'),
                    volume=quote_data.get('volume'),
                    change=quote_data.get('change'),
                    change_percent=self._parse_change_percent(quote_data.get('change_percent', '0')),
                    timestamp=datetime.utcnow()
                )
                db.add(price_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error collecting price data for {ticker}: {e}")
            return False
    
    def _collect_tipranks_data(self, db: Session, ticker: str) -> bool:
        """Collect and store TipRanks recommendation data"""
        try:
            # Get or create stock record
            stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
            if not stock:
                stock = Stock(ticker=ticker.upper())
                db.add(stock)
                db.flush()
            
            # Get comprehensive TipRanks data
            tipranks_data = self.tipranks.get_comprehensive_data(ticker)
            
            if not tipranks_data:
                logger.warning(f"No TipRanks data available for {ticker}")
                return False
            
            # Extract data components
            price_targets = tipranks_data.get('price_targets', {})
            sentiment = tipranks_data.get('sentiment', {})
            smart_score_data = tipranks_data.get('smart_score', {})
            
            # Check if we have recent recommendation data (within last hour)  
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_recommendation = db.query(Recommendation).filter(
                Recommendation.stock_id == stock.id,
                Recommendation.timestamp > one_hour_ago
            ).first()
            
            if recent_recommendation:
                # Update existing recommendation
                self._update_recommendation(recent_recommendation, price_targets, sentiment, smart_score_data)
            else:
                # Create new recommendation record
                recommendation = Recommendation(
                    stock_id=stock.id,
                    source="TipRanks",
                    smart_score=smart_score_data.get('smart_score'),
                    score_meaning=smart_score_data.get('score_meaning', ''),
                    mean_price_target=price_targets.get('mean_target'),
                    median_price_target=price_targets.get('median_target'),
                    high_price_target=price_targets.get('high_target'),
                    low_price_target=price_targets.get('low_target'),
                    num_analysts=price_targets.get('num_analysts', 0),
                    bullish_percent=sentiment.get('bullish_percent'),
                    bearish_percent=sentiment.get('bearish_percent'),
                    news_score=sentiment.get('news_score'),
                    timestamp=datetime.utcnow()
                )
                db.add(recommendation)
            
            return True
            
        except Exception as e:
            logger.error(f"Error collecting TipRanks data for {ticker}: {e}")
            return False
    
    def _update_recommendation(self, recommendation: Recommendation, price_targets: Dict, 
                             sentiment: Dict, smart_score_data: Dict):
        """Update existing recommendation with new data"""
        recommendation.smart_score = smart_score_data.get('smart_score') or recommendation.smart_score
        recommendation.score_meaning = smart_score_data.get('score_meaning', '') or recommendation.score_meaning
        recommendation.mean_price_target = price_targets.get('mean_target') or recommendation.mean_price_target
        recommendation.median_price_target = price_targets.get('median_target') or recommendation.median_price_target
        recommendation.high_price_target = price_targets.get('high_target') or recommendation.high_price_target
        recommendation.low_price_target = price_targets.get('low_target') or recommendation.low_price_target
        recommendation.num_analysts = price_targets.get('num_analysts', 0) or recommendation.num_analysts
        recommendation.bullish_percent = sentiment.get('bullish_percent') or recommendation.bullish_percent
        recommendation.bearish_percent = sentiment.get('bearish_percent') or recommendation.bearish_percent
        recommendation.news_score = sentiment.get('news_score') or recommendation.news_score
        recommendation.timestamp = datetime.utcnow()
    
    def _parse_change_percent(self, change_percent_str: str) -> float:
        """Parse change percentage string to float"""
        try:
            if isinstance(change_percent_str, str):
                # Remove % sign and convert to float
                return float(change_percent_str.replace('%', '').replace('+', ''))
            elif isinstance(change_percent_str, (int, float)):
                return float(change_percent_str)
            return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    async def collect_data_async(self, tickers: List[str]) -> Dict[str, bool]:
        """Collect data for multiple tickers asynchronously"""
        results = {}
        
        # Split tickers into smaller batches to avoid overwhelming APIs
        batch_size = 5
        ticker_batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
        
        for batch in ticker_batches:
            batch_results = await self._process_batch_async(batch)
            results.update(batch_results)
            
            # Wait between batches to respect rate limits
            if len(ticker_batches) > 1:
                await asyncio.sleep(60)  # 1 minute between batches
        
        return results
    
    async def _process_batch_async(self, tickers: List[str]) -> Dict[str, bool]:
        """Process a batch of tickers asynchronously"""
        tasks = []
        
        for ticker in tickers:
            task = asyncio.create_task(self._collect_single_ticker_async(ticker))
            tasks.append((ticker, task))
        
        results = {}
        for ticker, task in tasks:
            try:
                success = await task
                results[ticker] = success
            except Exception as e:
                logger.error(f"Async error collecting data for {ticker}: {e}")
                results[ticker] = False
        
        return results
    
    async def _collect_single_ticker_async(self, ticker: str) -> bool:
        """Collect data for a single ticker asynchronously"""
        try:
            with self.session_factory() as db:
                # Collect price data
                price_success = self._collect_price_data(db, ticker)
                
                # Add delay between API calls
                await asyncio.sleep(2)
                
                # Collect TipRanks data
                tipranks_success = self._collect_tipranks_data(db, ticker)
                
                db.commit()
                return price_success and tipranks_success
                
        except Exception as e:
            logger.error(f"Error in async data collection for {ticker}: {e}")
            return False
    
    def get_data_freshness(self, ticker: str) -> Dict[str, Optional[datetime]]:
        """Check when data was last updated for a ticker"""
        with self.session_factory() as db:
            stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
            
            if not stock:
                return {'price_data': None, 'recommendations': None}
            
            latest_price = db.query(PriceData).filter(
                PriceData.stock_id == stock.id
            ).order_by(PriceData.timestamp.desc()).first()
            
            latest_recommendation = db.query(Recommendation).filter(
                Recommendation.stock_id == stock.id
            ).order_by(Recommendation.timestamp.desc()).first()
            
            return {
                'price_data': latest_price.timestamp if latest_price else None,
                'recommendations': latest_recommendation.timestamp if latest_recommendation else None
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Remove old data to keep database size manageable"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.session_factory() as db:
            try:
                # Delete old price data (keep only recent)
                old_price_count = db.query(PriceData).filter(
                    PriceData.timestamp < cutoff_date
                ).count()
                
                db.query(PriceData).filter(
                    PriceData.timestamp < cutoff_date
                ).delete()
                
                # Keep more recommendation data (90 days)
                rec_cutoff = datetime.utcnow() - timedelta(days=90)
                old_rec_count = db.query(Recommendation).filter(
                    Recommendation.timestamp < rec_cutoff
                ).count()
                
                db.query(Recommendation).filter(
                    Recommendation.timestamp < rec_cutoff
                ).delete()
                
                db.commit()
                
                logger.info(f"Cleaned up {old_price_count} old price records and {old_rec_count} old recommendations")
                
                return {
                    'price_data_deleted': old_price_count,
                    'recommendations_deleted': old_rec_count
                }
                
            except Exception as e:
                logger.error(f"Error during data cleanup: {e}")
                db.rollback()
                return {'price_data_deleted': 0, 'recommendations_deleted': 0}