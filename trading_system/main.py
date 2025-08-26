#!/usr/bin/env python3
"""
TipRanks Trading System - Main Application Entry Point

This system automatically tracks US stock recommendations from TipRanks and generates
trading signals based on Smart Score, analyst price targets, and sentiment analysis.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))

from src.config.config import config
from src.api.tipranks_client import TipRanksClient
from src.api.alpha_vantage_client import AlphaVantageClient
from src.services.data_collector import DataCollector
from src.services.signal_generator import SignalGenerator
from src.services.scheduler import TradingScheduler
from src.services.notification_service import NotificationService
from src.models.stock_models import create_database, get_session_factory

def setup_logging():
    """Setup logging configuration"""
    
    # Ensure logs directory exists
    log_dir = os.path.dirname(config.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    return logger

def validate_configuration() -> bool:
    """Validate required configuration"""
    
    if not config.alpha_vantage_api_key:
        print("ERROR: ALPHA_VANTAGE_API_KEY is required but not set")
        print("Get your free API key from: https://www.alphavantage.co/support/#api-key")
        print("Set it in your .env file or environment variables")
        return False
    
    if not config.watchlist:
        print("WARNING: No watchlist configured, using default tickers")
    
    if config.max_position_size <= 0:
        print("ERROR: max_position_size must be greater than 0")
        return False
    
    return True

def initialize_clients(logger) -> tuple[TipRanksClient, AlphaVantageClient, Optional[NotificationService]]:
    """Initialize API clients and services"""
    
    logger.info("Initializing API clients...")
    
    # Initialize TipRanks client
    tipranks_client = TipRanksClient(proxy_url=config.tipranks_proxy_url)
    
    # Initialize Alpha Vantage client
    alpha_vantage_client = AlphaVantageClient(api_key=config.alpha_vantage_api_key)
    
    # Initialize notification service if email is enabled
    notification_service = None
    if config.email_enabled and config.sender_email:
        email_config = {
            'smtp_server': config.smtp_server,
            'smtp_port': config.smtp_port,
            'sender_email': config.sender_email,
            'sender_password': config.sender_password,
            'recipient_emails': config.recipient_emails,
            'webhook_url': config.webhook_url
        }
        notification_service = NotificationService(email_config)
        logger.info("Email notifications enabled")
    else:
        logger.info("Email notifications disabled")
    
    logger.info("API clients initialized successfully")
    return tipranks_client, alpha_vantage_client, notification_service

def initialize_database(logger) -> bool:
    """Initialize database"""
    
    try:
        logger.info(f"Initializing database: {config.database_url}")
        create_database(config.database_url)
        
        # Test database connection
        from sqlalchemy import text
        session_factory = get_session_factory(config.database_url)
        with session_factory() as db:
            # Simple query to test connection
            db.execute(text("SELECT 1"))
            
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def run_data_collection(logger, data_collector: DataCollector):
    """Run one-time data collection"""
    
    logger.info(f"Starting data collection for {len(config.watchlist)} tickers")
    print(f"Collecting data for: {', '.join(config.watchlist)}")
    
    results = data_collector.collect_all_data(config.watchlist)
    
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful
    
    print(f"\nData collection completed:")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {failed}")
    
    if failed > 0:
        print("\nFailed tickers:")
        for ticker, success in results.items():
            if not success:
                print(f"  - {ticker}")

def run_signal_generation(logger, signal_generator: SignalGenerator):
    """Run one-time signal generation"""
    
    logger.info("Starting signal generation")
    print("Generating trading signals...")
    
    session_factory = get_session_factory(config.database_url)
    with session_factory() as db:
        signals = signal_generator.generate_signals_for_watchlist(db, config.watchlist)
    
    print(f"\nGenerated {len(signals)} trading signals:")
    
    if signals:
        signal_summary = {}
        for signal in signals:
            signal_type = signal.signal_type
            if signal_type not in signal_summary:
                signal_summary[signal_type] = []
            signal_summary[signal_type].append(signal)
        
        for signal_type, signal_list in signal_summary.items():
            print(f"\n{signal_type} signals ({len(signal_list)}):")
            for signal in signal_list:
                # Get stock ticker
                session_factory = get_session_factory(config.database_url)
                with session_factory() as db:
                    stock = db.get(signal.stock_id)
                    ticker = stock.ticker if stock else "Unknown"
                
                print(f"  - {ticker}: ${signal.price_when_generated:.2f} "
                      f"(confidence: {signal.confidence:.2f})")
                if signal.target_price:
                    print(f"    Target: ${signal.target_price:.2f}")
                if signal.stop_loss_price:
                    print(f"    Stop Loss: ${signal.stop_loss_price:.2f}")
    else:
        print("No signals generated. This could mean:")
        print("  - No recent data available")
        print("  - All stocks are in HOLD status")
        print("  - Signal confidence is below threshold")

def run_scheduler(logger, scheduler: TradingScheduler):
    """Run the automated scheduler"""
    
    logger.info("Starting trading scheduler")
    print("Starting automated trading system...")
    print(f"Market hours: 9:30 AM - 4:00 PM ET")
    print(f"Data collection interval: {config.collection_interval_minutes} minutes")
    print(f"Watchlist: {', '.join(config.watchlist)}")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        scheduler.start()
        
        # Keep the main thread alive
        while scheduler.is_running:
            status = scheduler.get_schedule_status()
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Scheduler running | Market hours: {status['market_hours']} | "
                  f"Jobs: {status['scheduled_jobs']}", end="", flush=True)
            
            import time
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nShutting down scheduler...")
        scheduler.stop()
        print("Scheduler stopped successfully")

def main():
    """Main application entry point"""
    
    parser = argparse.ArgumentParser(description="TipRanks Trading System")
    parser.add_argument('command', choices=['collect', 'signals', 'run', 'status', 'execute', 'test-email'], 
                       help='Command to execute')
    parser.add_argument('--config-check', action='store_true', 
                       help='Validate configuration and exit')
    parser.add_argument('--broker', choices=['alpaca', 'mock'], default='mock',
                       help='Broker to use for order execution')
    parser.add_argument('--signal-id', type=int, help='Signal ID to execute (for execute command)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run in dry-run mode (no real trades)')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("=== TipRanks Trading System Started ===")
    
    # Validate configuration
    if not validate_configuration():
        sys.exit(1)
    
    if args.config_check:
        print("✓ Configuration is valid")
        sys.exit(0)
    
    # Initialize database
    if not initialize_database(logger):
        sys.exit(1)
    
    # Initialize API clients
    try:
        tipranks_client, alpha_vantage_client, notification_service = initialize_clients(logger)
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        sys.exit(1)
    
    # Initialize services
    data_collector = DataCollector(tipranks_client, alpha_vantage_client)
    signal_generator = SignalGenerator(tipranks_client, alpha_vantage_client, config.__dict__, notification_service)
    scheduler = TradingScheduler(data_collector, signal_generator, notification_service)
    
    # Execute command
    try:
        if args.command == 'collect':
            run_data_collection(logger, data_collector)
            
        elif args.command == 'signals':
            run_signal_generation(logger, signal_generator)
            
        elif args.command == 'run':
            run_scheduler(logger, scheduler)
            
        elif args.command == 'execute':
            # Execute specific signal or auto-execute all
            from src.brokers.alpaca_broker import AlpacaBroker
            from src.services.order_executor import OrderExecutor
            
            # Initialize broker
            if args.broker == 'alpaca':
                if not config.alpaca_api_key or not config.alpaca_secret_key:
                    print("❌ Alpaca credentials not configured")
                    sys.exit(1)
                
                broker_config = {
                    'api_key': config.alpaca_api_key,
                    'secret_key': config.alpaca_secret_key,
                    'paper_trading': config.paper_trading
                }
                broker = AlpacaBroker(broker_config)
            else:
                from src.brokers.mock_broker import MockBroker
                broker = MockBroker({})
            
            if not broker.connect():
                print("❌ Failed to connect to broker")
                sys.exit(1)
            
            # Initialize order executor
            executor = OrderExecutor(broker, notification_service)
            
            if args.signal_id:
                # Execute specific signal
                success = executor.execute_signal(args.signal_id)
                print(f"Signal {args.signal_id}: {'✓ Executed' if success else '✗ Failed'}")
            else:
                # Auto-execute all qualifying signals
                results = executor.auto_execute_signals()
                print(f"Auto-execution results:")
                print(f"  Executed: {results['executed']}")
                print(f"  Failed: {results['failed']}")
                print(f"  Skipped: {results['skipped']}")
        
        elif args.command == 'test-email':
            # Test email functionality
            if not notification_service:
                print("❌ Email notifications not configured")
                print("Set EMAIL_ENABLED=true and configure SMTP settings in .env")
                sys.exit(1)
            
            print("📧 Sending test email...")
            from src.models.stock_models import Stock, TradingSignal, Recommendation, SignalType
            from datetime import datetime
            
            # Create test data
            stock = Stock()
            stock.ticker = "AAPL"
            stock.company_name = "Apple Inc."
            
            signal = TradingSignal()
            signal.signal_type = SignalType.BUY.value
            signal.confidence = 0.85
            signal.reasoning = "DEMO: Strong Smart Score + bullish sentiment"
            signal.price_when_generated = 182.50
            signal.target_price = 195.00
            signal.stop_loss_price = 173.38
            signal.generated_at = datetime.utcnow()
            
            recommendation = Recommendation()
            recommendation.smart_score = 9
            recommendation.mean_price_target = 195.00
            recommendation.bullish_percent = 75.0
            recommendation.bearish_percent = 15.0
            
            success = notification_service.send_signal_alert(signal, stock, recommendation)
            print(f"Test email: {'✓ Sent successfully' if success else '✗ Failed'}")
            
        elif args.command == 'status':
            print("System Status:")
            print(f"  Database: {config.database_url}")
            print(f"  Watchlist: {len(config.watchlist)} tickers")
            print(f"  Alpha Vantage: {'✓' if config.alpha_vantage_api_key else '✗'}")
            print(f"  TipRanks Proxy: {'✓' if config.tipranks_proxy_url else 'Default'}")
            print(f"  Email Alerts: {'✓' if config.email_enabled and config.sender_email else '✗'}")
            print(f"  Recipients: {len(config.recipient_emails)} addresses")
            print(f"  Alpaca Broker: {'✓' if config.alpaca_api_key and config.alpaca_secret_key else '✗'}")
            print(f"  Trading Mode: {'Paper' if config.paper_trading else 'Live'} ({'Dry Run' if config.dry_run else 'Real Trades'})")
            
            # Check data freshness
            sample_ticker = config.watchlist[0] if config.watchlist else "AAPL"
            freshness = data_collector.get_data_freshness(sample_ticker)
            print(f"\nData freshness for {sample_ticker}:")
            print(f"  Price data: {freshness['price_data'] or 'Never'}")
            print(f"  Recommendations: {freshness['recommendations'] or 'Never'}")
            
    except Exception as e:
        logger.error(f"Error executing command '{args.command}': {e}")
        sys.exit(1)
    
    logger.info("=== TipRanks Trading System Finished ===")

if __name__ == "__main__":
    main()