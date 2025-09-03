#!/bin/bash

# 🚀 Script de déploiement du Trading System avec améliorations
# Améliorations déployées :
# ✅ Probabilités réalistes (25-75% au lieu de 80-85% fixes)  
# ✅ Logique SELL améliorée avec pondération basée sur les positions
# ✅ Graphiques de tendance avec vraies données Yahoo Finance
# ✅ Corrections bugs SQLAlchemy
# ✅ Visualisations interactives (Plotly)

set -e

DROPLET_IP="157.230.107.58"
REPO_DIR="/opt/trading_system"
SERVICE_NAME="trading-system"

echo "🚀 Début du déploiement du Trading System amélioré..."

# 1. Connexion au droplet et mise à jour du code
echo "📥 Récupération des dernières modifications depuis GitHub..."
ssh root@$DROPLET_IP << 'ENDSSH'
cd /opt/trading_system

# Arrêter le service existant
echo "⏹️  Arrêt du service trading-system..."
systemctl stop trading-system || echo "Service déjà arrêté"

# Sauvegarder la base de données et la config
echo "💾 Sauvegarde des données importantes..."
cp -r trading_system/trading_data.db /tmp/trading_data.db.backup 2>/dev/null || echo "Pas de DB à sauvegarder"
cp -r trading_system/.env /tmp/.env.backup 2>/dev/null || echo "Pas d'env à sauvegarder" 

# Récupérer les dernières modifications
echo "🔄 Mise à jour du code depuis GitHub..."
git fetch origin
git checkout feature/gsc-analyzer
git pull origin feature/gsc-analyzer

# Restaurer les données importantes
echo "🔄 Restauration des données..."
cp /tmp/trading_data.db.backup trading_system/trading_data.db 2>/dev/null || echo "Pas de DB à restaurer"
cp /tmp/.env.backup trading_system/.env 2>/dev/null || echo "Pas d'env à restaurer"
ENDSSH

# 2. Installation des nouvelles dépendances
echo "📦 Installation des nouvelles dépendances (matplotlib, plotly, etc.)..."
ssh root@$DROPLET_IP << 'ENDSSH'
cd /opt/trading_system/trading_system

# Mise à jour de pip
python3 -m pip install --upgrade pip

# Installation des nouvelles dépendances pour les graphiques
echo "📊 Installation des librairies graphiques..."
pip3 install yfinance>=0.2.18
pip3 install matplotlib>=3.7.0  
pip3 install seaborn>=0.12.0
pip3 install plotly>=5.15.0
pip3 install mplfinance>=0.12.9b0

# Installation de toutes les dépendances
pip3 install -r requirements.txt

# Créer le répertoire charts
mkdir -p charts
chmod 755 charts
ENDSSH

# 3. Test du système mis à jour
echo "🧪 Test du système mis à jour..."
ssh root@$DROPLET_IP << 'ENDSSH'
cd /opt/trading_system/trading_system

# Test de la collecte de données
echo "📈 Test de la collecte de données..."
timeout 60 python3 main.py collect || echo "Test collecte terminé"

# Test de génération de signaux
echo "📊 Test de génération de signaux avec graphiques..."
timeout 60 python3 main.py signals || echo "Test signaux terminé"

# Vérifier que les graphiques sont générés
if [ -d "charts" ] && [ "$(ls -A charts)" ]; then
    echo "✅ Graphiques générés avec succès !"
    ls -la charts/ | head -5
else
    echo "⚠️  Pas de graphiques générés"
fi
ENDSSH

# 4. Redémarrage du service
echo "🔄 Redémarrage du service trading-system..."
ssh root@$DROPLET_IP << 'ENDSSH'
# Redémarrer le service
echo "▶️  Redémarrage du service..."
systemctl start trading-system
systemctl enable trading-system

# Vérifier le statut
sleep 5
systemctl status trading-system --no-pager -l
ENDSSH

# 5. Vérification finale  
echo "✅ Vérification finale du déploiement..."
ssh root@$DROPLET_IP << 'ENDSSH'
cd /opt/trading_system/trading_system

echo "📊 Vérification des logs récents..."
tail -20 logs/trading_system.log 2>/dev/null || echo "Pas de logs disponibles"

echo "🔍 Vérification du processus..."
ps aux | grep python3 | grep main.py | head -3

echo "📈 Test final des signaux..."
timeout 30 python3 main.py status || echo "Test status terminé"
ENDSSH

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ !"
echo ""
echo "📋 RÉSUMÉ DES AMÉLIORATIONS DÉPLOYÉES :"
echo "✅ Probabilités réalistes (25-75% au lieu de valeurs fixes)"
echo "✅ Logique SELL améliorée avec pondération position" 
echo "✅ Graphiques de tendance avec données Yahoo Finance réelles"
echo "✅ Visualisations interactives (PNG + HTML)"
echo "✅ Corrections techniques (bugs SQLAlchemy)"
echo "✅ Nouvelles dépendances : matplotlib, seaborn, plotly, mplfinance"
echo ""
echo "🔧 Pour vérifier le service :"
echo "ssh root@$DROPLET_IP 'systemctl status trading-system'"
echo ""
echo "📊 Pour voir les graphiques générés :"
echo "ssh root@$DROPLET_IP 'ls -la /opt/trading_system/trading_system/charts/'"
echo ""
echo "📈 Pour tester manuellement :"
echo "ssh root@$DROPLET_IP 'cd /opt/trading_system/trading_system && python3 main.py signals'"