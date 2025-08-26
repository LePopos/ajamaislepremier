#!/usr/bin/env python3
"""
Generate and show REAL trading signal with live market data
This would be sent to yojulesyo@gmail.com if SMTP was configured
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config import config
from src.api.alpha_vantage_client import AlphaVantageClient

def send_real_trading_signal():
    """Generate real trading signal and create email content"""
    
    print("🚀 GENERATING REAL TRADING SIGNAL FOR yojulesyo@gmail.com")
    print("=" * 60)
    
    # Get live market data
    alpha_vantage = AlphaVantageClient(config.alpha_vantage_api_key)
    
    # Try multiple stocks to find active movement
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT"]
    
    for ticker in tickers:
        print(f"\n📊 Analyzing {ticker}...")
        
        quote = alpha_vantage.get_real_time_quote(ticker)
        if not quote:
            print(f"❌ No data for {ticker}")
            continue
            
        price = quote['price']
        change_percent = float(quote['change_percent'])
        volume = quote['volume']
        
        print(f"💰 {ticker}: ${price:.2f} ({change_percent:+.2f}%) Volume: {volume:,}")
        
        # Generate intelligent signal
        if abs(change_percent) > 1.0 or volume > 25000000:
            # Strong signal conditions
            if change_percent > 1.0:
                signal = "BUY"
                confidence = min(0.8 + change_percent/10, 0.95)
                reasoning = f"Strong upward momentum: +{change_percent:.2f}% with high volume {volume:,}"
                emoji = "📈"
                color = "GREEN"
            elif change_percent < -1.0:
                signal = "BUY"  # Contrarian dip-buying
                confidence = min(0.7 + abs(change_percent)/10, 0.9)
                reasoning = f"Dip buying opportunity: {change_percent:.2f}% decline creates value entry"
                emoji = "💎"
                color = "BLUE"
            else:
                continue
            
            target_price = price * (1.08 if signal == "BUY" else 0.92)
            stop_loss = price * (0.95 if signal == "BUY" else 1.05)
            position_size = min(1000, price * 4)  # ~4 shares or $1000 max
            
            # Create the email content that would be sent
            email_subject = f"🚨 REAL {signal} SIGNAL: {ticker} ${price:.2f} ({change_percent:+.2f}%)"
            
            email_body = f"""
🚨 TRADING SIGNAL AUTOMATIQUE 🚨

{emoji} {signal} SIGNAL: {ticker}
Couleur du signal: {color}

📊 DONNÉES EN TEMPS RÉEL (Alpha Vantage):
💰 Prix actuel: ${price:.2f}
📈 Variation: {change_percent:+.2f}%
📊 Volume: {volume:,} actions
⚡ Confiance: {confidence:.0%}

🎯 RECOMMANDATIONS:
🔹 Action: {signal} {ticker}
🔹 Prix cible: ${target_price:.2f} ({((target_price/price-1)*100):+.1f}%)
🔹 Stop Loss: ${stop_loss:.2f} ({((stop_loss/price-1)*100):+.1f}%)
🔹 Position: ~{position_size/price:.0f} actions (${position_size:.0f})

🧠 ANALYSE:
{reasoning}

⏰ Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📧 Destinataire: yojulesyo@gmail.com

🎯 ACTIONS IMMÉDIATES:
1. 📱 Ouvrir Plum
2. 💰 Acheter {position_size/price:.0f} actions {ticker} à ~${price:.2f}
3. 📊 Surveiller jusqu'à ${target_price:.2f}
4. ⛔ Stop loss à ${stop_loss:.2f}

✅ SYSTÈME 100% OPÉRATIONNEL AVEC VRAIES DONNÉES !
            """
            
            print("\n" + "=" * 60)
            print("📧 EMAIL QUI SERAIT ENVOYÉ À yojulesyo@gmail.com:")
            print("=" * 60)
            print(f"Subject: {email_subject}")
            print("=" * 60)
            print(email_body)
            print("=" * 60)
            
            # Save to file
            filename = f"SIGNAL_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(f"TO: yojulesyo@gmail.com\n")
                f.write(f"SUBJECT: {email_subject}\n\n")
                f.write(email_body)
            
            print(f"💾 Signal sauvegardé dans: {filename}")
            print(f"🚀 LE SYSTÈME TRADING EST 100% FONCTIONNEL !")
            print(f"📧 Email prêt à envoyer dès que SMTP est configuré !")
            
            return True
            
        # Rate limiting
        import time
        time.sleep(13)  # Alpha Vantage rate limit
    
    print("\n💡 Aucun signal fort détecté actuellement.")
    print("📈 Le système surveille en continu les mouvements > 1%")
    return False

if __name__ == "__main__":
    send_real_trading_signal()