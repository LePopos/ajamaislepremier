#!/usr/bin/env python3
"""
Test script pour tester le nouveau graphique analyst ratings dans les emails
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from src.models.stock_models import TradingSignal, Stock, Recommendation
from src.services.notification_service import NotificationService
from src.api.tipranks_client import TipRanksClient

def test_email_with_chart():
    """Test l'envoi d'email avec le graphique analyst ratings"""
    
    print("🧪 Test du graphique analyst ratings dans l'email...")
    
    # Configuration email de test (pas d'envoi réel)
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'test@example.com',  # Configuration fictive
        'sender_password': 'test_password',
        'recipient_emails': ['yojulesyo@gmail.com']
    }
    
    # Créer le service de notification
    notification_service = NotificationService(email_config)
    
    # Test avec AAPL - créer un objet simple pour le test
    class MockStock:
        def __init__(self):
            self.ticker = "AAPL"
            self.company_name = "Apple Inc."
    
    class MockSignal:
        def __init__(self):
            self.ticker = "AAPL"
            self.signal_type = "BUY"
            self.price_when_generated = 182.50
            self.confidence = 0.85
            self.target_price = 195.00
            self.stop_loss_price = 173.38
            self.position_size_usd = 1000.0
            self.reasoning = "Strong Smart Score + bullish analyst sentiment + positive price targets"
            self.generated_at = datetime.now()
    
    class MockRecommendation:
        def __init__(self):
            self.ticker = "AAPL"
            self.smart_score = 9
            self.mean_price_target = 195.00
            self.num_analysts = 12
            self.bullish_percent = 75
            self.bearish_percent = 15
    
    stock = MockStock()
    signal = MockSignal()
    recommendation = MockRecommendation()
    
    print("📊 Test du client TipRanks...")
    tipranks_client = TipRanksClient()
    
    # Test avec des données fictives pour démonstration
    print("📈 Création de données analyst fictives pour AAPL...")
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
    
    print(f"Données analyst fictives: {mock_analyst_data}")
    
    # Test de génération du graphique avec des données fictives
    print("📈 Génération du graphique avec données fictives...")
    chart_data = notification_service._generate_analyst_ratings_chart(mock_analyst_data)
    if chart_data:
        print("✅ Graphique généré avec succès!")
        print(f"Taille des données: {len(chart_data)} caractères")
        print(f"Début des données: {chart_data[:100]}...")
    else:
        print("❌ Échec de génération du graphique")
    
    # Test de récupération réelle (peut échouer)
    print("\n🔍 Test de récupération réelle TipRanks (optionnel)...")
    try:
        real_analyst_data = tipranks_client.get_analyst_recommendations("AAPL")
        print(f"Données TipRanks réelles: {real_analyst_data}")
    except Exception as e:
        print(f"⚠️ Échec récupération TipRanks réelles: {e}")
    
    # Modifier temporairement la fonction pour utiliser les données fictives
    print("📧 Génération du contenu email avec données fictives...")
    
    # Sauvegarder la fonction originale
    original_get_recommendations = tipranks_client.get_analyst_recommendations
    
    # Remplacer temporairement avec des données fictives
    def mock_get_recommendations(ticker):
        return mock_analyst_data
    
    tipranks_client.get_analyst_recommendations = mock_get_recommendations
    
    # Générer l'HTML
    html_content = notification_service._create_signal_email_html(signal, stock, recommendation)
    
    # Restaurer la fonction originale
    tipranks_client.get_analyst_recommendations = original_get_recommendations
    
    # Sauvegarder l'HTML pour inspection
    with open('/workspaces/ajamaislepremier/trading_system/test_email_with_chart.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Email HTML généré et sauvé dans 'test_email_with_chart.html'")
    print("📂 Tu peux ouvrir ce fichier dans un navigateur pour voir le résultat")
    
    # Vérifier que le graphique est inclus
    if 'data:image/png;base64,' in html_content:
        print("✅ Graphique analyst ratings inclus dans l'email!")
    else:
        print("❌ Graphique analyst ratings manquant")
    
    return True

if __name__ == "__main__":
    try:
        test_email_with_chart()
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()