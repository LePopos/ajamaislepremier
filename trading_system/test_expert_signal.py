#!/usr/bin/env python3
"""
Test expert analyst signal with Plum integration
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config import config
from src.api.alpha_vantage_client import AlphaVantageClient
from src.services.notification_service import NotificationService
from src.models.stock_models import Stock, TradingSignal, Recommendation, SignalType

def send_expert_signal():
    """Send signal for an expert analyst pick"""
    
    print("🎯 Testing Expert Analyst Signal...")
    
    # Get data for NVDA (C.J. Muse pick)
    alpha_vantage = AlphaVantageClient(config.alpha_vantage_api_key)
    quote = alpha_vantage.get_real_time_quote("NVDA")
    
    if not quote:
        print("❌ Failed to get NVDA data")
        return False
    
    price = quote['price']
    change_percent = float(quote['change_percent'])
    volume = quote['volume']
    
    print(f"📊 NVDA (C.J. Muse Expert Pick): ${price:.2f} ({change_percent:+.2f}%) Volume: {volume:,}")
    
    # Create stock object
    stock = Stock()
    stock.ticker = "NVDA"
    stock.company_name = "NVIDIA Corporation"
    stock.sector = "Technology/Semiconductors"
    
    # Create strong signal for expert pick
    signal = TradingSignal()
    signal.signal_type = SignalType.BUY.value
    signal.confidence = 0.88  # High confidence for expert pick
    signal.reasoning = f"C.J. Muse expert pick: AI/GPU dominance continues. Current momentum: {change_percent:+.2f}% with volume {volume:,}"
    signal.price_when_generated = price
    signal.target_price = price * 1.12  # 12% target based on expert analysis
    signal.stop_loss_price = price * 0.95  # 5% stop loss
    signal.position_size_usd = min(1500, price * 2)  # ~2 shares max
    signal.generated_at = datetime.now()
    
    # Create comprehensive recommendation
    recommendation = Recommendation()
    recommendation.smart_score = 9  # Strong score for NVDA
    recommendation.score_meaning = "Strong Buy"
    recommendation.mean_price_target = price * 1.15
    recommendation.bullish_percent = 85
    recommendation.bearish_percent = 10
    recommendation.num_analysts = 28
    recommendation.news_score = 9.2
    
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
    
    print(f"📧 Sending NVDA expert signal to {config.recipient_emails[0]}...")
    
    try:
        success = notification_service.send_signal_alert(signal, stock, recommendation)
        
        if success:
            print(f"✅ EXPERT SIGNAL EMAIL SENT!")
            print(f"📊 NVDA - C.J. Muse Pick")
            print(f"💰 Price: ${price:.2f} ({change_percent:+.2f}%)")
            print(f"🎯 12-Month Target: ${price * 1.15:.2f}")
            print(f"📈 Expert Confidence: 88%")
            print(f"🔗 Includes Plum app links")
            print(f"📅 M+6 & Y+1 forecasts included")
            return True
        else:
            print("❌ Failed to send email")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    send_expert_signal()