#!/usr/bin/env python3
"""
Générateur de rapport GSC combiné (hausses + baisses)
Utilise les données réelles GSC au lieu de l'API
"""

import csv
from datetime import datetime
from typing import List, Dict
import argparse

def create_rises_data() -> List[List]:
    """Données hausses (triées par différence absolue décroissante)"""
    return [
        ["https://www.legrand.fr/pro/normes-et-reglementations/norme-nf-c-15-100/norme-nf-c-15-100-suivez-le-guide", 3059, 2469, 590, 123367, 98425, 24942],
        ["https://www.legrand.fr/", 2640, 2152, 488, 70194, 67231, 2963],
        ["https://www.legrand.fr/questions-frequentes/que-doit-on-brancher-sur-un-interrupteur-differentiel-de-type-a", 1379, 1085, 294, 13676, 12175, 1501],
        ["https://www.legrand.fr/pro/normes-et-reglementations/eclairage-de-securite/normes-et-eclairage-de-securite-et-baes-ce-quil-faut-savoir", 770, 520, 250, 17626, 14288, 3338],
        ["https://www.legrand.fr/questions-frequentes/quelle-difference-entre-interrupteur-differentiel-et-disjoncteur-differentiel", 878, 712, 166, 18099, 16960, 1139],
        ["https://www.legrand.fr/questions-frequentes/quel-interrupteur-differentiel-choisir-pour-son-tableau-electrique", 622, 492, 130, 9783, 8159, 1624],
        ["https://www.legrand.fr/questions-frequentes/comment-cabler-un-interrupteur-va-et-vient", 483, 365, 118, 24826, 18423, 6403],
        ["https://www.legrand.fr/questions-frequentes/comment-installer-un-parafoudre-au-tableau-electrique", 322, 218, 104, 4910, 3679, 1231],
        ["https://www.legrand.fr/catalogue/interrupteurs-et-prises/celiane", 516, 415, 101, 17171, 17014, 157],
        ["https://www.legrand.fr/questions-frequentes/le-parafoudre-est-il-obligatoire", 371, 270, 101, 7659, 5982, 1677],
        ["https://www.legrand.fr/questions-frequentes/quelle-courbe-choisir-pour-un-disjoncteur", 665, 570, 95, 7015, 6052, 963],
        ["https://www.legrand.fr/mon-projet/tutoriels/comment-installer-et-raccorder-une-prise-electrique-rj-45", 384, 290, 94, 13161, 10548, 2613],
        ["https://www.legrand.fr/questions-frequentes/quelle-section-de-cable-electrique-entre-le-compteur-et-le-tableau", 746, 659, 87, 12665, 11666, 999],
        ["https://www.legrand.fr/questions-frequentes/comment-effectuer-linstallation-de-ma-prise-de-recharge-pour-voiture-electrique", 406, 321, 85, 17380, 14109, 3271],
        ["https://www.legrand.fr/questions-frequentes/quel-disjoncteur-choisir-pour-proteger-le-circuit-dedie-a-un-four", 512, 430, 82, 7860, 7375, 485],
        ["https://www.legrand.fr/pro/catalogue/pret-a-poser-greenup-access-pour-vehicule-electrique-avec-prise-de-courant-saillie-patere-et-disjoncteur-differentiel", 204, 124, 80, 5866, 3355, 2511],
        ["https://www.legrand.fr/questions-frequentes/quelle-est-la-norme-nf-c-15-100-pour-la-salle-de-bain", 333, 254, 79, 6633, 6193, 440],
        ["https://www.legrand.fr/questions-frequentes/comment-brancher-un-interrupteur-va-et-vient-dans-une-piece", 1155, 1079, 76, 51228, 48402, 2826],
        ["https://www.legrand.fr/questions-frequentes/combien-de-radiateurs-par-disjoncteur", 375, 299, 76, 8796, 7313, 1483],
        ["https://www.legrand.fr/catalogue/interrupteurs-et-prises", 564, 491, 73, 48525, 36854, 11671],
        ["https://www.legrand.fr/guides/tout-savoir-sur-la-prise-rj45", 646, 575, 71, 31387, 26606, 4781],
        ["https://www.legrand.fr/questions-frequentes/quel-interrupteur-differentiel-choisir", 329, 259, 70, 7667, 6661, 1006],
        ["https://www.legrand.fr/mon-projet/tutoriels/comment-installer-un-pret-a-poser-green-up-access-pour-vehicule-electrique", 554, 485, 69, 5105, 4747, 358],
        ["https://www.legrand.fr/questions-frequentes/combien-de-disjoncteurs-par-interrupteur-differentiel-63-a", 383, 314, 69, 6503, 5768, 735],
        ["https://www.legrand.fr/pro/catalogue", 544, 476, 68, 12895, 10593, 2302],
    ]

def create_falls_data() -> List[List]:
    """Données baisses (triées par différence absolue décroissante en négatif)"""
    return [
        ["https://www.legrand.fr/questions-frequentes/pourquoi-le-disjoncteur-saute-pendant-lorage", 317, 419, -102, 2782, 4413, -1631],
        ["https://www.legrand.fr/questions-frequentes/pourquoi-le-disjoncteur-saute-quand-il-fait-chaud", 21, 119, -98, 407, 935, -528],
        ["https://www.legrand.fr/questions-frequentes/comment-faire-un-branchement-electrique-dinterrupteur", 330, 399, -69, 17148, 16533, 615],
        ["https://www.legrand.fr/pro/catalogue/declencheur-a-minimum-de-tension-mt-dx3-12v-a-48v-et-12v-a-48v", 1, 50, -49, 5, 123, -118],
        ["https://www.legrand.fr/questions-frequentes/que-faire-quand-un-disjoncteur-saute-ou-ne-se-rearme-pas", 983, 1029, -46, 22160, 22596, -436],
        ["https://www.legrand.fr/questions-frequentes/quel-disjoncteur-choisir-pour-un-circuit-dedie-a-la-climatisation", 394, 438, -44, 5329, 6681, -1352],
        ["https://www.legrand.fr/questions-frequentes/comment-faire-le-branchement-des-fils-de-ma-prise-electrique", 108, 146, -38, 5481, 5422, 59],
        ["https://www.legrand.fr/mon-projet/je-minspire/piece-par-piece/bureau-et-espace-multimedia/multipliez-vos-acces-internet-filaires-grace-a-la-rallonge-multiprise-switch-rj-45", 27, 63, -36, 337, 1639, -1302],
        ["https://www.legrand.fr/mon-projet/tutoriels/comment-remplacer-une-ancienne-prise-electrique-par-une-neuve", 55, 86, -31, 3061, 2974, 87],
        ["https://www.legrand.fr/questions-frequentes/comment-brancher-un-interrupteur-double-dans-une-piece", 170, 200, -30, 8822, 8877, -55],
        ["https://www.legrand.fr/questions-frequentes/comment-brancher-la-phase-et-le-neutre-sur-une-prise-electrique", 778, 807, -29, 34017, 32737, 1280],
        ["https://www.legrand.fr/questions-frequentes/comment-brancher-une-prise-electrique-cablage", 945, 973, -28, 77352, 74953, 2399],
        ["https://www.legrand.fr/questions-frequentes/dans-quel-cas-utiliser-les-griffes-de-fixation-dans-les-boites-dencastrement", 59, 87, -28, 910, 968, -58],
        ["https://www.legrand.fr/questions-frequentes/quest-ce-quun-disjoncteur-de-branchement-et-ou-se-trouve-t-il", 219, 246, -27, 7480, 7354, 126],
        ["https://www.legrand.fr/questions-frequentes/comment-connecter-des-fils-souples-a-des-bornes-automatiques", 135, 162, -27, 1744, 1774, -30],
        ["https://www.legrand.fr/questions-frequentes/quel-disjoncteur-differentiel-pour-une-climatisation", 100, 127, -27, 2524, 2844, -320],
        ["https://www.legrand.fr/questions-frequentes/comment-cabler-un-voyant-temoin-ou-lumineux-pour-un-va-et-vient-ou-un-bouton-poussoir-plexo-tm", 273, 299, -26, 6418, 6175, 243],
        ["https://www.legrand.fr/questions-frequentes/comment-poser-une-prise-electrique-sur-ma-terrasse", 74, 100, -26, 2187, 2375, -188],
        ["https://www.legrand.fr/questions-frequentes/comment-savoir-si-un-disjoncteur-est-hs", 158, 183, -25, 3237, 3370, -133],
        ["https://www.legrand.fr/questions-frequentes/a-quoi-sert-un-interrupteur-differentiel-de-30-ma", 90, 115, -25, 4258, 3959, 299],
        ["https://www.legrand.fr/questions-frequentes/comment-brancher-une-horloge-sur-un-tableau-electrique", 37, 62, -25, 2559, 2343, 216],
        ["https://www.legrand.fr/pro/catalogue/reenclencheur-automatique-stop-and-go-standard-dx3-230v-2-modules", 50, 74, -24, 802, 689, 113],
        ["https://www.legrand.fr/questions-frequentes/combien-dinterrupteurs-brancher-sur-un-telerupteur", 149, 172, -23, 7005, 5807, 1198],
        ["https://www.legrand.fr/questions-frequentes/pourquoi-le-disjoncteur-saute-quand-jallume-la-lumiere", 155, 176, -21, 2965, 2709, 256],
        ["https://www.legrand.fr/maison-connectee/appli-home-control-pilotez-votre-maison-connectee", 121, 142, -21, 1638, 1619, 19],
    ]

def categorize_url(url: str) -> str:
    """Catégorise une URL"""
    if '/pro/' in url:
        return 'Professional'
    elif '/maison-connectee/' in url:
        return 'Smart Home'
    elif '/catalogue/' in url:
        return 'Catalog'
    elif '/questions-frequentes/' in url:
        return 'FAQ'
    elif '/mon-projet/' in url:
        return 'Projects'
    elif '/guides/' in url:
        return 'Guides'
    elif url == 'https://www.legrand.fr/':
        return 'Homepage'
    else:
        return 'Other'

def detect_anomalies(data: List[Dict], report_type: str) -> List[Dict]:
    """Détecte les anomalies dans les données"""
    anomalies = []
    
    for row in data:
        ctr_current = (row['clicks_current'] / row['impressions_current'] * 100) if row['impressions_current'] > 0 else 0
        ctr_previous = (row['clicks_previous'] / row['impressions_previous'] * 100) if row['impressions_previous'] > 0 else 0
        
        # 1. Détection d'effondrement de trafic (> 80% de baisse avec volume significatif)
        if report_type == "baisses":
            clicks_variation = (row['clicks_current'] - row['clicks_previous']) / row['clicks_previous'] * 100 if row['clicks_previous'] > 0 else 0
            
            if clicks_variation < -80 and row['clicks_previous'] >= 50:
                anomalies.append({
                    'type': '🚨 EFFONDREMENT CRITIQUE',
                    'severity': 'HIGH',
                    'url': row['url'],
                    'message': f"Chute de {clicks_variation:.1f}% ({row['clicks_previous']} → {row['clicks_current']} clics)",
                    'category': row['category']
                })
            
            # Questions saisonnières suspectes
            if "orage" in row['url'] and abs(row['clicks_diff']) > 50:
                anomalies.append({
                    'type': '🌩️ SAISONNALITÉ SUSPECTE',
                    'severity': 'MEDIUM',
                    'url': row['url'],
                    'message': f"Baisse anormale pour contenu météo ({row['clicks_diff']} clics)",
                    'category': row['category']
                })
            
            if "chaud" in row['url'] and abs(row['clicks_diff']) > 50:
                anomalies.append({
                    'type': '🌡️ SAISONNALITÉ INVERSÉE',
                    'severity': 'MEDIUM',
                    'url': row['url'],
                    'message': f"Baisse en période chaude suspecte ({row['clicks_diff']} clics)",
                    'category': row['category']
                })
        
        # 2. CTR anormalement bas ou élevé
        if ctr_current < 1 and row['impressions_current'] > 5000:
            anomalies.append({
                'type': '📉 CTR CRITIQUE',
                'severity': 'MEDIUM',
                'url': row['url'],
                'message': f"CTR très bas ({ctr_current:.2f}%) malgré {row['impressions_current']:,} impressions",
                'category': row['category']
            })
        elif ctr_current > 15:
            anomalies.append({
                'type': '📈 CTR EXCEPTIONNEL',
                'severity': 'LOW',
                'url': row['url'],
                'message': f"CTR très élevé ({ctr_current:.1f}%) - opportunité à exploiter",
                'category': row['category']
            })
        
        # 3. Disparités impressions vs clics
        if report_type == "hausses":
            if row['impressions_diff'] < 0 and row['clicks_diff'] > 100:
                anomalies.append({
                    'type': '🎯 EFFICACITÉ ACCRUE',
                    'severity': 'LOW',
                    'url': row['url'],
                    'message': f"Moins d'impressions ({row['impressions_diff']:+,}) mais plus de clics (+{row['clicks_diff']})",
                    'category': row['category']
                })
            elif row['impressions_diff'] > 10000 and row['clicks_diff'] < 100:
                anomalies.append({
                    'type': '👁️ VISIBILITÉ SANS IMPACT',
                    'severity': 'MEDIUM',
                    'url': row['url'],
                    'message': f"Forte hausse impressions (+{row['impressions_diff']:,}) mais peu de clics (+{row['clicks_diff']})",
                    'category': row['category']
                })
        
        # 4. Patterns techniques suspects
        if row['clicks_current'] == 1 and row['clicks_previous'] > 20:
            anomalies.append({
                'type': '⚠️ CHUTE TECHNIQUE SUSPECTÉE',
                'severity': 'HIGH',
                'url': row['url'],
                'message': f"Chute brutale vers 1 clic depuis {row['clicks_previous']} - Possible problème technique",
                'category': row['category']
            })
        
        # 5. Contenu obsolète/saisonnier
        if "climatisation" in row['url'] and report_type == "baisses" and abs(row['clicks_diff']) > 20:
            anomalies.append({
                'type': '❄️ SAISONNALITÉ NORMALE',
                'severity': 'LOW',
                'url': row['url'],
                'message': f"Baisse normale pour contenu climatisation hors saison ({row['clicks_diff']} clics)",
                'category': row['category']
            })
    
    return sorted(anomalies, key=lambda x: {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x['severity']], reverse=True)

def generate_insights(rises_data: List[Dict], falls_data: List[Dict], rises_anomalies: List[Dict], falls_anomalies: List[Dict]) -> List[str]:
    """Génère des insights intelligents sur les données combinées"""
    insights = []
    
    # Calculs globaux
    total_rises_clicks = sum(row['clicks_diff'] for row in rises_data)
    total_falls_clicks = sum(abs(row['clicks_diff']) for row in falls_data)
    net_impact = total_rises_clicks - total_falls_clicks
    
    # Insight principal
    if net_impact > 0:
        insights.append(f"📈 **Performance globale positive** : +{total_rises_clicks:,} clics en hausse vs -{total_falls_clicks:,} en baisse = **+{net_impact:,} clics nets**")
    else:
        insights.append(f"📉 **Performance globale négative** : +{total_rises_clicks:,} clics en hausse vs -{total_falls_clicks:,} en baisse = **{net_impact:,} clics nets**")
    
    # Champion vs plus grosse chute
    top_rise = rises_data[0] if rises_data else None
    top_fall = falls_data[0] if falls_data else None
    
    if top_rise and top_fall:
        insights.append(f"🏆 **Champion vs Chute** : +{top_rise['clicks_diff']} clics (Norme NF-C 15-100) contre -{abs(top_fall['clicks_diff'])} clics (question orage)")
    
    # Analyse catégorielle croisée
    rise_categories = {}
    fall_categories = {}
    
    for row in rises_data:
        cat = row['category']
        rise_categories[cat] = rise_categories.get(cat, 0) + row['clicks_diff']
    
    for row in falls_data:
        cat = row['category']
        fall_categories[cat] = fall_categories.get(cat, 0) + abs(row['clicks_diff'])
    
    # Catégories gagnantes et perdantes
    best_rise_cat = max(rise_categories.items(), key=lambda x: x[1]) if rise_categories else None
    worst_fall_cat = max(fall_categories.items(), key=lambda x: x[1]) if fall_categories else None
    
    if best_rise_cat:
        insights.append(f"📚 **Catégorie star** : {best_rise_cat[0]} gagne +{best_rise_cat[1]:,} clics")
    if worst_fall_cat:
        insights.append(f"📂 **Catégorie impactée** : {worst_fall_cat[0]} perd -{worst_fall_cat[1]:,} clics")
    
    # Détection de patterns saisonniers
    seasonal_rises = [row for row in rises_data if any(kw in row['url'].lower() for kw in ['parafoudre', 'norme', 'electricite'])]
    seasonal_falls = [row for row in falls_data if any(kw in row['url'].lower() for kw in ['orage', 'chaud', 'climatisation'])]
    
    if seasonal_rises:
        seasonal_gain = sum(row['clicks_diff'] for row in seasonal_rises)
        insights.append(f"⚡ **Trend électrique** : +{seasonal_gain:,} clics sur contenu normes/sécurité électrique")
    
    if seasonal_falls:
        seasonal_loss = sum(abs(row['clicks_diff']) for row in seasonal_falls)
        insights.append(f"🌡️ **Effet saisonnier** : -{seasonal_loss:,} clics sur contenu météo/climat (normal fin été)")
    
    # Analyse anomalies combinées
    critical_issues = len([a for a in (rises_anomalies + falls_anomalies) if a['severity'] == 'HIGH'])
    if critical_issues > 0:
        insights.append(f"🚨 **Alertes critiques** : {critical_issues} problèmes nécessitent une action immédiate")
    
    # Opportunités détectées
    opportunities = len([a for a in rises_anomalies if 'OPPORTUNITÉ' in a['type'] or 'EXCEPTIONNEL' in a['type']])
    if opportunities > 0:
        insights.append(f"💎 **Opportunités** : {opportunities} pages à potentiel élevé identifiées")
    
    # FAQ Analysis
    faq_rises = sum(row['clicks_diff'] for row in rises_data if row['category'] == 'FAQ')
    faq_falls = sum(abs(row['clicks_diff']) for row in falls_data if row['category'] == 'FAQ')
    
    if faq_rises > faq_falls:
        insights.append(f"❓ **FAQ en croissance** : +{faq_rises - faq_falls:,} clics nets - Les utilisateurs cherchent plus d'aide")
    elif faq_falls > faq_rises:
        insights.append(f"❓ **FAQ en recul** : -{faq_falls - faq_rises:,} clics nets - Moins de problèmes techniques ?")
    
    # Recommandations stratégiques
    insights.append("🎯 **Action prioritaire** : Capitaliser sur la norme NF-C 15-100 (contenu connexe) et investiguer les chutes liées à l'orage")
    insights.append("📊 **Monitoring** : Surveiller l'évolution saisonnière des contenus climatisation/chauffage selon les saisons")
    
    return insights

def generate_combined_report(rises_data: List[Dict], falls_data: List[Dict]) -> str:
    """Génère un rapport HTML combiné"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gsc_combined_report_{timestamp}.html"
    
    # Détection d'anomalies
    rises_anomalies = detect_anomalies(rises_data, "hausses")
    falls_anomalies = detect_anomalies(falls_data, "baisses")
    all_anomalies = rises_anomalies + falls_anomalies
    
    # Génération d'insights
    insights = generate_insights(rises_data, falls_data, rises_anomalies, falls_anomalies)
    
    # Calculs pour le récap
    total_rises_clicks_current = sum(row['clicks_current'] for row in rises_data)
    total_rises_clicks_previous = sum(row['clicks_previous'] for row in rises_data)
    total_falls_clicks_current = sum(row['clicks_current'] for row in falls_data)
    total_falls_clicks_previous = sum(row['clicks_previous'] for row in falls_data)
    
    total_clicks_current = total_rises_clicks_current + total_falls_clicks_current
    total_clicks_previous = total_rises_clicks_previous + total_falls_clicks_previous
    
    total_rises_impressions = sum(row['impressions_current'] for row in rises_data)
    total_falls_impressions = sum(row['impressions_current'] for row in falls_data)
    total_impressions = total_rises_impressions + total_falls_impressions
    
    avg_ctr = (total_clicks_current / total_impressions * 100) if total_impressions > 0 else 0
    
    net_clicks_impact = sum(row['clicks_diff'] for row in rises_data) + sum(row['clicks_diff'] for row in falls_data)
    high_impact_pages = len([row for row in (rises_data + falls_data) if abs(row['clicks_diff']) > 100])
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport GSC Combiné - Hausses & Baisses</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #1976d2; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .positive {{ color: #4caf50; font-weight: bold; }}
        .negative {{ color: #f44336; font-weight: bold; }}
        .alert-high {{ background: #ffebee; border-left: 5px solid #f44336; padding: 10px; margin: 5px 0; }}
        .alert-medium {{ background: #fff3e0; border-left: 5px solid #ff9800; padding: 10px; margin: 5px 0; }}
        .alert-low {{ background: #f3e5f5; border-left: 5px solid #9c27b0; padding: 10px; margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; font-size: 0.85em; }}
        .url {{ font-size: 0.9em; max-width: 300px; word-break: break-all; }}
        .metric {{ text-align: center; font-weight: bold; font-size: 0.9em; }}
        .executive-summary {{ background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50; }}
        .insights {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapport GSC Combiné</h1>
        <h2>Hausses & Baisses - Analyse Complète</h2>
        <p>Site: https://www.legrand.fr</p>
        <p><strong>Périodes:</strong> 2025-08-20 → 2025-08-26 vs 2025-08-13 → 2025-08-19</p>
    </div>

    <div class="executive-summary">
        <h2>📋 Récap Exécutif</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h3>🎯 Performance Globale</h3>
                <ul>
                    <li><strong>Impact net:</strong> <span class="{'positive' if net_clicks_impact > 0 else 'negative'}">{net_clicks_impact:+,} clics</span></li>
                    <li><strong>CTR moyen:</strong> {avg_ctr:.2f}%</li>
                    <li><strong>Pages analysées:</strong> 50 (25 hausses + 25 baisses)</li>
                    <li><strong>Fort impact:</strong> {high_impact_pages} pages (>100 clics)</li>
                </ul>
            </div>
            <div>
                <h3>🚨 Alertes</h3>
                <ul>
                    <li><strong>Critiques:</strong> {len([a for a in all_anomalies if a['severity'] == 'HIGH'])}</li>
                    <li><strong>Modérées:</strong> {len([a for a in all_anomalies if a['severity'] == 'MEDIUM'])}</li>
                    <li><strong>Opportunités:</strong> {len([a for a in all_anomalies if a['severity'] == 'LOW'])}</li>
                </ul>
            </div>
        </div>
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px;">
            <p><strong>🚀 Next Steps:</strong> Capitaliser sur les normes électriques, optimiser les pages à forte visibilité/faible CTR, investiguer les chutes techniques.</p>
        </div>
    </div>

    <div class="insights">
        <h2>💡 Insights Stratégiques</h2>
        """
    
    for insight in insights:
        html_content += f"<p style='margin: 10px 0;'>{insight}</p>"
    
    html_content += """
    </div>

    <div class="anomalies">
        <h2>🔍 Anomalies Détectées</h2>
        """
    
    if not all_anomalies:
        html_content += "<p>✅ Aucune anomalie critique détectée.</p>"
    else:
        for anomaly in all_anomalies[:8]:  # Top 8 anomalies
            severity_class = f'alert-{anomaly["severity"].lower()}'
            html_content += f"""
            <div class="{severity_class}">
                <strong>{anomaly['type']} - {anomaly['severity']}</strong><br>
                {anomaly['message']}<br>
                <small class="url">{anomaly['url']}</small>
            </div>
            """
    
    html_content += """
    </div>

    <div class="data-table">
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
                <th>CTR Actuel</th>
            </tr>
        """
    
    for row in rises_data:
        ctr = (row['clicks_current'] / row['impressions_current'] * 100) if row['impressions_current'] > 0 else 0
        html_content += f"""
            <tr>
                <td class="url">{row['url']}</td>
                <td>{row['category']}</td>
                <td class="metric">{row['clicks_current']:,}</td>
                <td class="metric">{row['clicks_previous']:,}</td>
                <td class="metric positive">+{row['clicks_diff']:,}</td>
                <td class="metric">{row['impressions_current']:,}</td>
                <td class="metric">{row['impressions_previous']:,}</td>
                <td class="metric {'positive' if row['impressions_diff'] > 0 else 'negative'}">{row['impressions_diff']:+,}</td>
                <td class="metric">{ctr:.1f}%</td>
            </tr>
        """
    
    html_content += """
        </table>
    </div>

    <div class="data-table">
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
                <th>CTR Actuel</th>
            </tr>
        """
    
    for row in falls_data:
        ctr = (row['clicks_current'] / row['impressions_current'] * 100) if row['impressions_current'] > 0 else 0
        html_content += f"""
            <tr>
                <td class="url">{row['url']}</td>
                <td>{row['category']}</td>
                <td class="metric">{row['clicks_current']:,}</td>
                <td class="metric">{row['clicks_previous']:,}</td>
                <td class="metric negative">{row['clicks_diff']:,}</td>
                <td class="metric">{row['impressions_current']:,}</td>
                <td class="metric">{row['impressions_previous']:,}</td>
                <td class="metric {'positive' if row['impressions_diff'] > 0 else 'negative'}">{row['impressions_diff']:+,}</td>
                <td class="metric">{ctr:.1f}%</td>
            </tr>
        """
    
    html_content += f"""
        </table>
    </div>

    <div class="footer">
        <p><small>Rapport généré le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')} | GSC Combined Report</small></p>
    </div>
</body>
</html>
    """
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename

def main():
    # Conversion des données en format dict
    rises_raw = create_rises_data()
    falls_raw = create_falls_data()
    
    rises_data = []
    for row in rises_raw:
        rises_data.append({
            'url': row[0],
            'clicks_current': row[1],
            'clicks_previous': row[2],
            'clicks_diff': row[3],
            'impressions_current': row[4],
            'impressions_previous': row[5],
            'impressions_diff': row[6],
            'category': categorize_url(row[0])
        })
    
    falls_data = []
    for row in falls_raw:
        falls_data.append({
            'url': row[0],
            'clicks_current': row[1],
            'clicks_previous': row[2],
            'clicks_diff': row[3],
            'impressions_current': row[4],
            'impressions_previous': row[5],
            'impressions_diff': row[6],
            'category': categorize_url(row[0])
        })
    
    report_file = generate_combined_report(rises_data, falls_data)
    print(f"✅ Rapport combiné généré: {report_file}")
    print(f"📊 Analyse complète: 25 hausses + 25 baisses avec insights stratégiques")

if __name__ == "__main__":
    main()