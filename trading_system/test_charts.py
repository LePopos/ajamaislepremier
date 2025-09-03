#!/usr/bin/env python3
"""
Script de test pour les graphiques de tendance
Génère des graphiques avec de vraies données Yahoo Finance
"""

import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.chart_generator import TrendChartGenerator
from src.services.enhanced_analyzer import EnhancedAnalyzer

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_chart_generation():
    """Test de génération des graphiques"""
    print("🔍 Test des graphiques de tendance avec vraies données...")
    
    # Initialiser le générateur
    chart_gen = TrendChartGenerator()
    
    # Tickers de test
    test_tickers = ['NVDA', 'AAPL', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\n📊 Génération des graphiques pour {ticker}...")
        
        try:
            # 1. Graphiques de tendance multi-périodes
            trend_charts = chart_gen.generate_trend_chart(ticker, periods=['3mo', '6mo'])
            if trend_charts:
                print(f"✅ Graphiques de tendance générés:")
                for period, path in trend_charts.items():
                    print(f"   - {period}: {path}")
            
            # 2. Graphique interactif
            interactive_chart = chart_gen.generate_interactive_chart(ticker, '6mo')
            if interactive_chart:
                print(f"✅ Graphique interactif: {interactive_chart}")
            
            # 3. Test de l'analyse complète avec graphiques
            analyzer = EnhancedAnalyzer()
            analysis = analyzer.get_comprehensive_analysis(ticker, 100.0)  # Prix fictif pour test
            
            if 'trend_charts' in analysis:
                print(f"✅ Analyse complète avec graphiques générée")
                charts = analysis['trend_charts']
                print(f"   - Graphiques inclus: {list(charts.keys())}")
            
        except Exception as e:
            print(f"❌ Erreur pour {ticker}: {e}")

def test_comparison_chart():
    """Test du graphique de comparaison"""
    print("\n📊 Test graphique de comparaison...")
    
    chart_gen = TrendChartGenerator()
    
    # Comparaison des actions tech
    tickers = ['NVDA', 'AMD', 'INTC']
    
    try:
        comparison_chart = chart_gen.generate_comparison_chart(tickers, '6mo')
        if comparison_chart:
            print(f"✅ Graphique de comparaison généré: {comparison_chart}")
        else:
            print("❌ Échec génération graphique de comparaison")
            
    except Exception as e:
        print(f"❌ Erreur comparaison: {e}")

def list_generated_charts():
    """Liste les graphiques générés"""
    print("\n📁 Graphiques générés:")
    
    charts_dir = "charts"
    if os.path.exists(charts_dir):
        files = os.listdir(charts_dir)
        if files:
            for file in sorted(files):
                filepath = os.path.join(charts_dir, file)
                size = os.path.getsize(filepath)
                print(f"   - {file} ({size:,} bytes)")
        else:
            print("   Aucun graphique trouvé")
    else:
        print("   Répertoire charts introuvable")

if __name__ == "__main__":
    setup_logging()
    
    print("🚀 Test du système de graphiques de tendance")
    print("=" * 50)
    
    # Tests
    test_chart_generation()
    test_comparison_chart()
    list_generated_charts()
    
    print("\n✅ Tests terminés!")
    print("📁 Vérifiez le répertoire 'charts' pour voir les graphiques générés")