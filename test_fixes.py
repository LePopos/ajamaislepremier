#!/usr/bin/env python3
"""
Script de test des corrections apportées au système de trading
"""

import os
import sys
sys.path.append('trading_system')

from src.api.alpha_vantage_client import AlphaVantageClient
from src.api.tipranks_client import TipRanksClient
from src.services.data_collector import DataCollector
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alpha_vantage():
    """Test Alpha Vantage avec corrections de date"""
    logger.info("🧪 Test Alpha Vantage...")
    
    api_key = "7LWO5KH8NV7188YL"  # Depuis .env
    client = AlphaVantageClient(api_key)
    
    # Test de récupération de données
    quote = client.get_real_time_quote("AAPL")
    logger.info(f"✅ Quote AAPL: {quote}")
    
    return bool(quote)

def test_tipranks():
    """Test TipRanks avec nouveaux endpoints"""
    logger.info("🧪 Test TipRanks...")
    
    client = TipRanksClient()
    
    # Test price targets avec nouvel endpoint
    price_targets = client.get_price_targets("AAPL")
    logger.info(f"✅ Price targets AAPL: {price_targets}")
    
    # Test sentiment avec nouvel endpoint
    sentiment = client.get_news_sentiment("AAPL")
    logger.info(f"✅ Sentiment AAPL: {sentiment}")
    
    return bool(price_targets) or bool(sentiment)

def test_data_collector():
    """Test DataCollector avec corrections de datetime"""
    logger.info("🧪 Test DataCollector...")
    
    try:
        alpha_client = AlphaVantageClient("7LWO5KH8NV7188YL")
        tipranks_client = TipRanksClient()
        collector = DataCollector(tipranks_client, alpha_client)
        
        # Test cleanup_old_data avec corrections de timedelta
        cleanup_result = collector.cleanup_old_data(30)
        logger.info(f"✅ Cleanup result: {cleanup_result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DataCollector test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Début des tests des corrections...")
    
    results = {
        "alpha_vantage": test_alpha_vantage(),
        "tipranks": test_tipranks(), 
        "data_collector": test_data_collector()
    }
    
    logger.info("📊 Résultats des tests:")
    for test_name, result in results.items():
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        logger.info(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("🎉 Tous les tests sont passés ! Le système est corrigé.")
    else:
        logger.error("💥 Certains tests ont échoué. Vérifiez les logs.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)