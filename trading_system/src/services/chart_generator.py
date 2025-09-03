import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import logging
import os
import base64
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

logger = logging.getLogger(__name__)

class TrendChartGenerator:
    """Générateur de graphiques de tendance basé sur les vraies données Yahoo Finance"""
    
    def __init__(self, chart_dir: str = "charts"):
        self.chart_dir = chart_dir
        self.ensure_chart_directory()
        
        # Style des graphiques
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def ensure_chart_directory(self):
        """Crée le répertoire des graphiques s'il n'existe pas"""
        if not os.path.exists(self.chart_dir):
            os.makedirs(self.chart_dir)
    
    def generate_trend_chart(self, ticker: str, periods: List[str] = ['3mo', '6mo', '1y']) -> Dict[str, str]:
        """
        Génère des graphiques de tendance pour différentes périodes
        Retourne les chemins des fichiers générés
        """
        try:
            stock = yf.Ticker(ticker.upper())
            charts_generated = {}
            
            for period in periods:
                try:
                    # Récupérer les données historiques
                    hist = stock.history(period=period)
                    
                    if hist.empty:
                        logger.warning(f"Aucune donnée historique pour {ticker} période {period}")
                        continue
                    
                    # Générer le graphique
                    chart_path = self._create_price_chart(ticker, hist, period)
                    if chart_path:
                        charts_generated[period] = chart_path
                        
                except Exception as e:
                    logger.error(f"Erreur génération graphique {ticker} {period}: {e}")
                    continue
            
            return charts_generated
            
        except Exception as e:
            logger.error(f"Erreur génération graphiques tendance {ticker}: {e}")
            return {}
    
    def _create_price_chart(self, ticker: str, data: pd.DataFrame, period: str) -> Optional[str]:
        """Crée un graphique de prix avec indicateurs techniques"""
        try:
            # Configuration du graphique
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])
            fig.suptitle(f'{ticker} - Analyse de Tendance ({period})', fontsize=16, fontweight='bold')
            
            # Graphique principal - Prix et moyennes mobiles
            dates = data.index
            close_prices = data['Close']
            
            # Prix de clôture
            ax1.plot(dates, close_prices, linewidth=2.5, label='Prix de clôture', color='#1f77b4')
            
            # Moyennes mobiles (vraies données)
            if len(close_prices) >= 20:
                ma20 = close_prices.rolling(window=20).mean()
                ax1.plot(dates, ma20, linewidth=2, label='MA20', color='orange', alpha=0.8)
                
            if len(close_prices) >= 50:
                ma50 = close_prices.rolling(window=50).mean()
                ax1.plot(dates, ma50, linewidth=2, label='MA50', color='red', alpha=0.8)
            
            # Support et résistance (vraies données)
            recent_high = data['High'].rolling(window=20).max()
            recent_low = data['Low'].rolling(window=20).min()
            
            ax1.fill_between(dates, recent_low, recent_high, alpha=0.1, color='gray', label='Support/Résistance')
            
            # Volume
            ax2.bar(dates, data['Volume'], alpha=0.6, color='steelblue', label='Volume')
            
            # Formatage
            ax1.set_ylabel('Prix ($)', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.set_xlabel('Date', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Format des dates
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Annotations de tendance
            self._add_trend_annotations(ax1, dates, close_prices)
            
            # Sauvegarder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{ticker}_{period}_trend_{timestamp}.png"
            filepath = os.path.join(self.chart_dir, filename)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Graphique généré: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erreur création graphique prix {ticker}: {e}")
            plt.close()
            return None
    
    def _add_trend_annotations(self, ax, dates, prices):
        """Ajoute des annotations de tendance basées sur les vraies données"""
        try:
            if len(prices) < 10:
                return
            
            # Calcul de la tendance récente (10 derniers points)
            recent_prices = prices.tail(10)
            x_vals = np.arange(len(recent_prices))
            
            # Régression linéaire pour la tendance
            slope = np.polyfit(x_vals, recent_prices.values, 1)[0]
            
            # Annotation de tendance
            trend_text = "📈 HAUSSIÈRE" if slope > 0 else "📉 BAISSIÈRE"
            trend_color = 'green' if slope > 0 else 'red'
            
            ax.text(0.02, 0.98, trend_text, transform=ax.transAxes, 
                   fontsize=12, fontweight='bold', color=trend_color,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            
            # Performance période
            start_price = prices.iloc[0]
            end_price = prices.iloc[-1]
            perf = ((end_price - start_price) / start_price) * 100
            
            perf_text = f"Performance: {perf:+.1f}%"
            perf_color = 'green' if perf > 0 else 'red'
            
            ax.text(0.02, 0.92, perf_text, transform=ax.transAxes,
                   fontsize=11, color=perf_color,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            
        except Exception as e:
            logger.error(f"Erreur annotations tendance: {e}")
    
    def generate_interactive_chart(self, ticker: str, period: str = '6mo') -> Optional[str]:
        """Génère un graphique interactif Plotly avec vraies données"""
        try:
            stock = yf.Ticker(ticker.upper())
            data = stock.history(period=period)
            
            if data.empty:
                return None
            
            # Créer le graphique interactif
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=(f'{ticker} - Prix et Indicateurs', 'Volume'),
                row_width=[0.7, 0.3]
            )
            
            # Graphique en chandelier (vraies données OHLC)
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Prix OHLC'
                ),
                row=1, col=1
            )
            
            # Moyennes mobiles
            if len(data) >= 20:
                ma20 = data['Close'].rolling(window=20).mean()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=ma20,
                        mode='lines',
                        name='MA20',
                        line=dict(color='orange')
                    ),
                    row=1, col=1
                )
            
            # Volume
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color='steelblue'
                ),
                row=2, col=1
            )
            
            # Mise en forme
            fig.update_layout(
                title=f'{ticker} - Analyse Technique Interactive ({period})',
                xaxis_rangeslider_visible=False,
                height=600,
                template='plotly_white'
            )
            
            # Sauvegarder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{ticker}_{period}_interactive_{timestamp}.html"
            filepath = os.path.join(self.chart_dir, filename)
            
            fig.write_html(filepath)
            
            logger.info(f"Graphique interactif généré: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erreur graphique interactif {ticker}: {e}")
            return None
    
    def generate_prediction_chart(self, ticker: str, current_price: float, 
                                predictions: Dict, period: str = '1y') -> Optional[str]:
        """Génère un graphique de prédictions basé sur les vraies données historiques"""
        try:
            stock = yf.Ticker(ticker.upper())
            historical_data = stock.history(period=period)
            
            if historical_data.empty:
                return None
            
            # Configuration
            fig, ax = plt.subplots(figsize=(14, 8))
            fig.suptitle(f'{ticker} - Prédictions vs Historique Réel', fontsize=16, fontweight='bold')
            
            # Données historiques réelles
            dates = historical_data.index
            prices = historical_data['Close']
            
            ax.plot(dates, prices, linewidth=2, label='Prix historique réel', color='blue', alpha=0.8)
            
            # Point actuel
            current_date = datetime.now()
            ax.scatter([current_date], [current_price], s=100, color='red', 
                      label=f'Prix actuel: ${current_price:.2f}', zorder=5)
            
            # Prédictions futures
            pred_6m = predictions.get('predictions', {}).get('6_months', {})
            pred_1y = predictions.get('predictions', {}).get('1_year', {})
            
            if pred_6m:
                future_date_6m = current_date + timedelta(days=180)
                target_6m = pred_6m.get('target_price', current_price)
                prob_6m = pred_6m.get('probability_up', 50)
                prob_down_6m = pred_6m.get('probability_down', 100 - prob_6m)
                
                ax.scatter([future_date_6m], [target_6m], s=120, color='orange', 
                          label=f'Cible 6M: ${target_6m:.2f} (↗{prob_6m}% ↘{prob_down_6m}%)', zorder=5)
                
                # Ligne de prédiction
                ax.plot([current_date, future_date_6m], [current_price, target_6m], 
                       linestyle='--', color='orange', alpha=0.7, linewidth=2)
            
            if pred_1y:
                future_date_1y = current_date + timedelta(days=365)
                target_1y = pred_1y.get('target_price', current_price)
                prob_1y = pred_1y.get('probability_up', 50)
                prob_down_1y = pred_1y.get('probability_down', 100 - prob_1y)
                
                ax.scatter([future_date_1y], [target_1y], s=120, color='green', 
                          label=f'Cible 1Y: ${target_1y:.2f} (↗{prob_1y}% ↘{prob_down_1y}%)', zorder=5)
                
                # Ligne de prédiction
                ax.plot([current_date, future_date_1y], [current_price, target_1y], 
                       linestyle='--', color='green', alpha=0.7, linewidth=2)
            
            # Zone de confiance (basée sur la volatilité historique réelle)
            volatility = prices.pct_change().std() * np.sqrt(252)  # Volatilité annualisée
            
            if pred_6m and pred_1y:
                future_dates = pd.date_range(current_date, future_date_1y, freq='D')
                days_from_now = np.array([(d - current_date).days for d in future_dates])
                
                # Modèle simple d'évolution avec volatilité
                expected_prices = current_price * (1 + (target_1y/current_price - 1) * days_from_now / 365)
                confidence_upper = expected_prices * (1 + volatility * np.sqrt(days_from_now / 365))
                confidence_lower = expected_prices * (1 - volatility * np.sqrt(days_from_now / 365))
                
                ax.fill_between(future_dates, confidence_lower, confidence_upper, 
                               alpha=0.2, color='gray', label='Zone de confiance (basée sur volatilité réelle)')
            
            # Formatage
            ax.set_ylabel('Prix ($)', fontsize=12)
            ax.set_xlabel('Date', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # Format des dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Sauvegarder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{ticker}_predictions_{timestamp}.png"
            filepath = os.path.join(self.chart_dir, filename)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Graphique prédictions généré: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erreur graphique prédictions {ticker}: {e}")
            plt.close()
            return None
    
    def generate_comparison_chart(self, tickers: List[str], period: str = '6mo') -> Optional[str]:
        """Compare plusieurs tickers sur le même graphique (vraies données)"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            fig.suptitle(f'Comparaison de Performance - {period}', fontsize=16, fontweight='bold')
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(tickers)))
            
            for i, ticker in enumerate(tickers):
                try:
                    stock = yf.Ticker(ticker.upper())
                    data = stock.history(period=period)
                    
                    if data.empty:
                        continue
                    
                    # Normaliser les prix (performance relative)
                    normalized_prices = (data['Close'] / data['Close'].iloc[0] - 1) * 100
                    
                    ax.plot(data.index, normalized_prices, linewidth=2, 
                           label=f'{ticker} ({normalized_prices.iloc[-1]:+.1f}%)', 
                           color=colors[i])
                    
                except Exception as e:
                    logger.error(f"Erreur comparaison {ticker}: {e}")
                    continue
            
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.set_ylabel('Performance (%)', fontsize=12)
            ax.set_xlabel('Date', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # Format des dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Sauvegarder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comparison_{period}_{timestamp}.png"
            filepath = os.path.join(self.chart_dir, filename)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Graphique comparaison généré: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erreur graphique comparaison: {e}")
            plt.close()
            return None
    
    def get_chart_base64(self, filepath: str) -> Optional[str]:
        """Convertit un graphique en base64 pour l'intégration dans des emails"""
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                return img_base64
                
        except Exception as e:
            logger.error(f"Erreur conversion base64: {e}")
            return None
    
    def cleanup_old_charts(self, days_old: int = 7):
        """Nettoie les anciens graphiques"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for filename in os.listdir(self.chart_dir):
                filepath = os.path.join(self.chart_dir, filename)
                if os.path.isfile(filepath):
                    file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_modified < cutoff_date:
                        os.remove(filepath)
                        logger.info(f"Ancien graphique supprimé: {filepath}")
                        
        except Exception as e:
            logger.error(f"Erreur nettoyage graphiques: {e}")