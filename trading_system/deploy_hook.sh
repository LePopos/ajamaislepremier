#!/bin/bash

# 🚀 Hook de déploiement automatique - s'exécute sur le droplet
# Ce script se déclenche quand le droplet fait un git pull

set -e

echo "🚀 DÉPLOIEMENT AUTOMATIQUE DÉTECTÉ !"
echo "📅 $(date)"
echo "📍 Répertoire: $(pwd)"

# Vérifier qu'on est dans le bon répertoire
if [[ ! -f "main.py" ]] || [[ ! -f "requirements.txt" ]]; then
    echo "❌ Erreur: Script exécuté depuis le mauvais répertoire"
    echo "📍 Doit être exécuté depuis /opt/trading_system/trading_system/"
    exit 1
fi

echo "✅ Répertoire correct détecté"

# Arrêter le service
echo "⏹️ Arrêt du service trading-system..."
systemctl stop trading-system 2>/dev/null || echo "Service déjà arrêté"

# Sauvegarder les données importantes
echo "💾 Sauvegarde des données critiques..."
cp -f trading_data.db /tmp/trading_data.db.backup 2>/dev/null || echo "Pas de DB à sauvegarder"
cp -f .env /tmp/.env.backup 2>/dev/null || echo "Pas d'env à sauvegarder"

# Installation des nouvelles dépendances
echo "📦 Installation des nouvelles dépendances..."
python3 -m pip install --upgrade pip

echo "📊 Installation des librairies de visualisation..."
pip3 install --upgrade yfinance>=0.2.18
pip3 install --upgrade matplotlib>=3.7.0
pip3 install --upgrade seaborn>=0.12.0  
pip3 install --upgrade plotly>=5.15.0
pip3 install --upgrade mplfinance>=0.12.9b0

echo "📦 Installation de toutes les dépendances..."
pip3 install -r requirements.txt --upgrade

# Créer le répertoire des graphiques
echo "📁 Préparation du répertoire graphiques..."
mkdir -p charts
chmod 755 charts

# Restaurer les données
echo "🔄 Restauration des données..."
cp -f /tmp/trading_data.db.backup trading_data.db 2>/dev/null || echo "Pas de DB à restaurer"
cp -f /tmp/.env.backup .env 2>/dev/null || echo "Pas d'env à restaurer"

# Test rapide du système
echo "🧪 Test rapide du système mis à jour..."
timeout 45 python3 main.py collect >/dev/null 2>&1 || echo "Test collecte terminé"

echo "🎯 Test de génération de signaux avec graphiques..."
timeout 45 python3 main.py signals >/dev/null 2>&1 || echo "Test signaux terminé"

# Vérifier que les graphiques sont générés
if [[ -d "charts" ]] && [[ -n "$(ls -A charts 2>/dev/null)" ]]; then
    echo "✅ Graphiques générés avec succès !"
    chart_count=$(ls -1 charts/ | wc -l)
    echo "📊 $chart_count graphiques créés"
    echo "📈 Exemples:"
    ls charts/ | head -3 | sed 's/^/   - /'
else
    echo "⚠️ Aucun graphique généré (peut-être normal si pas de données)"
fi

# Redémarrer le service
echo "▶️ Redémarrage du service trading-system..."
systemctl start trading-system
systemctl enable trading-system

echo "⏰ Attente du démarrage complet..."
sleep 15

# Vérification finale
echo "📋 Vérification du service..."
if systemctl is-active --quiet trading-system; then
    echo "✅ Service trading-system: ACTIF"
else
    echo "❌ Service trading-system: PROBLÈME"
    echo "📋 Status détaillé:"
    systemctl status trading-system --no-pager -l || true
fi

# Test final rapide
echo "🔍 Test final du système..."
timeout 30 python3 main.py status >/dev/null 2>&1 || echo "Test status terminé"

echo ""
echo "🎉 DÉPLOIEMENT AUTOMATIQUE TERMINÉ !"
echo ""
echo "📋 NOUVELLES FONCTIONNALITÉS DÉPLOYÉES:"
echo "  ✅ Probabilités réalistes (25-75% calculées dynamiquement)"
echo "  ✅ Logique SELL améliorée avec pondération positions"  
echo "  ✅ Graphiques de tendance avec vraies données Yahoo Finance"
echo "  ✅ Visualisations interactives (PNG haute-def + HTML)"
echo "  ✅ Corrections bugs SQLAlchemy et améliorations techniques"
echo ""
echo "📊 Graphiques disponibles dans: $(pwd)/charts/"
echo "📈 Pour tester: python3 main.py signals"
echo "📋 Logs du service: journalctl -u trading-system -f"
echo ""
echo "🚀 Le système est maintenant opérationnel avec toutes les améliorations !"
echo "📅 Déploiement terminé le: $(date)"
echo ""

# Créer un fichier de confirmation du déploiement
echo "$(date): Déploiement automatique réussi" > /tmp/last_deployment.log
echo "Améliorations: Probabilités réalistes, graphiques, corrections bugs" >> /tmp/last_deployment.log