#!/usr/bin/env python3
"""
Generate trading signals using Alpha Vantage data only
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config import config
from src.api.alpha_vantage_client import AlphaVantageClient
from src.services.notification_service import NotificationService
from src.models.stock_models import Stock, TradingSignal, SignalType, create_database

def create_simple_signal(ticker: str, price: float, change_percent: float):
    """Create a simple trading signal based on price movement"""
    
    stock = Stock()
    stock.ticker = ticker
    stock.company_name = f"{ticker} Inc."
    
    # Simple signal logic based on daily change
    if change_percent > 2.0:
        signal_type = SignalType.BUY
        confidence = min(0.7 + (change_percent / 10), 0.95)
        reasoning = f"Strong upward momentum: +{change_percent:.2f}% today"
    elif change_percent < -2.0:
        signal_type = SignalType.SELL
        confidence = min(0.7 + (abs(change_percent) / 10), 0.95) 
        reasoning = f"Strong downward movement: {change_percent:.2f}% today"
    elif abs(change_percent) < 0.5:
        signal_type = SignalType.BUY  # Slight bias toward buying
        confidence = 0.6
        reasoning = f"Stable price action: {change_percent:+.2f}% - good entry point"
    else:
        signal_type = SignalType.HOLD
        confidence = 0.5
        reasoning = f"Moderate movement: {change_percent:+.2f}% - wait and see"
    
    signal = TradingSignal()
    signal.signal_type = signal_type.value
    signal.confidence = confidence
    signal.reasoning = reasoning
    signal.price_when_generated = price
    signal.target_price = price * 1.05 if signal_type == SignalType.BUY else price * 0.95
    signal.stop_loss_price = price * 0.95 if signal_type == SignalType.BUY else price * 1.05
    signal.position_size_usd = min(1000.0, 1000.0 * confidence)
    signal.generated_at = datetime.utcnow()
    
    return stock, signal

def test_real_signals():
    """Generate real trading signals and send test email"""
    
    print("🚀 Generating REAL trading signals with Alpha Vantage data...")
    
    # Initialize Alpha Vantage client
    alpha_vantage = AlphaVantageClient(config.alpha_vantage_api_key)
    
    # Initialize email service
    email_config = {
        'smtp_server': config.smtp_server,
        'smtp_port': config.smtp_port,
        'sender_email': config.sender_email,
        'sender_password': config.sender_password,
        'recipient_emails': config.recipient_emails,
        'webhook_url': config.webhook_url
    }
    notification_service = NotificationService(email_config)
    
    # Create database
    create_database(config.database_url)
    
    # Test with top stocks
    watchlist = ["AAPL", "MSFT", "TSLA"]
    
    for ticker in watchlist:
        print(f"\n📊 Analyzing {ticker}...")
        
        # Get real price data
        quote = alpha_vantage.get_real_time_quote(ticker)
        
        if not quote or 'price' not in quote:
            print(f"❌ No data for {ticker}")
            continue
            
        price = quote['price']
        change_percent = float(quote['change_percent'])
        
        print(f"💰 {ticker}: ${price:.2f} ({change_percent:+.2f}%)")
        
        # Generate signal
        stock, signal = create_simple_signal(ticker, price, change_percent)
        
        print(f"📈 Signal: {signal.signal_type} (confidence: {signal.confidence:.1%})")
        print(f"🧠 Reasoning: {signal.reasoning}")
        
        # Send email alert
        print(f"📧 Sending email alert to {config.recipient_emails[0]}...")
        
        try:
            email_sent = notification_service.send_signal_alert(signal, stock)
            print(f"✅ Email sent: {email_sent}")
        except Exception as e:
            print(f"❌ Email failed: {e}")
            print("Note: L'email nécessite des vrais identifiants SMTP")
        
        # Wait between requests to respect rate limits
        import time
        time.sleep(15)  # Alpha Vantage rate limiting

if __name__ == "__main__":
    test_real_signals()