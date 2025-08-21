#!/usr/bin/env python3
"""
Script d'analyse Google Search Console
Récupère les top 500 URLs en hausse et en baisse avec filtres personnalisés
"""

import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import argparse

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class URLData:
    url: str
    clicks_current: int
    impressions_current: int
    ctr_current: float
    position_current: float
    clicks_previous: int
    impressions_previous: int
    ctr_previous: float
    position_previous: float
    
    @property
    def clicks_variation(self) -> float:
        if self.clicks_previous == 0:
            return float('inf') if self.clicks_current > 0 else 0
        return ((self.clicks_current - self.clicks_previous) / self.clicks_previous) * 100
    
    @property
    def impressions_variation(self) -> float:
        if self.impressions_previous == 0:
            return float('inf') if self.impressions_current > 0 else 0
        return ((self.impressions_current - self.impressions_previous) / self.impressions_previous) * 100


class GSCAnalyzer:
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
    
    def __init__(self, site_url: str, credentials_file: str = 'service-account.json'):
        self.site_url = site_url
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authentification avec Google Search Console API (Service Account ou OAuth)"""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Fichier {self.credentials_file} introuvable. "
                "Créez un Service Account dans Google Cloud Console et téléchargez la clé JSON."
            )
        
        # Déterminer le type de credentials en lisant le fichier
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            # Si c'est un Service Account
            if creds_data.get('type') == 'service_account':
                creds = ServiceAccountCredentials.from_service_account_file(
                    self.credentials_file, scopes=self.SCOPES)
                print(f"✅ Authentification Service Account: {creds_data.get('client_email')}")
            
            # Si c'est un OAuth client (fallback pour compatibilité)
            else:
                creds = None
                token_file = 'token.json'
                
                if os.path.exists(token_file):
                    creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
                
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())
                
                print("✅ Authentification OAuth réussie")
        
        except json.JSONDecodeError:
            raise ValueError(f"Le fichier {self.credentials_file} n'est pas un JSON valide.")
        except KeyError as e:
            raise ValueError(f"Clé manquante dans le fichier credentials: {e}")
        
        self.service = build('searchconsole', 'v1', credentials=creds)
    
    def get_search_analytics_data(self, start_date: str, end_date: str, row_limit: int = 25000) -> List[Dict]:
        """Récupère les données d'analyse de recherche pour une période donnée"""
        try:
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['page'],
                'rowLimit': row_limit,
                'startRow': 0
            }
            
            response = self.service.searchanalytics().query(
                siteUrl=self.site_url, body=request).execute()
            
            return response.get('rows', [])
        
        except HttpError as error:
            print(f"Erreur API GSC: {error}")
            return []
    
    def calculate_date_ranges(self, days: int = 7) -> Tuple[str, str, str, str]:
        """Calcule les plages de dates pour la comparaison"""
        today = datetime.now()
        
        current_end = today - timedelta(days=1)  # Hier
        current_start = current_end - timedelta(days=days-1)
        
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days-1)
        
        return (
            current_start.strftime('%Y-%m-%d'),
            current_end.strftime('%Y-%m-%d'),
            previous_start.strftime('%Y-%m-%d'),
            previous_end.strftime('%Y-%m-%d')
        )
    
    def merge_data_periods(self, current_data: List[Dict], previous_data: List[Dict]) -> List[URLData]:
        """Fusionne les données des deux périodes"""
        previous_dict = {row['keys'][0]: row for row in previous_data}
        merged_data = []
        
        for current_row in current_data:
            url = current_row['keys'][0]
            previous_row = previous_dict.get(url, {})
            
            url_data = URLData(
                url=url,
                clicks_current=current_row.get('clicks', 0),
                impressions_current=current_row.get('impressions', 0),
                ctr_current=current_row.get('ctr', 0) * 100,
                position_current=current_row.get('position', 0),
                clicks_previous=previous_row.get('clicks', 0),
                impressions_previous=previous_row.get('impressions', 0),
                ctr_previous=previous_row.get('ctr', 0) * 100,
                position_previous=previous_row.get('position', 0)
            )
            merged_data.append(url_data)
        
        # Ajouter les URLs qui n'existent que dans la période précédente
        for url, previous_row in previous_dict.items():
            if not any(data.url == url for data in merged_data):
                url_data = URLData(
                    url=url,
                    clicks_current=0,
                    impressions_current=0,
                    ctr_current=0,
                    position_current=0,
                    clicks_previous=previous_row.get('clicks', 0),
                    impressions_previous=previous_row.get('impressions', 0),
                    ctr_previous=previous_row.get('ctr', 0) * 100,
                    position_previous=previous_row.get('position', 0)
                )
                merged_data.append(url_data)
        
        return merged_data
    
    def filter_rising_urls(self, data: List[URLData], exclude_new: bool = True) -> List[URLData]:
        """Filtre les URLs en hausse"""
        filtered = []
        for url_data in data:
            if url_data.clicks_variation > 0:
                if exclude_new and url_data.clicks_previous == 0:
                    continue  # Exclure les nouveaux contenus
                filtered.append(url_data)
        
        return sorted(filtered, key=lambda x: x.clicks_variation, reverse=True)
    
    def filter_falling_urls(self, data: List[URLData], exclude_redirected: bool = True) -> List[URLData]:
        """Filtre les URLs en baisse"""
        filtered = []
        for url_data in data:
            if url_data.clicks_variation < 0:
                if exclude_redirected and url_data.clicks_current == 0:
                    continue  # Exclure les contenus redirigés
                filtered.append(url_data)
        
        return sorted(filtered, key=lambda x: x.clicks_variation)
    
    def export_to_csv(self, rising_urls: List[URLData], falling_urls: List[URLData], 
                     filename_prefix: str = "gsc_analysis"):
        """Exporte les résultats en CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export URLs en hausse
        rising_filename = f"{filename_prefix}_rising_{timestamp}.csv"
        with open(rising_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'clicks_current', 'clicks_previous', 'clicks_variation_%',
                         'impressions_current', 'impressions_previous', 'impressions_variation_%',
                         'ctr_current_%', 'ctr_previous_%', 'position_current', 'position_previous']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for url_data in rising_urls:
                writer.writerow({
                    'url': url_data.url,
                    'clicks_current': url_data.clicks_current,
                    'clicks_previous': url_data.clicks_previous,
                    'clicks_variation_%': round(url_data.clicks_variation, 2),
                    'impressions_current': url_data.impressions_current,
                    'impressions_previous': url_data.impressions_previous,
                    'impressions_variation_%': round(url_data.impressions_variation, 2),
                    'ctr_current_%': round(url_data.ctr_current, 2),
                    'ctr_previous_%': round(url_data.ctr_previous, 2),
                    'position_current': round(url_data.position_current, 1),
                    'position_previous': round(url_data.position_previous, 1)
                })
        
        # Export URLs en baisse
        falling_filename = f"{filename_prefix}_falling_{timestamp}.csv"
        with open(falling_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for url_data in falling_urls:
                writer.writerow({
                    'url': url_data.url,
                    'clicks_current': url_data.clicks_current,
                    'clicks_previous': url_data.clicks_previous,
                    'clicks_variation_%': round(url_data.clicks_variation, 2),
                    'impressions_current': url_data.impressions_current,
                    'impressions_previous': url_data.impressions_previous,
                    'impressions_variation_%': round(url_data.impressions_variation, 2),
                    'ctr_current_%': round(url_data.ctr_current, 2),
                    'ctr_previous_%': round(url_data.ctr_previous, 2),
                    'position_current': round(url_data.position_current, 1),
                    'position_previous': round(url_data.position_previous, 1)
                })
        
        return rising_filename, falling_filename
    
    def analyze(self, days: int = 7, top_limit: int = 500) -> Dict:
        """Lance l'analyse complète"""
        print(f"Analyse GSC pour {self.site_url}")
        print(f"Période: {days} jours")
        print("-" * 50)
        
        # Calcul des plages de dates
        current_start, current_end, previous_start, previous_end = self.calculate_date_ranges(days)
        print(f"Période actuelle: {current_start} à {current_end}")
        print(f"Période précédente: {previous_start} à {previous_end}")
        
        # Récupération des données
        print("\nRécupération des données...")
        current_data = self.get_search_analytics_data(current_start, current_end)
        previous_data = self.get_search_analytics_data(previous_start, previous_end)
        
        if not current_data and not previous_data:
            print("Aucune donnée trouvée pour les périodes spécifiées.")
            return {}
        
        # Fusion des données
        print("Fusion et calcul des variations...")
        merged_data = self.merge_data_periods(current_data, previous_data)
        
        # Filtrage
        print("Application des filtres...")
        rising_urls = self.filter_rising_urls(merged_data, exclude_new=True)[:top_limit]
        falling_urls = self.filter_falling_urls(merged_data, exclude_redirected=True)[:top_limit]
        
        # Export
        print("Export des résultats...")
        rising_file, falling_file = self.export_to_csv(rising_urls, falling_urls)
        
        # Résumé
        print("\n" + "="*50)
        print("RÉSULTATS DE L'ANALYSE")
        print("="*50)
        print(f"URLs en hausse (top {len(rising_urls)}): {rising_file}")
        print(f"URLs en baisse (top {len(falling_urls)}): {falling_file}")
        
        if rising_urls:
            print(f"\nTop 5 hausses:")
            for i, url in enumerate(rising_urls[:5], 1):
                print(f"{i}. {url.url}")
                print(f"   Clicks: {url.clicks_previous} → {url.clicks_current} ({url.clicks_variation:+.1f}%)")
        
        if falling_urls:
            print(f"\nTop 5 baisses:")
            for i, url in enumerate(falling_urls[:5], 1):
                print(f"{i}. {url.url}")
                print(f"   Clicks: {url.clicks_previous} → {url.clicks_current} ({url.clicks_variation:+.1f}%)")
        
        return {
            'rising_urls': rising_urls,
            'falling_urls': falling_urls,
            'rising_file': rising_file,
            'falling_file': falling_file
        }


def main():
    parser = argparse.ArgumentParser(description='Analyseur GSC - URLs en hausse/baisse')
    parser.add_argument('--site', default='https://www.legrand.fr', 
                       help='URL du site à analyser')
    parser.add_argument('--days', type=int, default=7,
                       help='Nombre de jours pour la comparaison')
    parser.add_argument('--top', type=int, default=500,
                       help='Nombre d\'URLs à extraire (top N)')
    parser.add_argument('--credentials', default='service-account.json',
                       help='Fichier de credentials Google (Service Account JSON)')
    
    args = parser.parse_args()
    
    try:
        analyzer = GSCAnalyzer(args.site, args.credentials)
        results = analyzer.analyze(days=args.days, top_limit=args.top)
        
        if results:
            print(f"\n✅ Analyse terminée avec succès!")
            print(f"📊 Fichiers générés: {results.get('rising_file')} et {results.get('falling_file')}")
        
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        print("\nPour configurer l'authentification:")
        print("1. Allez sur Google Cloud Console")
        print("2. Créez un projet et activez l'API Search Console") 
        print("3. Créez un Service Account")
        print("4. Téléchargez la clé JSON et renommez-la 'service-account.json'")
        print("5. Ajoutez l'email du Service Account dans Google Search Console")
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


if __name__ == "__main__":
    main()