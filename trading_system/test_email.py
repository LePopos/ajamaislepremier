#!/usr/bin/env python3
"""
Test script for email notifications
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.config import config
from services.notification_service import NotificationService
from models.stock_models import TradingSignal, Stock, Recommendation, SignalType

def test_email_configuration():
    """Test email configuration and send test email"""
    
    if not config.email_enabled:
        print("❌ Email is not enabled in configuration")
        print("Set EMAIL_ENABLED=true in your .env file")
        return False
    
    if not config.sender_email:
        print("❌ Sender email not configured")
        print("Set SENDER_EMAIL in your .env file")
        return False
    
    if not config.sender_password:
        print("❌ Sender password not configured")  
        print("Set SENDER_PASSWORD in your .env file")
        print("For Gmail, use an app-specific password: https://support.google.com/accounts/answer/185833")
        return False
    
    if not config.recipient_emails:
        print("❌ No recipient emails configured")
        print("Set RECIPIENT_EMAILS in your .env file")
        return False
    
    print("✅ Email configuration looks good")
    return True

def create_test_signal():
    """Create a test trading signal for email testing"""
    
    # Create test stock
    stock = Stock()
    stock.id = 1
    stock.ticker = "AAPL"
    stock.company_name = "Apple Inc."
    stock.sector = "Technology"
    
    # Create test signal
    signal = TradingSignal()
    signal.id = 1
    signal.stock_id = 1
    signal.signal_type = SignalType.BUY.value
    signal.confidence = 0.85
    signal.reasoning = "Strong Smart Score (9/10) + bullish sentiment (75%) + upside potential (12%)"
    signal.price_when_generated = 182.50
    signal.target_price = 195.00
    signal.stop_loss_price = 173.38
    signal.position_size_usd = 1000.00
    signal.generated_at = datetime.utcnow()
    
    # Create test recommendation
    recommendation = Recommendation()
    recommendation.id = 1
    recommendation.stock_id = 1
    recommendation.smart_score = 9
    recommendation.score_meaning = "Strong Buy"
    recommendation.mean_price_target = 195.00
    recommendation.num_analysts = 12
    recommendation.bullish_percent = 75.0
    recommendation.bearish_percent = 15.0
    recommendation.news_score = 8.2
    
    return signal, stock, recommendation

def test_send_alert():
    """Test sending a trading signal alert"""
    
    print("\n🧪 Testing signal alert email...")
    
    # Initialize notification service
    email_config = {
        'smtp_server': config.smtp_server,
        'smtp_port': config.smtp_port,
        'sender_email': config.sender_email,
        'sender_password': config.sender_password,
        'recipient_emails': config.recipient_emails,
        'webhook_url': config.webhook_url
    }
    
    notification_service = NotificationService(email_config)
    
    # Create test data
    signal, stock, recommendation = create_test_signal()
    
    # Send test alert
    try:
        success = notification_service.send_signal_alert(signal, stock, recommendation)
        
        if success:
            print("✅ Signal alert email sent successfully!")
            print(f"📧 Sent to: {', '.join(config.recipient_emails)}")
        else:
            print("❌ Failed to send signal alert email")
            
        return success
        
    except Exception as e:
        print(f"❌ Error sending signal alert: {e}")
        return False

def test_send_summary():
    """Test sending daily summary email"""
    
    print("\n🧪 Testing daily summary email...")
    
    # Initialize notification service
    email_config = {
        'smtp_server': config.smtp_server,
        'smtp_port': config.smtp_port,
        'sender_email': config.sender_email,
        'sender_password': config.sender_password,
        'recipient_emails': config.recipient_emails,
        'webhook_url': config.webhook_url
    }
    
    notification_service = NotificationService(email_config)
    
    # Create test summary data
    active_signals = [
        {
            'ticker': 'AAPL',
            'signal_type': 'BUY',
            'price': 182.50,
            'confidence': 0.85,
            'age_hours': 2.5
        },
        {
            'ticker': 'TSLA',
            'signal_type': 'SELL',
            'price': 248.42,
            'confidence': 0.72,
            'age_hours': 1.2
        }
    ]
    
    portfolio_summary = {
        'active_signals': 2,
        'total_value': 2500.00,
        'daily_pnl': 125.50
    }
    
    # Send test summary
    try:
        success = notification_service.send_daily_summary(active_signals, portfolio_summary)
        
        if success:
            print("✅ Daily summary email sent successfully!")
            print(f"📧 Sent to: {', '.join(config.recipient_emails)}")
        else:
            print("❌ Failed to send daily summary email")
            
        return success
        
    except Exception as e:
        print(f"❌ Error sending daily summary: {e}")
        return False

def main():
    """Main test function"""
    
    print("📧 Email Notification Test")
    print("=" * 40)
    
    # Test configuration
    if not test_email_configuration():
        print("\n💡 To fix configuration:")
        print("1. Copy .env.example to .env")  
        print("2. Set your email credentials in .env")
        print("3. For Gmail, use app-specific password")
        sys.exit(1)
    
    # Test signal alert
    signal_success = test_send_alert()
    
    # Test daily summary  
    summary_success = test_send_summary()
    
    # Results
    print("\n📊 Test Results:")
    print(f"Signal Alert: {'✅ PASS' if signal_success else '❌ FAIL'}")
    print(f"Daily Summary: {'✅ PASS' if summary_success else '❌ FAIL'}")
    
    if signal_success and summary_success:
        print("\n🎉 All email tests passed!")
        print("Your email notifications are working correctly.")
    else:
        print("\n❌ Some tests failed. Check your email configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()