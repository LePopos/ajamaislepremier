#!/bin/bash

# Script pour exécuter le système de trading automatiquement
# Utilise le même dossier que ce script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TRADING_DIR="$SCRIPT_DIR/trading_system"

echo "$(date): Démarrage du système de trading depuis $TRADING_DIR"

# Changer vers le répertoire de trading
cd "$TRADING_DIR" || {
    echo "❌ Erreur: impossible d'accéder à $TRADING_DIR"
    exit 1
}

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérifier les dépendances critiques
if [ ! -f "requirements.txt" ]; then
    echo "❌ Fichier requirements.txt manquant"
    exit 1
fi

# Installer les dépendances si nécessaire
echo "📦 Vérification des dépendances..."
python3 -m pip install -r requirements.txt --quiet

# Vérifier la configuration
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant"
    exit 1
fi

# Créer le dossier logs si nécessaire
mkdir -p logs

# Exécuter le système
echo "🚀 Exécution du système de trading..."
python3 main.py run

# Capturer le code de sortie
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ $(date): Système de trading exécuté avec succès"
else
    echo "❌ $(date): Erreur lors de l'exécution (code: $EXIT_CODE)"
fi

echo "📝 Logs disponibles dans: $TRADING_DIR/logs/"
exit $EXIT_CODE