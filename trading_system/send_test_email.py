#!/usr/bin/env python3
"""
Send test email to yojulesyo@gmail.com to demonstrate the trading system
"""
import os
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_demo_email():
    """Send a demo email showing what trading alerts look like"""
    
    # Email configuration
    smtp_server = "smtp.gmail.com"
    port = 587
    
    # Using a temporary demo setup
    sender_email = "claude.demo.system@gmail.com"
    recipient_email = "yojulesyo@gmail.com"
    
    # Create the email content
    subject = "🚨 DEMO: BUY Signal - AAPL - TipRanks Trading System"
    
    # HTML version
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
            <h1>🚨 BUY SIGNAL</h1>
            <h2>AAPL</h2>
            <p>Apple Inc.</p>
            <p><strong>⚠️ DEMO EMAIL - Trading System Preview</strong></p>
        </div>
        
        <div style="padding: 20px;">
            <h3>📈 Signal Details</h3>
            <ul>
                <li><strong>Action:</strong> BUY</li>
                <li><strong>Current Price:</strong> $182.50</li>
                <li><strong>Confidence:</strong> 85.0%</li>
                <li><strong>Position Size:</strong> $1000.00</li>
                <li><strong>Target Price:</strong> $195.00</li>
                <li><strong>Stop Loss:</strong> $173.38</li>
            </ul>
            
            <p><strong>Potential Return:</strong> +6.8%</p>
            
            <h3>🧠 Reasoning</h3>
            <p>Strong Smart Score (9/10) + bullish sentiment (75%) + upside potential (12%) + positive analyst targets</p>
            
            <h3>📊 TipRanks Analysis</h3>
            <ul>
                <li><strong>Smart Score:</strong> 9/10</li>
                <li><strong>Price Target:</strong> $195.00</li>
                <li><strong>Analysts:</strong> 12</li>
                <li><strong>Sentiment:</strong> 75% Bullish, 15% Bearish</li>
            </ul>
            
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4>🎯 Que faire maintenant ?</h4>
                <p><strong>1. Option manuelle :</strong> Connecte-toi à Plum et achète ~5 actions AAPL</p>
                <p><strong>2. Option automatique :</strong> Configure Alpaca pour l'exécution automatique</p>
                <p><strong>3. Option monitoring :</strong> Reçois les alertes et décide au cas par cas</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4>⚠️ Important Disclaimer</h4>
                <p><small>
                    Ceci est un signal automatisé de DÉMONSTRATION basé sur l'analyse TipRanks. 
                    Ce n'est pas un conseil financier. Toujours faire ses propres recherches avant d'investir.
                    Les performances passées ne garantissent pas les résultats futurs.
                </small></p>
            </div>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4>🚀 Prochaines étapes</h4>
                <p>Si ce système t'intéresse :</p>
                <ul>
                    <li>✅ Obtiens une clé API Alpha Vantage (gratuite)</li>
                    <li>✅ Configure tes alertes email</li>
                    <li>✅ Optionnel: Connecte un broker pour l'automatisation</li>
                </ul>
            </div>
            
            <p style="text-align: center; margin-top: 20px;">
                <small>Système généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (DEMO)</small>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text = f"""
🚨 BUY SIGNAL: AAPL (DEMO)
Apple Inc.

📈 Signal Details:
- Action: BUY
- Current Price: $182.50
- Confidence: 85.0%
- Position Size: $1000.00
- Target Price: $195.00
- Stop Loss: $173.38

Potential Return: +6.8%

🧠 Reasoning:
Strong Smart Score (9/10) + bullish sentiment (75%) + upside potential (12%)

📊 TipRanks Analysis:
- Smart Score: 9/10
- Price Target: $195.00
- Analysts: 12
- Sentiment: 75% Bullish, 15% Bearish

🎯 Que faire maintenant ?
1. Option manuelle : Connecte-toi à Plum et achète ~5 actions AAPL
2. Option automatique : Configure Alpaca pour l'exécution automatique
3. Option monitoring : Reçois les alertes et décide au cas par cas

⚠️ DISCLAIMER: Ceci est un signal de DÉMONSTRATION à des fins éducatives uniquement.

🚀 Si ce système t'intéresse, on peut configurer :
- Clé API Alpha Vantage (gratuite)
- Alertes email personnalisées
- Intégration broker optionnelle

Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (DEMO)
    """
    
    print("📧 Preparing demo email...")
    print(f"To: {recipient_email}")
    print(f"Subject: {subject}")
    print("\n" + "="*60)
    print("EMAIL CONTENT PREVIEW:")
    print("="*60)
    print(text)
    print("="*60)
    print("\n✅ Demo email content prepared!")
    print("\n💡 Cette email montre à quoi ressemblerait une vraie alerte de trading.")
    print("💡 Pour envoyer de vrais emails, tu aurais besoin de configurer:")
    print("   - Un compte email SMTP (Gmail + mot de passe d'application)")
    print("   - Tes adresses de destinataires")
    print("   - Une clé API Alpha Vantage pour les données réelles")
    
    return True

if __name__ == "__main__":
    send_demo_email()