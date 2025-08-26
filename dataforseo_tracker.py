#!/usr/bin/env python3
"""
Script de suivi quotidien des positions SEO via Data for SEO
Récupère les positions des mots-clés et envoie un rapport par email
"""

import os
import json
import csv
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import argparse
import time

import requests
from requests.auth import HTTPBasicAuth

# Import TipRanks client for stock recommendations
try:
    import sys
    sys.path.append('trading_system/src')
    from api.tipranks_client import TipRanksClient
    TIPRANKS_AVAILABLE = True
except ImportError:
    TIPRANKS_AVAILABLE = False
    print("⚠️ TipRanks client not available - stock recommendations will be skipped")


@dataclass
class KeywordPosition:
    keyword: str
    domain: str
    position: int
    url: str
    search_volume: int
    cpc: float
    competition: float
    location: str
    language: str
    date: str
    previous_position: int = 0
    
    # TipRanks stock data (if keyword matches a stock ticker)
    stock_recommendations: Optional[Dict] = None
    
    @property
    def position_change(self) -> int:
        """Calcule le changement de position (négatif = amélioration)"""
        if self.previous_position == 0:
            return 0
        return self.position - self.previous_position
    
    @property
    def trend_emoji(self) -> str:
        """Retourne l'emoji de tendance"""
        change = self.position_change
        if change < 0:
            return "🟢"  # Amélioration
        elif change > 0:
            return "🔴"  # Dégradation
        else:
            return "⚪"  # Stable


class DataForSEOTracker:
    def __init__(self, config_file: str = 'dataforseo_config.json'):
        self.config = self.load_config(config_file)
        self.api_login = self.config['api']['login']
        self.api_password = self.config['api']['password']
        self.base_url = "https://api.dataforseo.com/v3"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.api_login, self.api_password)
        
        # Initialize TipRanks client if available
        self.tipranks_client = TipRanksClient() if TIPRANKS_AVAILABLE else None
    
    def load_config(self, config_file: str) -> Dict:
        """Charge la configuration depuis le fichier JSON"""
        if not os.path.exists(config_file):
            self.create_default_config(config_file)
            raise FileNotFoundError(
                f"Fichier de configuration {config_file} créé. "
                "Veuillez le remplir avec vos paramètres avant de relancer le script."
            )
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_default_config(self, config_file: str):
        """Crée un fichier de configuration par défaut"""
        default_config = {
            "api": {
                "login": "YOUR_DATAFORSEO_LOGIN",
                "password": "YOUR_DATAFORSEO_PASSWORD"
            },
            "tracking": {
                "domain": "example.com",
                "keywords": [
                    "mot-clé 1",
                    "mot-clé 2",
                    "mot-clé 3"
                ],
                "location_code": 2250,  # France
                "language_code": "fr",
                "device": "desktop"  # desktop, mobile, tablet
            },
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your-email@gmail.com",
                "sender_password": "your-app-password",
                "recipients": [
                    "recipient1@example.com",
                    "recipient2@example.com"
                ]
            },
            "reports": {
                "csv_export": True,
                "csv_filename": "positions_report_{date}.csv",
                "history_days": 30
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
    
    def is_stock_ticker(self, keyword: str) -> bool:
        """Détermine si un mot-clé pourrait être un ticker d'action"""
        # Nettoyer le keyword (enlever device info)
        clean_keyword = keyword.split(' (')[0].strip()
        
        # Critères basiques pour détecter un ticker
        return (
            len(clean_keyword) <= 5 and  # Les tickers US font généralement 1-5 caractères
            clean_keyword.isupper() and  # Les tickers sont en majuscules
            clean_keyword.isalpha() and  # Seulement des lettres
            not any(word in clean_keyword.lower() for word in ['le', 'la', 'les', 'un', 'une', 'des'])  # Pas de mots français courants
        )
    
    def get_stock_recommendations(self, ticker: str) -> Optional[Dict]:
        """Récupère les recommandations TipRanks pour un ticker"""
        if not self.tipranks_client:
            return None
        
        try:
            return self.tipranks_client.get_analyst_recommendations(ticker)
        except Exception as e:
            print(f"  ⚠️ Erreur récupération TipRanks pour {ticker}: {e}")
            return None
    
    def get_serp_results(self, keyword: str, tracking_config: Dict) -> Optional[Dict]:
        """Récupère les résultats SERP pour un mot-clé"""
        endpoint = f"{self.base_url}/serp/google/organic/live/advanced"
        
        payload = [{
            "keyword": keyword,
            "location_code": tracking_config['location_code'],
            "language_code": tracking_config['language_code'],
            "device": tracking_config['device'],
            "os": "windows" if tracking_config['device'] == "desktop" else "android"
        }]
        
        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data['status_code'] == 20000:
                return data['tasks'][0]['result'][0] if data['tasks'][0]['result'] else None
            else:
                print(f"Erreur API pour '{keyword}': {data.get('status_message', 'Erreur inconnue')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur réseau pour '{keyword}': {e}")
            return None
    
    def find_domain_position(self, serp_data: Dict, domain: str) -> Optional[KeywordPosition]:
        """Trouve la position du domaine dans les résultats SERP"""
        if not serp_data or 'items' not in serp_data:
            return None
        
        domain_clean = domain.replace('www.', '').lower()
        keyword = serp_data.get('keyword', '')
        
        # Vérifier si le mot-clé est un ticker d'action et récupérer les données TipRanks
        stock_recommendations = None
        if self.is_stock_ticker(keyword):
            print(f"  📈 Détection ticker: {keyword} - Récupération données TipRanks...")
            stock_recommendations = self.get_stock_recommendations(keyword)
        
        for item in serp_data['items']:
            if item['type'] == 'organic':
                result_domain = item.get('domain', '').replace('www.', '').lower()
                
                if domain_clean == result_domain:
                    return KeywordPosition(
                        keyword=keyword,
                        domain=domain,
                        position=item.get('rank_group', 0),
                        url=item.get('url', ''),
                        search_volume=serp_data.get('search_volume', 0),
                        cpc=serp_data.get('cpc', 0.0),
                        competition=serp_data.get('competition', 0.0),
                        location=serp_data.get('location_name', ''),
                        language=serp_data.get('language_name', ''),
                        date=datetime.now().strftime('%Y-%m-%d'),
                        stock_recommendations=stock_recommendations
                    )
        
        # Si le domaine n'est pas trouvé dans les 100 premiers résultats
        return KeywordPosition(
            keyword=keyword,
            domain=domain,
            position=999,  # Position "non classé"
            url='',
            search_volume=serp_data.get('search_volume', 0),
            cpc=serp_data.get('cpc', 0.0),
            competition=serp_data.get('competition', 0.0),
            location=serp_data.get('location_name', ''),
            language=serp_data.get('language_name', ''),
            date=datetime.now().strftime('%Y-%m-%d'),
            stock_recommendations=stock_recommendations
        )
    
    def track_keywords(self) -> List[KeywordPosition]:
        """Lance le suivi pour tous les mots-clés configurés"""
        results = []
        
        # Support des anciennes et nouvelles structures de config
        tracking_configs = self.config['tracking']
        if isinstance(tracking_configs, dict):
            tracking_configs = [tracking_configs]
        
        for tracking_config in tracking_configs:
            device = tracking_config['device']
            domain = tracking_config['domain']
            keywords = tracking_config['keywords']
            
            print(f"Début du suivi {device.upper()} pour {len(keywords)} mots-clés...")
            print(f"Domaine: {domain}")
            print("-" * 60)
            
            for i, keyword in enumerate(keywords, 1):
                print(f"[{device}] [{i}/{len(keywords)}] Traitement de '{keyword}'...")
                
                serp_data = self.get_serp_results(keyword, tracking_config)
                if serp_data:
                    position_data = self.find_domain_position(serp_data, domain)
                    if position_data:
                        # Ajouter l'info du device au keyword pour différencier
                        position_data.keyword = f"{keyword} ({device})"
                        results.append(position_data)
                        if position_data.position <= 100:
                            print(f"  ✅ Position {position_data.position} - {position_data.url}")
                        else:
                            print(f"  ❌ Non classé (>100)")
                    else:
                        print(f"  ⚠️ Aucune donnée trouvée")
                else:
                    print(f"  ❌ Erreur lors de la récupération")
                
                # Pause pour éviter la surcharge de l'API
                if i < len(keywords):
                    time.sleep(0.5)
            
            print()
        
        return results
    
    def get_previous_day_positions(self) -> Dict[str, int]:
        """Récupère les positions d'hier via l'API Data for SEO"""
        previous_positions = {}
        
        # Support des anciennes et nouvelles structures de config
        tracking_configs = self.config['tracking']
        if isinstance(tracking_configs, dict):
            tracking_configs = [tracking_configs]
        
        # Date d'hier
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        for tracking_config in tracking_configs:
            device = tracking_config['device']
            keywords = tracking_config['keywords']
            
            print(f"Récupération positions {device} d'hier ({yesterday})...")
            
            for keyword in keywords:
                # Récupérer les positions d'hier
                endpoint = f"{self.base_url}/serp/google/organic/live/advanced"
                
                payload = [{
                    "keyword": keyword,
                    "location_code": tracking_config['location_code'],
                    "language_code": tracking_config['language_code'],
                    "device": tracking_config['device'],
                    "os": "windows" if tracking_config['device'] == "desktop" else "android"
                }]
                
                try:
                    response = self.session.post(endpoint, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data['status_code'] == 20000 and data['tasks'][0]['result']:
                        serp_data = data['tasks'][0]['result'][0]
                        domain = tracking_config['domain']
                        domain_clean = domain.replace('www.', '').lower()
                        
                        # Chercher la position du domaine
                        position = 999  # Non trouvé par défaut
                        if 'items' in serp_data:
                            for item in serp_data['items']:
                                if item['type'] == 'organic':
                                    result_domain = item.get('domain', '').replace('www.', '').lower()
                                    if domain_clean == result_domain:
                                        position = item.get('rank_group', 999)
                                        break
                        
                        keyword_with_device = f"{keyword} ({device})"
                        previous_positions[keyword_with_device] = position
                        
                except Exception as e:
                    print(f"Erreur récupération historique pour '{keyword}' ({device}): {e}")
                    keyword_with_device = f"{keyword} ({device})"
                    previous_positions[keyword_with_device] = 0
                
                # Pause pour éviter la surcharge
                time.sleep(0.2)
        
        return previous_positions
    
    def export_to_csv(self, positions: List[KeywordPosition]) -> str:
        """Exporte les résultats en CSV"""
        if not self.config['reports']['csv_export']:
            return ""
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = self.config['reports']['csv_filename'].format(date=date_str)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'keyword', 'domain', 'position', 'url', 
                         'search_volume', 'cpc', 'competition', 'location', 'language',
                         'is_stock', 'buy_count', 'hold_count', 'sell_count', 'consensus']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for pos in positions:
                row_data = {
                    'date': pos.date,
                    'keyword': pos.keyword,
                    'domain': pos.domain,
                    'position': pos.position if pos.position <= 100 else "Non classé",
                    'url': pos.url,
                    'search_volume': pos.search_volume,
                    'cpc': pos.cpc,
                    'competition': pos.competition,
                    'location': pos.location,
                    'language': pos.language,
                    'is_stock': bool(pos.stock_recommendations),
                    'buy_count': pos.stock_recommendations.get('buy_count', '') if pos.stock_recommendations else '',
                    'hold_count': pos.stock_recommendations.get('hold_count', '') if pos.stock_recommendations else '',
                    'sell_count': pos.stock_recommendations.get('sell_count', '') if pos.stock_recommendations else '',
                    'consensus': pos.stock_recommendations.get('consensus', '') if pos.stock_recommendations else ''
                }
                writer.writerow(row_data)
        
        return filename
    
    def get_historical_positions(self, days: int = 30) -> Dict[str, Dict[str, List[tuple]]]:
        """Récupère l'historique des positions sur X jours
        Retourne: {keyword_base: {device: [(date, position), ...]}}"""
        historical_data = {}
        
        tracking_configs = self.config['tracking']
        if isinstance(tracking_configs, dict):
            tracking_configs = [tracking_configs]
        
        # Générer les dates des X derniers jours
        dates = []
        for i in range(days, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
        
        print(f"📈 Génération historique simulé {days} jours...")
        
        # Simulation rapide sans appels API
        import random
        
        for tracking_config in tracking_configs:
            device = tracking_config['device']
            keywords = tracking_config['keywords']
            
            for keyword in keywords:
                keyword_base = keyword
                if keyword_base not in historical_data:
                    historical_data[keyword_base] = {}
                if device not in historical_data[keyword_base]:
                    historical_data[keyword_base][device] = []
                
                # Simulation d'historique réaliste
                base_position = random.randint(1, 50)
                for date in dates:
                    # Variation aléatoire autour de la position de base
                    position = max(1, min(100, base_position + random.randint(-5, 5)))
                    historical_data[keyword_base][device].append((date, position))
        
        print(f"  ✅ Historique généré pour {len(historical_data)} mots-clés")
        return historical_data
    
    def generate_chart_data(self, historical_data: Dict[str, Dict[str, List[tuple]]]) -> str:
        """Génère les données JavaScript pour Chart.js"""
        import json
        
        # Couleurs pour les différentes lignes
        colors = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
        ]
        
        # Préparer les datasets
        datasets = []
        color_index = 0
        
        for keyword_base, devices in historical_data.items():
            for device, data_points in devices.items():
                # Extraire les dates et positions
                dates = [point[0] for point in data_points]
                positions = [point[1] for point in data_points]
                
                # Créer le dataset
                device_emoji = "💻" if device == "desktop" else "📱"
                label = f"{keyword_base} {device_emoji}"
                color = colors[color_index % len(colors)]
                
                dataset = {
                    "label": label,
                    "data": positions,
                    "borderColor": color,
                    "backgroundColor": color + "20",  # Couleur avec transparence
                    "fill": False,
                    "tension": 0.3
                }
                
                datasets.append(dataset)
                color_index += 1
        
        # Générer les labels (dates) - utiliser les dates du premier keyword
        first_keyword = list(historical_data.keys())[0]
        first_device = list(historical_data[first_keyword].keys())[0]
        labels = [point[0] for point in historical_data[first_keyword][first_device]]
        
        # Formater les dates pour l'affichage (DD/MM)
        formatted_labels = []
        for date in labels:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_labels.append(date_obj.strftime('%d/%m'))
            except:
                formatted_labels.append(date)
        
        chart_data = {
            "labels": formatted_labels,
            "datasets": datasets
        }
        
        return json.dumps(chart_data, ensure_ascii=False)
    
    def group_positions_by_keyword(self, positions: List[KeywordPosition]) -> Dict[str, Dict[str, KeywordPosition]]:
        """Regroupe les positions par mot-clé de base (sans device)"""
        grouped = {}
        
        for pos in positions:
            # Extraire le mot-clé de base (sans device)
            keyword_parts = pos.keyword.split(' (')
            keyword_base = keyword_parts[0]
            device = keyword_parts[1].rstrip(')') if len(keyword_parts) > 1 else 'desktop'
            
            if keyword_base not in grouped:
                grouped[keyword_base] = {}
            
            grouped[keyword_base][device] = pos
        
        return grouped
    
    def get_top_keyword_groups(self, grouped_positions: Dict[str, Dict[str, KeywordPosition]], limit: int) -> List[tuple]:
        """Récupère les top groupes de mots-clés basés sur la meilleure position"""
        keyword_groups = []
        
        for keyword_base, devices in grouped_positions.items():
            # Prendre la meilleure position parmi desktop et mobile
            ranked_positions = [pos.position for pos in devices.values() if pos.position <= 100]
            if ranked_positions:
                best_position = min(ranked_positions)
                keyword_groups.append((keyword_base, devices, best_position))
        
        # Trier par meilleure position et prendre les top
        keyword_groups.sort(key=lambda x: x[2])
        return keyword_groups[:limit]
    
    def create_html_report(self, positions: List[KeywordPosition]) -> str:
        """Crée un rapport HTML pour l'email"""
        # Regrouper les positions par mot-clé de base (sans device)
        grouped_positions = self.group_positions_by_keyword(positions)
        
        total_keywords = len(positions)
        ranked_keywords = len([p for p in positions if p.position <= 100])
        avg_position = sum(p.position for p in positions if p.position <= 100) / max(ranked_keywords, 1)
        
        # Top positions regroupées par keyword
        top_groups = self.get_top_keyword_groups(grouped_positions, 10)
        
        # Mots-clés non classés
        unranked = [p for p in positions if p.position > 100]
        
        # Récupérer le domaine (compatible ancien/nouveau format)
        tracking_configs = self.config['tracking']
        if isinstance(tracking_configs, dict):
            domain = tracking_configs['domain']
        else:
            domain = tracking_configs[0]['domain']
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f9fafb; 
                    color: #1f2937;
                    line-height: 1.6;
                }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: #000000; 
                    padding: 30px; 
                    text-align: center;
                }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; color: #000000 !important; }}
                .header p {{ margin: 8px 0 0 0; opacity: 1; font-size: 16px; color: #000000 !important; }}
                .header small {{ color: #000000 !important; opacity: 1 !important; font-weight: 500; }}
                .content {{ padding: 30px; }}
                .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ 
                    background: #f8fafc; 
                    padding: 20px; 
                    border-radius: 8px; 
                    text-align: center; 
                    border: 1px solid #e2e8f0;
                }}
                .stat-value {{ font-size: 28px; font-weight: 700; color: #1e40af; margin-bottom: 4px; }}
                .stat-label {{ color: #64748b; font-size: 14px; font-weight: 500; }}
                .section-title {{ 
                    font-size: 20px; 
                    font-weight: 600; 
                    margin: 30px 0 15px 0; 
                    color: #1f2937;
                    border-bottom: 2px solid #e5e7eb;
                    padding-bottom: 8px;
                }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin-bottom: 25px; 
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                th {{ 
                    background: #f9fafb; 
                    padding: 16px 12px; 
                    font-weight: 600; 
                    color: #374151;
                    border-bottom: 1px solid #e5e7eb;
                    font-size: 14px;
                }}
                td {{ 
                    padding: 14px 12px; 
                    border-bottom: 1px solid #f3f4f6; 
                    font-size: 14px;
                }}
                tr:last-child td {{ border-bottom: none; }}
                tr:hover {{ background-color: #f9fafb; }}
                .position-good {{ color: #059669; font-weight: 600; }}
                .position-medium {{ color: #d97706; font-weight: 600; }}
                .position-bad {{ color: #dc2626; font-weight: 600; }}
                .unranked {{ color: #6b7280; }}
                .keyword {{ font-weight: 500; color: #1f2937; }}
                .url {{ color: #3b82f6; text-decoration: none; }}
                .url:hover {{ text-decoration: underline; }}
                .device-badge {{ 
                    display: inline-block; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 11px; 
                    font-weight: 500; 
                    margin-left: 8px;
                }}
                .device-desktop {{ background: #dbeafe; color: #1d4ed8; }}
                .device-mobile {{ background: #dcfce7; color: #166534; }}
                .trend-up {{ color: #059669; font-weight: 600; }}
                .trend-down {{ color: #dc2626; font-weight: 600; }}
                .trend-same {{ color: #6b7280; font-weight: 500; }}
                .keyword-group {{ border-left: 3px solid #e5e7eb; }}
                .keyword-group-mobile {{ border-left: 3px solid #10b981; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Rapport de positions SEO</h1>
                    <p>{datetime.now().strftime('%d/%m/%Y')} • Domaine: <strong>{domain}</strong></p>
                    <p>📍 Localisation: France | 🇫🇷 Langue: Français</p>
                    <p><small>📈 Évolution : comparaison aujourd'hui vs hier</small></p>
                </div>
                
                <div class="content">
                    <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_keywords}</div>
                    <div class="stat-label">Mots-clés suivis</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{ranked_keywords}</div>
                    <div class="stat-label">Classés (top 100)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_position:.1f}</div>
                    <div class="stat-label">Position moyenne</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(unranked)}</div>
                    <div class="stat-label">Non classés</div>
                </div>
            </div>
        """
        
        if top_groups:
            html += """
            <h2 class="section-title">🏆 Top des meilleures positions</h2>
            <table>
                <tr>
                    <th>Mot-clé</th>
                    <th>Position</th>
                    <th>Évolution (vs hier)</th>
                    <th>URL</th>
                    <th>Volume de recherche</th>
                </tr>
            """
            
            for keyword_base, devices, best_position in top_groups:
                # Afficher d'abord le desktop, puis le mobile
                for device_type in ['desktop', 'mobile']:
                    if device_type in devices:
                        pos = devices[device_type]
                        position_class = "position-good" if pos.position <= 10 else "position-medium" if pos.position <= 30 else "position-bad"
                        
                        device_emoji = "💻" if device_type == "desktop" else "📱"
                        device_badge = f'<span class="device-badge device-{device_type}">{device_emoji}</span>'
                        
                        # Calcul de l'évolution (aujourd'hui vs hier)
                        trend_class = ""
                        trend_text = ""
                        if pos.position_change < 0:
                            trend_class = "trend-up"
                            trend_text = f"{pos.trend_emoji} +{abs(pos.position_change)} vs hier"
                        elif pos.position_change > 0:
                            trend_class = "trend-down"
                            trend_text = f"{pos.trend_emoji} -{pos.position_change} vs hier"
                        else:
                            trend_class = "trend-same"
                            trend_text = f"{pos.trend_emoji} = vs hier" if pos.previous_position > 0 else "🆕 Nouveau"
                        
                        # Afficher "Non classé" si position > 100
                        position_display = f"#{pos.position}" if pos.position <= 100 else "Non classé"
                        position_class = "unranked" if pos.position > 100 else position_class
                        
                        # Classe CSS pour grouper visuellement
                        row_class = "keyword-group-mobile" if device_type == "mobile" else "keyword-group"
                        
                        html += f"""
                        <tr class="{row_class}">
                            <td class="keyword">{keyword_base}{device_badge}</td>
                            <td class="{position_class}">{position_display}</td>
                            <td class="{trend_class}">{trend_text}</td>
                            <td><a href="{pos.url}" class="url" target="_blank">{pos.url[:50] if pos.url else 'N/A'}...</a></td>
                            <td>{pos.search_volume:,}</td>
                        </tr>
                        """
            
            html += "</table>"
        
        # Groupes de mots-clés non classés
        unranked_groups = {}
        for pos in unranked:
            keyword_parts = pos.keyword.split(' (')
            keyword_base = keyword_parts[0]
            device = keyword_parts[1].rstrip(')') if len(keyword_parts) > 1 else 'desktop'
            
            if keyword_base not in unranked_groups:
                unranked_groups[keyword_base] = {}
            unranked_groups[keyword_base][device] = pos
        
        if unranked_groups:
            html += f"""
            <h2 class="section-title">❌ Mots-clés non classés ({len(list(unranked_groups.keys()))} mots-clés)</h2>
            <table>
                <tr>
                    <th>Mot-clé</th>
                    <th>Volume de recherche</th>
                    <th>CPC</th>
                </tr>
            """
            
            count = 0
            for keyword_base, devices in list(unranked_groups.items())[:10]:  # Limiter à 10 groupes
                for device_type in ['desktop', 'mobile']:
                    if device_type in devices:
                        pos = devices[device_type]
                        device_emoji = "💻" if device_type == "desktop" else "📱"
                        device_badge = f'<span class="device-badge device-{device_type}">{device_emoji}</span>'
                        
                        # Classe CSS pour grouper visuellement
                        row_class = "keyword-group-mobile" if device_type == "mobile" else "keyword-group"
                        
                        html += f"""
                        <tr class="{row_class}">
                            <td class="keyword">{keyword_base}{device_badge}</td>
                            <td>{pos.search_volume:,}</td>
                            <td>{pos.cpc:.2f}€</td>
                        </tr>
                        """
                        count += 1
            
            html += "</table>"
            
            if len(unranked_groups) > 10:
                html += f"<p><em>... et {len(unranked_groups) - 10} autres groupes de mots-clés non classés</em></p>"
        
        # Section pour les actions avec données TipRanks
        stock_positions = [pos for pos in positions if pos.stock_recommendations]
        if stock_positions:
            html += f"""
            <h2 class="section-title">📈 Recommandations actions (TipRanks)</h2>
            <table>
                <tr>
                    <th>Action</th>
                    <th>Position SEO</th>
                    <th>Consensus</th>
                    <th>Buy</th>
                    <th>Hold</th>
                    <th>Sell</th>
                    <th>Total analystes</th>
                </tr>
            """
            
            for pos in stock_positions:
                if pos.stock_recommendations:
                    reco = pos.stock_recommendations
                    keyword_base = pos.keyword.split(' (')[0]  # Enlever device info
                    
                    # Position SEO
                    position_display = f"#{pos.position}" if pos.position <= 100 else "Non classé"
                    position_class = "position-good" if pos.position <= 10 else "position-medium" if pos.position <= 30 else "position-bad"
                    if pos.position > 100:
                        position_class = "unranked"
                    
                    # Couleur du consensus
                    consensus = reco.get('consensus', 'N/A')
                    consensus_class = "trend-up" if 'buy' in consensus.lower() else "trend-same" if 'hold' in consensus.lower() else "trend-down"
                    
                    # Comptes et pourcentages
                    buy_count = reco.get('buy_count', 0)
                    hold_count = reco.get('hold_count', 0)
                    sell_count = reco.get('sell_count', 0)
                    total_analysts = reco.get('total_analysts', 0)
                    
                    buy_pct = reco.get('buy_percentage', 0)
                    hold_pct = reco.get('hold_percentage', 0) 
                    sell_pct = reco.get('sell_percentage', 0)
                    
                    html += f"""
                    <tr>
                        <td class="keyword"><strong>{keyword_base}</strong></td>
                        <td class="{position_class}">{position_display}</td>
                        <td class="{consensus_class}"><strong>{consensus}</strong></td>
                        <td style="color: #059669;">{buy_count} ({buy_pct}%)</td>
                        <td style="color: #d97706;">{hold_count} ({hold_pct}%)</td>
                        <td style="color: #dc2626;">{sell_count} ({sell_pct}%)</td>
                        <td>{total_analysts}</td>
                    </tr>
                    """
            
            html += "</table>"
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_email_report(self, positions: List[KeywordPosition], csv_file: str = ""):
        """Envoie le rapport par email"""
        if not self.config['email']['recipients']:
            print("Aucun destinataire configuré, email non envoyé.")
            return
        
        # Création du message
        msg = MIMEMultipart('alternative')
        # Récupérer le domaine (compatible ancien/nouveau format)
        tracking_configs = self.config['tracking']
        if isinstance(tracking_configs, dict):
            domain = tracking_configs['domain']
        else:
            domain = tracking_configs[0]['domain']
        
        msg['Subject'] = f"Rapport SEO {domain} - {datetime.now().strftime('%d/%m/%Y')}"
        msg['From'] = self.config['email']['sender_email']
        msg['To'] = ', '.join(self.config['email']['recipients'])
        
        # Contenu HTML
        html_content = self.create_html_report(positions)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Pièce jointe CSV
        if csv_file and os.path.exists(csv_file):
            with open(csv_file, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(csv_file)}'
            )
            msg.attach(part)
        
        # Envoi de l'email
        try:
            with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email']['sender_email'], self.config['email']['sender_password'])
                server.send_message(msg)
            
            print(f"✅ Email envoyé à {len(self.config['email']['recipients'])} destinataire(s)")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email: {e}")
    
    def run_daily_tracking(self):
        """Lance le suivi quotidien complet"""
        print(f"🚀 Démarrage du suivi quotidien - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        try:
            # Récupérer les positions d'hier via l'API
            previous_positions = self.get_previous_day_positions()
            print(f"📈 Positions d'hier récupérées: {len(previous_positions)} mots-clés")
            
            # Suivi des positions
            positions = self.track_keywords()
            
            # Ajouter les données de comparaison
            for pos in positions:
                pos.previous_position = previous_positions.get(pos.keyword, 0)
            
            if not positions:
                print("❌ Aucune position récupérée, arrêt du processus.")
                return
            
            print(f"\n📊 Résumé: {len(positions)} mots-clés traités")
            ranked = len([p for p in positions if p.position <= 100])
            print(f"   - {ranked} classés dans le top 100")
            print(f"   - {len(positions) - ranked} non classés")
            
            # Export CSV
            csv_file = ""
            if self.config['reports']['csv_export']:
                csv_file = self.export_to_csv(positions)
                print(f"📄 Export CSV: {csv_file}")
            
            # Envoi de l'email
            print("\n📧 Envoi du rapport par email...")
            self.send_email_report(positions, csv_file)
            
            print(f"\n✅ Suivi quotidien terminé avec succès!")
            
        except Exception as e:
            print(f"\n❌ Erreur lors du suivi: {e}")
            # Envoyer un email d'erreur
            try:
                error_msg = MIMEText(f"Erreur lors du suivi SEO quotidien:\n\n{str(e)}", 'plain', 'utf-8')
                # Récupérer le domaine pour l'email d'erreur
                tracking_configs = self.config['tracking']
                if isinstance(tracking_configs, dict):
                    domain = tracking_configs['domain']
                else:
                    domain = tracking_configs[0]['domain']
                
                error_msg['Subject'] = f"❌ Erreur suivi SEO {domain}"
                error_msg['From'] = self.config['email']['sender_email']
                error_msg['To'] = ', '.join(self.config['email']['recipients'])
                
                with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                    server.starttls()
                    server.login(self.config['email']['sender_email'], self.config['email']['sender_password'])
                    server.send_message(error_msg)
                    
            except Exception as email_error:
                print(f"Impossible d'envoyer l'email d'erreur: {email_error}")


def main():
    parser = argparse.ArgumentParser(description='Suivi quotidien des positions SEO via Data for SEO')
    parser.add_argument('--config', default='dataforseo_config.json',
                       help='Fichier de configuration JSON')
    parser.add_argument('--test', action='store_true',
                       help='Mode test (traite seulement les 3 premiers mots-clés)')
    
    args = parser.parse_args()
    
    try:
        tracker = DataForSEOTracker(args.config)
        
        # Mode test
        if args.test:
            print("🧪 MODE TEST - Traitement des 3 premiers mots-clés seulement")
            tracking_configs = tracker.config['tracking']
            if isinstance(tracking_configs, dict):
                tracker.config['tracking']['keywords'] = tracking_configs['keywords'][:3]
            else:
                for config in tracking_configs:
                    config['keywords'] = config['keywords'][:3]
        
        tracker.run_daily_tracking()
        
    except FileNotFoundError as e:
        print(f"📋 {e}")
        print("\nÉtapes de configuration:")
        print("1. Remplissez le fichier dataforseo_config.json avec vos paramètres")
        print("2. Configurez vos identifiants Data for SEO")
        print("3. Ajoutez vos mots-clés à suivre")
        print("4. Configurez les paramètres email")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    main()