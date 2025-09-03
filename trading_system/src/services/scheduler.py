import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List, Callable, Optional
import threading
from sqlalchemy.orm import Session

from ..services.data_collector import DataCollector
from ..services.signal_generator import SignalGenerator
from ..services.notification_service import NotificationService
from ..models.stock_models import get_session_factory, TradingSignal, Stock, Position
from ..config.config import config

logger = logging.getLogger(__name__)

class TradingScheduler:
    """Scheduler for automated data collection and signal generation"""
    
    def __init__(self, data_collector: DataCollector, signal_generator: SignalGenerator, 
                 notification_service: Optional[NotificationService] = None):
        self.data_collector = data_collector
        self.signal_generator = signal_generator
        self.notification_service = notification_service
        self.session_factory = get_session_factory(config.database_url)
        self.is_running = False
        self.scheduler_thread = None
        
        # Market hours (Eastern Time) - approximate
        self.market_open_hour = 9  # 9:30 AM ET
        self.market_close_hour = 16  # 4:00 PM ET
    
    def setup_schedule(self):
        """Setup the scheduled jobs"""
        
        # Data collection during market hours (every 15 minutes)
        schedule.every(config.collection_interval_minutes).minutes.do(
            self._safe_job_wrapper, 
            self.collect_market_data,
            "Market Data Collection"
        )
        
        # Signal generation (every 30 minutes during market hours)
        schedule.every(30).minutes.do(
            self._safe_job_wrapper,
            self.generate_signals,
            "Signal Generation"
        )
        
        # Update signal prices (every 5 minutes during market hours)
        schedule.every(5).minutes.do(
            self._safe_job_wrapper,
            self.update_signal_prices,
            "Signal Price Updates"
        )
        
        # Daily cleanup (once per day at 6 PM ET)
        schedule.every().day.at("18:00").do(
            self._safe_job_wrapper,
            self.daily_cleanup,
            "Daily Cleanup"
        )
        
        # Daily summary email (configurable hour)
        summary_time = f"{config.daily_summary_hour:02d}:00"
        schedule.every().day.at(summary_time).do(
            self._safe_job_wrapper,
            self.send_daily_summary,
            "Daily Summary Email"
        )
        
        # Weekly data cleanup (Sundays at 2 AM)
        schedule.every().sunday.at("02:00").do(
            self._safe_job_wrapper,
            self.weekly_cleanup,
            "Weekly Cleanup"
        )
        
        logger.info("Scheduled jobs configured")
    
    def start(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.setup_schedule()
        self.is_running = True
        
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Trading scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Clear all scheduled jobs
        schedule.clear()
        logger.info("Trading scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _safe_job_wrapper(self, job_func: Callable, job_name: str):
        """Wrapper to safely execute scheduled jobs"""
        try:
            logger.info(f"Starting scheduled job: {job_name}")
            start_time = datetime.now()
            
            # Only run market-related jobs during market hours
            if job_name in ["Market Data Collection", "Signal Generation", "Signal Price Updates"]:
                if not self._is_market_hours():
                    logger.info(f"Skipping {job_name} - outside market hours")
                    return
            
            job_func()
            
            duration = datetime.now() - start_time
            logger.info(f"Completed scheduled job: {job_name} (duration: {duration.total_seconds():.2f}s)")
            
        except Exception as e:
            logger.error(f"Error in scheduled job {job_name}: {e}")
    
    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (Eastern Time)"""
        import pytz
        
        # Get current time in UTC, then convert to Eastern Time
        utc_now = datetime.utcnow()
        eastern_tz = pytz.timezone('US/Eastern')
        eastern_now = utc_now.replace(tzinfo=pytz.UTC).astimezone(eastern_tz)
        
        # Skip weekends
        if eastern_now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        current_hour = eastern_now.hour
        current_minute = eastern_now.minute
        
        # US market hours: 9:30 AM - 4:00 PM ET
        market_start = 9.5  # 9:30 AM
        market_end = 16.0   # 4:00 PM
        current_time = current_hour + current_minute / 60.0
        
        return market_start <= current_time < market_end
    
    def collect_market_data(self):
        """Scheduled data collection job"""
        try:
            watchlist = config.watchlist
            logger.info(f"Collecting data for {len(watchlist)} tickers")
            
            results = self.data_collector.collect_all_data(watchlist)
            
            successful = sum(1 for success in results.values() if success)
            failed = len(results) - successful
            
            logger.info(f"Data collection completed: {successful} successful, {failed} failed")
            
            if failed > len(watchlist) * 0.5:  # More than 50% failed
                logger.warning(f"High failure rate in data collection: {failed}/{len(watchlist)}")
            
        except Exception as e:
            logger.error(f"Error in scheduled data collection: {e}")
    
    def generate_signals(self):
        """Scheduled signal generation job"""
        try:
            with self.session_factory() as db:
                # Clean up expired signals first
                expired_count = self.signal_generator.cleanup_expired_signals(db)
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired signals")
                
                # Generate new signals for watchlist
                watchlist = config.watchlist
                logger.info(f"Generating signals for {len(watchlist)} tickers")
                
                new_signals = self.signal_generator.generate_signals_for_watchlist(db, watchlist)
                
                logger.info(f"Generated {len(new_signals)} new trading signals")
                
                # Log signal summary
                if new_signals:
                    signal_summary = {}
                    for signal in new_signals:
                        signal_type = signal.signal_type
                        signal_summary[signal_type] = signal_summary.get(signal_type, 0) + 1
                    
                    summary_str = ", ".join([f"{k}: {v}" for k, v in signal_summary.items()])
                    logger.info(f"Signal breakdown: {summary_str}")
                
        except Exception as e:
            logger.error(f"Error in scheduled signal generation: {e}")
    
    def update_signal_prices(self):
        """Update prices for active signals and check stop losses"""
        try:
            with self.session_factory() as db:
                # Get all active signals
                active_signals = db.query(TradingSignal).filter(
                    TradingSignal.is_active == True
                ).all()
                
                if not active_signals:
                    return
                
                logger.info(f"Updating prices for {len(active_signals)} active signals")
                
                updated_count = 0
                for signal in active_signals:
                    if self.signal_generator.update_signal_prices(db, signal.id):
                        updated_count += 1
                
                logger.info(f"Updated {updated_count} signal prices")
                
        except Exception as e:
            logger.error(f"Error updating signal prices: {e}")
    
    def daily_cleanup(self):
        """Daily cleanup and maintenance"""
        try:
            logger.info("Starting daily cleanup")
            
            with self.session_factory() as db:
                # Clean up expired signals
                expired_count = self.signal_generator.cleanup_expired_signals(db)
                logger.info(f"Cleaned up {expired_count} expired signals")
                
                # Get active signals count
                active_signals = db.query(TradingSignal).filter(
                    TradingSignal.is_active == True
                ).count()
                
                # Get total positions
                open_positions = db.query(Position).filter(
                    Position.is_open == True
                ).count()
                
                logger.info(f"Daily summary: {active_signals} active signals, {open_positions} open positions")
            
        except Exception as e:
            logger.error(f"Error in daily cleanup: {e}")
    
    def send_daily_summary(self):
        """Send daily summary email"""
        try:
            if not self.notification_service or not config.send_daily_summary:
                return
            
            logger.info("Preparing daily summary email")
            
            with self.session_factory() as db:
                # Get active signals
                active_signals_db = db.query(TradingSignal, Stock).join(Stock).filter(
                    TradingSignal.is_active == True
                ).all()
                
                active_signals = []
                for signal, stock in active_signals_db:
                    age_hours = (datetime.utcnow() - signal.generated_at).total_seconds() / 3600
                    active_signals.append({
                        'ticker': stock.ticker,
                        'signal_type': signal.signal_type,
                        'price': signal.price_when_generated,
                        'confidence': signal.confidence,
                        'age_hours': age_hours
                    })
                
                # Get portfolio summary
                total_positions = db.query(Position).filter(Position.is_open == True).count()
                portfolio_summary = {
                    'active_signals': len(active_signals),
                    'total_value': 0.0,  # Would calculate from actual positions
                    'daily_pnl': 0.0     # Would calculate from price changes
                }
                
                # Send summary email
                success = self.notification_service.send_daily_summary(active_signals, portfolio_summary)
                
                if success:
                    logger.info("Daily summary email sent successfully")
                else:
                    logger.warning("Failed to send daily summary email")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def weekly_cleanup(self):
        """Weekly data cleanup"""
        try:
            logger.info("Starting weekly cleanup")
            
            # Clean up old data
            cleanup_results = self.data_collector.cleanup_old_data(days_to_keep=30)
            
            logger.info(f"Weekly cleanup completed: "
                       f"Deleted {cleanup_results['price_data_deleted']} price records, "
                       f"{cleanup_results['recommendations_deleted']} recommendation records")
            
        except Exception as e:
            logger.error(f"Error in weekly cleanup: {e}")
    
    def run_job_now(self, job_name: str):
        """Manually run a specific job"""
        job_mapping = {
            'collect_data': self.collect_market_data,
            'generate_signals': self.generate_signals,
            'update_prices': self.update_signal_prices,
            'daily_cleanup': self.daily_cleanup,
            'weekly_cleanup': self.weekly_cleanup,
            'send_summary': self.send_daily_summary
        }
        
        if job_name not in job_mapping:
            logger.error(f"Unknown job: {job_name}")
            return False
        
        try:
            logger.info(f"Manually running job: {job_name}")
            job_mapping[job_name]()
            return True
        except Exception as e:
            logger.error(f"Error running manual job {job_name}: {e}")
            return False
    
    def get_schedule_status(self) -> dict:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'scheduled_jobs': len(schedule.jobs),
            'next_runs': [str(job.next_run) for job in schedule.jobs[:5]],  # Next 5 jobs
            'market_hours': self._is_market_hours(),
            'current_time': datetime.now().isoformat()
        }