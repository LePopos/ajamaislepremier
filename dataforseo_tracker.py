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


class DataForSEOTracker:
    def __init__(self, config_file: str = 'dataforseo_config.json'):
        self.config = self.load_config(config_file)
        self.api_login = self.config['api']['login']
        self.api_password = self.config['api']['password']
        self.base_url = "https://api.dataforseo.com/v3"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.api_login, self.api_password)
    
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
    
    def get_serp_results(self, keyword: str) -> Optional[Dict]:
        """Récupère les résultats SERP pour un mot-clé"""
        endpoint = f"{self.base_url}/serp/google/organic/live/advanced"
        
        payload = [{
            "keyword": keyword,
            "location_code": self.config['tracking']['location_code'],
            "language_code": self.config['tracking']['language_code'],
            "device": self.config['tracking']['device'],
            "os": "windows" if self.config['tracking']['device'] == "desktop" else "android"
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
        
        for item in serp_data['items']:
            if item['type'] == 'organic':
                result_domain = item.get('domain', '').replace('www.', '').lower()
                
                if domain_clean == result_domain:
                    return KeywordPosition(
                        keyword=serp_data.get('keyword', ''),
                        domain=domain,
                        position=item.get('rank_group', 0),
                        url=item.get('url', ''),
                        search_volume=serp_data.get('search_volume', 0),
                        cpc=serp_data.get('cpc', 0.0),
                        competition=serp_data.get('competition', 0.0),
                        location=serp_data.get('location_name', ''),
                        language=serp_data.get('language_name', ''),
                        date=datetime.now().strftime('%Y-%m-%d')
                    )
        
        # Si le domaine n'est pas trouvé dans les 100 premiers résultats
        return KeywordPosition(
            keyword=serp_data.get('keyword', ''),
            domain=domain,
            position=999,  # Position "non classé"
            url='',
            search_volume=serp_data.get('search_volume', 0),
            cpc=serp_data.get('cpc', 0.0),
            competition=serp_data.get('competition', 0.0),
            location=serp_data.get('location_name', ''),
            language=serp_data.get('language_name', ''),
            date=datetime.now().strftime('%Y-%m-%d')
        )
    
    def track_keywords(self) -> List[KeywordPosition]:
        """Lance le suivi pour tous les mots-clés configurés"""
        print(f"Début du suivi pour {len(self.config['tracking']['keywords'])} mots-clés...")
        print(f"Domaine: {self.config['tracking']['domain']}")
        print("-" * 60)
        
        results = []
        keywords = self.config['tracking']['keywords']
        
        for i, keyword in enumerate(keywords, 1):
            print(f"[{i}/{len(keywords)}] Traitement de '{keyword}'...")
            
            serp_data = self.get_serp_results(keyword)
            if serp_data:
                position_data = self.find_domain_position(serp_data, self.config['tracking']['domain'])
                if position_data:
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
                time.sleep(1)
        
        return results
    
    def export_to_csv(self, positions: List[KeywordPosition]) -> str:
        """Exporte les résultats en CSV"""
        if not self.config['reports']['csv_export']:
            return ""
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = self.config['reports']['csv_filename'].format(date=date_str)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'keyword', 'domain', 'position', 'url', 
                         'search_volume', 'cpc', 'competition', 'location', 'language']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for pos in positions:
                writer.writerow({
                    'date': pos.date,
                    'keyword': pos.keyword,
                    'domain': pos.domain,
                    'position': pos.position if pos.position <= 100 else "Non classé",
                    'url': pos.url,
                    'search_volume': pos.search_volume,
                    'cpc': pos.cpc,
                    'competition': pos.competition,
                    'location': pos.location,
                    'language': pos.language
                })
        
        return filename
    
    def create_html_report(self, positions: List[KeywordPosition]) -> str:
        """Crée un rapport HTML pour l'email"""
        total_keywords = len(positions)
        ranked_keywords = len([p for p in positions if p.position <= 100])
        avg_position = sum(p.position for p in positions if p.position <= 100) / max(ranked_keywords, 1)
        
        # Top 10 positions
        top_positions = sorted([p for p in positions if p.position <= 100], key=lambda x: x.position)[:10]
        
        # Mots-clés non classés
        unranked = [p for p in positions if p.position > 100]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .stat-card {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ color: #6c757d; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                .position-good {{ color: #28a745; font-weight: bold; }}
                .position-medium {{ color: #ffc107; font-weight: bold; }}
                .position-bad {{ color: #dc3545; font-weight: bold; }}
                .unranked {{ color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de positions SEO - {datetime.now().strftime('%d/%m/%Y')}</h1>
                <p>Domaine: <strong>{self.config['tracking']['domain']}</strong></p>
                <p>Localisation: {positions[0].location if positions else 'N/A'} | 
                   Langue: {positions[0].language if positions else 'N/A'}</p>
            </div>
            
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
        
        if top_positions:
            html += """
            <h2>🏆 Top 10 des meilleures positions</h2>
            <table>
                <tr>
                    <th>Mot-clé</th>
                    <th>Position</th>
                    <th>URL</th>
                    <th>Volume de recherche</th>
                </tr>
            """
            
            for pos in top_positions:
                position_class = "position-good" if pos.position <= 10 else "position-medium" if pos.position <= 30 else "position-bad"
                html += f"""
                <tr>
                    <td>{pos.keyword}</td>
                    <td class="{position_class}">#{pos.position}</td>
                    <td><a href="{pos.url}" target="_blank">{pos.url[:60]}...</a></td>
                    <td>{pos.search_volume:,}</td>
                </tr>
                """
            
            html += "</table>"
        
        if unranked:
            html += f"""
            <h2>❌ Mots-clés non classés ({len(unranked)})</h2>
            <table>
                <tr>
                    <th>Mot-clé</th>
                    <th>Volume de recherche</th>
                    <th>CPC</th>
                </tr>
            """
            
            for pos in unranked[:20]:  # Limiter à 20 pour éviter des emails trop longs
                html += f"""
                <tr>
                    <td>{pos.keyword}</td>
                    <td>{pos.search_volume:,}</td>
                    <td>{pos.cpc:.2f}€</td>
                </tr>
                """
            
            html += "</table>"
            
            if len(unranked) > 20:
                html += f"<p><em>... et {len(unranked) - 20} autres mots-clés non classés</em></p>"
        
        html += """
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
        msg['Subject'] = f"Rapport SEO {self.config['tracking']['domain']} - {datetime.now().strftime('%d/%m/%Y')}"
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
            # Suivi des positions
            positions = self.track_keywords()
            
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
                error_msg['Subject'] = f"❌ Erreur suivi SEO {self.config['tracking']['domain']}"
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
            original_keywords = tracker.config['tracking']['keywords']
            tracker.config['tracking']['keywords'] = original_keywords[:3]
        
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