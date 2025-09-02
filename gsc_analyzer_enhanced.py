#!/usr/bin/env python3
"""
Analyseur Google Search Console Amélioré
Génère un rapport hebdomadaire automatisé avec analyse intelligente et alertes
"""

import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import argparse
import statistics
from collections import defaultdict
import re

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class URLAnalysis:
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
    
    @property
    def ctr_variation(self) -> float:
        if self.ctr_previous == 0:
            return float('inf') if self.ctr_current > 0 else 0
        return ((self.ctr_current - self.ctr_previous) / self.ctr_previous) * 100
    
    @property
    def position_variation(self) -> float:
        if self.position_previous == 0:
            return 0
        return ((self.position_current - self.position_previous) / self.position_previous) * 100

    @property
    def category(self) -> str:
        """Catégorise l'URL selon son chemin"""
        if '/pro/' in self.url:
            return 'Professional'
        elif '/maison-connectee/' in self.url:
            return 'Smart Home'
        elif '/catalogue/' in self.url:
            return 'Catalog'
        elif '/actualites/' in self.url:
            return 'News'
        elif '/mon-projet/' in self.url:
            return 'Projects'
        elif '/outils/' in self.url:
            return 'Tools'
        elif '/questions-frequentes/' in self.url:
            return 'FAQ'
        else:
            return 'Other'

    def get_product_type(self) -> str:
        """Identifie le type de produit depuis l'URL"""
        product_types = {
            'interrupteur': 'Switches',
            'prise': 'Outlets',
            'detecteur': 'Detectors',
            'disjoncteur': 'Circuit Breakers',
            'compteur': 'Meters',
            'programmateur': 'Timers',
            'transformateur': 'Transformers',
            'coffret': 'Boxes',
            'borne': 'Terminals',
            'bloc': 'Blocks',
            'kit': 'Kits',
            'visiophone': 'Video Intercoms',
            'volets-roulants': 'Shutters'
        }
        
        url_lower = self.url.lower()
        for keyword, product_type in product_types.items():
            if keyword in url_lower:
                return product_type
        return 'Other'


@dataclass 
class Alert:
    type: str
    severity: str  # 'HIGH', 'MEDIUM', 'LOW'
    message: str
    url: Optional[str] = None
    metric_value: Optional[float] = None


@dataclass
class WeeklyReport:
    period: str
    summary: Dict
    top_rises: List[URLAnalysis]
    top_falls: List[URLAnalysis]
    alerts: List[Alert]
    category_analysis: Dict
    seasonal_insights: List[str]


class EnhancedGSCAnalyzer:
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
    
    def __init__(self, site_url: str, credentials_file: str = 'service-account.json'):
        self.site_url = site_url
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authentification avec Service Account"""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"Fichier {self.credentials_file} introuvable.")
        
        creds = ServiceAccountCredentials.from_service_account_file(
            self.credentials_file, scopes=self.SCOPES)
        
        with open(self.credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        print(f"✅ Authentification: {creds_data.get('client_email')}")
        self.service = build('searchconsole', 'v1', credentials=creds)
    
    def get_search_analytics_data(self, start_date: str, end_date: str, row_limit: int = 25000) -> List[Dict]:
        """Récupère les données d'analyse de recherche"""
        try:
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['page'],
                'rowLimit': row_limit,
                'startRow': 0,
                'dataState': 'final'  # Assure données finales
            }
            
            print(f"📅 Requête GSC: {start_date} à {end_date} (limit: {row_limit})")
            
            response = self.service.searchanalytics().query(
                siteUrl=self.site_url, body=request).execute()
            
            rows = response.get('rows', [])
            print(f"📊 {len(rows)} URLs récupérées pour la période {start_date} à {end_date}")
            
            # Vérification des premières entrées pour debug
            if rows:
                top_url = rows[0]
                print(f"🔍 Top URL: {top_url['keys'][0]}")
                print(f"   Clics: {top_url.get('clicks', 0)}, Impressions: {top_url.get('impressions', 0)}")
            
            return rows
        
        except HttpError as error:
            print(f"❌ Erreur API GSC: {error}")
            return []
    
    def calculate_date_ranges(self, days: int = 7) -> Tuple[str, str, str, str]:
        """Calcule les plages de dates pour la comparaison"""
        # Périodes exactes pour correspondre à GSC
        current_start = '2025-08-20'
        current_end = '2025-08-26'
        previous_start = '2025-08-13'
        previous_end = '2025-08-19'
        
        return (
            current_start,
            current_end,
            previous_start,
            previous_end
        )
    
    def merge_data_periods(self, current_data: List[Dict], previous_data: List[Dict]) -> List[URLAnalysis]:
        """Fusionne les données des deux périodes"""
        previous_dict = {row['keys'][0]: row for row in previous_data}
        merged_data = []
        
        for current_row in current_data:
            url = current_row['keys'][0]
            previous_row = previous_dict.get(url, {})
            
            url_analysis = URLAnalysis(
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
            merged_data.append(url_analysis)
        
        # Ajouter les URLs qui n'existent que dans la période précédente
        for url, previous_row in previous_dict.items():
            if not any(data.url == url for data in merged_data):
                url_analysis = URLAnalysis(
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
                merged_data.append(url_analysis)
        
        return merged_data
    
    def detect_anomalies(self, top_rises: List[URLAnalysis], top_falls: List[URLAnalysis]) -> List[Alert]:
        """Détecte les anomalies uniquement sur les TOP 25 hausses et baisses"""
        alerts = []
        
        # Seuils d'anomalies
        HIGH_DROP_THRESHOLD = -80  # Baisse de 80%+ = alerte HIGH
        HIGH_RISE_THRESHOLD = 500   # Hausse de 500%+ = alerte HIGH
        CTR_DROP_THRESHOLD = -50    # Baisse CTR de 50%+ = alerte MEDIUM
        POSITION_DROP_THRESHOLD = 50  # Baisse position de 50+ rangs = alerte MEDIUM
        
        # Analyse des TOP 25 baisses
        for url_data in top_falls:
            # Alertes sur les chutes de clics importantes
            if url_data.clicks_variation < HIGH_DROP_THRESHOLD and url_data.clicks_previous >= 10:
                alerts.append(Alert(
                    type='TRAFFIC_DROP',
                    severity='HIGH',
                    message=f"Chute massive de trafic: {url_data.clicks_variation:.1f}%",
                    url=url_data.url,
                    metric_value=url_data.clicks_variation
                ))
            
            # Alertes CTR sur les baisses
            if url_data.ctr_variation < CTR_DROP_THRESHOLD and url_data.impressions_current >= 100:
                alerts.append(Alert(
                    type='CTR_DROP',
                    severity='MEDIUM',
                    message=f"Chute importante du CTR: {url_data.ctr_variation:.1f}%",
                    url=url_data.url,
                    metric_value=url_data.ctr_variation
                ))
            
            # Alertes position sur les baisses
            position_drop = url_data.position_current - url_data.position_previous
            if position_drop > POSITION_DROP_THRESHOLD and url_data.position_previous > 0:
                alerts.append(Alert(
                    type='RANKING_DROP',
                    severity='MEDIUM',
                    message=f"Chute de positionnement: +{position_drop:.1f} rangs",
                    url=url_data.url,
                    metric_value=position_drop
                ))
        
        # Analyse des TOP 25 hausses
        for url_data in top_rises:
            # Alertes sur les hausses anormales
            if url_data.clicks_variation > HIGH_RISE_THRESHOLD and url_data.clicks_current >= 20:
                alerts.append(Alert(
                    type='TRAFFIC_SPIKE',
                    severity='MEDIUM',
                    message=f"Pic de trafic inhabituel: +{url_data.clicks_variation:.1f}%",
                    url=url_data.url,
                    metric_value=url_data.clicks_variation
                ))
        
        return sorted(alerts, key=lambda x: (x.severity, abs(x.metric_value or 0)), reverse=True)
    
    def analyze_by_category(self, data: List[URLAnalysis]) -> Dict:
        """Analyse les performances par catégorie"""
        category_stats = defaultdict(lambda: {
            'urls': [],
            'total_clicks_current': 0,
            'total_clicks_previous': 0,
            'total_impressions_current': 0,
            'total_impressions_previous': 0
        })
        
        for url_data in data:
            category = url_data.category
            category_stats[category]['urls'].append(url_data)
            category_stats[category]['total_clicks_current'] += url_data.clicks_current
            category_stats[category]['total_clicks_previous'] += url_data.clicks_previous
            category_stats[category]['total_impressions_current'] += url_data.impressions_current
            category_stats[category]['total_impressions_previous'] += url_data.impressions_previous
        
        # Calcul des variations par catégorie
        category_analysis = {}
        for category, stats in category_stats.items():
            clicks_variation = 0
            impressions_variation = 0
            
            if stats['total_clicks_previous'] > 0:
                clicks_variation = ((stats['total_clicks_current'] - stats['total_clicks_previous']) / 
                                  stats['total_clicks_previous']) * 100
            
            if stats['total_impressions_previous'] > 0:
                impressions_variation = ((stats['total_impressions_current'] - stats['total_impressions_previous']) / 
                                       stats['total_impressions_previous']) * 100
            
            category_analysis[category] = {
                'url_count': len(stats['urls']),
                'clicks_variation': clicks_variation,
                'impressions_variation': impressions_variation,
                'performance': 'POSITIVE' if clicks_variation > 0 else 'NEGATIVE' if clicks_variation < -10 else 'STABLE'
            }
        
        return category_analysis
    
    def get_seasonal_insights(self, current_start: str, current_end: str) -> List[str]:
        """Analyse la saisonnalité"""
        insights = []
        current_month = datetime.strptime(current_start, '%Y-%m-%d').month
        
        seasonal_patterns = {
            (12, 1, 2): "Période hivernale - Forte demande pour le chauffage et l'éclairage",
            (6, 7, 8): "Période estivale - Hausse attendue pour les volets roulants et climatisation", 
            (3, 4, 5): "Période printemps - Pic de projets de rénovation",
            (9, 10, 11): "Rentrée - Augmentation des projets maison et bureau"
        }
        
        for months, pattern in seasonal_patterns.items():
            if current_month in months:
                insights.append(pattern)
        
        # Analyse jour de la semaine
        start_date = datetime.strptime(current_start, '%Y-%m-%d')
        if start_date.weekday() >= 5:  # Weekend
            insights.append("Période incluant le weekend - Trafic résidentiel généralement plus élevé")
        
        return insights
    
    def generate_weekly_report(self, days: int = 7) -> WeeklyReport:
        """Génère le rapport hebdomadaire complet"""
        print("🔍 Génération du rapport hebdomadaire...")
        
        # Récupération des données
        current_start, current_end, previous_start, previous_end = self.calculate_date_ranges(days)
        current_data = self.get_search_analytics_data(current_start, current_end)
        previous_data = self.get_search_analytics_data(previous_start, previous_end)
        
        if not current_data:
            raise ValueError("Aucune donnée trouvée pour la période actuelle")
        
        # Fusion et analyse
        merged_data = self.merge_data_periods(current_data, previous_data)
        
        # Tri par différence absolue de clics (pas pourcentage)
        rising_urls = sorted(
            [url for url in merged_data if (url.clicks_current - url.clicks_previous) > 0],
            key=lambda x: (x.clicks_current - x.clicks_previous), reverse=True
        )[:25]
        
        falling_urls = sorted(
            [url for url in merged_data if (url.clicks_current - url.clicks_previous) < 0],
            key=lambda x: (x.clicks_current - x.clicks_previous)  # Plus petite différence (plus négatif) en premier
        )[:25]
        
        # Détection d'anomalies uniquement sur les TOP 25
        alerts = self.detect_anomalies(rising_urls, falling_urls)
        
        # Analyse par catégorie uniquement sur les TOP 50 (25 + 25)
        top_50_urls = rising_urls + falling_urls
        category_analysis = self.analyze_by_category(top_50_urls)
        
        # Insights saisonniers
        seasonal_insights = self.get_seasonal_insights(current_start, current_end)
        
        # Les métriques sont maintenant calculées uniquement sur les TOP 50
        
        # Calcul des métriques uniquement sur les TOP 50
        top_50_clicks_current = sum(url.clicks_current for url in top_50_urls)
        top_50_clicks_previous = sum(url.clicks_previous for url in top_50_urls)
        top_50_impressions_current = sum(url.impressions_current for url in top_50_urls)
        top_50_impressions_previous = sum(url.impressions_previous for url in top_50_urls)
        
        summary = {
            'period': f"{current_start} à {current_end}",
            'current_start': current_start,
            'current_end': current_end,
            'previous_start': previous_start,
            'previous_end': previous_end,
            'total_clicks_variation': ((top_50_clicks_current - top_50_clicks_previous) / 
                                     top_50_clicks_previous * 100) if top_50_clicks_previous > 0 else 0,
            'total_impressions_variation': ((top_50_impressions_current - top_50_impressions_previous) / 
                                          top_50_impressions_previous * 100) if top_50_impressions_previous > 0 else 0,
            'urls_analyzed': 50,  # Seulement TOP 50
            'rising_urls_count': len(rising_urls),
            'falling_urls_count': len(falling_urls),
            'high_alerts': len([a for a in alerts if a.severity == 'HIGH']),
            'medium_alerts': len([a for a in alerts if a.severity == 'MEDIUM'])
        }
        
        return WeeklyReport(
            period=f"{current_start} à {current_end}",
            summary=summary,
            top_rises=rising_urls,
            top_falls=falling_urls,
            alerts=alerts[:10],  # Top 10 alertes
            category_analysis=category_analysis,
            seasonal_insights=seasonal_insights
        )
    
    def export_report_to_html(self, report: WeeklyReport, filename: str = None) -> str:
        """Exporte le rapport en HTML lisible"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gsc_weekly_report_{timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport GSC Hebdomadaire - {report.period}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #1976d2; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .alert-high {{ background: #ffebee; border-left: 5px solid #f44336; padding: 10px; margin: 5px 0; }}
        .alert-medium {{ background: #fff3e0; border-left: 5px solid #ff9800; padding: 10px; margin: 5px 0; }}
        .positive {{ color: #4caf50; font-weight: bold; }}
        .negative {{ color: #f44336; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; }}
        .url {{ font-size: 0.9em; max-width: 400px; word-break: break-all; }}
        .metric {{ text-align: center; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapport GSC Hebdomadaire</h1>
        <h2>Période: {report.period}</h2>
        <p>Site: {self.site_url}</p>
    </div>

    <div class="period-comparison">
        <h2>📅 Périodes Comparées</h2>
        <div style="display: flex; gap: 20px; margin: 10px 0;">
            <div style="flex: 1; background: #e3f2fd; padding: 15px; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #1976d2;">📆 Semaine Actuelle</h3>
                <p style="margin: 0; font-size: 1.1em; font-weight: bold;">{report.summary['current_start']} → {report.summary['current_end']}</p>
                <p style="margin: 5px 0 0 0; color: #666;">(7 jours)</p>
            </div>
            <div style="flex: 1; background: #f3e5f5; padding: 15px; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #7b1fa2;">📆 Semaine Précédente</h3>
                <p style="margin: 0; font-size: 1.1em; font-weight: bold;">{report.summary['previous_start']} → {report.summary['previous_end']}</p>
                <p style="margin: 5px 0 0 0; color: #666;">(7 jours)</p>
            </div>
        </div>
    </div>

    <div class="summary">
        <h2>📈 Résumé Exécutif</h2>
        <ul>
            <li><strong>URLs analysées (TOP 50):</strong> {report.summary['urls_analyzed']}</li>
            <li><strong>Variation totale clics:</strong> <span class="{'positive' if report.summary['total_clicks_variation'] > 0 else 'negative'}">{report.summary['total_clicks_variation']:+.1f}%</span></li>
            <li><strong>Variation totale impressions:</strong> <span class="{'positive' if report.summary['total_impressions_variation'] > 0 else 'negative'}">{report.summary['total_impressions_variation']:+.1f}%</span></li>
            <li><strong>URLs en hausse:</strong> {report.summary['rising_urls_count']}</li>
            <li><strong>URLs en baisse:</strong> {report.summary['falling_urls_count']}</li>
            <li><strong>Alertes critiques:</strong> {report.summary['high_alerts']} (HIGH) + {report.summary['medium_alerts']} (MEDIUM)</li>
        </ul>
    </div>

    <div class="alerts">
        <h2>🚨 Alertes Prioritaires</h2>
        """
        
        if not report.alerts:
            html_content += "<p>Aucune alerte détectée cette semaine.</p>"
        else:
            for alert in report.alerts:
                css_class = 'alert-high' if alert.severity == 'HIGH' else 'alert-medium'
                html_content += f"""
                <div class="{css_class}">
                    <strong>{alert.type} - {alert.severity}</strong><br>
                    {alert.message}<br>
                    {f'<small class="url">{alert.url}</small>' if alert.url else ''}
                </div>
                """
        
        html_content += """
    </div>

    <div class="top-rises">
        <h2>🚀 Top 25 Hausses</h2>
        <table>
            <tr>
                <th>URL</th>
                <th>Catégorie</th>
                <th>Clics<br>7 derniers jours</th>
                <th>Clics<br>7 jours précédents</th>
                <th>Clics<br>Différence</th>
                <th>Impressions<br>7 derniers jours</th>
                <th>Impressions<br>7 jours précédents</th>
                <th>Impressions<br>Différence</th>
                <th>Position</th>
            </tr>
        """
        
        for url_data in report.top_rises:
            clicks_diff = url_data.clicks_current - url_data.clicks_previous
            impressions_diff = url_data.impressions_current - url_data.impressions_previous
            html_content += f"""
            <tr>
                <td class="url">{url_data.url}</td>
                <td>{url_data.category}</td>
                <td class="metric">{url_data.clicks_current:,}</td>
                <td class="metric">{url_data.clicks_previous:,}</td>
                <td class="metric positive">+{clicks_diff:,}</td>
                <td class="metric">{url_data.impressions_current:,}</td>
                <td class="metric">{url_data.impressions_previous:,}</td>
                <td class="metric {'positive' if impressions_diff > 0 else 'negative'}">{impressions_diff:+,}</td>
                <td class="metric">{url_data.position_current:.1f}</td>
            </tr>
            """
        
        html_content += """
        </table>
    </div>

    <div class="top-falls">
        <h2>📉 Top 25 Baisses</h2>
        <table>
            <tr>
                <th>URL</th>
                <th>Catégorie</th>
                <th>Clics<br>7 derniers jours</th>
                <th>Clics<br>7 jours précédents</th>
                <th>Clics<br>Différence</th>
                <th>Impressions<br>7 derniers jours</th>
                <th>Impressions<br>7 jours précédents</th>
                <th>Impressions<br>Différence</th>
                <th>Position</th>
            </tr>
        """
        
        for url_data in report.top_falls:
            clicks_diff = url_data.clicks_current - url_data.clicks_previous
            impressions_diff = url_data.impressions_current - url_data.impressions_previous
            html_content += f"""
            <tr>
                <td class="url">{url_data.url}</td>
                <td>{url_data.category}</td>
                <td class="metric">{url_data.clicks_current:,}</td>
                <td class="metric">{url_data.clicks_previous:,}</td>
                <td class="metric negative">{clicks_diff:,}</td>
                <td class="metric">{url_data.impressions_current:,}</td>
                <td class="metric">{url_data.impressions_previous:,}</td>
                <td class="metric {'positive' if impressions_diff > 0 else 'negative'}">{impressions_diff:+,}</td>
                <td class="metric">{url_data.position_current:.1f}</td>
            </tr>
            """
        
        html_content += """
        </table>
    </div>

    <div class="category-analysis">
        <h2>🏷️ Analyse par Catégorie</h2>
        <table>
            <tr>
                <th>Catégorie</th>
                <th>URLs</th>
                <th>Performance Clics</th>
                <th>Performance Impressions</th>
                <th>Statut</th>
            </tr>
        """
        
        for category, analysis in report.category_analysis.items():
            status_color = 'positive' if analysis['performance'] == 'POSITIVE' else 'negative' if analysis['performance'] == 'NEGATIVE' else ''
            html_content += f"""
            <tr>
                <td>{category}</td>
                <td class="metric">{analysis['url_count']}</td>
                <td class="metric {'positive' if analysis['clicks_variation'] > 0 else 'negative'}">{analysis['clicks_variation']:+.1f}%</td>
                <td class="metric {'positive' if analysis['impressions_variation'] > 0 else 'negative'}">{analysis['impressions_variation']:+.1f}%</td>
                <td class="metric {status_color}">{analysis['performance']}</td>
            </tr>
            """
        
        html_content += f"""
        </table>
    </div>

    <div class="pie-chart">
        <h2>📊 Répartition par Catégorie</h2>
        <div style="width: 100%; max-width: 600px; margin: 0 auto;">
            <canvas id="categoryChart" width="400" height="400"></canvas>
        </div>
    </div>

    <div class="seasonal-insights">
        <h2>🗓️ Insights Saisonniers</h2>
        <ul>
        """
        
        for insight in report.seasonal_insights:
            html_content += f"<li>{insight}</li>"
        
        html_content += f"""
        </ul>
    </div>

    <div class="footer">
        <p><small>Rapport généré le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')} | GSC Analyzer Enhanced</small></p>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Données du graphique en camembert
        const categoryData = {{
            labels: {list(report.category_analysis.keys())},
            datasets: [{{
                data: {[analysis['url_count'] for analysis in report.category_analysis.values()]},
                backgroundColor: [
                    '#1976d2',  // Professional
                    '#4caf50',  // Smart Home
                    '#ff9800',  // Catalog
                    '#f44336',  // News
                    '#9c27b0',  // Projects
                    '#00bcd4',  // Tools
                    '#795548',  // FAQ
                    '#607d8b'   // Other
                ].slice(0, {len(report.category_analysis)}),
                borderWidth: 2,
                borderColor: '#fff'
            }}]
        }};

        // Configuration du graphique
        const config = {{
            type: 'pie',
            data: categoryData,
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Distribution des URLs par Catégorie (TOP 50)',
                        font: {{
                            size: 16
                        }}
                    }},
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 20,
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' URLs (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }};

        // Création du graphique
        const ctx = document.getElementById('categoryChart').getContext('2d');
        new Chart(ctx, config);
    </script>
</body>
</html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename


def main():
    parser = argparse.ArgumentParser(description='Analyseur GSC Amélioré - Rapport Hebdomadaire')
    parser.add_argument('--site', default='https://www.legrand.fr', help='URL du site')
    parser.add_argument('--days', type=int, default=7, help='Période d\'analyse en jours')
    parser.add_argument('--credentials', default='service-account.json', help='Fichier credentials')
    parser.add_argument('--format', choices=['html', 'text'], default='html', help='Format du rapport')
    
    args = parser.parse_args()
    
    try:
        analyzer = EnhancedGSCAnalyzer(args.site, args.credentials)
        report = analyzer.generate_weekly_report(days=args.days)
        
        if args.format == 'html':
            filename = analyzer.export_report_to_html(report)
            print(f"\n✅ Rapport HTML généré: {filename}")
        else:
            # Format texte simple pour débogage
            print("\n" + "="*60)
            print(f"RAPPORT GSC - {report.period}")
            print("="*60)
            print(f"📊 {report.summary['urls_analyzed']:,} URLs analysées")
            print(f"📈 Clics: {report.summary['total_clicks_variation']:+.1f}%")
            print(f"👁️ Impressions: {report.summary['total_impressions_variation']:+.1f}%")
            print(f"🚨 {report.summary['high_alerts']} alertes critiques")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    main()