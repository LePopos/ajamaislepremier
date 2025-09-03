import yfinance as yf
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .chart_generator import TrendChartGenerator

logger = logging.getLogger(__name__)

class EnhancedAnalyzer:
    """Analyse hybride avancée combinant données Yahoo Finance et intelligence contextuelle"""
    
    def __init__(self):
        self.current_date = datetime.now()
        self.chart_generator = TrendChartGenerator()
        
    def get_comprehensive_analysis(self, ticker: str, current_price: float) -> Dict[str, Any]:
        """Analyse complète d'un ticker avec prédictions M+6 et Y+1"""
        try:
            # 1. Récupérer données enrichies Yahoo Finance
            financial_data = self._get_enhanced_yahoo_data(ticker)
            
            # 2. Analyse technique avancée
            technical_analysis = self._perform_technical_analysis(ticker, financial_data)
            
            # 3. Analyse fondamentale
            fundamental_analysis = self._analyze_fundamentals(ticker, financial_data)
            
            # 4. Contexte sectoriel et macro
            sector_context = self._get_sector_context(ticker, financial_data)
            
            # 5. Prédictions M+6 et Y+1
            predictions = self._generate_predictions(ticker, current_price, financial_data, technical_analysis)
            
            # 6. Recommandation d'allocation budgétaire
            budget_allocation = self._calculate_budget_allocation(
                ticker, current_price, technical_analysis, fundamental_analysis, 
                sector_context, predictions
            )
            
            # 7. Génération des graphiques de tendance
            charts = self._generate_trend_charts(ticker, current_price, predictions)
            
            # 8. Analyse contextuelle Claude
            claude_analysis = self._generate_claude_context_analysis(
                ticker, current_price, financial_data, technical_analysis, 
                fundamental_analysis, sector_context, predictions
            )
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'analysis_date': self.current_date.isoformat(),
                'financial_data': financial_data,
                'technical_analysis': technical_analysis,
                'fundamental_analysis': fundamental_analysis,
                'sector_context': sector_context,
                'predictions': predictions,
                'budget_allocation': budget_allocation,
                'claude_analysis': claude_analysis,
                'trend_charts': charts
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {ticker}: {e}")
            return self._fallback_analysis(ticker, current_price)
    
    def _get_enhanced_yahoo_data(self, ticker: str) -> Dict[str, Any]:
        """Récupère données enrichies Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker.upper())
            
            # Info de base
            info = stock.info
            
            # Historique 2 ans pour analyse
            hist_2y = stock.history(period='2y')
            hist_1y = stock.history(period='1y')
            hist_6m = stock.history(period='6mo')
            hist_3m = stock.history(period='3mo')
            
            # Données financières
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            # News récentes
            news = stock.news[:5] if hasattr(stock, 'news') and stock.news else []
            
            return {
                'info': info,
                'price_history': {
                    '2y': hist_2y.tail(10).to_dict('records') if not hist_2y.empty else [],
                    '1y': hist_1y.tail(10).to_dict('records') if not hist_1y.empty else [],
                    '6m': hist_6m.tail(10).to_dict('records') if not hist_6m.empty else [],
                    '3m': hist_3m.tail(10).to_dict('records') if not hist_3m.empty else []
                },
                'financial_statements': {
                    'income': financials.head(4).to_dict() if not financials.empty else {},
                    'balance': balance_sheet.head(4).to_dict() if not balance_sheet.empty else {},
                    'cashflow': cashflow.head(4).to_dict() if not cashflow.empty else {}
                },
                'recent_news': [
                    {
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'published': item.get('providerPublishTime', 0)
                    } for item in news
                ],
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced Yahoo data for {ticker}: {e}")
            return {}
    
    def _perform_technical_analysis(self, ticker: str, financial_data: Dict) -> Dict[str, Any]:
        """Analyse technique avancée"""
        try:
            hist_3m = financial_data.get('price_history', {}).get('3m', [])
            if not hist_3m:
                return {'error': 'No price history available'}
            
            prices = [item['Close'] for item in hist_3m if 'Close' in item]
            volumes = [item['Volume'] for item in hist_3m if 'Volume' in item]
            
            if len(prices) < 10:
                return {'error': 'Insufficient price data'}
            
            # Calculs techniques
            current_price = prices[-1]
            ma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
            ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices)
            
            # RSI simplifié
            gains = []
            losses = []
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
            avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs)) if rs > 0 else 50
            
            # Volatilité
            volatility = np.std(prices[-30:]) if len(prices) >= 30 else np.std(prices)
            
            # Support/Résistance
            recent_high = max(prices[-30:]) if len(prices) >= 30 else max(prices)
            recent_low = min(prices[-30:]) if len(prices) >= 30 else min(prices)
            
            # Tendance
            if len(prices) >= 20:
                trend_slope = (prices[-1] - prices[-20]) / 20
                trend = 'bullish' if trend_slope > 0 else 'bearish'
            else:
                trend = 'neutral'
            
            return {
                'current_price': current_price,
                'ma_20': round(ma_20, 2),
                'ma_50': round(ma_50, 2),
                'rsi': round(rsi, 2),
                'volatility': round(volatility, 2),
                'support_level': round(recent_low, 2),
                'resistance_level': round(recent_high, 2),
                'trend': trend,
                'price_vs_ma20': round(((current_price - ma_20) / ma_20) * 100, 2),
                'average_volume': int(np.mean(volumes)) if volumes else 0
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {ticker}: {e}")
            return {'error': str(e)}
    
    def _analyze_fundamentals(self, ticker: str, financial_data: Dict) -> Dict[str, Any]:
        """Analyse fondamentale"""
        try:
            info = financial_data.get('info', {})
            
            return {
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'profit_margin': info.get('profitMargins', 0),
                'roe': info.get('returnOnEquity', 0),
                'beta': info.get('beta', 1.0),
                'dividend_yield': info.get('dividendYield', 0),
                'analyst_recommendation': info.get('recommendationMean', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in fundamental analysis for {ticker}: {e}")
            return {}
    
    def _get_sector_context(self, ticker: str, financial_data: Dict) -> Dict[str, Any]:
        """Contexte sectoriel"""
        try:
            info = financial_data.get('info', {})
            
            return {
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'business_summary': info.get('longBusinessSummary', '')[:500] + '...' if info.get('longBusinessSummary') else '',
                'employees': info.get('fullTimeEmployees', 0),
                'country': info.get('country', 'Unknown'),
                'website': info.get('website', '')
            }
            
        except Exception as e:
            logger.error(f"Error getting sector context for {ticker}: {e}")
            return {}
    
    def _generate_predictions(self, ticker: str, current_price: float, 
                            financial_data: Dict, technical_analysis: Dict) -> Dict[str, Any]:
        """Générer prédictions M+6 et Y+1"""
        try:
            # Facteurs pour prédiction
            rsi = technical_analysis.get('rsi', 50)
            trend = technical_analysis.get('trend', 'neutral')
            volatility = technical_analysis.get('volatility', 0)
            pe_ratio = financial_data.get('info', {}).get('trailingPE', 20)
            revenue_growth = financial_data.get('info', {}).get('revenueGrowth', 0)
            
            # Modèle simplifié de prédiction
            base_growth_6m = 0.05  # 5% base growth 6 mois
            base_growth_1y = 0.12  # 12% base growth 1 an
            
            # Ajustements basés sur les indicateurs
            growth_modifier = 1.0
            
            # RSI impact
            if rsi > 70:  # Surachat
                growth_modifier -= 0.2
            elif rsi < 30:  # Survente
                growth_modifier += 0.2
            
            # Tendance impact
            if trend == 'bullish':
                growth_modifier += 0.15
            elif trend == 'bearish':
                growth_modifier -= 0.15
            
            # Fondamentaux impact
            if pe_ratio and pe_ratio < 15:  # Sous-évalué
                growth_modifier += 0.1
            elif pe_ratio and pe_ratio > 30:  # Surévalué
                growth_modifier -= 0.1
            
            # Croissance revenus
            if revenue_growth and revenue_growth > 0.2:  # Forte croissance
                growth_modifier += 0.1
            elif revenue_growth and revenue_growth < 0:  # Décroissance
                growth_modifier -= 0.15
            
            # Calcul prédictions
            predicted_6m = current_price * (1 + (base_growth_6m * growth_modifier))
            predicted_1y = current_price * (1 + (base_growth_1y * growth_modifier))
            
            # Scénarios
            volatility_factor = max(volatility / current_price, 0.1)  # Au moins 10% de volatilité
            
            scenarios_6m = {
                'bull': predicted_6m * (1 + volatility_factor),
                'base': predicted_6m,
                'bear': predicted_6m * (1 - volatility_factor)
            }
            
            scenarios_1y = {
                'bull': predicted_1y * (1 + volatility_factor * 1.5),
                'base': predicted_1y,
                'bear': predicted_1y * (1 - volatility_factor * 1.5)
            }
            
            # Calcul de probabilités plus réalistes basées sur les données
            prob_up_6m = self._calculate_realistic_probability(
                rsi, trend, volatility, pe_ratio, revenue_growth, growth_modifier, timeframe='6m'
            )
            prob_up_1y = self._calculate_realistic_probability(
                rsi, trend, volatility, pe_ratio, revenue_growth, growth_modifier, timeframe='1y'
            )
            
            return {
                'predictions': {
                    '6_months': {
                        'target_price': round(predicted_6m, 2),
                        'scenarios': {k: round(v, 2) for k, v in scenarios_6m.items()},
                        'probability_up': prob_up_6m,
                        'probability_down': 100 - prob_up_6m
                    },
                    '1_year': {
                        'target_price': round(predicted_1y, 2),
                        'scenarios': {k: round(v, 2) for k, v in scenarios_1y.items()},
                        'probability_up': prob_up_1y,
                        'probability_down': 100 - prob_up_1y
                    }
                },
                'growth_factors': {
                    'modifier_applied': round(growth_modifier, 2),
                    'rsi_impact': 'Positive' if rsi < 30 else 'Negative' if rsi > 70 else 'Neutral',
                    'trend_impact': trend.title(),
                    'valuation_impact': 'Undervalued' if pe_ratio and pe_ratio < 15 else 'Overvalued' if pe_ratio and pe_ratio > 30 else 'Fair'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions for {ticker}: {e}")
            return {}
    
    def _calculate_realistic_probability(self, rsi: float, trend: str, volatility: float, 
                                       pe_ratio: float, revenue_growth: float, 
                                       growth_modifier: float, timeframe: str) -> int:
        """Calcule une probabilité de hausse réaliste basée sur les données du marché"""
        try:
            base_prob = 45 if timeframe == '6m' else 50  # Base plus prudente
            
            # Ajustements basés sur les indicateurs RÉELS
            adjustments = 0
            
            # 1. RSI impact (fort impact sur la probabilité)
            if rsi < 25:  # Très survendu
                adjustments += 25
            elif rsi < 35:  # Survendu
                adjustments += 15
            elif rsi > 75:  # Très suracheté
                adjustments -= 25
            elif rsi > 65:  # Suracheté
                adjustments -= 15
            
            # 2. Tendance (impact modéré)
            if trend == 'bullish':
                adjustments += 10
            elif trend == 'bearish':
                adjustments -= 15
            
            # 3. Valorisation (P/E) - impact sur le long terme
            if pe_ratio > 0:
                if pe_ratio < 12:  # Très sous-évalué
                    adjustments += 15 if timeframe == '1y' else 8
                elif pe_ratio < 18:  # Sous-évalué
                    adjustments += 8 if timeframe == '1y' else 5
                elif pe_ratio > 35:  # Très surévalué
                    adjustments -= 20 if timeframe == '1y' else -10
                elif pe_ratio > 25:  # Surévalué
                    adjustments -= 10 if timeframe == '1y' else -5
            
            # 4. Croissance des revenus (impact fondamental)
            if revenue_growth > 0.3:  # Très forte croissance
                adjustments += 20
            elif revenue_growth > 0.1:  # Bonne croissance
                adjustments += 10
            elif revenue_growth < -0.1:  # Décroissance
                adjustments -= 15
            
            # 5. Volatilité (réduit la confiance)
            if volatility > 0.3:  # Très volatil
                adjustments -= 10
            elif volatility > 0.2:  # Volatil
                adjustments -= 5
            
            # 6. Facteur temps (incertitude croissante)
            if timeframe == '1y':
                adjustments = int(adjustments * 0.8)  # Moins certain sur 1 an
            
            # Calcul final avec plafonds réalistes
            final_prob = base_prob + adjustments
            
            # Plafonnement réaliste pour un système financier
            if final_prob > 75:  # Maximum réaliste pour un système automatique
                final_prob = 75
            elif final_prob < 25:  # Minimum réaliste
                final_prob = 25
            
            return final_prob
            
        except Exception as e:
            logger.error(f"Error calculating realistic probability: {e}")
            return 50  # Neutre en cas d'erreur
    
    def _calculate_budget_allocation(self, ticker: str, current_price: float,
                                   technical_analysis: Dict, fundamental_analysis: Dict,
                                   sector_context: Dict, predictions: Dict) -> Dict[str, Any]:
        """Calcule la recommandation d'allocation budgétaire (montant en euros entre 10€ et 200€)"""
        try:
            # Budget constraints
            MIN_INVESTMENT = 10.0  # 10€ minimum
            MAX_INVESTMENT = 200.0  # 200€ maximum
            BASE_INVESTMENT = 50.0  # 50€ base prudente
            
            # Facteurs d'ajustement
            allocation_modifiers = []
            
            # 1. Facteur confiance technique (RSI + Tendance)
            rsi = technical_analysis.get('rsi', 50)
            trend = technical_analysis.get('trend', 'neutral')
            
            if trend == 'bullish' and 30 <= rsi <= 70:
                allocation_modifiers.append(('strong_technical', 1.8))  # +80%
            elif trend == 'bullish' or (30 <= rsi <= 70):
                allocation_modifiers.append(('good_technical', 1.4))    # +40%
            elif rsi > 75 or rsi < 25:
                allocation_modifiers.append(('risky_technical', 0.6))   # -40%
            else:
                allocation_modifiers.append(('neutral_technical', 1.0)) # Neutre
            
            # 2. Facteur fondamental (P/E + Croissance)
            pe_ratio = fundamental_analysis.get('pe_ratio', 20)
            revenue_growth = fundamental_analysis.get('revenue_growth', 0)
            
            if pe_ratio > 0:
                if pe_ratio < 15 and revenue_growth > 0.1:  # Sous-évalué + croissance
                    allocation_modifiers.append(('undervalued_growth', 2.0))  # +100%
                elif pe_ratio < 20 and revenue_growth > 0:
                    allocation_modifiers.append(('fair_value', 1.3))          # +30%
                elif pe_ratio > 40:
                    allocation_modifiers.append(('overvalued', 0.7))          # -30%
                else:
                    allocation_modifiers.append(('normal_valuation', 1.0))
            
            # 3. Facteur sectoriel (stabilité/volatilité)
            sector = sector_context.get('sector', 'Unknown').lower()
            
            if sector in ['utilities', 'consumer staples', 'healthcare']:
                allocation_modifiers.append(('defensive_sector', 1.4))     # +40% (stable)
            elif sector in ['technology', 'biotechnology']:
                allocation_modifiers.append(('growth_sector', 1.2))        # +20% (croissance)
            elif sector in ['energy', 'materials', 'real estate']:
                allocation_modifiers.append(('cyclical_sector', 0.8))      # -20% (cyclique)
            else:
                allocation_modifiers.append(('neutral_sector', 1.0))
            
            # 4. Facteur prédictions (probabilité de hausse)
            predictions_data = predictions.get('predictions', {})
            prob_6m = predictions_data.get('6_months', {}).get('probability_up', 50)
            prob_1y = predictions_data.get('1_year', {}).get('probability_up', 50)
            
            avg_prob = (prob_6m + prob_1y) / 2
            if avg_prob >= 75:
                allocation_modifiers.append(('high_conviction', 1.8))      # +80%
            elif avg_prob >= 60:
                allocation_modifiers.append(('medium_conviction', 1.3))    # +30%
            elif avg_prob <= 40:
                allocation_modifiers.append(('low_conviction', 0.6))       # -40%
            else:
                allocation_modifiers.append(('neutral_conviction', 1.0))
            
            # 5. Facteur volatilité (Beta + volatilité historique)
            beta = fundamental_analysis.get('beta', 1.0)
            volatility = technical_analysis.get('volatility', 0)
            
            if beta > 1.5 or volatility > current_price * 0.05:  # Très volatil
                allocation_modifiers.append(('high_volatility', 0.7))      # -30%
            elif beta < 0.8:
                allocation_modifiers.append(('low_volatility', 1.2))       # +20%
            else:
                allocation_modifiers.append(('normal_volatility', 1.0))
            
            # Calcul final avec plafonnement
            final_multiplier = 1.0
            for factor_name, multiplier in allocation_modifiers:
                final_multiplier *= multiplier
            
            # Calcul montant final en euros
            recommended_amount = BASE_INVESTMENT * final_multiplier
            
            # Plafonnement intelligent
            if recommended_amount > MAX_INVESTMENT:
                recommended_amount = MAX_INVESTMENT
            elif recommended_amount < MIN_INVESTMENT:
                recommended_amount = MIN_INVESTMENT
            
            # Calcul d'une fourchette (±20% du montant recommandé)
            range_variation = recommended_amount * 0.2
            min_amount = max(MIN_INVESTMENT, recommended_amount - range_variation)
            max_amount = min(MAX_INVESTMENT, recommended_amount + range_variation)
            
            # Classification du niveau de confiance basé sur le montant
            if recommended_amount >= 150:
                confidence_level = "TRÈS ÉLEVÉ"
                risk_category = "Opportunité exceptionnelle - MAX INVESTMENT"
            elif recommended_amount >= 100:
                confidence_level = "ÉLEVÉ" 
                risk_category = "Belle opportunité - Position significative"
            elif recommended_amount >= 50:
                confidence_level = "MODÉRÉ"
                risk_category = "Position équilibrée - Standard"
            elif recommended_amount >= 25:
                confidence_level = "FAIBLE"
                risk_category = "Position prudente - Petit test"
            else:
                confidence_level = "TRÈS FAIBLE"
                risk_category = "Position minimale - Risque élevé"
            
            # Explication détaillée
            explanation_parts = []
            for factor_name, multiplier in allocation_modifiers:
                impact = "+" if multiplier > 1.0 else "-" if multiplier < 1.0 else "="
                pct_impact = abs((multiplier - 1.0) * 100)
                explanation_parts.append(f"{factor_name}: {impact}{pct_impact:.0f}%")
            
            return {
                'recommended_amount': round(recommended_amount, 0),
                'amount_range': {
                    'min': round(min_amount, 0),
                    'max': round(max_amount, 0)
                },
                'confidence_level': confidence_level,
                'risk_category': risk_category,
                'base_investment': BASE_INVESTMENT,
                'final_multiplier': round(final_multiplier, 2),
                'allocation_factors': allocation_modifiers,
                'explanation': " | ".join(explanation_parts),
                'investment_rationale': self._generate_investment_rationale(recommended_amount, confidence_level),
                'allocation_logic': {
                    'technical_strength': trend == 'bullish' and 30 <= rsi <= 70,
                    'fundamental_strength': pe_ratio < 20 and revenue_growth > 0,
                    'sector_stability': sector in ['utilities', 'consumer staples', 'healthcare'],
                    'high_conviction': avg_prob >= 75,
                    'low_volatility': beta < 1.5 and volatility < current_price * 0.05
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating budget allocation for {ticker}: {e}")
            return {
                'recommended_amount': 50.0,
                'amount_range': {'min': 40.0, 'max': 60.0},
                'confidence_level': 'MODÉRÉ',
                'risk_category': 'Position standard (erreur de calcul)',
                'explanation': 'Allocation par défaut suite à une erreur'
            }
    
    def _generate_investment_rationale(self, amount: float, confidence_level: str) -> str:
        """Génère une explication du montant recommandé"""
        if amount >= 150:
            return f"Investissement maximal de {amount:.0f}€ recommandé : tous les indicateurs convergent vers une opportunité exceptionnelle avec un excellent ratio risque/rendement."
        elif amount >= 100:
            return f"Investissement significatif de {amount:.0f}€ : les fondamentaux et la technique s'alignent pour une belle opportunité de croissance."
        elif amount >= 50:
            return f"Investissement standard de {amount:.0f}€ : profil équilibré avec un potentiel intéressant sans prise de risque excessive."
        elif amount >= 25:
            return f"Position prudente de {amount:.0f}€ : test de la position avec un capital limité en raison d'incertitudes."
        else:
            return f"Position minimale de {amount:.0f}€ : risque élevé identifié, investissement de découverte seulement."
    
    def _generate_claude_context_analysis(self, ticker: str, current_price: float,
                                        financial_data: Dict, technical_analysis: Dict,
                                        fundamental_analysis: Dict, sector_context: Dict,
                                        predictions: Dict) -> str:
        """Génère une analyse contextuelle intelligente style Claude"""
        
        # Date actuelle pour contexte
        today = datetime.now().strftime("%d %B %Y")
        
        # Récupération des métriques clés
        sector = sector_context.get('sector', 'Unknown')
        industry = sector_context.get('industry', 'Unknown')
        rsi = technical_analysis.get('rsi', 50)
        trend = technical_analysis.get('trend', 'neutral')
        pe_ratio = fundamental_analysis.get('pe_ratio', 0)
        revenue_growth = fundamental_analysis.get('revenue_growth', 0)
        target_6m = predictions.get('predictions', {}).get('6_months', {}).get('target_price', current_price)
        target_1y = predictions.get('predictions', {}).get('1_year', {}).get('target_price', current_price)
        prob_up_6m = predictions.get('predictions', {}).get('6_months', {}).get('probability_up', 50)
        prob_up_1y = predictions.get('predictions', {}).get('1_year', {}).get('probability_up', 50)
        
        # Construction de l'analyse contextuelle
        analysis_parts = []
        
        # 1. Contexte macro et sectoriel
        analysis_parts.append(f"**Contexte {today}** : {ticker} évolue dans le secteur {sector}, un secteur ")
        
        if sector.lower() in ['technology', 'communication services', 'consumer discretionary']:
            analysis_parts.append("actuellement sous pression des politiques monétaires restrictives mais bénéficiant de l'essor de l'IA et de la transformation digitale.")
        elif sector.lower() in ['energy', 'materials']:
            analysis_parts.append("volatil en raison des tensions géopolitiques et de la transition énergétique mondiale.")
        elif sector.lower() in ['healthcare', 'utilities', 'consumer staples']:
            analysis_parts.append("défensif, recherché en période d'incertitude économique.")
        else:
            analysis_parts.append("avec ses propres défis sectoriels dans le contexte économique actuel.")
        
        # 2. Analyse technique contextuelle
        analysis_parts.append(f"\\n\\n**Position technique** : ")
        if rsi > 70:
            analysis_parts.append(f"Le RSI à {rsi:.1f} indique une situation de surachat, suggérant une possible correction à court terme. ")
        elif rsi < 30:
            analysis_parts.append(f"Le RSI à {rsi:.1f} signale une survente, présentant une opportunité d'achat potentielle. ")
        else:
            analysis_parts.append(f"Le RSI équilibré à {rsi:.1f} indique une situation technique neutre. ")
        
        if trend == 'bullish':
            analysis_parts.append("La tendance haussière récente soutient un momentum positif.")
        elif trend == 'bearish':
            analysis_parts.append("La tendance baissière récente nécessite une vigilance accrue.")
        else:
            analysis_parts.append("L'absence de tendance claire nécessite d'attendre une direction.")
        
        # 3. Fondamentaux et valorisation
        analysis_parts.append(f"\\n\\n**Valorisation** : ")
        if pe_ratio and pe_ratio > 0:
            if pe_ratio < 15:
                analysis_parts.append(f"Avec un P/E de {pe_ratio:.1f}, l'action apparaît sous-évaluée par rapport au marché. ")
            elif pe_ratio > 30:
                analysis_parts.append(f"Le P/E élevé de {pe_ratio:.1f} suggère des attentes de croissance importantes déjà intégrées. ")
            else:
                analysis_parts.append(f"Le P/E de {pe_ratio:.1f} indique une valorisation équilibrée. ")
        
        if revenue_growth and revenue_growth != 0:
            if revenue_growth > 0.2:
                analysis_parts.append(f"La forte croissance des revenus ({revenue_growth*100:.1f}%) soutient la valorisation.")
            elif revenue_growth > 0:
                analysis_parts.append(f"La croissance modérée des revenus ({revenue_growth*100:.1f}%) est rassurante.")
            else:
                analysis_parts.append(f"La baisse des revenus ({revenue_growth*100:.1f}%) est préoccupante.")
        
        # 4. Perspectives et catalyseurs
        analysis_parts.append(f"\\n\\n**Perspectives** : ")
        
        # Logique contextuelle basée sur le secteur et les conditions actuelles
        if sector.lower() == 'technology':
            analysis_parts.append("L'IA générative et la transition cloud restent des catalyseurs majeurs, mais la régulation croissante et la saturation de certains marchés créent des headwinds. ")
        elif sector.lower() == 'healthcare':
            analysis_parts.append("Le vieillissement démographique et l'innovation thérapeutique soutiennent la demande, tandis que les pressions réglementaires sur les prix demeurent un risque. ")
        elif sector.lower() == 'energy':
            analysis_parts.append("La transition énergétique crée à la fois des opportunités (renouvelables) et des défis (fossiles traditionnels). ")
        
        # 5. Prédictions avec contexte
        change_6m = ((target_6m - current_price) / current_price) * 100
        change_1y = ((target_1y - current_price) / current_price) * 100
        
        analysis_parts.append(f"\\n\\n**Prédictions quantitatives** :")
        analysis_parts.append(f"\\n• **6 mois** : ${target_6m:.2f} ({change_6m:+.1f}%) - Probabilité hausse {prob_up_6m:.0f}%")
        analysis_parts.append(f"\\n• **1 an** : ${target_1y:.2f} ({change_1y:+.1f}%) - Probabilité hausse {prob_up_1y:.0f}%")
        
        # 6. Recommandation contextuelle
        analysis_parts.append(f"\\n\\n**Recommandation** : ")
        if prob_up_6m > 65 and rsi < 70:
            analysis_parts.append("Position favorable avec un timing d'entrée approprié. Surveillance des volumes pour confirmer.")
        elif prob_up_6m < 40 or rsi > 75:
            analysis_parts.append("Prudence recommandée. Attendre une correction ou des signaux techniques plus favorables.")
        else:
            analysis_parts.append("Position neutre. Surveiller les catalyseurs sectoriels et les indicateurs macro pour orienter la décision.")
        
        return ''.join(analysis_parts)
    
    def _generate_trend_charts(self, ticker: str, current_price: float, predictions: Dict) -> Dict[str, Any]:
        """Génère les graphiques de tendance avec vraies données"""
        try:
            logger.info(f"Génération des graphiques de tendance pour {ticker}")
            
            charts = {}
            
            # 1. Graphiques de tendance multi-périodes
            trend_charts = self.chart_generator.generate_trend_chart(
                ticker, 
                periods=['3mo', '6mo', '1y']
            )
            if trend_charts:
                charts['trend_charts'] = trend_charts
                logger.info(f"Graphiques de tendance générés: {list(trend_charts.keys())}")
            
            # 2. Graphique de prédictions
            prediction_chart = self.chart_generator.generate_prediction_chart(
                ticker, 
                current_price, 
                predictions
            )
            if prediction_chart:
                charts['prediction_chart'] = prediction_chart
                logger.info(f"Graphique de prédictions généré: {prediction_chart}")
            
            # 3. Graphique interactif
            interactive_chart = self.chart_generator.generate_interactive_chart(ticker)
            if interactive_chart:
                charts['interactive_chart'] = interactive_chart
                logger.info(f"Graphique interactif généré: {interactive_chart}")
            
            return charts
            
        except Exception as e:
            logger.error(f"Erreur génération graphiques {ticker}: {e}")
            return {}
    
    def _fallback_analysis(self, ticker: str, current_price: float) -> Dict[str, Any]:
        """Analyse de fallback en cas d'erreur"""
        return {
            'ticker': ticker,
            'current_price': current_price,
            'analysis_date': self.current_date.isoformat(),
            'claude_analysis': f"Analyse limitée pour {ticker} à ${current_price:.2f}. Données insuffisantes pour une analyse complète. Recommandation : Surveiller l'évolution des volumes et attendre plus de données.",
            'predictions': {
                'predictions': {
                    '6_months': {'target_price': current_price * 1.05, 'probability_up': 50},
                    '1_year': {'target_price': current_price * 1.12, 'probability_up': 55}
                }
            },
            'error': 'Limited analysis due to insufficient data'
        }