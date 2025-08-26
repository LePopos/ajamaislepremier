#!/usr/bin/env python3
"""
Système de monitoring automatisé pour le DataForSEO tracker
- Scheduling automatique aux heures optimales du marché US
- Surveillance temps réel des changements TipRanks
- Alertes sur mouvements importants
"""

import os
import json
import time
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

# Import du tracker existant
from dataforseo_tracker import DataForSEOTracker, KeywordPosition

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class RecommendationChange:
    """Représente un changement de recommandation"""
    ticker: str
    old_consensus: str
    new_consensus: str
    old_buy_count: int
    new_buy_count: int
    old_hold_count: int
    new_hold_count: int
    old_sell_count: int
    new_sell_count: int
    change_magnitude: int  # Nombre total d'analystes qui ont changé
    timestamp: str
    
    @property
    def is_major_change(self) -> bool:
        """Détermine si c'est un changement majeur"""
        consensus_changed = self.old_consensus != self.new_consensus
        analyst_change = abs(self.change_magnitude) >= 5
        big_shift = (
            abs(self.new_buy_count - self.old_buy_count) >= 3 or
            abs(self.new_sell_count - self.old_sell_count) >= 3
        )
        
        return consensus_changed or analyst_change or big_shift


class TradingMonitor:
    """Système de monitoring automatisé"""
    
    def __init__(self, config_file: str = 'dataforseo_config.json'):
        self.config_file = config_file
        self.tracker = DataForSEOTracker(config_file)
        self.data_file = 'trading_monitor_data.json'
        self.last_recommendations = self.load_last_recommendations()
        self.is_monitoring = False
        self.monitoring_thread = None
        
    def load_last_recommendations(self) -> Dict[str, Dict]:
        """Charge les dernières recommandations sauvegardées"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur chargement données: {e}")
        return {}
    
    def save_recommendations(self, recommendations: Dict[str, Dict]):
        """Sauvegarde les recommandations actuelles"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(recommendations, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Erreur sauvegarde données: {e}")
    
    def get_stock_tickers_from_config(self) -> List[str]:
        """Extrait les tickers d'actions de la configuration"""
        tickers = []
        
        tracking_configs = self.tracker.config['tracking']
        if isinstance(tracking_configs, dict):
            tracking_configs = [tracking_configs]
        
        for config in tracking_configs:
            keywords = config.get('keywords', [])
            for keyword in keywords:
                if self.tracker.is_stock_ticker(keyword):
                    tickers.append(keyword.upper())
        
        return list(set(tickers))  # Remove duplicates
    
    def check_recommendation_changes(self) -> List[RecommendationChange]:
        """Vérifie les changements de recommandations"""
        if not self.tracker.tipranks_client:
            return []
        
        changes = []
        tickers = self.get_stock_tickers_from_config()
        
        logger.info(f"🔍 Vérification de {len(tickers)} tickers: {tickers}")
        
        current_recommendations = {}
        
        for ticker in tickers:
            try:
                current_reco = self.tracker.get_stock_recommendations(ticker)
                if not current_reco:
                    continue
                
                current_recommendations[ticker] = current_reco
                
                # Comparer avec les précédentes recommandations
                if ticker in self.last_recommendations:
                    old_reco = self.last_recommendations[ticker]
                    
                    change = RecommendationChange(
                        ticker=ticker,
                        old_consensus=old_reco.get('consensus', ''),
                        new_consensus=current_reco.get('consensus', ''),
                        old_buy_count=old_reco.get('buy_count', 0),
                        new_buy_count=current_reco.get('buy_count', 0),
                        old_hold_count=old_reco.get('hold_count', 0),
                        new_hold_count=current_reco.get('hold_count', 0),
                        old_sell_count=old_reco.get('sell_count', 0),
                        new_sell_count=current_reco.get('sell_count', 0),
                        change_magnitude=abs(
                            (current_reco.get('buy_count', 0) - old_reco.get('buy_count', 0)) +
                            (current_reco.get('hold_count', 0) - old_reco.get('hold_count', 0)) +
                            (current_reco.get('sell_count', 0) - old_reco.get('sell_count', 0))
                        ),
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # Vérifier si c'est un changement significatif
                    if (change.old_consensus != change.new_consensus or 
                        change.change_magnitude > 0):
                        changes.append(change)
                        
                        if change.is_major_change:
                            logger.warning(f"🚨 Changement majeur détecté pour {ticker}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Erreur vérification {ticker}: {e}")
        
        # Sauvegarder les nouvelles recommandations
        self.last_recommendations.update(current_recommendations)
        self.save_recommendations(self.last_recommendations)
        
        return changes
    
    def send_alert_email(self, changes: List[RecommendationChange]):
        """Envoie un email d'alerte pour les changements importants"""
        if not changes:
            return
        
        major_changes = [c for c in changes if c.is_major_change]
        if not major_changes:
            return
        
        # Créer le contenu de l'email d'alerte
        html_content = self.create_alert_html(major_changes)
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import smtplib
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 ALERTE TipRanks - {len(major_changes)} changement(s) majeur(s)"
            msg['From'] = self.tracker.config['email']['sender_email']
            msg['To'] = ', '.join(self.tracker.config['email']['recipients'])
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.tracker.config['email']['smtp_server'], 
                             self.tracker.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(self.tracker.config['email']['sender_email'], 
                           self.tracker.config['email']['sender_password'])
                server.send_message(msg)
            
            logger.info(f"✅ Alerte envoyée pour {len(major_changes)} changements majeurs")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi alerte: {e}")
    
    def create_alert_html(self, changes: List[RecommendationChange]) -> str:
        """Crée le contenu HTML pour l'email d'alerte"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
                .alert-header {{ background: #dc2626; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .change-card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin: 10px 0; }}
                .ticker {{ font-size: 18px; font-weight: bold; color: #1f2937; }}
                .consensus-change {{ font-size: 16px; margin: 10px 0; }}
                .old {{ color: #dc2626; }}
                .new {{ color: #059669; }}
                .counts {{ display: flex; gap: 20px; margin: 10px 0; }}
                .count {{ text-align: center; }}
            </style>
        </head>
        <body>
            <div class="alert-header">
                <h1>🚨 ALERTE - Changements TipRanks</h1>
                <p>{datetime.now().strftime('%d/%m/%Y à %H:%M')} - {len(changes)} changement(s) majeur(s) détecté(s)</p>
            </div>
        """
        
        for change in changes:
            consensus_color = "color: #059669;" if 'buy' in change.new_consensus.lower() else "color: #dc2626;" if 'sell' in change.new_consensus.lower() else "color: #d97706;"
            
            html += f"""
            <div class="change-card">
                <div class="ticker">📈 {change.ticker}</div>
                <div class="consensus-change">
                    Consensus: <span class="old">{change.old_consensus}</span> → 
                    <span class="new" style="{consensus_color}">{change.new_consensus}</span>
                </div>
                <div class="counts">
                    <div class="count">
                        <strong>Buy</strong><br>
                        {change.old_buy_count} → {change.new_buy_count}
                        <span style="color: {'#059669' if change.new_buy_count > change.old_buy_count else '#dc2626' if change.new_buy_count < change.old_buy_count else '#6b7280'};">
                            ({change.new_buy_count - change.old_buy_count:+d})
                        </span>
                    </div>
                    <div class="count">
                        <strong>Hold</strong><br>
                        {change.old_hold_count} → {change.new_hold_count}
                        <span style="color: {'#059669' if change.new_hold_count > change.old_hold_count else '#dc2626' if change.new_hold_count < change.old_hold_count else '#6b7280'};">
                            ({change.new_hold_count - change.old_hold_count:+d})
                        </span>
                    </div>
                    <div class="count">
                        <strong>Sell</strong><br>
                        {change.old_sell_count} → {change.new_sell_count}
                        <span style="color: {'#dc2626' if change.new_sell_count > change.old_sell_count else '#059669' if change.new_sell_count < change.old_sell_count else '#6b7280'};">
                            ({change.new_sell_count - change.old_sell_count:+d})
                        </span>
                    </div>
                </div>
                <p><small>Détecté le {change.timestamp}</small></p>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def run_daily_report(self):
        """Lance le rapport quotidien complet"""
        logger.info("📊 Lancement du rapport quotidien complet")
        try:
            self.tracker.run_daily_tracking()
        except Exception as e:
            logger.error(f"Erreur rapport quotidien: {e}")
    
    def run_quick_check(self):
        """Vérification rapide et alertes"""
        logger.info("🔍 Vérification rapide des changements")
        try:
            changes = self.check_recommendation_changes()
            if changes:
                self.send_alert_email(changes)
                logger.info(f"✅ {len(changes)} changements détectés")
            else:
                logger.info("➡️ Aucun changement détecté")
        except Exception as e:
            logger.error(f"Erreur vérification rapide: {e}")
    
    def start_monitoring(self):
        """Démarre le monitoring en temps réel"""
        logger.info("🚀 Démarrage du monitoring automatisé")
        
        # Planning des tâches
        schedule.clear()
        
        # 09h00 : Rapport quotidien complet (pré-ouverture EU)
        schedule.every().day.at("09:00").do(self.run_daily_report)
        
        # 15h30 : Vérification ouverture US
        schedule.every().day.at("15:30").do(self.run_quick_check)
        
        # 18h00 : Vérification mi-session US
        schedule.every().day.at("18:00").do(self.run_quick_check)
        
        # 22h00 : Vérification post-clôture US
        schedule.every().day.at("22:00").do(self.run_quick_check)
        
        # Vérifications périodiques pendant les heures de trading US (15h30-22h)
        # Toutes les 30 minutes
        schedule.every().hour.at(":00").do(self._conditional_check)
        schedule.every().hour.at(":30").do(self._conditional_check)
        
        logger.info("📅 Planning configuré:")
        logger.info("   09h00 : Rapport quotidien complet")
        logger.info("   15h30 : Check ouverture US")
        logger.info("   18h00 : Check mi-session US") 
        logger.info("   22h00 : Check post-clôture US")
        logger.info("   15h30-22h : Vérifications toutes les 30min")
        
        # Lancer le monitoring
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.monitoring_thread.start()
        
        return self.monitoring_thread
    
    def _conditional_check(self):
        """Vérification conditionnelle pendant les heures de trading"""
        current_hour = datetime.now().hour
        # Seulement pendant les heures de trading US (15h30-22h heure française)
        if 15 <= current_hour <= 22:
            self.run_quick_check()
    
    def _run_scheduler(self):
        """Exécute le scheduler en boucle"""
        while self.is_monitoring:
            schedule.run_pending()
            time.sleep(60)  # Vérifier toutes les minutes
    
    def stop_monitoring(self):
        """Arrête le monitoring"""
        logger.info("🛑 Arrêt du monitoring")
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading Monitor - Système de monitoring automatisé")
    parser.add_argument('--config', default='dataforseo_config.json', help='Fichier de configuration')
    parser.add_argument('--daemon', action='store_true', help='Lancer en mode daemon')
    parser.add_argument('--check-now', action='store_true', help='Vérification immédiate')
    parser.add_argument('--report-now', action='store_true', help='Rapport immédiat')
    
    args = parser.parse_args()
    
    try:
        monitor = TradingMonitor(args.config)
        
        if args.check_now:
            logger.info("🔍 Vérification immédiate demandée")
            changes = monitor.check_recommendation_changes()
            if changes:
                monitor.send_alert_email(changes)
                print(f"✅ {len(changes)} changements détectés et traités")
            else:
                print("➡️ Aucun changement détecté")
        
        elif args.report_now:
            logger.info("📊 Rapport immédiat demandé")
            monitor.run_daily_report()
        
        elif args.daemon:
            logger.info("🚀 Démarrage en mode daemon")
            thread = monitor.start_monitoring()
            
            try:
                # Garder le programme vivant
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("⏹️ Arrêt demandé par l'utilisateur")
                monitor.stop_monitoring()
        else:
            print("Usage:")
            print("  --daemon        : Lancer le monitoring automatique")
            print("  --check-now     : Vérification immédiate")
            print("  --report-now    : Rapport immédiat")
    
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        raise


if __name__ == "__main__":
    main()