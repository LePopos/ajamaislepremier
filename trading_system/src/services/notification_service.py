import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import logging
import requests
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import base64

from ..models.stock_models import TradingSignal, Stock, Recommendation
from ..config.config import config
from ..services.expert_analysis import ExpertAnalysis

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending trading alerts via email, SMS, webhooks"""
    
    def __init__(self, email_config: Dict):
        self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.sender_email = email_config.get('sender_email')
        self.sender_password = email_config.get('sender_password')
        self.recipient_emails = email_config.get('recipient_emails', [])
        self.webhook_url = email_config.get('webhook_url')
        self.expert_analysis = ExpertAnalysis()
    
    def _generate_analyst_ratings_chart(self, recommendations: Dict) -> str:
        """Generate a pie chart for analyst ratings and return as base64 encoded image"""
        try:
            if not recommendations or not recommendations.get('total_analysts'):
                return ""
            
            # Get the data
            buy_count = recommendations.get('buy_count', 0)
            hold_count = recommendations.get('hold_count', 0)  
            sell_count = recommendations.get('sell_count', 0)
            total = buy_count + hold_count + sell_count
            
            if total == 0:
                return ""
            
            # Define colors and labels
            labels = []
            sizes = []
            colors = []
            
            if buy_count > 0:
                labels.append(f'Buy ({buy_count})')
                sizes.append(buy_count)
                colors.append('#28a745')  # Green
                
            if hold_count > 0:
                labels.append(f'Hold ({hold_count})')
                sizes.append(hold_count)
                colors.append('#ffc107')  # Yellow
                
            if sell_count > 0:
                labels.append(f'Sell ({sell_count})')
                sizes.append(sell_count)
                colors.append('#dc3545')  # Red
            
            # Create the chart
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                             autopct='%1.1f%%', startangle=90,
                                             textprops={'fontsize': 12})
            
            # Improve text styling
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)
            
            # Add title
            consensus = recommendations.get('consensus', 'N/A')
            ticker = recommendations.get('ticker', '')
            ax.set_title(f'{ticker} - Analyst Ratings\nConsensus: {consensus}', 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Add total analysts count
            total_analysts = recommendations.get('total_analysts', 0)
            fig.text(0.5, 0.02, f'Total Analysts: {total_analysts}', 
                    ha='center', fontsize=12, style='italic')
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Set background color
            fig.patch.set_facecolor('white')
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100, 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Clean up
            plt.close(fig)
            buffer.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Error generating analyst ratings chart: {e}")
            return ""
        
    def send_signal_alert(self, signal: TradingSignal, stock: Stock, 
                         recommendation: Optional[Recommendation] = None) -> bool:
        """Send trading signal alert via email"""
        
        try:
            if not self.sender_email or not self.recipient_emails:
                logger.warning("Email configuration incomplete - skipping email alert")
                return False
            
            # Create email content
            subject = f"🚨 {signal.signal_type} Signal: {stock.ticker}"
            
            html_body = self._create_signal_email_html(signal, stock, recommendation)
            text_body = self._create_signal_email_text(signal, stock, recommendation)
            
            # Send email
            success = self._send_email(subject, html_body, text_body)
            
            if success:
                logger.info(f"Email alert sent for {signal.signal_type} signal on {stock.ticker}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending signal alert: {e}")
            return False
    
    def send_daily_summary(self, active_signals: List[Dict], portfolio_summary: Dict) -> bool:
        """Send daily portfolio summary"""
        
        try:
            if not self.sender_email or not self.recipient_emails:
                return False
            
            subject = f"📊 Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            html_body = self._create_summary_email_html(active_signals, portfolio_summary)
            text_body = self._create_summary_email_text(active_signals, portfolio_summary)
            
            return self._send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False
    
    def send_webhook_notification(self, data: Dict) -> bool:
        """Send notification via webhook (Slack, Discord, etc.)"""
        
        try:
            if not self.webhook_url:
                return False
            
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Webhook notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    def _send_email(self, subject: str, html_body: str, text_body: str) -> bool:
        """Send email using SMTP"""
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = ", ".join(self.recipient_emails)
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                
                for recipient in self.recipient_emails:
                    server.sendmail(self.sender_email, recipient, message.as_string())
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _create_signal_email_html(self, signal: TradingSignal, stock: Stock, 
                                 recommendation: Optional[Recommendation] = None) -> str:
        """Create HTML email for trading signal"""
        
        # Signal colors
        color_map = {
            'BUY': '#28a745',   # Green
            'SELL': '#dc3545',  # Red  
            'HOLD': '#ffc107'   # Yellow
        }
        
        signal_color = color_map.get(signal.signal_type, '#6c757d')
        
        # Get expert analysis
        expert_analysis = self.expert_analysis.get_expert_analysis(stock.ticker, signal.price_when_generated)
        expert_pick_info = self.expert_analysis.is_expert_pick(stock.ticker)
        
        # Calculate potential return
        potential_return = ""
        if (signal.target_price and signal.price_when_generated and 
            signal.target_price != 0 and signal.price_when_generated != 0):
            return_pct = ((signal.target_price - signal.price_when_generated) / 
                         signal.price_when_generated * 100)
            potential_return = f"<p><strong>Potential Return:</strong> {return_pct:+.1f}%</p>"
        
        # Expert analysis section
        expert_section = ""
        if expert_analysis:
            expert_section = f"""
            <h3>👨‍💼 Expert Analyst Insights</h3>
            <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                <p><strong>Analyst:</strong> {expert_analysis['analyst_name']} ({', '.join(expert_pick_info.get('analysts', []))})</p>
                <p><strong>Investment Thesis:</strong> {expert_analysis['investment_thesis']}</p>
                <p><strong>Key Risks:</strong> {expert_analysis['key_risks']}</p>
                <p><strong>Timeline Outlook:</strong> {expert_analysis['timeline_outlook']}</p>
            </div>
            
            <h3>📈 Profitability Forecast</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0;">
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                    <h4 style="color: #007bff; margin: 0;">6 Months (M+6)</h4>
                    <p style="font-size: 18px; margin: 5px 0;"><strong>{expert_analysis['profit_probability_6m']}%</strong> probability</p>
                    <p style="margin: 5px 0;">Target: <strong>${expert_analysis['target_price_6m']:.2f}</strong></p>
                    <p style="margin: 0; color: {'green' if expert_analysis['expected_return_6m'] > 0 else 'red'};">
                        {expert_analysis['expected_return_6m']:+.1%} expected return
                    </p>
                </div>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                    <h4 style="color: #28a745; margin: 0;">12 Months (Y+1)</h4>
                    <p style="font-size: 18px; margin: 5px 0;"><strong>{expert_analysis['profit_probability_12m']}%</strong> probability</p>
                    <p style="margin: 5px 0;">Target: <strong>${expert_analysis['target_price_12m']:.2f}</strong></p>
                    <p style="margin: 0; color: {'green' if expert_analysis['expected_return_12m'] > 0 else 'red'};">
                        {expert_analysis['expected_return_12m']:+.1%} expected return
                    </p>
                </div>
            </div>
            <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; text-align: center;">
                <strong>Expert Recommendation: {expert_analysis['recommendation_strength']}</strong>
            </div>
            """
        
        # Recommendation details with analyst ratings chart
        rec_details = ""
        if recommendation:
            chart_html = ""
            
            # Try to get analyst recommendations and generate chart
            try:
                from ..api.tipranks_client import TipRanksClient
                tipranks_client = TipRanksClient()
                analyst_recommendations = tipranks_client.get_analyst_recommendations(stock.ticker)
                
                # Only generate chart if we have valid data
                if analyst_recommendations and analyst_recommendations.get('total_analysts', 0) > 0:
                    chart_base64 = self._generate_analyst_ratings_chart(analyst_recommendations)
                    if chart_base64:
                        chart_html = f"""
                        <div style="text-align: center; margin: 20px 0;">
                            <img src="{chart_base64}" alt="Analyst Ratings Chart" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        </div>
                        """
            except Exception as e:
                logger.error(f"Error generating analyst chart for {stock.ticker}: {e}")
            
            rec_details = f"""
            <h3>📊 TipRanks Analysis</h3>
            <ul>
                <li><strong>Smart Score:</strong> {recommendation.smart_score or 'N/A'}/10</li>
                <li><strong>Price Target:</strong> ${recommendation.mean_price_target or 'N/A'}</li>
                <li><strong>Analysts:</strong> {recommendation.num_analysts or 0}</li>
                <li><strong>Sentiment:</strong> {recommendation.bullish_percent or 0}% Bullish, {recommendation.bearish_percent or 0}% Bearish</li>
            </ul>
            
            {chart_html}
            """
        
        # Plum app links and action buttons
        plum_section = f"""
        <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
            <h3 style="color: #856404;">📱 Action Immédiate</h3>
            <p style="margin-bottom: 15px;">Prêt à investir ? Ouvre Plum maintenant !</p>
            
            <div style="margin: 15px 0;">
                <a href="plum://open" style="display: inline-block; background-color: #6f42c1; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                    📱 Ouvrir l'App Plum
                </a>
                <a href="https://withplum.com/app" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                    🌐 Plum Web
                </a>
            </div>
            
            <p style="font-size: 14px; color: #856404; margin-top: 15px;">
                <strong>Recherche:</strong> "{stock.ticker}" dans Plum<br>
                <strong>Quantité suggérée:</strong> ~{int((signal.position_size_usd or 0) / (signal.price_when_generated or 1))} actions
            </p>
        </div>
        """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: {signal_color}; color: white; padding: 20px; text-align: center;">
                <h1>🚨 {signal.signal_type} SIGNAL</h1>
                <h2>{stock.ticker}</h2>
                <p>{stock.company_name or ''}</p>
            </div>
            
            <div style="padding: 20px;">
                <h3>📈 Signal Details</h3>
                <ul>
                    <li><strong>Action:</strong> {signal.signal_type}</li>
                    <li><strong>Current Price:</strong> ${signal.price_when_generated:.2f}</li>
                    <li><strong>Confidence:</strong> {signal.confidence:.1%}</li>
                    <li><strong>Position Size:</strong> ${signal.position_size_usd or 0:.2f}</li>
                    <li><strong>Target Price:</strong> ${signal.target_price or 'N/A'}</li>
                    <li><strong>Stop Loss:</strong> ${signal.stop_loss_price or 'N/A'}</li>
                </ul>
                
                {potential_return}
                
                <h3>🧠 Reasoning</h3>
                <p>{signal.reasoning or 'No specific reasoning provided'}</p>
                
                {expert_section}
                
                {rec_details}
                
                {plum_section}
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <h4>⚠️ Important Disclaimer</h4>
                    <p><small>
                        This is an automated signal based on technical analysis and should not be considered as financial advice. 
                        Always do your own research and consider your risk tolerance before making any investment decisions.
                        Past performance does not guarantee future results.
                    </small></p>
                </div>
                
                <p style="text-align: center; margin-top: 20px;">
                    <small>Generated at {signal.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</small>
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_signal_email_text(self, signal: TradingSignal, stock: Stock, 
                                 recommendation: Optional[Recommendation] = None) -> str:
        """Create plain text email for trading signal"""
        
        potential_return = ""
        if (signal.target_price and signal.price_when_generated and 
            signal.target_price != 0 and signal.price_when_generated != 0):
            return_pct = ((signal.target_price - signal.price_when_generated) / 
                         signal.price_when_generated * 100)
            potential_return = f"Potential Return: {return_pct:+.1f}%\n"
        
        rec_details = ""
        if recommendation:
            rec_details = f"""
TipRanks Analysis:
- Smart Score: {recommendation.smart_score or 'N/A'}/10
- Price Target: ${recommendation.mean_price_target or 'N/A'}
- Analysts: {recommendation.num_analysts or 0}
- Sentiment: {recommendation.bullish_percent or 0}% Bullish, {recommendation.bearish_percent or 0}% Bearish
"""
        
        text = f"""
🚨 {signal.signal_type} SIGNAL: {stock.ticker}
{stock.company_name or ''}

📈 Signal Details:
- Action: {signal.signal_type}
- Current Price: ${signal.price_when_generated:.2f}
- Confidence: {signal.confidence:.1%}
- Position Size: ${signal.position_size_usd or 0:.2f}
- Target Price: ${signal.target_price or 'N/A'}
- Stop Loss: ${signal.stop_loss_price or 'N/A'}

{potential_return}

🧠 Reasoning:
{signal.reasoning or 'No specific reasoning provided'}

{rec_details}

⚠️ DISCLAIMER: This is an automated signal and should not be considered as financial advice.
Always do your own research before making investment decisions.

Generated at {signal.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return text
    
    def _create_summary_email_html(self, active_signals: List[Dict], portfolio_summary: Dict) -> str:
        """Create HTML daily summary email"""
        
        # Build signals table
        signals_rows = ""
        for signal_data in active_signals:
            color = {'BUY': '#28a745', 'SELL': '#dc3545', 'HOLD': '#ffc107'}.get(
                signal_data.get('signal_type'), '#6c757d')
            
            signals_rows += f"""
            <tr>
                <td><strong>{signal_data.get('ticker')}</strong></td>
                <td><span style="color: {color}; font-weight: bold;">{signal_data.get('signal_type')}</span></td>
                <td>${signal_data.get('price', 0):.2f}</td>
                <td>{signal_data.get('confidence', 0):.1%}</td>
                <td>{signal_data.get('age_hours', 0):.1f}h</td>
            </tr>
            """
        
        if not signals_rows:
            signals_rows = "<tr><td colspan='5' style='text-align: center;'>No active signals</td></tr>"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <div style="background-color: #007bff; color: white; padding: 20px; text-align: center;">
                <h1>📊 Daily Trading Summary</h1>
                <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
            </div>
            
            <div style="padding: 20px;">
                <h2>🎯 Active Signals</h2>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="border: 1px solid #dee2e6; padding: 8px;">Ticker</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px;">Signal</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px;">Price</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px;">Confidence</th>
                            <th style="border: 1px solid #dee2e6; padding: 8px;">Age</th>
                        </tr>
                    </thead>
                    <tbody>
                        {signals_rows}
                    </tbody>
                </table>
                
                <h2>💼 Portfolio Summary</h2>
                <ul>
                    <li><strong>Active Signals:</strong> {portfolio_summary.get('active_signals', 0)}</li>
                    <li><strong>Total Value:</strong> ${portfolio_summary.get('total_value', 0):,.2f}</li>
                    <li><strong>Today's P&L:</strong> ${portfolio_summary.get('daily_pnl', 0):+,.2f}</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_summary_email_text(self, active_signals: List[Dict], portfolio_summary: Dict) -> str:
        """Create plain text daily summary email"""
        
        signals_text = ""
        for signal_data in active_signals:
            signals_text += f"- {signal_data.get('ticker')}: {signal_data.get('signal_type')} @ ${signal_data.get('price', 0):.2f} ({signal_data.get('confidence', 0):.1%})\n"
        
        if not signals_text:
            signals_text = "- No active signals\n"
        
        text = f"""
📊 Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}

🎯 Active Signals:
{signals_text}

💼 Portfolio Summary:
- Active Signals: {portfolio_summary.get('active_signals', 0)}
- Total Value: ${portfolio_summary.get('total_value', 0):,.2f}
- Today's P&L: ${portfolio_summary.get('daily_pnl', 0):+,.2f}

Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return text
    
    def send_custom_email(self, subject: str, html_content: str, recipients: List[str] = None) -> bool:
        """Send a custom email with HTML content"""
        
        # Use provided recipients or default ones
        original_recipients = self.recipient_emails
        if recipients:
            self.recipient_emails = recipients
        
        try:
            # Convert HTML to text for fallback
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Send email
            success = self._send_email(subject, html_content, text_content)
            
            if success:
                logger.info(f"Custom email sent successfully: {subject}")
            else:
                logger.error(f"Failed to send custom email: {subject}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending custom email: {e}")
            return False
        finally:
            # Restore original recipients
            self.recipient_emails = original_recipients
    
    def send_enhanced_signal_alert(self, signal: TradingSignal, stock: Stock, 
                                 recommendation: Optional[Recommendation] = None,
                                 enhanced_analysis: Optional[Dict] = None) -> bool:
        """Send enhanced trading signal alert with comprehensive analysis"""
        
        try:
            # Create enhanced HTML email
            html_content = self._create_enhanced_signal_email_html(
                signal, stock, recommendation, enhanced_analysis
            )
            
            # Create subject
            signal_type = signal.signal_type.upper()
            subject = f"🎯 {signal_type} SIGNAL: {stock.ticker} - ${signal.price_when_generated:.2f}"
            
            if enhanced_analysis and 'predictions' in enhanced_analysis:
                pred_6m = enhanced_analysis['predictions'].get('predictions', {}).get('6_months', {})
                if pred_6m:
                    target_6m = pred_6m.get('target_price', 0)
                    subject += f" → ${target_6m:.2f} (+6M)"
            
            # Convert to text for fallback
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Send email
            success = self._send_email(subject, html_content, text_content)
            
            if success:
                logger.info(f"Enhanced signal alert sent for {stock.ticker}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending enhanced signal alert: {e}")
            # Fallback to regular signal alert
            return self.send_signal_alert(signal, stock, recommendation)
    
    def _create_enhanced_signal_email_html(self, signal: TradingSignal, stock: Stock, 
                                         recommendation: Optional[Recommendation] = None,
                                         enhanced_analysis: Optional[Dict] = None) -> str:
        """Create enhanced HTML email for trading signal with comprehensive analysis"""
        
        # Signal colors
        color_map = {
            'BUY': '#28a745',   # Green
            'SELL': '#dc3545',  # Red  
            'HOLD': '#ffc107'   # Yellow
        }
        
        signal_color = color_map.get(signal.signal_type, '#6c757d')
        current_time = datetime.now().strftime('%d/%m/%Y à %H:%M')
        
        # Basic signal info
        basic_info = f"""
        <div style="background: {signal_color}15; padding: 20px; border-radius: 8px; border-left: 4px solid {signal_color}; margin-bottom: 25px;">
            <h2 style="color: {signal_color}; margin: 0 0 15px 0;">{signal.signal_type} SIGNAL - {stock.ticker}</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <strong>Prix actuel:</strong> ${signal.price_when_generated:.2f}<br>
                    <strong>Confiance:</strong> {signal.confidence:.0%}<br>
                    <strong>Généré le:</strong> {current_time}
                </div>
                <div>
                    <strong>Société:</strong> {stock.company_name or stock.ticker}<br>
                    <strong>Raisonnement:</strong> {signal.reasoning[:100]}...
                </div>
            </div>
        </div>
        """
        
        # Enhanced analysis section
        enhanced_section = ""
        predictions_section = ""
        
        if enhanced_analysis:
            # Technical & Fundamental Analysis
            tech_analysis = enhanced_analysis.get('technical_analysis', {})
            fund_analysis = enhanced_analysis.get('fundamental_analysis', {})
            
            enhanced_section = f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                <h3 style="color: #495057; margin: 0 0 15px 0;">📈 Analyse Technique & Fondamentale</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                    <div>
                        <h4 style="color: #007bff; margin: 0 0 10px 0;">Technique</h4>
                        <p><strong>RSI:</strong> {tech_analysis.get('rsi', 0):.1f}</p>
                        <p><strong>Tendance:</strong> {tech_analysis.get('trend', 'N/A').title()}</p>
                        <p><strong>Support:</strong> ${tech_analysis.get('support_level', 0):.2f}</p>
                        <p><strong>Résistance:</strong> ${tech_analysis.get('resistance_level', 0):.2f}</p>
                    </div>
                    <div>
                        <h4 style="color: #28a745; margin: 0 0 10px 0;">Fondamentale</h4>
                        <p><strong>P/E Ratio:</strong> {fund_analysis.get('pe_ratio', 0):.1f}</p>
                        <p><strong>Croissance Rev.:</strong> {fund_analysis.get('revenue_growth', 0)*100:+.1f}%</p>
                        <p><strong>Beta:</strong> {fund_analysis.get('beta', 0):.2f}</p>
                        <p><strong>ROE:</strong> {fund_analysis.get('roe', 0)*100:.1f}%</p>
                    </div>
                </div>
            </div>
            """
            
            # Predictions section
            predictions = enhanced_analysis.get('predictions', {}).get('predictions', {})
            if predictions:
                pred_6m = predictions.get('6_months', {})
                pred_1y = predictions.get('1_year', {})
                
                predictions_section = f"""
                <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 25px;">
                    <h3 style="color: #007bff; margin: 0 0 15px 0;">🎯 Prédictions Quantitatives</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div style="background: white; padding: 15px; border-radius: 6px;">
                            <h4 style="color: #495057; margin: 0 0 10px 0;">📅 6 Mois (M+6)</h4>
                            <p><strong>Cible:</strong> ${pred_6m.get('target_price', 0):.2f}</p>
                            <p><strong>Prob. hausse:</strong> {pred_6m.get('probability_up', 50):.0f}%</p>
                            <div style="font-size: 12px; color: #6c757d;">
                                Scénarios: Bull ${pred_6m.get('scenarios', {}).get('bull', 0):.2f} | 
                                Base ${pred_6m.get('scenarios', {}).get('base', 0):.2f} | 
                                Bear ${pred_6m.get('scenarios', {}).get('bear', 0):.2f}
                            </div>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 6px;">
                            <h4 style="color: #495057; margin: 0 0 10px 0;">📅 1 An (Y+1)</h4>
                            <p><strong>Cible:</strong> ${pred_1y.get('target_price', 0):.2f}</p>
                            <p><strong>Prob. hausse:</strong> {pred_1y.get('probability_up', 50):.0f}%</p>
                            <div style="font-size: 12px; color: #6c757d;">
                                Scénarios: Bull ${pred_1y.get('scenarios', {}).get('bull', 0):.2f} | 
                                Base ${pred_1y.get('scenarios', {}).get('base', 0):.2f} | 
                                Bear ${pred_1y.get('scenarios', {}).get('bear', 0):.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            # Budget Allocation section
            budget_allocation = enhanced_analysis.get('budget_allocation', {})
            if budget_allocation:
                recommended_amount = budget_allocation.get('recommended_amount', 50)
                amount_range = budget_allocation.get('amount_range', {'min': 40, 'max': 60})
                confidence_level = budget_allocation.get('confidence_level', 'MODÉRÉ')
                risk_category = budget_allocation.get('risk_category', 'Position standard')
                investment_rationale = budget_allocation.get('investment_rationale', '')
                
                # Color based on amount level
                if recommended_amount >= 150:
                    allocation_color = '#dc3545'  # Rouge - MAX
                elif recommended_amount >= 100:
                    allocation_color = '#28a745'  # Vert - Élevé
                elif recommended_amount >= 50:
                    allocation_color = '#007bff'  # Bleu - Standard
                else:
                    allocation_color = '#ffc107'  # Jaune - Prudent
                
                budget_section = f"""
                <div style="background: {allocation_color}15; padding: 20px; border-radius: 8px; border-left: 4px solid {allocation_color}; margin-bottom: 25px;">
                    <h3 style="color: {allocation_color}; margin: 0 0 15px 0;">💰 Montant Recommandé</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                        <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                            <h4 style="color: {allocation_color}; margin: 0 0 10px 0; font-size: 36px; font-weight: bold;">{recommended_amount:.0f}€</h4>
                            <p style="margin: 0; font-weight: bold; color: #495057;">Montant optimal</p>
                            <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 14px;">
                                Fourchette: {amount_range['min']:.0f}€ - {amount_range['max']:.0f}€
                            </p>
                            <p style="margin: 10px 0 0 0; color: {allocation_color}; font-size: 14px; font-weight: bold;">
                                {confidence_level}
                            </p>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 6px;">
                            <h4 style="color: #495057; margin: 0 0 10px 0;">Logique d'Investissement</h4>
                            <p style="margin: 0; font-weight: bold; color: #495057;">{risk_category}</p>
                            <p style="margin: 15px 0 0 0; font-size: 13px; color: #6c757d; line-height: 1.4;">
                                {investment_rationale}
                            </p>
                        </div>
                    </div>
                </div>
                """
            else:
                budget_section = ""
            
            # Claude Analysis section
            claude_analysis = enhanced_analysis.get('claude_analysis', '')
            if claude_analysis:
                claude_section = f"""
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 25px;">
                    <h3 style="color: #856404; margin: 0 0 15px 0;">🧠 Analyse Contextuelle</h3>
                    <div style="background: white; padding: 15px; border-radius: 6px; line-height: 1.6;">
                        {claude_analysis.replace('\\n', '<br>')}
                    </div>
                </div>
                """
            else:
                claude_section = ""
        
        # Combine all sections
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
            <div style="background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <h1 style="color: #495057; text-align: center; margin-bottom: 30px;">
                    🎯 Signal de Trading - {stock.ticker}
                </h1>
                
                {basic_info}
                {enhanced_section}
                {predictions_section}
                {budget_section if enhanced_analysis else ""}
                {claude_section if enhanced_analysis else ""}
                
                <div style="text-align: center; margin-top: 30px; padding-top: 25px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px; margin: 0;">
                        🤖 Système de trading automatique - <strong>Enhanced Analysis</strong><br>
                        Généré le {current_time} avec analyse hybride Yahoo Finance + Claude
                    </p>
                </div>
                
            </div>
        </div>
        """
        
        return html_content