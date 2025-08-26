#!/usr/bin/env python3
"""
Envoi d'un email de test réel avec le graphique analyst ratings
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import base64

def generate_demo_chart():
    """Génère un graphique de démo pour les analyst ratings"""
    try:
        # Données fictives
        labels = ['Buy (10)', 'Hold (4)', 'Sell (1)']
        sizes = [10, 4, 1]
        colors = ['#28a745', '#ffc107', '#dc3545']
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Graphique en secteurs
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90,
                                         textprops={'fontsize': 12})
        
        # Améliorer le style
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        # Titre
        ax.set_title('AAPL - Analyst Ratings\nConsensus: Strong Buy', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Note en bas
        fig.text(0.5, 0.02, 'Total Analysts: 15', 
                ha='center', fontsize=12, style='italic')
        
        ax.axis('equal')
        fig.patch.set_facecolor('white')
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100, 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        plt.close(fig)
        buffer.close()
        
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"Erreur génération graphique: {e}")
        return ""

def send_test_email():
    """Envoie un email de test avec le graphique"""
    
    # Configuration email
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "patatecrackito@gmail.com"
    password = "vivg vwrp rqfx gcpn"
    recipient_email = "yojulesyo@gmail.com"
    
    # Générer le graphique
    print("📊 Génération du graphique analyst ratings...")
    chart_data = generate_demo_chart()
    
    if not chart_data:
        print("❌ Échec génération graphique")
        return False
    
    print("✅ Graphique généré!")
    
    # Créer l'email
    message = MIMEMultipart("alternative")
    message["Subject"] = f"🚨 BUY Signal: AAPL - Avec Graphique Analyst Ratings - {datetime.now().strftime('%H:%M')}"
    message["From"] = sender_email
    message["To"] = recipient_email
    
    # Contenu HTML avec graphique intégré
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
            <h1>🚨 BUY SIGNAL</h1>
            <h2>AAPL - Apple Inc.</h2>
            <p><strong>Nouveau système avec graphique analyst ratings !</strong></p>
        </div>
        
        <div style="padding: 20px;">
            <h3>📈 Signal Details</h3>
            <ul>
                <li><strong>Action:</strong> BUY</li>
                <li><strong>Prix actuel:</strong> $182.50</li>
                <li><strong>Confiance:</strong> 85.0%</li>
                <li><strong>Prix cible:</strong> $195.00</li>
                <li><strong>Stop Loss:</strong> $173.38</li>
                <li><strong>Position:</strong> $1,000</li>
            </ul>
            
            <p><strong>Rendement potentiel:</strong> <span style="color: #28a745; font-size: 18px;">+6.8%</span></p>
            
            <h3>🧠 Analyse</h3>
            <p>Fort consensus des analystes avec 67% de recommandations BUY + Smart Score 9/10 + objectifs de prix positifs</p>
            
            <h3>👨‍💼 Analyst Ratings - NOUVEAU ! 🎉</h3>
            <div style="text-align: center; margin: 20px 0; background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <img src="{chart_data}" alt="Graphique Analyst Ratings" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            </div>
            <div style="text-align: center; margin: 10px 0; font-size: 16px; color: #333;">
                <strong>Distribution:</strong> 
                <span style="color: #28a745;">●</span> 10 Buy (66.7%) • 
                <span style="color: #ffc107;">●</span> 4 Hold (26.7%) • 
                <span style="color: #dc3545;">●</span> 1 Sell (6.7%)
                <br><strong>Consensus: <span style="color: #28a745;">Strong Buy</span></strong>
            </div>
            
            <h3>📊 TipRanks Analysis</h3>
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <ul style="margin: 0; padding-left: 20px;">
                    <li><strong>Smart Score:</strong> 9/10 🌟</li>
                    <li><strong>Prix cible:</strong> $195.00</li>
                    <li><strong>Analystes:</strong> 15 total</li>
                    <li><strong>Sentiment:</strong> 75% Bullish 🐂</li>
                </ul>
            </div>
            
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <h3 style="color: #856404;">📱 Action Immédiate</h3>
                <p>Prêt à investir ? Ouvre Plum maintenant !</p>
                
                <div style="margin: 15px 0;">
                    <a href="plum://open" style="display: inline-block; background-color: #6f42c1; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 5px; font-weight: bold;">
                        📱 Ouvrir Plum App
                    </a>
                    <a href="https://withplum.com/app" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 5px; font-weight: bold;">
                        🌐 Plum Web
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #856404;">
                    <strong>Recherche:</strong> "AAPL" dans Plum<br>
                    <strong>Quantité:</strong> ~5 actions (≈$912)
                </p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #17a2b8;">
                <h4 style="margin-top: 0;">ℹ️ À propos de ce système</h4>
                <p style="margin-bottom: 0;"><small>
                    Ce système analyse automatiquement 10 actions d'experts analystes chaque jour.
                    Le nouveau graphique analyst ratings montre visuellement la distribution des recommandations.
                    Système actif tous les jours de bourse avec vérifications toutes les 30 minutes.
                </small></p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                <p style="margin: 0;"><small>
                    ⚠️ <strong>Disclaimer:</strong> Signal automatisé à des fins éducatives. 
                    Pas un conseil financier. Toujours faire ses propres recherches.
                </small></p>
            </div>
            
            <p style="text-align: center; margin-top: 20px; color: #666;">
                <small>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</small>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Créer les parties de l'email
    html_part = MIMEText(html, "html")
    message.attach(html_part)
    
    # Envoyer l'email
    print("📧 Envoi de l'email...")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        
        print("✅ Email envoyé avec succès!")
        print(f"📨 Destinataire: {recipient_email}")
        print(f"📊 Graphique analyst ratings inclus dans l'email")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test d'envoi d'email avec graphique analyst ratings")
    print("=" * 50)
    
    success = send_test_email()
    
    if success:
        print("\n🎉 Test réussi! L'email avec le graphique a été envoyé.")
        print("📱 Vérifie ta boîte mail (yojulesyo@gmail.com)")
        print("🎯 Le système est prêt à tourner automatiquement demain!")
    else:
        print("\n❌ Test échoué. Vérifie la configuration email.")