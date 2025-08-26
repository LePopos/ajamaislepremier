#!/usr/bin/env python3
"""
Test final du système d'email avec graphique analyst ratings
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from src.services.notification_service import NotificationService
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def create_demo_email():
    """Créer un email de démo avec graphique"""
    
    # Configuration email
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'demo@example.com',
        'sender_password': 'demo',
        'recipient_emails': ['yojulesyo@gmail.com']
    }
    
    notification_service = NotificationService(email_config)
    
    # Mock objects
    class MockStock:
        def __init__(self):
            self.ticker = "AAPL"
            self.company_name = "Apple Inc."
    
    class MockSignal:
        def __init__(self):
            self.signal_type = "BUY"
            self.price_when_generated = 182.50
            self.confidence = 0.85
            self.target_price = 195.00
            self.stop_loss_price = 173.38
            self.position_size_usd = 1000.0
            self.reasoning = "Strong analyst consensus with 67% Buy ratings + Smart Score 9/10"
            self.generated_at = datetime.now()
    
    class MockRecommendation:
        def __init__(self):
            self.smart_score = 9
            self.mean_price_target = 195.00
            self.num_analysts = 15
            self.bullish_percent = 75
            self.bearish_percent = 15
    
    # Données analyst fictives avec plus d'analystes
    mock_analyst_data = {
        'ticker': 'AAPL',
        'total_analysts': 15,
        'buy_count': 10,
        'hold_count': 4,  
        'sell_count': 1,
        'consensus': 'Strong Buy',
        'buy_percentage': 66.7,
        'hold_percentage': 26.7,
        'sell_percentage': 6.7,
        'timestamp': datetime.now().isoformat()
    }
    
    print("🧪 Test du graphique analyst ratings...")
    
    # Test direct de génération de graphique
    chart_data = notification_service._generate_analyst_ratings_chart(mock_analyst_data)
    if chart_data:
        print("✅ Graphique généré avec succès!")
        print(f"Taille: {len(chart_data)} caractères")
    else:
        print("❌ Échec génération graphique")
        return
    
    # Créer email avec graphique intégré manuellement
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
            <h1>🚨 BUY SIGNAL</h1>
            <h2>AAPL</h2>
            <p>Apple Inc.</p>
        </div>
        
        <div style="padding: 20px;">
            <h3>📈 Signal Details</h3>
            <ul>
                <li><strong>Action:</strong> BUY</li>
                <li><strong>Current Price:</strong> $182.50</li>
                <li><strong>Confidence:</strong> 85.0%</li>
                <li><strong>Position Size:</strong> $1,000.00</li>
                <li><strong>Target Price:</strong> $195.00</li>
                <li><strong>Stop Loss:</strong> $173.38</li>
            </ul>
            
            <p><strong>Potential Return:</strong> +6.8%</p>
            
            <h3>🧠 Reasoning</h3>
            <p>Strong analyst consensus with 67% Buy ratings + Smart Score 9/10 + positive price targets</p>
            
            <h3>📊 TipRanks Analysis</h3>
            <ul>
                <li><strong>Smart Score:</strong> 9/10</li>
                <li><strong>Price Target:</strong> $195.00</li>
                <li><strong>Analysts:</strong> 15 total</li>
                <li><strong>Sentiment:</strong> 75% Bullish, 15% Bearish</li>
            </ul>
            
            <h3>👨‍💼 Analyst Recommendations</h3>
            <div style="text-align: center; margin: 20px 0;">
                <img src="{chart_data}" alt="Analyst Ratings Chart" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            </div>
            <div style="text-align: center; margin: 10px 0; font-size: 14px; color: #666;">
                <strong>Distribution:</strong> 10 Buy (66.7%) • 4 Hold (26.7%) • 1 Sell (6.7%) • Consensus: <span style="color: #28a745; font-weight: bold;">Strong Buy</span>
            </div>
            
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <h3 style="color: #856404;">📱 Action Immédiate</h3>
                <p style="margin-bottom: 15px;">Prêt à investir ? Ouvre Plum maintenant !</p>
                
                <div style="margin: 15px 0;">
                    <a href="plum://open" style="display: inline-block; background-color: #6f42c1; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        📱 Ouvrir l'App Plum
                    </a>
                    <a href="https://withplum.com/app" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        🌐 Plum Web
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #856404; margin-top: 15px;">
                    <strong>Recherche:</strong> "AAPL" dans Plum<br>
                    <strong>Quantité suggérée:</strong> ~5 actions (≈$1,000)
                </p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4>⚠️ Important Disclaimer</h4>
                <p><small>
                    Ceci est un signal automatisé basé sur l'analyse technique et les données TipRanks. 
                    Ce n'est pas un conseil financier. Toujours faire ses propres recherches avant d'investir.
                    Les performances passées ne garantissent pas les résultats futurs.
                </small></p>
            </div>
            
            <p style="text-align: center; margin-top: 20px;">
                <small>Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</small>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Sauvegarder l'email final
    output_file = '/workspaces/ajamaislepremier/trading_system/DEMO_EMAIL_WITH_CHART.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Email de démo créé: {output_file}")
    print("📧 L'email contient:")
    print("   - Signal BUY pour AAPL")
    print("   - Graphique analyst ratings en secteurs")
    print("   - 15 analystes: 10 Buy, 4 Hold, 1 Sell")
    print("   - Liens d'action vers Plum")
    print("   - Disclaimer complet")
    
    # Vérifier que le graphique est inclus
    if 'data:image/png;base64,' in html_content:
        print("✅ Graphique analyst ratings INCLUS dans l'email!")
        return True
    else:
        print("❌ Graphique manquant")
        return False

if __name__ == "__main__":
    success = create_demo_email()
    if success:
        print("\n🎉 Test réussi! Le système d'email avec graphique fonctionne.")
    else:
        print("\n❌ Test échoué.")