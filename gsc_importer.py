#!/usr/bin/env python3
"""
Générateur de rapport GSC à partir de données exportées
Utilise les données réelles GSC au lieu de l'API
"""

import csv
from datetime import datetime
from typing import List, Dict
import argparse

def create_sample_data_rises() -> str:
    """Crée un fichier CSV avec les données de hausses"""
    filename = "gsc_data_rises.csv"
    
    # Données hausses fournies par l'utilisateur
    sample_data = [
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
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'Clics_Actuels', 'Clics_Précédents', 'Clics_Différence', 
                        'Impressions_Actuelles', 'Impressions_Précédentes', 'Impressions_Différence'])
        writer.writerows(sample_data)
    
    return filename

def create_sample_data_falls() -> str:
    """Crée un fichier CSV avec les données de baisses"""
    filename = "gsc_data_falls.csv"
    
    # Données baisses fournies par l'utilisateur
    sample_data = [
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
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'Clics_Actuels', 'Clics_Précédents', 'Clics_Différence', 
                        'Impressions_Actuelles', 'Impressions_Précédentes', 'Impressions_Différence'])
        writer.writerows(sample_data)
    
    return filename

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

def generate_insights(data: List[Dict], anomalies: List[Dict], report_type: str) -> List[str]:
    """Génère des insights intelligents basés sur les données"""
    insights = []
    
    # Calculs de base
    total_clicks_current = sum(row['clicks_current'] for row in data)
    total_clicks_previous = sum(row['clicks_previous'] for row in data)
    total_impressions_current = sum(row['impressions_current'] for row in data)
    total_impressions_previous = sum(row['impressions_previous'] for row in data)
    
    avg_ctr_current = (total_clicks_current / total_impressions_current * 100) if total_impressions_current > 0 else 0
    avg_ctr_previous = (total_clicks_previous / total_impressions_previous * 100) if total_impressions_previous > 0 else 0
    
    # Analyse par catégories
    categories = {}
    for row in data:
        cat = row['category']
        if cat not in categories:
            categories[cat] = {'clicks_diff': 0, 'count': 0}
        categories[cat]['clicks_diff'] += row['clicks_diff']
        categories[cat]['count'] += 1
    
    if report_type == "hausses":
        # Insights Hausses
        top_url = data[0] if data else None
        if top_url:
            insights.append(f"🏆 **Champion de la semaine** : {top_url['clicks_diff']:+,} clics sur la page Norme NF-C 15-100. Cette norme électrique est clairement un sujet d'actualité.")
        
        # Analyse catégorielle
        best_category = max(categories.items(), key=lambda x: x[1]['clicks_diff']) if categories else None
        if best_category:
            cat_name, cat_data = best_category
            insights.append(f"📚 **Catégorie gagnante** : {cat_name} avec {cat_data['clicks_diff']:+,} clics. Les utilisateurs cherchent activement ces informations.")
        
        # Pattern recognition
        faq_growth = sum(row['clicks_diff'] for row in data if row['category'] == 'FAQ')
        if faq_growth > 1000:
            insights.append(f"❓ **Boom des FAQ** : +{faq_growth:,} clics sur les questions fréquentes. Les utilisateurs ont besoin d'aide technique.")
        
        pro_growth = sum(row['clicks_diff'] for row in data if row['category'] == 'Professional')
        if pro_growth > 500:
            insights.append(f"🔧 **Segment Pro en croissance** : +{pro_growth:,} clics. Le marché professionnel est dynamique.")
        
        # Opportunités
        high_impressions_low_clicks = [row for row in data if row['impressions_current'] > 10000 and row['clicks_current'] < 500]
        if high_impressions_low_clicks:
            insights.append(f"💎 **Opportunité SEO** : {len(high_impressions_low_clicks)} pages avec forte visibilité mais peu de clics. Optimiser les titres/descriptions.")
        
        # Saisonnalité positive
        seasonal_content = [row for row in data if any(keyword in row['url'].lower() for keyword in ['parafoudre', 'orage', 'climatisation', 'chauffage'])]
        if seasonal_content:
            total_seasonal = sum(row['clicks_diff'] for row in seasonal_content)
            insights.append(f"🌡️ **Effet saison** : +{total_seasonal:,} clics sur contenus saisonniers. Période favorable pour ces sujets.")
    
    else:  # baisses
        # Insights Baisses
        worst_url = data[0] if data else None
        if worst_url and abs(worst_url['clicks_diff']) > 50:
            insights.append(f"⚠️ **Plus grosse chute** : {worst_url['clicks_diff']:,} clics sur une question liée à l'orage. Saisonnalité normale ou problème technique ?")
        
        # Détection de patterns problématiques
        technical_issues = len([a for a in anomalies if 'TECHNIQUE' in a['type']])
        if technical_issues > 0:
            insights.append(f"🔧 **Alerte technique** : {technical_issues} pages avec des chutes suspectes. Vérifier l'indexation et les redirections.")
        
        seasonal_drops = [row for row in data if any(keyword in row['url'].lower() for keyword in ['climatisation', 'chaud', 'orage'])]
        if seasonal_drops:
            total_seasonal_drop = sum(abs(row['clicks_diff']) for row in seasonal_drops)
            insights.append(f"❄️ **Saisonnalité naturelle** : -{total_seasonal_drop:,} clics sur contenus saisonniers. Normal en cette période.")
        
        # Problèmes de performance
        low_ctr_pages = [row for row in data if row['impressions_current'] > 5000 and (row['clicks_current'] / row['impressions_current']) < 0.01]
        if low_ctr_pages:
            insights.append(f"📉 **CTR problématique** : {len(low_ctr_pages)} pages avec beaucoup d'impressions mais peu de clics. Retravailler les snippets.")
        
        # Impact par catégorie
        worst_category = min(categories.items(), key=lambda x: x[1]['clicks_diff']) if categories else None
        if worst_category and worst_category[1]['clicks_diff'] < -100:
            cat_name, cat_data = worst_category
            insights.append(f"📂 **Catégorie impactée** : {cat_name} perd {cat_data['clicks_diff']:,} clics. Analyser la concurrence et l'actualité.")
    
    # CTR Analysis (commun)
    if avg_ctr_current > avg_ctr_previous:
        ctr_improvement = ((avg_ctr_current - avg_ctr_previous) / avg_ctr_previous) * 100
        insights.append(f"🎯 **CTR amélioré** : +{ctr_improvement:.1f}% ({avg_ctr_previous:.2f}% → {avg_ctr_current:.2f}%). La pertinence du contenu augmente.")
    elif avg_ctr_current < avg_ctr_previous:
        ctr_decline = ((avg_ctr_previous - avg_ctr_current) / avg_ctr_previous) * 100
        insights.append(f"🎯 **CTR dégradé** : -{ctr_decline:.1f}% ({avg_ctr_previous:.2f}% → {avg_ctr_current:.2f}%). Optimiser les meta-descriptions.")
    
    # Recommandations stratégiques
    if report_type == "hausses":
        insights.append("🚀 **Action recommandée** : Capitaliser sur les pages en croissance en créant du contenu connexe et en optimisant le maillage interne.")
        if any('norme' in row['url'].lower() for row in data[:5]):
            insights.append("📋 **Trend détecté** : Les normes électriques intéressent beaucoup. Créer plus de contenu réglementaire.")
    else:
        insights.append("🔍 **Action recommandée** : Investiguer les chutes anormales, mettre à jour le contenu vieillissant, et surveiller les problèmes techniques.")
        high_impact_drops = [row for row in data if abs(row['clicks_diff']) > 50 and row['clicks_previous'] > 100]
        if high_impact_drops:
            insights.append(f"🎯 **Priorité** : {len(high_impact_drops)} pages à fort impact nécessitent une attention immédiate.")
    
    return insights

def generate_html_report(data: List[Dict], title: str = "Top 25 URLs", report_type: str = "hausses") -> str:
    """Génère un rapport HTML"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gsc_real_data_report_{timestamp}.html"
    
    # Calcul des totaux
    total_clicks_current = sum(row['clicks_current'] for row in data)
    total_clicks_previous = sum(row['clicks_previous'] for row in data)
    total_impressions_current = sum(row['impressions_current'] for row in data)
    total_impressions_previous = sum(row['impressions_previous'] for row in data)
    
    clicks_variation = ((total_clicks_current - total_clicks_previous) / total_clicks_previous * 100) if total_clicks_previous > 0 else 0
    impressions_variation = ((total_impressions_current - total_impressions_previous) / total_impressions_previous * 100) if total_impressions_previous > 0 else 0
    
    # Détection d'anomalies
    anomalies = detect_anomalies(data, report_type)
    
    # Génération d'insights
    insights = generate_insights(data, anomalies, report_type)
    
    # Analyse par catégorie
    categories = {}
    for row in data:
        cat = row['category']
        if cat not in categories:
            categories[cat] = {'count': 0, 'clicks_diff': 0, 'impressions_diff': 0}
        categories[cat]['count'] += 1
        categories[cat]['clicks_diff'] += row['clicks_diff']
        categories[cat]['impressions_diff'] += row['impressions_diff']
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport GSC Réel - {title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #1976d2; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .positive {{ color: #4caf50; font-weight: bold; }}
        .negative {{ color: #f44336; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; font-size: 0.85em; }}
        .url {{ font-size: 0.9em; max-width: 300px; word-break: break-all; }}
        .metric {{ text-align: center; font-weight: bold; font-size: 0.9em; }}
        .category-analysis {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapport GSC avec Données Réelles</h1>
        <h2>{title}</h2>
        <p>Site: https://www.legrand.fr</p>
        <p><strong>Périodes:</strong> 2025-08-20 → 2025-08-26 vs 2025-08-13 → 2025-08-19</p>
    </div>

    <div class="summary">
        <h2>📈 Résumé des {len(data)} URLs</h2>
        <ul>
            <li><strong>Total clics actuels:</strong> {total_clicks_current:,}</li>
            <li><strong>Total clics précédents:</strong> {total_clicks_previous:,}</li>
            <li><strong>Variation clics:</strong> <span class="{'positive' if clicks_variation > 0 else 'negative'}">{clicks_variation:+.1f}%</span></li>
            <li><strong>Variation impressions:</strong> <span class="{'positive' if impressions_variation > 0 else 'negative'}">{impressions_variation:+.1f}%</span></li>
            <li><strong>Anomalies détectées:</strong> {len([a for a in anomalies if a['severity'] == 'HIGH'])} critiques, {len([a for a in anomalies if a['severity'] == 'MEDIUM'])} modérées</li>
        </ul>
    </div>

    <div class="anomalies">
        <h2>🔍 Anomalies Détectées</h2>
        """
    
    if not anomalies:
        html_content += "<p>✅ Aucune anomalie significative détectée.</p>"
    else:
        for anomaly in anomalies[:10]:  # Top 10 anomalies
            severity_class = 'alert-high' if anomaly['severity'] == 'HIGH' else 'alert-medium' if anomaly['severity'] == 'MEDIUM' else 'alert-low'
            html_content += f"""
            <div class="{severity_class}">
                <strong>{anomaly['type']} - {anomaly['severity']}</strong><br>
                {anomaly['message']}<br>
                <small class="url">{anomaly['url']}</small>
            </div>
            """
    
    html_content += """
    </div>

    <div class="insights">
        <h2>💡 Insights & Recommandations</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        """
    
    for insight in insights:
        html_content += f"<p style='margin: 10px 0; line-height: 1.6;'>{insight}</p>"
    
    html_content += """
        </div>
    </div>

    <div class="executive-summary">
        <h2>📋 Récap Exécutif</h2>
        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
            <h3>🎯 En bref :</h3>
            <ul style="margin: 10px 0; line-height: 1.8;">
                <li><strong>Volume :</strong> {total_clicks_current:,} clics vs {total_clicks_previous:,} précédents ({clicks_variation:+.1f}%)</li>
                <li><strong>Efficacité :</strong> CTR moyen de {((total_clicks_current / total_impressions_current) * 100):.2f}%</li>
                <li><strong>Impact :</strong> {len([row for row in data if abs(row['clicks_diff']) > 100])} pages avec impact > 100 clics</li>
                <li><strong>Alertes :</strong> {len([a for a in anomalies if a['severity'] == 'HIGH'])} critiques, {len([a for a in anomalies if a['severity'] == 'MEDIUM'])} modérées</li>
            </ul>
            <p style="margin-top: 15px;"><strong>🚀 Next steps :</strong> {'Capitaliser sur la croissance et dupliquer les succès' if report_type == 'hausses' else 'Investiguer les baisses anormales et corriger les problèmes techniques'}</p>
        </div>
    </div>

    <div class="data-table">
        <h2>🚀 {title}</h2>
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
    
    for row in data:
        ctr = (row['clicks_current'] / row['impressions_current'] * 100) if row['impressions_current'] > 0 else 0
        html_content += f"""
            <tr>
                <td class="url">{row['url']}</td>
                <td>{row['category']}</td>
                <td class="metric">{row['clicks_current']:,}</td>
                <td class="metric">{row['clicks_previous']:,}</td>
                <td class="metric {'positive' if row['clicks_diff'] > 0 else 'negative'}">{row['clicks_diff']:+,}</td>
                <td class="metric">{row['impressions_current']:,}</td>
                <td class="metric">{row['impressions_previous']:,}</td>
                <td class="metric {'positive' if row['impressions_diff'] > 0 else 'negative'}">{row['impressions_diff']:+,}</td>
                <td class="metric">{ctr:.1f}%</td>
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
                <th>Total Clics Diff</th>
                <th>Total Impressions Diff</th>
            </tr>
    """
    
    for category, stats in sorted(categories.items(), key=lambda x: x[1]['clicks_diff'], reverse=True):
        html_content += f"""
            <tr>
                <td>{category}</td>
                <td class="metric">{stats['count']}</td>
                <td class="metric {'positive' if stats['clicks_diff'] > 0 else 'negative'}">{stats['clicks_diff']:+,}</td>
                <td class="metric {'positive' if stats['impressions_diff'] > 0 else 'negative'}">{stats['impressions_diff']:+,}</td>
            </tr>
        """
    
    html_content += f"""
        </table>
    </div>

    <div class="footer">
        <p><small>Rapport généré le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')} | Données GSC réelles</small></p>
    </div>
</body>
</html>
    """
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename

def main():
    parser = argparse.ArgumentParser(description='Générateur de rapport GSC à partir de données réelles')
    parser.add_argument('--rises', action='store_true', help='Créer rapport des hausses')
    parser.add_argument('--falls', action='store_true', help='Créer rapport des baisses')
    parser.add_argument('--csv-file', help='Fichier CSV avec les données GSC')
    
    args = parser.parse_args()
    
    if args.rises:
        filename = create_sample_data_rises()
        data = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'url': row['URL'],
                    'clicks_current': int(row['Clics_Actuels']),
                    'clicks_previous': int(row['Clics_Précédents']),
                    'clicks_diff': int(row['Clics_Différence']),
                    'impressions_current': int(row['Impressions_Actuelles']),
                    'impressions_previous': int(row['Impressions_Précédentes']),
                    'impressions_diff': int(row['Impressions_Différence']),
                    'category': categorize_url(row['URL'])
                })
        report_file = generate_html_report(data, f"Top {len(data)} Hausses", "hausses")
        print(f"✅ Rapport hausses généré: {report_file}")
        return
    
    if args.falls:
        filename = create_sample_data_falls()
        data = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'url': row['URL'],
                    'clicks_current': int(row['Clics_Actuels']),
                    'clicks_previous': int(row['Clics_Précédents']),
                    'clicks_diff': int(row['Clics_Différence']),
                    'impressions_current': int(row['Impressions_Actuelles']),
                    'impressions_previous': int(row['Impressions_Précédentes']),
                    'impressions_diff': int(row['Impressions_Différence']),
                    'category': categorize_url(row['URL'])
                })
        report_file = generate_html_report(data, f"Top {len(data)} Baisses", "baisses")
        print(f"✅ Rapport baisses généré: {report_file}")
        return
    
    csv_file = args.csv_file or "gsc_data_sample.csv"
    
    try:
        data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'url': row['URL'],
                    'clicks_current': int(row['Clics_Actuels']),
                    'clicks_previous': int(row['Clics_Précédents']),
                    'clicks_diff': int(row['Clics_Différence']),
                    'impressions_current': int(row['Impressions_Actuelles']),
                    'impressions_previous': int(row['Impressions_Précédentes']),
                    'impressions_diff': int(row['Impressions_Différence']),
                    'category': categorize_url(row['URL'])
                })
        
        report_file = generate_html_report(data, f"Top {len(data)} Hausses", "hausses")
        print(f"✅ Rapport généré: {report_file}")
        print(f"📊 {len(data)} URLs analysées avec les données réelles GSC")
        
    except FileNotFoundError:
        print(f"❌ Fichier {csv_file} introuvable.")
        print("💡 Utilisez --create-sample pour créer un exemple, ou spécifiez --csv-file avec vos données")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()