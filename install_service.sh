#!/bin/bash

# Script d'installation du service trading system
set -e

SERVICE_NAME="trading-system"
SERVICE_FILE="/workspaces/ajamaislepremier/trading-system.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🔧 Installation du service Trading System..."

# Vérifier les droits root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root (sudo)"
   exit 1
fi

# Arrêter le service s'il existe déjà
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "🛑 Arrêt du service existant..."
    systemctl stop $SERVICE_NAME
fi

# Copier le fichier service
echo "📋 Copie du fichier service..."
cp $SERVICE_FILE $SYSTEMD_DIR/

# Recharger systemd
echo "🔄 Rechargement de systemd..."
systemctl daemon-reload

# Activer le service pour démarrage automatique
echo "✅ Activation du service au boot..."
systemctl enable $SERVICE_NAME

# Démarrer le service
echo "🚀 Démarrage du service..."
systemctl start $SERVICE_NAME

# Vérifier le statut
echo "📊 Statut du service:"
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "✅ Service installé avec succès!"
echo "📝 Logs disponibles avec: sudo journalctl -u $SERVICE_NAME -f"
echo "🔧 Commandes utiles:"
echo "   - sudo systemctl start $SERVICE_NAME"
echo "   - sudo systemctl stop $SERVICE_NAME" 
echo "   - sudo systemctl restart $SERVICE_NAME"
echo "   - sudo systemctl status $SERVICE_NAME"